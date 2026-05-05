#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from routing_miss_report import group_turns, load_events, score_turn
from telemetry_common import telemetry_root, utc_now, write_text_atomic


DEFAULT_ROUTER_FILE = Path("<framework-home>/hooks/smart_router.py")
PATCH_DIR_NAME = "router_patch_drafts"

STOPWORDS = {
    "about",
    "after",
    "agent",
    "agents",
    "api",
    "app",
    "apps",
    "appsapi",
    "appsweb",
    "<user>",
    "audit",
    "branch",
    "build",
    "change",
    "changes",
    "check",
    "checks",
    "continue",
    "code",
    "codex",
    "component",
    "components",
    "config",
    "control",
    "create",
    "current",
    "days",
    "debug",
    "diff",
    "edit",
    "file",
    "files",
    "fix",
    "fixed",
    "frontend",
    "hooks",
    "implement",
    "improve",
    "issue",
    "issues",
    "last",
    "local",
    "message",
    "next",
    "okay",
    "page",
    "patch",
    "please",
    "prompt",
    "read",
    "report",
    "review",
    "router",
    "routing",
    "run",
    "score",
    "short",
    "smart",
    "status",
    "summary",
    "telemetry",
    "test",
    "tests",
    "thanks",
    "today",
    "turn",
    "update",
    "updated",
    "verification",
    "web",
    "week",
    "weekly",
    "with",
    "work",
    "src",
    "tsx",
    "jsx",
    "roomid",
    "users",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a draft patch for smart_router.py from routing drift telemetry.")
    parser.add_argument("--days", type=int, default=7, help="Trailing days to include. Default: 7")
    parser.add_argument("--min-score", type=int, default=3, help="Minimum routing-miss score to include. Default: 3")
    parser.add_argument("--min-pair-count", type=int, default=2, help="Minimum repeated route-drift count required. Default: 2")
    parser.add_argument("--top-pairs", type=int, default=3, help="Maximum routed->observed pairs to convert into draft edits. Default: 3")
    parser.add_argument("--router-file", type=Path, default=DEFAULT_ROUTER_FILE, help="Router file to draft against.")
    return parser.parse_args()


def normalize_token(token: str) -> str:
    token = token.lower()
    token = token.replace("next.js", "nextjs")
    token = token.replace("web rtc", "webrtc")
    token = token.replace("socket.io", "socketio")
    token = re.sub(r"[^a-z0-9]+", "", token)
    return token


def extract_turn_tokens(turn: dict[str, Any]) -> set[str]:
    raw_parts = [
        turn.get("prompt_excerpt") or "",
        turn.get("message_excerpt") or "",
        " ".join(turn.get("commands") or []),
        " ".join(turn.get("file_refs") or []),
    ]
    tokens: set[str] = set()
    for raw in raw_parts:
        cleaned = re.sub(r"[/_:().\-\[\]]+", " ", raw)
        for piece in re.findall(r"[A-Za-z0-9+]{3,}", cleaned):
            normalized = normalize_token(piece)
            if not normalized:
                continue
            if normalized in STOPWORDS:
                continue
            if len(normalized) < 5 or normalized.isdigit():
                continue
            if re.search(r"\d", normalized):
                continue
            if not normalized.isalpha():
                continue
            tokens.add(normalized)
    return tokens


def existing_pattern_text(router_text: str) -> str:
    return router_text.lower()


def choose_tokens(turns: list[dict[str, Any]], router_text: str, routed_domain: str, observed_domain: str) -> list[str]:
    doc_counts: Counter[str] = Counter()
    for turn in turns:
        for token in extract_turn_tokens(turn):
            doc_counts[token] += 1

    min_docs = max(2, math.ceil(len(turns) * 0.6))
    domain_words = {
        routed_domain.replace("-", ""),
        observed_domain.replace("-", ""),
    }
    existing_text = existing_pattern_text(router_text)

    preferred_prefixes = {
        "frontend": ("booking", "lesson", "teacher", "student", "dashboard", "stripe", "room", "video"),
        "backend": ("webhook", "payment", "prisma", "booking", "teacher", "student", "stripe", "clerk", "api"),
        "debug": ("traceback", "crash", "panic", "regression", "hang"),
        "security": ("clerk", "secret", "token", "oauth", "permission"),
    }
    preferred = preferred_prefixes.get(observed_domain, ())

    scored: list[tuple[int, int, str]] = []
    for token, count in doc_counts.items():
        if count < min_docs:
            continue
        if token in domain_words:
            continue
        if token in existing_text:
            continue
        if token.endswith(("json", "yaml", "toml", "patch")):
            continue
        preference_score = 1 if any(token.startswith(prefix) for prefix in preferred) else 0
        scored.append((preference_score, count, token))

    scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return [token for _, _, token in scored[:6]]


def build_domain_insertions(router_text: str, selected_pairs: list[tuple[tuple[str, str], list[dict[str, Any]]]]) -> dict[str, list[str]]:
    per_domain: dict[str, list[str]] = defaultdict(list)
    for (routed_domain, observed_domain), turns in selected_pairs:
        tokens = choose_tokens(turns, router_text, routed_domain, observed_domain)
        if tokens:
            regex = r'\b(' + "|".join(re.escape(token) for token in tokens) + r')\b'
            per_domain[observed_domain].append(regex)
    return per_domain


def apply_insertions(router_text: str, insertions: dict[str, list[str]]) -> str:
    updated = router_text
    for domain, regexes in insertions.items():
        unique_regexes: list[str] = []
        for regex in regexes:
            if regex not in unique_regexes and regex not in updated:
                unique_regexes.append(regex)
        if not unique_regexes:
            continue

        domain_anchor = re.search(rf'\(\n\s*"{re.escape(domain)}",', updated)
        if not domain_anchor:
            continue
        anchor_start = domain_anchor.start()
        list_start = updated.find("[", domain_anchor.end())
        if list_start == -1:
            continue
        close_match = re.search(r"\],\n\s*\[", updated[list_start:])
        if not close_match:
            continue
        list_end = list_start + close_match.start()

        body = updated[list_start + 1 : list_end]
        current_patterns = re.findall(r'r"[^"]+"', body)
        additions = [f'r"{regex}"' for regex in unique_regexes if f'r"{regex}"' not in current_patterns]
        if not additions:
            continue

        all_patterns = current_patterns + additions
        list_text = "[\n" + "".join(f"            {item},\n" for item in all_patterns) + "        ]"
        updated = updated[:list_start] + list_text + updated[list_end + 1 :]
    return updated


def patch_paths() -> tuple[Path, Path, Path]:
    root = telemetry_root() / PATCH_DIR_NAME
    root.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    latest_patch = root / "latest-smart-router.patch"
    latest_summary = root / "latest-smart-router.md"
    stamped_patch = root / f"smart-router-{stamp}.patch"
    return latest_patch, latest_summary, stamped_patch


def summarize_pairs(selected_pairs: list[tuple[tuple[str, str], list[dict[str, Any]]]], insertions: dict[str, list[str]], patch_path: Path) -> str:
    lines = [
        "# Smart Router Draft Patch",
        "",
        f"- Generated: {utc_now()}",
        f"- Draft patch: `{patch_path}`",
        "",
        "## Repeated route drifts",
        "",
    ]
    for (routed, observed), turns in selected_pairs:
        lines.append(f"- `{routed} -> {observed}`: {len(turns)} turn(s)")
        sample = turns[0].get("prompt_excerpt") or ""
        lines.append(f"  Sample prompt: {sample[:160]}")
        if observed in insertions:
            lines.append(f"  Proposed regex additions: {', '.join(f'`{r}`' for r in insertions[observed])}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This patch is a draft only. Review the regex additions before applying them.",
            "- The suggester only proposes additive pattern changes. It does not rewrite scoring or strategy logic.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    events = load_events(args.days)
    turns = group_turns(events)
    scored = []
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for turn in turns.values():
        result = score_turn(turn)
        entry = {**turn, **result}
        scored.append(entry)
        routed = result.get("routed_domain")
        observed = result.get("observed_domain")
        if (
            result.get("score", 0) >= args.min_score
            and observed
            and routed
            and observed != routed
        ):
            by_pair[(routed, observed)].append(entry)

    selected_pairs = sorted(
        [
            (pair, entries)
            for pair, entries in by_pair.items()
            if len(entries) >= args.min_pair_count
        ],
        key=lambda item: (-len(item[1]), -(sum(int(e.get("score") or 0) for e in item[1]))),
    )[: args.top_pairs]

    print(f"Telemetry root: {telemetry_root()}")
    print(f"Window: last {args.days} day(s)")
    print(f"Turns analyzed: {len(turns)}")
    print(f"Repeated route drifts meeting threshold: {len(selected_pairs)}")
    print()

    if not selected_pairs:
        print("No repeated route drifts met the threshold. No draft patch written.")
        return

    router_text = args.router_file.read_text(encoding="utf-8")
    insertions = build_domain_insertions(router_text, selected_pairs)
    proposed = apply_insertions(router_text, insertions)

    if proposed == router_text:
        print("No safe additive regex suggestions were found. No draft patch written.")
        return

    diff = "".join(
        difflib.unified_diff(
            router_text.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile=str(args.router_file),
            tofile=str(args.router_file),
        )
    )

    latest_patch, latest_summary, stamped_patch = patch_paths()
    summary = summarize_pairs(selected_pairs, insertions, latest_patch)

    write_text_atomic(latest_patch, diff)
    write_text_atomic(stamped_patch, diff)
    write_text_atomic(latest_summary, summary)

    print(f"Wrote draft patch: {latest_patch}")
    print(f"Wrote timestamped patch: {stamped_patch}")
    print(f"Wrote summary: {latest_summary}")
    print()
    print("Top repeated drifts:")
    for (routed, observed), entries in selected_pairs:
        print(f"  {routed} -> {observed}: {len(entries)} turn(s)")
        if insertions.get(observed):
            print(f"    regex additions: {', '.join(insertions[observed])}")


if __name__ == "__main__":
    main()
