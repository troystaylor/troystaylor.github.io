---
layout: post
title: "Workato MCP connector for Power Platform"
date: 2026-04-13 14:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Workato, MCP, Copilot Studio, Custom Connectors, Power Platform, Automation, Integration, Agent Studio]
description: "Power Platform custom connector for the Workato Developer API—manage recipes, connections, jobs, Agent Studio genies, MCP servers, data tables, and deployments through 225 REST operations and 46 MCP tools."
---

[Workato](https://www.workato.com/) is an enterprise automation platform with its own recipe engine, connection framework, and—more recently—its own [Agent Studio](https://docs.workato.com/agent-studio.html) for building AI genies and [MCP server hosting](https://docs.workato.com/mcp.html). Organizations running Workato alongside Power Platform now have a management problem: two automation platforms, two sets of recipes, two places to monitor jobs.

This MCP connector wraps the full [Workato Developer API](https://www.workato.com/developers) with 225 operations for Power Automate and Power Apps, plus 46 MCP tools for Copilot Studio agents. Manage Workato from inside Power Platform—start recipes, check job status, query data tables, manage Agent Studio genies, and even administer Workato's own MCP servers—all without switching consoles.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Workato)

## 225 operations across 12 categories

| Category | Operations | What you can do |
|----------|-----------|-----------------|
| Recipes | 18 | List, create, get, update, delete, copy, start, stop, reset trigger, poll, health analysis, versions |
| Jobs | 5 | List jobs, get details, repeat, test cases, resume |
| Connections | 5 | List, create, update, delete, disconnect |
| Folders and projects | 7 | List, create, update, delete folders and projects |
| Lookup tables | 8 | List, create, batch delete tables; lookup, list, add, update, delete rows |
| Agent Studio | 16 | Manage genies, knowledge bases, skills, user groups |
| MCP servers | 14 | List, create, get, update, delete servers; renew tokens, assign tools, manage policies |
| Data tables | 6 | List, create, get, update, delete, truncate |
| API platform | 14 | Manage API collections, endpoints, clients, keys, portals |
| Environment and configuration | 22 | Certificates, connectors, OAuth profiles, activity logs, tags, properties, secrets |
| Recipe lifecycle and deployments | 21 | Manifests, packages, builds, deployments, review workflow (assign, submit, approve, reject) |
| Workspace management | 18 | Members, invitations, privileges, IAM users, user groups, app links |

## 46 MCP tools

When added as an MCP connector in Copilot Studio, the agent gets 46 curated tools:

| Domain | Tools | Coverage |
|--------|-------|----------|
| Workspace | 1 | Get workspace details |
| Recipes | 7 | List, get, start, stop, health, versions |
| Jobs | 2 | List jobs, get job details |
| Connections | 1 | List connections |
| Folders and projects | 2 | List folders, list projects |
| Data | 5 | Lookup tables, data tables |
| Agent Studio | 7 | Genies, knowledge bases, skills |
| MCP servers | 3 | List, get, list tools |
| API platform | 2 | Collections, endpoints |
| Environment | 5 | Activity logs, tags, properties, event topics |
| Deployments | 4 | List/get deployments, builds |
| Members | 2 | List, get members |
| Testing | 2 | Run, get test results |
| RLCM | 2 | Export/get packages |

## How it works

```
User: "What Workato recipes failed today?"

1. Orchestrator calls list_recipes({
     active: true
   })

   → Returns recipe list with IDs

2. Orchestrator calls list_jobs({
     recipe_id: "12345",
     status: "failed",
     since: "2026-04-13T00:00:00Z"
   })

   → Returns: 2 failed jobs
     Job 98765: "Salesforce sync" - Failed at step 3: Connection timeout
     Job 98766: "Salesforce sync" - Failed at step 3: Connection timeout

3. Agent responds: "Your Salesforce sync recipe had 2 failures today,
   both from connection timeouts at step 3. Want me to check the
   Salesforce connection status?"
```

```
User: "Start the weekly report recipe"

1. Orchestrator calls list_recipes({
     filter: "weekly report"
   })

   → Recipe ID: 54321, Status: Stopped

2. Orchestrator calls start_recipe({
     id: "54321"
   })

   → Recipe started successfully
```

## Managing Workato's Agent Studio from Copilot Studio

The connector includes 16 Agent Studio operations—you can manage Workato's AI genies from a Copilot Studio agent. List genies, start and stop them, assign skills and knowledge bases, and manage user group access.

This creates an interesting cross-platform pattern: a Copilot Studio agent that administers Workato's own agent infrastructure. Useful for organizations consolidating AI agent management into a single pane.

| Operation | What it does |
|-----------|-------------|
| List genies | Inventory all Agent Studio genies |
| Create/update genie | Configure genie name, description, instructions |
| Start/stop genie | Control genie availability |
| Assign/remove skills | Manage which skills a genie can use |
| Assign/remove knowledge bases | Control genie knowledge sources |
| Manage user groups | Control who can interact with a genie |

## Workato MCP servers from Power Platform

Workato now hosts MCP servers natively. This connector gives you 14 operations to manage those servers from Power Platform—list servers, create new ones, assign tools, update policies, renew tokens, and manage user group access.

A cross-platform MCP management scenario: monitor Workato-hosted MCP servers alongside your Power Platform connectors from a single Copilot Studio agent.

## Deployment lifecycle management

The connector covers Workato's full recipe lifecycle management (RLCM) workflow:

```
Export manifest → Build package → Deploy to target environment
                                         ↓
                              Review workflow:
                              Assign → Submit → Approve/Reject → Reopen
```

Automate Workato deployments from Power Automate. Build a flow that exports a recipe package from development, deploys it to staging, and routes an approval to the release manager—all without touching the Workato console.

## Supported data centers

| Region | Host |
|--------|------|
| US (default) | www.workato.com |
| EU | app.eu.workato.com |
| JP | app.jp.workato.com |
| SG | app.sg.workato.com |
| AU | app.au.workato.com |
| IL | app.il.workato.com |
| Developer Sandbox | app.trial.workato.com |

Select your data center when creating the connection. All API calls route to the correct host automatically.

## Use cases

**Cross-platform automation monitoring**: Build a Power Automate flow that checks Workato job health alongside Power Automate flow runs. Surface failures from both platforms in a single Teams notification or Dataverse dashboard.

**Recipe management agent**: A Copilot Studio agent that lets operations teams start, stop, and troubleshoot Workato recipes through natural language. "Why did the Salesforce sync fail?" The agent checks job history, connection status, and recipe health in one conversation.

**Deployment automation**: Trigger Workato recipe deployments from a Power Automate approval flow. When a release manager approves in Teams, the flow exports the package, deploys it, and logs the deployment in Dataverse.

**Agent Studio administration**: Manage Workato's AI genies from inside Copilot Studio. Provision genies, assign skills and knowledge bases, and control user access—useful for organizations standardizing agent management across platforms.

**Data table synchronization**: Sync Workato data tables with Dataverse using Power Automate. Keep reference data consistent across both platforms without manual exports.

## Prerequisites

1. A [Workato](https://www.workato.com/) workspace (any plan)
2. An API client token generated from **Workspace admin > API clients**
3. Knowledge of which [data center](https://docs.workato.com/security/data-protection/data-center.html) your workspace is hosted on

## Authentication

1. Sign in to your Workato workspace.
2. Navigate to **Workspace admin > API clients**.
3. Click **Create API client** (or select an existing client).
4. Assign the appropriate role with permissions for the APIs you need.
5. Generate and copy the API token.

## Known limitations

- Workato API has rate limits per endpoint category (typically 60-2,000 requests/minute). Check the [Workato API documentation](https://docs.workato.com/workato-api.html) for details.
- OAuth connection creation via the API requires pre-existing access/refresh tokens. Shell connections can be created instead.
- Starting May 7, 2026, `folder_id` becomes required for recipe and connection creation endpoints.

## Setting up the connector

1. Download the connector files from the [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Workato)
2. Import into Power Platform:

```powershell
pac auth create --environment "https://yourorg.crm.dynamics.com"
pac connector create --api-definition apiDefinition.swagger.json --api-properties apiProperties.json --script script.csx
```

Or import manually through **Power Automate > Data > Custom Connectors > Import an OpenAPI file**.

## Resources

- [Workato Developer API documentation](https://docs.workato.com/workato-api.html)
- [Workato Agent Studio](https://docs.workato.com/agent-studio.html)
- [Workato MCP server hosting](https://docs.workato.com/mcp.html)
- [Full connector source](https://github.com/troystaylor/SharingIsCaring/tree/main/Workato)
