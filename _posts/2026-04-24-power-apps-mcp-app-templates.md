---
layout: post
title: "Power Apps MCP App Templates: widget kit for custom tools in Microsoft 365 Copilot"
date: 2026-04-24 10:00:00 -0500
categories: [Power Platform, MCP]
tags: [Power Apps, MCP Apps, Custom Tools, Model-driven Apps, Microsoft 365 Copilot, Widgets, Fluent UI]
description: "A reusable widget kit and prompt recipe library for building rich visual custom tools in model-driven Power Apps with MCP Apps support for Microsoft 365 Copilot."
---

Model-driven Power Apps can now generate an MCP server and declarative agent from your app. Custom tools extend the built-in grid and form tools with natural language prompts and optional HTML widgets that render tool output as interactive visuals inside chat.

The hard part isn't the protocol. It's designing widgets that look right, handle edge cases, and pair cleanly with the JSON your prompts produce.

This template kit solves that. It ships 18 ready-to-use widget templates and matching prompt recipes so you can go from "I want a KPI dashboard in Copilot" to a working custom tool in minutes.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Apps%20MCP%20App%20Templates)

## Widgets vs. MCP Apps

Microsoft uses two terms interchangeably, and it helps to know both:

- **Widgets** are the self-contained HTML files that render a tool's JSON output visually inside a chat conversation. This is the most common term in Power Apps documentation.
- **MCP Apps** refers to the protocol extension (`@modelcontextprotocol/ext-apps`) that enables MCP servers to deliver interactive UIs to hosts. This term comes from the MCP specification.

In this kit, widget means an individual HTML file you attach to a custom tool. MCP App means the protocol those widgets use to communicate with the host.

## What's in the kit

### 18 widget templates

Every widget follows the MCP Apps protocol and is ready to paste into the tool editor's UX field.

| Widget | File | Data shape | Example use |
|--------|------|-----------|-------------|
| Base Template | `base-widget.html` | Any JSON | Starting point for custom widgets |
| KPI Dashboard | `kpi-dashboard.html` | Aggregate metrics | Revenue, case counts, pipeline totals |
| Record Timeline | `record-timeline.html` | Date-sequenced events | Case history, activity feed, audit trail |
| Status Pipeline | `status-pipeline.html` | Stage-grouped records | Opportunity pipeline, case funnel |
| Comparison Grid | `comparison-grid.html` | Multi-option scored matrix | Vendor comparison, option analysis |
| Data Table | `data-table.html` | Rows + columns (sortable) | Account list, query results, tabular data |
| Approval Card | `approval-card.html` | Single record + actions | Expense approval, change request |
| Progress Tracker | `progress-tracker.html` | Sequential steps | BPF stages, onboarding checklist |
| Alert List | `alert-list.html` | Severity-prioritized items | SLA breaches, overdue tasks |
| Detail Card | `detail-card.html` | Sectioned record profile | Account summary, case detail |
| Donut Chart | `donut-chart.html` | Labeled segments | Cases by priority, leads by source |
| Bar Chart | `bar-chart.html` | Category bars | Revenue by region, count by team |
| Metric Sparkline | `metric-sparkline.html` | Value + trend line | Monthly revenue trend, case volume |
| Kanban Board | `kanban-board.html` | Cards grouped by column | Cases by status, task boards |
| Hierarchy Tree | `hierarchy-tree.html` | Parent-child nesting | Account hierarchy, BU structure |
| Calendar Heat Map | `calendar-heatmap.html` | Date x intensity grid | Case creation density, activity patterns |
| Before/After | `before-after.html` | Field-level diffs | Audit history, change tracking |
| Calendar | `calendar.html` | Month grid with events | Appointments, due dates, SLA deadlines |

### Prompt recipes for every widget

Each widget has a matching prompt pattern you paste into the tool's instructions field. The prompt tells the AI model how to query Dataverse and shape JSON output that the widget expects.

