# Implementation Phase

Implementation follows the approved plan while adapting to codebase reality. The plan is the contract, not a suggestion to ignore.

## Startup

- Read the approved plan fully before editing.
- Check which phases are already complete.
- Read all files mentioned in the active phase before modifying them.
- Confirm the active phase and success criteria.
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

Do not push through a mismatch silently.

## Verification

After implementation:

- Run the active phase's automated verification.
- Fix failures that are clearly inside the phase scope.
- If a failure indicates the plan is wrong or scope is larger than expected, stop with a plan mismatch.
- Record exact commands and results in the progress artifact.

## Progress Update

After automated verification, update `thoughts/shared/progress/...` with:

- plan path
- phase completed
- files changed
- verification commands and results
- decisions and deviations
- blockers or remaining risks
- next phase
- whether the user must reply `confirmed: proceed`

## Phase Boundary

Pause after verified phase completion. Tell the user what passed, what still needs manual review, and the exact next phase.
