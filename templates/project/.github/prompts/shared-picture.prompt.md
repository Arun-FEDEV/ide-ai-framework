---
name: shared-picture
description: Build the Shared-Picture Contract before local/project-state work.
agent: "Control Plane"
tools: ["search/codebase", "search"]
---

Create a Shared-Picture Contract for the current request.

Ask one output-focused question at a time only if the tangible result is not clear. State the recommended interpretation and why. When clear, present:

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

Do not use local/project-state tools beyond read-only evidence needed to frame the contract unless already unlocked.
