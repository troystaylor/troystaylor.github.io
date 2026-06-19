---
layout: post
title: "Freshdesk MCP connector with 129 operations for Power Platform"
date: 2026-06-19 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Freshdesk, MCP, Custom Connectors, Power Platform, Copilot Studio, Customer Support, Freshworks]
description: "Dual-mode Power Platform custom connector for Freshdesk with 129 REST operations and MCP tools for Copilot Studio. Covers tickets, contacts, companies, agents, knowledge base, forums, custom objects, canned responses, time entries, CSAT, and bulk operations."
---

Freshdesk has a broad API surface — tickets, contacts, companies, knowledge base articles, forums, custom objects, canned responses, and more. This connector wraps 129 operations into a single dual-mode custom MCP connector for Power Platform. The MCP endpoint lets Copilot Studio agents handle support tasks conversationally. The typed operations give Power Automate full schemas and IntelliSense for the same 129 operations.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Freshdesk).

## Dual-mode architecture

Like my other MCP connectors, this one ships two interfaces in one connector:

- **MCP endpoint** — a single `InvokeMCP` operation that speaks JSON-RPC 2.0 for Copilot Studio agents
- **Typed REST operations** — 128 individual operations with full request/response schemas, parameter validation, and IntelliSense for Power Automate

Both paths share the same `script.csx` code. The MCP handler resolves tool names to Freshdesk API endpoints using the same routing logic the typed operations use.

## Authentication

Freshdesk uses API key authentication. The connector accepts the key as a secure connection parameter, injects it via a policy template header (`x-fd-apikey`), and the script converts it to HTTP Basic auth (`apiKey:X` base64-encoded) for every outbound call.

No OAuth flows to configure. Just paste your API key from **Profile Settings > API Key** in your Freshdesk portal.

## REST operations (129)

### Tickets (17)

`CreateTicket`, `ViewTicket`, `ListTickets`, `UpdateTicket`, `DeleteTicket`, `RestoreTicket`, `FilterTickets`, `ListTicketFields`, `ListTicketConversations`, `ListTicketTimeEntries`, `ForwardTicket`, `MergeTickets`, `ListWatchers`, `AddWatcher`, `RemoveWatcher`, `CreateOutboundEmail`, `ViewArchiveTicket`

### Conversations (4)

`CreateReply`, `CreateNote`, `UpdateConversation`, `DeleteConversation`

### Contacts (10)

`CreateContact`, `ViewContact`, `ListContacts`, `UpdateContact`, `DeleteContact`, `FilterContacts`, `SearchContacts`, `RestoreContact`, `HardDeleteContact`, `MergeContacts`

### Companies (7)

`CreateCompany`, `ViewCompany`, `ListCompanies`, `UpdateCompany`, `DeleteCompany`, `FilterCompanies`, `SearchCompanies`

### Agents (7)

`ViewAgent`, `ListAgents`, `GetCurrentAgent`, `CreateAgent`, `UpdateAgent`, `DeleteAgent`, `SearchAgents`

### Groups (5)

`ViewGroup`, `ListGroups`, `CreateGroup`, `UpdateGroup`, `DeleteGroup`

### Skills (5)

`ListSkills`, `ViewSkill`, `CreateSkill`, `UpdateSkill`, `DeleteSkill`

### Solutions / Knowledge base (16)

`ListSolutionCategories`, `CreateSolutionCategory`, `ViewSolutionCategory`, `UpdateSolutionCategory`, `DeleteSolutionCategory`, `ListSolutionFolders`, `CreateSolutionFolder`, `ViewSolutionFolder`, `UpdateSolutionFolder`, `DeleteSolutionFolder`, `ListSolutionArticles`, `CreateSolutionArticle`, `ViewSolutionArticle`, `UpdateSolutionArticle`, `DeleteSolutionArticle`, `SearchSolutionArticles`

### Forums / Discussions (19)

`ListForumCategories`, `CreateForumCategory`, `ViewForumCategory`, `UpdateForumCategory`, `DeleteForumCategory`, `ListForums`, `CreateForum`, `ViewForum`, `UpdateForum`, `DeleteForum`, `ListTopics`, `CreateTopic`, `ViewTopic`, `UpdateTopic`, `DeleteTopic`, `ListComments`, `CreateComment`, `UpdateComment`, `DeleteComment`

### Time entries (5)

`ListTimeEntries`, `CreateTimeEntry`, `UpdateTimeEntry`, `DeleteTimeEntry`, `ToggleTimer`

### Custom objects (7)

`ListCustomObjectSchemas`, `ViewCustomObjectSchema`, `ListCustomObjectRecords`, `CreateCustomObjectRecord`, `ViewCustomObjectRecord`, `UpdateCustomObjectRecord`, `DeleteCustomObjectRecord`

### Bulk operations (2)

`BulkUpdateTickets`, `BulkDeleteTickets`

### Ticket extras (4)

