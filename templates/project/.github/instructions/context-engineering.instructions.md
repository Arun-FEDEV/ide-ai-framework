---
applyTo: "**/*"
---

# Context Engineering

Use this workflow for work/action prompts: requests to inspect local project state, run commands, edit files, implement, fix, review setup, test, deploy, or otherwise act.

## Shared-Picture Gate

Before local/project-state tools or edits:

1. State the recommended interpretation and why.
2. Ask one tailored output-focused question.
3. Continue only until the tangible result is clear.
4. Present this contract:

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

Default phases:

1. Research
2. Plan
3. Implementation
4. Verification
5. Progress compaction

Stop after research and stop after plan unless the user explicitly unlocks the next phase. Direct implementation is allowed only when the contract says the task is tiny and the user confirms it.

## Durable Artifacts

For meaningful or multi-step work, write durable artifacts:

- Research: `thoughts/shared/research/YYYY-MM-DD_HH-MM-SS_task.md`
- Plans: `thoughts/shared/plans/YYYY-MM-DD-task.md`
- Progress: `thoughts/shared/progress/YYYY-MM-DD-task.md`

After every verified implementation phase, update progress with:

- Plan path
- Phase completed
- Files changed
- Verification commands and results
- Decisions and deviations
- Blockers or remaining risks
- Next phase
- Whether the user must reply `confirmed: proceed`

## Verification

Use the narrowest meaningful automated check. Do not mark manual verification complete until the user confirms it. If the check cannot be run, say so directly and preserve the remaining risk.

## Compaction

When context is noisy, preserve only: goal, contract, current phase, decisions, relevant files, verification evidence, blockers, and next action. Distill raw logs and large tool output.
