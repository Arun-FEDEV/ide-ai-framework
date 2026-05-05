---
name: git-safe
description: Inspect git state and propose safe next git actions without publishing.
agent: "Git Worker"
tools: ["search/codebase", "search", "runCommands", "changes"]
---

Inspect git state and propose safe next actions. Do not commit, push, create PRs/issues, mutate labels/comments, or deploy.

Report branch, changed files, likely ownership boundaries, suggested commit grouping, verification evidence, and risks. If a protected branch is active, recommend creating a feature branch before any git write.
