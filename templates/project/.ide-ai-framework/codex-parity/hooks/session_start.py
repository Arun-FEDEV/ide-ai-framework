#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd):
    try:
        return subprocess.check_output(
            cmd, cwd=cwd, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return ""


def git_root(cwd):
    root = run(["git", "rev-parse", "--show-toplevel"], cwd)
    return root or cwd


def git_branch(cwd):
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    return branch or "n/a"


def detect_project(cwd):
    if "/project-specific workspace" in cwd:
        return "project-specific workspace"
    if "project-specific workspace" in cwd or "project-specific workspace" in cwd.lower():
        return "project-specific workspace"
    if "project-gamma" in cwd.lower():
        return "project-specific workspace"
    return "General"


def list_agents():
    agents_dir = Path("<framework-home>/agents")
    if not agents_dir.exists():
        return []
    return sorted(p.stem for p in agents_dir.glob("*.toml"))


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()
    project = detect_project(cwd)
    root = git_root(cwd)
    branch = git_branch(cwd)
    agents = ", ".join(list_agents()) or "none"

    notes = [
        f"PROJECT: {project}",
        f"ROOT: {root}",
        f"BRANCH: {branch}",
        "INSTRUCTIONS: Codex is configured to treat CLAUDE.md as a project-doc fallback.",
        f"CUSTOM-AGENTS: {agents}",
        "SAFETY: destructive Bash commands and main-branch write ops are hook-guarded.",
        "DOCS: openaiDeveloperDocs MCP is configured for OpenAI and Codex questions.",
        "TELEMETRY: prompt routes, Bash activity, and turn outcomes are logged under ~/.codex/telemetry.",
        "REPORT: run `python3 ~/.codex/hooks/telemetry_report.py --days 7` to audit routing and verification patterns.",
    ]

    if project in {"project-specific workspace", "project-specific workspace", "project-specific workspace"}:
        notes.append(
            "PITFALLS: for non-trivial work, read ~/Obsidian/Coding/Mistakes/ or invoke $project-pitfalls."
        )

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(notes),
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
