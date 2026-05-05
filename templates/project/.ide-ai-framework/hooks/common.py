from __future__ import annotations

import datetime as dt
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Callable


CONFIRMATION_PHRASE = "confirmed: proceed"
DEFAULT_NEXT_PHASE = "research"


def control_home() -> Path:
    value = os.environ.get("IDE_AI_FRAMEWORK_HOME")
    if value:
        return Path(value).expanduser()
    return Path.home() / ".ide-ai-framework"


def telemetry_root() -> Path:
    return control_home() / "telemetry"


def sessions_dir() -> Path:
    return telemetry_root() / "sessions"


def turns_dir() -> Path:
    return telemetry_root() / "turns"


def events_path() -> Path:
    return telemetry_root() / "events.jsonl"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value or "default")


def read_payload() -> dict[str, Any]:
    try:
        data = json.load(__import__("sys").stdin)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, separators=(",", ":"), sort_keys=True))


def compact_json(value: dict[str, Any]) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as handle:
        handle.write(data)
        tmp = Path(handle.name)
    tmp.replace(path)


def append_event(event: dict[str, Any]) -> None:
    path = events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(compact_json(event))
        handle.write("\n")


def session_id(payload: dict[str, Any]) -> str:
    for key in ("session_id", "sessionId", "conversation_id", "conversationId"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return "default"


def turn_id(payload: dict[str, Any]) -> str:
    for key in ("turn_id", "turnId", "request_id", "requestId", "tool_use_id", "toolUseId"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return "default"


def tool_name(payload: dict[str, Any]) -> str:
    for key in ("tool_name", "toolName", "name", "tool"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    tool = payload.get("tool")
    if isinstance(tool, dict):
        name = tool.get("name")
        if isinstance(name, str):
            return name
    return ""


def tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("tool_input", "toolInput", "input", "arguments", "args"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def cwd(payload: dict[str, Any]) -> str:
    for key in ("cwd", "workspaceFolder", "workspace_folder"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def text_excerpt(value: Any, limit: int = 600) -> str:
    text = "" if value is None else str(value).strip()
    return text if len(text) <= limit else text[: limit - 1] + "..."


def normalize_prompt(prompt: str) -> str:
    return re.sub(r"\s+", " ", (prompt or "").strip().lower())


def is_confirmation(prompt: str) -> bool:
    return normalize_prompt(prompt) == CONFIRMATION_PHRASE


def extract_prompt(payload: dict[str, Any]) -> str:
    for key in ("prompt", "text", "input", "userMessage", "message"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    messages = payload.get("messages")
    if isinstance(messages, list):
        parts: list[str] = []
        for item in messages:
            if isinstance(item, dict):
                content = item.get("content")
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for piece in content:
                        if isinstance(piece, dict) and isinstance(piece.get("text"), str):
                            parts.append(piece["text"])
        if parts:
            return "\n".join(parts).strip()
    return ""


def state_path(kind: str, value: str) -> Path:
    base = sessions_dir() if kind == "session" else turns_dir()
    return base / f"{safe_id(value)}.json"


def load_state(kind: str, value: str) -> dict[str, Any]:
    path = state_path(kind, value)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def update_state(kind: str, value: str, updater: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    current = load_state(kind, value)
    updated = updater(current)
    updated.setdefault(f"{kind}_id", value)
    updated.setdefault("updated_at", utc_now())
    atomic_write(state_path(kind, value), json.dumps(updated, indent=2, sort_keys=True) + "\n")
    return updated


def command_from_payload(payload: dict[str, Any]) -> str:
    inp = tool_input(payload)
    for key in ("command", "cmd", "script", "input", "text"):
        value = inp.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    strings: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, str):
            strings.append(value)
        elif isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(inp)
    likely = [item for item in strings if any(token in item for token in ("git ", "npm ", "pnpm ", "python", "pytest", "rm "))]
    return likely[0].strip() if likely else (strings[0].strip() if strings else "")


def command_tags(command: str) -> list[str]:
    checks = [
        ("test", r"\b(pytest|jest|vitest|go test|cargo test|npm run test|pnpm test|yarn test)\b"),
        ("e2e", r"\b(playwright|cypress|test:e2e|e2e)\b"),
        ("lint", r"\b(eslint|ruff|mypy|npm run lint|pnpm lint|yarn lint|tsc\b)\b"),
        ("build", r"\b(next build|npm run build|pnpm build|yarn build|docker build)\b"),
        ("git", r"\bgit\b"),
    ]
    lower = command.lower()
    tags = [name for name, pattern in checks if re.search(pattern, lower)]
    return tags or ["other"]


def hook_context(event_name: str, context: str) -> dict[str, Any]:
    return {"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": context}}


def hook_decision(reason: str, decision: str = "deny") -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }
