#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess

from common import command_from_payload, cwd, hook_decision, load_state, read_payload, session_id, tool_name, write_json


BLOCK_PATTERNS = [
    (r"\bgit\s+reset\s+--hard\b", "Blocked destructive git history reset."),
    (r"\bgit\s+checkout\s+--\b", "Blocked path-destructive git checkout."),
    (r"\bgit\s+clean\s+-f", "Blocked destructive git clean."),
    (r"\brm\s+-rf\s+/\b", "Blocked destructive root deletion."),
    (r"\bsudo\s+rm\s+-rf\b", "Blocked destructive sudo deletion."),
    (r"\bmkfs\b", "Blocked filesystem formatting command."),
    (r"\bdd\s+if=/dev/(zero|random)\b", "Blocked destructive disk write command."),
]

PROTECTED_BRANCHES = {"main", "master"}
PROTECTED_GIT_WRITES = re.compile(r"\bgit\s+(commit|merge|rebase|cherry-pick|push|revert)\b")


def current_branch(where: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=where,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip().lower()
    except Exception:
        return ""


def is_local_tool(name: str) -> bool:
    lowered = (name or "").lower()
    if not lowered:
        return True
    safe_fragments = ("web", "docs", "search")
    risky_fragments = ("terminal", "run", "edit", "write", "apply", "workspace", "file", "notebook", "mcp")
    return any(fragment in lowered for fragment in risky_fragments) and not lowered.startswith(safe_fragments)


def main() -> int:
    payload = read_payload()
    sid = session_id(payload)
    state = load_state("session", sid)
    name = tool_name(payload)
    command = command_from_payload(payload)

    if state.get("shared_picture_gate") == "awaiting_contract" and is_local_tool(name):
        write_json(
            hook_decision(
                "Shared-Picture Gate is locked. Present a Shared-Picture Contract and wait for exact `confirmed: proceed` before local/project-state tools."
            )
        )
        return 0

    if command:
        for pattern, reason in BLOCK_PATTERNS:
            if re.search(pattern, command):
                write_json(hook_decision(reason))
                return 0
        branch = current_branch(cwd(payload))
        if branch in PROTECTED_BRANCHES and PROTECTED_GIT_WRITES.search(command):
            write_json(hook_decision(f"Blocked git write on protected branch `{branch}`. Create a feature branch first."))
            return 0

    write_json({"continue": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
