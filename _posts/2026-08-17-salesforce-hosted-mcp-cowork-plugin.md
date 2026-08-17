---
layout: post
title: "Run Salesforce in Copilot Cowork with no MCP server to deploy"
date: 2026-08-17 16:00:00 -0400
categories: [MCP (Model Context Protocol), Copilot Studio, Integration]
tags: [Salesforce, Microsoft 365 Copilot, Copilot Cowork, MCP, Agent Skills, Hosted MCP Servers, SOQL]
description: "A Copilot Cowork plugin that connects to Salesforce's own hosted MCP servers. Nineteen CRM skills, no container to deploy, and every action runs as the signed-in Salesforce user."
---

Salesforce operates MCP servers for its own platform, so a Cowork plugin for Salesforce doesn't need an MCP server at all. [Salesforce for Copilot Cowork (Hosted MCP)](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Salesforce%20Hosted%20MCP) connects Copilot Cowork straight to `api.salesforce.com` — no container app, no Bicep, no Azure resource to keep patched.

This is the counterpart to my [self-hosted Salesforce Cowork plugin](https://troystaylor.com/mcp%20(model%20context%20protocol)/copilot%20studio/integration/2026-06-01-salesforce-cowork-plugin-mcp-server.html), which ships a C# MCP server on Azure Container Apps. Same CRM workflows, opposite architecture.

## How it works

```text
Copilot Cowork
   |  MCP (streamable HTTP) + OAuth 2.0 / PKCE
   v
https://api.salesforce.com/platform/mcp/v1/platform/sobject-all
   |  runs as the signed-in Salesforce user
   v
Salesforce org - profile, sharing rules, field-level security enforced
```

The plugin contributes two things: a connector definition that points at the Salesforce endpoint, and nineteen skills that carry the CRM domain knowledge.

That second part is where the work went. The hosted server exposes *generic* sObject tools — `soqlQuery`, `getObjectSchema`, `createSobjectRecord` — not `search_accounts`-style domain tools. Without skills, the agent guesses field API names and SOQL syntax on every turn. The skills name the objects, the fields, the exact queries, how to read the results, and when to stop and ask before writing.

## Tools on the default server

The plugin targets `platform/sobject-all`, which provides eleven tools:

| Tool | Purpose |
|---|---|
| `getObjectSchema` | Object index, or full field schema for one object |
| `soqlQuery` | Run a SOQL query |
| `find` | Run a SOSL text search |
| `getUserInfo` | Identity of the signed-in Salesforce user |
| `listRecentSobjectRecords` | Recently viewed or modified records |
| `getRelatedRecords` | Child records via a relationship path |
| `createSobjectRecord` | Create a record |
| `updateSobjectRecord` | Update a record |
| `updateRelatedSobjectRecord` | Update a child record via relationship |
| `deleteSobjectRecord` | Delete a record |
| `deleteRelatedSobjectRecord` | Delete a child record via relationship |

Salesforce publishes seven standard servers. Four cover sObjects at different permission levels, and three cover Data 360 and Tableau Next.

## Nineteen skills

Ten read skills, eight write skills, and one meta skill:

| Skill | Intent | Mode |
|---|---|---|
| `account-briefing` | Account 360 snapshot before a customer meeting | Read |
| `opportunity-health-summary` | Deal hygiene inspection and risk scoring | Read |
| `pipeline-review` | Pipeline and forecast roll-ups by stage, owner, or period | Read |
| `open-risks-and-blockers` | Stalled deals, past-due dates, overdue tasks, escalations | Read |
| `next-best-action` | Evidence-based next move on a deal | Read |
| `find-contacts` | Locate contacts and leads, with deal context | Read |
| `review-tasks` | Triage open activities and upcoming meetings | Read |
| `lead-followup` | Untouched and aging lead triage | Read |
| `case-triage` | Open and escalated cases, correlated with revenue | Read |
| `explore-salesforce-data` | Schema discovery and ad-hoc SOQL on any object | Read |
| `create-account` | Create an account, duplicate-checked | Write |
| `update-account` | Edit account fields | Write |
| `create-opportunity` | Create a deal tied to an account | Write |
| `update-opportunity` | Stage, amount, close date, next step, owner | Write |
| `add-contact` | Create a contact and link it to a deal | Write |
| `update-contact` | Edit contact fields and deal roles | Write |
| `log-call-notes` | Log calls and meetings, create follow-ups | Write |
| `delete-salesforce-record` | Guarded deletion with cascade disclosure | Write |
| `improve-skills` | Capture skill misfires and report improvement insights | Meta |

Every write skill shows a before/after diff and requires explicit confirmation before it calls a mutation tool. `delete-salesforce-record` goes further: it asks for confirmation by record name and Id, and discloses what the cascade will remove.

Two reference files carry the detail that would otherwise bloat every skill — a CRM object reference with field API names, picklist values, Id prefixes, and required fields, and a SOQL cookbook covering aggregates, relationships, escaping, error codes, and limits. Cowork loads them only when a skill needs them.

## Pick a server with configure.ps1

Different orgs want different blast radius. `configure.ps1` rewrites `mcpServerUrl` and declares only the skills the target server can actually support:

```powershell
./configure.ps1 -ListServers                    # see the options
./configure.ps1 -Server sobject-all             # full CRUD (default)
./configure.ps1 -Server sobject-reads           # read-only deployment
./configure.ps1 -Server sobject-all -Sandbox    # sandbox or scratch org
./configure.ps1 -Server sobject-all -ReferenceId "<auth-config-id>"
```

| Server | Tools | Skills | Capability |
|---|---|---|---|
| `platform/sobject-all` | 11 | 19 of 19 | Full CRUD — default |
| `platform/sobject-reads` | 6 | 11 of 19 | Read-only |
| `platform/sobject-mutations` | 6 | 12 of 19 | Create and update, no delete |
| `platform/sobject-deletes` | 5 | 6 of 19 | Delete only |

Skill folders stay in the repo, so re-running with a broader server restores the fuller set. `preflight.ps1` fails the build if a hand-edited manifest declares a skill the target server can't run.

The skill counts drop sharply on the mutation and delete servers because Salesforce exposes `getUserInfo` only on `sobject-reads` and `sobject-all`. Six skills resolve "my deals" and "my tasks" through it. Treat those two servers as narrow, purpose-built deployments rather than general CRM assistants.

### Custom servers

Salesforce Setup can build a custom MCP server that composes sObject tools with Apex invocable methods, `@AuraEnabled` controllers, Apex REST endpoints, API Catalog entries, Flows, and Prompt Builder templates. Target one with:

```powershell
./configure.ps1 -CustomServer "myorg/crm-plus"
./configure.ps1 -CustomServer "myorg/crm-readonly" -BaseOn sobject-reads
```

`-BaseOn` tells the script which standard tool set the custom server is assumed to include, so it can pick the skill set. Verify that assumption against the server's real `tools/list` output — `preflight.ps1` can't validate a custom server's tools.

Custom servers are also the route around the plugin's two biggest gaps. Lead conversion and record merge have no operation on the standard sObject servers. An admin can expose either as a Flow or `@InvocableMethod`, then add a skill that names that tool.

## Authentication

Salesforce Hosted MCP uses OAuth 2.0 authorization code with PKCE, per user. Three facts drive the configuration.

**Dynamic client registration isn't supported.** Salesforce says so explicitly, so the connector can't omit `authorization` and let Cowork self-register. Create an auth config up front in the Microsoft Enterprise token store and reference it with `authorization.type` of `OAuthPluginVault`.

**Connected Apps aren't supported.** You need an External Client App in the Salesforce org, with the `mcp_api` and `refresh_token` scopes and JWT-based access tokens for named users. Budget for propagation: the ECA can take up to 30 minutes to become operational.

**The redirect URI is fixed.** Register `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect` as the ECA callback URL. It's identical for every Copilot plugin and every OAuth provider.

| Setting | Production | Sandbox / scratch |
|---|---|---|
| Authorization URL | `https://login.salesforce.com/services/oauth2/authorize` | `https://test.salesforce.com/services/oauth2/authorize` |
| Token URL | `https://login.salesforce.com/services/oauth2/token` | `https://test.salesforce.com/services/oauth2/token` |
| Scopes | `mcp_api refresh_token` | same |
| PKCE | Required (S256) | same |
| MCP URL | `https://api.salesforce.com/platform/mcp/v1/<SERVER-NAME>` | `https://api.salesforce.com/platform/mcp/v1/sandbox/<SERVER-NAME>` |

`offline_access` is a Microsoft identity platform scope. Salesforce uses `refresh_token` instead, which is already in the list. Adding `offline_access` here breaks the registration.

Every action runs as the signed-in Salesforce user. The plugin has no service account and can't exceed that user's profile, sharing rules, or field-level security.

## Deploy

1. **In Salesforce:** create the External Client App with the Teams callback URL, add the `mcp_api` and `refresh_token` scopes, enable JWT-based access tokens for named users, and enable the MCP server under Setup > Integration > Salesforce MCP Servers. The server is off by default.
2. **Verify in Postman before touching Cowork.** Add the Postman callback to the ECA, create an MCP request over HTTP, authorize with PKCE, then confirm `tools/list` returns the eleven tools and `getUserInfo` returns the right user. If this fails, nothing downstream will work.
3. **In Microsoft 365:** create the OAuth auth config in [Teams developer portal](https://dev.teams.microsoft.com/tools) > **Tools** > **OAuth client registration**. Supply the ECA consumer key and secret, the Salesforce endpoints, scopes `mcp_api refresh_token`, and PKCE. Set **Base URL** to the same value as `mcpServerUrl`. Capture the auth config ID.
4. **Configure, validate, and package:**

   ```powershell
   cd "Cowork Plugins/Salesforce Hosted MCP"
   ./configure.ps1 -Server sobject-all -ReferenceId "<auth-config-id>"
   ./preflight.ps1
   ./package.ps1
   ```

5. Upload `Salesforce Hosted MCP.zip` in the Microsoft 365 admin center, publish to test users, then connect in a **fresh** Cowork session. An existing session won't pick up a newly published connector.

`preflight.ps1 -AllowPlaceholders` downgrades unresolved placeholders to warnings while you're still developing.

## Smoke test in this order

```text
Who am I in Salesforce?

What's my Salesforce pipeline this quarter?

Brief me on [a real account].

What fields are on the Opportunity object?
```

Those four exercise `getUserInfo`, SOQL aggregates, `find` plus multi-query synthesis, and `getObjectSchema` in turn. Finish with a small write on a test record to confirm the confirmation gate fires before anything is saved.

## Two things that cost me time

**The manifest schema matters.** This plugin uses `vDevPreview` (`manifestVersion: "devPreview"`), not `v1.28`. In Cowork's current runtime, only the devPreview path binds the MCP connector. A `v1.28` manifest loads the skills and silently drops the connector, so the agent never invokes a tool and gives you no reason why. devPreview also wants `packageName` in reverse-DNS form and omits `mcpToolDescription` — Cowork discovers tools through MCP `tools/list`.

**Base URL must match `mcpServerUrl`.** A mismatch in the Teams developer portal registration produces no clear error. Sign-in succeeds, the connector stays disconnected, and token exchange quietly fails.

## Hosted or self-hosted

| | Hosted MCP (this plugin) | [Self-hosted](https://troystaylor.com/mcp%20(model%20context%20protocol)/copilot%20studio/integration/2026-06-01-salesforce-cowork-plugin-mcp-server.html) |
|---|---|---|
| Infrastructure | None | Azure Container App, App Insights, Bicep |
| Time to first call | Salesforce Setup only | `azd up` plus Salesforce Setup |
| Tool surface | Generic sObject tools, all objects | 16 purpose-built CRM tools |
| Custom logic and shaping | In skills only | In C# server code |
| Telemetry | Salesforce-side | Application Insights, fully controlled |
| Custom objects | Work immediately | Require server changes |
| Read-only variant | `configure.ps1 -Server sobject-reads` | Second `/mcp/federated` endpoint |
| Ongoing maintenance | Salesforce's | Yours |

Choose hosted MCP for breadth and zero infrastructure. Choose self-hosted when you need response shaping, custom telemetry, request-level policy, or tool definitions that hide the Salesforce data model from the agent.

## Known constraints

- Lead conversion and record merge have no operation on the standard sObject servers. Expose them as a Flow or invocable action on a custom server, or handle them in Salesforce.
- Opportunity products need a `Pricebook2Id` on the opportunity before `OpportunityLineItem` records can be created.
- SOQL returns at most 50,000 records per transaction; SOSL `find` returns at most 2,000.
- Deletions are recoverable for 15 days from the Recycle Bin. The connector has no undelete tool.
- Custom picklist values are the norm, so skills call `getObjectSchema` before writing picklist fields rather than assuming Salesforce defaults.

## Resources

- [Salesforce Hosted MCP Cowork plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Salesforce%20Hosted%20MCP)
- [Setup checklist](https://github.com/troystaylor/SharingIsCaring/blob/main/Cowork%20Plugins/Salesforce%20Hosted%20MCP/SETUP-CHECKLIST.md)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
- [Self-hosted Salesforce Cowork plugin](https://troystaylor.com/mcp%20(model%20context%20protocol)/copilot%20studio/integration/2026-06-01-salesforce-cowork-plugin-mcp-server.html)
- [Salesforce Hosted MCP servers in Copilot Studio](https://troystaylor.com/power%20platform/custom%20connectors/2026-06-12-salesforce-hosted-mcp-servers-copilot-studio.html)
- [Build plugins for Copilot Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
- [Configure plugin authentication](https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-authentication)
