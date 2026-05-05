#!/usr/bin/env python3
from __future__ import annotations

from common import hook_context, load_state, read_payload, session_id, write_json


def main() -> int:
    payload = read_payload()
    state = load_state("session", session_id(payload))
    context = "\n".join(
        [
            "CONTROL-PLANE COMPACTION:",
            f"phase: {state.get('phase', 'unknown')}",
            f"gate: {state.get('shared_picture_gate', 'unknown')}",
            f"next_phase: {state.get('shared_picture_next_phase', 'research')}",
            "preserve goal, contract, current phase, decisions, files, verification, blockers, and next action.",
        ]
    )
    write_json(hook_context("PreCompact", context))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
