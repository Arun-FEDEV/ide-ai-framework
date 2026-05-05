# Architecture

IDE AI Framework has three layers.

## Behavior Layer

Files copied into `.github`:

- `copilot-instructions.md` provides repo-wide behavior.
- `instructions/*.instructions.md` provides detailed context-engineering rules.
- `agents/*.agent.md` defines role-specific Copilot agents.
- `prompts/*.prompt.md` defines reusable workflows.

These files shape model behavior but are not deterministic enforcement.

Portable framework assets copied into `.ide-ai-framework`:

- `skills/index.json` and full skill directories provide the skill library.
- `agents/index.json` and `agents/*.md` provide client-neutral agent specs.
- `context-engineering/SKILL.md` and `context-engineering/references/*.md` provide the phase workflow.
- `compaction/context-engineering.md` provides the operational compaction prompt.
- `codex-parity/agents/*.toml`, `codex-parity/hooks/*.py`, and `codex-parity/compact-prompts/*.md` preserve the original Codex-style source assets that adapters can port from.

These assets let IDE and CLI adapters discover the same framework behavior even when they do not understand VS Code-specific `.github` files.

## Enforcement Layer

Files copied into `.ide-ai-framework/hooks`:

- `session_start.py`
- `smart_router.py`
- `pre_tool_use_policy.py`
- `post_tool_use_telemetry.py`
- `pre_compact.py`
- `subagent_policy.py`
- `stop_outcome_logger.py`
- `common.py`

These scripts are registered from `.github/hooks/ide-ai-framework.json`.

The hook scripts maintain session state under `IDE_AI_FRAMEWORK_HOME`, defaulting to `~/.ide-ai-framework`.

`smart_router.py` injects route context and recommended skill names from the installed skill registry semantics. `pre_compact.py` points the client to the compaction prompt.

The runtime hooks under `.ide-ai-framework/hooks` are VS Code adapter hooks. The fuller Codex-style source hooks are also installed under `.ide-ai-framework/codex-parity/hooks` so maintainers can compare behavior and build adapters for other clients.

## Proof Layer

The package has:

- Static verification in `scripts/verify.py`.
- Hook fixture tests under `tests`.
- Manual VS Code verification in `docs/vscode-verification.md`.

Manual VS Code verification is required before a public release because hook payloads and tool names are runtime integration details.
