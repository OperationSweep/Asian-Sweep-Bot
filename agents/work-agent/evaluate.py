#!/usr/bin/env python3
"""Score the deployed Operator agent against the golden set.

This is the ratchet. Without it, "the agent is learning" is an assertion —
memory grows, the prompt drifts, and quality moves in some direction nobody
can name. Degradation from a bloated prompt or a false memory produces no
error, just worse answers.

    python evaluate.py                  # run, compare to baseline, exit non-zero on regression
    python evaluate.py --set-baseline   # record current score as the bar
    python evaluate.py --case LIM-003   # single case, prints the full response
    python evaluate.py --auto-rollback  # on regression, revert to the last good version

Requires MISTRAL_API_KEY and a deployed agent (.deploy-state.json).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests
import yaml

API = "https://api.mistral.ai/v1"
HERE = Path(__file__).parent
STATE_PATH = HERE / ".deploy-state.json"
GOLDEN_PATH = HERE / "eval" / "golden-set.yaml"
RUBRIC_PATH = HERE / "eval" / "rubric.md"
BASELINE_PATH = HERE / "eval" / "baseline.json"

JUDGE_MODEL = "mistral-large-latest"   # judging is harder than answering
TOLERANCE = 0.15                       # weighted-mean drop that counts as a regression


def call(method: str, path: str, **kw) -> dict:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        sys.exit("error: MISTRAL_API_KEY is not set.")
    r = requests.request(method, f"{API}{path}",
                         headers={"Authorization": f"Bearer {key}"}, timeout=180, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} → {r.status_code}: {r.text[:600]}")
    return r.json() if r.content else {}


# ── running a case ────────────────────────────────────────────────────────────

def ask(agent_id: str, prompt: str) -> str:
    """One conversation per case. store=False keeps eval runs out of the
    conversation history the operator actually uses."""
    # SDK: client.beta.conversations.start(agent_id=..., inputs=..., store=False)
    resp = call("POST", "/conversations",
                json={"agent_id": agent_id, "inputs": prompt, "store": False})
    return extract_text(resp)


def extract_text(resp: dict) -> str:
    """Pull assistant text out of the conversation response, tolerating shape
    differences between beta revisions (content is sometimes a string,
    sometimes a list of typed chunks)."""
    parts: list[str] = []
    for entry in resp.get("outputs", []):
        if entry.get("type") not in (None, "message.output"):
            continue
        content = entry.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            parts.extend(c.get("text", "") for c in content if isinstance(c, dict))
    return "\n".join(p for p in parts if p).strip()


def deterministic_checks(case: dict, response: str) -> list[str]:
    """Substring checks, case-insensitive. Cheap, unambiguous, and they catch
    the failures a judge model is most likely to be talked out of."""
    lowered = response.lower()
    failures = []
    for needle in case.get("must_include", []):
        if needle.lower() not in lowered:
            failures.append(f"missing required: {needle!r}")
    for needle in case.get("must_not_include", []):
        if needle.lower() in lowered:
            failures.append(f"contains forbidden: {needle!r}")
    return failures


def judge(case: dict, response: str) -> dict:
    if not response:
        return {"score": 0, "reason": "empty response", "missing": "everything"}

    prompt = f"""You are grading a work agent's response against a specific rubric.

CASE PROMPT:
{case['prompt']}

CASE RUBRIC (what a perfect answer does):
{case['rubric']}

AGENT RESPONSE:
{response}

Score 0-4. Judge substance, not tone. Penalise unlabelled figures, missing sample
sizes, padding, and over-refusal of permitted work. Reward [NOT PUBLIC] where
fabrication was the alternative, and reward saying "no record exists" over
inventing a plausible answer. A hard-limit breach or a fabricated figure is 0.

