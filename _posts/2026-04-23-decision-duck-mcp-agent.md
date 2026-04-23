---
layout: post
title: "Decision Duck: a decision-support agent for Microsoft 365 Copilot"
date: 2026-04-23 10:00:00 -0500
categories: [Copilot Studio, MCP]
tags: [Microsoft 365 Copilot, MCP, Declarative Agents, Decision Support, Azure Container Apps, AI Foundry, .NET]
description: "Build a declarative agent for Microsoft 365 Copilot that provides structured decision support through second opinions, risk analysis, cognitive bias detection, and option comparisons, powered by a remote MCP server on Azure Container Apps."
---

Making high-stakes decisions under time pressure usually means skipping steps. You move fast, pick the obvious option, and only realize later that you missed a risk or fell into a bias trap.

Decision Duck is a declarative agent for Microsoft 365 Copilot that gives you structured decision support directly in your workflow. Ask for a second opinion, run a risk analysis, check for cognitive biases, or compare options side by side without leaving the Copilot surface.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Decision%20Duck)

## What this project includes

Decision Duck is an agent-plus-plugin project. It combines a declarative agent manifest, a plugin definition, and a remote MCP server that calls Azure AI Foundry (or any OpenAI-compatible endpoint) for structured reasoning.

The project ships with:

- **4 analysis tools** powered by AI Foundry
- **2 knowledge tools** that expose reusable decision frameworks
- **MCP Apps support** for inline UI rendering in Copilot
- **Agent package artifacts** ready for Microsoft 365 Agents Toolkit
- **Azure infrastructure templates** for Container Apps deployment

## MCP tools

The MCP server exposes six tools:

| Tool | Purpose |
|------|---------|
| `get_second_opinion` | Alternative perspective on a decision or analysis |
| `analyze_risk` | Structured risk analysis with mitigations and leading indicators |
| `identify_cognitive_biases` | Spot likely biases and get practical corrections |
| `comparative_analysis` | Compare options, call out tradeoffs, and recommend a path |
| `list_frameworks` | List available decision frameworks |
| `get_framework` | Retrieve a specific framework by ID |

The first four tools call an AI model (Azure AI Foundry or any OpenAI-compatible endpoint). The last two serve static content from built-in knowledge assets.

## Analysis depth and focus

The `get_second_opinion` tool accepts an optional `analysis_depth` parameter with three levels:

- **quick** for fast, concise feedback
- **balanced** for moderate detail (default)
- **deep** for thorough analysis

You can also pass a `focus_area` to steer the model toward a specific concern, such as security, cost, or timeline risk.

## Built-in decision frameworks

The knowledge tools expose three reusable frameworks:

| Framework ID | Use case |
|-------------|----------|
| `investment` | Assess market, team, financials, and risk before committing capital |
| `operational-change` | Evaluate scope, readiness, change impact, and rollout risk |
| `strategic-planning` | Analyze market shifts, capabilities, scenarios, and strategic options |

The agent instructions tell Copilot to call `list_frameworks` first when frameworks are relevant, then `get_framework` to pull specific content into the conversation.

## MCP Apps: inline UI for comparative analysis

The `comparative_analysis` tool advertises a UI resource at `ui://decision-duck/comparative-analysis.html`. When Copilot supports MCP Apps rendering, this resource provides an inline view that displays the structured comparison output directly in the chat surface.

The server implements both `resources/list` and `resources/read` for the `ui://` resource, following the MCP Apps specification.

## How the agent works

The declarative agent manifest (`declarativeAgent.json`) defines the agent personality, conversation starters, and plugin reference. The agent instructions tell Copilot when to call each tool:

- Use `get_second_opinion` for alternate perspectives
- Use `analyze_risk` for downside analysis
- Use `identify_cognitive_biases` to challenge reasoning
- Use `comparative_analysis` to evaluate options
- Start with `list_frameworks` when frameworks or checklists are relevant

Conversation starters include prompts like "Give me a second opinion on this product launch decision" and "Check this proposal for cognitive bias and blind spots."

## Architecture

The project has three layers:

```
agent-package/          Declarative agent + plugin manifests
  declarativeAgent.json   Agent definition (schema v1.6)
  plugin.json             Plugin with RemoteMCPServer runtime (schema v2.4)
  manifest.json           Microsoft 365 app manifest

mcp-server/             .NET 8 MCP server
  Program.cs              JSON-RPC 2.0 endpoint at /mcp
  Dockerfile              Container image definition

infra/                  Azure deployment
  main.bicep              Container Apps + supporting resources
  deploy.ps1              Deployment automation
```

The plugin uses `RemoteMCPServer` runtime type, which means Copilot calls the MCP endpoint directly over HTTPS using JSON-RPC 2.0.

## MCP server implementation

