---
layout: post
title: "Zendesk MCP connector for Power Platform"
date: 2026-03-19 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Zendesk, MCP, Custom Connectors, Power Platform, Copilot Studio, Ticketing, Help Center, CSAT, SLA]
description: "Power Platform custom connector for Zendesk Support API v2 with 42 REST operations, 41 MCP tools for Copilot Studio, Help Center integration, and Application Insights telemetry."
---

Zendesk Support covers ticketing, user management, organizations, Help Center articles, SLA policies, satisfaction ratings, and more—each behind its own set of API endpoints. This connector wraps 42 REST operations across 9 Zendesk API areas into a single Power Platform custom connector with 41 MCP tools for Copilot Studio agents, built-in search syntax references, and Application Insights telemetry.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Zendesk).

## What's included

### Tickets (11 operations)

List, get, create, update, delete, and merge tickets. Retrieve conversation threads, time metrics (first reply, resolution, wait times), related info (incidents, followups), full audit trails, and system and custom ticket field definitions.

### Users (6 operations)

List users filtered by role, get a specific user, create end-users or agents, update profiles, get tickets requested by or assigned to a user, and list all identities (email, phone, social).

### Organizations (5 operations)

List organizations, get details by ID, create new organizations, get tickets for an org, and list user-organization memberships.

### Groups (3 operations)

List agent groups, get details, and list agent-group memberships.

### Search (1 operation)

Full-text search across tickets, users, organizations, and other Zendesk objects using Zendesk search syntax.

### Views (3 operations)

List available views, execute a view to return its tickets, and get ticket counts for a view.

### Satisfaction Ratings, Tags, Macros (3 operations)

List CSAT ratings with score and date filters, list popular tags, and list macros.

### Help Center (8 operations)

List articles by section, category, or label. Get full article content. Search articles by keyword. List articles within a section. Create articles in a section. Browse sections and categories, including sections within a specific category.

### SLA Policies (2 operations)

List all SLA policies with targets and get a specific SLA policy by ID.

## MCP tools for Copilot Studio

The connector exposes 41 MCP tools via JSON-RPC 2.0:

| Tool | Description |
|------|-------------|
| `search` | Search Zendesk using search syntax (tickets, users, organizations) |
| `list_tickets` | List tickets with sorting and pagination |
| `get_ticket` | Get a specific ticket by ID |
| `create_ticket` | Create a new ticket with subject, priority, type, requester, assignee, tags |
| `update_ticket` | Update ticket status, priority, assignee, add comments, modify tags |
| `delete_ticket` | Soft-delete a ticket |
| `merge_tickets` | Merge source tickets into a target ticket |
| `get_ticket_comments` | Get the full conversation thread on a ticket |
| `get_ticket_metrics` | Get time metrics (first reply, resolution, wait times) |
| `get_ticket_related` | Get related info (incidents, followups) |
| `get_ticket_audits` | Get full audit trail for a ticket |
| `list_ticket_fields` | List system and custom ticket fields |
| `list_ticket_attachments` | List all attachments on a ticket across comments |
| `list_users` | List users filtered by role |
| `get_user` | Get a specific user by ID |
| `create_user` | Create a new end-user, agent, or admin |
| `update_user` | Update user profile details |
| `get_user_tickets` | Get tickets requested by, assigned to, or CC'd to a user |
| `list_user_identities` | List all identities (email, phone, etc.) for a user |
| `list_organizations` | List organizations |
| `get_organization` | Get a specific organization by ID |
| `create_organization` | Create a new organization |
| `get_organization_tickets` | Get tickets for an organization |
| `list_organization_memberships` | List org memberships (filter by user or org) |
| `list_groups` | List agent groups |
| `get_group` | Get a specific group by ID |
| `list_group_memberships` | List group memberships (filter by user or group) |
| `list_views` | List available views |
| `get_view_tickets` | Execute a view and return its tickets |
| `get_view_count` | Get ticket count for a view |
| `list_satisfaction_ratings` | List CSAT ratings with score and date filters |
| `list_tags` | List popular recent tags |
| `list_macros` | List available macros |
| `list_articles` | List Help Center articles by section, category, or label |
| `get_article` | Get a specific Help Center article by ID |
| `search_articles` | Search Help Center articles by keyword |
| `create_article` | Create a new Help Center article in a section |
| `list_sections` | List Help Center sections (optionally by category) |
| `list_categories` | List Help Center categories |
| `list_sla_policies` | List all SLA policies and their targets |
| `get_sla_policy` | Get a specific SLA policy by ID |