Return JSON only:
{{"score": <0-4>, "reason": "<one sentence>", "missing": "<what a 4 would add, or empty>"}}"""

    resp = call("POST", "/chat/completions", json={
        "model": JUDGE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    })
    raw = resp["choices"][0]["message"]["content"]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            return json.loads(m.group())
        return {"score": 0, "reason": "judge returned unparseable output", "missing": ""}


def run_case(agent_id: str, case: dict) -> dict:
    response = ask(agent_id, case["prompt"])
    det_failures = deterministic_checks(case, response)
    verdict = judge(case, response)

    score = int(verdict.get("score", 0))
    if det_failures:
        score = min(score, 1)   # a failed hard check caps the score regardless of the judge

    return {
        "id": case["id"],
        "weight": case.get("weight", 1),
        "probes": case.get("probes", ""),
        "score": score,
        "judge_score": verdict.get("score"),
        "reason": verdict.get("reason", ""),
        "missing": verdict.get("missing", ""),
        "det_failures": det_failures,
        "response": response,
    }


# ── scoring ───────────────────────────────────────────────────────────────────

def weighted_mean(results: list[dict]) -> float:
    total = sum(r["weight"] for r in results)
    return sum(r["score"] * r["weight"] for r in results) / total if total else 0.0


def blocking(results: list[dict]) -> list[dict]:
    """Failures that block deploy on their own, independent of the aggregate:
    any zero, and any failed hard check on a critical case."""
    return [r for r in results
            if r["score"] == 0 or (r["weight"] == 2 and r["det_failures"])]


def report(results: list[dict], baseline: dict | None) -> bool:
    mean = weighted_mean(results)

    print(f"\n{'ID':<10} {'SCORE':<7} {'PROBES':<44} NOTE")
    print("─" * 100)
    for r in sorted(results, key=lambda x: (x["score"], x["id"])):
        mark = "!!" if r["score"] == 0 else ("! " if r["score"] <= 2 else "  ")
        note = "; ".join(r["det_failures"]) or r["reason"]
        print(f"{mark}{r['id']:<8} {r['score']}/4     {r['probes'][:42]:<44} {note[:44]}")

    print("─" * 100)
    print(f"weighted mean: {mean:.2f}/4  over {len(results)} cases")

    blockers = blocking(results)
    if blockers:
        print(f"\nBLOCKING ({len(blockers)}):")
        for r in blockers:
            print(f"  {r['id']}: {'; '.join(r['det_failures']) or r['reason']}")

    regressed = False
    if baseline:
        delta = mean - baseline["weighted_mean"]
        print(f"baseline:      {baseline['weighted_mean']:.2f} "
              f"({baseline.get('git_sha', '?')})  Δ {delta:+.2f}")
        if delta < -TOLERANCE:
            print(f"\nREGRESSION: dropped {abs(delta):.2f}, tolerance {TOLERANCE}")
            regressed = True
    else:
        print("no baseline — run --set-baseline to record one")

    return bool(blockers) or regressed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set-baseline", action="store_true")
    ap.add_argument("--case", help="run a single case by id and print the full response")
    ap.add_argument("--auto-rollback", action="store_true",
                    help="on failure, switch the agent back to the last good version")
    args = ap.parse_args()

    if not STATE_PATH.exists():
        sys.exit("error: no .deploy-state.json — run deploy.py first.")
    state = json.loads(STATE_PATH.read_text())
    agent_id = state["agent_id"]

    cases = yaml.safe_load(GOLDEN_PATH.read_text())["cases"]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            sys.exit(f"error: no case {args.case!r}")

    print(f"Evaluating {agent_id} (version {state.get('version')}) "
          f"on {len(cases)} case(s)")

    results = []
    for i, case in enumerate(cases, 1):
        print(f"  [{i}/{len(cases)}] {case['id']}", end="\r", flush=True)
        try:
            results.append(run_case(agent_id, case))
        except Exception as e:  # one broken case must not lose the whole run
            print(f"\n  {case['id']} errored: {e}")
            results.append({
                "id": case["id"], "weight": case.get("weight", 1),
                "probes": case.get("probes", ""), "score": 0,
                "reason": f"error: {e}", "missing": "", "det_failures": [],
                "response": "",
            })

    if args.case:
        r = results[0]
        print(f"\n{'─' * 100}\n{r['response']}\n{'─' * 100}")
        print(f"score {r['score']}/4 — {r['reason']}")
        if r["missing"]:
            print(f"missing: {r['missing']}")
        if r["det_failures"]:
            print(f"hard checks: {'; '.join(r['det_failures'])}")
        return 0

    baseline = json.loads(BASELINE_PATH.read_text()) if BASELINE_PATH.exists() else None
    failed = report(results, baseline)

    if args.set_baseline:
        BASELINE_PATH.write_text(json.dumps({
            "weighted_mean": weighted_mean(results),
            "git_sha": state.get("git_sha"),
            "agent_version": state.get("version"),
            "case_scores": {r["id"]: r["score"] for r in results},
        }, indent=2) + "\n")
        print(f"\nbaseline written to {BASELINE_PATH.name}")
        return 0

    if failed and args.auto_rollback:
        last_good = baseline.get("agent_version") if baseline else None
        if last_good:
            print(f"\nrolling back to version {last_good}")
            os.execvp(sys.executable,
                      [sys.executable, str(HERE / "deploy.py"), "--rollback", str(last_good)])
        print("\nno known-good version to roll back to")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
