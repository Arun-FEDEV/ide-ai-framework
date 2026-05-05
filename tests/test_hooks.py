from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "templates" / "project" / ".ide-ai-framework" / "hooks"


def run_hook(name: str, payload: dict, home: Path) -> dict:
    env = os.environ.copy()
    env["IDE_AI_FRAMEWORK_HOME"] = str(home)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        ["python3", str(HOOKS / name)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=ROOT,
        check=True,
    )
    return json.loads(result.stdout)


class HookTests(unittest.TestCase):
    def test_work_prompt_locks_local_tools_until_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            route = run_hook(
                "smart_router.py",
                {"session_id": "s1", "turn_id": "t1", "prompt": "please inspect this repo and fix setup"},
                home,
            )
            self.assertIn("SHARED-PICTURE-GATE: required", route["hookSpecificOutput"]["additionalContext"])

            denied = run_hook(
                "pre_tool_use_policy.py",
                {"session_id": "s1", "toolName": "terminal", "toolInput": {"command": "ls"}},
                home,
            )
            self.assertEqual("deny", denied["hookSpecificOutput"]["permissionDecision"])

            unlocked = run_hook(
                "smart_router.py",
                {"session_id": "s1", "turn_id": "t2", "prompt": "confirmed: proceed"},
                home,
            )
            self.assertIn("confirmed", unlocked["hookSpecificOutput"]["additionalContext"])

    def test_destructive_command_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            command = "git reset " + "--hard"
            denied = run_hook(
                "pre_tool_use_policy.py",
                {"session_id": "s2", "toolName": "terminal", "toolInput": {"command": command}},
                Path(tmp),
            )
            self.assertEqual("deny", denied["hookSpecificOutput"]["permissionDecision"])

    def test_configured_private_terms_are_absent(self) -> None:
        terms = [term for term in os.environ.get("IDE_AI_FRAMEWORK_BLOCKED_TERMS", "").split("|") if term]
        if not terms:
            self.skipTest("IDE_AI_FRAMEWORK_BLOCKED_TERMS is not set")
        text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        )
        for term in terms:
            self.assertNotIn(term.lower(), text.lower())


if __name__ == "__main__":
    unittest.main()
