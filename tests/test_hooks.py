from __future__ import annotations

import json
import os
import re
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
            self.assertIn("RECOMMENDED-SKILLS", route["hookSpecificOutput"]["additionalContext"])

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

    def test_skill_routing_recommends_tdd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            route = run_hook(
                "smart_router.py",
                {"session_id": "s3", "turn_id": "t1", "prompt": "use TDD to add this feature"},
                Path(tmp),
            )
            context = route["hookSpecificOutput"]["additionalContext"]
            self.assertIn("context-engineering", context)
            self.assertIn("tdd", context)

    def test_framework_assets_are_packaged(self) -> None:
        base = ROOT / "templates" / "project" / ".ide-ai-framework"
        expected = [
            base / "skills" / "index.json",
            base / "agents" / "index.json",
            base / "context-engineering" / "SKILL.md",
            base / "context-engineering" / "references" / "research-phase.md",
            base / "context-engineering" / "references" / "plan-phase.md",
            base / "context-engineering" / "references" / "implementation-phase.md",
            base / "context-engineering" / "references" / "verification-phase.md",
            base / "compaction" / "context-engineering.md",
            base / "codex-parity" / "hooks" / "smart_router.py",
            base / "codex-parity" / "hooks" / "pre_tool_use_policy.py",
            base / "codex-parity" / "agents" / "reviewer.toml",
            base / "codex-parity" / "compact-prompts" / "context-engineering.md",
            base / "skills" / "tdd" / "tests.md",
            base / "skills" / "github-triage" / "AGENT-BRIEF.md",
        ]
        for path in expected:
            self.assertTrue(path.exists(), str(path))
        skills = json.loads((base / "skills" / "index.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(skills["skills"]), 20)

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
            if term.isalpha() and term.upper() == term and len(term) <= 5:
                pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", re.IGNORECASE)
            else:
                pattern = re.compile(re.escape(term), re.IGNORECASE)
            self.assertIsNone(pattern.search(text), term)


if __name__ == "__main__":
    unittest.main()
