#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from collections import Counter
from typing import Any

from telemetry_common import telemetry_root
from telemetry_turns import group_turns, load_events


DOMAIN_PATTERNS: dict[str, list[str]] = {
    "analysis": [
        r"\b(setup|config|routing|router|hook|agents\.md|skill|plugin|automation|orchestration)\b",
    ],
    "security": [
        r"\b(security|auth|oauth|jwt|xss|csrf|inject|secret|permission|vulnerability)\b",
    ],
    "debug": [
        r"\b(debug|bug|broken|error|traceback|panic|crash|failing|regression|fix)\b",
    ],
    "architecture": [
        r"\b(architecture|migration|rewrite|redesign|multi-service|platform|system design)\b",
    ],
    "frontend": [
        r"\b(react|next\.?js|frontend|ui|ux|tailwind|css|tsx|jsx|component|browser|apps/web)\b",
    ],
    "backend": [
        r"\b(api|backend|fastapi|nestjs|prisma|sql|orm|service|webhook|apps/api|alembic)\b",
    ],
    "testing": [
        r"\b(test|tests|pytest|jest|vitest|playwright|coverage|integration test|e2e)\b",
    ],
    "git": [
        r"\b(git|branch|commit|rebase|merge|pull request|pr)\b",
    ],
    "performance": [
        r"\b(perf|performance|slow|latency|throughput|memory leak|bundle size|n\+1)\b",
    ],
    "openai-docs": [
        r"\b(openai|codex|mcp|responses api|agents sdk|gpt-5|chatgpt)\b",
    ],
}


COMMAND_TAG_DOMAIN_WEIGHTS = {
    "test": ("testing", 2),
    "e2e": ("testing", 2),
    "lint": ("testing", 1),
    "build": ("testing", 1),
    "infra": ("backend", 1),
    "git": ("git", 2),
}


FILE_REF_WEIGHTS = [
    (r"/apps/web/|\.tsx(?::\d+)?$", "frontend", 2),
    (r"/apps/api/|/prisma/|\.py(?::\d+)?$|\.sql(?::\d+)?$", "backend", 2),
]


