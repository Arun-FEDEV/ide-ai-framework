# Codex Context Engineering Compaction Prompt

Compact the session into an operational handoff that keeps Codex in the smart zone.

Preserve, in order:

1. Original user goal and latest user direction.
2. Shared-Picture Contract, including tangible output, end state, out of scope, constraints, risks, and exact confirmation/phase state.
3. Current phase: shared-picture, research, plan, implementation, verification, blocked, or final.
4. Durable artifacts already written under `thoughts/shared/research`, `thoughts/shared/plans`, or `thoughts/shared/progress`.
5. Decisions made and why.
6. Rejected approaches and why they were rejected.
7. Relevant files, symbols, commands, tests, docs, routes, services, and data flow.
8. Research findings about how the system actually works, and whether research was descriptive-only or evaluative.
9. Plan phases with completed/pending status, unresolved questions, and the current phase boundary.
10. Files changed and the intent of each change.
11. Verification evidence: exact command, result, important output summary, and automated vs manual verification status.
12. Current blocker, failure, uncertainty, plan mismatch, or user decision.
13. Next concrete action and whether the user must confirm with `confirmed: proceed` before tools are used.
14. Open questions for the user.

Discard or aggressively summarize:

- Raw command logs except the lines needed as evidence.
- Repeated search/grep output after extracting file/symbol facts.
- MCP payloads, browser dumps, API responses, telemetry dumps, and huge JSON blobs after extracting relevant fields.
- Full test logs after extracting failure/pass facts, command, exit status, and the few lines needed as evidence.
- Failed dead ends after recording the lesson.
- Stale assumptions, implementation chatter, and duplicated context.

If there was a plan mismatch, preserve Expected, Found, Why this matters, Recommended next step, and the user's decision if one exists.

If you cannot confidently preserve the goal, shared-picture contract, current phase, artifact paths, verification evidence, and next action, say so and stop for the user rather than continuing from a weak compacted state.
