# Research Phase

Research is documentarian work first. The job is to map the current system so planning starts from correct information.

## Rules

- Document what exists, where it exists, how it works, and how components interact.
- Do not propose fixes, critique, refactor, optimize, or choose an implementation unless the Shared-Picture Contract explicitly asks for evaluation.
- Read directly mentioned files fully before decomposing the task.
- Prefer fresh codebase evidence over old notes or prior assumptions.
- Use `rg` and `rg --files` before broad reads.
- Include file and line references where possible.
- Treat large logs, MCP payloads, JSON blobs, and browser dumps as raw evidence to distill immediately.
- If research shows the original assumption is wrong, say so and stop or ask for confirmation before planning.

## Research Document

For meaningful research, write to `thoughts/shared/research/YYYY-MM-DD_HH-MM-SS_task.md`.

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

### [Component Or Flow]

- What exists:
- How it works:
- How it connects:
- Evidence:

## Code References

- `path/file.ext:line` - What is there.

## Architecture Documentation

## Historical Context

## Related Research

## Open Questions
```

## Handoff

End research with:

- what is known
- what remains uncertain
- whether planning is safe
- the recommended next phase
- whether the user must reply `confirmed: proceed`
