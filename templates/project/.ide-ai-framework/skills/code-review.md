# Skill: Code Review

Use for review requests, audit requests, or before publishing changes.

## Output Shape

Lead with findings ordered by severity. Each finding should include:

- Impact
- File/symbol reference
- Why the behavior is risky
- Minimal remediation idea

Then include open questions, verification gaps, and a brief summary.

## Priorities

- Correctness regressions
- Security-adjacent risks
- Missing tests or missing proof
- Broken contracts between modules
- Risky operational behavior

If no issues are found, say so clearly and list remaining residual risk.
