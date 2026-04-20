---
layout: post
title: "HVE Guidance MCP connector for Copilot Studio"
date: 2026-04-20 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [HVE, Copilot Studio, MCP, Custom Connectors, Power Platform, AI Engineering, GitHub, Validation]
description: "A Power Platform custom connector that exposes the microsoft/hve-core AI engineering repository through 12 MCP tools, letting Copilot Studio agents discover, validate, and plan adoption of HVE guidance assets."
---

AI engineering standards are only useful if developers can find them, apply them, and validate their work against them. The [microsoft/hve-core](https://github.com/microsoft/hve-core) repository holds curated guidance for AI engineering—instructions, prompts, skills, and agent configurations—but browsing a GitHub repository is not a natural part of a Copilot Studio conversation.

This connector bridges that gap. Twelve MCP tools let your agent discover assets, validate content quality, track changes, and generate adoption plans, all without leaving the conversation.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/HVE%20Guidance)

## What the connector covers

The 12 tools group into four areas:

### Discovery

| Tool | Description |
|------|-------------|
| `list_assets` | List HVE assets by type (agent, instruction, prompt, skill, collection) or path |
| `get_asset` | Retrieve a single asset with frontmatter metadata, intended use, constraints, and related assets |
| `search_assets` | Keyword search across the repository |
| `recommend_assets_for_task` | Score and rank assets by relevance to a task description |

### Validation

| Tool | Description |
|------|-------------|
| `validate_instruction` | Check instruction markdown for structure, safety signals, and completeness |
| `validate_prompt` | Check prompt quality and flag unsafe patterns |
| `validate_agent_config` | Validate JSON agent configurations for required fields and structure |

### Change intelligence

| Tool | Description |
|------|-------------|
| `summarize_asset_changes` | Summarize recent commits for a path or asset type |
| `compare_asset_versions` | Compare two refs for a specific file and report whether it changed materially |
| `get_release_highlights` | Retrieve release notes from the repository |

### Workflow and adoption

| Tool | Description |
|------|-------------|
| `get_workflow_for_scenario` | Return a suggested workflow for a given engineering scenario |
| `generate_adoption_plan` | Generate a phased adoption plan for a team with specific goals and a timeline |

## How the tools work together

The tools compose naturally in a conversation. An agent can:

1. Call `recommend_assets_for_task` to find relevant assets for "add governance to our agent pipeline"
2. Call `get_asset` on the top result to see intended use, constraints, and related assets
3. Call `validate_instruction` against a draft instruction to catch issues before merging
4. Call `generate_adoption_plan` to produce a phased rollout for the team

The recommendation tool goes beyond path matching. It scores candidates using task intent labels, frontmatter metadata, and summary matching, so "add code review standards" doesn't return generic onboarding assets.

Validation tools return structured findings with three fields per issue: what the problem is, why it matters, and how to fix it. That structure is more useful to an agent than a plain warning string.

## Asset types

The connector maps asset types to their standard HVE repository paths:

| Type | Path |
|------|------|
| `agent` | `.github/agents` |
| `instruction` | `.github/instructions` |
| `prompt` | `.github/prompts` |
| `skill` | `.github/skills` |
| `collection` | `collections` |

## Example prompt flows

### Discover and review

```text
User: What HVE assets should I use for a risky multi-file refactor?
Agent: [recommend_assets_for_task] → planning, research, review assets ranked by relevance
Agent: [get_asset] → opens top asset, shows constraints and related assets
```

### Validate before merging

```text
User: Validate this instruction and tell me what to fix.
Agent: [validate_instruction] → returns findings with message, why, and fix per issue
```

### Team rollout planning

```text
User: Create an 8-week adoption plan for the API Platform team to standardize agent prompts.
Agent: [generate_adoption_plan] → phased milestones, relevant tool suggestions, team-scoped goals
```

### Track what changed

```text
User: Summarize HVE instruction changes from the last 30 days.
Agent: [summarize_asset_changes] → commit list scoped to instruction paths
User: Did the code review instruction change materially since last month?
Agent: [compare_asset_versions] → diff summary with changed status and estimated line deltas
```

## Runtime details

The connector reads from GitHub using the REST API with short-lived in-memory caching (5 minutes for most operations, 2 minutes for search) to reduce duplicate requests and lower latency. GitHub throttling errors return structured retry metadata rather than unhandled exceptions.

Tool errors return as MCP tool results with `isError: true`, so the agent can handle failures gracefully without breaking the conversation.

## Authentication

Connection parameters:

| Parameter | Required | Default |
|-----------|----------|---------|
| GitHub Token | Yes | — |
| Repository Owner | No | `microsoft` |
| Repository Name | No | `hve-core` |
| Branch | No | `main` |

Use a read-only personal access token scoped to repository access. Pointing the connector at a fork or internal mirror changes only the connection parameters—the tool logic stays the same.

## Deploy

```powershell
pac auth create --environment "https://yourorg.crm.dynamics.com"

pac connector create `
  --api-definition-file apiDefinition.swagger.json `
  --api-properties-file apiProperties.json `
  --script-file script.csx
```

If `--script-file` fails in your environment, upload `script.csx` manually in the connector **Code** tab after creation.

## Evaluation pack

The repository includes `docs/evaluation-scenarios.md` with 14 manual scenarios covering discovery, retrieval, recommendation, validation, change intelligence, and adoption planning. Each scenario includes expected tool selection and scoring criteria across tool correctness, result usefulness, explanation quality, ranking, and actionability.

Use it to track quality regressions when the upstream HVE repository changes or when you swap the connected repository.

## Observability

Add your Application Insights instrumentation key to `script.csx` to enable telemetry:

```csharp
private const string APP_INSIGHTS_KEY = "your-instrumentation-key";
```

Logged events include `McpRequestReceived`, `McpRequestCompleted`, and per-tool exceptions with correlation IDs across all events.

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI definition with the single MCP streamable endpoint |
| `apiProperties.json` | Connector metadata and GitHub connection parameters |
| `script.csx` | MCP routing, all 12 tool handlers, caching, validation logic, and telemetry |
| `docs/evaluation-scenarios.md` | Manual evaluation pack with 14 scenarios and a scoring rubric |

## Resources

- [HVE Guidance connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/HVE%20Guidance)
- [microsoft/hve-core repository](https://github.com/microsoft/hve-core)
- [Custom connectors overview](https://learn.microsoft.com/en-us/connectors/custom-connectors/)
- [Power Platform CLI overview](https://learn.microsoft.com/en-us/power-platform/developer/cli/introduction)
- [Application Insights overview](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
