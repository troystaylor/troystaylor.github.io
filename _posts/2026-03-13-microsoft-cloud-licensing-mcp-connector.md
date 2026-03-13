---
layout: post
title: "Microsoft Cloud Licensing MCP connector for Copilot Studio"
date: 2026-03-13 11:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, Microsoft Graph, Licensing]
---

Managing Microsoft 365 licenses through the admin center works until you need to automate it. The Microsoft Graph Cloud Licensing API (beta) exposes allotments, assignments, usage rights, assignment errors, and waiting members programmatically—but there's no built-in Power Platform connector for it. This custom connector exposes 28 MCP tools so a Copilot Studio agent can manage your organization's license allocation end to end.

## What the connector covers

### Allotments (2 tools)

Allotments represent pools of licenses for a specific SKU. Each allotment shows how many units are allotted vs. consumed, what services are included, and which subscriptions back it.

| Tool | Description |
|------|-------------|
| list_allotments | List all license allotments in the organization |
| get_allotment | Get details of a specific license allotment |

### Allotment assignments (2 tools)

Link users or groups to allotments and optionally disable specific service plans within the SKU.

| Tool | Description |
|------|-------------|
| list_allotment_assignments | List assignments consuming from an allotment |
| create_allotment_assignment | Create a new license assignment for an allotment |

### Allotment waiting members (2 tools)

When an allotment is over-assigned, excess users are placed in a waiting room until licenses free up.

| Tool | Description |
|------|-------------|
| list_allotment_waiting_members | List over-assigned users in the waiting room |
| get_allotment_waiting_member | Get details of a specific waiting member |

### Organization assignments (4 tools)

Manage license assignments across the entire organization:

| Tool | Description |
|------|-------------|
| list_assignments | List all license assignments in the organization |
| get_assignment | Get details of a specific assignment |
| update_assignment | Update an assignment to enable or disable services |
| delete_assignment | Delete a license assignment |

### Assignment errors (2 tools)

When license synchronization fails—conflicting assignments, insufficient licenses—the API captures the errors:

| Tool | Description |
|------|-------------|
| list_assignment_errors | List assignment synchronization errors (org-level) |
| get_assignment_error | Get details of a specific assignment error |

### User-scoped (6 tools)

Drill into a specific user's license state:

| Tool | Description |
|------|-------------|
| list_user_usage_rights | List usage rights for a user |
| get_user_usage_right | Get a specific usage right for a user |
| list_user_assignments | List license assignments for a user |
| list_user_assignment_errors | List assignment errors for a user |
| list_user_waiting_members | List allotments a user is waiting for |
| reprocess_user_assignments | Reprocess assignments to fix sync issues |

The `reprocess_user_assignments` tool is particularly useful—it retriggers license synchronization for a user when assignments get stuck.

### Group-scoped (3 tools)

| Tool | Description |
|------|-------------|
| list_group_usage_rights | List usage rights for a group |
| get_group_usage_right | Get a specific usage right for a group |
| list_group_assignments | List license assignments for a group |

### Signed-in user (4 tools)

Self-service tools for the current user:

| Tool | Description |
|------|-------------|
| list_my_usage_rights | List the signed-in user's usage rights |
| list_my_assignments | List the signed-in user's assignments |
| list_my_waiting_members | List allotments the signed-in user is waiting for |
| list_my_assignment_errors | List assignment errors for the signed-in user |

## Pairs with the Copilot Licensing connector

This connector answers "Who has which licenses and are there assignment failures?" The [Copilot Licensing connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Licensing) answers "How many Copilot Studio credits are my agents consuming?" Together they cover allocation and consumption—the full licensing picture.

| Question | Connector |
|----------|-----------|
| How many M365 E5 licenses are assigned? | Cloud Licensing |
| Are any users waiting for licenses? | Cloud Licensing |
| Which service plans are disabled for a user? | Cloud Licensing |
| How many Copilot credits did my agents burn? | Copilot Licensing |
| What's my billed vs. non-billed credit split? | Copilot Licensing |

## Agent scenarios

**License audit:**
> "Show me all allotments that are over 90% consumed" → Agent calls `list_allotments` → filters by consumed vs. allotted units → flags allotments nearing capacity

**Onboarding:**
> "Assign an E5 license to the new hire" → Agent calls `list_allotments` to find the E5 allotment → `create_allotment_assignment` with the user's ID

**Troubleshooting:**
> "Why doesn't this user have Teams?" → Agent calls `list_user_usage_rights` → checks service plans → `list_user_assignment_errors` → finds conflicting assignment → `reprocess_user_assignments` to retry

**Waiting room management:**
> "Who's stuck waiting for licenses?" → Agent calls `list_allotment_waiting_members` → returns users with `waitingSinceDateTime` → prioritizes by longest wait

**Self-service:**
> "What licenses do I have?" → Agent calls `list_my_usage_rights` → summarizes active SKUs and service plans

## Important notes

### Beta API only

All endpoints use the Microsoft Graph beta API. There are no v1.0 endpoints for the `cloudLicensing` namespace yet. Beta endpoints may change without notice.

### ETag and OData patterns

Assignment creation uses `@odata.bind` for the `assignedTo` relationship. Some list operations may need `$top` for large tenants. The `reprocessAssignments` action returns 204 No Content on success.

## Prerequisites

Azure AD app registration with these delegated permissions:

- `CloudLicensing.ReadWrite.All` - Manage cloud licensing
- `User.Read.All` - Read user profiles
- `Group.Read.All` - Read group profiles
- `Directory.Read.All` - Read directory data

Admin consent is required for all permissions.

## Setup

1. Register an Azure AD application
2. Add the delegated permissions listed above
3. Generate a client secret
4. Grant admin consent
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
4. The agent discovers all 28 tools automatically

## Application Insights

Add your connection string to `script.csx` to track:

- All incoming requests with operation IDs
- MCP tool invocations with timing
- Errors with full exception details

## Resources

- [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Cloud%20Licensing)
- [Cloud Licensing API overview](https://learn.microsoft.com/en-us/graph/api/resources/cloud-licensing-api-overview?view=graph-rest-beta)
- [Allotment resource](https://learn.microsoft.com/en-us/graph/api/resources/cloudlicensing-allotment?view=graph-rest-beta)
- [Assignment resource](https://learn.microsoft.com/en-us/graph/api/resources/cloudlicensing-assignment?view=graph-rest-beta)
- [Copilot Licensing connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Licensing)
