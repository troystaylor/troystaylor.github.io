---
layout: post
title: "Agent-to-Agent (A2A) connector for Copilot Studio and Power Automate"
date: 2026-05-05 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Copilot Studio, MCP, A2A, Work IQ, Power Platform, Agent-to-Agent, Power Automate]
description: "Connect Copilot Studio agents and Power Automate flows to any A2A v1.0 agent using a dual-mode MCP connector. Pre-configured for Work IQ, with a reusable template for Salesforce Agentforce, Google Vertex, LangGraph, CrewAI, and other A2A agents."
---

Microsoft [announced the Work IQ API public preview](https://techcommunity.microsoft.com/blog/copilot-studio-blog/work-iq-api-public-preview-build-copilot-powered-agents-with-a2a/4516286) on April 30, giving developers programmatic access to the intelligence behind Microsoft 365 Copilot through the [Agent-to-Agent (A2A) protocol](https://a2a-protocol.org/latest/). Agents communicate as peers—delegating work, receiving grounded responses, and maintaining context across interactions. All scoped to the user's permissions and tenant compliance policies.

The announcement includes .NET, Rust, and Swift samples. Power Platform was missing from that list. I built two connectors to fill the gap:

- **Agent2Agent** — pre-configured for Work IQ, ready to deploy
- **Power A2A Template** — generic version for any A2A v1.0 agent

Both provide 10 REST operations for Power Automate and 6 MCP tools for Copilot Studio. Same operations, same architecture. The difference is configuration: Agent2Agent ships with Work IQ's OAuth settings and endpoint, while the template ships with placeholders you fill in for your target agent.

Full source: [Agent2Agent](https://github.com/troystaylor/SharingIsCaring/tree/main/Agent2Agent) | [Power A2A Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20A2A%20Template)

## Why a custom connector instead of native A2A

Copilot Studio has native A2A support, but it works as full delegation—your agent hands off the conversation to the remote agent and gets back a response. That covers simple scenarios. The custom connector approach unlocks four patterns that native A2A can't do:

| Scenario | Custom connector | Native A2A |
|----------|-----------------|------------|
| Power Automate flows (scheduled, event-driven) | Yes — only option | Not available |
| Inspect response before showing user | Yes — tool returns data to your agent | No — full delegation |
| Fan out to multiple agents | Yes — call each as a tool | No — one agent at a time |
| Simple delegation to one agent | Either works | Simpler setup |

The Power Automate row is the biggest differentiator. Native A2A lives inside Copilot Studio conversations. With the connector, you can schedule a Monday morning flow that asks Work IQ "summarize last week's key decisions and action items across my team" and posts the result to a Teams channel. No user conversation required.

## Operations

### REST operations (Power Automate and Power Apps)

| Operation | Purpose |
|-----------|---------|
| Send Message | Send a message and wait for the agent's completed response |
| Send Message (Async) | Send a message and return immediately with a task ID |
| Get Task | Poll task status, artifacts, and history by task ID |
| List Tasks | List tasks filtered by context ID, state, or pagination |
| Cancel Task | Cancel an in-progress task |
| Get Agent Card | Discover agent identity, skills, and capabilities |
| Create Push Notification Config | Configure webhook notifications for task updates |
| Get Push Notification Config | Retrieve a push notification config |
| List Push Notification Configs | List all push configs for a task |
| Delete Push Notification Config | Delete a push notification config |

### MCP tools (Copilot Studio)

| Tool | Purpose |
|------|---------|
| `send_message` | Sync delegation — send message, wait for response |
| `send_message_async` | Fire-and-forget — returns task ID for polling |
| `get_task` | Poll task status and retrieve artifacts |
| `list_tasks` | Filter tasks by context or state |
| `cancel_task` | Cancel an in-progress task |
| `get_agent_card` | Runtime discovery of agent capabilities |

## Multi-turn conversations

Pass the `contextId` from a previous response into the next Send Message call to maintain conversation state. The agent remembers prior context.

In Power Automate, use the **Context ID** output from Send Message as input to the next Send Message action. In Copilot Studio, the `send_message` tool accepts `context_id` — pass the value from the previous response.

## Architecture

```
Copilot Studio Agent / Power Automate Flow
    │
    │  MCP tools (6) / REST operations (10)
    ▼
Power Platform Connector (script.csx)
    │
    │  A2A v1.0 (JSON-RPC or HTTP+JSON)
    ▼
A2A Agent Endpoint
(Work IQ, Agentforce, Vertex, LangGraph, CrewAI)
```

The `script.csx` handles protocol translation between Power Platform's request format and A2A v1.0. It supports two protocol bindings:

- **JSON-RPC** (default) — used by Work IQ. All requests POST to a single endpoint with the method name inside the JSON-RPC body.
- **HTTP+JSON** — standard REST paths. Used by most other A2A agents.

## Work IQ setup

Work IQ requires a one-time tenant setup. Use the Agent2Agent connector for this path.

### Prerequisites

- Microsoft 365 Copilot license for each user
- Global admin or application admin to create the service principal and grant consent

### Step 1: Create the Work IQ service principal

Using [Graph Explorer](https://developer.microsoft.com/graph/graph-explorer) signed in as an admin:

1. Set method to **POST** and URL to `https://graph.microsoft.com/v1.0/servicePrincipals`
2. Consent to `Application.ReadWrite.All`
3. Request body:

```json
{ "appId": "fdcc1f02-fc51-4226-8753-f668596af7f7" }
```

4. Run query — 201 Created confirms success (conflict means it already exists, safe to proceed)

### Step 2: Create the app registration

1. Go to [Microsoft Entra admin center](https://entra.microsoft.com/) > App registrations > **New registration**
2. Set Supported account types to **Accounts in this organizational directory only**
3. Register, then copy the **Application (client) ID**
4. Authentication > Add a platform > Web > Add redirect URI: `https://global.consent.azure-apim.net/redirect`
5. API permissions > Add a permission > APIs my organization uses > search **Work IQ** > Delegated > `WorkIQAgent.Ask` > Add
6. Grant admin consent for your tenant
7. Copy your **Directory (tenant) ID**

### Step 3: Deploy

Edit `apiProperties.json` and replace `[[REPLACE_WITH_APP_ID]]` with your App ID, then deploy:

```powershell
paconn create -s "Agent2Agent" `
  --api-def apiDefinition.swagger.json `
  --api-prop apiProperties.json `
  --script script.csx
```

### Location metadata

Work IQ requires location metadata for time-sensitive queries ("today", "this week"). Include `timeZone` (IANA format, for example `America/Los_Angeles`) and `timeZoneOffset` (UTC offset in minutes, for example `-480` for PST) in your Send Message requests.

## Targeting other A2A agents

Use the Power A2A Template for connecting to non-Work IQ agents. Three configuration changes in `script.csx`:

```csharp
// 1. Your agent's endpoint URL
private const string A2A_ENDPOINT = "https://your-agent.example.com/a2a/";

// 2. Protocol binding: "jsonrpc" (Work IQ, default) or "httpjson" (REST)
private const string A2A_PROTOCOL_BINDING = "httpjson";

// 3. Optional: target specific agent on multi-agent gateways
private const string A2A_DEFAULT_AGENT_ID = "";
```

Then update `apiProperties.json` with the authentication your agent requires. The template ships with three options:

**OAuth 2.0** (default):

```json
"connectionParameters": {
  "token": {
    "type": "oauthSetting",
    "oAuthSettings": {
      "identityProvider": "aad",
      "clientId": "[[REPLACE_WITH_APP_ID]]",
      "scopes": "your-scope",
      "redirectMode": "Global",
      "redirectUrl": "https://global.consent.azure-apim.net/redirect"
    }
  }
}
```

**API Key**:

```json
"connectionParameters": {
  "apiKey": {
    "type": "securestring",
    "uiDefinition": {
      "displayName": "API Key",
      "description": "API key for the A2A agent",
      "tooltip": "Enter the API key provided by the agent",
      "constraints": { "required": "true" }
    }
  }
}
```

**No Auth**:

```json
"connectionParameters": {}
```

Deploy with the same CLI command:

```powershell
paconn create -s "Power A2A Template" `
  --api-def apiDefinition.swagger.json `
  --api-prop apiProperties.json `
  --script script.csx
```

## Example prompts

With the Work IQ connector, try these in a Copilot Studio agent or Power Automate flow:

- "What meetings do I have tomorrow that I need to prepare for?"
- "Summarize last week's key decisions and action items across my team"
- "What did the team decide about the migration timeline?"
- "Find recent emails about the Q3 budget review"
- "What's the status of the Zava partnership proposal?"

## Use cases

### Scheduled intelligence (Power Automate)

Every Monday morning, ask Work IQ "summarize last week's key decisions and action items across my team" and post the result to a Teams channel. No user conversation required.

### Event-driven routing (Power Automate)

When a support ticket escalates, send the ticket details to an A2A triage agent, parse the response, and route to the appropriate team.

### Selective tool use (Copilot Studio)

Your Copilot Studio agent calls `send_message` to ask Work IQ about a customer, inspects the response, combines it with CRM data, then presents a unified briefing — without handing off the entire conversation.

### Multi-agent fan-out (Copilot Studio)

Ask three different A2A agents the same question, compare their responses, and synthesize a combined answer. Each agent is a separate tool call.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Token audience mismatch | Verify `resourceUri` in apiProperties.json matches `api://workiq.svc.cloud.microsoft` |
| 403 Forbidden (no scope) | Missing Copilot license | Assign Microsoft 365 Copilot license, wait 15-30 min |
| 403 with scope error | Missing admin consent | Grant admin consent for `WorkIQAgent.Ask` |
| Empty responses | Index not built | Wait 15-30 min after license assignment |
| Method not found (-32601) | Missing A2A-Version header | Verify the setHeader policy in apiProperties.json sets `A2A-Version: 1.0` |

## Files in this project

### Agent2Agent (Work IQ)

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | Swagger with A2A operations and MCP tools |
| `apiProperties.json` | OAuth configuration for Work IQ |
| `script.csx` | A2A protocol translation and Application Insights telemetry |
| `readme.md` | Setup and usage guidance |

### Power A2A Template (any A2A agent)

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | Swagger with A2A operations and MCP tools |
| `apiProperties.json` | Pluggable auth configuration (OAuth, API Key, or none) |
| `script.csx` | A2A protocol translation with configurable endpoint and binding |
| `readme.md` | Setup and usage guidance |

## Resources

- [Agent2Agent connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Agent2Agent)
- [Power A2A Template source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20A2A%20Template)
- [Work IQ API public preview announcement](https://techcommunity.microsoft.com/blog/copilot-studio-blog/work-iq-api-public-preview-build-copilot-powered-agents-with-a2a/4516286)
- [A2A Protocol specification](https://a2a-protocol.org/latest/specification/)
- [Work IQ API overview](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/work-iq-api-overview)
- [Work IQ API quickstart](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/work-iq-api-quickstart)
- [Work IQ samples (C#, Rust, Swift)](https://github.com/microsoft/work-iq-samples)
- [Copilot Studio documentation](https://learn.microsoft.com/microsoft-copilot-studio/)
