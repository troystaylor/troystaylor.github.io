---
layout: post
title: "Connect Copilot Studio to an MCP server with public-client PKCE"
date: 2026-09-04 16:30:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [PKCE, OAuth, MCP, Copilot Studio, Custom Connectors, PAC CLI, Power Automate]
description: "A script-free Power Platform custom connector template that authenticates to a remote MCP Streamable HTTP server with authorization code, PKCE S256, and a static public client that has no client secret."
---

Remote MCP servers that follow the [MCP authorization spec](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization) expect the client to be a public client: authorization code, PKCE with `S256`, and no client secret. The Copilot Studio Add MCP Server wants a secret. [MCP Public Client PKCE](https://github.com/troystaylor/SharingIsCaring/tree/main/MCP%20Public%20Client%20PKCE) is a two-file connector template that skips the designer and configures a static public client through PAC CLI instead.

It's based on Microsoft's [MCP Streamable HTTP connector template](https://github.com/microsoft/PowerPlatformConnectors/tree/dev/custom-connectors/MCP-Streamable-HTTP), with the OAuth configuration swapped out.

## Read this before you deploy it

`oauth2pkcewithdcr` is a hidden Power Platform identity provider, and its current refresh template includes `client_secret={ClientSecret}` even when the connector defines no `clientSecret`. The initial authorization works. Refresh is the open question, and it depends on how your authorization server handles an unexpected empty `client_secret`.

Treat this template as experimental. The [refresh validation](#validate-refresh-behavior) section below is the part that decides whether it's usable for you.

## Two files, no script

| File | Purpose |
|---|---|
| `apiDefinition.swagger.json` | The remote MCP Streamable HTTP operation and OAuth endpoints |
| `apiProperties.json` | The hidden public-client PKCE identity provider |

There's no `script.csx`. Power Platform forwards MCP traffic straight to the remote server, so nothing needs to sit in the middle.

You'll need a remote MCP server using Streamable HTTP, an authorization server supporting authorization code with PKCE `S256`, a static public-client registration with no secret, and its client ID, authorization endpoint, token endpoint, refresh endpoint, and scopes. Also PAC CLI and permission to create connectors in a test environment. If refresh is part of your test, the authorization server has to issue refresh tokens.

## Configure the API definition

Edit `apiDefinition.swagger.json`:

1. Replace `your-mcp-server.example.com` with the MCP hostname, without `https://` or a path.
2. Replace `/mcp` in `basePath` with the MCP endpoint path.
3. Replace the authorization and token endpoint URLs.
4. Replace `mcp.tools` with the scope your server requires.

For multiple scopes, add each one to both `securityDefinitions.oauth2_auth.scopes` and `security[0].oauth2_auth`.

The single operation carries the marker that tells Power Platform this is MCP traffic rather than a REST call:

```json
"paths": {
  "/": {
    "post": {
      "operationId": "InvokeMCP",
      "summary": "Invoke MCP with public-client PKCE",
      "x-ms-agentic-protocol": "mcp-streamable-1.0",
      "responses": {
        "200": { "description": "MCP response" }
      }
    }
  }
}
```

Keep `x-ms-agentic-protocol` and keep the operation at path `/` beneath `basePath`. The MCP path lives in `basePath`, not in the operation path.

## Configure the connector properties

The OAuth settings in `apiProperties.json` are where the public client is declared:

```json
"oAuthSettings": {
  "identityProvider": "oauth2pkcewithdcr",
  "clientId": "[YOUR_CLIENT_ID]",
  "scopes": ["mcp.tools"],
  "redirectMode": "Global",
  "redirectUrl": "[YOUR_REDIRECT_URL]",
  "properties": {
    "IsFirstParty": "False",
    "IsOnbehalfofLoginSupported": false
  },
  "customParameters": {
    "serverUrl": { "value": "https://your-mcp-server.example.com" },
    "authorizationUrl": { "value": "https://your-auth-server.example.com/oauth/authorize" },
    "tokenUrl": { "value": "https://your-auth-server.example.com/oauth/token" },
    "refreshUrl": { "value": "https://your-auth-server.example.com/oauth/token" }
  }
}
```

Replace the client ID, the scope, and the four URLs. `serverUrl` is the MCP server origin without the endpoint path — the path stays in the swagger `basePath`.

Leave `[YOUR_REDIRECT_URL]` alone. Power Platform overwrites it with the generated per-connector callback URL at deployment.

Never add a `clientSecret` property. Adding one turns this into a confidential client and defeats the whole exercise. The scope list here also has to match the scopes in `apiDefinition.swagger.json`.

## Create the connector

Confirm the target environment first:

```powershell
pac auth list
pac connector list --environment POWER_PLATFORM_ENVIRONMENT_ID_OR_URL
```

Then create it:

```powershell
pac connector create `
    --environment POWER_PLATFORM_ENVIRONMENT_ID_OR_URL `
    --api-definition-file .\apiDefinition.swagger.json `
    --api-properties-file .\apiProperties.json
```

Don't pass `--script-file`. Record the connector ID that PAC returns — the next step needs it. Power Platform validates both files during creation, so resolve any errors PAC reports before continuing.

## Register the generated callback URL

Power Platform generates the redirect URL, so you have to read it back out of the deployed connector:

```powershell
pac connector download `
    --environment POWER_PLATFORM_ENVIRONMENT_ID_OR_URL `
    --connector-id CONNECTOR_ID `
    --outputDirectory .\deployed-connector
```

Open `deployed-connector\apiProperties.json` and find:

```text
properties.connectionParameters.token.oAuthSettings.redirectUrl
```

Register that exact URL with your authorization server's public-client registration. It uses HTTPS and the `global.consent.azure-apim.net` host. The callback is specific to this connector in this environment, so a connector deployed to a second environment needs its own registration.

## Create and test the connection

1. Open [Power Automate](https://make.powerautomate.com) and select the environment you deployed to.
2. Open **Custom connectors** and edit **MCP Public Client PKCE**.
3. Open **Test** and select **New connection**.
4. If a client-secret field appears, leave it blank.
5. Complete authorization and consent, then refresh the connection list.

Then wire it into an agent:

1. Open [Copilot Studio](https://copilotstudio.microsoft.com) and select the same environment.
2. Open a non-production test agent, go to **Tools**, and select **Add a tool**.
3. Select **MCP Public Client PKCE** and its connection, then add it to the agent.
4. Confirm Copilot Studio discovers the remote tools, and invoke a safe read-only one.

## Validate refresh behavior

A successful first tool call proves that authorization code with PKCE worked and that MCP connectivity is fine. It says nothing about refresh, which is where the `client_secret={ClientSecret}` template matters.

To test it:

1. Keep the same connection and agent.
2. Wait for the access token to expire, plus a clock-skew buffer.
3. Don't repair or recreate the connection.
4. Invoke the same read-only tool again.
5. Check sanitized authorization-server logs for the refresh request.

If the normal access-token lifetime is too long to wait out, use a non-production client or policy with a shorter lifetime. A long-lived access token postpones the question rather than answering it.

Record only these observations:

```text
Refresh request observed: yes/no
grant_type: refresh_token/other
client_id present: yes/no
client_secret presence: absent/empty/populated
HTTP Basic client authentication present: true/false
Refresh outcome: succeeded/rejected
OAuth error code, if any:
Post-refresh MCP tool outcome: succeeded/failed
```

Never record tokens, codes, verifiers, secrets, cookies, or authorization headers.

## Interpret the result

| Observation | Interpretation |
|---|---|
| `client_secret` absent, no HTTP Basic authentication, refresh succeeds | Strict public-client refresh behavior works |
| `client_secret` empty and refresh succeeds | A compatibility path, but only if the authorization-server owner approves empty-value handling |
| `client_secret` empty and refresh fails | The current provider refresh template is incompatible |
| `client_secret` populated | Confidential-client behavior is being applied |
| HTTP Basic authentication present | Client authentication is being applied |
| No refresh request observed | The test is inconclusive — the token probably hadn't expired |

The result you want:

```text
client_secret presence: absent
HTTP Basic client authentication present: false
Refresh outcome: succeeded
Post-refresh MCP tool outcome: succeeded
```

Nothing in the OAuth specifications requires an authorization server to ignore an unexpected empty `client_secret`. Confirm empty-value behavior with the authorization-server owner instead of assuming that empty and absent mean the same thing.

## Update the connector

After changing either file:

```powershell
pac connector update `
    --environment POWER_PLATFORM_ENVIRONMENT_ID_OR_URL `
    --connector-id CONNECTOR_ID `
    --api-definition-file .\apiDefinition.swagger.json `
    --api-properties-file .\apiProperties.json
```

Delete and recreate existing connections after any OAuth configuration change. Cached connections hold the old settings and will fail in ways that look like server problems.

## Resources

- [MCP Public Client PKCE template](https://github.com/troystaylor/SharingIsCaring/tree/main/MCP%20Public%20Client%20PKCE)
- [Microsoft MCP Streamable HTTP connector template](https://github.com/microsoft/PowerPlatformConnectors/tree/dev/custom-connectors/MCP-Streamable-HTTP)
- [Update custom connector OAuth identity providers with PAC CLI](https://troystaylor.com/power%20platform/custom%20connectors/2026-08-07-update-custom-connector-oauth-identity-providers-pac-cli.html)
- [Connect a Copilot Studio agent to an existing MCP server](https://learn.microsoft.com/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
- [Create and test a custom connector](https://learn.microsoft.com/connectors/custom-connectors/define-blank#step-5-test-the-connector)
- [RFC 6749: The OAuth 2.0 authorization framework](https://www.rfc-editor.org/rfc/rfc6749.html)
- [RFC 7636: Proof key for code exchange by OAuth public clients](https://www.rfc-editor.org/rfc/rfc7636.html)
- [RFC 8252: OAuth 2.0 for native apps](https://www.rfc-editor.org/rfc/rfc8252.html)
