---
layout: post
title: "Copilot Package Management MCP connector for Copilot Studio"
date: 2026-05-11 11:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, Microsoft Graph, Package Management, IT Operations]
---

IT admins manage Copilot agents and apps through the Microsoft 365 admin center—one package at a time. The Microsoft Graph beta Package Management API exposes the tenant catalog programmatically, but there's no built-in Power Platform connector for it. This custom connector surfaces 6 MCP tools so a Copilot Studio agent can inventory, inspect, block, unblock, update access, and reassign ownership of packages without leaving the conversation.

## What the connector covers

The connector wraps the `beta/copilot/admin/catalog/packages` endpoint with both standard Power Automate operations and MCP tools for Copilot Studio.

### Standard operations (Power Automate)

| Operation | Description |
|-----------|-------------|
| List packages | Retrieve all Copilot agents and apps in the tenant catalog. Supports `$filter` on `supportedHosts`, `elementTypes`, and `lastModifiedDateTime` |
| Get package details | Get detailed metadata for a specific package including element details, categories, and access information |
| Update package | Update the allowed and acquired users/groups for a package |
| Block package | Block a package to prevent usage across the organization |
| Unblock package | Unblock a package to allow usage |
| Reassign package | Reassign package ownership to a different user |

### MCP tools (Copilot Studio)

| Tool | Description |
|------|-------------|
| list_packages | List all packages with optional filters for host, element type, and modified date |
| get_package_details | Get detailed metadata for a specific package |
| block_package | Block a package to prevent usage |
| unblock_package | Unblock a package to allow usage |
| update_package_access | Update allowed and acquired users/groups for availability and deployment control |
| reassign_package | Reassign package ownership to a new user |

## Filtering

The `list_packages` tool supports three filter parameters that map to OData `$filter` expressions:

| Parameter | Values | Example filter |
|-----------|--------|----------------|
| supportedHost | Copilot, Outlook, Teams, M365 | `supportedHosts/any(h:h eq 'Copilot')` |
| elementType | Bots, DeclarativeAgent, CustomEngineAgent, OfficeAddIns | `elementTypes/any(h:h eq 'DeclarativeAgent')` |
| lastModifiedAfter | ISO 8601 date | `lastModifiedDateTime gt 2026-01-01T00:00:00Z` |

Filters combine with `and` when multiple parameters are provided. The MCP tool builds the OData expression automatically—the agent just passes the values.

## Package metadata

Each package returned by `list_packages` includes:

- **displayName** — human-readable name
- **type** — microsoft, external, shared, or custom
- **isBlocked** — whether the package is administratively blocked
- **availableTo / deployedTo** — scope: all, some, or none
- **supportedHosts** — where the package runs (Copilot, Teams, Outlook, M365)
- **elementTypes** — what's inside (Bots, DeclarativeAgent, CustomEngineAgent)
- **publisher, version, platform** — origin and version info

The `get_package_details` tool returns additional fields: `longDescription`, `sensitivity`, `categories`, `allowedUsersAndGroups`, `acquireUsersAndGroups`, and `elementDetails`.

## Agent scenarios

**Inventory audit:**
> "List all declarative agents in the tenant" → Agent calls `list_packages` with `elementType: DeclarativeAgent` → returns every declarative agent with publisher, version, and deployment scope

**Block a rogue agent:**
> "Block the package with ID abc-123" → Agent calls `block_package` → package is immediately prevented from running across the organization

**Access control:**
> "Make this agent available only to the Sales team" → Agent calls `update_package_access` with the Sales group ID in `allowedUsersAndGroups` → restricts availability to that group

**Ownership transfer:**
> "Reassign all of Kim's agents to Alex" → Agent calls `list_packages` → filters by publisher → calls `reassign_package` for each package with Alex's user ID

**Recently changed packages:**
> "What agents were modified in the last 30 days?" → Agent calls `list_packages` with `lastModifiedAfter: 2026-04-11T00:00:00Z` → returns recently updated packages for review

## Prerequisites

- A [Microsoft Agent 365](https://www.microsoft.com/microsoft-agent-365) license
- An Entra ID app registration with these delegated permissions:
  - `CopilotPackages.Read.All` — list and view packages
  - `CopilotPackages.ReadWrite.All` — block, unblock, update, and reassign packages
- Global Administrator or appropriate admin role to manage packages

## Setup

1. Register an Entra ID application (or use an existing one)
2. Add the delegated permissions listed above
3. Grant admin consent
4. Add the redirect URI: `https://global.consent.azure-apim.net/redirect`
5. Update `apiProperties.json` with your client ID
6. Deploy with PAC CLI:

```powershell
pac connector create `
  --api-definition-file apiDefinition.swagger.json `
  --api-properties-file apiProperties.json `
  --script-file script.csx
```

For Copilot Studio:

1. Open your agent
2. Go to **Actions** > **Add an action** > **Connector**
3. Search for your connector and add it
4. The agent discovers all 6 tools automatically

## Application Insights

Add your connection string to `script.csx` to track:

- All incoming requests with correlation IDs
- MCP tool invocations with timing
- Errors with full exception details

## Important notes

- This API is in beta and subject to change. Don't use in production.
- Only available in the Global service cloud (not US Government or China).
- The `List packages` operation only supports delegated permissions (not application-only).
- Requires a Microsoft Agent 365 license.

## Resources

- [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Package%20Management)
- [Package Management API overview](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/admin-settings/package/overview)
- [copilotPackage resource](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/admin-settings/package/resources/copilotpackage)
- [copilotPackageDetail resource](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/admin-settings/package/resources/copilotpackagedetail)
