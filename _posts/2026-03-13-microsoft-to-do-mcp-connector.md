---
layout: post
title: "Microsoft To Do MCP connector for Copilot Studio"
date: 2026-03-13 09:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, Microsoft Graph, To Do, Tasks]
---

Microsoft To Do has a Graph API, but no official MCP server and no built-in Power Platform connector that covers the full surface. This custom connector exposes 28 MCP tools across task lists, tasks, checklist items, linked resources, file attachments, delta queries, and Outlook categories—everything an AI agent needs to manage a user's tasks end to end.

## What the connector covers

### Task lists

| Tool | Description |
|------|-------------|
| list_task_lists | Get all task lists |
| get_task_list | Get a specific task list |
| create_task_list | Create a new task list |
| update_task_list | Update a task list name |
| delete_task_list | Delete a task list |

### Tasks

Full CRUD plus a dedicated completion tool:

| Tool | Description |
|------|-------------|
| list_tasks | Get all tasks in a list (supports OData filter, top, skip, orderby) |
| get_task | Get a specific task |
| create_task | Create a new task with optional body, due date, recurrence, and categories |
| update_task | Update a task |
| complete_task | Mark a task as completed |
| delete_task | Delete a task |

The `create_task` tool supports recurrence patterns—daily, weekly, monthly, and yearly—so your agent can set up recurring tasks without manual scheduling.

### Checklist items

Break tasks into subtasks:

| Tool | Description |
|------|-------------|
| list_checklist_items | Get checklist items for a task |
| get_checklist_item | Get a specific checklist item |
| create_checklist_item | Create a checklist item |
| update_checklist_item | Update a checklist item |
| delete_checklist_item | Delete a checklist item |

### Linked resources

Connect tasks to external content:

| Tool | Description |
|------|-------------|
| list_linked_resources | Get linked resources for a task |
| get_linked_resource | Get a specific linked resource |
| create_linked_resource | Create a linked resource |
| update_linked_resource | Update a linked resource |
| delete_linked_resource | Delete a linked resource |

Linked resources let an agent tie a task to a Teams message, a SharePoint document, or any URL—keeping context alongside the work item.

### File attachments

Attach files directly to tasks (up to 3 MB, base64 encoded):

| Tool | Description |
|------|-------------|
| list_task_attachments | Get file attachments for a task |
| get_task_attachment | Get a specific attachment with content |
| create_task_attachment | Attach a file to a task |
| delete_task_attachment | Delete a file attachment |

### Delta queries

Sync without polling everything:

| Tool | Description |
|------|-------------|
| get_tasks_delta | Get tasks added, deleted, or updated since last sync |
| get_task_lists_delta | Get task lists added, deleted, or updated since last sync |

Delta queries return only what changed since the last call. An agent can track task completions, new assignments, or list reorganizations without fetching the entire dataset each time.

### Categories

| Tool | Description |
|------|-------------|
| list_outlook_categories | Get Outlook categories for tagging tasks |

## Agent scenarios

**Daily standup prep:**
> "What tasks did I complete yesterday and what's due today?" → Agent calls `list_tasks` with OData filters on `completedDateTime` and `dueDateTime` → summarizes progress

**Project breakdown:**
> "Create a task list for the website redesign with these milestones" → Agent calls `create_task_list` → `create_task` for each milestone with due dates → `create_checklist_item` for subtasks

**Recurring reminders:**
> "Remind me to submit timesheets every Friday" → Agent calls `create_task` with weekly recurrence pattern

**Cross-app linking:**
> "Link this Teams conversation to my review task" → Agent calls `create_linked_resource` with the Teams message URL

**Change tracking:**
> "What tasks were updated since our last sync?" → Agent calls `get_tasks_delta` → returns only modified items

## Prerequisites

Azure AD app registration with these delegated permissions:

- `Tasks.ReadWrite` - Read and write To Do tasks
- `MailboxSettings.Read` - Read mailbox settings (required for categories)
- `offline_access` - Refresh tokens

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
4. The agent discovers all 28 tools automatically

## Application Insights

Add your connection string to `script.csx` to track:

- All incoming requests with operation IDs
- MCP tool invocations with timing
- Errors with full exception details

## Resources

- [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20To%20Do)
- [To Do API overview](https://learn.microsoft.com/en-us/graph/api/resources/todo-overview?view=graph-rest-1.0)
- [todoTask resource](https://learn.microsoft.com/en-us/graph/api/resources/todotask?view=graph-rest-1.0)
- [Delta query documentation](https://learn.microsoft.com/en-us/graph/api/todotask-delta?view=graph-rest-1.0)
