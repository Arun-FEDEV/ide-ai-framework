#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED = [
    "README.md",
    "LICENSE",
    "AGENTS.md",
    "docs/capability-matrix.md",
    "docs/architecture.md",
    "docs/install.md",
    "docs/vscode-verification.md",
    "scripts/install.py",
    "templates/project/.github/copilot-instructions.md",
    "templates/project/.github/instructions/context-engineering.instructions.md",
    "templates/project/.github/hooks/ide-ai-framework.json",
    "templates/project/.github/prompts/compact.prompt.md",
    "templates/project/.ide-ai-framework/README.md",
    "templates/project/.ide-ai-framework/agents/index.json",
    "templates/project/.ide-ai-framework/skills/index.json",
    "templates/project/.ide-ai-framework/context-engineering/SKILL.md",
    "templates/project/.ide-ai-framework/context-engineering/references/research-phase.md",
    "templates/project/.ide-ai-framework/context-engineering/references/plan-phase.md",
    "templates/project/.ide-ai-framework/context-engineering/references/implementation-phase.md",
    "templates/project/.ide-ai-framework/context-engineering/references/verification-phase.md",
    "templates/project/.ide-ai-framework/compaction/context-engineering.md",
    "templates/project/.ide-ai-framework/hooks/common.py",
    "templates/project/.ide-ai-framework/hooks/smart_router.py",
    "templates/project/.ide-ai-framework/hooks/pre_tool_use_policy.py",
]


def frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path}: missing frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AssertionError(f"{path}: missing closing frontmatter")
    return text[4:end]


def main() -> int:
    missing = [item for item in EXPECTED if not (ROOT / item).exists()]
    if missing:
        raise SystemExit("missing files:\n" + "\n".join(missing))

    json.loads((ROOT / "templates/project/.github/hooks/ide-ai-framework.json").read_text(encoding="utf-8"))
    skill_index = json.loads((ROOT / "templates/project/.ide-ai-framework/skills/index.json").read_text(encoding="utf-8"))
    agent_index = json.loads((ROOT / "templates/project/.ide-ai-framework/agents/index.json").read_text(encoding="utf-8"))

    for path in (ROOT / "templates/project/.github/agents").glob("*.agent.md"):
        fm = frontmatter(path)
        for key in ("name:", "description:", "tools:", "agents: []"):
            if key not in fm:
                raise SystemExit(f"{path}: missing {key}")

    for path in (ROOT / "templates/project/.github/prompts").glob("*.prompt.md"):
        fm = frontmatter(path)
        for key in ("name:", "description:", "agent:"):
            if key not in fm:
                raise SystemExit(f"{path}: missing {key}")

    for item in skill_index.get("skills", []):
        rel = item.get("path")
        if not rel or not (ROOT / "templates/project/.ide-ai-framework" / rel).exists():
            raise SystemExit(f"skill registry points to missing path: {rel}")

    for item in agent_index.get("agents", []):
        rel = item.get("path")
        if not rel or not (ROOT / "templates/project/.ide-ai-framework/agents" / rel).exists():
            raise SystemExit(f"agent registry points to missing path: {rel}")

    if len(skill_index.get("skills", [])) < 20:
        raise SystemExit("skill registry is unexpectedly small")

    print("package verification ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