Add the connector as an action in Copilot Studio, and the agent discovers the tools automatically. Users can then interact with Zendesk through natural conversation:

**User:** "Show me all open urgent tickets assigned to me"
**Agent:** *Calls `search` with `type:ticket status:open priority:urgent assignee:me`*

**User:** "Search the Help Center for password reset articles"
**Agent:** *Calls `search_articles` with the keyword and returns matching results*

**User:** "Create a ticket for a billing issue reported by the Acme account"
**Agent:** *Calls `create_ticket` with subject, priority, and organization details*

**User:** "Summarize the conversation on ticket 12345"
**Agent:** *Calls `get_ticket_comments` and returns the thread summary*

## MCP resources

The connector includes reference resources that the agent can consult during conversations:

| Resource | Description |
|----------|-------------|
| `zendesk://reference/search-syntax` | Comprehensive Zendesk search query syntax guide |
| `zendesk://reference/ticket-statuses` | Ticket statuses, transitions, priorities, and types reference |
| `zendesk://tickets/{id}` | Resource template—retrieve a ticket by ID |
| `zendesk://users/{id}` | Resource template—retrieve a user by ID |

## MCP prompts

| Prompt | Description |
|--------|-------------|
| `triage_ticket` | Analyze a ticket and suggest priority, type, group, and next steps |
| `summarize_ticket` | Summarize a ticket conversation for handoff or escalation |

## Setup

### Zendesk OAuth prerequisites

1. In Zendesk Admin Center, go to **Apps and integrations > APIs > Zendesk API > OAuth Clients**.
2. Click **Add OAuth Client**.
3. Fill in the details:
   - **Client name:** Power Platform Connector
   - **Redirect URLs:** `https://global.consent.azure-apim.net/redirect`
   - **Description:** Power Platform custom connector integration
4. Save and note the **Client ID** and **Client Secret**.

### Import the connector

Use the Power Platform CLI:

```bash
paconn create --api-def apiDefinition.swagger.json --api-prop apiProperties.json --script script.csx
```

After import, replace `yoursubdomain` with your Zendesk subdomain in:

- `apiDefinition.swagger.json`—the `host` field
- `apiProperties.json`—all OAuth URL templates

Enter your Client ID and Client Secret from the Zendesk OAuth client.

## Search syntax reference

Zendesk uses a structured search syntax for filtering across object types:

```
type:ticket status:open priority:urgent assignee:me
type:ticket created>7days -status:closed
type:ticket tags:billing organization:"Acme Inc"
type:user role:agent email:@example.com
```

The `search` MCP tool and the `zendesk://reference/search-syntax` resource give the agent full access to this syntax, so users can express complex queries in natural language.

## Application Insights (optional)

Update the `APP_INSIGHTS_CONNECTION_STRING` constant in `script.csx` with your Application Insights connection string to enable telemetry.

## Try it yourself

The complete connector code is available in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Zendesk):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Zendesk/apiDefinition.swagger.json)—OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Zendesk/script.csx)—Connector script with MCP tools and telemetry
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Zendesk/apiProperties.json)—Connector metadata
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Zendesk/readme.md)—Full documentation

## Resources

- [Zendesk Support API documentation](https://developer.zendesk.com/api-reference/)
- [Zendesk Search API](https://developer.zendesk.com/api-reference/ticketing/ticket-management/search/)
- [Zendesk OAuth authentication](https://developer.zendesk.com/api-reference/ticketing/introduction/#oauth-authentication)
- [Application Insights telemetry for connectors](https://troystaylor.github.io/power%20platform/2026/01/07/power-platform-custom-connectors-application-insights.html)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
