---
layout: post
title: "Building an Agent 365 Blueprint connector for Power Platform"
date: 2026-07-07 14:00:00 -0500
categories: [Power Platform, MCP]
tags: [Agent 365, Custom Connectors, Microsoft Graph, Entra ID, Governance, Power Automate]
description: "A Power Platform custom connector for managing Agent 365 blueprints via Microsoft Graph — creating Entra app registrations, configuring Work IQ permissions, managing secrets, and governing agent identities at scale from Power Automate."
---

Every Agent 365 agent starts with a blueprint — an Entra ID application registration that serves as the enterprise template for compliant agents. The blueprint defines which Work IQ servers the agent can access, what permissions it holds, and how it authenticates at runtime. Every agent instance inherits its blueprint's rules, ensuring consistent governance across Mail, Calendar, Teams, SharePoint, and other M365 workloads.

The [Agent 365 CLI](https://learn.microsoft.com/en-us/microsoft-agent-365/developer/agent-365-cli) (`a365 setup blueprint`, `a365 setup permissions`) automates these operations for developers. This connector provides the same capabilities in Power Automate — letting IT admins automate agent provisioning at scale, governance flows create blueprints when new teams or projects spin up, and compliance monitoring audit permissions across the tenant.

## How it relates to the Agent 365 MCP connector

These two connectors cover different halves of the Agent 365 lifecycle:

| Connector | Backend | Purpose |
|-----------|---------|---------|
| Agent 365 Blueprint (this) | Microsoft Graph | Entra lifecycle — blueprints, permissions, identity |
| [Agent 365 MCP](/power%20platform/mcp/2026-07-07-agent-365-mcp-connector.html) | Agent 365 platform | Runtime — Work IQ tools, MCPManagement, AdminTools |

Blueprint creates and governs the agent definition. MCP provides the runtime tool access. Together they cover the full lifecycle.

## Operations

The connector exposes 10 typed operations against Microsoft Graph:

| Operation | Purpose |
|-----------|---------|
| CreateBlueprint | Create an Entra app registration as an Agent 365 blueprint |
| GetBlueprint | Retrieve blueprint app registration details |
| UpdateBlueprint | Update blueprint properties and permissions |
| DeleteBlueprint | Remove the blueprint from Entra ID |
| CreateServicePrincipal | Create the SP required before granting permissions |
| GrantDelegatedPermissions | Create OAuth2 delegated grants (e.g., `Tools.ListInvoke.All`) |
| ListBlueprintPermissionGrants | List all delegated permission grants on the blueprint |
| GrantApplicationPermissions | Assign app roles for S2S auth scenarios |
| ListApplicationPermissions | List app role assignments on the blueprint |
| CreateBlueprintSecret | Generate a client secret for agent runtime auth |

## End-to-end example: provision a sales agent blueprint

Here's the typical five-step flow to create a fully configured blueprint:

```
1. CreateBlueprint
   → displayName: "Sales Agent Blueprint"
   → returns: blueprintId, appId

2. CreateServicePrincipal
   → appId: (from step 1)
   → returns: servicePrincipalId

3. GrantDelegatedPermissions
   → clientId: (SP from step 2)
   → resourceId: (Work IQ Mail MCP SP ID)
   → scope: "Tools.ListInvoke.All"

4. GrantDelegatedPermissions
   → clientId: (SP from step 2)
   → resourceId: (Work IQ Calendar MCP SP ID)
   → scope: "Tools.ListInvoke.All"

5. CreateBlueprintSecret
   → blueprintId: (from step 1)
   → displayName: "Runtime Secret"
   → returns: secretText (only returned once — store securely)
```

After these five steps, the blueprint is ready for agent instances to inherit. The agent uses the `appId` and `secretText` to authenticate at runtime and gets scoped access to only the Work IQ servers you've explicitly granted.

## Work IQ permission model

Agent 365 uses a per-server permission model. Each Work IQ MCP server has its own Entra app registration, and you grant `Tools.ListInvoke.All` to each one individually:

| Server | Scope | Grant type |
|--------|-------|-----------|
| Work IQ Mail MCP | Tools.ListInvoke.All | Per-server delegated |
| Work IQ Calendar MCP | Tools.ListInvoke.All | Per-server delegated |
| Work IQ Teams MCP | Tools.ListInvoke.All | Per-server delegated |
| Work IQ Word MCP | Tools.ListInvoke.All | Per-server delegated |
| Work IQ Tools (metadata) | McpServersMetadata.Read.All | Shared metadata access |

To resolve server SP IDs in your tenant:

```
GET /v1.0/servicePrincipals?$filter=displayName eq 'Work IQ Mail MCP'
```

The legacy shared-scope model (`McpServers.Mail.All`, etc.) is deprecated. Use per-server `Tools.ListInvoke.All` for all new blueprints.

## Authentication and prerequisites

The connector authenticates via OAuth 2.0 with the `https://graph.microsoft.com/.default` scope. The Entra app registration for the connector itself needs these application permissions (with admin consent):

- `Application.ReadWrite.All` — create and manage app registrations
- `DelegatedPermissionGrant.ReadWrite.All` — manage OAuth2 grants
- `AppRoleAssignment.ReadWrite.All` — manage app role assignments

The signed-in user needs at minimum the **Agent ID Developer** role for blueprint creation, and **Global Administrator** for OAuth2 permission grants.

## Deployment

1. Import via Maker portal (Custom connectors > Import OpenAPI) or deploy with PAC CLI:

```powershell
pac connector create `
    -df apiDefinition.swagger.json `
    -sf script.csx `
    -env <environment-id>
```

2. Configure OAuth in the Security tab with your app registration client ID and the `https://graph.microsoft.com/.default` scope
3. Create a connection — admin consent is required for the Graph permissions

## Key behaviors

- All operations are idempotent — safe to retry
- Blueprint deletion does NOT cascade to agent instances; clean up instances separately
- Secret values are only returned once on creation — store them in Key Vault or a secure variable
- The connector uses `script.csx` only for request shaping (no MCP proxy logic needed since Graph is the direct backend)

## Use cases

**Automated agent provisioning** — When a new project is created in your ITSM system, a Power Automate flow creates the blueprint, grants the appropriate Work IQ permissions, and stores the secret in Key Vault. The dev team gets a ready-to-use agent identity.

**Compliance auditing** — A scheduled flow calls `ListBlueprintPermissionGrants` across all blueprints and flags any that have overly broad permissions or missing expiry dates on secrets.

**Self-service agent onboarding** — A Power App lets team leads request agent blueprints with pre-approved permission sets. An approval flow provisions the blueprint with only the requested scopes.

The full source is available in the [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Agent%20365%20Blueprint).
