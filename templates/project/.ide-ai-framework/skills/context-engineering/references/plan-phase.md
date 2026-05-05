# Plan Phase

Planning turns research into an implementation contract. Be skeptical, concrete, and collaborative.

## Rules

- Use current codebase evidence and research artifacts as the source of truth.
- Ask only questions that cannot be answered through code or document investigation.
- If the user corrects a misunderstanding, verify it against the code before finalizing the plan.
- Do not write a final plan with unresolved open questions.
- Make every decision needed for implementation before finalizing.
- Keep phases incremental and independently verifiable.
- Separate automated verification from manual verification.
- Include "what we are not doing" to prevent scope creep.

## Plan Document

Write meaningful plans to `thoughts/shared/plans/YYYY-MM-DD-task.md` or the repo's established `thoughts/shared/plans/...` naming pattern.

Use this structure:

```md
# [Task] Implementation Plan

## Overview

## Current State Analysis

## Desired End State

## Key Discoveries

- `path/file.ext:line` - Relevant fact or pattern.

## What We Are Not Doing

## Implementation Approach

## Phase 1: [Name]

### Overview

### Changes Required

#### [Component Or File Group]

File: `path/file.ext`
Changes:

### Success Criteria

#### Automated Verification

- [ ] Command or check:

#### Manual Verification

- [ ] Human check, if relevant:

### Phase Boundary

Stop after this phase unless the user explicitly grants broader autonomy.

## Testing Strategy

## Performance Considerations

## Migration And Rollback Notes

## References
```

## Final Plan Gate

Before implementation, confirm:

- no unresolved open questions remain
- each phase has clear edit targets
- each phase has success criteria
- verification is split into automated and manual checks
- the next phase requires `confirmed: proceed`
