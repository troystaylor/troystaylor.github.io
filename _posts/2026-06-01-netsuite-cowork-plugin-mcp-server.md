---
layout: post
title: "Build a NetSuite Cowork plugin with SuiteQL and full record CRUD"
date: 2026-06-01 12:00:00 -0000
categories: [MCP (Model Context Protocol), Copilot Studio, Integration]
tags: [NetSuite, Microsoft 365 Copilot, MCP, Azure Container Apps, Copilot Cowork, SuiteQL]
---

## Why a NetSuite plugin for Cowork

Most ERP plugins for Copilot ship a fixed list of tools — get customer, list invoices, maybe a saved search or two. The moment someone asks something off-script, the plugin shrugs and the user goes back to NetSuite.

The NetSuite plugin in the [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/NetSuite) takes a different path. It pairs scenario skills for the questions people ask every day with a SuiteQL escape hatch and full record CRUD for everything else. The whole surface runs through an in-tenant MCP server, so credentials and data stay in your tenant.

## What the plugin includes

This plugin ships:

- A `devPreview` Cowork plugin manifest
- Thirteen skills covering customer, sales, AR, vendor, SuiteQL, and record CRUD workflows
- An MCP server with a full read/write endpoint and a read-only federated endpoint
- Azure deployment assets driven by `azd up`
- Preflight, packaging, icon, and smoke-test scripts

Plugin folder:

- https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/NetSuite

Repository:

- https://github.com/troystaylor/SharingIsCaring

## Current scope

The plugin covers the most common NetSuite reach-ins:

- SuiteQL queries against any NetSuite table
- Full CRUD on any record type (customer, vendor, salesorder, invoice, and more)
- Sublist line management on transactional records
- Record metadata discovery (record types and field schemas)
- Sales and finance scenario skills: customer briefings, open sales orders, AR aging, vendor lookup, recent transactions

That mix lets the plugin handle both targeted scenario prompts and open-ended ad hoc questions through SuiteQL.

## Skills shipped in the plugin

The plugin ships thirteen skills, split into read and write modes.

Read skills:

- customer-briefing: Build a customer snapshot before account reviews
- open-sales-orders-review: Review open sales orders by customer or status
- ar-aging-snapshot: Pull open AR invoices and surface aging
- vendor-lookup: Find vendor records and contact info
- recent-transactions: List recent transactions for an entity
- run-suiteql-query: Execute an arbitrary SuiteQL query
- list-records: List and filter records of a given type
- get-record-details: Retrieve a single record by id
- get-record-metadata: Discover record types and field schemas

Write skills:

- create-record: Create a new record of any type
- update-record: Patch fields on an existing record
- delete-record: Permanently delete a record
- manage-sublist-lines: Add, update, or remove sublist lines

The scenario skills cover the questions people ask every day. The generic record skills cover everything else.

## MCP tool surface and dual routes

The MCP server exposes two endpoints from one backend:

- `/mcp/full` — all 16 tools (read and write). The plugin's `mcpServerUrl` points here.
- `/mcp/federated` — 10 read-only tools, for federated and agent-to-agent scenarios where writes aren't wanted.

Read tools (10):

- `run_suiteql`
- `list_records`
- `get_record`
- `list_record_types`
- `get_record_metadata`
- `get_sublist`
- `search_customers`
- `search_vendors`
- `get_open_sales_orders`
- `get_open_invoices`

Write tools (6):

- `create_record`
- `update_record`
- `delete_record`
- `add_sublist_line`
- `update_sublist_line`
- `delete_sublist_line`

One backend, two routes. The full route powers the Cowork plugin. The federated route gives downstream agents a safe read-only NetSuite surface without giving them write tools.

## Manifest schema choice

The plugin uses the `devPreview` Teams manifest schema (`manifestVersion: "devPreview"`), not `v1.28`. That's deliberate.

In Cowork's current runtime, only the `devPreview` path actually binds the MCP connector. A `v1.28` manifest loads the skills but silently drops the connector, so the agent never invokes any tools. The `devPreview` path also requires `packageName` in reverse-DNS form and omits `mcpToolDescription`. Cowork discovers tools dynamically through MCP `tools/list`.

If you build from a `v1.28` template and skills run but nothing reaches NetSuite, the manifest version is the first thing to check.

## NetSuite prerequisites

Before deploying, set up NetSuite:

