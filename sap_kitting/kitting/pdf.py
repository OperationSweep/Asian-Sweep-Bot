"""Get the ZPRO output out of SAP as a PDF named after the work order.

Three strategies, because which one works depends on how ZPRO renders its
output. Try them in this order:

  preview_button  ZPRO shows a print preview with its own PDF/export button.
                  Cleanest when it exists. Needs the button ID from
                  inspect_screen.py.
  pdf_printer     Print to a SAP output device that maps to a Windows virtual
                  PDF printer, then type the filename into the Windows save
                  dialog. Works almost everywhere; the weak point is the save
                  dialog, which pywinauto handles.
  spool           Print to a spool with a PDF device type and download it.
                  Cleanest for unattended/server runs but needs Basis to
                  provide a PDF device.
"""

from __future__ import annotations

import logging
import time
from datetime import date
from pathlib import Path

from .models import KittingError
from .sap import VKEY_CTRL_P, VKEY_ENTER, SapSession

log = logging.getLogger(__name__)


def target_path(order_number: str, pdf_config: dict) -> Path:
    """Build the output path from the template, and refuse silent overwrites."""
    template = pdf_config.get("filename_template", "{order}.pdf")
    filename = template.format(order=order_number, date=date.today().strftime("%Y%m%d"))

    out_dir = Path(pdf_config["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename

    if path.exists() and not pdf_config.get("overwrite", False):
        raise KittingError(
            f"{path} already exists. Set pdf.overwrite: true, or move the old "
            f"file - refusing to overwrite a kitting document."
        )
    return path


def export(sap: SapSession, order_number: str, pdf_config: dict) -> Path:
    strategy = pdf_config.get("strategy", "pdf_printer")
    path = target_path(order_number, pdf_config)

    if sap.dry_run:
        log.info("[dry-run] would export PDF via %s to %s", strategy, path)
        return path

    if strategy == "pdf_printer":
        _export_via_pdf_printer(sap, path, pdf_config["pdf_printer"])
    elif strategy == "spool":
        _export_via_spool(sap, path, pdf_config["spool"])
    elif strategy == "preview_button":
        _export_via_preview_button(sap, path, pdf_config.get("preview_button", {}))
    else:
        raise KittingError(f"unknown pdf strategy {strategy!r}")

    if not path.exists():
        raise KittingError(f"PDF export reported success but {path} is missing")

    log.info("saved %s", path)
    return path


def _export_via_pdf_printer(sap: SapSession, path: Path, cfg: dict) -> None:
    """Ctrl+P in SAP, then drive the Windows 'Save Print Output As' dialog."""
    sap.send_vkey(VKEY_CTRL_P)

    # The SAP print dialog: set the output device, then confirm.
    device = cfg.get("sap_output_device", "LOCL")
    for element_id in (
        "wnd[1]/usr/ctxtPRI_PARAMS-PDEST",
        "wnd[1]/usr/ctxtRSPOLNPAR-PDEST",
    ):
        try:
            sap.set_text(element_id, device)
            break
        except KittingError:
            continue

    sap.send_vkey(VKEY_ENTER, window="wnd[1]")
    _fill_windows_save_dialog(path, cfg)


def _fill_windows_save_dialog(path: Path, cfg: dict) -> None:
    """Type the target path into the Windows save dialog and press Save.

    This is the one step that leaves SAP's world, so it is also the most
    fragile: the dialog title differs by Windows language and by which virtual
    printer is used. Both are configurable.
    """
    try:
        from pywinauto import Desktop
    except ImportError as exc:
        raise KittingError(
            "pywinauto is required for the pdf_printer strategy: pip install pywinauto"
        ) from exc

    title = cfg.get("save_dialog_title", "Save Print Output As")
    timeout = cfg.get("save_dialog_timeout_s", 30)
    deadline = time.time() + timeout

    dialog = None
    while time.time() < deadline:
        try:
            dialog = Desktop(backend="win32").window(title_re=f".*{title}.*")
            if dialog.exists():
                break
        except Exception:
            pass
        time.sleep(0.5)

    if dialog is None or not dialog.exists():
        raise KittingError(
            f"The Windows save dialog titled '{title}' never appeared within "
            f"{timeout}s. Check pdf.pdf_printer.windows_printer and "
            f"save_dialog_title - the title is localised."
        )

    dialog.wait("ready", timeout=timeout)
    dialog.Edit.set_edit_text(str(path))
    dialog.Button.click()   # the Save button

    # The printer writes asynchronously; wait for the file to land.
    file_deadline = time.time() + timeout
    while time.time() < file_deadline:
        if path.exists() and path.stat().st_size > 0:
            return
        time.sleep(0.5)

    raise KittingError(f"save dialog accepted but {path} never appeared")


def _export_via_spool(sap: SapSession, path: Path, cfg: dict) -> None:
    """Print to a PDF spool device. Requires a PDF device type from Basis."""
    raise KittingError(
        "The spool strategy needs a PDF output device (device type PDF1/PDFUC) "
        "that only your Basis team can create, plus the spool number ZPRO "
        f"returns. Ask them for the device name, set pdf.spool.sap_output_device, "
        f"then implement the SP01 download for your system. Target was {path}."
    )


def _export_via_preview_button(sap: SapSession, path: Path, cfg: dict) -> None:
    """Press ZPRO's own export button, then fill the save dialog."""
    button_id = cfg.get("button_id")
    if not button_id:
        raise KittingError(
            "pdf.preview_button.button_id is not set. Run inspect_screen.py on "
            "the ZPRO output screen to find the export button's ID."
        )
    sap.press(button_id)
    _fill_windows_save_dialog(path, cfg)
