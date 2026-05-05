#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys

from telemetry_common import load_session_state


BLOCK_PATTERNS = [
    (r"\bgit\s+reset\s+--hard\b", "Blocked destructive git reset."),
    (r"\bgit\s+checkout\s+--\b", "Blocked path-destructive git checkout."),
    (r"\bgit\s+clean\s+-f", "Blocked destructive git clean."),
    (r"\brm\s+-rf\s+/\b", "Blocked destructive root deletion."),
    (r"\bsudo\s+rm\s+-rf\b", "Blocked destructive sudo deletion."),
    (r"\bmkfs\b", "Blocked destructive filesystem formatting command."),
    (r"\bdd\s+if=/dev/(zero|random)\b", "Blocked destructive disk write command."),
]

PROTECTED_BRANCHES = {"main", "master"}
PROTECTED_GIT_WRITES = re.compile(
    r"\bgit\s+(commit|merge|rebase|cherry-pick|push|revert)\b"
)
LOCAL_TOOL_NAMES = {"Bash", "apply_patch", "Edit", "Write"}
EVIDENCE_MCP_PATTERNS = [
    re.compile(r"^mcp__openaiDeveloperDocs__"),
    re.compile(r"^mcp__.*browser.*"),
]


def current_branch(cwd):
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=cwd,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            .strip()
            .lower()
        )
    except Exception:
        return ""


def emit_block(reason):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))


def is_local_project_state_tool(tool_name):
    if not isinstance(tool_name, str) or not tool_name:
        return False
    if tool_name in LOCAL_TOOL_NAMES:
        return True
    if tool_name.startswith("mcp__"):
        return not any(pattern.search(tool_name) for pattern in EVIDENCE_MCP_PATTERNS)
    return False


def shared_picture_gate_blocks(payload, tool_name):
    if not is_local_project_state_tool(tool_name):
        return False

    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return False

    state = load_session_state(session_id)
    return state.get("shared_picture_gate") == "awaiting_contract"


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    tool_input = payload.get("tool_input") or {}
    tool_name = payload.get("tool_name") or ""
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    cwd = payload.get("cwd") or os.getcwd()

    if shared_picture_gate_blocks(payload, tool_name):
        emit_block(
            "Shared-Picture Gate is locked. Ask tailored output-focused questions, present a Shared-Picture Contract, and wait for exact `confirmed: proceed` before local/project-state tools."
        )
        return

    if not isinstance(command, str) or not command.strip():
        return

    for pattern, reason in BLOCK_PATTERNS:
        if re.search(pattern, command):
            emit_block(reason)
            return

    branch = current_branch(cwd)
    if branch in PROTECTED_BRANCHES and PROTECTED_GIT_WRITES.search(command):
        emit_block(f"Blocked git write on protected branch `{branch}`. Create a feature branch first.")
        return


if __name__ == "__main__":
    main()
