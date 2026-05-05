#!/usr/bin/env python3
from __future__ import annotations

import re

from common import (
    DEFAULT_NEXT_PHASE,
    append_event,
    cwd,
    extract_prompt,
    hook_context,
    is_confirmation,
    load_state,
    normalize_prompt,
    read_payload,
    session_id,
    text_excerpt,
    turn_id,
    update_state,
    utc_now,
    write_json,
)


WORK_ACTION_RE = re.compile(
    r"\b(implement|build|create|add|update|change|edit|modify|fix|patch|set up|configure|install|"
    r"remove|delete|refactor|migrate|deploy|run|test|verify|inspect|look at|audit|review|debug|"
    r"investigate|research|enforce|apply|ship|improve)\b"
)


def complexity(prompt: str) -> int:
    text = normalize_prompt(prompt)
    if len(text.split()) <= 12 and re.search(r"\b(typo|rename|format|one line|small fix)\b", text):
        return 0
    if re.search(r"\b(plan first|architecture|migration|rewrite|platform|end-to-end|deploy|automation)\b", text):
        return 3
    if WORK_ACTION_RE.search(text):
        return 2
    return 1


def domain(prompt: str) -> str:
    text = normalize_prompt(prompt)
    checks = [
        ("security", r"\b(security|auth|jwt|xss|csrf|secret|permission|vulnerability)\b"),
        ("debug", r"\b(debug|bug|broken|error|traceback|crash|failing|regression)\b"),
        ("frontend", r"\b(react|next|frontend|ui|ux|css|component|browser|responsive)\b"),
        ("backend", r"\b(api|backend|database|sql|service|stripe|webhook|worker)\b"),
        ("git", r"\b(git|github|branch|commit|rebase|push|pull request|merge)\b"),
        ("testing", r"\b(test|pytest|vitest|jest|coverage|e2e|playwright)\b"),
    ]
    for name, pattern in checks:
        if re.search(pattern, text):
            return name
    return "general"


def is_work_action(prompt: str) -> bool:
    if is_confirmation(prompt):
        return False
    return bool(WORK_ACTION_RE.search(normalize_prompt(prompt)))


def main() -> int:
    payload = read_payload()
    prompt = extract_prompt(payload)
    sid = session_id(payload)
    tid = turn_id(payload)
    state = load_state("session", sid)
    next_phase = state.get("shared_picture_next_phase") or DEFAULT_NEXT_PHASE

    level = complexity(prompt)
    dom = domain(prompt)
    gate = "idle"
    phase = state.get("phase") or "analysis"

    if is_confirmation(prompt):
        gate = "unlocked"
        phase = next_phase
        context = "\n".join(
            [
                f"ROUTE: L{level} | workspace | {dom}",
                "STRATEGY: inline-first",
                f"TURN-KIND: {phase}",
                "AGENT-POLICY: stay inline unless the user explicitly asks for delegation or parallel agents.",
                f"SHARED-PICTURE-GATE: confirmed; `{next_phase}` phase is unlocked for this turn only.",
                "PHASE-BOUNDARY: stop after this phase and request `confirmed: proceed` before the next phase.",
            ]
        )
    elif is_work_action(prompt):
        gate = "awaiting_contract"
        phase = "contract"
        context = "\n".join(
            [
                f"ROUTE: L{level} | workspace | {dom}",
                "STRATEGY: inline-first",
                "TURN-KIND: implementation",
                "AGENT-POLICY: stay inline unless the user explicitly asks for delegation or parallel agents.",
                "SHARED-PICTURE-GATE: required before local/project-state tools for this work/action request.",
                "CONFIRMATION: ask tailored output-focused questions one at a time, present a Shared-Picture Contract, then require exact `confirmed: proceed`.",
                f"NEXT-PHASE: `{next_phase}` unless the contract explicitly says direct implementation is appropriate.",
            ]
        )
    else:
        context = f"ROUTE: L{level} | workspace | {dom}\nSTRATEGY: inline-first"

    event = {
        "ts": utc_now(),
        "event": "prompt_submit",
        "session_id": sid,
        "turn_id": tid,
        "cwd": cwd(payload),
        "complexity": level,
        "domain": dom,
        "shared_picture_gate": gate,
        "phase": phase,
        "prompt_excerpt": text_excerpt(prompt, 300),
    }
    append_event(event)

    def update(current: dict) -> dict:
        current.update(event)
        current["shared_picture_gate"] = gate
        current["phase"] = phase
        if gate == "unlocked":
            current["shared_picture_phase"] = next_phase
        elif gate == "awaiting_contract":
            current["shared_picture_phase"] = "contract"
            current["shared_picture_next_phase"] = next_phase
        return current

    update_state("session", sid, update)
    update_state("turn", tid, lambda current: {**current, **event})

    write_json(hook_context("UserPromptSubmit", context))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
