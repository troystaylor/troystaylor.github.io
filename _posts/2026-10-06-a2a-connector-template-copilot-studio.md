---
layout: post
title: "Add Entra ID and PKCE sign-in to Copilot Studio A2A agents"
date: 2026-10-06 15:30:00 -0400
categories: [Power Platform, Custom Connectors]
tags: [A2A, Agent-to-Agent, Copilot Studio, Custom Connectors, Microsoft Entra ID, PKCE, OAuth, PAC CLI, Work IQ]
description: "A script-free custom connector template that adds an external Agent2Agent (A2A) agent to Copilot Studio under Agents, with Microsoft Entra ID, OAuth 2.0 with PKCE, API key, or no authentication, deployed with PAC CLI."
---

Copilot Studio can [connect to an agent over the Agent2Agent (A2A) protocol](https://learn.microsoft.com/microsoft-copilot-studio/add-agent-agent-to-agent) from **Agents → Add agent → A2A agent**. That built-in option offers three authentication choices: **None**, **API key**, and **OAuth 2.0**. If the agent sits behind Microsoft Entra ID, or its authorization server requires PKCE, you're stuck.

The [A2A Connector Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/A2A%20Connector%20Template) fills that gap. It's a two-file custom connector with no `script.csx` that you deploy with PAC CLI. Once deployed, it shows up in the same **Add agent** list as the built-in options, and Copilot Studio treats it as a native A2A agent.

## When to use the template

Use the built-in **A2A agent** option when it covers your agent. It's simpler. Use the template when you need any of these:

| Need | Built-in A2A agent | Template |
|---|---|---|
| No authentication or an API key | Yes | Yes |
| OAuth 2.0 authorization code with a client secret | Yes | Yes |
| Microsoft Entra ID sign-in | No | Yes |
| OAuth 2.0 with PKCE (`S256`) | No | Yes |
| An agent card that requires a token to read | No | Yes |
| A definition in source control, deployed to several environments | No | Yes |

The last row matters more than it looks. The built-in option creates a connector for you in one environment. The template gives you a definition you can review, commit, and deploy to dev, test, and production with the same commands.

## How this differs from the Power A2A Template

In May we published the [Agent-to-Agent connector and Power A2A Template](/power%20platform/custom%20connectors/2026-05-05-agent-to-agent-a2a-connector-work-iq.html). That pair wraps A2A as Model Context Protocol (MCP) tools and REST actions through a `script.csx`. Your Copilot Studio agent calls them as tools, and Power Automate calls them as actions.

This template takes the other path. It has no script and no tools. Copilot Studio adds the external agent as an agent, sends it A2A requests directly, and the orchestrator delegates to it like any other connected agent. Pick the Power A2A Template when you need Power Automate or want to inspect the response as tool output. Pick this one when you want the external agent to behave like a native Copilot Studio agent.

## One operation, marked as A2A

The whole connector is one operation:

```json
"paths": {
  "/your-a2a-endpoint": {
    "post": {
      "operationId": "InvokeA2A",
      "summary": "Your A2A Agent",
      "description": "Describe what the agent does and which requests it should handle.",
      "x-ms-agentic-protocol": "a2a-1.0",
      "x-ms-a2a-card-endpoint": "https://your-agent.example.com/your-a2a-endpoint/.well-known/agent-card.json",
      "x-ms-a2a-card-json": "null",
      "responses": {
        "default": { "description": "default", "schema": {} }
      }
    }
  }
}
```

`x-ms-agentic-protocol: a2a-1.0` is what puts the connector in the **Add agent** list. Copilot Studio sends every A2A request to this operation.

The operation path is the agent's message endpoint, the `url` in its agent card. It isn't the agent card URL. The Microsoft Learn article makes the same point for the built-in option.

Microsoft doesn't document these `x-ms-a2a-*` fields. They match what Copilot Studio generates when you add an A2A agent in the portal, which is how the template was built.

## Five authentication options

Each option has its own `apiProperties.json` in the `auth` folder. Copy the one you need over `apiProperties.json`, then paste the matching `securityDefinitions` block into the API definition.

| Option | Identity provider | Use when | Status |
|---|---|---|---|
| None | — | The agent doesn't require authentication | Deploys |
| API key | — | The agent takes a key in a header or query parameter | Deploys |
| OAuth 2.0 | `oauth2` | Authorization code with a client secret | Deploys |
| Microsoft Entra ID | `aad` | The agent's API is protected by Entra ID | Tested end to end |
| OAuth 2.0 with PKCE | `oauth2pkcewithdcr` | The authorization server requires PKCE `S256` | Deploys |

**Deploys** means Power Platform accepts the connector and Copilot Studio lists it. Test sign-in and a real call before you rely on it.

The PKCE option uses `oauth2pkcewithdcr`, the same hidden identity provider covered in the [MCP public-client PKCE post](/power%20platform/custom%20connectors/mcp/2026-09-04-mcp-public-client-pkce-connector.html). It sends PKCE on sign-in, but it sends the client secret only on token refresh. Validate both sign-in and refresh against your authorization server before production.

The Entra ID option follows the standard [Entra ID pattern for custom connectors](https://learn.microsoft.com/connectors/custom-connectors/azure-active-directory-authentication): an app registration with a client secret, a delegated permission on the agent's API, and admin consent. You set the API's Application ID URI and scope in `apiProperties.json`:

```json
"oAuthSettings": {
  "identityProvider": "aad",
  "clientId": "[YOUR_CLIENT_ID]",
  "scopes": [ "[YOUR_RESOURCE_URI]/[YOUR_SCOPE]" ],
  "properties": {
    "IsFirstParty": "False",
    "AzureActiveDirectoryResourceId": "[YOUR_RESOURCE_URI]"
  },
  "customParameters": {
    "resourceUri": { "value": "[YOUR_RESOURCE_URI]" },
    "loginUri": { "value": "https://login.microsoftonline.com" },
    "loginUriAAD": { "value": "https://login.microsoftonline.com" }
  }
}
```

## Point the connector at your agent

`Set-A2AAgentCard.ps1` reads the agent card and rewrites the API definition. It sets `host` and the operation path from the card's endpoint and records the card URL in `x-ms-a2a-card-endpoint`.

```powershell
# Card is public
.\Set-A2AAgentCard.ps1 -CardUrl 'https://agent.example.com/a2a/.well-known/agent-card.json'

# Card requires a token
.\Set-A2AAgentCard.ps1 -CardUrl $cardUrl -BearerToken $token

# No card; you know the endpoint
.\Set-A2AAgentCard.ps1 -Endpoint 'https://agent.example.com/a2a'
```

The script handles both card shapes. It reads the top-level `url` from A2A 0.3 cards, and the first JSON-RPC entry in `supportedInterfaces` from A2A 1.0 cards. It rejects endpoints that aren't HTTPS and warns when it drops a query string.

Add `-EmbedCard` to store the card in `x-ms-a2a-card-json`. Copilot Studio takes the agent's name and description from the connector either way, so embedding is optional. Re-run the script when the card changes.

## Write the description for the orchestrator

When you add the agent, Copilot Studio copies two values from the connector:

| Field | Becomes |
|---|---|
| `info.title` | The agent's name |
| The operation's `description` | The agent's description |

The orchestrator reads the description to decide when to delegate. Say what the agent does and which requests it should handle, for example: "Answers questions about the signed-in user's email, meetings, and files." The Learn article links to [guidance on writing effective metadata](https://learn.microsoft.com/microsoft-copilot-studio/advanced-generative-actions#best-practices), and it applies here.

Copilot Studio copies these values once. Updating the connector later won't change an agent you've already added. Edit the description on the agent's **Agents** page instead.

## Deploy with PAC CLI

Create the connector with [`pac connector create`](https://learn.microsoft.com/power-platform/developer/cli/reference/connector). Don't pass `--script-file`.

```powershell
pac connector create `
    --environment <YOUR_ENVIRONMENT_ID> `
    --api-definition-file .\apiDefinition.swagger.json `
    --api-properties-file .\apiProperties.json
```

For OAuth options, Power Platform generates a redirect URL that's unique to this connector in this environment. Download the deployed connector to read it, then register it with your authorization server:

```powershell
pac connector download `
    --environment <YOUR_ENVIRONMENT_ID> `
    --connector-id <CONNECTOR_ID> `
    --outputDirectory .\deployed

(Get-Content .\deployed\apiProperties.json -Raw | ConvertFrom-Json).
    properties.connectionParameters.token.oAuthSettings.redirectUrl
```

Register each environment's URL separately.

The client secret never touches your working folder. The readme writes it to a temporary copy of `apiProperties.json`, runs `pac connector update` against that copy, and deletes it. That keeps the folder safe to commit. For more on swapping identity providers this way, see [Update custom connector OAuth identity providers with PAC CLI](/power%20platform/custom%20connectors/2026-08-07-update-custom-connector-oauth-identity-providers-pac-cli.html).

## Add the agent in Copilot Studio

Open your agent, go to **Agents → Add agent**, and select your connector by its `info.title`. Don't select **A2A agent**, which creates a separate connector. Create a connection, sign in, and select **Add and configure**.

In the agent's YAML, the result is an `AgentToAgentTool`:

```yaml
kind: AgentToAgentTool
connectionReference: <your-agent-schema-name>.cr.<connection-reference>
connectorId: /providers/Microsoft.PowerApps/apis/<your-connector-api-name>
operationId: InvokeA2A
```

Because A2A connections run on the custom connector infrastructure, Learn notes you can also reach agents running on-premises or inside a virtual network.

When you test, ask for the task instead of naming the agent. "What meetings do I have today?" routes better than "Use My Agent to check my meetings." Copilot Studio forwards your words to the external agent, and that agent doesn't know the name you gave it. If the first question right after you add the agent isn't routed, wait a minute and ask again.

## Example: Work IQ

[Work IQ](https://learn.microsoft.com/microsoft-365/copilot/extensibility/work-iq/a2a/quickstart) is the end-to-end tested case. It's a Microsoft 365 A2A agent behind Entra ID, and its card requires a token.

| Setting | Value |
|---|---|
| Authentication option | Microsoft Entra ID |
| Endpoint | `https://workiq.svc.cloud.microsoft/a2a` |
| `[YOUR_RESOURCE_URI]` | `api://workiq.svc.cloud.microsoft` |
| `[YOUR_SCOPE]` | `WorkIQAgent.Ask` |
| App registration permission | **Work IQ** (under **APIs my organization uses**), delegated **WorkIQAgent.Ask**, with admin consent |

Since the card needs a token, run the script with `-Endpoint 'https://workiq.svc.cloud.microsoft/a2a'`, or pass `-CardUrl` with a `-BearerToken`. Your tenant must be [enabled for Work IQ](https://learn.microsoft.com/microsoft-365/copilot/extensibility/work-iq/enable-work-iq).

Work IQ also shows why protocol version matters. Copilot Studio's documented payload uses the A2A 0.3 `message/send` method. Work IQ supports both versions and falls back to 0.3 when the request has no `A2A-Version` header, so it works without changes. If your agent accepts only A2A 1.0, expect a "method not found" error.

For a PKCE example, see [Workday A2A](https://github.com/troystaylor/SharingIsCaring/tree/main/Workday%20A2A) in the same repository.

## Troubleshooting

| Symptom | Fix |
|---|---|
| The connector isn't listed under **Add agent** | Deploy to the environment that contains your agent, and check that `x-ms-agentic-protocol` is `a2a-1.0` |
| `Set-A2AAgentCard.ps1` reports HTTP 401 | Pass a valid `-BearerToken` for the agent's API, or use `-Endpoint` |
| `InvalidScriptDefinitionUrlWithNonNullOperations` on create | Leave `scriptOperations` as `[]` |
| Sign-in fails with a redirect URI mismatch | Register the redirect URL from the downloaded connector |
| Sign-in fails with `AADSTS65001` | Grant admin consent for the app's API permission |
| The agent returns 401 | Check `[YOUR_RESOURCE_URI]` against the API's Application ID URI |
| The orchestrator never calls the agent | Rewrite the description on the **Agents** page so it matches what users ask |
| "Method not found" from the agent | The agent accepts only A2A 1.0; check whether it can accept 0.3 |

## Resources

- [A2A Connector Template source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/A2A%20Connector%20Template)
- [Connect an agent over the A2A protocol](https://learn.microsoft.com/microsoft-copilot-studio/add-agent-agent-to-agent)
- [Add other agents overview](https://learn.microsoft.com/microsoft-copilot-studio/authoring-add-other-agents)
- [Authenticate a connector with Entra ID](https://learn.microsoft.com/connectors/custom-connectors/azure-active-directory-authentication)
- [pac connector reference](https://learn.microsoft.com/power-platform/developer/cli/reference/connector)
- [Work IQ A2A quickstart](https://learn.microsoft.com/microsoft-365/copilot/extensibility/work-iq/a2a/quickstart)
- [Agent2Agent protocol](https://a2a-protocol.org/)
- [Agent-to-Agent connector and Power A2A Template](/power%20platform/custom%20connectors/2026-05-05-agent-to-agent-a2a-connector-work-iq.html)
