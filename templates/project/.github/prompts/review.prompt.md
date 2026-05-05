---
name: review
description: Review changes for correctness, regressions, risks, and missing proof.
agent: "Reviewer"
tools: ["search/codebase", "search", "problems", "changes"]
---

Review the current changes in a code-review stance.

Lead with findings ordered by severity. Cite file paths and symbols. Focus on correctness, behavior regressions, security-adjacent risks, and missing tests. If no issues are found, say so clearly and list any residual verification gaps.
