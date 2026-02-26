---
layout: post
title: "PowerHoof: an AI agent that replaces MCP with Nushell"
date: 2026-02-26 09:00:00 -0500
categories: [Power Platform, Copilot Studio]
tags: [PowerHoof, Nushell, AI Agent, Azure, Foundry Local, MCP, Power Platform, Custom Connectors, Copilot Studio, Token Efficiency]
description: "PowerHoof is an AI agent that uses Nushell pipelines instead of MCP tool schemas, cutting token usage by 87%. Runs fully local with Foundry Local and Nushell, or scales to Azure with Container Apps, Cosmos DB, and Azure OpenAI."
---

MCP solves tool discovery, but it creates a new problem: schema bloat. Register 20 tools and you're sending 5,000+ tokens of JSON schema with every request before the LLM even starts thinking. Chain three tool calls together and you're looking at three separate LLM round-trips, three responses, and roughly 15,000 tokens for what should be a single operation. PowerHoof replaces that entire pattern with [Nushell](https://www.nushell.sh/) pipelines—structured data, composable commands, and drastically fewer tokens.

You can find the complete code in the [PowerHoof repository](https://github.com/troystaylor/PowerHoof).

## Why not MCP?

After building dozens of MCP connectors for Power Platform, the token overhead became hard to ignore. Every MCP request ships full JSON schemas for every registered tool. Each tool call is isolated—no shared context, no pipelining. Errors come back as JSON blobs that the LLM has to interpret.

Here's a concrete example. To list files and filter by date with MCP, you need three separate calls: one to list files, one to filter results, and one to sort. That's three LLM round-trips and roughly 15,000 tokens.

With Nushell, the same operation is a single pipeline:

```nushell
ls | where modified > (date now) - 7day | sort-by size
```

One call. One response. About 500 tokens total.

| Capability | MCP | Nushell |
|------------|-----|---------|
| Schema overhead | ~5,000 tokens | ~250 tokens |
| Multi-step operations | 3+ LLM round-trips | 1 pipeline |
| Error handling | JSON parsing | Native exceptions |
| Data format | Unstructured text | Typed tables and records |

Nushell works for agents because pipelines are composable—the LLM generates one command and the runtime handles data flow. Output comes back as tables and records, not strings to parse. Errors surface immediately with clear messages. And the same commands run on Windows, Linux, and macOS.

## Architecture

PowerHoof runs as a Node.js application—locally on your machine or deployed to Azure Container Apps. The architecture breaks into six layers:

```
Gateway (HTTP/WS) -> Orchestrator (Agent Loop) -> Conversation Manager (State)
       |                     |                           |
LLM Provider          Nushell Executor            Memory Store
```

- **Gateway** accepts REST and WebSocket connections
- **Orchestrator** runs the agent loop—prompt the LLM, validate the script, execute in Nushell, feed results back
- **Conversation Manager** tracks state across turns
- **Nushell Executor** runs scripts locally or in sandboxed Azure Container Apps Dynamic Sessions
- **Memory Store** persists conversation history to Cosmos DB or in-memory for local dev
- **LLM Provider** abstracts the model backend

### Nushell execution modes

The executor has three modes:

| Mode | What it does | When to use it |
|------|-------------|----------------|
| **Local** | Runs Nushell directly on your machine | Local development with real execution |
| **Session** | Runs in Azure Container Apps Dynamic Sessions with Hyper-V isolation | Production deployments |
| **Mock** | Returns canned responses | Unit testing and UI work |

For local development, install Nushell (`winget install nushell`) and set the executor type to `local`:

```json
{
  "nushell": {
    "executorType": "local"
  }
}
```

No Azure account needed. Nushell runs on your machine, Foundry Local runs the LLM on your machine, and in-memory storage handles conversation state. The entire agent stack works offline.

For production, switch to `session` and PowerHoof runs Nushell in Hyper-V-isolated containers with restricted network access and read-only filesystems.

### The orchestrator loop

The orchestrator is the core agent cycle. Here's what happens on each turn:

1. **User message arrives** — The gateway receives it via REST, WebSocket, or a channel adapter (Teams, Dataverse)
2. **Skill check** — The orchestrator checks if a registered skill matches the message (for example, `/weather Seattle`). If a skill matches, it runs directly without touching the LLM
3. **Build context** — The system prompt, Nushell command reference (~250 tokens), and conversation history are assembled within the 128K token budget
4. **LLM generates a response** — The response may contain plain text, or it may contain a fenced Nushell code block
5. **Nushell extraction** — If the response includes a fenced `nushell` code block, the orchestrator extracts the script
6. **Validation** — The validator checks the script for blocked commands and dangerous patterns
7. **Execution** — The validated script runs in the configured executor (local, session, or mock)
8. **Result injection** — Execution output feeds back into the conversation as a `[Nushell Result]` message
9. **Loop or respond** — The orchestrator calls the LLM again with the execution results (up to 5 iterations). When the LLM responds without a Nushell block, that's the final answer

The key insight: steps 5-9 happen within a single user turn. The LLM can chain multiple Nushell executions without any additional user input. A request like "list my Azure resources, find the most expensive ones, and save a summary" might loop three times internally—but from the user's perspective it's one message in, one response out.

### Script validation

Every LLM-generated Nushell script goes through the validator before execution. The validator enforces three categories of rules:

**Blocked commands** — These are completely rejected:

| Category | Commands |
|----------|----------|
| File operations | `rm`, `remove` |
| Process control | `kill` |
| Code execution | `exec`, `eval` |
| Network tools | `ssh`, `scp`, `curl`, `wget`, `nc` |
| Shell escapes | `bash`, `sh`, `cmd`, `powershell`, `pwsh` |
| Package managers | `cargo`, `npm`, `pip`, `apt`, `brew` |
| Elevation | `sudo` |

**Blocked patterns** — Regex rules catch dangerous constructs even when composed from allowed commands:
- Modifying environment variables (`$env.PATH =`)
- Backtick command substitution
- Subshell execution (`$(...)`)
- Direct writes to root paths
- Infinite loops (`loop { }`)

**Warnings** — These don't block execution but get flagged:
- Piping to HTTP endpoints
- File save operations
- Accessing the home directory
- Recursive glob patterns

The validator also enforces a maximum pipeline depth of 20 stages and a maximum script length of 100KB. Each script gets a safety classification: `safe`, `moderate` (has warnings), or `risky` (blocked). When validation fails, the agent receives the error and can explain it or try a different approach.

## LLM providers

PowerHoof supports four provider backends:

| Provider | Description | Use case |
|----------|-------------|----------|
| **Azure OpenAI** | Cloud-hosted GPT-4o, o1 | Production deployments |
| **Foundry Local** | On-device inference (phi-4-mini, phi-3.5-mini) | Local dev, offline, privacy-sensitive |
| **Foundry Local + NPU** | NPU-accelerated inference for Copilot+ PCs | Low-power, background AI |
| **Mock** | Canned responses | Unit testing |

Foundry Local is the interesting one for development. Install it with `winget install Microsoft.AI.Foundry.Local`, and PowerHoof automatically downloads models on first use (~2GB for phi-3.5-mini). No cloud dependency, no API keys, no cost.

For Copilot+ PCs with NPUs, Foundry Local can offload inference to the neural processing unit at roughly 5-10W instead of 65W+ for GPU. That means the agent runs in the background while you work without draining your battery.

```json
{
  "providers": {
    "local": {
      "type": "foundry-local",
      "modelAlias": "phi-4-mini"
    }
  }
}
```

## Power Platform integration

PowerHoof connects to Power Platform through three channels:

### Custom connector

PowerHoof exposes an OpenAPI spec at `/openapi.json`. Import it directly into Power Platform as a custom connector:

1. Go to **make.powerapps.com** > **Custom connectors** > **New**
2. Import from URL: `https://your-api.azurecontainerapps.io/openapi.json`
3. Configure OAuth with your Azure AD app registration

The connector supports OAuth 2.0 Dynamic Discovery (RFC 8414), so Copilot Studio can auto-configure authentication. Point it at the `/.well-known/oauth-authorization-server` endpoint and it discovers the authorization and token endpoints automatically.

### Dataverse channel

For tighter Power Platform integration, enable the Dataverse channel adapter. PowerHoof polls Dataverse tables for incoming messages and writes responses back:

```json
{
  "channels": {
    "dataverse": {
      "enabled": true,
      "dmPolicy": "open",
      "environmentUrl": "https://yourorg.crm.dynamics.com",
      "messageTable": "powerhoof_messages",
      "responseTable": "powerhoof_responses"
    }
  }
}
```

Power Apps and Power Automate flows write to the message table. PowerHoof picks them up, processes them through the agent loop, and writes responses back. No HTTP calls from the client side—just Dataverse reads and writes.

### Microsoft Graph channel

Enable the Graph adapter to receive messages from Teams and Outlook:

```json
{
  "channels": {
    "graph": {
      "enabled": true,
      "dmPolicy": "pairing",
      "subscriptions": ["teams-messages", "outlook-mail"]
    }
  }
}
```

When `dmPolicy` is set to `pairing`, new senders go through a verification flow before the agent accepts their messages:

1. **Unknown sender** messages the agent through Teams or Outlook
2. **Agent responds** with a 6-digit pairing code: "I don't recognize you yet. To start chatting, verify with this code: **123456**"
3. **Sender confirms** the code through a trusted channel—the PowerHoof dashboard or admin approval
4. **Agent approves** the sender. All future messages from that sender flow through without pairing

Codes expire after 15 minutes. Each sender can have up to 3 pending requests. Admins can approve or reject senders directly, revoke existing approvals, and view all pending requests. Expired codes clean up automatically.

This matters because exposing an AI agent through Teams means anyone in the tenant (or external federated users) can interact with it. The pairing flow adds a trust layer without requiring Azure AD group membership—useful when you want to onboard users gradually.

## Custom Nushell commands

PowerHoof ships with five custom commands that extend Nushell for agent tasks:

| Command | Purpose | Example |
|---------|---------|---------|
| `ph web` | HTTP requests with auto-parsing | `ph web get "https://api.example.com/users" \| from json \| select name email` |
| `ph file` | Safe file operations in sandbox | `ph file read data.json \| from json \| where status == "active"` |
| `ph azure` | Azure CLI wrapper | `ph azure resource list --resource-group myRG` |
| `ph memo` | Persistent memory | `ph memo save "user_preference" "prefers dark mode"` |
| `ph ask` | Sub-agent queries | `ph ask "What's the current weather in Seattle?"` |

The LLM composes these into pipelines. A request like "find my most expensive Azure resources and save a summary" becomes:

```nushell
ph azure resource list --resource-group myRG | sort-by cost --reverse | first 10 | ph memo save "expensive_resources"
```

One pipeline, one LLM turn.

## Skills platform

Skills are pluggable capabilities loaded from a `skills/` directory. PowerHoof watches the directory for changes during development, so you can add skills without restarting the server.

Two built-in skills ship with the project:

**Weather** (`/weather Seattle`) — Current conditions, 3-day forecast, UV index, and air quality using structured Nushell output.

**Translate** (`/tr hello to Spanish`) — Offline phrase translation across common languages. No API needed.

### Write a custom skill

Skills implement a four-method interface:

```typescript
interface Skill {
  manifest: SkillManifest;       // ID, name, description, version, permissions
  initialize?(): Promise<void>;   // Optional setup
  canHandle(ctx: SkillContext): Promise<boolean>;  // Does this skill match?
  execute(ctx: SkillContext): Promise<SkillResult>; // Run the skill
  shutdown?(): Promise<void>;     // Optional cleanup
}
```

A minimal skill that responds to `/ping`:

```typescript
export default {
  manifest: {
    id: "ping",
    name: "Ping",
    description: "Responds with pong",
    version: "1.0.0",
    examples: ["/ping"],
  },
  async canHandle(ctx) {
    return ctx.message.content.trim().toLowerCase().startsWith("/ping");
  },
  async execute(ctx) {
    return { success: true, content: "Pong!" };
  },
};
```

Drop that file in the `skills/` directory and PowerHoof loads it automatically. During development, the skill loader watches for file changes—no server restart needed.

Skills can request permissions (`execute-shell`, `network`, `secrets`, `files`) and access the Nushell executor directly through the `SkillContext`. They can also delegate to other skills or fall through to the LLM if they can't fully handle a request. The `nextAction` field in the skill result controls this: `respond` (default), `delegate` (hand off to another skill), `escalate` (flag for human), `fallthrough` (let the LLM handle it), or `silent` (no response).

## Conversation memory

PowerHoof stores three types of data: conversations, memos, and user preferences.

**Conversations** are the message history for each session. The conversation manager tracks every user message, assistant response, and Nushell execution result with token counts and timestamps. When building context for the LLM, the manager works backward from the most recent messages and includes as many as fit within the 128K token budget. Older messages that don't fit are dropped from context—they're still persisted, just not sent to the LLM.

**Memos** are key-value facts stored through the `ph memo` / `ph remember` commands. When a user says "remember that my project deadline is March 15th," the agent runs `ph remember 'project-deadline' '2026-03-15'` and stores it in the memo table. Later, `ph recall 'project-deadline'` retrieves it. Memos survive across conversations—they're per-user, not per-session.

**User preferences** are structured settings that skills and the orchestrator can read—things like preferred output format, timezone, or language.

For local development, all three use in-memory Maps. For production, Cosmos DB handles persistence with Managed Identity authentication (no connection strings in config). Each data type gets its own container, partitioned by user ID.

The `compactionMode: "safeguard"` setting in the agent config enables reasoning mode on the LLM. The model's reasoning output preserves key context even when conversation history exceeds the token window—the model reasons about what's important before generating a response.

## Token efficiency

PowerHoof tracks token usage and compares it against estimated MCP equivalents. In testing, a 50-request session used about 35,000 tokens—an 87% reduction compared to the same operations through MCP tooling. That translates directly to lower API costs and faster response times.

The savings come from three places: no schema overhead per request, pipeline composition instead of multi-turn tool chaining, and structured data that doesn't need LLM interpretation.

### Where the overhead lives

The token tracker breaks it down by category. MCP defines tool schemas for filesystem operations (read, write, list, search, info), web requests, database CRUD, memory operations, and Azure resource management. Each schema adds 120-400 tokens of JSON. Across all categories, that's roughly 4,690 tokens of tool definitions sent with every request.

PowerHoof's Nushell command reference covers the same capabilities in about 250 tokens—a one-line usage string and description per command instead of a full JSON Schema.

### Second example: Azure cost analysis

A user asks "What did my Azure resources cost last month, grouped by resource group?"

**MCP approach** (3 tool calls):
1. Call `list_resources` tool — LLM processes result — ~5,690 tokens (4,690 schema + 1,000 response)
2. Call `get_costs` tool — LLM processes result — ~5,690 tokens
3. Call `store_memo` tool with summary — ~4,890 tokens
4. Total: **~16,270 tokens**, 3 LLM round-trips

**PowerHoof approach** (1 pipeline):

```nushell
ph azure costs --days 30
  | group-by resource_group
  | each { |g| { group: $g.group, total: ($g.items | get cost | math sum) } }
  | sort-by total --reverse
```

One LLM call generates the pipeline. One execution returns the grouped, sorted result. The LLM summarizes it in natural language. Total: **~1,500 tokens**, 2 LLM calls (generate + summarize). That's a 91% reduction for this specific operation.

## Security

Multiple layers protect the execution pipeline:

| Layer | What it does |
|-------|-------------|
| **OAuth 2.0 / Azure AD** | Enterprise SSO with Microsoft Entra ID |
| **Script validation** | All LLM-generated Nushell scripts validated before execution |
| **Hyper-V isolation** | Production: Nushell runs in Azure Container Apps Dynamic Sessions |
| **Network restrictions** | Production: limited outbound network access from sandbox |
| **Read-only filesystem** | Production: sandbox filesystem is read-only |
| **Execution timeout** | Scripts killed after configurable timeout |
| **DM pairing** | Untrusted senders verify with a 6-digit code |
| **Key Vault** | Secrets stored in Azure Key Vault, resolved at runtime |
| **Managed Identity** | No secrets in code or config files |

## Getting started

### Run fully local (no cloud required)

Install Nushell and Foundry Local, then start the agent:

```bash
winget install nushell
winget install Microsoft.AI.Foundry.Local

git clone https://github.com/troystaylor/PowerHoof.git
cd PowerHoof
npm install
npm run build
cp config.foundry-local.json config.dev.json
npm start
```

Foundry Local downloads models automatically on first use (~2GB for phi-3.5-mini). Nushell runs locally, the LLM runs locally, and conversation state stays in memory. No Azure account, no API keys, no cost.

For Copilot+ PCs, Foundry Local offloads inference to the NPU at roughly 5-10W—the agent runs in the background without draining your battery.

### Mock mode (no AI, no Nushell)

```bash
git clone https://github.com/troystaylor/PowerHoof.git
cd PowerHoof
npm install
npm run build
npm start
```

Mock mode uses canned LLM responses and skips Nushell execution—useful for UI and integration work.

### Deploy to Azure

The quickest path uses the included PowerShell script:

```powershell
./deploy-azure.ps1 -ResourceGroup powerhoof-rg -Location eastus2 -CreateOpenAI
```

This creates an Azure Container Registry, builds and pushes the Docker image, deploys a GPT-4o model, creates a Container Apps environment, and deploys the app with all environment variables configured.

For infrastructure-as-code, use the Azure Developer CLI:

```bash
azd auth login
azd up
```

The `azure.yaml` and Bicep templates handle the full infrastructure: Container Apps, Cosmos DB, Azure OpenAI, Key Vault, and Dynamic Sessions pool.

## What's next

PowerHoof is at v0.11.0. The channel adapters, skills platform, and Nushell execution pipeline are functional. The areas that need work are expanding the built-in skill library, adding more channel adapters, and improving the script validator. Contributions are welcome—check the [repository](https://github.com/troystaylor/PowerHoof) for open issues.
