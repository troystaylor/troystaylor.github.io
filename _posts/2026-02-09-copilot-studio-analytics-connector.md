---
layout: post
title: "Copilot Studio Analytics connector for Power Platform"
date: 2026-02-09 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Copilot Studio, Analytics, Dataverse, MCP, Custom Connectors, Power Platform, Power Automate, CSAT]
description: "Custom connector that queries Copilot Studio analytics from Dataverse—conversation metrics, topic performance, session outcomes, CSAT scores, transcript parsing, and MCP tools for agent integration."
---

Copilot Studio captures rich analytics data in Dataverse, but getting that data into flows, apps, or other agents isn't straightforward. This custom connector wraps those Dataverse tables with purpose-built operations for conversation analytics, topic performance, session outcomes, customer satisfaction scores, and full transcript parsing. It also exposes those same analytics as MCP tools so a Copilot Studio agent can report on its own performance conversationally.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Analytics).

## What it does

The connector queries four Dataverse tables—`bot`, `conversationtranscript`, `botcomponent`, and `msdyn_botsession`—and computes analytics server-side in the connector script. Instead of building complex Dataverse queries and post-processing in your flow, call a single operation and get structured metrics back.

## Operations

### Bot management

| Operation | Description |
|-----------|-------------|
| ListBots | List all Copilot Studio bots in the environment with OData filtering |
| GetBot | Retrieve a specific bot by ID |

### Transcripts

| Operation | Description |
|-----------|-------------|
| ListConversationTranscripts | Retrieve transcripts with parsed content, activity counts, and message counts |
| GetConversationTranscript | Get a single transcript with full parsed content |
| ParseTranscriptContent | Parse a transcript into structured messages with roles, timestamps, and topics triggered |

Transcript parsing converts the raw JSON content into structured data including user/bot message counts, topics triggered, escalation status, and individual messages with roles and timestamps.

### Analytics

| Operation | Description |
|-----------|-------------|
| GetConversationAnalytics | Aggregated conversation statistics across all bots or filtered by bot/date |
| GetBotConversationAnalytics | Comprehensive metrics for a specific bot over a date range |
| GetTopicAnalytics | Topic-level trigger counts, completion rates, and escalation rates |
| GetSessionAnalytics | Session outcomes, durations, and daily trends |
| GetCSATAnalytics | Customer satisfaction scores, rating distribution, and recent feedback |

### Session and conversation data

| Operation | Description |
|-----------|-------------|
| ListBotSessions | Raw session data for engagement tracking |
| ListBotConversations | Individual conversation records |

## Analytics deep dive

### Bot conversation analytics

Call `GetBotConversationAnalytics` with a bot ID and optional date range to get:

- Total conversations and daily breakdown
- Average messages per conversation (total and user-only)
- Average duration in seconds
- Escalation rate and escalated count

```json
{
  "botId": "12345678-...",
  "totalConversations": 150,
  "averageMessagesPerConversation": 8.5,
  "averageDurationSeconds": 245.5,
  "escalationRate": 12.5,
  "escalatedCount": 19,
  "conversationsByDay": [
    { "date": "2025-01-15", "count": 25 }
  ]
}
```

### Topic analytics

`GetTopicAnalytics` returns the top N topics ranked by trigger count, each with completion and escalation rates:

```json
{
  "topics": [
    {
      "topicName": "Order Status",
      "triggerCount": 450,
      "completionRate": 92.5,
      "escalationRate": 5.2
    }
  ]
}
```

### Session analytics

`GetSessionAnalytics` breaks sessions into outcomes:

```json
{
  "totalSessions": 500,
  "averageSessionDurationSeconds": 180.5,
  "outcomeBreakdown": [
    { "outcome": "resolved", "count": 400, "percentage": 80.0 },
    { "outcome": "escalated", "count": 75, "percentage": 15.0 },
    { "outcome": "abandoned", "count": 25, "percentage": 5.0 }
  ]
}
```

### CSAT analytics

`GetCSATAnalytics` returns satisfaction scores with rating distribution and recent feedback:

```json
{
  "totalResponses": 120,
  "averageRating": 4.2,
  "csatScore": 85.0,
  "ratingDistribution": [
    { "rating": 5, "count": 55, "percentage": 45.8 },
    { "rating": 4, "count": 42, "percentage": 35.0 }
  ],
  "recentFeedback": [
    { "transcriptId": "abc123...", "rating": 5, "comment": "Very helpful!" }
  ]
}
```

## MCP protocol

The connector includes a `/mcp` endpoint with seven JSON-RPC 2.0 tools for Copilot Studio agent integration:

| MCP Tool | Description |
|----------|-------------|
| `list_bots` | List all bots in the environment |
| `get_conversation_analytics` | Aggregated conversation metrics for a bot |
| `get_topic_analytics` | Topic-level analytics with trigger counts and escalation rates |
| `get_csat_analytics` | Customer satisfaction scores and feedback |
| `get_session_analytics` | Session outcomes and duration metrics |
| `get_recent_transcripts` | Recent conversation transcripts with parsed content |
| `parse_transcript` | Parse a specific transcript into structured messages |

This means a Copilot Studio agent can answer questions about its own analytics:

**User:** "How many conversations did the support bot handle last week?"
**Agent:** *Calls `get_conversation_analytics` with date range and returns the count*

**User:** "Which topics have the highest escalation rate?"
**Agent:** *Calls `get_topic_analytics` and highlights topics with high escalation*

**User:** "What's our CSAT score for January?"
**Agent:** *Calls `get_csat_analytics` with the date range*

## Setup

### 1. Azure AD app registration

1. Create or reuse an app registration in the Azure Portal.
2. Add API permission: **Dynamics CRM → user_impersonation**.
3. Grant admin consent.
4. Note the Application (client) ID and Directory (tenant) ID.

### 2. Import the connector

1. Import `apiDefinition.swagger.json` as a custom connector in Power Platform.
2. Enable custom code and upload `script.csx`.
3. Create a connection with your tenant and Dataverse domain.

### 3. Dataverse security

Ensure your user has **System Administrator**, **System Customizer**, or a custom role with read access to the `bot` and `conversationtranscript` tables.

## Power Automate examples

### Daily conversation count

1. Call **ListConversationTranscripts** with filter: `createdon ge @{formatDateTime(utcNow(), 'yyyy-MM-dd')}T00:00:00Z`
2. Use the `Length` expression on the `value` array.

### Export transcripts to SharePoint

1. **ListConversationTranscripts** for a specific bot.
2. **Apply to each** on `value`.
3. **Create file** in SharePoint with transcript content.

### Analytics summary email

1. Call **GetConversationAnalytics** with a date filter.
2. Compose an HTML email body with the statistics.
3. Send the email.

## Common OData filters

Filter by bot:
```
_bot_value eq '12345678-1234-1234-1234-123456789012'
```

Filter by date range:
```
createdon ge 2024-01-01T00:00:00Z and createdon le 2024-01-31T23:59:59Z
```

## Application Insights (optional)

Update the connection string in `script.csx` to enable telemetry:

```csharp
private static readonly string AppInsightsConnectionString = "InstrumentationKey=your-key-here;...";
```

Events logged: `CopilotStudioAnalytics_Request`, `CopilotStudioAnalytics_Response`, `CopilotStudioAnalytics_Error`.

## Try it yourself

The complete connector code is available in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Analytics):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Copilot%20Studio%20Analytics/apiDefinition.swagger.json) — OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Copilot%20Studio%20Analytics/script.csx) — Connector script with analytics and MCP
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Copilot%20Studio%20Analytics/apiProperties.json) — Connector metadata
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Copilot%20Studio%20Analytics/readme.md) — Full documentation

## Resources

- [Copilot Studio documentation](https://docs.microsoft.com/en-us/microsoft-copilot-studio/)
- [Dataverse Web API reference](https://docs.microsoft.com/en-us/power-apps/developer/data-platform/webapi/overview)
- [OData query options](https://docs.microsoft.com/en-us/power-apps/developer/data-platform/webapi/query-data-web-api)
- [Model Context Protocol specification](https://spec.modelcontextprotocol.io/)
- [Power Platform Custom Connectors](https://learn.microsoft.com/en-us/connectors/custom-connectors/)
- [Application Insights telemetry for connectors](https://troystaylor.github.io/power%20platform/2026/01/07/power-platform-custom-connectors-application-insights.html)