## How to use a widget

1. Create a custom tool in your model-driven app's App MCP tab
2. Write prompt instructions that produce JSON matching the widget's contract (documented in each HTML file's header comment)
3. Test the tool and verify the JSON output
4. Open the widget HTML from this kit that matches your data pattern
5. Paste the HTML into the tool's UX field (step 2 of the tool editor)
6. Download and re-upload the app package to Teams or Microsoft 365 Agents

## Widget architecture

Every widget follows the same structure:

```
┌─ <head> ──────────────────────────────────────────┐
│  Fluent Web Components (UMD)                       │
│  CSS using Fluent design tokens                    │
└────────────────────────────────────────────────────┘
┌─ <body> ──────────────────────────────────────────┐
│  #loading  — spinner + contextual message          │
│  #content  — rendered visualization                │
│  #error    — error message + retry button          │
└────────────────────────────────────────────────────┘
┌─ <script type="module"> ─────────────────────────┐
│  Import App class + Fluent tokens (ESM)            │
│  show() / showError() / applyTheme() / esc()       │
│  render(data) — widget-specific                    │
│  Protocol handlers → connect()                     │
│  Optional: callServerTool for interactivity        │
│  Optional: fallback data for local preview         │
└────────────────────────────────────────────────────┘
```

All widgets pull three CDN dependencies:

| Package | Format | Source | Purpose |
|---------|--------|--------|---------|
| `@modelcontextprotocol/ext-apps` | ESM | cdn.jsdelivr.net | App class (protocol) |
| `@fluentui/tokens` | ESM | cdn.jsdelivr.net | Theme tokens (light/dark) |
| `@fluentui/web-components@beta` | UMD | unpkg.com | Fluent UI elements |

### Fluent design tokens

Widgets use Fluent design tokens for all colors, so they adapt to light and dark mode automatically. No hardcoded hex or RGB values.

| Purpose | Token |
|---------|-------|
| Primary text | `var(--colorNeutralForeground1)` |
| Secondary text | `var(--colorNeutralForeground2)` |
| Card background | `var(--colorNeutralBackground2)` |
| Brand/accent | `var(--colorBrandBackground)` |
| Borders | `var(--colorNeutralStroke1)` |
| Error | `var(--colorStatusDangerForeground1)` |
| Success | `var(--colorStatusSuccessForeground1)` |

## Prompt recipe examples

### KPI Dashboard

```
Query the {table} table. Count all records where statecode eq 0.
Sum the {column} column. Calculate the average {column}.
Count records created in the last 30 days.

Return JSON with "title" (string) and "metrics" (array).
Each metric has: "label" (string), "value" (number),
"format" ("currency", "percent", or "number"),
"trend" (number, percent change from previous period),
"target" (number, optional goal for progress bar).
```

### Record Timeline

```
Query the {table} table. Select {date_column}, {title_column},
{description_column}, {status_column}.
Filter to records related to the input parameter {record_id}.
Order by {date_column} descending. Top 20.

Return JSON with "title" (string) and "events" (array).
Each event has: "date" (ISO 8601), "title" (string),
"description" (string), "type" ("success", "warning", "error", or "info").
Map status: Resolved→success, Escalated→warning, Failed→error, other→info.
```

### Kanban Board

```
Query {table} assigned to the current user. Group by {status_column}.
For each record return ticket number (id), subject (title),
customer or parent name (subtitle), and priority (badge).

Return JSON with "title" (string) and "columns" (array).
Each column has: "name" (status label) and "cards" (array).
Each card has: "id", "title", "subtitle", "badge" (optional).
Order columns by workflow progression.
```

The kit includes prompt recipes for all 18 widgets plus a tool chaining pattern for passing structured data between tools.

## Interactive callbacks with callServerTool

Widgets aren't limited to displaying data. The Approval Card widget demonstrates how to call back into the MCP server to trigger actions.