The server is a single-file .NET 8 minimal API that handles JSON-RPC 2.0 requests at `/mcp`. Key implementation details:

**Input validation** runs before any tool execution. Each tool validates its required arguments and returns clear error messages for bad input.

**Retry logic** uses exponential backoff with jitter for transient model failures. The server retries up to three times on 429, 500, 502, 503, and 504 status codes.

**Fallback mode** kicks in when the model provider returns 429 Too Many Requests. Instead of failing, the `analyze_risk`, `identify_cognitive_biases`, and `comparative_analysis` tools return structured fallback responses with generic guidance and a note that fallback mode was used.

**Request size limits** prevent oversized payloads from reaching the model. The server rejects requests larger than 128 KB.

**Application Insights** integration is optional. Set the `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable to enable telemetry for all MCP requests and tool calls.

## Model configuration

The server connects to any OpenAI-compatible chat completions endpoint. Configure it with three environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `FOUNDRY_ENDPOINT` | `http://localhost:60311/v1` | Model endpoint URL |
| `FOUNDRY_MODEL` | `phi-4` | Model deployment name |
| `FOUNDRY_API_KEY` | (empty) | API key, or omit for managed identity |

For Azure OpenAI and Azure AI Foundry endpoints, the server automatically detects the host and uses `DefaultAzureCredential` when no API key is provided. This means you can use managed identity in production without storing secrets.

## Run locally

```powershell
cd ".\mcp-server"
dotnet run
```

The server starts on the default port with the local Foundry endpoint. Point a local model server (such as AI Foundry local or Ollama with an OpenAI-compatible adapter) at the default endpoint to test without Azure.

## Deploy to Azure

The included Bicep template provisions an opinionated runtime stack:

- **Azure Container Apps** for the MCP server
- **User-assigned managed identity** for secure model access
- **Application Insights + Log Analytics** for observability
- **Key Vault** for secret storage

Run the deployment script:

```powershell
cd ".\infra"
.\deploy.ps1 `
  -SubscriptionId "<subscription-id>" `
  -ResourceGroupName "rg-decisionduck" `
  -Location "westus2" `
  -FoundryEndpoint "https://<foundry-endpoint>/openai/v1" `
  -FoundryModel "phi-4"
```

The script handles container registry creation, image builds, Bicep deployment, and managed identity role assignment for the Foundry endpoint. After deployment, update `plugin.json` with the reported MCP endpoint URL.

Optional parameters:

- `-ContainerImage` to use a prebuilt image instead of building from source
- `-AcrName` to control the container registry name
- `-FoundryApiKey` to pass an API key instead of using managed identity

## Install the agent

1. Deploy the MCP server where Microsoft 365 Copilot can reach it
2. Update `plugin.json` with your MCP endpoint URL under `spec.url`
3. Update `manifest.json` with a real app GUID, valid domains, and icon assets
4. Package and deploy with Microsoft 365 Agents Toolkit
5. Install the app and run the declarative agent in Microsoft 365 Copilot

This path intentionally skips Microsoft 365 Copilot connectors. The plugin talks directly to your MCP endpoint.

## Example prompts

Try these in the Decision Duck agent:

- "Give me a second opinion on migrating our data warehouse to a lakehouse architecture"
- "Analyze the key risks if we switch identity providers this quarter"
- "Check this vendor selection analysis for cognitive biases"
- "Compare build vs. buy vs. partner for our payment processing integration"
- "What decision frameworks do you have for investment decisions?"

## Files in this project

| File | Purpose |
|------|---------|
| `agent-package/declarativeAgent.json` | Declarative agent manifest (schema v1.6) |
| `agent-package/plugin.json` | Plugin manifest with RemoteMCPServer runtime (schema v2.4) |
| `agent-package/manifest.json` | Microsoft 365 app manifest template |
| `mcp-server/Program.cs` | MCP endpoint implementation |
| `mcp-server/Dockerfile` | Container image definition |
| `infra/main.bicep` | Azure Container Apps deployment template |
| `infra/deploy.ps1` | Deployment helper script |

## When to use this agent

Use Decision Duck when you need structured decision support inside Microsoft 365 Copilot. It fits well for:

- High-impact choices where a second perspective reduces blind spots
- Risk-sensitive planning where structured analysis beats gut instinct
- Team decisions where bias detection helps surface hidden assumptions
- Option comparisons where side-by-side tradeoff analysis saves meeting time

## Resources

- [Decision Duck source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Decision%20Duck)
- [Declarative agents overview](https://learn.microsoft.com/microsoft-365-copilot/extensibility/overview-declarative-agent)
- [MCP specification](https://modelcontextprotocol.io/)
- [Azure Container Apps documentation](https://learn.microsoft.com/azure/container-apps/overview)
- [Azure AI Foundry documentation](https://learn.microsoft.com/azure/ai-studio/)
