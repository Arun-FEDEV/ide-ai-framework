# Implementation Phase

Implementation follows the approved plan while adapting to codebase reality.

## Startup

- Read the approved plan before editing.
- Check which phases are already complete.
- Read files mentioned in the active phase before modifying them.
- Confirm active phase and success criteria.
- Implement one phase at a time unless the user explicitly grants broader autonomy.

## During Implementation

- Keep edits scoped to the active phase.
- Preserve existing codebase patterns unless the plan says otherwise.
- Update plan checkboxes only for completed automated work.
- Do not mark manual verification complete until the user confirms it.
- If context gets noisy, compact before continuing.

## Plan Mismatch

If reality does not match the plan, stop and present:

```md
Issue in Phase [N]:

Expected:
Found:
Why this matters:
Recommended next step:

How should I proceed?
```

## Progress Artifact

After automated verification, update `thoughts/shared/progress/YYYY-MM-DD-task.md` with:

- Plan path
- Phase completed
- Files changed
- Verification commands and results
- Decisions and deviations
- Blockers or remaining risks
- Next phase
- Whether the user must reply `confirmed: proceed`
