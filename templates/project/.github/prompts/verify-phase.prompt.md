---
name: verify-phase
description: Run narrow verification for the current completed implementation phase.
agent: "Control Plane"
tools: ["search/codebase", "search", "runCommands", "problems", "changes"]
---

Verify the current implementation phase with the narrowest meaningful automated check from the plan.

Run only checks relevant to the phase. If a check fails because of the phase changes, fix within scope and rerun. If failure shows the plan is wrong or scope is larger than expected, stop with a plan mismatch. Update `thoughts/shared/progress/` with commands, results, remaining manual checks, and next phase.
