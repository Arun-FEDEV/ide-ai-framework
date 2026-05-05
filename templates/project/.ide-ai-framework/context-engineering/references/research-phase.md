# Research Phase

Research is documentarian work first. Map the current system before planning.

## Rules

- Document what exists, where it exists, how it works, and how components interact.
- Do not propose fixes, critique, refactor, optimize, or choose an implementation unless the contract asks for evaluation.
- Read directly mentioned files fully before decomposing the task.
- Prefer fresh codebase evidence over old notes or prior assumptions.
- Use `rg` and `rg --files` before broad reads.
- Include file and line references where possible.
- Distill large logs, API payloads, browser dumps, and JSON blobs immediately.
- If research shows the original assumption is wrong, say so and stop or ask for confirmation before planning.

## Artifact

Write meaningful research to `thoughts/shared/research/YYYY-MM-DD_HH-MM-SS_task.md`.

Use this structure:

```md
# Research: [Question]

Date:
Researcher:
Repository:
Branch:
Commit:
Status:

## Research Question
## Summary
## Detailed Findings
## Code References
## Architecture Documentation
## Historical Context
## Related Research
## Open Questions
```

End with what is known, what remains uncertain, whether planning is safe, the recommended next phase, and whether the user must reply `confirmed: proceed`.
