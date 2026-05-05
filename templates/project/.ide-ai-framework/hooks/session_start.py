#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

from common import cwd, hook_context, read_payload, write_json


def run(cmd: list[str], where: str) -> str:
    try:
        return subprocess.check_output(cmd, cwd=where, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""


def main() -> int:
    payload = read_payload()
    where = cwd(payload)
    root = run(["git", "rev-parse", "--show-toplevel"], where) or where
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], where) or "n/a"
    has_templates = Path(where, ".github", "copilot-instructions.md").exists()
    notes = [
        f"IDE-AI-FRAMEWORK: active",
        f"ROOT: {root}",
        f"BRANCH: {branch}",
        "WORKFLOW: Shared-Picture Gate, phase boundaries, narrow verification, progress artifacts.",
        "ASSETS: .ide-ai-framework/skills, .ide-ai-framework/agents, .ide-ai-framework/context-engineering, .ide-ai-framework/compaction.",
        "SAFETY: hook policy blocks locked local/project-state tools, dangerous commands, and protected-branch git writes when supported by the host.",
        "AGENTS: do not delegate unless the user explicitly asks for delegation or parallel agents.",
    ]
    if not has_templates:
        notes.append("WARNING: repo-level Copilot instruction file was not found in this workspace.")
    write_json(hook_context("SessionStart", "\n".join(notes)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
