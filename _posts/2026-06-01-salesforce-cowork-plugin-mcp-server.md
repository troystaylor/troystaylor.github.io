---
layout: post
title: "Build a Salesforce Cowork plugin with an in-tenant MCP server"
date: 2026-06-01 09:00:00 -0000
categories: [MCP (Model Context Protocol), Copilot Studio, Integration]
tags: [Salesforce, Microsoft 365 Copilot, MCP, Azure Container Apps, Copilot Cowork]
---

## Why a Salesforce plugin for Cowork

Sellers don't want to leave Copilot to update Salesforce. They want to ask for an account briefing, get opportunity health, log a call, and move on. That only works if Cowork can read and write CRM data safely inside your tenant.

My Salesforce plugin in the [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Salesforce) gives you that surface. It packages a Cowork plugin manifest, a focused skill set, and an in-tenant MCP server that fronts Salesforce with both read and write tools.

## What the plugin includes

This plugin ships:

- A `devPreview` Cowork plugin manifest
- Thirteen skills covering account, opportunity, contact, and task workflows
- An MCP server with both a full read/write endpoint and a read-only federated endpoint
- Azure deployment assets driven by `azd up`
- Preflight and packaging scripts for repeatable builds

Plugin folder:

- https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Salesforce

Repository:

- https://github.com/troystaylor/SharingIsCaring

## Current scope

The plugin focuses on what sales teams actually do every day:

- Account briefings and full CRUD on accounts
- Opportunity health, risk summaries, and full CRUD on opportunities
- Next-best-action recommendations
- Contact discovery and full CRUD on contacts
- Task review and call-note logging

That scope keeps the plugin useful for both pre-meeting prep and post-meeting cleanup without sprawling into every Salesforce object.

## Skills shipped in the plugin

The plugin ships thirteen skills, split into read and write modes.

Read skills:

- account-briefing: Build an account snapshot before customer meetings
- opportunity-health-summary: Assess pipeline quality and stage health
- next-best-action: Recommend concrete next steps per deal
- open-risks-and-blockers: Surface stalled deals and blockers
- find-contacts: Search for contacts by name, account, or email
- review-tasks: List and review open tasks across deals

Write skills:

- create-account: Create a new account record
- update-account: Edit account fields
- create-opportunity: Create a new opportunity tied to an account
- update-opportunity: Change stage, amount, close date, owner, and fields
- add-contact: Create a new contact under an account
- update-contact: Edit contact fields
- log-call-notes: Add structured call outcomes and follow-ups

Splitting skills this way keeps each prompt focused, which makes responses more predictable and easier to tune.

## MCP tool surface and dual routes

The MCP server exposes two endpoints from one backend:

- `/mcp/full` — all 16 tools (read and write). The plugin's `mcpServerUrl` points here.
- `/mcp/federated` — 9 read-only tools, for federated and agent-to-agent scenarios where writes aren't wanted.

Read tools (9):

- `search_accounts`
- `get_account`
- `search_opportunities`
- `get_opportunity`
- `search_contacts`
- `get_contact`
- `list_tasks`
- `get_task`
- `list_recent_activities`

Write tools (7):

- `create_account`
- `update_account`
- `create_opportunity`
- `update_opportunity`
- `create_contact`
- `update_contact`
- `create_task`

One backend, two routes. You get write capability for Cowork users and a safer read-only surface for downstream agents that just need grounding.

## Manifest schema choice

The plugin uses the `devPreview` Teams manifest schema (`manifestVersion: "devPreview"`), not `v1.28`. That's deliberate.

In Cowork's current runtime, only the `devPreview` path actually binds the MCP connector. A `v1.28` manifest loads the skills but silently drops the connector, so the agent never invokes any tools. The `devPreview` path also requires `packageName` in reverse-DNS form and omits `mcpToolDescription`. Cowork discovers tools dynamically through MCP `tools/list`.

If you start from a `v1.28` template and skills run but nothing reaches Salesforce, the manifest version is the first thing to check.

## Deploy to Azure

The deployment flow is straightforward:

1. Provision the Azure infrastructure and MCP server:

   ```powershell
   cd "Cowork Plugins/Salesforce"
   azd up
   ```

2. Register an OAuth client in the Teams Developer Portal pointing at your Salesforce connected app, and capture the OAuth registration `referenceId`.
3. In `manifest.json`, replace:
   - `id` (`{{GUID}}`) with a fresh GUID
   - `agentConnectors[0].toolSource.remoteMcpServer.mcpServerUrl` (`<YOUR-CONTAINER-APP-FQDN>`) with the deployed Container App FQDN
   - `agentConnectors[0].toolSource.remoteMcpServer.authorization.referenceId` (`{{OAUTH_REFERENCE_ID}}`) with the OAuth registration ID
4. Validate and package:

   ```powershell
   ./preflight.ps1
   ./package.ps1 -SkipIcons
   ```

5. Upload `Salesforce.zip` in the Microsoft 365 Admin Center, publish to test users, then connect in a fresh Cowork session.

For a value-mapping checklist see `SETUP-CHECKLIST.md`. For re-cutover after redeploys see `CUTOVER-RUNBOOK.md`.

## What to customize first

When you adapt this plugin for a real tenant, start here:

- Trigger phrases and tone for each skill to match how your sellers talk
- Field selection in account and opportunity reads to keep responses tight
- Required fields and picklist values in write tools to match your org
- OAuth scopes pinned to the minimum your Salesforce connected app needs
- Logging and correlation IDs so MCP calls are easy to trace end to end

## Why this pattern is useful

This plugin is a good template for any SaaS system where you want Copilot to do more than read.

You get:

- One MCP backend with two intent-shaped routes
- Skills aligned to seller workflows, not raw API calls
- A manifest that actually binds in today's Cowork runtime
- An OAuth path that fits enterprise controls
- A repeatable `azd` deployment and packaging flow

Drop in a different SaaS API and most of the structure carries over.

## Resources

- [Salesforce Cowork plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Salesforce)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
- [Build plugins for Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
- [Microsoft 365 Copilot plugin authentication](https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-authentication)
- [Salesforce REST API developer guide](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm)
