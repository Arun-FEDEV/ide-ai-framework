#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys

from telemetry_common import append_event, command_tags, parse_tool_response, update_turn_state, utc_now


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    turn_id = payload.get("turn_id")
    session_id = payload.get("session_id")
    cwd = payload.get("cwd") or os.getcwd()
    tool_name = payload.get("tool_name")
    tool_use_id = payload.get("tool_use_id")
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    response_summary = parse_tool_response(payload.get("tool_response"))
    tags = command_tags(command) if isinstance(command, str) and command.strip() else ["other"]

    event = {
        "ts": utc_now(),
        "event": "bash_post_tool",
        "session_id": session_id,
        "turn_id": turn_id,
        "cwd": cwd,
        "tool_name": tool_name,
        "tool_use_id": tool_use_id,
        "command": command,
        "command_tags": tags,
        "response": response_summary,
    }
    append_event(event)

    if isinstance(turn_id, str) and turn_id:
        def _update(state: dict) -> dict:
            commands = list(state.get("commands") or [])
            commands.append(
                {
                    "command": command,
                    "tags": tags,
                    "response": response_summary,
                    "tool_use_id": tool_use_id,
                    "ts": event["ts"],
                }
            )
            verification_commands = list(state.get("verification_commands") or [])
            if any(tag in {"test", "e2e", "lint", "build"} for tag in tags):
                verification_commands.append(command)

            state["commands"] = commands[-25:]
            state["verification_commands"] = verification_commands[-12:]
            state["bash_tool_calls"] = int(state.get("bash_tool_calls") or 0) + 1
            state["last_command"] = command
            state["last_command_tags"] = tags
            state["updated_at"] = event["ts"]
            return state

        update_turn_state(turn_id, _update)


if __name__ == "__main__":
    main()
