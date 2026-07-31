#!/usr/bin/env python3
"""Deploy the Operator agent from this repository to Mistral.

Git is the source of truth; Mistral is the deploy target. This script pushes
instructions, tools and memory, and records what it did in .deploy-state.json.

    python deploy.py --create      # first run: create library + agent
    python deploy.py               # subsequent: new agent version + memory sync
    python deploy.py --dry-run     # show what would change
    python deploy.py --rollback 3  # switch the live agent back to version 3

Written against the REST API rather than the SDK so the field names are pinned
and visible. SDK equivalents are noted in comments where they exist.

Requires MISTRAL_API_KEY.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import requests
import yaml

API = "https://api.mistral.ai/v1"
HERE = Path(__file__).parent
STATE_PATH = HERE / ".deploy-state.json"
CONFIG_PATH = HERE / "agent.yaml"


# ── plumbing ──────────────────────────────────────────────────────────────────

class DeployError(RuntimeError):
    pass


def api_key() -> str:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        raise DeployError("MISTRAL_API_KEY is not set.")
    return key


def call(method: str, path: str, **kw) -> dict:
    headers = {"Authorization": f"Bearer {api_key()}"}
    headers.update(kw.pop("headers", {}))
    r = requests.request(method, f"{API}{path}", headers=headers, timeout=120, **kw)
    if r.status_code >= 400:
        raise DeployError(f"{method} {path} → {r.status_code}: {r.text[:600]}")
    return r.json() if r.content else {}


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def git(*args: str, default: str = "unknown") -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=HERE, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return default


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ── config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    cfg = yaml.safe_load(CONFIG_PATH.read_text())
    cfg["_instructions"] = (HERE / cfg["instructions_file"]).read_text()
    return cfg


def memory_files(cfg: dict) -> list[Path]:
    """Memory sources plus any extra globs, deduplicated, in declaration order."""
    lib = cfg["library"]
    paths: list[Path] = [HERE / s for s in lib.get("sources", [])]
    for pattern in lib.get("extra_globs") or []:
        base = HERE
        # Path.glob rejects patterns with leading '..'; split the literal prefix off.
        while pattern.startswith("../"):
            base, pattern = base.parent, pattern[3:]
        paths.extend(sorted(base.glob(pattern)))

    seen, out = set(), []
    for p in paths:
        resolved = p.resolve()
        if resolved in seen:
            continue
        if not p.exists():
            print(f"  ! missing, skipped: {p}")
            continue
        seen.add(resolved)
        out.append(p)
    return out


def doc_name(path: Path) -> str:
    """Stable, collision-free document name. Library documents have no path,
    so research/foo.md and memory/foo.md would otherwise overwrite each other."""
    parent = path.parent.name
    return f"{parent}__{path.name}" if parent not in {"work-agent", ""} else path.name


# ── library ───────────────────────────────────────────────────────────────────

def ensure_library(cfg: dict, state: dict, dry_run: bool) -> str:
    lib_id = cfg["library"].get("id") or state.get("library_id")
    if lib_id:
        return lib_id
    if dry_run:
        print("  would create library:", cfg["library"]["name"])
        return "DRY-RUN-LIBRARY"

    created = call(
        "POST", "/libraries",
        json={
            "name": cfg["library"]["name"],
            "description": cfg["library"].get("description"),
            # SDK: client.beta.libraries.create(...)
        },
    )
    lib_id = created["id"]
    print(f"  created library {lib_id}")
    print(f"  → paste this into agent.yaml as library.id: {lib_id}")
    return lib_id


def list_documents(lib_id: str) -> dict[str, str]:
    """{document_name: document_id} for everything currently in the library."""
    docs, page = {}, 0
    while True:
        resp = call("GET", f"/libraries/{lib_id}/documents",
                    params={"page": page, "page_size": 100})
        batch = resp.get("data", resp if isinstance(resp, list) else [])
        if not batch:
            break
        for d in batch:
            docs[d.get("name") or d.get("filename", "")] = d["id"]
        if len(batch) < 100:
            break
        page += 1
    return docs


def sync_library(cfg: dict, lib_id: str, state: dict, dry_run: bool) -> dict:
    """Upload changed files; replace-by-name. Content-hashed so unchanged files
    are not re-uploaded and re-indexed on every deploy."""
    hashes = dict(state.get("document_hashes", {}))
    existing = {} if dry_run else list_documents(lib_id)

    for path in memory_files(cfg):
        name = doc_name(path)
        content = path.read_text()
        h = digest(content)

        if hashes.get(name) == h and name in existing:
            continue

        if dry_run:
            print(f"  would upload: {name}")
            continue

        if name in existing:
            call("DELETE", f"/libraries/{lib_id}/documents/{existing[name]}")

        # multipart field name is `file` — SDK: client.beta.libraries.documents.upload()
        call("POST", f"/libraries/{lib_id}/documents",
             files={"file": (name, content.encode(), "text/markdown")})
        hashes[name] = h
        print(f"  uploaded: {name}")

    return hashes


# ── agent ─────────────────────────────────────────────────────────────────────

def build_tools(cfg: dict, lib_id: str) -> list[dict]:
    tools = []
    for tool in cfg["tools"]:
        tool = dict(tool)
        if tool["type"] == "document_library":
            tool["library_ids"] = [lib_id]
        tools.append(tool)
    return tools


def agent_payload(cfg: dict, lib_id: str, version_message: str) -> dict:
    return {
        "model": cfg["model"],
        "name": cfg["name"],
        "description": cfg.get("description"),
        "instructions": cfg["_instructions"],
        "tools": build_tools(cfg, lib_id),
        "completion_args": cfg.get("completion_args", {}),
        "metadata": {
            **{k: str(v) for k, v in (cfg.get("metadata") or {}).items()},
            "git_sha": git("rev-parse", "--short", "HEAD"),
            "git_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        },
        "version_message": version_message[:200],
    }


def deploy(create: bool, dry_run: bool, message: str | None) -> None:
    cfg, state = load_config(), load_state()
    version_message = message or git("log", "-1", "--pretty=%s", default="manual deploy")

    print(f"Deploying {cfg['name']}")
    print(f"  model:  {cfg['model']}")
    print(f"  commit: {version_message}")

    lib_id = ensure_library(cfg, state, dry_run)
    hashes = sync_library(cfg, lib_id, state, dry_run)
    payload = agent_payload(cfg, lib_id, version_message)

    agent_id = state.get("agent_id")
    if dry_run:
        print(f"  would {'create' if not agent_id else 'update'} agent")
        print(f"  instructions: {len(cfg['_instructions'])} chars")
        return

    if create or not agent_id:
        # SDK: client.beta.agents.create(**payload)
        agent = call("POST", "/agents", json=payload)
        print(f"  created agent {agent['id']}")
    else:
        # SDK: client.beta.agents.update(agent_id=..., **payload)
        agent = call("PATCH", f"/agents/{agent_id}", json=payload)
        print(f"  updated agent {agent['id']} → version {agent.get('version')}")

    save_state({
        "agent_id": agent["id"],
        "library_id": lib_id,
        "version": agent.get("version"),
        "git_sha": payload["metadata"]["git_sha"],
        "version_message": version_message,
        "document_hashes": hashes,
    })
    print(f"  state written to {STATE_PATH.name}")


def rollback(version: int) -> None:
    state = load_state()
    agent_id = state.get("agent_id")
    if not agent_id:
        raise DeployError("No agent_id in .deploy-state.json — nothing to roll back.")

    # No request body; version is a query parameter.
    call("PATCH", f"/agents/{agent_id}/version", params={"version": version})
    state["version"] = version
    state["rolled_back_to"] = version
    save_state(state)
    print(f"Rolled {agent_id} back to version {version}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--create", action="store_true", help="create rather than update")
    ap.add_argument("--dry-run", action="store_true", help="show changes, send nothing")
    ap.add_argument("--message", help="version message (defaults to last commit subject)")
    ap.add_argument("--rollback", type=int, metavar="N", help="switch to version N")
    args = ap.parse_args()

    try:
        if args.rollback is not None:
            rollback(args.rollback)
        else:
            deploy(args.create, args.dry_run, args.message)
    except DeployError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
