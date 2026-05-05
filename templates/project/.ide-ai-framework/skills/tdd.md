# Skill: TDD

Use when the user requests TDD, test-first work, red-green-refactor, or a risky behavior change that needs regression proof.

## Workflow

1. Confirm the public interface and observable behaviors.
2. Write one failing test for one behavior.
3. Implement the smallest change that passes that test.
4. Repeat one vertical slice at a time.
5. Refactor only when tests are green.

## Guardrails

- Test behavior through public interfaces, not private implementation details.
- Prefer stable fixtures and direct assertions over broad snapshots.
- Do not write a large batch of imagined tests before seeing the implementation path.
- Record exact test commands and results in the progress artifact.
