# IDE AI Framework

A distributable Codex-style control plane for VS Code GitHub Copilot Chat.

The goal is to give teams the same working feel as a disciplined Codex setup:

- Shared-Picture Gate before local/project-state work.
- Exact `confirmed: proceed` phase unlocks.
- Research, plan, implementation, verification, and progress boundaries.
- Deterministic hook blocking for dangerous commands and protected-branch git writes.
- Repo-local Copilot instructions, agents, prompts, and hooks.
- Local telemetry for route, tool, verification, and outcome evidence.

## Status

This repo is an early public scaffold. VS Code hook support is Preview, so production use requires verification in a real VS Code Copilot Chat session before teams depend on the enforcement layer.

## Who This Is For

Developers and teams who want AI coding assistance to behave less like a free-form chat window and more like an accountable engineering workflow.

## Install Into A Project

From this repo:

```sh
python3 scripts/install.py --target /path/to/your/project
```

Dry run first:

```sh
python3 scripts/install.py --target /path/to/your/project --dry-run
```

The installer copies:

- `.github/copilot-instructions.md`
- `.github/instructions/context-engineering.instructions.md`
- `.github/agents/*.agent.md`
- `.github/prompts/*.prompt.md`
- `.github/hooks/ide-ai-framework.json`
- `.ide-ai-framework/skills/*`
- `.ide-ai-framework/agents/*`
- `.ide-ai-framework/context-engineering/*`
- `.ide-ai-framework/compaction/*`
- `.ide-ai-framework/hooks/*.py`

## Verify The Package

```sh
python3 scripts/verify.py
python3 -m unittest discover -s tests
```

Manual VS Code verification is still required. See `docs/vscode-verification.md`.

## What This Can And Cannot Enforce

See `docs/capability-matrix.md`.

Short version:

- VS Code Copilot Chat can load instructions, agents, prompt files, and hooks.
- Hooks can provide deterministic blocking where VS Code supports hook decisions.
- Inline suggestions do not reliably honor these workflow instructions.
- Other Copilot or AI CLIs need their own adapters if they do not support VS Code-style hooks.

## Repository Layout

```text
docs/                         Product docs and capability matrix
scripts/install.py             Installs templates into a target project
scripts/verify.py              Static package verification
templates/project/             Files copied into developer projects
templates/project/.github/     Copilot instructions, agents, prompts, hooks
templates/project/.ide-ai-framework/hooks/
                               Standalone hook scripts installed into projects
templates/project/.ide-ai-framework/skills/
                               Portable skill library and registry
templates/project/.ide-ai-framework/context-engineering/
                               Shared-Picture Gate and phase references
templates/project/.ide-ai-framework/compaction/
                               Operational compaction prompt
templates/project/.ide-ai-framework/agents/
                               Portable agent specs for other adapters
tests/                         Fixture tests for installable hooks
```

## Release Checklist

1. Run automated verification.
2. Install into a clean test workspace.
3. Confirm VS Code discovers instructions, agents, prompts, and hooks.
4. Confirm the Shared-Picture Gate blocks local/project-state tools before confirmation.
5. Confirm exact `confirmed: proceed` unlocks only one phase.
6. Confirm dangerous command and protected-branch git-write blocks.
7. Publish only after explicit approval.
