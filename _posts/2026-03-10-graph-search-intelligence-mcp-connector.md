---
layout: post
title: "Graph Search and Intelligence MCP connector for Copilot Studio"
date: 2026-03-10 14:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, Microsoft Graph, Search, OneDrive, SharePoint]
---

Your Copilot Studio agent can answer questions about emails and calendars. But what about finding that document someone shared last month? Or discovering who in your organization works on similar projects? Or searching across Teams chats, SharePoint sites, and external data sources in one query?

The Graph Search and Intelligence connector brings Microsoft 365's search and insight capabilities to your agents with 19 MCP tools spanning five categories.

## Five search and intelligence categories

### KQL-powered search (8 tools)

Search across Microsoft 365 workloads using Keyword Query Language:

| Tool | Entity Type | Use Case |
|------|-------------|----------|
| search_messages | message | Find emails by sender, subject, attachments |
| search_chat_messages | chatMessage | Search Teams chats and channel messages |
| search_events | event | Find calendar events by organizer, attendees |
| search_files | driveItem | Search OneDrive and SharePoint files |
| search_sites | site | Find SharePoint sites |
| search_list_items | listItem | Search SharePoint list items with custom fields |
| search_external | externalItem | Search external content via Graph connectors |
| search_interleaved | message + chatMessage | Cross-search email and Teams in one call |

**KQL examples:**

```
subject:quarterly AND from:john
filetype:docx budget
IsMentioned:true
organizer:cathy
```

All tools call the Microsoft Graph Search API (`POST /v1.0/search/query`) with entity-specific wrappers.

### Copilot semantic search (1 tool)

| Tool | Description |
|------|-------------|
| semantic_search_files | Natural language semantic + lexical search across OneDrive |

Ask questions like "find the presentation about next quarter's roadmap" instead of constructing KQL queries. The Copilot Search API combines semantic understanding with lexical matching to find relevant files.

**Requirements:**
- Microsoft 365 Copilot license
- Beta endpoint (subject to change)
- Global service only (not available in sovereign clouds)

### Item insights (3 tools)

ML-powered document discovery based on user behavior:

| Tool | Description |
|------|-------------|
| list_trending_documents | Documents trending in your closest network |
| list_shared_documents | Documents shared with or by you, ordered by recency |
| list_used_documents | Recently viewed or modified documents |

These tools surface content you probably need without requiring explicit searches.

### People intelligence (1 tool)

| Tool | Description |
|------|-------------|
| list_relevant_people | Relevance-ranked people from communication patterns |

Find colleagues based on how frequently you interact—not just org chart relationships.

### OneDrive file access (6 tools)

Direct file operations for when you know what you're looking for:

| Tool | Description |
|------|-------------|
| list_recent_files | Recently accessed files |
| list_shared_with_me | Files others have shared with you |
| get_file_metadata | File or folder properties (name, size, dates, author) |
| get_file_content | Pre-authenticated download URL |
| list_folder_children | List contents of a folder |
| search_my_drive | Lightweight search within user's own drive |

## Example agent scenarios

### Find relevant context for a meeting

1. Agent uses `search_events` to find the upcoming meeting
2. Uses `search_messages` to find related email threads
3. Uses `search_files` to locate attachments and shared documents
4. Summarizes context for the user

### Discover expertise in the organization

1. User asks "Who knows about Azure Arc?"
2. Agent uses `search_messages` and `search_chat_messages` to find discussions
3. Uses `list_relevant_people` to identify frequent collaborators
4. Provides a list of potential contacts

### Prepare for a new project

1. Agent uses `list_trending_documents` to surface popular content in the team
2. Uses `semantic_search_files` to find related past projects
3. Uses `list_shared_documents` to find materials from similar initiatives

## Interleaved search

The `search_interleaved` tool searches email and Teams messages simultaneously. Graph API allows combining `message` and `chatMessage` entity types in a single request—other combinations require separate calls.

This is powerful for questions like "What did we discuss about the Q3 budget?" that span both email and chat.

## Prerequisites

Azure AD app registration with these delegated permissions:

- `Files.Read.All` - File search and access
- `Sites.Read.All` - SharePoint site search
- `Mail.Read` - Email search
- `Calendars.Read` - Calendar event search
- `Chat.Read` - Teams chat search
- `ChannelMessage.Read.All` - Teams channel search
- `People.Read` - People intelligence
- `ExternalItem.Read.All` - External content search

For semantic search, users also need a Microsoft 365 Copilot license.

## Setup

1. Register an Azure AD application
2. Add the delegated permissions listed above
3. Generate a client secret
4. Update `apiProperties.json` with your client ID
5. Deploy with PAC CLI:

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
4. The agent discovers all 19 tools automatically

## Known limitations

1. **Entity combinations**: Only `message` + `chatMessage` can be interleaved. Other entity types require separate searches.
2. **Event page size**: Calendar event search has a maximum page size of 25.
3. **Semantic search**: Requires Copilot license, delegated permissions only, global service only.
4. **External items**: Requires `contentSources` to specify which Graph connector connections to search.

## Deprecation notices

| API | Status | Retirement | Replacement |
|-----|--------|------------|-------------|
| GET /me/drive/recent | Deprecated | November 2026 | list_used_documents |
| GET /me/drive/sharedWithMe | Deprecated | November 2026 | list_shared_documents |
| GET /me/people | Maintenance mode | None announced | Graph Search with person entity |

The connector includes both deprecated and replacement APIs during the transition period.

## Application Insights telemetry

Add your connection string to `script.csx` to track:

| Event | Description |
|-------|-------------|
| RequestReceived | Every incoming request with correlation ID |
| RequestCompleted | Success responses with duration |
| SearchDispatched | Search operation intercepted with entity types |
| McpRequestReceived | MCP tool invocations |
| McpRequestProcessed | MCP responses with error status |

## Resources

- [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Graph%20Search%20and%20Intelligence)
- [Microsoft Graph Search API documentation](https://learn.microsoft.com/en-us/graph/api/resources/search-api-overview)
- [Item Insights API documentation](https://learn.microsoft.com/en-us/graph/api/resources/iteminsights)
- [People API documentation](https://learn.microsoft.com/en-us/graph/api/resources/people)
