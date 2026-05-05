# Plan Phase

Planning turns research into an implementation contract.

## Rules

- Use current codebase evidence and research artifacts as the source of truth.
- Ask only questions that cannot be answered through code or document investigation.
- Do not write a final plan with unresolved open questions.
- Make every decision needed for implementation before finalizing.
- Keep phases incremental and independently verifiable.
- Separate automated verification from manual verification.
- Include what is out of scope to prevent drift.

## Artifact

Write meaningful plans to `thoughts/shared/plans/YYYY-MM-DD-task.md`.

Use this structure:

```md
# [Task] Implementation Plan

## Overview
## Current State Analysis
## Desired End State
## Key Discoveries
## What We Are Not Doing
## Implementation Approach
## Phase 1: [Name]
### Overview
### Changes Required
### Success Criteria
#### Automated Verification
#### Manual Verification
### Phase Boundary
## Testing Strategy
## Performance Considerations
## Migration And Rollback Notes
## References
```

Stop after the plan and require `confirmed: proceed` before implementation.
