---
layout: post
title: "Copilot Studio Evaluations MCP connector for Power Platform"
date: 2026-04-17 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Copilot Studio, Evaluations, MCP, Custom Connectors, Power Platform, Quality Metrics, Test Sets, Power Automate]
description: "Power Platform custom connector for Copilot Studio agent evaluations—manage test sets, trigger quality assessments, and retrieve abstention, relevance, and completeness scores through five MCP tools and five REST operations."
---

You built a Copilot Studio agent. It answers questions, calls connectors, routes to topics. But how do you know if the answers are actually good? Copilot Studio has a built-in evaluation framework that scores agents on abstention (did it answer?), relevance (was the answer on topic?), and completeness (was the answer thorough?). The problem is it's manual—you open the UI, pick a test set, click run, and wait.

This connector makes agent evaluation programmatic. Five MCP tools and five REST operations that let a Copilot Studio agent or Power Automate flow manage test sets, trigger evaluation runs, and retrieve quality metrics through the [Power Platform REST API](https://learn.microsoft.com/en-us/rest/api/power-platform/copilotstudio/bots). Schedule nightly quality checks, build dashboards from evaluation results, or let an agent evaluate itself and recommend improvements.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Evaluations)

## Tools

### MCP tools for Copilot Studio

| Tool | Description |
|------|-------------|
| `get_test_sets` | List all test sets for an agent |
| `get_test_set_details` | Get a specific test set with all test cases |
| `start_evaluation` | Launch an evaluation run with optional authentication |
| `get_run_details` | Retrieve quality metrics and test results |
| `list_test_runs` | Get all historical evaluation runs |

### REST operations for Power Automate

| Operation | Method | Description |
|-----------|--------|-------------|
| Get Agent Test Sets | GET | Retrieve test set inventory with metadata |
| Get Agent Test Set Details | GET | View individual test cases within a set |
| Start Agent Evaluation | GET | Trigger an async evaluation run and get a run ID |
| Get Agent Test Run Details | GET | Retrieve completed evaluation results |
| Get Agent Test Runs | GET | List all evaluation runs for an agent |

## Quality metrics

Each completed evaluation returns three scores:

| Metric | What it measures |
|--------|-----------------|
| **Abstention** | Percentage of questions the agent declined to answer. Low is usually better, but some abstention on edge cases is healthy. |
| **Relevance** | How well the agent's responses matched the expected topic. Higher is better. |
| **Completeness** | How thorough the agent's responses were. Higher is better. |

Results also include `aiResultReason`—an AI-generated explanation of overall performance that summarizes what went well and where the agent struggled.

## How it works

```
User: "Run the compliance test set against our customer service agent"

1. Orchestrator calls get_test_sets({
     environmentId: "env-uuid",
     botId: "bot-uuid"
   })
   → Returns test sets: ["Compliance Testing", "FAQ Coverage",
                          "Edge Cases"]

2. Orchestrator calls start_evaluation({
     environmentId: "env-uuid",
     botId: "bot-uuid",
     testSetId: "compliance-test-set-uuid"
   })
   → { runId: "run-uuid-12345",
       state: "Running",
       totalTestCases: 25,
       testCasesProcessed: 0 }

3. After 2-3 minutes, orchestrator calls get_run_details({
     environmentId: "env-uuid",
     botId: "bot-uuid",
     testSetId: "compliance-test-set-uuid",
     runId: "run-uuid-12345"
   })
   → { state: "Completed",
       metricsResults: [
         { name: "Abstention", score: 0.12 },
         { name: "Relevance", score: 0.94 },
         { name: "Completeness", score: 0.87 }
       ],
       aiResultReason: "Agent handled 22 of 25 cases well.
         Abstained on 3 policy exception questions.
         Relevance was strong across all categories.
         Completeness dropped on multi-step procedures." }

4. Agent responds: "Compliance evaluation complete.
   Abstention: 12%, Relevance: 94%, Completeness: 87%.
   The agent deferred on 3 policy exception questions—
   consider adding knowledge articles on policy exceptions
   to improve completeness on multi-step procedures."
```

## Scheduling nightly evaluations

Build a Power Automate flow that evaluates agent quality on a schedule:

```
1. Trigger: Scheduled (daily at 2 AM)
2. Get Agent Test Sets
   - Environment ID: [your-env-id]
   - Bot ID: [your-agent-id]
3. For Each test set:
   4. Start Agent Evaluation
      - Test Set ID: current test set ID
   5. Do Until state = "Completed" or "Failed"
      - Get Agent Test Run Details
      - Delay 30 seconds
   6. Parse metrics from response
   7. Send results summary to admin email or post to Teams
```

This catches quality regressions before users do—if a knowledge source update breaks answers in a specific category, you'll know by morning.

## Authenticated evaluations

Some agents use authenticated connections (for example, a Copilot Studio connection that accesses user-specific data). To evaluate these agents accurately, pass the `mcsConnectionId` parameter when starting an evaluation:

1. Go to [Power Automate](https://make.powerautomate.com/)
2. Open the **Connections** page
3. Select the Microsoft Copilot Studio connection
4. Copy the `mcsConnectionId` from the URL

The evaluation then runs with that connection's credentials, testing the agent as a real user would experience it.

## Authentication

OAuth 2.0 with Microsoft Entra ID. Register an app with **Power Platform API** permissions and the `.default` scope.

### Prerequisites

1. **App registration** in Microsoft Entra ID with Power Platform API access
2. **Environment ID** and **Bot ID** for the target agent
3. **Test sets** created in Copilot Studio with Active state
4. (Optional) **MCS Connection ID** for authenticated evaluations

## Application Insights logging

The connector includes hardcoded Application Insights telemetry. Enable it in `script.csx`:

```csharp
private const bool APP_INSIGHTS_ENABLED = true;
private const string APP_INSIGHTS_KEY = "your-instrumentation-key";
```

Logged events:

- **Operation events** — Request/response for each API call
- **MCP tool invocations** — Details of each Copilot Studio tool usage
- **Evaluation lifecycle** — Start, progress updates, completion
- **Errors and exceptions** — Diagnostics with stack traces

### Useful queries

```kusto
// All MCP tool calls
customEvents
| where name == "MCP_ToolCall"
| summarize Count = count() by tostring(customDimensions.ToolName)

// Evaluation errors
customExceptions
| where tostring(customDimensions.Connector) == "Copilot Studio Agent Evaluation"
| project timestamp, outerType, outerMessage, customDimensions.Operation
```

## Limitations

- Evaluations are asynchronous—allow 2-5 minutes for completion depending on test set size
- Test sets must have Active state to run
- Maximum 200 test cases per set (Power Platform limit)
- Requires tenant admin or delegated Power Platform API access

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 5 REST operations |
| `apiProperties.json` | OAuth 2.0 auth config and script operation bindings |
| `script.csx` | C# script handling MCP protocol routing and Application Insights telemetry |
| `readme.md` | Setup and usage documentation |

## Resources

- [Copilot Studio Evaluations connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Evaluations)
- [Copilot Studio agent evaluation documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/analytics-agent-evaluation-intro)
- [Run evaluations using tools/flows](https://learn.microsoft.com/en-us/microsoft-copilot-studio/analytics-agent-evaluation-automate-tools)
- [Power Platform REST API reference](https://learn.microsoft.com/en-us/rest/api/power-platform/)
- [Application Insights documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
