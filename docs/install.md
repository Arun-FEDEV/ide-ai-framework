# Install

## Install Into A Workspace

```sh
python3 scripts/install.py --target /path/to/project
```

Dry run:

```sh
python3 scripts/install.py --target /path/to/project --dry-run
```

Overwrite existing control-plane files:

```sh
python3 scripts/install.py --target /path/to/project --force
```

## What Gets Installed

- Copilot instructions, agents, prompts, and hook registration under `.github`.
- Portable framework assets under `.ide-ai-framework`.
- Standalone hook scripts under `.ide-ai-framework/hooks`.
- Skill library under `.ide-ai-framework/skills`.
- Context-engineering workflow under `.ide-ai-framework/context-engineering`.
- Compaction prompt under `.ide-ai-framework/compaction`.
- Client-neutral agent specs under `.ide-ai-framework/agents`.
- Codex-parity source assets under `.ide-ai-framework/codex-parity`.

## Rollback

Remove:

- `.github/copilot-instructions.md`
- `.github/instructions/context-engineering.instructions.md`
- `.github/agents`
- `.github/prompts`
- `.github/hooks/ide-ai-framework.json`
- `.ide-ai-framework`

State and telemetry default to `~/.ide-ai-framework` and can be removed separately.
