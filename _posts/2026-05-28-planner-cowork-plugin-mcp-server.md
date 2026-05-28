---
layout: post
title: "Build a Planner Cowork plugin with a combined Planner and To Do MCP server"
date: 2026-05-28 09:00:00 -0000
categories: [MCP (Model Context Protocol), Copilot Studio, Integration]
tags: [Microsoft Planner, Microsoft To Do, MCP, Microsoft Graph, Copilot Cowork, Azure]
---

## Why this Planner plugin matters

Microsoft 365 Copilot Cowork is moving toward a plugin model that lets you package skills, connectors, and deployment together. That matters if you want a real task-management experience instead of a thin demo.

My Planner plugin in the [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Planner) does exactly that. It combines a Cowork plugin manifest, skills, and an in-tenant MCP server so Copilot can work with task data in a controlled way.

What makes this one interesting is the data surface: the MCP server combines Microsoft Planner and Microsoft To Do API endpoints in one plugin. That gives you a single experience for group plans, personal plans, and private task lists.

## What the plugin includes

This Planner plugin includes:

- A Cowork plugin manifest
- A skill set for common task workflows
- An MCP server that exposes Planner and To Do operations together
- Azure deployment assets
- Packaging scripts for repeatable builds

Repository folder:

- https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Planner

Repository:

- https://github.com/troystaylor/SharingIsCaring

## Current scope

The README describes a focused task-management scope:

- Plan health summaries and risk detection
- Individual workload snapshots
- Personal and private task lists from Microsoft To Do and personal Planner plans
- Task triage recommendations
- Controlled task updates with user confirmation
- Team capacity monitoring

That mix is useful because it covers both team execution and personal follow-through without splitting the experience across separate tools.

## Skills shipped in the plugin

The plugin ships with eight skills:

- plan-health-summary: Summarize plan status, deadlines, and execution risk
- my-workload-snapshot: Show assigned tasks, due windows, and blockers
- personal-task-list: List tasks from personal and private Planner plans
- personal-weekly-delta: Summarize weekly movement across personal and private tasks
- task-triage: Prioritize tasks by urgency, impact, and dependency
- update-task: Apply controlled updates to Planner tasks and details
- team-capacity-watch: Detect overloaded teammates and rebalance opportunities
- plan-activity-recap: Recap recent plan changes and execution trends

This keeps the plugin aligned to real work patterns: review, prioritize, update, and summarize.

## MCP tool surface

The MCP server exposes tools for both Planner and To Do scenarios:

- `list_group_plans`
- `list_plan_tasks`
- `list_plan_buckets`
- `list_my_tasks`
- `list_my_private_tasks`
- `list_my_personal_tasks`
- `my_personal_tasks_weekly_delta`
- `list_user_tasks`
- `get_task`
- `get_task_details`
- `create_task`
- `update_task`
- `update_task_details`
- `plan_health_summary`

That combined surface is the key design choice. Instead of making users switch between separate plugins for Planner and To Do, the server exposes a single MCP layer over both endpoint families.

## Microsoft Graph endpoints

The plugin maps to Microsoft Graph Planner and To Do endpoints in v1.0:

- `GET /groups/{group-id}/planner/plans`
- `GET /planner/plans/{plan-id}/tasks`
- `GET /planner/plans/{plan-id}/buckets`
- `GET /me/planner/plans`
- `GET /me/planner/tasks`
- `GET /me/todo/lists`
- `GET /me/todo/lists/{todoTaskListId}/tasks`
- `GET /users/{id}/planner/tasks`
- `GET /planner/tasks/{id}`
- `GET /planner/tasks/{id}/details`
- `POST /planner/tasks`
- `PATCH /planner/tasks/{id}` with `If-Match`
- `PATCH /planner/tasks/{id}/details` with `If-Match`

That endpoint mix is what lets the plugin handle group plans, personal plans, and To Do lists in one place.

## Manifest and runtime notes

The README calls out an important implementation detail: the plugin uses the `devPreview` Teams manifest schema. The v1.28 `agentConnectors.remoteMcpServer` path expects a static `mcpToolDescription.file`, but Cowork does not bind the connector cleanly in practice.

With `devPreview`, Cowork discovers tools dynamically through MCP `tools/list`, which is the working path for this plugin.

## Deploy to Azure

The deployment flow is straightforward:

1. Set the Azure environment values.
2. Validate the template.
3. Provision the infrastructure.
4. Copy the `MCP_FULL_URL` output into `manifest.json`.
5. Register the OAuth Plugin Vault entry in Cowork.
6. Set the returned `referenceId` in the manifest.
7. Package and upload the plugin.

The repo also includes a development packaging command:

```powershell
cd "Cowork Plugins/Planner"
./package.ps1 -SkipIcons
```

## Why this pattern is useful

This plugin is a good example of how to design for task workflows instead of just exposing raw APIs.

You get:

- One plugin surface for team and personal tasks
- Skills that match how people actually talk about work
- A single MCP server that combines Planner and To Do endpoints
- A deployment model that fits enterprise controls

That combination makes the plugin easier to adopt and easier to extend.

## Resources

- [Planner Cowork plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Planner)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
- [Copilot Cowork plugin development](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
- [Plugin authentication](https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-authentication)
- [Microsoft Graph Planner overview](https://learn.microsoft.com/graph/api/resources/planner-overview?view=graph-rest-1.0)
