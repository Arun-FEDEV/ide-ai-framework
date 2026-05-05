# Skill: Git Safety

Use for branch hygiene, commits, pushes, PR preparation, and merge/rebase planning.

## Rules

- Never commit on `main` or `master`.
- Do not push, create PRs/issues, mutate labels/comments, or deploy without explicit immediate approval.
- Summarize branch, remote, and pending files before git writes.
- Prefer non-interactive git commands.
- Avoid destructive commands unless the user explicitly requested the destructive operation and accepted the risk.

## Recommended Output

- Current branch
- Remote status
- Changed files
- Proposed commit grouping
- Verification evidence
- Exact next command that needs approval
