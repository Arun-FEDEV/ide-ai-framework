# Architecture

IDE AI Framework has three layers.

## Behavior Layer

Files copied into `.github`:

- `copilot-instructions.md` provides repo-wide behavior.
- `instructions/*.instructions.md` provides detailed context-engineering rules.
- `agents/*.agent.md` defines role-specific Copilot agents.
- `prompts/*.prompt.md` defines reusable workflows.

These files shape model behavior but are not deterministic enforcement.

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

## Proof Layer

The package has:

- Static verification in `scripts/verify.py`.
- Hook fixture tests under `tests`.
- Manual VS Code verification in `docs/vscode-verification.md`.

Manual VS Code verification is required before a public release because hook payloads and tool names are runtime integration details.
