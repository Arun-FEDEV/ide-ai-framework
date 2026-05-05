#!/usr/bin/env python3
from __future__ import annotations

from common import append_event, cwd, load_state, read_payload, session_id, text_excerpt, turn_id, update_state, utc_now


NEXT_PHASE = {
    "contract": "research",
    "research": "plan",
    "plan": "implementation",
    "implementation": "implementation",
    "verification": "implementation",
}


def main() -> int:
    payload = read_payload()
    sid = session_id(payload)
    tid = turn_id(payload)
    turn = load_state("turn", tid)
    session = load_state("session", sid)
    last_message = payload.get("last_assistant_message") or payload.get("lastAssistantMessage") or ""
    event = {
        "ts": utc_now(),
        "event": "turn_stop",
        "session_id": sid,
        "turn_id": tid,
        "cwd": cwd(payload),
        "phase": session.get("phase") or turn.get("phase"),
        "verification_commands": turn.get("verification_commands") or [],
        "message_excerpt": text_excerpt(last_message, 500),
    }
    append_event(event)

    def update(current: dict) -> dict:
        if current.get("shared_picture_gate") == "unlocked":
            completed = current.get("shared_picture_phase") or current.get("shared_picture_next_phase") or "research"
            current["shared_picture_completed_phase"] = completed
            current["shared_picture_gate"] = "awaiting_contract"
            current["shared_picture_phase"] = "contract"
            current["shared_picture_next_phase"] = NEXT_PHASE.get(completed, "implementation")
            current["phase"] = "contract"
            current["relocked_at"] = event["ts"]
        current["last_stop"] = event
        return current

    update_state("session", sid, update)
    print('{"continue":true}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
