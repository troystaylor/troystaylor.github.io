---
layout: post
title: "Call a Copilot Studio agent from Power Automate, including GitHub Copilot harness agents"
date: 2026-09-14 12:30:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Copilot Studio, Custom Connectors, MCP, Power Automate, Agentic Runtime, Server-Sent Events, Power Platform API, Entra ID]
description: "Copilot Studio Agent Runtime is a custom connector that runs a turn against a published Copilot Studio agent, buffers the server-sent event stream, and returns one finished answer to a flow or a calling agent."
---

Power Automate can't consume a stream. The Copilot Studio agentic runtime only speaks one, and the supported Copilot Studio client library doesn't cover agents built on the GitHub Copilot harness at all.

[Copilot Studio Agent Runtime](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Agent%20Runtime) closes that gap. The connector opens a conversation with a published agent, reads the entire server-sent event stream, consolidates it, and returns one completed JSON answer. A flow gets a finished reply. A Copilot Studio agent gets a Model Context Protocol (MCP) tool it can call to delegate work to another agent.

## A data plane connector, not another control plane one

The other Copilot Studio connectors in the repository manage agents. This one runs them.

| Connector | Plane | What it does |
|---|---|---|
| [Copilot Studio Bots](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Bots) | Control | Evaluate, quarantine, inventory, migrate identity |
| [Copilot Studio Analytics](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Analytics) | Reporting | Read transcripts and session records after the fact |
| **Copilot Studio Agent Runtime** | **Data** | **Open a conversation and get an answer** |

The two pair well. `List Agents` in Copilot Studio Bots returns `schemaName` and `isCLIAgent`, which tell you which agent to call here and whether it runs on the GitHub Copilot harness.

## The endpoint is undocumented

```text
POST https://{environment-host}/copilotstudio/agenticruntime/3p/dataverse-backed/
     authenticated/bots/{schemaName}/conversations?api-version=1

POST https://{environment-host}/copilotstudio/agenticruntime/3p/dataverse-backed/
     authenticated/bots/{schemaName}/conversations/{conversationId}?api-version=1
```

This route doesn't appear on Microsoft Learn and carries no compatibility guarantee. Microsoft's position today is that the Copilot Studio client library "can only be used with agents created by using the standard harness," and that "agents using the GitHub Copilot harness aren't yet officially supported." The `/3p` agentic runtime route is how Microsoft's own experimental Copilot Studio plugin reaches those agents.

Treat it as experimental and keep a fallback.

The `agenticruntime` prefix and the `3p` third-party segment separate this from the classic Direct-to-Engine route at `/copilotstudio/dataverse-backed/` with `api-version=2022-03-01-preview`, which [Power Agent Desktop](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Agent%20Desktop) and [Power Agent Tray](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Agent%20Tray) use.

## What the agent and app registration need

The agent must be published, because draft agents don't resolve. It must use **Authenticate with Microsoft**, which is what the `/authenticated/` path segment means. And it must be shared with the signed-in user, or the call returns `403`.

The app registration needs the **Power Platform API** delegated permission `CopilotStudio.Copilots.Invoke` with admin consent granted, plus a web redirect URI matching the connector's generated consent URL.

Sign-in is delegated only. The `/authenticated/` route rejects app-only client credential tokens and answers with `S2SDirectEngineRequiresNoAuthentication`. Service-to-service Direct-to-Engine exists, but it's a private preview and applies only to **No Authentication** agents. Every connection here is a user sign-in.

## Derive the environment host

The connector reads the host from the connection rather than hardcoding it. Take your environment GUID, strip the hyphens, and split after the 30th character:

```powershell
$environmentId = "0a1b2c3d-4e5f-6071-8293-a4b5c6d7e809"
$id = $environmentId.Replace("-", "").ToLower()
"$($id.Substring(0, 30)).$($id.Substring(30)).environment.api.powerplatform.com"

# 0a1b2c3d4e5f60718293a4b5c6d7e8.09.environment.api.powerplatform.com
```

Enter the hostname only, with no `https://` and no trailing slash. Non-production clouds use `api.test.`, `api.preprod.`, or `api.dev.` suffixes and work the same way. Sovereign clouds aren't verified — the agentic runtime may not be deployed there.

The schema name looks like `cr1a2_myAgent`. Read it from the agent's **Settings** page, from the direct connection URL in channel settings, or from `List Agents` in Copilot Studio Bots.

