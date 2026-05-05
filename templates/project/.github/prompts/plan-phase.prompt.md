---
name: plan-phase
description: Turn research into a phased implementation plan and stop.
agent: "Planner"
tools: ["search/codebase", "search"]
---

Create a phased implementation plan from the current research artifact and codebase evidence.

Include overview, current state, desired end state, key discoveries with file references, out of scope, exact edit targets, phases, automated verification, manual verification, rollback notes, and references. Save it under `thoughts/shared/plans/`. Stop after the plan and ask the user for `confirmed: proceed`.
