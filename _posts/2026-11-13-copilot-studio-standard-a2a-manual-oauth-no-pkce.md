---
layout: post
title: "Standard harness agents skip PKCE on A2A with manual OAuth"
date: 2026-11-13 16:30:00 -0400
categories: [Power Platform, Copilot Studio]
tags: [Copilot Studio, A2A, MCP, OAuth, PKCE, Custom Connectors, PAC CLI, Microsoft Copilot harness]
description: "Copilot Studio creates a different OAuth identity provider for A2A and MCP connectors depending on harness and auth option. Most MCP and A2A providers require PKCE, but a standard harness agent that adds an A2A agent with manual OAuth gets a connector without it. Here's the full matrix and a PAC CLI fix."
---

Copilot Studio creates a custom connector behind every A2A agent and MCP server you add. The OAuth settings in that connector decide whether sign-in uses Proof Key for Code Exchange (PKCE), and the wizard doesn't tell you which identity provider it picked.

The comparison covered both agent harnesses, both protocols, and the manual and dynamic OAuth options. One combination stands out: a standard harness agent that connects to an A2A agent with manual OAuth. That connector doesn't use PKCE, and the sign-in request shows it.

## What PKCE adds

[PKCE](https://datatracker.ietf.org/doc/html/rfc7636) protects the authorization code. The client creates a random `code_verifier`, sends a hash of it as the `code_challenge` when it starts sign-in, and sends the original verifier when it redeems the code. An attacker who intercepts the code can't redeem it without the verifier.

The Microsoft identity platform [recommends `code_challenge` for all application types](https://learn.microsoft.com/entra/identity-platform/v2-oauth2-auth-code-flow), public and confidential clients alike. Authorization servers can also enforce it per client, which is where a connector without PKCE fails.

## The matrix

Each Copilot Studio connector stores its sign-in behavior in an `identityProvider` value in the connector's API properties. Here's what each combination produced:

| Scenario | Auth option | Connector created with | PKCE |
|---|---|---|---|
| A2A, standard harness | Manual OAuth | `oauth2` (client ID and secret) | No. Sign-in sends no code challenge, and the token request sends the client secret |
| A2A, Microsoft Copilot harness | Manual OAuth | `oauth2pkce` | Enabled in the connector definition |
| MCP, standard and Microsoft Copilot harness | Manual OAuth | `oauth2pkce` | Enabled in the connector definition |
| MCP, standard and Microsoft Copilot harness | Dynamic client registration (DCR) | `oauth2pkcewithdcr` | Enabled in the connector definition |

A standard harness agent that connects to an A2A agent with manual OAuth is the only combination that doesn't create a PKCE-enabled connector. Everything else in the table does.

## Where each option lives

The portal paths differ by harness, so it helps to know which wizard you're in.

**A2A, standard harness.** Go to your agent's **Agents** page, select **Add agent**, then **A2A agent**. You enter the endpoint URL and choose **None**, **API key**, or **OAuth 2.0**. For OAuth 2.0 the docs list the client ID, client secret, authorization URL, token URL, and refresh URL. See [Connect an agent available over the A2A protocol](https://learn.microsoft.com/microsoft-copilot-studio/add-agent-agent-to-agent).

**A2A, Microsoft Copilot harness.** Go to the **Build** tab, select **Connected agents**, then **Add** and **Add A2A agent**. You enter the agent card URL, and OAuth 2.0 offers a **Dynamic** or **Manual** configuration type. The wizard also has an **Add redirect URL** step. See [Add an A2A agent as a connected agent](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/add-agent-to-agent).

**MCP, standard harness.** Go to **Tools**, then **Add a tool**, **New tool**, and **Model Context Protocol**. OAuth 2.0 offers **Dynamic discovery**, **Dynamic**, and **Manual**. See [Connect your agent to an existing MCP server](https://learn.microsoft.com/microsoft-copilot-studio/mcp-add-existing-server-to-agent).

**MCP, Microsoft Copilot harness.** Go to the **Build** tab, select **Tools**, then **Add** and **Model Context Protocol (MCP)**. This article is [in preview](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/tools-add-mcp-server) and doesn't list the authentication fields. Expect the details to change.

For the harness tradeoffs, see [Compare Copilot Studio agent harnesses](https://learn.microsoft.com/microsoft-copilot-studio/guidance/choose-harness).

## What the sign-in request shows

For the connector a standard harness agent creates for an A2A agent with manual OAuth, both ends of the flow tell the same story:

- The authorization request carried no code challenge.
- The token request included the client secret.

That's a plain authorization code flow with a confidential client. It works, and it's what the `oauth2` identity provider is designed to do. It also means an authorization server that enforces PKCE for the client rejects the sign-in.

The other three rows use `oauth2pkce` or `oauth2pkcewithdcr`. The connector definition has PKCE enabled, so sign-in includes a code challenge.

The Microsoft Learn pages for these wizards describe the fields you fill in. They don't name the identity provider the wizard picks, so this matrix comes from inspecting the connectors, not from documentation. Treat it as an observation of current behavior.

## Choosing an option

- **Your authorization server supports dynamic client registration:** pick a DCR option in MCP. You get `oauth2pkcewithdcr` and no client to register by hand.
- **You have a preregistered client and an MCP server:** pick **Manual**. You get `oauth2pkce`.
- **You have a preregistered client and an A2A agent in the Microsoft Copilot harness:** pick **Manual**. You get `oauth2pkce`.
- **You have a preregistered client and an A2A agent in the standard harness:** manual OAuth gives you `oauth2`. If the authorization server requires PKCE, or you don't want the secret in the token request, update the connector as described next.

## Switch the A2A connector to PKCE

You can change the identity provider yourself with [PAC CLI](https://learn.microsoft.com/power-platform/developer/cli/reference/connector). Testing this change worked: sign-in used a code challenge, the authorization server verified the code verifier, and the token request sent no client secret.

1. Find the connector ID. `pac connector list` shows only solution-aware connectors, so a connector you haven't added to a solution might be missing from the list. In that case, copy the ID from the connector's URL in Power Automate.

    ```powershell
    pac connector list --environment <environment-id>
    ```

2. Download the connector.

    ```powershell
    pac connector download `
      --environment <environment-id> `
      --connector-id <connector-id> `
      --outputDirectory .\a2a-connector
    ```

3. In `apiProperties.json`, find `properties.connectionParameters.token.oAuthSettings`. Set `identityProvider` to `oauth2pkce`, or to `oauth2pkcewithdcr` if the authorization server supports dynamic client registration. Remove any `clientSecret` property. Leave the rest of the file as downloaded.

    ```json
    "oAuthSettings": {
      "identityProvider": "oauth2pkce",
      "clientId": "<your-client-id>",
      "scopes": [ "<scope>" ]
    }
    ```

4. Update the connector.

    ```powershell
    pac connector update `
      --environment <environment-id> `
      --connector-id <connector-id> `
      --api-properties-file .\a2a-connector\apiProperties.json `
      --api-definition-file .\a2a-connector\apiDefinition.swagger.json
    ```

5. Delete the existing connection and create a new one. A connection made before the update keeps its old settings.

6. Check the redirect URL in the downloaded `apiProperties.json`, and make sure the same URL is registered with your authorization server. Register the client as a public client that allows PKCE.

If you need a reference, create a test A2A connection in the Microsoft Copilot harness with manual OAuth, download that connector, and compare its `oAuthSettings` with yours.

Keep your edited `apiProperties.json` in source control. The Microsoft Copilot harness wizard [discards the connector](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/add-agent-to-agent) it built from earlier settings when you change the authentication settings, so a later wizard edit can undo your change.

## Check your own connectors

To audit what's already deployed, download each A2A and MCP connector and read `identityProvider`:

```powershell
pac connector download --connector-id <connector-id> --outputDirectory .\check
Select-String -Path .\check\apiProperties.json -Pattern '"identityProvider"'
```

Anything that says `oauth2` with an A2A agent behind it was probably created by the standard harness with manual OAuth, and it sends a client secret with no PKCE.

If you'd rather define the A2A connector yourself, the [A2A connector template](/power%20platform/custom%20connectors/2026-10-06-a2a-connector-template-copilot-studio.html) already ships with PKCE and Microsoft Entra ID sign-in.

## Resources

- [Connect an agent available over the A2A protocol (standard harness)](https://learn.microsoft.com/microsoft-copilot-studio/add-agent-agent-to-agent)
- [Add an A2A agent as a connected agent (Microsoft Copilot harness)](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/add-agent-to-agent)
- [Connect your agent to an existing MCP server](https://learn.microsoft.com/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
- [Add an MCP server as a tool (Microsoft Copilot harness)](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/tools-add-mcp-server)
- [pac connector](https://learn.microsoft.com/power-platform/developer/cli/reference/connector)
- [Microsoft identity platform and OAuth 2.0 authorization code flow](https://learn.microsoft.com/entra/identity-platform/v2-oauth2-auth-code-flow)
- [RFC 7636: Proof Key for Code Exchange](https://datatracker.ietf.org/doc/html/rfc7636)