## Four REST actions, three MCP tools

| Operation | Description |
|-----------|-------------|
| **Ask Agent** | Opens a conversation, sends a message, returns the finished answer |
| **Start Conversation** | Opens a conversation and returns its ID plus any greeting |
| **Send Message** | Sends a turn to an existing conversation and returns the finished reply |
| **Invoke Copilot Studio Agent Runtime MCP** | The JSON-RPC endpoint — it shows in the action list, but skip it in a flow |

Use **Ask Agent** for stateless work. Use **Start Conversation** followed by **Send Message** when the agent needs to remember earlier turns. Both message operations accept an optional BCP 47 locale such as `en-GB`.

The MCP tools mirror the same three operations:

| Tool | Arguments |
|------|-----------|
| `ask_agent` | `schemaName`\*, `text`\*, `locale` |
| `start_conversation` | `schemaName`\*, `emitStartConversationEvent` |
| `send_message` | `schemaName`\*, `conversationId`\*, `text`\*, `locale` |

\* required

`emitStartConversationEvent` defaults to `true`. Set it to `false` to suppress the greeting.

This is what makes agent-to-agent invocation work. A Copilot Studio agent can call a GitHub Copilot harness agent as a tool, which no supported channel currently offers.

## Consolidating the stream takes two rules

The runtime replies with `text/event-stream`. Power Platform can't surface a stream to a flow, so the connector reads the whole thing and consolidates it.

Naive concatenation breaks, because the runtime streams in two shapes depending on the agent and client:

| Shape | What arrives | How it's handled |
|---|---|---|
| **Cumulative** | Each `typing` activity repeats everything so far | Keep only the last one |
| **Delta** | Each `typing` activity carries a new fragment | Concatenate in order |
| **Final** | A `message` activity with `streamType: "final"` | Authoritative — wins over both |

The connector detects the shape by testing whether each chunk begins with the previous one. Guessing wrong is visible in the output either way: treating cumulative text as deltas repeats the answer several times over, and treating deltas as cumulative truncates it to the last fragment.

The response keeps both the consolidated text and the raw activities:

```json
{
  "conversationId": "abc123",
  "text": "Paris is the capital of France.",
  "isComplete": true,
  "activityCount": 4,
  "attachments": [],
  "suggestedActions": [ { "type": "imBack", "title": "Tell me more", "value": "more" } ],
  "citations": [ { "@type": "Claim", "position": 1, "appearance": { "name": "France", "url": "https://example.com" } } ],
  "activities": [ "..." ]
}
```

Read `text` in almost every flow. Check `isComplete` when correctness matters — `false` means the runtime never signaled turn completion, so `text` is partial. `activityCount` covers this turn only, not the whole conversation. **Ask Agent** also returns `greetingActivities` separately, so the agent's opening line never pollutes `text`.

## Send a raw activity to trigger a topic

**Send Message** exposes a **Raw Activity** field for anything that isn't a plain user message. An `event` or `invoke` activity can trigger a topic directly:

```json
{
  "activity": {
    "type": "event",
    "name": "StartOrderLookup",
    "value": { "orderId": "SO-4417" }
  }
}
```

**Message** is ignored when **Raw Activity** is present. The connector always overwrites the `conversation` property with the conversation in the request path, so a caller can't post into a conversation it doesn't own.

## Errors name the thing to check

The runtime returns bare status codes for common misconfigurations, so the connector translates each one:

```json
{
  "status": 403,
  "message": "Forbidden. Share the agent with the signed-in user, and confirm admin consent was granted for CopilotStudio.Copilots.Invoke. This endpoint rejects app-only (service principal) tokens: the connection must be a delegated user sign-in.",
  "details": "<raw response body from the runtime>"
}
```

| Status | Meaning |
|---|---|
| `400` | Missing `schemaName`, `conversationId`, or message text — raised before any call is made |
| `401` | Wrong token audience, or the app registration is missing `CopilotStudio.Copilots.Invoke` |
| `403` | Agent not shared, admin consent not granted, or an app-only token was used |
| `404` | Wrong host or schema name, agent not published, or not served by the agentic runtime |
| `408` / `504` | The turn didn't finish in time |
| `429` | Throttled — retry after a delay |

MCP callers get the same payload as the tool result with `isError: true`, so the calling agent reads the explanation instead of seeing an opaque failure.

