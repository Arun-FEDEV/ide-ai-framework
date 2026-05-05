#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import Counter
from typing import Any

from telemetry_common import telemetry_root
from telemetry_turns import group_turns, load_events


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize Codex telemetry events.")
    parser.add_argument("--days", type=int, default=7, help="Trailing days to include. Default: 7")
    return parser.parse_args()


def print_section(title: str, turns: list[dict[str, Any]]) -> None:
    print(f"{title}:")
    print(f"  turns: {len(turns)}")
    if not turns:
        print()
        return

    project_counts = Counter((turn.get("project") or "unknown") for turn in turns)
    domain_counts = Counter(((turn.get("route") or {}).get("domain") or "unknown") for turn in turns)
    strategy_counts = Counter(((turn.get("route") or {}).get("strategy") or "unknown") for turn in turns)
    turn_kind_counts = Counter((turn.get("turn_kind") or "unknown") for turn in turns)
    tag_counts = Counter(tag for turn in turns for tag in (turn.get("command_tags") or []))

    print("  projects:")
    for name, count in project_counts.most_common(8):
        print(f"    {name}: {count}")

    print("  domains:")
    for name, count in domain_counts.most_common(8):
        print(f"    {name}: {count}")

    print("  turn kinds:")
    for name, count in turn_kind_counts.most_common(8):
        print(f"    {name}: {count}")

    print("  strategies:")
    for name, count in strategy_counts.most_common(8):
        print(f"    {name}: {count}")

    print("  command tags:")
    for name, count in tag_counts.most_common(8):
        print(f"    {name}: {count}")

    implementation_or_deploy = [turn for turn in turns if turn.get("turn_kind") in {"implementation", "deploy"}]
    claimed = sum(1 for turn in turns if turn.get("verification_claimed"))
    recorded = sum(1 for turn in turns if turn.get("verification_commands"))
    unable = sum(1 for turn in turns if turn.get("unable_to_verify"))
    required_recorded = sum(1 for turn in implementation_or_deploy if turn.get("verification_commands"))
    required_missing = [turn for turn in implementation_or_deploy if not turn.get("verification_commands")]

    print("  verification:")
    print(f"    stop messages claiming verification: {claimed}")
    print(f"    turns with verification commands recorded: {recorded}")
    print(f"    stop messages admitting unverified work: {unable}")
    print(f"    implementation/deploy turns: {len(implementation_or_deploy)}")
    print(f"    implementation/deploy turns with verification commands: {required_recorded}")
    print(f"    implementation/deploy turns missing verification commands: {len(required_missing)}")

    print("  recent implementation/deploy turns without verification commands:")
    for turn in sorted(required_missing, key=lambda item: item.get("ts") or "", reverse=True)[:8]:
        route = turn.get("route") or {}
        print(
            f"    {turn.get('ts')} | {route.get('project') or 'unknown'} | "
            f"{turn.get('turn_kind') or 'unknown'} | {route.get('domain') or 'unknown'} | "
            f"{(turn.get('prompt_excerpt') or '')[:90]}"
        )
    print()


def main() -> None:
    args = parse_args()
    events = load_events(args.days)
    turns = list(group_turns(events).values())

    print(f"Telemetry root: {telemetry_root()}")
    print(f"Window: last {args.days} day(s)")
    print(f"Events: {len(events)}")
    print(f"Turns: {len(turns)}")
    print()

    if not turns:
        print("No turn data recorded in the selected window.")
        return

    prompts = sum(1 for event in events if event.get("event") == "prompt_submit")
    stops = sum(1 for event in events if event.get("event") == "turn_stop")
    bash = sum(1 for event in events if event.get("event") == "bash_post_tool")

    print(f"Prompt submits: {prompts}")
    print(f"Turn stops: {stops}")
    print(f"Bash post-tool events: {bash}")
    print()

    human_turns = [turn for turn in turns if turn.get("source") == "human"]
    automation_turns = [turn for turn in turns if turn.get("source") == "automation"]

    print("Turn sources:")
    print(f"  human: {len(human_turns)}")
    print(f"  automation: {len(automation_turns)}")
    print()

    print_section("Human turns", human_turns)
    print_section("Automation turns", automation_turns)


if __name__ == "__main__":
    main()
