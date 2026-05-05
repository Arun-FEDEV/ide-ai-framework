# Capability Matrix

This project targets multiple AI developer surfaces, but not all of them expose the same control points.

## VS Code GitHub Copilot Chat

Supported by this repo:

- Repository instructions via `.github/copilot-instructions.md`.
- Pattern instructions via `.github/instructions/*.instructions.md`.
- Custom agents via `.github/agents/*.agent.md`.
- Prompt files via `.github/prompts/*.prompt.md`.
- Hook-based enforcement via `.github/hooks/*.json`, where available.

Limitations:

- Hooks are a Preview VS Code capability and may change.
- Hook payload field names need real VS Code verification.
- Inline completions are not the same as Chat and should not be treated as fully governed by this workflow.

## Copilot CLI

Planned adapter target, not implemented in this scaffold.

Expected fallback:

- Use generated instruction files and manual prompts.
- Use shell-level guardrails or wrapper commands for deterministic blocking.

## GitHub Copilot Cloud Agents

Planned adapter target, not implemented in this scaffold.

Expected fallback:

- Use agent instruction files supported by the cloud agent.
- Do not assume VS Code local hooks run in cloud execution.

## Other AI Coding CLIs

Use this repo as a policy source and template library. Deterministic enforcement requires an adapter for that client's hook, permission, or wrapper model.
