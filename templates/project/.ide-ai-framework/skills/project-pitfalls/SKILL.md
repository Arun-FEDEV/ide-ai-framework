---
name: "project-pitfalls"
description: "Use when working on project-specific workspace, project-specific workspace, project-specific workspace, or any non-trivial task where historical mistakes in ~/Obsidian/Coding/Mistakes/ should be checked before making changes."
---

# Project Pitfalls

Read the smallest useful set of historical gotcha notes before making non-trivial changes.

## Goal

Convert past mistakes into explicit execution constraints before touching code.

## When to use

- project-specific workspace, project-specific workspace, or project-specific workspace work above a trivial fix
- Anything involving routing, APIs, ML loops, infra, storage, or debugging workflows
- Tasks where a previous mistake note is likely to save time or prevent regression

## Workflow

1. Identify the project and task domain.
2. Search `~/Obsidian/Coding/Mistakes/` for the most relevant note names or keywords.
3. Read only the top 1-3 notes that materially match the current task.
4. Extract 3-5 concrete guardrails.
5. Apply those guardrails before editing or testing.

## Output format

Return a short checklist:

- `Relevant notes:` filenames
- `Guardrails:` concise rules to follow now
- `Watch for:` specific failure modes or regressions

## Guardrails

- Do not bulk-read the whole mistakes folder.
- Prefer notes that mention the current project, subsystem, or failure mode.
- If no note is relevant, say so and move on quickly.
