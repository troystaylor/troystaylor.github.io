---
layout: post
title: "Graph Mail and Calendar MCP connector for Copilot Studio"
date: 2026-03-10 10:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, Microsoft Graph, Outlook, Mail, Calendar]
---

Microsoft updated the official [Work IQ Mail](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/mail) and [Work IQ Calendar](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/calendar) MCP servers yesterday. Together they provide 21 tools covering core Outlook scenarios. But when your Copilot Studio agent needs to manage attachments, organize folders, create inbox rules, or draft emails that sound like you wrote them—you need more.

This connector delivers 77 MCP tools that cover everything Work IQ offers, plus 50+ additional capabilities for production-grade mail and calendar automation.

## What the official servers cover

The **Work IQ Mail** server (10 tools) handles:

- Create drafts, send, reply, reply-all
- Get, update, delete messages
- List sent items
- Search messages with KQL

The **Work IQ Calendar** server (11 tools) handles:

- Create, update, delete events
- Accept, decline, cancel invitations
- Find meeting times and check availability
- List events and calendar view

These work well for straightforward scenarios. But real-world agents need deeper control.

## What this connector adds

### Complete attachment support

Work IQ can't touch attachments. This connector lets your agent list, read, add, and remove them:

| Tool | Description |
|------|-------------|
| list_attachments | List message attachments with metadata |
| get_attachment | Get attachment with base64 content |
| get_attachment_content | Download raw binary content |
| create_attachment | Add file to draft message |
| delete_attachment | Remove attachment from draft |

Same operations exist for calendar event attachments—your agent can add meeting agendas or download shared files.

### Mail folder management

Organize messages programmatically:

| Tool | Description |
|------|-------------|
| list_folders | List all mail folders with search |
| get_mail_folder | Get folder by ID or well-known name |
| create_mail_folder | Create new folder or subfolder |
| update_mail_folder | Rename folders |
| delete_mail_folder | Delete folder and contents |
| list_child_folders | List subfolders |
| list_folder_messages | List messages in a specific folder |
| move_message | Move message to folder |
| copy_message | Copy message to folder |

### Inbox rules

Automate mail processing:

| Tool | Description |
|------|-------------|
| list_message_rules | List inbox rules |
| create_message_rule | Create rules (move, categorize, forward) |
| get_message_rule | Get rule details |
| update_message_rule | Modify existing rules |
| delete_message_rule | Remove rules |

### Draft workflows

Create and manage drafts before sending:

| Tool | Description |
|------|-------------|
| create_draft | Create new draft message |
| create_draft_in_folder | Create draft in specific folder |
| create_reply_draft | Prepare reply without sending |
| create_reply_all_draft | Prepare reply-all |
| create_forward_draft | Prepare forward with recipients |
| send_draft | Send when ready |

### Calendar management

Beyond events—manage calendars themselves:

| Tool | Description |
|------|-------------|
| list_calendars | List user's calendars |
| create_calendar | Create secondary calendars |
| update_calendar | Change name or color |
| delete_calendar | Remove secondary calendars |
| list_event_instances | Get recurring event occurrences |
| snooze_reminder | Snooze event reminders |
| dismiss_reminder | Dismiss reminders |

### Mail tips

Know before you send:

| Tool | Description |
|------|-------------|
| get_mail_tips | Check auto-reply status, mailbox full, delivery restrictions |

## Voice-matched email drafting

The killer feature: two composite tools that help agents write emails that sound like you.

### get_writing_samples

Fetches recent sent emails to analyze writing patterns:

- Greeting and closing styles
- Formality level
- Sentence structure and vocabulary
- Tone and voice characteristics

Parameters let you filter by recipient (for relationship-aware matching) or topic keyword.

### draft_with_style_guide

Combines your company's writing guidelines with personal voice analysis. When conflicts arise:

- Style guide wins for formal/external communications
- Personal voice wins for casual/internal messages

### Example workflows

**Reply in your voice:**
> "Reply to this email in my style" → Agent calls `get_writing_samples` → analyzes patterns → drafts reply matching your tone

**Follow company guidelines:**
> "Write a budget request using our style guide" → Agent calls `draft_with_style_guide` with your rules → produces compliant draft

**Executive communications:**
> "Draft an all-hands email about the new initiative" → Agent fetches previous all-hands samples → captures your leadership voice → drafts announcement

## Search everywhere

Every list operation supports `$search`:

- list_messages
- list_sent
- list_folders
- list_folder_messages
- list_events
- list_calendars
- list_users
- list_people

Plus full KQL search via `search_messages`:

```
subject:quarterly AND from:john
hasAttachment:true AND received>=2025-01-01
"exact phrase match"
```

## Complete comparison

### Work IQ Mail (10 tools)

| Work IQ Tool | This Connector |
|--------------|----------------|
| createMessage | create_draft |
| deleteMessage | delete_message |
| getMessage | get_message |
| listSent | list_sent |
| reply | reply |
| replyAll | reply_all |
| searchMessages | search_messages |
| sendDraft | send_draft |
| sendMail | send_mail |
| updateMessage | update_message |

### Work IQ Calendar (11 tools)

| Work IQ Tool | This Connector |
|--------------|----------------|
| acceptEvent | accept_event |
| cancelEvent | cancel_event |
| createEvent | create_event |
| declineEvent | decline_event |
| deleteEvent | delete_event |
| findMeetingTimes | find_meeting_times |
| getEvent | get_event |
| getSchedule | get_schedule |
| listCalendarView | calendar_view |
| listEvents | list_events |
| updateEvent | update_event |
| listEvents | list_events |
| updateEvent | update_event |
| getMyProfile | get_my_profile |
| getMyManager | get_my_manager |
| getUserProfile | get_user_profile |
| getUsersManager | get_users_manager |
| getDirectReports | get_direct_reports |
| listUsers | list_users |

**Additional tools beyond Work IQ:** list_messages, forward, list_folders, move_message, copy_message, all attachment operations, folder management, calendar management, inbox rules, draft workflows, event instances, reminders, mail tips, get_writing_samples, draft_with_style_guide, and more.

## Prerequisites

Azure AD app registration with these delegated permissions:

- `Mail.ReadWrite` - Read and write mail
- `Mail.Send` - Send mail
- `Calendars.ReadWrite` - Read and write calendars
- `User.Read` - Sign in and read profile
- `User.ReadBasic.All` - Read basic profiles
- `MailboxSettings.ReadWrite` - Manage inbox rules
- `People.Read` - List relevant people
- `offline_access` - Refresh tokens

## Setup

1. Register an Azure AD application
2. Add the delegated permissions listed above
3. Generate a client secret
4. Grant admin consent for `MailboxSettings.ReadWrite` and `People.Read`
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
4. The agent discovers all 77 tools automatically

## Application Insights

Add your connection string to `script.csx` to track:

- All incoming requests with operation IDs
- MCP tool invocations with timing
- Errors with full exception details

## Resources

- [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Graph%20Mail%20and%20Calendar)
- [Work IQ Mail reference](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/mail)
- [Work IQ Calendar reference](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/calendar)
- [Graph Mail API documentation](https://learn.microsoft.com/en-us/graph/api/resources/mail-api-overview)
- [Graph Calendar API documentation](https://learn.microsoft.com/en-us/graph/api/resources/calendar)
