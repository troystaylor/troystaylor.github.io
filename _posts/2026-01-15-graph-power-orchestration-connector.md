---
layout: post
title: "Graph Power Orchestration: let your agent discover and call any Graph API"
date: 2026-01-15 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Copilot Studio, Microsoft Graph, MCP, AI Agents, API]
description: "An MCP connector that lets Copilot Studio agents discover Microsoft Graph operations dynamically and execute them with delegated permissions. Three tools. The entire Graph API."
---

Microsoft now offers [Frontier MCP servers](https://learn.microsoft.com/en-us/microsoft-agent-365/tooling-servers-overview) through Agent 365—enterprise-grade tooling for Outlook, Teams, SharePoint, and more. These pre-certified servers cover common productivity workflows with centralized governance and observability.

But what about the rest of Microsoft Graph?

Graph Power Orchestration fills that gap. Instead of waiting for pre-built servers for every Graph endpoint, your agent gets three MCP tools:

1. **discover_graph** – search MS Learn docs to find the right endpoint
2. **invoke_graph** – call any Graph API with the user's permissions  
3. **batch_invoke_graph** – run up to 20 requests in a single call

The connector discovers operations on demand, so new Graph features and current Graph schema become available without hardcoding the server. And it respects the delegated permissions you've configured in your app registration—your agent can only access what users are authorized to reach and perform actions they're authorized to take.

## Why this matters for agents

Traditional Graph connectors ship with fixed actions. When Microsoft adds a new API (say, Copilot settings or Loop components), you wait for connector updates. With Graph Power Orchestration, your agent:

- **Handles any request** – access any Graph v1.0 or beta endpoint without predefined actions
- **Understands permissions** – discovery returns required scopes, so the agent knows what's accessible
- **Stays current** – queries MS Learn's live documentation, so new APIs work immediately

The secret sauce? This connector acts as an MCP client itself, calling Microsoft's own Learn MCP server to search documentation in real-time. It's MCP all the way down.

## What your agent can do

Users ask questions in natural language. Your agent translates intent into Graph calls:

| User says | Agent discovers | Agent calls |
|-----------|-----------------|-------------|
| "What's on my calendar today?" | "list calendar events" | `/me/calendarView` |
| "Send a meeting reminder to Sarah" | "send mail" | `/me/sendMail` |
| "What's happening in the Marketing channel?" | "get channel messages" | `/teams/{id}/channels/{id}/messages` |
| "Find the Q4 budget spreadsheet" | "search files" | `/drives/{id}/items` |
| "Who does Alex report to?" | "get manager" | `/users/{id}/manager` |
| "Get everyone's availability" | "check free/busy" | Batch 20 lookups in one call |

The `discover_graph` tool returns permission hints, so your agent knows if the user has access before attempting the call.

## How it works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Copilot Studio Agent                         │
└─────────────────────────────────────────────────────────────────┘
                              │ MCP Protocol
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Graph Power Orchestration Connector                │
│  ┌─────────────────┐              ┌──────────────────────────┐  │
│  │   MCP Server    │              │      MCP Client          │  │
│  │  (for Copilot)  │              │  (calls MS Learn MCP)    │  │
│  └────────┬────────┘              └────────────┬─────────────┘  │
│           │                                    │                │
│           ▼                                    ▼                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  • discover_graph → MS Learn MCP → Parse Graph operations   ││
│  │  • invoke_graph → Microsoft Graph API → Return results      ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────────────┐
│   MS Learn MCP Server   │   │     Microsoft Graph API         │
│ learn.microsoft.com/api │   │    graph.microsoft.com          │
│     (No Auth)           │   │   (Delegated Auth)              │
└─────────────────────────┘   └─────────────────────────────────┘
```

The architecture is called "chained MCP" – the connector is both an MCP server (receiving requests from Copilot Studio) and an MCP client (querying MS Learn for documentation). Your agent talks MCP to the connector, and the connector talks MCP to Microsoft Learn.

## The three tools

### discover_graph

Search Microsoft's documentation to find the Graph endpoint you need:

```json
{
  "query": "list my calendar events for this week",
  "category": "calendar"
}
```

Response includes everything you need:

```json
{
  "success": true,
  "operationCount": 3,
  "operations": [
    {
      "endpoint": "/me/calendar/events",
      "method": "GET",
      "description": "List events in the user's primary calendar",
      "requiredPermissions": ["Calendars.Read"]
    },
    {
      "endpoint": "/me/calendarView",
      "method": "GET",
      "description": "Get calendar view for a date range",
      "requiredPermissions": ["Calendars.Read"]
    }
  ]
}
```

Discovery results cache for 10 minutes to reduce redundant calls.

### invoke_graph

Execute any Graph request with the signed-in user's permissions:

```json
{
  "endpoint": "/me/calendar/events",
  "method": "GET",
  "queryParams": {
    "$select": "subject,start,end,location",
    "$orderby": "start/dateTime"
  }
}
```

The connector handles the tedious parts:
- Adds `$top=25` to collection queries (prevents oversized responses)
- Sets default date ranges for `calendarView` (today + 7 days)
- Strips HTML from email/calendar bodies (keeps response lean)
- Handles 429 throttling with automatic retry

Response includes pagination metadata:

```json
{
  "success": true,
  "hasMore": true,
  "nextLink": "https://graph.microsoft.com/v1.0/me/calendar/events?$skip=25",
  "nextPageHint": "Call invoke_graph again with nextLink as the endpoint",
  "data": { "value": [...] }
}
```

### batch_invoke_graph

Run multiple operations in one call – perfect for gathering related data:

```json
{
  "requests": [
    { "id": "profile", "endpoint": "/me", "method": "GET" },
    { "id": "emails", "endpoint": "/me/messages", "method": "GET" },
    { "id": "events", "endpoint": "/me/calendar/events", "method": "GET" }
  ]
}
```

Response bundles everything:

```json
{
  "success": true,
  "batchSize": 3,
  "successCount": 3,
  "errorCount": 0,
  "responses": [
    { "id": "profile", "status": 200, "data": {...} },
    { "id": "emails", "status": 200, "data": {...} },
    { "id": "events", "status": 200, "data": {...} }
  ]
}
```

Batch calls are capped at 20 requests (Graph's limit). Your agent can gather a user's profile, recent emails, and upcoming meetings in a single round-trip.

## Helpful error messages

Permission errors distinguish between connector issues and org policy issues:

```json
{
  "success": false,
  "errorType": "permission_denied",
  "userMessage": "You don't have permission to access emails. This is controlled by your organization's Entra ID settings, not this connector.",
  "action": "Contact your IT administrator to request the necessary permissions.",
  "technicalDetails": {
    "httpStatus": 403,
    "graphError": "Authorization_RequestDenied",
    "resource": "/users/someone@contoso.com/messages"
  }
}
```

The error types: `session_expired`, `permission_denied`, `not_found_or_no_access`, `service_error`. Your agent can use these to give users actionable guidance instead of cryptic failures.

## Zero Trust compliance

This connector follows Microsoft Zero Trust principles:

| Principle | How it's implemented |
|-----------|----------------------|
| **Verify explicitly** | OBO token validates user identity on every Graph request |
| **Least privilege** | Users only access resources they have Entra permissions for |
| **Assume breach** | Even if connector is compromised, access is limited to the user's scope |

Granting broad scopes to the app registration doesn't grant users access to everything. Their actual Entra ID permissions determine what they can reach. The app registration defines the *ceiling*.

## Setting it up

### App registration

1. **Create app registration** in Microsoft Entra ID
2. **Add delegated permissions** for Microsoft Graph
3. **Grant admin consent** for all permissions
4. **Configure authentication**:
   - Redirect URI: `https://global.consent.azure-apim.net/redirect`
   - Enable ID tokens and Access tokens

### Recommended scopes (minimum)

```
User.Read
User.ReadBasic.All
Mail.Read
Mail.ReadWrite
Mail.Send
Calendars.Read
Calendars.ReadWrite
Files.Read.All
Files.ReadWrite.All
Sites.Read.All
Sites.ReadWrite.All
```

### Extended scopes (full coverage)

Add these for comprehensive Graph coverage:

```
# Users & Groups
User.Read.All, Group.Read.All, GroupMember.Read.All, Directory.Read.All

# Teams
Team.ReadBasic.All, Channel.ReadBasic.All, ChannelMessage.Read.All, Chat.Read

# Tasks & Planner
Tasks.Read, Tasks.ReadWrite

# Security & Reports (if needed)
SecurityEvents.Read.All, AuditLog.Read.All, Reports.Read.All
```

> **Note:** There's a limit of 400 permissions per app registration.

### Import the connector

1. Download files from [the GitHub repo](https://github.com/troystaylor/SharingIsCaring/tree/main/Graph%20Power%20Orchestration)
2. Import via Power Platform maker portal
3. Configure OAuth 2.0 with your app registration
4. Create a connection using your Microsoft account

## Optional: Application Insights

Add your connection string to enable telemetry:

```csharp
private const string APP_INSIGHTS_CONNECTION_STRING = "InstrumentationKey=xxx;...";
```

This tracks request duration, tool execution success/failure, and error details.

## The agent experience

Here's what happens when a user asks "What meetings do I have tomorrow?"

1. **Agent calls `discover_graph`** with query "calendar events for date range"
2. **Connector queries MS Learn MCP** and returns matching endpoints with permissions
3. **Agent picks `/me/calendarView`** based on the description
4. **Agent calls `invoke_graph`** with tomorrow's date range
5. **Connector adds smart defaults** (ordering, field selection, response limits)
6. **Agent formats the response** as a natural language summary

The user asked a question. The agent figured out the API. No hardcoded logic required.

## Get the connector

📦 **GitHub**: [Graph Power Orchestration](https://github.com/troystaylor/SharingIsCaring/tree/main/Graph%20Power%20Orchestration)

Three tools. The entire Graph API. Your agent handles the rest.

#CopilotStudio #MicrosoftGraph #MCP #AIAgents #PowerPlatform