`ViewTicketSummary`, `UpdateTicketSummary`, `ListTicketForms`, `ListEmailConfigs`

### Canned responses (5)

`ListCannedResponseFolders`, `ListCannedResponses`, `ViewCannedResponse`, `CreateCannedResponse`, `UpdateCannedResponse`

### Admin / Configuration (9)

`ListRoles`, `ViewRole`, `ListSLAPolicies`, `ListProducts`, `ViewProduct`, `ListBusinessHours`, `ViewBusinessHour`, `ListScenarioAutomations`, `ViewAccount`

### Email (3)

`ListEmailMailboxes`, `ViewEmailMailbox`, `ListEmailConfigs`

### Fields (2)

`ListContactFields`, `ListCompanyFields`

### CSAT (2)

`ListSurveys`, `ListSatisfactionRatings`

### MCP (1)

`InvokeMCP`

## MCP tools for Copilot Studio

The MCP endpoint exposes all 129 capabilities as individual tools. Each tool includes a description, typed input schema with required field annotations, and maps directly to a Freshdesk API endpoint.

Some examples of what an agent can handle:

**User:** "Show me all open tickets assigned to the support group"
**Agent:** Calls `list_tickets` with status and group filters.

**User:** "Create a high-priority ticket for billing@zava.com about a failed payment"
**Agent:** Calls `create_ticket` with email, subject, description, and priority set to 3 (High).

**User:** "Find the knowledge base article about password resets and add it as a reply to ticket 4521"
**Agent:** Chains `search_solution_articles` with `create_reply`.

**User:** "Merge tickets 100, 101, and 102 into ticket 99"
**Agent:** Calls `merge_tickets` with primary_id 99 and the secondary IDs.

**User:** "Bulk update all tickets in the list to pending status and assign them to the billing group"
**Agent:** Calls `bulk_update_tickets` with the ticket IDs, status, and group_id.

## Custom objects

Freshdesk custom objects let you extend the data model beyond tickets, contacts, and companies. The connector covers the full lifecycle:

1. `list_custom_object_schemas` / `view_custom_object_schema` — discover available schemas and their fields
2. `create_custom_object_record` — create records with arbitrary field key-value pairs
3. `list_custom_object_records` / `view_custom_object_record` — read records
4. `update_custom_object_record` / `delete_custom_object_record` — modify or remove records

One thing to watch: custom object record IDs are strings (for example, `BKG-1`), not integers. The connector handles this correctly in both the typed operations and MCP tools.

## Rate limits

Freshdesk enforces per-account rate limits based on plan:

| Plan | Requests per minute |
|------|---------------------|
| Growth | 100 |
| Pro | 400 |
| Enterprise | 700 |

The `include` parameter on `ListTickets` consumes additional API credits per embedded resource, so use it selectively on lower-tier plans.

## Application Insights

To enable telemetry, set the `APP_INSIGHTS_INSTRUMENTATION_KEY` constant in `script.csx`. Telemetry is silently skipped when the placeholder value is unchanged.

Events tracked:

- `TypedOperation` — operation ID, HTTP method, status code
- `McpToolCall` — tool name, status code
- `McpError` — method, error message

## Known issues

- The `include` parameter on List Tickets consumes additional API credits per embedded resource
- Filter Tickets queries are limited to pages 1-10 (max 300 results)
- Tickets older than 30 days are only returned when using the `updated_since` filter
- Custom Object record IDs are strings (for example, `BKG-1`), not integers

## Setup

### 1. Get your Freshdesk API key

1. Log in to your Freshdesk portal.
2. Click your profile picture (top right) > **Profile Settings**.
3. Copy your API key from below the Change Password section.

### 2. Update the host

Open `apiDefinition.swagger.json` and replace the `host` value:

```json
"host": "placeholder.freshdesk.com"
```

Change `placeholder` to your Freshdesk subdomain (for example, `mycompany.freshdesk.com`).

### 3. Deploy the connector

```powershell
pac connector create --api-definition-file apiDefinition.swagger.json --api-properties-file apiProperties.json --script-file script.csx
```

### 4. Create a connection

Create a connection and paste your Freshdesk API key when prompted.

### 5. Add to Copilot Studio

1. In Copilot Studio, open your agent.
2. Add this connector as an action (MCP server).
3. Test with prompts like "List my open tickets", "Search contacts by email", or "Create a new company".

## Try it yourself

The complete connector code is in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Freshdesk):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Freshdesk/apiDefinition.swagger.json) — OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Freshdesk/script.csx) — Connector script with MCP tools and telemetry
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Freshdesk/apiProperties.json) — Connector metadata
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Freshdesk/readme.md) — Full documentation

## Resources

- [Freshdesk API reference](https://developers.freshdesk.com/api/)
- [Freshworks developer portal](https://developers.freshworks.com/)
- [Application Insights telemetry for connectors](https://troystaylor.com/power%20platform/2026-01-07-power-platform-custom-connectors-application-insights.html)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
