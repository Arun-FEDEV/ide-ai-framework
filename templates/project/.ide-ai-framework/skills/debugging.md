# Skill: Debugging

Use when behavior is broken, tests fail, errors appear, or a regression is reported.

## Workflow

1. Reproduce the failure when feasible.
2. Isolate the smallest failing path.
3. Identify root cause with code evidence.
4. Patch the smallest coherent fix.
5. Add or run focused regression proof.

## Guardrails

- Do not guess past missing reproduction evidence.
- Keep changes scoped to the failure.
- If reproduction is blocked, document the exact evidence and uncertainty.
- Prefer one focused failing test over broad exploratory edits.
