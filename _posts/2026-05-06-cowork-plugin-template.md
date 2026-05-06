---
layout: post
title: "Cowork plugin template: connect enterprise APIs to Copilot Cowork"
date: 2026-05-06 10:00:00 -0500
categories: [Power Platform, MCP]
tags: [Copilot Cowork, MCP, Cowork Plugins, Skills, Microsoft 365 Copilot, Agent Skills]
description: "A template for building custom Copilot Cowork plugins that connect enterprise APIs using skills, MCP connectors, and the Agent Skills open standard. Includes skill archetypes, auth patterns, validation, and a deployable Microsoft Learn example."
---

Microsoft [announced new Cowork capabilities](https://www.microsoft.com/en-us/microsoft-365/blog/2026/05/05/copilot-cowork-from-conversation-to-action-across-skills-integrations-and-devices/) yesterday — mobile support, built-in skills across Microsoft 365, and custom plugins that extend Cowork to third-party systems. The announcement mentions connectors to LSEG, Miro, monday.com, and S&P Global Energy, with more coming.

That's the first-party side. On the custom side, there's a gap between Microsoft's 4 first-party plugins and Claude Code's 100+ developer-tool plugins: enterprise and vertical SaaS APIs. ServiceNow, SAP, Workday, industry-specific platforms, internal company APIs. I built this template to fill that gap.

Skills use the [Agent Skills open standard](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development#cross-platform-compatibility) and work across Cowork, Claude Code, VS Code Copilot, Gemini CLI, JetBrains Junie, and Cursor. Build once, run everywhere.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugin%20Template)

## What's in the template

A Cowork plugin combines two things: **skills** (prompt-based workflow instructions) and **connectors** (remote MCP servers that provide tools). The template includes both, plus a skills-only variant for scenarios where Cowork's built-in capabilities handle the data access.

### Three packaging patterns

| Pattern | Manifest file | When to use |
|---------|--------------|-------------|
| **Skills + Connector** | `manifest.json` | Your API needs live data access via a remote MCP server |
| **Skills Only** | `manifest-skills-only.json` | Skills guide Cowork's built-in capabilities (Graph, email, files) — no external API |
| **Connector Only** | Remove `agentSkills` from `manifest.json` | MCP tools are self-describing enough for Cowork's built-in skills |

## Skill archetypes

The three included patterns cover about 80% of what business users ask an API-backed agent to do:

| Skill | Pattern | Trigger phrases |
|-------|---------|-----------------|
| **search-and-explore** | Discovery | "Find", "look up", "show me", "check status" |
| **create-and-update** | Mutation | "Create", "add", "update", "change", "close" |
| **report-and-summarize** | Aggregation | "Summarize", "report on", "how are we doing", "weekly update" |
| **improve-skills** | Feedback | "That wasn't right", "you should have known", "review skill feedback" |

Each SKILL.md includes trigger phrase examples, numbered workflow steps referencing specific MCP tools, output format templates, edge case handling, and authentication handling for users who haven't connected yet.

The `improve-skills` skill adds a feedback loop: it records activation gaps and user corrections to the MCP server at runtime, then surfaces accumulated insights when you prepare the next version.

### Writing effective skills

Skills should read like instructions to a capable assistant, not API documentation:

```markdown
# Good — business workflow
1. Ask the user which time period they want (default to this week)
2. Pull all open tickets using the `search_tickets` tool
3. Group by priority and assignee
4. Highlight anything past SLA
5. Present a summary table and recommend actions

# Bad — implementation details
1. Call GET /api/v1/tickets?status=open&created_after={date}
2. Parse the response JSON array
3. Map the priority field to display values
```

### Avoid built-in skill name conflicts

Cowork has 13 built-in skills. If a plugin skill has the same name as a built-in, the built-in takes priority and your skill is silently skipped. Avoid these names:

`word`, `excel`, `powerpoint`, `pdf`, `email`, `scheduling`, `calendar-management`, `meetings`, `daily-briefing`, `enterprise-search`, `deep-research`, `communications`, `adaptive-cards`

## Example: Microsoft Learn research

The template includes a complete, deployable plugin in `examples/microsoft-learn/` that wraps the official [Microsoft Learn MCP Server](https://learn.microsoft.com/en-us/training/support/mcp) with three skills — research docs, compare services, and create learning plans. Zero auth, zero cost, immediately deployable.

## Authentication

| Type | Use when | User experience |
|------|----------|----------------|
| `None` | Public APIs, internal services | No prompt |
| `OAuthPluginVault` | OAuth 2.0 APIs (recommended) | One-time consent flow |
| `ApiKeyPluginVault` | API key services | User provides key once |
| `DynamicClientRegistration` | RFC 7591 dynamic client registration | OAuth consent flow |

Secrets never go in the manifest. The `referenceId` points to credentials in the Microsoft Enterprise Token Store. You register OAuth client ID, secret, URLs, and scopes through Partner Center during App Store submission. Partner Center generates the `referenceId`.

Every skill that calls connector tools must handle the "not yet connected" state. Tell the user they need to sign in, don't retry the tool call until confirmed, and never silently retry mutation operations. Each skill template includes a `## Handling Authentication` section.

## MCP server constraints

If your plugin includes a connector, your MCP server needs to follow these constraints:

| Constraint | Detail |
|------------|--------|
| **30-second timeout** | Every tool call must complete within 30 seconds. Use pagination, pre-aggregation, or async job patterns |
| **Structured JSON responses** | Return JSON objects with `total_count` and `has_more`, not prose |
| **Parameter descriptions** | Every input parameter needs a `description` — this is how the agent decides what to pass |
| **Error format** | Use `isError: true` for business errors, JSON-RPC error codes only for protocol failures |
| **Auth scoping** | Validate the user's OAuth token and scope data to that user on every request |

The `server/` folder provides a protocol guide and an example `tools/list` response with full input schemas.

## Template structure

```
Cowork Plugin Template/
├── manifest.json                  # M365 Unified App Manifest (skills + connector)
├── manifest-skills-only.json      # Alternate manifest (skills only)
├── color.png                      # 192x192 full-color icon (you provide)
├── outline.png                    # 32x32 outline icon (you provide)
├── DEPLOYMENT.md                  # ALM and production deployment guide
├── .github/
│   └── workflows/
│       └── validate-plugin.yml    # CI/CD validation and packaging
├── auth/                          # Auth configuration examples
├── server/                        # MCP server design guidance
├── skills/
│   ├── search-and-explore/        # Discovery workflow pattern
│   ├── create-and-update/         # Mutation workflow pattern
│   ├── report-and-summarize/      # Aggregation workflow pattern
│   └── improve-skills/            # Feedback and iteration pattern
└── package.ps1                    # Validation and packaging script
```

## Quick start

### 1. Copy the template

```powershell
Copy-Item -Recurse "Cowork Plugin Template" "My Service Plugin"
```

### 2. Replace placeholders

Search for `{{` across all files and replace with your values:

| Placeholder | Replace with |
|-------------|-------------|
| `{{GUID}}` | A unique GUID (`[guid]::NewGuid()` in PowerShell) |
| `{{company}}` | Your company identifier (lowercase, no spaces) |
| `{{Company Name}}` | Your company display name |
| `{{Service Name}}` | The API/service name (for example, "ServiceNow", "Workday") |
| `{{Your Name}}` | Skill author name |
| `{{your-mcp-endpoint}}` | Your hosted MCP server URL |
| `{{service-name}}` | Kebab-case service identifier |
| `{{entity}}` | Your primary entity name (for example, "tickets", "customers") |

### 3. Customize skills

- Edit each SKILL.md to reference your actual MCP tool names
- Update `api-field-reference.md` with your real entities, fields, and valid values
- Adjust trigger phrases in descriptions to match your domain language
- Add or remove skills as needed for your API's workflow domains

### 4. Validate and package

```powershell
.\package.ps1                # full validation (requires icons)
.\package.ps1 -SkipIcons     # during development
.\package.ps1 -Json          # structured output for CI/CD
```

### 5. Sideload for testing

1. Open **M365 Admin Center** > **Manage Apps** > **Upload custom app**
2. Upload the generated `.zip` file
3. Open **Cowork** > **Sources & Skills** — your skills should appear

## Cross-platform compatibility

| Platform | Compatibility |
|----------|--------------|
| Microsoft 365 Copilot Cowork | Full |
| Claude Code | Full |
| VS Code / GitHub Copilot | Full |
| Gemini CLI | Full |
| JetBrains Junie | Full |
| Cursor | Full |

To maintain a dual Claude Code + Cowork plugin, use the Claude plugin structure as the superset and convert with the included `Convert-ClaudePluginToMOS3.ps1` script.

## Resources

- [Cowork Plugin Template source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugin%20Template)
- [Copilot Cowork announcement](https://www.microsoft.com/en-us/microsoft-365/blog/2026/05/05/copilot-cowork-from-conversation-to-action-across-skills-integrations-and-devices/)
- [Cowork plugin development guide](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development)
- [Add plugins to Cowork](https://aka.ms/cowork-plugins)
- [Create custom plugins](https://aka.ms/cowork-build-plugins)
- [Manage plugins](https://aka.ms/cowork-manage-plugins)
- [Agent Skills open standard](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development#cross-platform-compatibility)
- [Microsoft Learn MCP Server](https://learn.microsoft.com/en-us/training/support/mcp)
