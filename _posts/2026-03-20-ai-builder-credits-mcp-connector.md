---
layout: post
title: "Monitor credit consumption with AI Builder Credits MCP connector"
date: 2026-03-20 10:00:00 -0600
categories: [Power Platform, Custom Connectors]
tags: [AI Builder, Copilot Studio, Dataverse, MCP, credits, monitoring]
---

With Microsoft's [announcement of the end of AI Builder credits](https://learn.microsoft.com/ai-builder/endofaibcredits), monitoring your credit consumption has become critical. Seeded credits from premium licenses end November 1, 2026, and add-on credits will stop being available for renewal. When credits run out, AI Builder features fall back to Copilot Studio Credits—and if those are exhausted too, your automations stop working.

A customer recently asked me how they could proactively track their AI Builder usage before hitting these limits. The answer: give Copilot Studio agents direct access to the consumption data. This MCP connector queries the `msdyn_aievents` table in Dataverse so agents can report on credit usage, identify high-consumption models, and help plan the transition to Copilot Credits.

## What this connector does

The AI Builder Credits connector queries the `msdyn_aievents` table in Dataverse to retrieve credit consumption data. It provides five MCP tools that let agents:

- List recent AI events with credit details
- Get credit summaries grouped by model and source
- Track daily usage trends
- Retrieve specific event details
- List AI Builder models in the environment

## Available tools

| Tool | Description |
|------|-------------|
| `list_ai_events` | List recent AI Builder events with credit consumption, model name, source, and status |
| `get_credit_summary` | Get credit consumption summary grouped by model and source for a date range |
| `get_daily_usage` | Get daily credit consumption for trend analysis |
| `get_ai_event` | Get details of a specific AI Builder event by ID |
| `list_ai_models` | List AI Builder models in the environment |

## Prerequisites

Before you can use this connector, you need:

- A Power Platform environment with AI Builder usage
- An Azure AD app registration with delegated permissions for Dataverse user access
- Admin consent granted for the permissions

## Setting up the connector

### Register an Azure AD app

1. Go to the [Azure portal](https://portal.azure.com) > **Microsoft Entra ID** > **App registrations**
2. Register a new application or select an existing one
3. Under **Authentication**, add `https://global.consent.azure-apim.net/redirect` as a redirect URI
4. Copy the **Application (client) ID** into the connector's `apiProperties.json` `clientId` field

### Import the connector

1. Download the connector files from the [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/AI%20Builder%20Credits)
2. In the Power Platform admin center, go to **Custom connectors**
3. Import the connector using the swagger and properties files
4. Update the `clientId` in the properties file with your app registration ID

## Tool details

### list_ai_events

List recent AI Builder events with credit consumption details.

**Parameters:**
- `top` (integer) - Maximum events to return (default: 25, max: 100)
- `source` (string) - Filter by source: PowerAutomate, PowerApps, API, or CopilotStudio
- `fromDate` (string) - Filter events from this date (ISO 8601)

**Returns:**
- Event ID, model name, credits consumed, date, source, status, automation name

### get_credit_summary

Get a summary of credit consumption grouped by model and source.

**Parameters:**
- `fromDate` (string) - Start date (defaults to first of current month)
- `toDate` (string) - End date (defaults to today)

**Returns:**
- Total events and credits
- Breakdown by AI model
- Breakdown by source (Power Automate, Power Apps, API, Copilot Studio)

### get_daily_usage

Get credit consumption grouped by day for trend analysis.

**Parameters:**
- `days` (integer) - Days to look back (default: 7, max: 30)

**Returns:**
- Daily usage with event count and credits per day

### get_ai_event

Get details of a specific AI Builder event.

**Parameters:**
- `eventId` (string, required) - The AI event GUID

**Returns:**
- Full event details including model template, automation link, data info

### list_ai_models

List AI Builder models in the environment.

**Parameters:**
- `top` (integer) - Maximum models to return (default: 50)

**Returns:**
- Model ID, name, template type, status, creation date

## The data source

The connector queries the Dataverse `msdyn_aievents` table, which stores:

- **msdyn_creditconsumed** - Credits used per action
- **msdyn_AIModelId** - Reference to the AI model
- **msdyn_processingdate** - When the action occurred
- **msdyn_consumptionsource** - 0=Power Automate, 1=Power Apps, 2=API, 3=Copilot Studio
- **msdyn_processingstatus** - 0=Processed
- **msdyn_automationname** - Name of the flow or app that triggered the action

## How the MCP implementation works

The connector uses a custom script connector pattern with the MCP protocol. The swagger definition includes the `x-ms-agentic-protocol: mcp-streamable-1.0` annotation to enable MCP support:

```json
{
  "paths": {
    "/": {
      "post": {
        "operationId": "InvokeMCP",
        "x-ms-agentic-protocol": "mcp-streamable-1.0",
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "required": true,
            "schema": {
              "type": "object"
            }
          }
        ]
      }
    }
  }
}
```

The `script.csx` file handles all MCP protocol operations and routes tool calls to the appropriate handlers. Each tool queries Dataverse using OData and returns structured JSON responses.

## Known limitations

- **Environment-scoped data** - You need separate connections to monitor multiple environments
- **Periodic computation** - Credit consumption data is computed periodically (typically daily) by the platform
- **Data retention** - Historical data retention depends on your Dataverse capacity settings

## Use cases

This connector is useful for:

- **Cost management** - Track which models and automations consume the most credits
- **Capacity planning** - Analyze usage trends to predict future credit needs
- **Troubleshooting** - Identify which automations are causing unexpected credit consumption
- **Reporting** - Generate usage reports for stakeholders

## Resources

- [Full source code on GitHub](https://github.com/troystaylor/SharingIsCaring/tree/main/AI%20Builder%20Credits)
- [AI Builder Activity Monitoring](https://learn.microsoft.com/ai-builder/activity-monitoring)
- [AI Event (msdyn_AIEvent) table reference](https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/msdyn_aievent)
- [AI Builder Credit Management](https://learn.microsoft.com/ai-builder/credit-management)