VERIFICATION_REQUIRED_TURN_KINDS = {"implementation", "deploy"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report likely Codex routing misses.")
    parser.add_argument("--days", type=int, default=7, help="Trailing days to include. Default: 7")
    parser.add_argument(
        "--min-score",
        type=int,
        default=3,
        help="Minimum routing-miss score to report. Default: 3",
    )
    return parser.parse_args()


def score_observed_domains(turn: dict[str, Any]) -> dict[str, int]:
    scores = Counter()
    text_chunks = [
        turn.get("prompt_excerpt") or "",
        turn.get("message_excerpt") or "",
        " ".join(turn.get("commands") or []),
        " ".join(turn.get("file_refs") or []),
    ]
    text_blob = "\n".join(text_chunks).lower()

    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            scores[domain] += len(re.findall(pattern, text_blob))

    for tag in turn.get("command_tags") or []:
        if tag in COMMAND_TAG_DOMAIN_WEIGHTS:
            domain, weight = COMMAND_TAG_DOMAIN_WEIGHTS[tag]
            scores[domain] += weight

    for ref in turn.get("file_refs") or []:
        for pattern, domain, weight in FILE_REF_WEIGHTS:
            if re.search(pattern, ref.lower()):
                scores[domain] += weight

    return dict(scores)


def score_turn(turn: dict[str, Any]) -> dict[str, Any]:
    route = turn.get("route") or {}
    routed_domain = route.get("domain") or "unknown"
    observed_scores = score_observed_domains(turn)
    turn_kind = turn.get("turn_kind") or "analysis"
    if not observed_scores:
        return {
            "score": 0,
            "routed_domain": routed_domain,
            "observed_domain": None,
            "observed_scores": observed_scores,
            "reasons": [],
        }

    observed_domain, observed_score = max(observed_scores.items(), key=lambda item: item[1])
    routed_score = observed_scores.get(routed_domain, 0)
    reasons: list[str] = []
    score = 0
    verification_commands = turn.get("verification_commands") or []
    verification_required = turn_kind in VERIFICATION_REQUIRED_TURN_KINDS

    testing_is_supporting_signal = (
        observed_domain == "testing"
        and verification_commands
        and routed_domain in {"debug", "frontend", "backend", "security", "performance"}
        and routed_score >= max(2, observed_score - 2)
    )

    if (
        not testing_is_supporting_signal
        and observed_domain != routed_domain
        and observed_score >= max(2, routed_score + 2)
    ):
        delta = observed_score - routed_score
        score += min(4, 1 + delta)
        reasons.append(
            f"Observed domain `{observed_domain}` scored {observed_score} vs routed `{routed_domain}` at {routed_score}."
        )

    complexity = route.get("complexity")
    bash_tool_calls = int(turn.get("bash_tool_calls") or 0)
    if isinstance(complexity, int):
        if complexity <= 1 and bash_tool_calls >= 4:
            bump = 1 if bash_tool_calls < 7 else 2
            score += bump
            reasons.append(f"Complexity looked under-classified: routed L{complexity} but used {bash_tool_calls} Bash tool calls.")
        elif complexity >= 3 and bash_tool_calls == 0:
            score += 1
            reasons.append(f"Complexity may be over-classified: routed L{complexity} with no Bash activity recorded.")

    strategy = route.get("strategy")
    if strategy == "inline-first" and bash_tool_calls >= 6 and turn_kind in {"implementation", "deploy", "review"}:
        score += 1
        reasons.append("Strategy may be too optimistic: inline-first turn accumulated substantial command activity.")

    if routed_domain in {"analysis", "openai-docs"} and turn_kind in {"implementation", "deploy"} and observed_domain in {"frontend", "backend", "debug"} and observed_score >= 3:
        score += 1
        reasons.append("Routed as a meta/documentation task but execution signals look implementation-heavy.")

    if verification_required and (bash_tool_calls >= 4 or (isinstance(complexity, int) and complexity >= 2)):
        if not verification_commands:
            bump = 2 if turn_kind == "deploy" or bash_tool_calls >= 10 else 1
            score += bump
            reasons.append(f"{turn_kind.title()} turn ended without verification commands.")
            if turn.get("verification_claimed"):
                score += 1
                reasons.append("Verification was claimed, but no verification commands were recorded.")
        elif turn.get("unable_to_verify"):
            score += 1
            reasons.append(f"{turn_kind.title()} turn reported verification blockers.")

    return {
        "score": score,
        "routed_domain": routed_domain,
        "observed_domain": observed_domain,
        "observed_scores": observed_scores,
        "reasons": reasons,
    }


def analyze_turns(turns: list[dict[str, Any]], min_score: int) -> dict[str, Any]:
    scored = []
    pair_counts = Counter()
    project_counts = Counter()
    turn_kind_counts = Counter()
    for turn in turns:
        result = score_turn(turn)
        entry = {**turn, **result}
        scored.append(entry)
        if result["score"] >= min_score and result["observed_domain"]:
            pair_counts[(result["routed_domain"], result["observed_domain"])] += 1
            project_counts[turn.get("project") or "unknown"] += 1
            turn_kind_counts[turn.get("turn_kind") or "unknown"] += 1

    candidates = sorted(
        [item for item in scored if item["score"] >= min_score],
        key=lambda item: (-item["score"], item.get("ts") or "", item.get("turn_id") or ""),
    )
    domain_mismatch = sum(1 for item in candidates if item.get("observed_domain") and item["observed_domain"] != item["routed_domain"])
    same_domain = len(candidates) - domain_mismatch
    return {
        "scored": scored,
        "candidates": candidates,
        "pair_counts": pair_counts,
        "project_counts": project_counts,
        "turn_kind_counts": turn_kind_counts,
        "domain_mismatch": domain_mismatch,
        "same_domain": same_domain,
    }


def print_bucket(title: str, turns: list[dict[str, Any]], min_score: int, max_examples: int) -> None:
    analysis = analyze_turns(turns, min_score)
    candidates = analysis["candidates"]
    print(f"{title}:")
    print(f"  turns analyzed: {len(turns)}")
    print(f"  candidate misses (score >= {min_score}): {len(candidates)}")
    print(f"  domain mismatches: {analysis['domain_mismatch']}")
    print(f"  strategy/complexity misses: {analysis['same_domain']}")
    print()

    if analysis["pair_counts"]:
        print("  most common route drifts:")
        for (routed, observed), count in analysis["pair_counts"].most_common(8):
            print(f"    {routed} -> {observed}: {count}")
        print()

    if analysis["turn_kind_counts"]:
        print("  candidate misses by turn kind:")
        for kind, count in analysis["turn_kind_counts"].most_common(8):
            print(f"    {kind}: {count}")
        print()

    if analysis["project_counts"]:
        print("  candidate misses by project:")
        for project, count in analysis["project_counts"].most_common(8):
            print(f"    {project}: {count}")
        print()

    for item in candidates[:max_examples]:
        route = item.get("route") or {}
        print(
            f"  [score {item['score']}] {item.get('ts')} | {route.get('project') or 'unknown'} | "
            f"kind={item.get('turn_kind') or 'unknown'} | routed={item['routed_domain']} observed={item['observed_domain']} | "
            f"strategy={route.get('strategy') or 'unknown'} | bash_calls={item.get('bash_tool_calls') or 0}"
        )
        print(f"    Prompt: {(item.get('prompt_excerpt') or '')[:160]}")
        if item.get("message_excerpt"):
            print(f"    Final: {(item.get('message_excerpt') or '')[:160]}")
        for reason in item.get("reasons") or []:
            print(f"    Why: {reason}")
        if item.get("observed_scores"):
            top_scores = sorted(item["observed_scores"].items(), key=lambda pair: -pair[1])[:4]
            print("    Signals: " + ", ".join(f"{domain}={score}" for domain, score in top_scores))
        print()


def main() -> None:
    args = parse_args()
    events = load_events(args.days)
    turns = list(group_turns(events).values())
    human_turns = [turn for turn in turns if turn.get("source") == "human"]
    automation_turns = [turn for turn in turns if turn.get("source") == "automation"]

    print(f"Telemetry root: {telemetry_root()}")
    print(f"Window: last {args.days} day(s)")
    print(f"Turns analyzed: {len(turns)}")
    print(f"Human turns: {len(human_turns)}")
    print(f"Automation turns: {len(automation_turns)}")
    print()

    if not turns:
        print("No turn data recorded in the selected window.")
        return

    print_bucket("Human turns", human_turns, args.min_score, max_examples=12)
    print_bucket("Automation turns", automation_turns, args.min_score, max_examples=6)


if __name__ == "__main__":
    main()
