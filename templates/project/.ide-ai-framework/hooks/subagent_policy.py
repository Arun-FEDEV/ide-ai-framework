#!/usr/bin/env python3
from __future__ import annotations

from common import append_event, hook_decision, read_payload, session_id, tool_name, utc_now, write_json


def main() -> int:
    payload = read_payload()
    event_name = payload.get("hook_event_name") or payload.get("hookEventName") or "Subagent"
    append_event(
        {
            "ts": utc_now(),
            "event": str(event_name),
            "session_id": session_id(payload),
            "tool_name": tool_name(payload),
        }
    )
    if str(event_name).lower().endswith("start"):
        write_json(hook_decision("Subagents require explicit user request for delegation or parallelism.", decision="ask"))
        return 0
    print('{"continue":true}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