When the user clicks Approve or Reject, the widget calls:

```javascript
const result = await app.callServerTool({
  name: TOOL_NAME,
  arguments: { action: "approve", id: record.id }
});
```

The MCP server executes the target tool, which updates Dataverse, and returns a result. The widget shows success or failure feedback inline.

To set this up:

1. Create a second custom tool in the same app (for example, "Process Approval")
2. In its prompt instructions, handle the `action` and `id` parameters to update the record's status
3. In the Approval Card widget HTML, set `TOOL_NAME` to that tool's name

When `TOOL_NAME` is `null` (the default), button clicks show visual feedback only without calling the server.

## Local preview

Every widget includes a commented-out fallback section at the bottom of the `<script>` block. Uncomment it to render sample data in a plain browser without an MCP host:

```javascript
// --- Local preview (uncomment to test in a browser) ---
const SAMPLE = {
  "title": "My Dashboard",
  "metrics": [{ "label": "Open Cases", "value": 42, "format": "number" }]
};
render(SAMPLE); show('content');
```

Open the `.html` file directly in a browser, uncomment the `SAMPLE` block, replace the JSON with your test data, and verify the layout. Re-comment the block before pasting into Power Apps.

Theme tokens won't resolve in a plain browser (no host context), so colors fall back to CSS defaults.

## Generating custom widgets

For data shapes not covered by this kit, use the `/generate-mcp-app-ui` skill:

```
/generate-mcp-app-ui Show a bar chart of revenue by region.
Tool output: {"regions":[{"name":"West","revenue":340000},{"name":"East","revenue":520000}]}
```

Install the skill via: `/plugin marketplace add microsoft/power-platform-skills`

## Beyond the kit

These niche visualizations can be generated on demand with `/generate-mcp-app-ui`:

| Visualization | Data shape | Example use |
|--------------|-----------|-------------|
| Geo Map | Points with lat/lng | Account locations, service territory |
| Gantt Timeline | Tasks with start/end dates | Project schedule, SLA tracking |
| Sankey Diagram | Nodes and links | Lead flow, process transitions |
| Scatter Plot | X/Y points | Revenue vs. deal count, risk matrix |
| Stacked Bar | Categories with segments | Revenue by region broken down by product |

## Hybrid pattern: App MCP + external MCP

A model-driven app's declarative agent can combine built-in App MCP tools with external MCP servers:

- **App MCP custom tools** handle Dataverse queries and visualizations with no hosting required
- **External MCP server** (Power Platform custom connector) handles external API calls such as Salesforce, HubSpot, or Graph

The declarative agent manifest supports multiple plugin references pointing to different MCP endpoints. Your existing custom connectors can work alongside App MCP tools in the same agent.

## Prerequisites

- A model-driven Power App
- Microsoft 365 Copilot license
- Permission to upload custom apps in Microsoft Teams
- (Optional) GitHub Copilot CLI or Claude Code with the `generate-mcp-app-ui` skill

## Resources

- [Power Apps MCP App Templates source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Apps%20MCP%20App%20Templates)
- [Enable your app and custom tools in Microsoft 365 Copilot](https://learn.microsoft.com/power-apps/maker/model-driven-apps/enable-your-app-copilot)
- [Generate MCP app widgets with AI code generation tools](https://learn.microsoft.com/power-apps/maker/model-driven-apps/generate-mcp-app-widgets)
- [MCP Apps protocol specification](https://apps.extensions.modelcontextprotocol.io/api/documents/Overview.html)
- [MCP Apps now available in Copilot Chat](https://devblogs.microsoft.com/microsoft365dev/mcp-apps-now-available-in-copilot-chat/)
- [Custom tools and rich UI for app-based conversations](https://www.microsoft.com/power-platform/blog/2026/04/22/custom-tools-and-rich-ui-for-app-based-conversations-are-now-in-public-preview/)
