"""SAP GUI control IDs, kept in one YAML file instead of scattered in code.

ZPRO is a custom transaction, so its IDs exist only on your system. Every entry
starts as null in controls.example.yaml; tools/discover_controls.py reads the
real ones off a live screen. Asking for an ID that has not been filled in
raises an error that says exactly how to get it, rather than failing deep
inside a posting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from ..models import KittingError

DISCOVERY_HINT = (
    "Run:  python tools/discover_controls.py --window wnd[0]\n"
    "with that SAP screen open, find the control in the output, and put its id "
    "in controls.yaml under {path!r}."
)


class Controls:
    """Read-only view over controls.yaml with helpful failures."""

    def __init__(
        self,
        data: Dict[str, Any],
        source: str = "controls.yaml",
        permissive: bool = False,
    ) -> None:
        self._data = data or {}
        self._source = source
        # Dry runs set this so the operator can rehearse the whole sequence
        # before any control has been discovered. A placeholder can never
        # reach SAP: nothing is sent in dry-run mode.
        self._permissive = permissive

    @classmethod
    def load(cls, path: str | Path, permissive: bool = False) -> "Controls":
        path = Path(path)
        if not path.exists():
            if permissive:
                return cls({}, str(path), permissive=True)
            raise KittingError(
                f"{path} not found. Copy controls.example.yaml to controls.yaml "
                f"and fill it in using tools/discover_controls.py."
            )
        return cls(
            yaml.safe_load(path.read_text(encoding="utf-8")),
            str(path),
            permissive=permissive,
        )

    def get(self, path: str) -> str:
        """Fetch a dotted key, e.g. 'zpro.work_order_field'."""
        node: Any = self._data
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                node = None
                break
            node = node[part]

        if node is None or (isinstance(node, str) and not node.strip()):
            if self._permissive:
                return f"<UNSET {path}>"
            raise KittingError(
                f"{path!r} is not set in {self._source}.\n"
                + DISCOVERY_HINT.format(path=path)
            )
        return str(node)

    def optional(self, path: str, default: Any = None) -> Any:
        """Fetch a control that the flow can work without.

        Returns the raw node for anything that is not a single id string, so a
        list of ids (co04.clear_fields) comes back as a list.
        """
        node: Any = self._data
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]

        if node is None or (isinstance(node, str) and not node.strip()):
            return default
        if isinstance(node, str) and node.startswith("<UNSET "):
            return default
        return node

    def missing(self) -> list[str]:
        """Every unfilled control, so pre-flight can report them all at once."""
        gaps: list[str] = []

        def walk(node: Any, prefix: str) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    walk(value, f"{prefix}.{key}" if prefix else key)
            elif node is None or (isinstance(node, str) and not node.strip()):
                gaps.append(prefix)

        walk(self._data, "")
        return sorted(gaps)
