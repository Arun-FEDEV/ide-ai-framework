---
name: context-engineering
description: Shared-Picture Gate, phased research/plan/implementation workflow, durable artifacts, verification, and compaction.
---

# Context Engineering

Use this skill for work/action requests: prompts that ask the assistant to inspect local project state, run commands, edit files, implement, fix, review setup, test, deploy, or otherwise act.

## Shared-Picture Gate

Before local/project-state tools:

1. State the recommended interpretation and why.
2. Ask one tailored output-focused question if the tangible result is unclear.
3. Present the Shared-Picture Contract.
4. Require exact `confirmed: proceed` to unlock the next phase.

## Contract Template

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

## Phase Order

1. Research
2. Plan
3. Implementation
4. Verification
5. Progress compaction

Stop after research and stop after plan unless the user explicitly unlocks the next phase.

## References

- `references/research-phase.md`
- `references/plan-phase.md`
- `references/implementation-phase.md`
- `references/verification-phase.md`
