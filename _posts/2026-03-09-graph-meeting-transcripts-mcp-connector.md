---
layout: post
title: "Graph Meeting Transcripts MCP connector for Copilot Studio"
date: 2026-03-09 10:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, Microsoft Graph, Teams, Transcripts, Recordings, Virtual Events]
---

Microsoft updated the official [Work IQ Teams MCP server](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/teams) today with comprehensive chat and channel tools. It handles chats, channels, teams, members, and messages beautifully. But if you need meeting transcripts, recordings, attendance reports, AI insights, or virtual events? You still need a custom solution.

That's where the Graph Meeting Transcripts connector comes in. It fills the gaps the official server doesn't cover—giving your Copilot Studio agents access to the meeting artifacts that matter most for productivity and compliance scenarios.

## What the official Teams MCP server covers

The Work IQ Teams server focuses on communication management:

- **Chat tools** - Create, read, update, and delete chats and messages
- **Channel tools** - Manage channels, post messages, handle replies
- **Team tools** - Retrieve team properties and memberships
- **Member management** - Add, update, and list participants

These cover day-to-day Teams collaboration. But meetings generate artifacts that live outside this scope.

## What this connector adds

The Graph Meeting Transcripts connector exposes 30 MCP tools organized into categories that complement the official server:

### Meeting management

| Tool | Description |
|------|-------------|
| find_meeting | Find an online meeting by its join URL |
| get_meeting | Get meeting details by ID |
| create_meeting | Create a new online meeting |
| update_meeting | Update meeting properties |
| delete_meeting | Delete an online meeting |

### Transcripts and recordings

| Tool | Description |
|------|-------------|
| list_transcripts | List all transcripts for a meeting |
| get_transcript_content | Get VTT text content of a transcript |
| list_recordings | List all recordings for a meeting |

Transcript content comes back in VTT format with timestamps and speaker identification. Recording operations return pre-authenticated download URLs—the connector intercepts Graph's 302 redirect and extracts the URL so your agent can work with it directly.

### Attendance

| Tool | Description |
|------|-------------|
| list_attendance_reports | List attendance reports for a meeting |
| get_attendance_records | Get individual participant join/leave times |

Attendance reports include total participant count, per-participant roles, email addresses, and attendance duration. You can see exactly who joined when and for how long.

### AI insights

| Tool | Description |
|------|-------------|
| list_ai_insights | List AI-generated insights for a meeting |
| get_ai_insight | Get detailed summary with notes and action items |

AI insights require a Microsoft 365 Copilot license and may take up to 4 hours after a meeting ends to become available. They support private scheduled meetings, town halls, webinars, and Meet Now sessions.

### Virtual events

The connector provides full coverage for webinars and town halls:

| Category | Tools |
|----------|-------|
| Webinars | list_webinars, create_webinar, get_webinar, publish_webinar, cancel_webinar |
| Town halls | list_townhalls, create_townhall, get_townhall, publish_townhall, cancel_townhall |
| Sessions | list_sessions, get_session |
| Presenters | list_presenters, add_presenter, remove_presenter |
| Registrations | list_registrations, create_registration, cancel_registration |

Virtual events start in draft status. Use the publish tools to make them visible to attendees.

## Prerequisites

You need an Azure AD app registration with these delegated permissions:

- `OnlineMeetingTranscript.Read.All` - for transcripts
- `OnlineMeetingRecording.Read.All` - for recordings
- `OnlineMeetingArtifact.Read.All` - for attendance reports
- `OnlineMeetings.Read` - for meeting lookup
- `OnlineMeetings.ReadWrite` - for meeting CRUD
- `VirtualEvent.ReadWrite` - for webinars and town halls
- `User.Read`
- `offline_access`

Transcription and recording must be enabled for meetings where you want to retrieve those artifacts.

## Setup

1. Create a custom connector in Power Platform
2. Import the `apiDefinition.swagger.json` file from the [GitHub repo](https://github.com/troystaylor/SharingIsCaring/tree/main/Graph%20Meeting%20Transcripts)
3. Configure OAuth 2.0 authentication using your Azure AD app
4. Test the connection

For Copilot Studio:

1. Open your agent in Copilot Studio
2. Go to **Actions** > **Add an action** > **Connector**
3. Search for your connector name and add it
4. The agent automatically discovers the 30 tools via the MCP endpoint

## Example scenarios

### Summarize my last meeting

An agent can:
1. Use `find_meeting` with the join URL from the user's calendar
2. Use `list_transcripts` to find available transcripts
3. Use `get_transcript_content` to retrieve the VTT text
4. Summarize the content for the user

### Check meeting attendance

1. Use `find_meeting` to get the meeting ID
2. Use `list_attendance_reports` to find reports
3. Use `get_attendance_records` to get participant details
4. Report who attended and for how long

### Get AI-generated action items

1. Use `find_meeting` to locate the meeting
2. Use `list_ai_insights` to check for available insights
3. Use `get_ai_insight` to retrieve the detailed summary
4. Extract and present action items to the user

## Application Insights telemetry

The connector includes optional Application Insights integration for monitoring and troubleshooting:

| Event | Description |
|-------|-------------|
| RequestReceived | Every incoming request with operation ID |
| RequestCompleted | Successful completion with duration |
| McpToolCallStarted | MCP tool invocation started |
| McpToolCallCompleted | Tool completed with success/error status |
| McpToolCallError | Tool execution failure details |

Sample KQL query to see tool usage:

```kql
customEvents
| where customDimensions.ServerName == "graph-meeting-transcripts-mcp"
| where name == "ToolExecuted"
| summarize count() by tostring(customDimensions.Tool), bin(timestamp, 1h)
| render columnchart
```

## Important notes

- Transcripts and recordings are [metered APIs](https://learn.microsoft.com/en-us/graph/teams-licenses#payment-models-for-meeting-apis)—charges apply per use
- Recording download is only available to the meeting organizer by default
- Meeting artifacts expire per [Teams limits](https://learn.microsoft.com/en-us/microsoftteams/limits-specifications-teams#meeting-expiration)
- Delta queries support incremental sync for transcripts and recordings
- The old `meetingRegistration` API is deprecated—use the webinar registration tools instead

## Resources

- [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Graph%20Meeting%20Transcripts)
- [Work IQ Teams MCP server reference](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/teams)
- [Graph API meeting transcripts documentation](https://learn.microsoft.com/en-us/graph/api/resources/calltranscript)
- [Teams licenses for meeting APIs](https://learn.microsoft.com/en-us/graph/teams-licenses)
