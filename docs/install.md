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
- Standalone hook scripts under `.ide-ai-framework/hooks`.

## Rollback

Remove:

- `.github/copilot-instructions.md`
- `.github/instructions/context-engineering.instructions.md`
- `.github/agents`
- `.github/prompts`
- `.github/hooks/ide-ai-framework.json`
- `.ide-ai-framework`

State and telemetry default to `~/.ide-ai-framework` and can be removed separately.
