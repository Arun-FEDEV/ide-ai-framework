# VS Code Verification

Run these checks in a clean workspace after installation.

## Discovery

- Open VS Code in the installed target workspace.
- Run `Chat: Open Customizations`.
- Confirm the Copilot instructions, context-engineering instruction file, agents, and prompt files appear.
- Confirm `.ide-ai-framework/skills/index.json`, `.ide-ai-framework/context-engineering/SKILL.md`, and `.ide-ai-framework/compaction/context-engineering.md` exist in the target workspace.
- Open the Copilot Chat Hooks output channel and confirm the hook config loads.

## Shared-Picture Gate

- Ask Copilot Chat for a work/action request that would normally inspect or edit local files.
- Expected: Copilot asks for a Shared-Picture Contract or a hook blocks local/project-state tools before confirmation.
- Reply exactly `confirmed: proceed`.
- Expected: only the next phase unlocks.

## Command Policy

- Ask Copilot to run a harmless command such as listing files.
- Expected: command is allowed and telemetry records it.
- Ask Copilot to run a destructive git history reset in words.
- Expected: hook denies it before execution.
- On a protected branch, ask for a git write operation.
- Expected: hook denies it before execution.

## Telemetry

Check:

```sh
python3 .ide-ai-framework/hooks/telemetry_report.py
```

Expected: recent prompt routes, command records, verification commands, and stop outcomes appear.

## Skill Routing

- Ask for TDD or test-first implementation.
- Expected: route context includes `RECOMMENDED-SKILLS` with `context-engineering` and `tdd`.
- Ask for a security review.
- Expected: route context includes `security-review`.
