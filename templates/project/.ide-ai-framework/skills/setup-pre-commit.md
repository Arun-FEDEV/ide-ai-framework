# Skill: Setup Pre-Commit

Use when the user asks to add commit-time formatting, linting, type checks, or tests.

## Workflow

1. Inspect the repo's package manager and existing scripts.
2. Prefer existing tooling over introducing new tools.
3. Add the narrowest useful pre-commit path.
4. Verify with the configured hook command and relevant package scripts.
5. Document how to bypass or debug the hook.

Do not make commit hooks so slow that developers stop using them.
