---
layout: post
title: "Slack MCP connector with 70 operations and typed tools for Copilot Studio"
date: 2026-03-24 10:00:00 -0600
categories: [Power Platform, Custom Connectors]
tags: [Slack, Copilot Studio, MCP, Power Mission Control, messaging, collaboration]
---

This [connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Slack) takes a hybrid approach: eight typed tools for high-value messaging operations, plus three Power Mission Control tools covering 70 Slack API methods. The typed tools give the orchestrator direct access to the most common actions—send a message, search, list channels—without a scan step. The Mission Control MCP tools handle everything else across 15 API domains.

## Tools

### Typed tools (direct access)

These eight tools are registered with full schemas so the orchestrator can invoke them directly:

| Tool | Description |
|------|-------------|
| `send_message` | Send a message to a channel or conversation |
| `search_messages` | Search for messages across the workspace |
| `list_channels` | List channels in the workspace |
| `get_channel_history` | Get recent messages from a channel |
| `get_user_info` | Get user profile information |
| `list_users` | List all workspace users |
| `add_reaction` | Add an emoji reaction to a message |
| `upload_file` | Upload a text-based file to Slack |

### Orchestration tools (scan, launch, sequence)

For the remaining 70 Slack API methods, the connector uses Power Mission Control's progressive discovery:

| Tool | Description |
|------|-------------|
| `scan_slack` | Discover available Slack API operations by intent |
| `launch_slack` | Execute any Slack API method |
| `sequence_slack` | Execute multiple Slack API methods in one call |

The capability index covers methods across messaging, channels, users, reactions, pins, files, search, bookmarks, reminders, usergroups, emoji, dnd, stars, team, and auth.

### Discovery example

```
1. Orchestrator calls scan_slack({query: "create a reminder"})
   → Returns: reminders.add (POST)

2. Orchestrator calls launch_slack({
     endpoint: "reminders.add",
     body: { "text": "Review PRs", "time": "in 30 minutes" }
   })
   → Returns: reminder confirmation
```

### Sequence example

Execute multiple operations in one call with `sequence_slack`:

```json
{
  "requests": [
    { "id": "1", "endpoint": "conversations.list", "body": { "limit": 5 } },
    { "id": "2", "endpoint": "users.list", "body": { "limit": 5 } }
  ]
}
```

## REST operations for Power Automate and Power Apps

The same eight typed tools are also exposed as Swagger operations so you can use them in Power Automate flows and Power Apps—not just Copilot Studio:

| Operation | Operation ID |
|-----------|-------------|
| Send Message | `SendMessage` |
| Search Messages | `SearchMessages` |
| List Channels | `ListChannels` |
| Get Channel History | `GetChannelHistory` |
| Get User Info | `GetUserInfo` |
| List Users | `ListUsers` |
| Add Reaction | `AddReaction` |
| Upload File | `UploadFile` |

## Prerequisites

- A Slack workspace with admin access
- A Slack app configured at [api.slack.com/apps](https://api.slack.com/apps)
- OAuth 2.0 credentials (Client ID and Client Secret)

## Slack app setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and select **Create New App**
2. Choose **From scratch** and provide a name and workspace
3. Navigate to **OAuth & Permissions** in the sidebar
4. Under **Redirect URLs**, add: `https://global.consent.azure-apim.net/redirect`
5. Under **User Token Scopes**, add the required scopes:

   `channels:read`, `channels:history`, `channels:write`, `chat:write`, `users:read`, `users:read.email`, `users.profile:read`, `files:read`, `files:write`, `reactions:read`, `reactions:write`, `pins:read`, `pins:write`, `search:read`, `groups:read`, `groups:history`, `im:read`, `im:history`, `mpim:read`, `mpim:history`, `reminders:read`, `reminders:write`, `bookmarks:read`, `bookmarks:write`, `usergroups:read`, `usergroups:write`, `emoji:read`, `dnd:read`, `dnd:write`, `team:read`

6. Note your **Client ID** and **Client Secret** from the **Basic Information** page

## Connector setup

1. Import the connector into Power Platform using the PAC CLI or the custom connectors portal
2. During connection setup, enter your Slack app's Client ID and Client Secret
3. Authorize with Slack when prompted—this generates a user token (`xoxp-`)

## Authentication

This connector uses OAuth 2.0 authorization code flow with user tokens (`xoxp-`). The token acts on behalf of the authenticated user.

| Setting | Value |
|---------|-------|
| Authorization URL | `https://slack.com/oauth/v2/authorize` |
| Token URL | `https://slack.com/api/oauth.v2.access` |
| Refresh URL | `https://slack.com/api/oauth.v2.access` |
| Token type | User token (`xoxp-`) |

**Token rotation**: Slack user tokens don't support refresh tokens unless [token rotation](https://api.slack.com/authentication/rotation) is explicitly enabled on your Slack app. Navigate to **OAuth & Permissions** > **Advanced token security** and enable **Token Rotation** for refresh tokens to work. Without this, tokens eventually expire and users must re-authorize.

## Slack API notes

- All Slack API methods use POST (even read operations)
- API URL pattern: `https://slack.com/api/{method.name}`
- Responses always contain `"ok": true/false`
- Pagination uses the `cursor`/`next_cursor` pattern—pass the returned `nextCursor` value as the `cursor` parameter for the next page
- Rate limiting is tier-based (Tier 1-4) with HTTP 429 and `Retry-After` header (handled automatically with retry)

## Resources

- [Full source code on GitHub](https://github.com/troystaylor/SharingIsCaring/tree/main/Slack)
- [Slack API documentation](https://api.slack.com/methods)
- [Slack OAuth documentation](https://api.slack.com/authentication/oauth-v2)
- [Power Mission Control template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20Mission%20Control%20Template)
