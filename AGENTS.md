# IDE AI Framework Contributor Instructions

This repository packages a Codex-style workflow for VS Code GitHub Copilot Chat.

## Non-Negotiables

- Keep the product generic. Do not hardcode maintainer-specific absolute paths into installable templates.
- Instructions are not enforcement. Deterministic blocking belongs in hooks and tests.
- Preserve the Shared-Picture Gate: work/action prompts require a contract and exact `confirmed: proceed`.
- Preserve phase boundaries: research, plan, implementation, verification, progress compaction.
- Do not claim parity for surfaces that cannot support it. Use the capability matrix.
- Use `rg` or `rg --files` before broad reads.
- Verify with the narrowest meaningful test before declaring success.
- Do not create GitHub repos, push, publish packages, or mutate issue/PR state without explicit approval.

## Product Shape

The repo must be installable by developers into their own project workspaces:

- Templates live under `templates/project`.
- Install logic lives under `scripts/install.py`.
- Hook scripts copied into projects must be standalone and avoid importing from this repo after installation.
- Documentation must distinguish VS Code Copilot Chat, Copilot CLI, cloud agents, and other clients.