When a call fails, confirm each layer in order. It isolates the problem faster than reading the error alone:

1. **Host** — does it match the `{30}.{2}` split of your environment GUID? A wrong host gives `404`, not a connection error.
2. **Schema name** — copy it from `List Agents` exactly. It's case-sensitive.
3. **Published** — republish if in doubt. A draft-only agent gives `404`.
4. **Sharing** — confirm the signed-in user is on the agent's share list.
5. **Permission** — check `CopilotStudio.Copilots.Invoke` has admin consent.

A `401` is almost always the app registration rather than the agent.

## Know the limits before you build on it

**Turn length is the hard one.** Power Platform cuts a connector request off at roughly 120 seconds. Agentic loop turns routinely run longer, and this endpoint has no polling or resume route, so a long turn is simply lost. Keep prompts tightly scoped and don't build deep research tasks on it.

The rest:

- **No streaming to the caller.** The answer arrives all at once when the turn completes. Progressive rendering isn't possible through a custom connector.
- **Delegated identity only.** Every call runs as the signed-in user. There's no unattended option.
- **Unversioned in practice.** `api-version=1` is pinned because it's what the route accepts today.
- **Cost.** Agents on the GitHub Copilot harness bill 100–500+ Copilot Credits per task regardless of Microsoft 365 Copilot licensing. Calling one in a loop from a flow gets expensive fast. Check the harness with `List Agents` before wiring an agent into automation.

## Deploy the connector

```powershell
pac auth create --environment <environment-id>

pac connector create `
    --api-definition-file apiDefinition.swagger.json `
    --api-properties-file apiProperties.json `
    --script-file script.csx
```

Replace `[YOUR_CLIENT_ID]` in `apiProperties.json` with your app registration's client ID and set the client secret in the portal **Security** tab. Then read back the generated redirect URL and register it:

```powershell
pac connector download --connector-id <id> --outputDirectory ./verify
# properties.connectionParameters.token.oAuthSettings.redirectUrl

az ad app update --id <appId> --web-redirect-uris `
    "https://global.consent.azure-apim.net/redirect" "<per-connector-url>"
```

Each environment generates a different redirect URL. Consent fails if only the generic one is registered.

Validate before deploying:

```powershell
npx ppcv "./Copilot Studio Agent Runtime"
```

Finally, create a connection and supply the environment host derived above.

## Three ways to use it

### Ask an agent from a flow

Use **Ask Agent** when each call is independent.

| Field | Value |
|---|---|
| Agent Schema Name | `cr1a2_contractReviewer` |
| Message | `Summarize the risks in contract @{triggerBody()?['contractId']}` |

Read `text` from the output. You don't need to touch `activities`.

### Hold a multi-turn conversation

When later turns depend on earlier ones, keep the conversation open:

1. **Start Conversation**, then store `conversationId` in a variable.
2. **Send Message** with that `conversationId`, then read `text`.
3. Repeat step 2 for each follow-up. The agent retains context across turns.

Don't call **Ask Agent** in a loop for this. Each call opens a fresh conversation and the agent forgets everything.

### Let one agent call another

This is the scenario the MCP endpoint exists for, and the only way to reach a GitHub Copilot harness agent as a tool:

1. In Copilot Studio, open the calling agent and go to **Tools** > **Add a tool** > **Model Context Protocol**.
2. Select this connector and create or pick a connection.
3. Add `ask_agent` for one-shot delegation.
4. In the calling agent's instructions, say when to delegate and which `schemaName` to pass. The model won't know the schema name otherwise:

   > When the user asks a contract question, call `ask_agent` with `schemaName` set to `cr1a2_contractReviewer` and the user's question as `text`.

Add `start_conversation` and `send_message` only when the calling agent genuinely needs a multi-turn side conversation. For most delegation, `ask_agent` alone produces better behavior.

## Resources

- [Copilot Studio Agent Runtime source](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Agent%20Runtime)
- [Copilot Studio Bots connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Bots)
- [Copilot Studio client library](https://learn.microsoft.com/microsoft-copilot-studio/publication-connect-bot-to-custom-application)
- [Write code in a custom connector](https://learn.microsoft.com/connectors/custom-connectors/write-code)
- [Copilot Studio Bots v1.2 post](/power%20platform/custom%20connectors/mcp/2026-09-09-copilot-studio-bots-v1-2-channel-manifest.html)
