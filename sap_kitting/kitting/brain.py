"""Where Mistral actually earns its place in this workflow.

Deliberately narrow. Keying an order number into a production ERP is a fixed
five-step sequence - having a language model improvise it buys nothing and can
post the wrong thing. So the model does not drive SAP. It does two jobs that
are genuinely hard to write rules for:

  map_columns  the scan sheet's headers changed, or a new site sends a
               differently-labelled export, and we need header -> logical field.
  triage       ZPRO threw a message or a popup we do not recognise, and we need
               retry / skip / stop plus a sentence a kitter can act on.

Both are advisory. triage can never escalate to "press this key"; the caller
decides what to do with the verdict, and allow_write_tools stays false.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You assist a factory kitting automation that drives the SAP
transaction ZPRO. You never operate SAP yourself; you only interpret data and
error text. Be terse and concrete. If you are unsure, say so and prefer the
safest verdict (stop), because a wrong guess posts bad data to a production ERP.
"""

TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["retry", "skip", "stop"],
            "description": "retry: transient, try the same order again. "
                           "skip: this order is bad, continue with the rest. "
                           "stop: something is wrong with the run itself.",
        },
        "reason": {"type": "string", "description": "One sentence for the kitter."},
        "confidence": {"type": "number", "description": "0.0 to 1.0"},
    },
    "required": ["verdict", "reason", "confidence"],
}

COLUMN_SCHEMA = {
    "type": "object",
    "properties": {
        "order_number": {"type": "string"},
        "part_number": {"type": "string"},
        "serial": {"type": "string"},
        "quantity": {"type": "string"},
        "component_type": {"type": "string"},
    },
    "required": ["order_number"],
}


@dataclass
class Triage:
    verdict: str
    reason: str
    confidence: float


class MistralBrain:
    """Thin wrapper over the Mistral chat API with JSON-shaped replies."""

    def __init__(self, model: str = "mistral-medium-3505") -> None:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError(
                "MISTRAL_API_KEY is not set. Get a key from console.mistral.ai, "
                "or run with brain.mode: none for the deterministic path."
            )
        try:
            from mistralai import Mistral
        except ImportError as exc:
            raise RuntimeError("pip install mistralai") from exc

        self.client = Mistral(api_key=api_key)
        self.model = model

    def _ask_json(self, prompt: str, schema: dict) -> dict:
        """One turn, JSON back. Uses tool calling to force the shape."""
        tools = [{
            "type": "function",
            "function": {
                "name": "answer",
                "description": "Return the structured answer.",
                "parameters": schema,
            },
        }]

        response = self.client.chat.complete(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            tools=tools,
            tool_choice="any",
            parallel_tool_calls=False,
        )

        message = response.choices[0].message
        if not getattr(message, "tool_calls", None):
            raise RuntimeError(f"model did not return structured output: {message.content}")

        return json.loads(message.tool_calls[0].function.arguments)

    # -- job 1: work out the column mapping -------------------------------

    def map_columns(self, headers: List[str], sample_rows: List[dict]) -> Dict[str, str]:
        """Guess which spreadsheet column is which logical field.

        Returns a mapping you can drop straight into config.yaml's sheet.columns.
        Always review it once before trusting it - then hard-code it, so the
        steady-state run needs no LLM call at all.
        """
        prompt = (
            "A factory scan sheet has these column headers:\n"
            f"{json.dumps(headers, indent=2)}\n\n"
            "Here are the first rows:\n"
            f"{json.dumps(sample_rows, indent=2, default=str)}\n\n"
            "Which header holds the SAP work order number, the material/part "
            "number, the serial number, the quantity, and the component type "
            "(optic filter, coupler, and so on)? Return the exact header text "
            "for each. Omit a field entirely if the sheet has no such column."
        )
        mapping = self._ask_json(prompt, COLUMN_SCHEMA)
        log.info("Mistral proposed column mapping: %s", mapping)
        return mapping

    # -- job 2: triage an unexpected SAP screen ---------------------------

    def triage(
        self,
        order_number: str,
        error: str,
        status_message: str = "",
        popup_text: str = "",
    ) -> Triage:
        """Classify a failure as retry / skip / stop, with a readable reason."""
        prompt = (
            f"While running SAP transaction ZPRO for work order {order_number}, "
            f"the automation failed.\n\n"
            f"Python error: {error}\n"
            f"SAP status bar: {status_message or '(empty)'}\n"
            f"Popup text: {popup_text or '(none)'}\n\n"
            "Classify this. 'Order does not exist' or 'no data' means skip. "
            "A lock, a timeout, or 'try again later' means retry. Anything "
            "about authorisation, a changed screen layout, or a field that was "
            "not found means stop, because the configuration is wrong."
        )
        data = self._ask_json(prompt, TRIAGE_SCHEMA)
        verdict = Triage(
            verdict=data.get("verdict", "stop"),
            reason=data.get("reason", ""),
            confidence=float(data.get("confidence", 0.0)),
        )
        log.info(
            "Mistral triage for %s: %s (%.0f%%) - %s",
            order_number, verdict.verdict, verdict.confidence * 100, verdict.reason,
        )
        return verdict


def load(config: dict) -> Optional[MistralBrain]:
    """Build a brain if config asks for one, otherwise None."""
    brain_config = config.get("brain", {})
    if brain_config.get("mode", "none") != "mistral":
        return None
    return MistralBrain(model=brain_config.get("model", "mistral-medium-3505"))
