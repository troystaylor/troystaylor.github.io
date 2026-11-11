---
layout: post
title: "Triage Microsoft 365 Message Center posts by service and deadline"
date: 2026-11-10 18:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [Message Center, Microsoft Graph, MCP, Copilot Studio, Power Automate, Custom Connectors, Microsoft 365, Admin]
description: "A Power Platform custom connector for the Microsoft 365 Message Center. Filter your tenant's posts by service, severity, and action deadline, trigger flows on new posts, and give Copilot Studio agents the same tools through MCP."
---

Message Center is where Microsoft tells you what's changing in your tenant: new features, retirements, required actions, and planned maintenance. It's also easy to miss a deadline in, because the admin center shows a long list and leaves the sorting to you.

[M365 Message Center](https://github.com/troystaylor/SharingIsCaring/tree/main/M365%20Message%20Center) is a custom connector for the [Microsoft Graph service communications API](https://learn.microsoft.com/graph/api/resources/service-communications-api-overview). It reads your tenant's posts from Power Automate, Power Apps, Logic Apps, and Copilot Studio, filters them by service, severity, or deadline, and marks them read, archived, or favorited as you triage. One deployment gives you standard operations and an MCP endpoint.

## Pick the right Microsoft source

Microsoft publishes change information in three places, and they answer different questions.

| You want | Use |
| --- | --- |
| Posts in **your** Message Center, filtered to your tenant's services, with your read and archive status | This connector |
| The public Microsoft 365 Roadmap and Azure Updates, with no sign-in | The [Release Communications MCP server](https://learn.microsoft.com/microsoft-365/admin/manage/mrc-mcp), or its [Power Platform wrapper](/power%20platform/2026-08-13-microsoft-release-communications-mcp-connector.html) |
| Microsoft Entra users, groups, apps, and devices in natural language | The [Microsoft MCP Server for Enterprise](https://learn.microsoft.com/graph/mcp-server/overview) (preview) |

The roadmap shows what's planned for everyone. Message Center shows what's changing in your tenant and what you need to do about it.

## Operations

| Operation | Graph call |
| --- | --- |
| List Message Center Posts | `GET /admin/serviceAnnouncement/messages` |
| Get Message Center Post | `GET /admin/serviceAnnouncement/messages/{id}` |
| List Post Attachments | `GET /admin/serviceAnnouncement/messages/{id}/attachments` |
| Mark Posts Read / Unread | `markRead`, `markUnread` |
| Archive Posts / Unarchive Posts | `archive`, `unarchive` |
| Favorite Posts / Unfavorite Posts | `favorite`, `unfavorite` |

**List Message Center Posts** returns the most recently changed posts first, each with a short summary. Every filter is optional, and they combine.

| Input | What it does |
| --- | --- |
| Service | Posts that affect one service, such as `Microsoft Teams` or `Exchange Online`. Use the name as Message Center shows it |
| Category | `planForChange`, `preventOrFixIssue`, or `stayInformed` |
| Severity | `normal`, `high`, or `critical` |
| Major Changes Only | Posts marked as a major change |
| Modified Since | Posts published or updated on or after a date. A date without a time zone is read as UTC |
| Action Due Before | Posts with an action-required deadline between now and a date, sorted soonest first |
| Keyword | Text to find in the title or body |
| Max Posts | 1 to 50, default 20 |

One call examines at most 500 posts so you stay inside the service's rate limit. The result reports `totalMatches`, `scannedCount`, and `truncated`. When `truncated` is true, add a filter such as Modified Since to narrow the search.

**Get Message Center Post** takes a post from a dropdown of the last 90 days or an ID such as `MC123456`. It returns the full text as plain text, the links, tags, and services, the dates, the action-required deadline, and your read, archived, and favorite status. The status operations change only **your** view in the admin center. The posts themselves never change.

## Start a flow when Microsoft publishes a post

Message Center doesn't send notifications, so the **When a Message Center post is published or updated** trigger checks on a schedule. A flow starts within a few minutes of a change.

The trigger takes the same Service, Category, Severity, Major Changes Only, and Keyword filters as the list operation, so only matching posts start a run. **New Posts Only** skips posts Microsoft revised after publishing. Message Center has no creation date, so that option relies on the `Updated message` tag and the `(Updated)` title prefix.

When you turn the flow on, the newest post sets the starting point and doesn't start a run. You won't get a flood for posts that already exist. If several posts change between checks, each one starts its own run.

## Tools for Copilot Studio agents

The **Invoke M365 Message Center MCP** operation serves four tools.

| Tool | What it does |
| --- | --- |
| `list_messages` | List and search posts with the same filters as the list operation |
| `get_message` | Get one post by ID |
| `list_message_attachments` | List a post's attachments by name, type, and size |
| `set_message_status` | Mark up to 20 posts read, unread, archived, unarchived, favorited, or unfavorited for the signed-in user |

Post IDs must look like `MC123456`, and anything else is refused before a request is made. Post text is written by Microsoft and other services, so the tool descriptions tell the agent to summarize it and not to follow instructions that appear inside it.

To use the tools, add the connector to your agent as a tool and pick **Invoke M365 Message Center MCP**.

## Example flows

**Alert your team when a major Teams change is posted**

1. Trigger: When a Message Center post is published or updated, with Service set to `Microsoft Teams` and Major Changes Only on.
2. Post an adaptive card to your admin channel with the title, severity, action deadline, and Admin Center Link.
3. Mark Posts Read for the post's ID once someone acknowledges it.

**Send a weekly change digest**

1. Trigger: recurrence, every Monday.
2. List Message Center Posts with Modified Since set to seven days ago and Category set to `planForChange`.
3. For each post, add a row to your change-tracking list with the title, services, deadline, and Admin Center Link.
4. Post the count to a Teams channel.

**Remind owners before an action deadline**

1. Trigger: recurrence, every day.
2. List Message Center Posts with Action Due Before set to 14 days from now.
3. For each post, send the title, deadline, and Admin Center Link to the service owner.
4. Mark Posts Read for the IDs you handled.

## Prerequisites

- A Power Platform environment where you can create custom connectors
- [Power Platform CLI](https://learn.microsoft.com/power-platform/developer/cli/introduction) (`pac`), signed in to that environment
- A Microsoft Entra app registration
- A Microsoft Entra administrator to grant consent for two delegated Microsoft Graph permissions
- Users who hold an admin role that can read Message Center, such as **Global Reader**, **Service Support Administrator**, **Helpdesk Administrator**, or **Global Administrator**. Other users are denied, even after consent

## Set up the connector

### 1. Register an app in Microsoft Entra ID

```powershell
az ad app create --display-name "M365 Message Center Connector" `
  --sign-in-audience AzureADMyOrg `
  --web-redirect-uris "https://global.consent.azure-apim.net/redirect"

# Delegated Microsoft Graph permissions
$graph = "00000003-0000-0000-c000-000000000000"
$read  = az ad sp show --id $graph --query "oauth2PermissionScopes[?value=='ServiceMessage.Read.All'].id" -o tsv
$write = az ad sp show --id $graph --query "oauth2PermissionScopes[?value=='ServiceMessageViewpoint.Write'].id" -o tsv
az ad app permission add --id <appId> --api $graph --api-permissions "$read=Scope" "$write=Scope"

az ad app permission admin-consent --id <appId>

# Power Platform needs a client secret to complete sign-in
az ad app credential reset --id <appId> --append --display-name "Power Platform connector" --years 1 --query password -o tsv
```

Copy the secret now, because you can't read it again. The two permissions are:

- `ServiceMessage.Read.All` covers listing, reading, and attachments. Only an administrator can consent to it.
- `ServiceMessageViewpoint.Write` covers marking posts read, archived, or favorited. If you only want to read posts, leave it out. The status operations then return `403`.

If `admin-consent` fails right after you create the app, wait a minute and run it again.

### 2. Add your client ID

In `apiProperties.json`, replace `[YOUR_CLIENT_ID]` with your app's Application (client) ID. Leave `[YOUR_REDIRECT_URL]` as it is, because the platform replaces it with a per-connector URL when you deploy.

### 3. Deploy the connector

```powershell
pac connector create `
    --api-definition-file apiDefinition.swagger.json `
    --api-properties-file apiProperties.json `
    --script-file script.csx
```

`--script-file` is required because the connector declares script operations. Leave it off and you'll see `InvalidScriptDefinitionUrlWithNonNullOperations`. To update an existing connector, use `pac connector update` with `--connector-id`.

### 4. Add the client secret and redirect URL

In [Power Automate](https://make.powerautomate.com), open **Custom connectors**, edit **M365 Message Center**, go to **Security**, enter the secret in **Client secret**, and select **Update connector**.

Sign-in also fails until the connector's redirect URL is registered on your app. Download the deployed connector and read `properties.connectionParameters.token.oAuthSettings.redirectUrl`:

```powershell
pac connector download --connector-id <your connector ID> --outputDirectory ./verify

az ad app update --id <appId> --web-redirect-uris `
    "https://global.consent.azure-apim.net/redirect" "<redirect URL from the download>"
```

### 5. Create a connection

In Power Automate, go to **Connections**, select **New connection**, choose **M365 Message Center**, and sign in with an account that holds one of the roles above.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `403 Forbidden` on any operation | The signed-in user doesn't hold a Message Center admin role, or an administrator hasn't consented to `ServiceMessage.Read.All` |
| `403 Forbidden` only on Mark, Archive, or Favorite | `ServiceMessageViewpoint.Write` has no admin consent |
| `AADSTS65001` at sign-in | Admin consent hasn't been granted. Run the `admin-consent` command or ask an administrator to |
| `AADSTS7000215` or `AADSTS7000218` at sign-in | The connector has no client secret, or the secret is wrong or expired |
| `AADSTS50011` redirect URI mismatch | The per-connector redirect URL isn't registered on your app |
| `429 Too Many Requests` | Service communications allows 240 requests per minute and 800 per hour per app and tenant. One list call can use up to five requests, so space out scheduled runs and add filters |
| The trigger doesn't start a flow for an existing post | Expected. The newest post sets the starting point when you turn the flow on |
| The trigger fires again for a post you handled | Microsoft updated the post. Turn on New Posts Only |
| The trigger never fires | Check that Service matches the name Message Center shows, then confirm the connection's user holds a Message Center admin role |
| The post dropdown is empty | It lists the last 90 days. You can still type an ID such as `MC123456` |

## Government and national clouds

The service communications API is available in US Government and China clouds. Change `host` in `apiDefinition.swagger.json` and `GraphBaseUrl` in `script.csx` to your cloud's [Graph endpoint](https://learn.microsoft.com/graph/deployments), and use that cloud's Entra authority in the OAuth URLs.

## Telemetry

Application Insights logging is off by default. To turn it on, set `APP_INSIGHTS_ENABLED` to `true` and replace the instrumentation key placeholder in `script.csx`. The script sends request and tool-call events with the method, tool name, and status code, and no post content.

## Resources

- [M365 Message Center connector](https://github.com/troystaylor/SharingIsCaring/tree/main/M365%20Message%20Center)
- [Working with the service communications API](https://learn.microsoft.com/graph/api/resources/service-communications-api-overview)
- [List serviceAnnouncement messages](https://learn.microsoft.com/graph/api/serviceannouncement-list-messages)
- [serviceUpdateMessage resource type](https://learn.microsoft.com/graph/api/resources/serviceupdatemessage)
- [Message Center in the Microsoft 365 admin center](https://learn.microsoft.com/microsoft-365/admin/manage/message-center)
