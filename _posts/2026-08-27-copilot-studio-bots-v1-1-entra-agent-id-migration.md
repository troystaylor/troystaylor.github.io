---
layout: post
title: "Migrate Copilot Studio agents to Microsoft Entra Agent ID with v1.1"
date: 2026-08-27 17:30:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Copilot Studio, Microsoft Entra Agent ID, Custom Connectors, MCP, Power Automate, Agent Identity, Governance, Power Platform API]
description: "Copilot Studio Bots v1.1 adds Power Automate actions and MCP tools to migrate older agents to Microsoft Entra Agent ID, validate them in stages, and roll them back when needed."
---

Copilot Studio changed how it identifies agents in May 2026. New agents now receive a Microsoft Entra Agent ID, while older agents keep the app registration Copilot Studio created for them.

Microsoft plans to migrate those older agents in a future update. [Copilot Studio Bots v1.1](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Bots) lets you move first, test the result, and roll back an agent that fails validation.

The release adds two Power Automate actions and two Model Context Protocol (MCP) tools to the evaluation, inventory, and containment connector introduced in the [original post](/power%20platform/custom%20connectors/mcp/2026-08-20-copilot-studio-bots-connector.html).

## What's new in v1.1

| | v1.0 | v1.1 |
|---|---:|---:|
| Documented Bots API operations | 13 | 13 |
| Power Automate actions | 16 | 18 |
| MCP tools | 16 | 18 |
| OpenAPI operations, including MCP | 17 | 19 |
| Agent identity migration | No | Migrate and roll back |

The two new Power Automate actions are:

| Action | Result |
|---|---|
| **Migrate Agent Identity To Entra Agent ID** | Converts an older agent's app-registration identity to a Microsoft Entra Agent ID |
| **Roll Back Agent Identity To App Registration** | Reverts a migrated agent when validation fails |

Copilot Studio agents get matching tools:

- `migrate_agent_identity`
- `rollback_agent_identity`

Both take an environment ID and agent ID. The Power Automate actions use the connector's existing cascading dropdowns, while MCP callers can use `list_agents` to find the raw identifiers first.

## Why migrate before Microsoft does

A Microsoft Entra Agent ID gives administrators a first-class identity for each agent. Microsoft lists several benefits:

- Agent sign-in and audit logs in Microsoft Entra
- Agent lifecycle management
- Connector permissions visible as API permissions
- Conditional Access policies scoped to agent activity
- Integration with Microsoft Entra ID Governance

Manual migration gives you a window to test those controls against your own channels, connectors, actions, flows, and authentication settings before automatic migration reaches the tenant.

The migration converts the identity **in place**. The application (client) ID stays the same, so channel registrations and connectors continue to resolve to the same identifier. A successful response also returns the new `agentIdentityId` and `servicePrincipalObjectId` for lookup in the Microsoft Entra admin center.

## The API sits next to the Bots operations

The new routes use the same Power Platform host, agent path, OAuth connection, and `2024-10-01` API version as the connector's 13 Bots operations:

```text
POST https://api.powerplatform.com/copilotstudio/
     environments/{environmentId}/bots/{botId}/
     api/agentidentitymigration/migrate?api-version=2024-10-01

POST https://api.powerplatform.com/copilotstudio/
     environments/{environmentId}/bots/{botId}/
     api/agentidentitymigration/rollback?api-version=2024-10-01
```

They aren't part of the [Bots REST operation group](https://learn.microsoft.com/rest/api/power-platform/copilotstudio/bots). Microsoft documents them separately in the [agent identity migration guide](https://learn.microsoft.com/microsoft-copilot-studio/govern-migrate-api-entra-agent-identity), and the manual migration feature is in preview.

Neither request has a body. A migration returns one of two terminal statuses:

