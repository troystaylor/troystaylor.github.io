---
layout: post
title: "Power Rubber Duck MCP connector for Copilot Studio"
date: 2026-04-20 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Power Rubber Duck, Copilot Studio, MCP, Custom Connectors, Power Platform, Decision Intelligence, Cognitive Bias, Azure AI Foundry]
description: "A Power Platform custom connector that adds multi-perspective decision analysis to Copilot Studio with MCP tools for second opinions, risk analysis, cognitive bias detection, and option comparison, plus shared decision resources."
---

High-stakes decisions usually break for the same reason: we only look from one angle.

Power Rubber Duck is a Power Platform custom connector that exposes a full MCP server to Copilot Studio. It gives your agent four analysis tools and a shared resource library, so you can challenge assumptions, compare tradeoffs, and check for reasoning blind spots before you commit.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Rubber%20Duck)

## What this connector adds

You get two capabilities in one connector:

1. **Tool-driven analysis** for dynamic decision support
2. **Resource-driven grounding** for consistent frameworks and checklists

That combination matters. Tools help your agent reason in the moment. Resources keep the reasoning anchored to reusable standards.

## MCP tools

| Tool | Description | Typical use |
|------|-------------|-------------|
| `get_second_opinion` | Gets an alternate perspective from a secondary Foundry model | Validate strategy, challenge assumptions, and reduce tunnel vision |
| `analyze_risk` | Produces structured risk analysis with mitigation ideas | Evaluate downside before launching initiatives |
| `identify_cognitive_biases` | Detects common bias patterns in your reasoning | Catch confirmation bias, anchoring, or overconfidence |
| `comparative_analysis` | Compares multiple options against criteria and tradeoffs | Build vs buy vs partner, platform choices, process changes |

## MCP resources

The connector exposes 10 resources that Copilot Studio can read with `resources/list` and `resources/read`:

- 3 decision frameworks: investment, operational change, and strategic planning
- 2 knowledge assets: benchmarks and case studies
- 3 reasoning guides: bias checklist, decision process, and critical questions
- 2 best-practice guides: implementation and organizational decision-making

These resources make outcomes more consistent across prompts and users because the agent can pull from the same decision playbook every time.

## How it works in Copilot Studio

```text
User asks a decision question
  -> Copilot Studio reads a decision framework resource
  -> Copilot Studio calls get_second_opinion
  -> Copilot Studio calls analyze_risk
  -> Copilot Studio calls identify_cognitive_biases
  -> Copilot Studio synthesizes recommendation + rationale
```

The MCP endpoint supports:

- `tools/list`
- `tools/call`
- `resources/list`
- `resources/read`

It also includes direct REST operations for each tool and resource action, which is useful when you want to call them from Power Automate or test each operation independently.

## Example decision flow

Say your team is deciding whether to enter a new market.

1. Read `resource://decision-frameworks/strategic`
2. Call `get_second_opinion` with `analysis_depth: "deep"`
3. Call `analyze_risk` for technical, financial, and organizational risks
4. Call `identify_cognitive_biases` on your current plan narrative
5. Call `comparative_analysis` across options: build, partner, acquire
6. Return a recommendation with risks, mitigations, and monitoring signals

That gives you a recommendation plus an audit trail of why the recommendation was made.

## Deploy the connector

### Prerequisites

- Power Platform CLI (`pac`)
- A Copilot Studio environment
- A Foundry-compatible model endpoint (local or cloud)

### Validate and create

```powershell
# Validate connector
ppcv ".\Power Rubber Duck"

# Create connector
pac connector create --api-definition-file ".\Power Rubber Duck\apiDefinition.swagger.json" `
                     --api-properties-file ".\Power Rubber Duck\apiProperties.json" `
                     --script-file ".\Power Rubber Duck\script.csx"
```

### Configure model endpoint

In `script.csx`, set:

```csharp
private string foundryEndpoint = "http://endpoint";
private string foundryModel = "phi-4";
```

You can also override these with connection parameters (`foundry_endpoint` and `foundry_model`) in the connector configuration.

## Observability with Application Insights

The script includes telemetry hooks for MCP requests, tool calls, resource reads, model calls, and exceptions.

Once you set your instrumentation key in `script.csx`, you can track:

- Which tools are used most
- Which resources are read most
- Error patterns by operation
- Model response characteristics over time

This helps you improve both agent quality and runtime reliability.

## Why this pattern is useful

Most agent decisions fail quietly. You get fluent output, but weak reasoning.

Power Rubber Duck pushes your agent to:

- Use multiple perspectives
- Challenge its own assumptions
- Compare options explicitly
- Ground recommendations in shared decision assets

If you care about decision quality, not just answer quality, this is a practical pattern to adopt.

## Files in the project

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI definition, MCP endpoint, and direct operations |
| `apiProperties.json` | Connector metadata and connection parameters |
| `script.csx` | MCP routing, tool logic, resources, Foundry calls, and telemetry |
| `readme.md` | Setup guide, examples, and troubleshooting |

## Resources

- [Power Rubber Duck source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Rubber%20Duck)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Custom connectors overview](https://learn.microsoft.com/en-us/connectors/custom-connectors/)
- [Power Platform CLI overview](https://learn.microsoft.com/en-us/power-platform/developer/cli/introduction)
- [Application Insights overview](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
