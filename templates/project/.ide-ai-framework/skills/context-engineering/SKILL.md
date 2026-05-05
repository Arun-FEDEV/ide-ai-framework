---
name: context-engineering
description: Enforce the user's Dex-style coding workflow: shared-picture gate, research/plan/implement phases, durable artifacts, and smart compaction. Use when a prompt asks Codex to do work, inspect local project state, run commands, edit files, implement, fix, test, deploy, or change Codex/project setup.
---

# Context Engineering

## Start Every Work Request

Show a concise status line:

```text
MODE: Shared-picture gate
PHASE: Clarifying output contract
NEXT: Ask tailored question before local/project-state tools
```

Do not use local execution, repo file reads/searches, edits, tests, builds, deploys, GitHub mutations, or project-state MCP/app tools before the gate is confirmed. Web, OpenAI docs, and browser evidence lookup are allowed when they help ask better questions.

## Shared-Picture Grill

Ask one tailored question at a time. Each question must:

- State Codex's recommended interpretation and why.
- Ask about the tangible output or end state.
- Let the user agree, decline, or redirect.
- Avoid implementation trivia unless it changes the output.

Continue until you can state the contract. Then present:

```md
## Shared-Picture Contract

Goal:
Tangible output:
End state:
Out of scope:
Constraints/preferences:
Evidence gathered:
Risks/ambiguities:
Next phase to unlock:
Confirmation required:
Reply `confirmed: proceed` to unlock the next phase.
```

Only the exact phrase `confirmed: proceed` unlocks the next phase.

## Phase Workflow

Default phase order:

1. Research
2. Plan
3. Implementation
4. Verification
5. Progress compaction

Stop after research and stop after plan unless the user unlocks the next phase. Direct implementation is allowed only when the contract says the task is tiny and the user confirms it.

Load phase-specific guidance before starting each phase:

- Research: follow `references/research-phase.md`.
- Planning: follow `references/plan-phase.md`.
- Implementation: follow `references/implementation-phase.md`.

If a referenced phase file is missing, say so and treat that as a phase-boundary issue instead of silently improvising.

Use Dex-style artifacts for meaningful or multi-step work:

- `thoughts/shared/research/YYYY-MM-DD_HH-MM-SS_task.md`
- `thoughts/shared/plans/task.md`
- `thoughts/shared/progress/task.md`

For small work that does not need research or plan files, still document the decision, verification, and end state in chat. Use a progress artifact when the session becomes meaningful, multi-step, noisy, or likely to resume later.

After every verified implementation phase, update progress with files changed, verification command/result, decisions, blockers, and next phase.

## Smart Compaction

Compact whenever context gets noisy: broad search, long logs, large MCP/JSON output, failed approaches, phase switches, passed/failed verification, plan changes, context pressure, or the user asks to save state.

Preserve goal, contract, phase, decisions, relevant files/symbols/tests, verification evidence, blockers, and next action. Distill raw logs/MCP/JSON into the facts needed for the task; do not keep massive dumps as working context.