1. Enable REST Web Services: Setup > Company > Enable Features > SuiteTalk.
2. Create an OAuth 2.0 Integration Record: Setup > Integration > Manage Integrations > New.
   - Enable OAuth 2.0
   - Redirect URI: `https://teams.microsoft.com/api/platform/v1.0/oauthRedirect`
   - Scope: `rest_webservices`
   - Capture the Client ID and Client Secret (shown once)
3. Get your Account ID: Setup > Company > Company Information. Replace any hyphen with an underscore (for example, sandbox `TSTDRV1234567_SB1`).

## Deploy to Azure

The deployment flow:

1. Provision the Azure infrastructure and MCP server:

   ```powershell
   cd "Cowork Plugins/NetSuite"
   azd up
   ```

   You'll be prompted for `NETSUITE_ACCOUNT_ID` (for example, `1234567` or `TSTDRV1234567_SB1`).

2. Bind the container app to ACR with its system identity (one-time, after first `azd up`):

   ```powershell
   az containerapp registry set `
     -g <resource-group> -n <container-app-name> `
     --server <acr-name>.azurecr.io --identity system
   ```

   The Bicep ships with `registries: []` to avoid a first-deploy chicken-and-egg problem — the AcrPull role isn't assigned yet when the container app first tries to bind. Run `azd deploy` again after binding. Subsequent deploys work without this step.

3. Register an OAuth client in the Teams Developer Portal pointing at your NetSuite Integration Record:
   - Authorization endpoint: `https://<account>.app.netsuite.com/app/login/oauth2/authorize.nl`
   - Token endpoint: `https://<account>.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token`
   - Scope: `rest_webservices`

   Capture the OAuth registration `referenceId`.

4. In `manifest.json`, replace:
   - `id` (`{{GUID}}`) with a fresh GUID
   - `agentConnectors[0].toolSource.remoteMcpServer.mcpServerUrl` (`<YOUR-CONTAINER-APP-FQDN>`) with the deployed Container App FQDN
   - `agentConnectors[0].toolSource.remoteMcpServer.authorization.referenceId` (`{{OAUTH_REFERENCE_ID}}`) with the OAuth registration ID

5. Validate and package:

   ```powershell
   ./preflight.ps1
   ./package.ps1 -SkipIcons
   ```

6. Smoke-test the deployed MCP endpoint:

   ```powershell
   ./smoke.ps1 -Fqdn <container-app-fqdn>
   ```

   Expect `200 Healthy` on `/health/live` and `/health/ready`, plus a `tools/list` response listing all 16 tools.

7. Upload `NetSuite.zip` in the Microsoft 365 Admin Center, publish to test users, then connect in a fresh Cowork session.

For a value-mapping checklist see `SETUP-CHECKLIST.md`. For re-cutover after redeploys see `CUTOVER-RUNBOOK.md`.

## Helper scripts

The plugin ships several helpers worth knowing about:

- `preflight.ps1`: Validate manifest, skills, icons, and connector wiring before packaging
- `package.ps1`: Build `NetSuite.zip` from manifest, skills, and icons
- `generate-icons.ps1`: Download source PNG and produce a 192x192 `color.png` and 32x32 `outline.png`
- `fix-outline.ps1`: Rebuild `outline.png` as a pure-white silhouette (required by Microsoft 365 Admin Center)
- `smoke.ps1`: Post-deploy smoke test that hits `/health/live`, `/health/ready`, `/status`, and runs MCP `initialize` plus `tools/list` against `/mcp/full`

Those scripts make the upload-to-Cowork loop fast and predictable.

## What to customize first

When you adapt this plugin for a real tenant, start here:

- SuiteQL query patterns and saved-search equivalents for your data model
- Field selection in customer and vendor reads to keep responses tight
- Required fields and lists on common record types for your write tools
- OAuth scopes pinned to the minimum your Integration Record needs
- Logging and correlation IDs so MCP calls are easy to trace end to end

## Why this pattern is useful

This plugin is a strong example of mixing scenario skills with a generic CRUD and query layer.

You get:

- One MCP backend with two intent-shaped routes
- Skills for high-frequency finance and sales questions
- A SuiteQL escape hatch for anything the scenario skills don't cover
- Full record CRUD without writing a new tool for every object type
- An OAuth and deployment flow that fits enterprise controls

Most other ERP integrations stop at read-only. This one gives you a complete two-way path while keeping data and credentials inside your tenant.

## Resources

- [NetSuite Cowork plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/NetSuite)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
- [Build plugins for Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
- [Microsoft 365 Copilot plugin authentication](https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-authentication)
- [NetSuite SuiteQL reference](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_156257770590.html)
- [NetSuite REST API browser](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_1540391670.html)
