#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys

from telemetry_common import (
    append_event,
    delete_turn_state,
    infer_message_summary,
    load_turn_state,
    update_session_state,
    utc_now,
)

NEXT_SHARED_PICTURE_PHASE = {
    "contract": "research",
    "research": "plan",
    "plan": "implementation",
    "implementation": "implementation",
    "verification": "implementation",
}


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"continue": True}))
        return

    turn_id = payload.get("turn_id")
    session_id = payload.get("session_id")
    cwd = payload.get("cwd") or os.getcwd()
    stop_hook_active = bool(payload.get("stop_hook_active"))
    last_message = payload.get("last_assistant_message") or ""

    state = load_turn_state(turn_id) if isinstance(turn_id, str) and turn_id else {}
    message_summary = infer_message_summary(last_message)

    event = {
        "ts": utc_now(),
        "event": "turn_stop",
        "session_id": session_id,
        "turn_id": turn_id,
        "cwd": cwd,
        "stop_hook_active": stop_hook_active,
        "route": {
            "project": state.get("project"),
            "complexity": state.get("complexity"),
            "domain": state.get("domain"),
            "strategy": state.get("strategy"),
            "turn_kind": state.get("turn_kind"),
            "phase": state.get("phase"),
            "recommended_agents": state.get("recommended_agents") or [],
            "recommended_skills": state.get("recommended_skills") or [],
        },
        "bash_tool_calls": int(state.get("bash_tool_calls") or 0),
        "verification_commands": state.get("verification_commands") or [],
        "message": message_summary,
        "prompt_excerpt": state.get("prompt_excerpt"),
    }
    append_event(event)

    if isinstance(session_id, str) and session_id:
        def _update_session(current: dict) -> dict:
            route = event["route"]
            next_phase = route.get("phase") or route.get("turn_kind") or current.get("phase")
            previous_phase = current.get("phase")
            current_phase_turns = int(current.get("phase_turns") or 0)
            current_phase_bash_calls = int(current.get("phase_bash_tool_calls") or 0)
            if next_phase and next_phase == previous_phase:
                phase_turns = current_phase_turns + 1
                phase_bash_calls = current_phase_bash_calls + int(event.get("bash_tool_calls") or 0)
            else:
                phase_turns = 1 if next_phase else 0
                phase_bash_calls = int(event.get("bash_tool_calls") or 0)
            current.update(
                {
                    "session_id": session_id,
                    "cwd": cwd,
                    "project": route.get("project"),
                    "complexity": route.get("complexity"),
                    "domain": route.get("domain"),
                    "strategy": route.get("strategy"),
                    "turn_kind": route.get("turn_kind"),
                    "phase": next_phase,
                    "phase_turns": phase_turns,
                    "phase_bash_tool_calls": phase_bash_calls,
                    "recommended_agents": route.get("recommended_agents") or [],
                    "recommended_skills": route.get("recommended_skills") or [],
                    "last_prompt_excerpt": event.get("prompt_excerpt") or current.get("last_prompt_excerpt"),
                    "last_message_excerpt": message_summary.get("message_excerpt") or current.get("last_message_excerpt"),
                    "last_bash_tool_calls": event.get("bash_tool_calls") or 0,
                    "updated_at": event["ts"],
                }
            )
            if current.get("shared_picture_gate") == "unlocked":
                completed_phase = current.get("shared_picture_phase") or current.get("shared_picture_next_phase") or "research"
                next_shared_phase = NEXT_SHARED_PICTURE_PHASE.get(completed_phase, "implementation")
                current["shared_picture_gate"] = "awaiting_contract"
                current["shared_picture_completed_phase"] = completed_phase
                current["shared_picture_phase"] = "contract"
                current["shared_picture_next_phase"] = next_shared_phase
                current["shared_picture_relocked_at"] = event["ts"]
                current["phase"] = "contract"
            return current

        update_session_state(session_id, _update_session)

    if isinstance(turn_id, str) and turn_id:
        delete_turn_state(turn_id)

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
