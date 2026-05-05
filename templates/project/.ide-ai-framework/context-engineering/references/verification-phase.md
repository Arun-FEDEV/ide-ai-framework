# Verification Phase

Verification proves the phase outcome with the narrowest meaningful check.

## Rules

- Run checks that directly correspond to the changed behavior.
- Prefer targeted tests over broad suites when the change is narrow.
- Include lint/type/build checks when the change affects shared surfaces or deployment behavior.
- Separate automated verification from manual verification.
- Do not claim manual verification is complete unless the user confirmed it.
- If verification fails inside the phase scope, fix and rerun.
- If verification reveals the plan is wrong or scope is larger than expected, stop with a plan mismatch.

## Evidence Format

Record:

- Command
- Exit status
- Pass/fail summary
- Important output lines
- Remaining manual checks
- Residual risk
