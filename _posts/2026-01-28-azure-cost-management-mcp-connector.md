---
layout: post
title: "Azure Cost Management MCP connector for Power Platform"
date: 2026-01-28 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Azure Cost Management, MCP, Connector, Copilot Studio, Power Platform, Power Automate, Budgets, Forecasts, Exports]
---

## Overview
Bring Azure Cost Management into Copilot Studio and Power Platform with a full MCP server and custom connector. Query costs, forecasts, budgets, alerts, exports, and more across subscriptions, resource groups, management groups, billing accounts, and benefit scopes. Pair it with the native Power BI Azure Cost Management connector for dashboards and ad hoc analysis: [Connect Azure Cost Management to Power BI](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-connect-azure-cost-management).

> My repo: [Azure Cost Management connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Cost%20Management)

## What You Get
- **58 operations** covering cost queries, forecasts, budgets, alerts, exports, views, scheduled actions, allocation rules, benefit utilization, reports, settings, price sheets
- **MCP server** (`azure-cost-management`, protocol `2025-03-26`) with **10 tools** for Copilot Studio
- **Response shaping** for Power Platform (named fields, computed budget utilization)
- **App Insights telemetry** baked in (request, query, budget, MCP tool calls)

## Prerequisites
- Azure subscription with Cost Management access
- Azure AD app registration (pre-configured in repo)
- RBAC: Cost Management Reader/Contributor, Billing Reader as needed
- Power Platform environment (Dev) and Copilot Studio

## Deploy the Connector
```powershell
pac connector create --environment <environment-id> --api-definition-file apiDefinition.swagger.json --api-properties-file apiProperties.json --script-file script.csx
```

When creating a connection, sign in with the app registration. The swagger and script are in the repo folder.

## MCP Tools for Copilot Studio
Server name: `azure-cost-management`

Tools include:
- `query_subscription_costs`, `query_resource_group_costs`, `query_management_group_costs`
- `get_subscription_forecast`
- `list_subscription_budgets`, `get_budget`, `create_budget`, `update_budget`, `delete_budget`
- `list_dimensions`, `list_cost_alerts`, `dismiss_alert`
- `list_exports`, `create_export`, `run_export`, `delete_export`
- `list_views`, `create_view`, `generate_cost_report`

Example MCP call:
```javascript
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query_subscription_costs",
    "arguments": {
      "subscriptionId": "00000000-0000-0000-0000-000000000000",
      "queryType": "Usage",
      "timeframe": "MonthToDate",
      "granularity": "Daily",
      "groupBy": "ServiceName"
    }
  }
}
```

## Sample Cost Query Payloads
Query monthly costs by service:
```javascript
{
  "type": "Usage",
  "timeframe": "MonthToDate",
  "dataset": {
    "granularity": "Daily",
    "aggregation": {
      "totalCost": { "name": "Cost", "function": "Sum" }
    },
    "grouping": [{ "type": "Dimension", "name": "ServiceName" }]
  }
}
```

Create a budget:
```javascript
{
  "properties": {
    "category": "Cost",
    "amount": 1000,
    "timeGrain": "Monthly",
    "timePeriod": {
      "startDate": "2025-01-01T00:00:00Z",
      "endDate": "2025-12-31T00:00:00Z"
    },
    "notifications": {
      "alert80": {
        "enabled": true,
        "operator": "GreaterThan",
        "threshold": 80,
        "thresholdType": "Actual",
        "contactEmails": ["admin@contoso.com"],
        "frequency": "Daily"
      }
    }
  }
}
```

## Enable Telemetry
In `script.csx`, set your Application Insights connection string:
```csharp
private const string APP_INSIGHTS_CONNECTION_STRING = "InstrumentationKey=xxx;IngestionEndpoint=https://xxx.in.applicationinsights.azure.com/";
```

Events emitted: `CostManagement_RequestReceived`, `CostManagement_QueryProcessed`, `CostManagement_BudgetProcessed`, `MCPToolCall`, `MCPToolError`, and more.

## Copilot Studio setup
1. Deploy connector and create a connection.
2. Add MCP server to Copilot Studio (server name `azure-cost-management`).
3. Enable tools you need (cost queries, budgets, exports).
4. Ground responses with Copilot Studio Knowledge (docs, runbooks) for guidance.
5. Add safety and instructions; test with sample tool calls.

## Governance and Limits
- API rate limits apply (handle 429 with backoff).
- Scope-aware permissions: subscription vs. management group vs. billing.
- DLP: classify connector appropriately.
- Use official sources and telemetry to monitor usage.

## Resources
- Repo: [Azure Cost Management connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Cost%20Management)
- Docs: [Azure Cost Management REST](https://learn.microsoft.com/en-us/rest/api/cost-management/)
- Power BI: [Connect Azure Cost Management to Power BI](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-connect-azure-cost-management)
- Best practices: [Cost management](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/cost-mgt-best-practices)

