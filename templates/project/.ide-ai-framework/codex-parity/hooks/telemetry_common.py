#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Callable


MAX_TEXT = 400


def telemetry_root() -> Path:
    override = os.environ.get("CODEX_TELEMETRY_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".codex" / "telemetry"


def events_path() -> Path:
    return telemetry_root() / "events.jsonl"


def turns_dir() -> Path:
    return telemetry_root() / "turns"


def sessions_dir() -> Path:
    return telemetry_root() / "sessions"


def ensure_layout() -> None:
    root = telemetry_root()
    root.mkdir(parents=True, exist_ok=True)
    turns_dir().mkdir(parents=True, exist_ok=True)
    sessions_dir().mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _lock_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.lock")


def _excerpt(text: Any, max_len: int = MAX_TEXT) -> str:
    if text is None:
        return ""
    value = str(text).strip()
    if len(value) <= max_len:
        return value
    return value[: max_len - 1] + "…"


def compact_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def with_lock(path: Path, fn: Callable[[], Any]) -> Any:
    ensure_layout()
    lock_path = _lock_path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        return fn()


def write_text_atomic(path: Path, text: str) -> None:
    def _write() -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)

    with_lock(path, _write)


def append_event(event: dict[str, Any]) -> None:
    path = events_path()

    def _write() -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(compact_json(event))
            handle.write("\n")

    with_lock(path, _write)


def turn_state_path(turn_id: str) -> Path:
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", turn_id)
    return turns_dir() / f"{safe_id}.json"


def session_state_path(session_id: str) -> Path:
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", session_id)
    return sessions_dir() / f"{safe_id}.json"


def load_turn_state(turn_id: str) -> dict[str, Any]:
    path = turn_state_path(turn_id)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def update_turn_state(turn_id: str, updater: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    path = turn_state_path(turn_id)

    def _update() -> dict[str, Any]:
        current = {}
        if path.exists():
            try:
                current = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                current = {}
        updated = updater(current or {})
        updated.setdefault("turn_id", turn_id)
        updated.setdefault("updated_at", utc_now())
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tmp:
            json.dump(updated, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)
        return updated

    return with_lock(path, _update)


def load_session_state(session_id: str) -> dict[str, Any]:
    path = session_state_path(session_id)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def update_session_state(session_id: str, updater: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    path = session_state_path(session_id)

    def _update() -> dict[str, Any]:
        current = {}
        if path.exists():
            try:
                current = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                current = {}
        updated = updater(current or {})
        updated.setdefault("session_id", session_id)
        updated.setdefault("updated_at", utc_now())
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tmp:
            json.dump(updated, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)
        return updated

    return with_lock(path, _update)


def delete_turn_state(turn_id: str) -> None:
    path = turn_state_path(turn_id)

    def _delete() -> None:
        if path.exists():
            path.unlink()

    with_lock(path, _delete)


def sha1_short(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def command_tags(command: str) -> list[str]:
    tags: list[str] = []
    checks = [
        ("test", r"\b(pytest|jest|vitest|go test|cargo test|swift test|npm run test|pnpm test|yarn test)\b"),
        ("e2e", r"\b(playwright|cypress|test:e2e|e2e)\b"),
        ("lint", r"\b(eslint|ruff|mypy|npm run lint|pnpm lint|yarn lint|tsc\b)\b"),
        ("build", r"\b(next build|npm run build|pnpm build|yarn build|docker build|nest build)\b"),
        ("infra", r"\b(terraform|terragrunt|helm|kubectl|docker compose|docker build)\b"),
        ("git", r"\bgit\b"),
    ]
    lower = command.lower()
    for tag, pattern in checks:
        if re.search(pattern, lower):
            tags.append(tag)
    if not tags:
        tags.append("other")
    return tags


def parse_tool_response(raw: Any) -> dict[str, Any]:
    value = raw
    if isinstance(raw, str):
        stripped = raw.strip()
        if stripped:
            try:
                value = json.loads(stripped)
            except Exception:
                value = {"raw": _excerpt(stripped, 600)}
        else:
            value = {}

    if not isinstance(value, dict):
        return {"raw": _excerpt(value, 600)}

    exit_code = None
    for key in ("exit_code", "exitCode", "returncode", "return_code", "code"):
        candidate = value.get(key)
        if isinstance(candidate, int):
            exit_code = candidate
            break

    stdout = value.get("stdout")
    stderr = value.get("stderr")
    output = value.get("output")

    return {
        "exit_code": exit_code,
        "ok": (exit_code == 0) if isinstance(exit_code, int) else None,
        "stdout_excerpt": _excerpt(stdout),
        "stderr_excerpt": _excerpt(stderr),
        "output_excerpt": _excerpt(output),
        "keys": sorted(value.keys())[:20],
    }


def extract_file_refs(text: str) -> list[str]:
    matches = re.findall(r"\]\((/[^):]+(?::\d+)?)\)", text or "")
    return matches[:12]


def infer_message_summary(text: str) -> dict[str, Any]:
    lower = (text or "").lower()
    mentioned_commands = re.findall(r"`([^`]+)`", text or "")
    verification_claimed = bool(
        re.search(r"\b(test|tests|tested|verification|verified|validated|lint|build|playwright|pytest|jest|vitest)\b", lower)
    )
    unable_to_verify = bool(
        re.search(
            r"\b(could not run|couldn't run|unable to run|did not run|wasn't able to run|not run tests|not able to run)\b",
            lower,
        )
    )
    findings_mode = bool(re.search(r"\bfindings?\b", lower))
    return {
        "message_excerpt": _excerpt(text, 800),
        "verification_claimed": verification_claimed,
        "unable_to_verify": unable_to_verify,
        "findings_mode": findings_mode,
        "mentioned_commands": mentioned_commands[:10],
        "file_refs": extract_file_refs(text or ""),
    }
