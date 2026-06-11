---
layout: post
title: "Decision Duck Cowork plugin: structured decision support in Microsoft 365 Copilot"
date: 2026-06-12 14:00:00 -0000
categories: [MCP (Model Context Protocol), Copilot Studio, Integration]
tags: [Decision Support, Microsoft 365 Copilot, MCP, Azure Container Apps, Copilot Cowork, AI Foundry]
---

## From declarative agent to Cowork plugin

I published the [Decision Duck MCP server and declarative agent](https://troystaylor.com/copilot%20studio/mcp/2026/04/23/decision-duck-mcp-agent.html) back in April. That version worked through the Microsoft 365 Agents Toolkit with a `plugin.json` manifest. Cowork changed the plugin surface: skills replace static plugin manifests, the `devPreview` Teams schema replaces `v1.28`, and the auth path shifts from OAuth client registration to Microsoft Entra SSO.

This post covers the Cowork plugin that wraps the same MCP server with nine skills, composite workflows, and an SSO auth path that avoids a known Frontier bug.

Plugin folder: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Decision%20Duck)

## What the plugin includes

Nine skills, one MCP connector, one plugin package.

### Analysis skills (one per MCP tool)

| Skill | MCP tool | Trigger phrases |
|-------|----------|-----------------|
| `second-opinion` | `get_second_opinion` | "second opinion", "challenge this", "stress test my thinking" |
| `risk-analysis` | `analyze_risk` | "what could go wrong", "risks", "risk register", "mitigations" |
| `bias-check` | `identify_cognitive_biases` | "bias check", "what biases am I missing", "review my reasoning" |
| `compare-options` | `comparative_analysis` | "compare options", "tradeoffs", "which should we pick" |

### Knowledge skill

| Skill | MCP tools | Trigger phrases |
|-------|-----------|-----------------|
| `decision-frameworks` | `list_frameworks`, `get_framework` | "which framework", "RICE", "OODA", "one-way door", "use a framework" |

### Composite workflow skills (multi-tool orchestration)

| Skill | Calls | Use when |
|-------|-------|----------|
| `decide` | `comparative_analysis` then `analyze_risk` then `identify_cognitive_biases` | "help me decide", "I need to make a call on" |
| `pre-mortem` | `pre_mortem` | "pre-mortem", "imagine this failed" |
| `red-team` | `red_team` | "red team this", "tear this apart", "be the skeptic" |
| `stakeholder-lens` | `stakeholder_analysis` | "how would [role] see this", "from finance's perspective" |

The composite skills are the most useful addition over the original declarative agent. `decide` chains three tools in sequence: compare options, analyze risks on the leading option, then check for cognitive biases. One prompt, three passes, one structured output.

## Architecture

```
Cowork user
   │
   ▼
Cowork plugin (skills + connector)
   │  OAuth: OAuthPluginVault (referenceId)
   ▼
Entra ID  ──── Bearer token (aud = Decision Duck API)
   │
   ▼
Decision Duck MCP server  (Azure Container Apps)
   │  POST /mcp  (JSON-RPC 2.0)
   │  - tools/list, tools/call
   │  - resources/list, resources/read
   ▼
Azure AI Foundry (gpt-4o-mini / configurable)
```

The MCP server is the same one from the original Decision Duck project. The Cowork plugin just wraps it with skills and a new auth path.

## Auth: Microsoft Entra SSO, not OAuth client

The plugin uses the **SSO registration** path in Teams Developer Portal, not the OAuth client registration path. The OAuth client path has a known Frontier bug where the consent popup never closes — `postMessage` to the Teams JS SDK fails silently. The SSO path bypasses this by using Microsoft's enterprise token store instead of the popup-based redirect.

Practically, this means:

1. Register a single-tenant Entra app in the Cowork tenant
2. Create a **Microsoft Entra SSO client ID registration** in Teams Developer Portal (not an OAuth client)
3. Capture the `referenceId` for the manifest
4. Apply the server-side token validation patch from `server/auth-middleware.md`

Full Entra app setup is in `auth/README.md` in the plugin folder.

## Manifest schema choice

The plugin uses `devPreview` Teams manifest schema, same as my [Salesforce Cowork plugin](https://troystaylor.com/mcp%20(model%20context%20protocol)/copilot%20studio/integration/2026/06/01/salesforce-cowork-plugin-mcp-server.html). Only the `devPreview` path actually binds the MCP connector in Cowork's current runtime. A `v1.28` manifest loads the skills but silently drops the connector.

The `devPreview` path requires `packageName` in reverse-DNS form (`com.troystaylor.decision-duck-cowork`) and omits `mcpToolDescription` — Cowork discovers tools dynamically through MCP `tools/list`.

## Deploy and package

The MCP server must already be deployed (see the [original Decision Duck post](https://troystaylor.com/copilot%20studio/mcp/2026/04/23/decision-duck-mcp-agent.html) for Azure Container Apps deployment).

1. Add icons: `color.png` (192x192) and `outline.png` (32x32) in the plugin root
2. Register SSO following `auth/README.md`
3. Apply the token validation patch from `server/auth-middleware.md` to the MCP server
4. Update `manifest.json` with your values:
   - `id` — a fresh GUID
   - `mcpServerUrl` — your Container App FQDN
   - `referenceId` — the SSO registration ID from Teams Developer Portal
5. Package:

   ```powershell
   .\package.ps1                 # full validation
   .\package.ps1 -SkipIcons      # while iterating
   ```

6. Upload in M365 Admin Center under **Agents** > **All Agents** > **Add Agent**
7. In Cowork, go to **Sources & Skills**, enable Decision Duck, and complete the one-time consent

### Plugin rotation

When redeploying after changing auth, rotate both the plugin `id` (new GUID) and append a letter suffix to names. Cowork blocks reusing an already-installed plugin ID.

## What to customize

When adapting this plugin for your own decision workflows:

- **Trigger phrases** — tune them to match how your team talks about decisions
- **Analysis depth** — the `get_second_opinion` tool accepts `quick`, `balanced`, or `deep` modes
- **Frameworks** — add domain-specific frameworks to the knowledge tools
- **Model selection** — swap `gpt-4o-mini` for a different model via environment variables on the MCP server
- **Composite skill chains** — create new multi-tool workflows by adding skills that call tools in sequence

## Resources

- [Decision Duck Cowork plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Decision%20Duck)
- [Decision Duck MCP server](https://github.com/troystaylor/SharingIsCaring/tree/main/Decision%20Duck)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
- [Build plugins for Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
- [Microsoft 365 Copilot plugin authentication](https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-authentication)
