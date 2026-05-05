# IDE AI Framework

Mirror the Codex working style for GitHub Copilot Chat in this workspace.

## Operating Rules

- For work/action requests, complete the Shared-Picture Gate before local/project-state tools, edits, tests, builds, deployments, or GitHub mutations.
- Ask tailored output-focused questions one at a time until the tangible result is clear.
- Present a Shared-Picture Contract and require exact `confirmed: proceed` before the next phase.
- `confirmed: proceed` unlocks only one phase. Default phase order: research, plan, implementation, verification, progress compaction.
- Stop after research and stop after plan unless the user explicitly unlocks the next phase.
- Use `rg` or `rg --files` before broad reads.
- Prefer repo-local patterns and narrow changes.
- Verify with the narrowest meaningful automated check before declaring success.
- Never imply manual VS Code/GitHub verification is complete unless the user confirms it.
- Do not spawn subagents, delegate, or run parallel agent work unless the user explicitly asks for delegation, parallelism, or one-agent-per-point workflows.
- Do not push, create PRs/issues, mutate labels/comments, deploy, or change global/user-level Copilot settings without explicit immediate approval.
- Never commit on `main` or `master`.

## Enforcement

Instructions shape behavior but do not provide deterministic blocking. The hook layer planned for this workspace is responsible for hard blocks, protected-branch policy, phase relocking, and telemetry.

Until hooks are installed and verified, treat these instructions as binding workflow rules and state clearly when enforcement has not been proven in VS Code.
