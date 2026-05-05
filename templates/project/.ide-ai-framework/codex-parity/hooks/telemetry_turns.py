#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter
from typing import Any

from telemetry_common import events_path


TURN_KIND_PATTERNS: dict[str, list[str]] = {
    "review": [
        r"\b(review findings|code review|review\b|audit\b|critique|sign[- ]?off|double check)\b",
    ],
    "deploy": [
        r"\b(deploy|deployment|production|prod\b|release|publish|go live|push live|app store|submission|vercel deploy|railway rebuild)\b",
    ],
    "docs": [
        r"\b(docs?|documentation|readme|agents\.md|claude\.md|architecture doc|design doc|runbook|playbook|guide)\b",
    ],
    "implementation": [
        r"\b(implement|implementation|build|create|wire up|set up|refactor|fix|patch|add|change|update|continue|proceed|go ahead)\b",
    ],
    "analysis": [
        r"\b(plan|blueprint|spec\b|explain|assess|evaluate|re-?evaluate|compare|what'?s left|round up)\b",
    ],
}


IMPLEMENTATION_DOMAINS = {"frontend", "backend", "debug", "security", "performance", "testing"}
DOCS_DOMAINS = {"openai-docs"}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def load_events(days: int) -> list[dict[str, Any]]:
    path = events_path()
    if not path.exists():
        return []
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except Exception:
            continue
        ts = event.get("ts")
        try:
            when = dt.datetime.fromisoformat(ts)
        except Exception:
            continue
        if when >= cutoff:
            events.append(event)
    return events


def is_automation_prompt(prompt_excerpt: str) -> bool:
    return normalize_text(prompt_excerpt).startswith("automation:")


def classify_turn_kind_from_prompt(prompt: str, domain: str | None = None, session_state: dict[str, Any] | None = None) -> str:
    text = normalize_text(prompt)
    if not text:
        if isinstance(session_state, dict):
            return session_state.get("phase") or session_state.get("turn_kind") or "analysis"
        return "analysis"

    scores = Counter()
    for kind, patterns in TURN_KIND_PATTERNS.items():
        for pattern in patterns:
            scores[kind] += len(re.findall(pattern, text))

    if domain in IMPLEMENTATION_DOMAINS:
        scores["implementation"] += 1
    elif domain in DOCS_DOMAINS:
        scores["docs"] += 1
    elif domain == "analysis":
        scores["analysis"] += 1

    if not scores:
        return "analysis"

    order = ["review", "deploy", "docs", "implementation", "analysis"]
    return max(order, key=lambda kind: (scores[kind], -order.index(kind)))


def _markdown_ref_count(file_refs: list[str]) -> int:
    return sum(1 for ref in file_refs if ref.lower().endswith(".md") or ".md:" in ref.lower())


def classify_turn_kind(turn: dict[str, Any]) -> str:
    route = turn.get("route") or {}
    existing = route.get("turn_kind")
    if isinstance(existing, str) and existing:
        return existing

    if turn.get("findings_mode"):
        return "review"

    prompt_excerpt = turn.get("prompt_excerpt") or ""
    message_excerpt = turn.get("message_excerpt") or ""
    text_blob = "\n".join(
        [
            prompt_excerpt,
            message_excerpt,
            " ".join(turn.get("commands") or []),
            " ".join(turn.get("file_refs") or []),
        ]
    )
    text = normalize_text(text_blob)
    scores = Counter()
    for kind, patterns in TURN_KIND_PATTERNS.items():
        for pattern in patterns:
            scores[kind] += len(re.findall(pattern, text))

    routed_domain = route.get("domain")
    if routed_domain in IMPLEMENTATION_DOMAINS:
        scores["implementation"] += 2
    elif routed_domain in DOCS_DOMAINS:
        scores["docs"] += 2
    elif routed_domain == "analysis":
        scores["analysis"] += 1

    if turn.get("verification_commands"):
        scores["implementation"] += 1

    if _markdown_ref_count(turn.get("file_refs") or []) >= 2 and routed_domain not in IMPLEMENTATION_DOMAINS:
        scores["docs"] += 2

    if routed_domain == "git" and not scores["deploy"] and not scores["review"]:
        scores["analysis"] += 1

    order = ["review", "deploy", "docs", "implementation", "analysis"]
    return max(order, key=lambda kind: (scores[kind], -order.index(kind))) if scores else "analysis"


def group_turns(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    turns: dict[str, dict[str, Any]] = {}
    for event in events:
        turn_id = event.get("turn_id")
        if not isinstance(turn_id, str) or not turn_id:
            continue
        turn = turns.setdefault(
            turn_id,
            {
                "turn_id": turn_id,
                "project": None,
                "route": {},
                "prompt_excerpt": "",
                "message_excerpt": "",
                "verification_commands": [],
                "command_tags": [],
                "commands": [],
                "file_refs": [],
                "bash_tool_calls": 0,
                "ts": event.get("ts"),
                "is_automation": False,
                "findings_mode": False,
                "verification_claimed": False,
                "unable_to_verify": False,
                "turn_kind": None,
                "phase": None,
            },
        )

        turn["ts"] = event.get("ts") or turn["ts"]

        if event.get("event") == "prompt_submit":
            turn["project"] = event.get("project") or turn["project"]
            turn["route"] = {
                "project": event.get("project"),
                "complexity": event.get("complexity"),
                "domain": event.get("domain"),
                "strategy": event.get("strategy"),
                "turn_kind": event.get("turn_kind"),
                "phase": event.get("phase"),
            }
            turn["prompt_excerpt"] = event.get("prompt_excerpt") or turn["prompt_excerpt"]
            turn["is_automation"] = is_automation_prompt(turn["prompt_excerpt"])

        elif event.get("event") == "bash_post_tool":
            turn["commands"].append(event.get("command") or "")
            turn["command_tags"].extend(event.get("command_tags") or [])
            turn["bash_tool_calls"] = int(turn.get("bash_tool_calls") or 0) + 1

        elif event.get("event") == "turn_stop":
            route = event.get("route") or {}
            if route:
                turn["route"] = route
            turn["project"] = route.get("project") or turn["project"]
            message = event.get("message") or {}
            turn["message_excerpt"] = message.get("message_excerpt") or turn["message_excerpt"]
            turn["verification_commands"] = event.get("verification_commands") or turn["verification_commands"]
            turn["file_refs"].extend(message.get("file_refs") or [])
            turn["bash_tool_calls"] = int(event.get("bash_tool_calls") or turn.get("bash_tool_calls") or 0)
            turn["findings_mode"] = bool(message.get("findings_mode"))
            turn["verification_claimed"] = bool(message.get("verification_claimed"))
            turn["unable_to_verify"] = bool(message.get("unable_to_verify"))
            if not turn["prompt_excerpt"]:
                turn["prompt_excerpt"] = event.get("prompt_excerpt") or ""
                turn["is_automation"] = is_automation_prompt(turn["prompt_excerpt"])

    for turn in turns.values():
        turn["turn_kind"] = classify_turn_kind(turn)
        route = turn.get("route") or {}
        turn["phase"] = route.get("phase") or turn["turn_kind"]
        route["turn_kind"] = route.get("turn_kind") or turn["turn_kind"]
        route["phase"] = route.get("phase") or turn["phase"]
        turn["source"] = "automation" if turn.get("is_automation") else "human"

    return turns

