# IDE AI Framework Assets

This directory is installed into a target workspace by IDE AI Framework.

It contains the portable assets that make the workflow self-contained:

- `agents/` - role specs for clients that support agent definitions outside `.github/agents`.
- `skills/` - reusable workflow skills and a `index.json` registry.
- `context-engineering/` - Shared-Picture Gate and phase workflow instructions.
- `compaction/` - compaction prompt for preserving operational state.
- `hooks/` - standalone hook scripts used by VS Code Copilot Chat where supported.

The `.github` files make VS Code Copilot Chat discover the framework. These `.ide-ai-framework` files make the same behavior understandable and portable for other IDE or CLI adapters.
