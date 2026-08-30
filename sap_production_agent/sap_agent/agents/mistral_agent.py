"""Mistral integration - Option C: supervisor, not driver.

Three architectures were on the table:

  A  Python app calling Mistral for reasoning
  B  Mistral Agent owning the tools, deciding what to call
  C  Deterministic Python owning every posting action, Mistral advising

This is C, and the reason is specific rather than general caution. Under B the
model chooses when to call post_goods_issue(). A goods issue is irreversible
and moves real stock, so a single mis-sequenced call - a retry after a posting
that actually succeeded, an order posted twice because a tool result was
misread - costs a stock correction, not a re-run. There is nothing in this
workflow the model needs that freedom for: the sequence is fixed, and the
workbook already says exactly what should happen.

So the tools below are read-and-advise only. Every write to SAP happens in
sap/zpro.py and sap/co04.py, on the deterministic path, whether or not Mistral
is enabled. What the model gets is the two decisions that genuinely need
judgement:

  interpret_message   an SAP message no rule matched. The classifier is
                      deliberately strict and returns UNKNOWN rather than
                      guessing; this turns UNKNOWN into a recommendation with a
                      reason, and the operator still confirms.
  explain_run         plain-language summary of what happened and what to do
                      next, for the operator and the audit log.

Both are advisory. Neither can post, retry, or resolve anything on its own -
the orchestrator treats a recommendation as input to a stop-or-continue
decision it makes itself.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You advise a factory automation that posts goods issues in
SAP transaction ZPRO for fibre-optic kitting. You never operate SAP; you
interpret data and message text so an operator can decide.

Rules:
- Prefer the safest reading. A wrong "continue" posts stock incorrectly.
- If a message could mean the posting failed, say stop.
- Be terse and concrete. One or two sentences of reasoning, no preamble.
- You are told which materials carry serials in this build and which do not.
  A missing-serial message about a material that DOES carry serials means the
  entry failed and is never safe to continue past.
"""

RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendation": {
            "type": "string",
            "enum": ["continue", "retry", "skip", "stop"],
            "description": (
                "continue: harmless, the posting succeeded. "
                "retry: transient, the same order can be attempted again. "
                "skip: this order is bad but the batch can go on. "
                "stop: halt the run and get a human."
            ),
        },
        "severity": {
            "type": "string",
            "enum": ["informational", "warning", "error"],
        },
        "reason": {"type": "string", "description": "One sentence for the operator."},
        "confidence": {"type": "number", "description": "0.0 to 1.0"},
    },
    "required": ["recommendation", "severity", "reason", "confidence"],
}

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "what_happened": {"type": "string"},
        "next_actions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["headline", "what_happened", "next_actions"],
}


@dataclass
class Recommendation:
    recommendation: str
    severity: str
    reason: str
    confidence: float

    @property
    def safe_to_continue(self) -> bool:
        """Advice is only ever acted on unattended when it is confident.

        A low-confidence "continue" is treated as "stop" - the model saying it
        is unsure is itself the useful signal.
        """
        return self.recommendation == "continue" and self.confidence >= 0.8


class MistralAdvisor:
    def __init__(
        self,
        model: str = "mistral-medium-3505",
        api_key: Optional[str] = None,
        timeout_s: int = 30,
    ) -> None:
        key = api_key or os.environ.get("MISTRAL_API_KEY")
        if not key:
            raise RuntimeError(
                "MISTRAL_API_KEY is not set. Get one from console.mistral.ai, or "
                "run with mistral.enabled: false for the fully deterministic path."
            )
        try:
            from mistralai import Mistral
        except ImportError as exc:
            raise RuntimeError("pip install mistralai") from exc

        self.client = Mistral(api_key=key)
        self.model = model
        self.timeout_s = timeout_s

    def _ask(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """One turn, structured output, via tool calling to force the shape."""
        response = self.client.chat.complete(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "answer",
                    "description": "Return the structured answer.",
                    "parameters": schema,
                },
            }],
            tool_choice="any",
            parallel_tool_calls=False,
        )
        message = response.choices[0].message
        calls = getattr(message, "tool_calls", None)
        if not calls:
            raise RuntimeError(f"no structured output returned: {message.content}")
        return json.loads(calls[0].function.arguments)

    # -- advisory job 1 ----------------------------------------------------

    def interpret_message(
        self,
        work_order: str,
        message_type: str,
        message_text: str,
        serialised_materials: Sequence[str],
        non_serialised_materials: Sequence[str],
        serials_written: int,
    ) -> Recommendation:
        prompt = (
            f"SAP returned a message the rule-based classifier could not place.\n\n"
            f"Work order: {work_order}\n"
            f"Message type: {message_type or '(none)'}\n"
            f"Message text: {message_text}\n"
            f"Serials written to the components view before posting: {serials_written}\n\n"
            f"Materials that DO carry serials in this build:\n"
            f"{', '.join(serialised_materials) or '(none)'}\n\n"
            f"Materials that carry NO serials in this build (SAP is expected to "
            f"ask for these):\n{', '.join(non_serialised_materials) or '(none)'}\n\n"
            f"What should the automation do?"
        )
        data = self._ask(prompt, RECOMMENDATION_SCHEMA)
        result = Recommendation(
            recommendation=data.get("recommendation", "stop"),
            severity=data.get("severity", "error"),
            reason=data.get("reason", ""),
            confidence=float(data.get("confidence", 0.0)),
        )
        log.info(
            "Mistral on %s: %s (%.0f%%) - %s",
            work_order, result.recommendation, result.confidence * 100, result.reason,
        )
        return result

    # -- advisory job 2 ----------------------------------------------------

    def explain_run(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            "Summarise this kitting run for the operator who has just walked back "
            "to the terminal. Say plainly whether it worked, and what they need to "
            "do next.\n\n"
            f"{json.dumps(summary, indent=2, default=str)}"
        )
        return self._ask(prompt, SUMMARY_SCHEMA)


def load(config: dict) -> Optional[MistralAdvisor]:
    """Build an advisor if config enables one, otherwise None."""
    settings = config.get("mistral", {})
    if not settings.get("enabled", False):
        return None
    return MistralAdvisor(
        model=settings.get("model", "mistral-medium-3505"),
        timeout_s=settings.get("timeout_s", 30),
    )
