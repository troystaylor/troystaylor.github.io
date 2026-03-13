---
layout: post
title: "Microsoft Planner MCP connector for Copilot Studio"
date: 2026-03-13 10:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, Microsoft Graph, Planner, Tasks]
---

Power Platform has a built-in Planner connector, but it covers a narrow slice of the API. No rosters, no business scenarios, no archive/unarchive, no delta queries, no board format control. This custom connector exposes 54 MCP tools that cover the full Microsoft Graph Planner API surface—including beta endpoints for preview features.

## What the connector covers

### Plans (16 tools)

Beyond basic CRUD, the connector handles plan lifecycle operations that the built-in connector doesn't touch:

| Tool | Description |
|------|-------------|
| list_group_plans | Get all plans for a Microsoft 365 group |
| get_plan | Get a specific plan by ID |
| create_plan | Create a new plan in a group or roster |
| update_plan | Update a plan title (requires ETag) |
| delete_plan | Delete a plan (requires ETag) |
| get_plan_details | Get category labels and shared-with info |
| update_plan_details | Update category labels (requires ETag) |
| list_plan_buckets | Get all buckets in a plan |
| list_plan_tasks | Get all tasks in a plan |
| archive_plan | Archive a plan to make it read-only |
| unarchive_plan | Reactivate an archived plan |
| move_plan_to_container | Move a plan to a different container |
| list_my_plans | Get all plans for the current user |
| list_favorite_plans | Get plans marked as favorites |
| list_recent_plans | Get recently viewed plans |

Archive and unarchive let your agent freeze completed projects without deleting them. Move plan to container handles scenarios like migrating a personal plan to a group.

### Tasks (16 tools)

Full task management plus board format control and delta sync:

| Tool | Description |
|------|-------------|
| get_task | Get a specific task by ID |
| create_task | Create a new task in a plan |
| update_task | Update task properties (requires ETag) |
| delete_task | Delete a task (requires ETag) |
| complete_task | Mark a task as completed |
| get_task_details | Get description, checklist, and references |
| update_task_details | Update description (requires ETag) |
| list_my_tasks | Get tasks assigned to the current user |
| list_my_day_tasks | Get tasks in the user's My Day view |
| get_assigned_to_board_format | Get Assigned To task board format |
| update_assigned_to_board_format | Update Assigned To task board format |
| get_progress_board_format | Get Progress task board format |
| update_progress_board_format | Update Progress task board format |
| get_bucket_board_format | Get Bucket task board format |
| update_bucket_board_format | Update Bucket task board format |
| get_task_delta | Get incremental task changes via delta query |

The board format tools control how tasks appear in Planner's Kanban views—something you can't do through the built-in connector at all.

### Buckets (5 tools)

| Tool | Description |
|------|-------------|
| get_bucket | Get a specific bucket by ID |
| create_bucket | Create a new bucket in a plan |
| update_bucket | Update bucket name or order (requires ETag) |
| delete_bucket | Delete a bucket (requires ETag) |
| list_bucket_tasks | Get all tasks in a bucket |

### Rosters (7 tools)

Rosters are plan containers that don't require a Microsoft 365 group—useful for cross-team or ad-hoc collaboration:

| Tool | Description |
|------|-------------|
| create_roster | Create a new roster |
| get_roster | Get a specific roster by ID |
| delete_roster | Delete a roster |
| list_roster_members | Get all members of a roster |
| add_roster_member | Add a member to a roster |
| remove_roster_member | Remove a member from a roster |
| list_roster_plans | Get all plans in a roster |

### Business scenarios (10 tools, preview)

Business scenarios let applications create and manage Planner tasks with custom policies. These are preview endpoints on the Graph beta API:

| Tool | Description |
|------|-------------|
| list_business_scenarios | Get all scenarios in the tenant |
| get_business_scenario | Get a specific scenario by ID |
| create_business_scenario | Create a new business scenario |
| update_business_scenario | Update scenario name and owners |
| delete_business_scenario | Delete a scenario and all its data |
| get_scenario_planner | Get Planner configuration for a scenario |
| get_scenario_plan | Get the plan for a scenario and group |
| list_scenario_tasks | Get all tasks for a scenario |
| create_scenario_task | Create a task for a scenario |
| get_plan_configuration | Get plan configuration (buckets, localization) |
| get_task_configuration | Get task configuration (edit policies) |

## ETag concurrency control

Planner uses ETags for optimistic concurrency on every update and delete operation. Your agent must first read the item to get its current `@odata.etag` value, then pass that value when modifying or deleting.

This is a pattern the agent handles naturally: "Update the task title" triggers a `get_task` call to retrieve the ETag, then an `update_task` call with the ETag included.

## API versioning

The connector uses Graph v1.0 for stable operations (plans, tasks, buckets, board formats, my tasks, my plans) and Graph beta for preview features (rosters, business scenarios, archive/unarchive, move plan, favorite plans, recent plans, my day tasks, and delta queries). Beta endpoints may change without notice.

## Agent scenarios

**Sprint planning:**
> "Create a plan for Sprint 24 with buckets for To Do, In Progress, Review, and Done" → Agent calls `create_plan` → `create_bucket` for each column → ready for task assignment

**Daily standup:**
> "What's on my plate today?" → Agent calls `list_my_day_tasks` → summarizes priorities with due dates

**Project archival:**
> "Archive all completed project plans" → Agent calls `list_my_plans` → filters completed plans → `archive_plan` for each one

**Cross-team roster:**
> "Set up a shared plan for the hackathon team without creating a group" → Agent calls `create_roster` → `add_roster_member` for each participant → `create_plan` in the roster

**Change tracking:**
> "What tasks changed since yesterday?" → Agent calls `get_task_delta` → returns only additions, updates, and deletions

## Prerequisites

Azure AD app registration with these delegated permissions:

- `Tasks.ReadWrite` - Read and write Planner tasks
- `Group.ReadWrite.All` - Manage group plans
- `BusinessScenarioConfig.ReadWrite.OwnedBy` - Configure business scenarios (preview)
- `BusinessScenarioData.ReadWrite.OwnedBy` - Manage business scenario data (preview)
- `offline_access` - Refresh tokens

Admin consent may be required for the business scenario permissions.

## Setup

1. Register an Azure AD application
2. Add the delegated permissions listed above
3. Generate a client secret
4. Grant admin consent for business scenario and group permissions
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
4. The agent discovers all 54 tools automatically

## Application Insights

Add your connection string to `script.csx` to track:

- All incoming requests with operation IDs
- MCP tool invocations with timing
- Errors with full exception details

## Resources

- [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Planner)
- [Planner API overview](https://learn.microsoft.com/en-us/graph/api/resources/planner-overview?view=graph-rest-1.0)
- [plannerTask resource](https://learn.microsoft.com/en-us/graph/api/resources/plannertask?view=graph-rest-1.0)
- [Business scenarios overview](https://learn.microsoft.com/en-us/graph/api/resources/businessscenario-overview?view=graph-rest-beta)