```json
{
  "status": "Migrated",
  "cdsBotId": "00000000-0000-0000-0000-000000000000",
  "environmentId": "00000000-0000-0000-0000-000000000000",
  "tenantId": "00000000-0000-0000-0000-000000000000",
  "agentIdentityId": "00000000-0000-0000-0000-000000000000",
  "applicationId": "00000000-0000-0000-0000-000000000000",
  "servicePrincipalObjectId": "00000000-0000-0000-0000-000000000000",
  "completedAtUtc": "2026-08-27T20:00:00Z"
}
```

`AlreadyMigrated` is also a successful result. Migration is idempotent, so a repeated call doesn't create a second identity.

Rollback returns `RolledBack` or `NotMigrated`. `NotMigrated` means there was nothing to undo, not that the request failed.

## Migrate in stages

Migration affects a live agent. Microsoft recommends a staged rollout instead of moving the whole estate at once:

1. Pick a small group of noncritical agents
2. Include the channels, authentication modes, connectors, flows, and integrations you need to test
3. Coordinate a validation window with the makers
4. Migrate one agent or a small batch
5. Test every published channel, action, connector, and authentication flow
6. Review Microsoft Entra sign-in logs and Conditional Access results
7. Roll back failures before starting the next batch

The API migrates one agent per request. A Power Automate flow can loop over a planned batch, but leave room between calls. The service can return `429 Too Many Requests`, and the connector surfaces that response instead of hiding it behind automatic retries.

Administrative permissions still apply. The caller must be a Power Platform Administrator, Dynamics 365 Administrator, or Global Administrator. A caller without the required role receives `403 Forbidden`.

## Use an agent for a plan-and-apply migration

The existing `list_agents` tool makes identity migration easier to control. Let the agent inventory the environment first, then name the agents to migrate:

```text
User: List the unpublished agents in the sandbox environment.

Agent:
  1. list_agents { environmentId: "<sandbox-environment-id>" }
  2. Presents agent names, owners, publish state, and IDs

User: Migrate Contoso Support Test and Expense Policy Test.

Agent:
  3. migrate_agent_identity { environmentId, botId } for each named agent
  4. Reports Migrated or AlreadyMigrated and the new agent identity IDs

User: Expense Policy Test can no longer authenticate in Teams. Roll it back.

Agent:
  5. rollback_agent_identity { environmentId, botId }
  6. Reports RolledBack
```

This keeps discovery separate from the write. The user sees the inventory and names the migration set before any identity changes.

Rollback makes the operation recoverable, but it doesn't replace testing. Stop the batch when an agent fails validation, undo that agent, and find the cause before continuing.

## Update the connector

Replace `REPLACE_WITH_CLIENT_ID` in `apiProperties.json`, then validate and update the connector with the Power Platform Connector CLI and Power Platform CLI:

```powershell
ppcv "./Copilot Studio Bots"

pac connector update `
    --connector-id 00000000-0000-0000-0000-000000000000 `
    --api-definition-file apiDefinition.swagger.json `
    --api-properties-file apiProperties.json `
    --script-file script.csx
```

Keep `--script-file`. The MCP endpoint and its two new tools run through `script.csx`, and the connector declares script operations in `apiProperties.json`.

Existing flows keep their actions. After the update, the two migration actions appear beside evaluation, quarantine, consent bypass, reassignment, deletion, and agent inventory.

## Resources

- [Copilot Studio Bots v1.1 source](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Bots)
- [v1.1 commit](https://github.com/troystaylor/SharingIsCaring/commit/59247f57bfc530dfac84cc5a17c196bdfef8f904)
- [Microsoft Entra Agent IDs for Copilot Studio](https://learn.microsoft.com/microsoft-copilot-studio/admin-use-entra-agent-identities)
- [Migrate agents to Microsoft Entra Agent ID](https://learn.microsoft.com/microsoft-copilot-studio/govern-migrate-api-entra-agent-identity)
- [Original Copilot Studio Bots post](/power%20platform/custom%20connectors/mcp/2026-08-20-copilot-studio-bots-connector.html)
