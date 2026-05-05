#!/usr/bin/env python3
from __future__ import annotations

from common import (
    append_event,
    command_from_payload,
    command_tags,
    cwd,
    read_payload,
    session_id,
    text_excerpt,
    tool_name,
    turn_id,
    update_state,
    utc_now,
)


def main() -> int:
    payload = read_payload()
    command = command_from_payload(payload)
    tags = command_tags(command) if command else ["other"]
    event = {
        "ts": utc_now(),
        "event": "post_tool_use",
        "session_id": session_id(payload),
        "turn_id": turn_id(payload),
        "cwd": cwd(payload),
        "tool_name": tool_name(payload),
        "command": text_excerpt(command, 500),
        "command_tags": tags,
    }
    append_event(event)

    def update(current: dict) -> dict:
        commands = list(current.get("commands") or [])
        commands.append(event)
        current["commands"] = commands[-25:]
        if any(tag in {"test", "e2e", "lint", "build"} for tag in tags):
            verification = list(current.get("verification_commands") or [])
            verification.append(command)
            current["verification_commands"] = verification[-12:]
        return current

    update_state("turn", turn_id(payload), update)
    print('{"continue":true}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
