---
layout: post
title: "Point a Copilot plugin at a Power Platform connector"
date: 2026-10-29 16:58:00 -0700
categories: [Power Platform, Custom Connectors, Integration]
tags: [Copilot Cowork, Power Platform, Custom Connectors, Agent Skills, Work IQ Dev Tools, paconn, MCP, OAuth]
description: "A Copilot plugin doesn't need a remote MCP server URL or its own OAuth registration. It can point at an existing Power Platform custom connector and let the connection handle sign-in. Here's how the pattern works in Copilot Cowork, with a Salesforce connector as the test case."
---

Most Copilot plugins point at a remote MCP server URL and ask you to register an OAuth client in the Teams Developer Portal. A plugin can also point at an existing Power Platform custom connector. The plugin stores a pointer, the platform resolves the endpoint and operations at runtime, and the user signs in through a normal Power Platform connection.

If you already have a custom connector, you don't need to host a second server just to give Copilot access to the same API. Sign-in, token refresh, and the endpoint stay in the connector and the connection.

I tested the pattern in Copilot Cowork with a Salesforce connector. Salesforce is incidental. Any connector with an OpenAPI definition should follow the same steps. The [Salesforce PP Plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Plugins/Salesforce%20PP%20Plugin) folder in my SharingIsCaring repository has the working plugin, and the [learnings document](https://github.com/troystaylor/SharingIsCaring/blob/main/Copilot%20Plugins/Salesforce%20PP%20Plugin/Power%20Platform%20Connector%20Plugins%20-%20Learnings.md) records every result I confirmed.

## Where this works today

Everything here was observed in **Copilot Cowork**. The `openApiConnector` tool source comes from Work IQ Dev Tools (`wiqd`) and is a devPreview shape. As of the Microsoft Learn pages I checked today, the published `agentConnectors[].toolSource` schema lists only `remoteMcpServer`, so Learn doesn't document this pattern for Microsoft 365 Copilot chat. Expect it to change.

## Remote MCP server or connector

| | Remote MCP server | Power Platform connector |
| --- | --- | --- |
| Manifest node | `toolSource.remoteMcpServer` | `toolSource.openApiConnector` |
| Hosted MCP URL needed | Yes | No |
| Sign-in | Developer Portal OAuth registration (`OAuthPluginVault`) | Power Platform connection (`ConnectionVault`) |
| Manifest version | 1.29 | `devPreview` only |
| Tool list | `tools/list` from the server | Resolved by the platform from the connector |

## What Cowork does with the pointer

Cowork doesn't list MCP tools from the plugin. It treats the plugin as a connector it hydrates and calls by operation. In a trace, a request ran a "Hydrate connector" step, then "Invoke connector operation" with `Tool provider: powerplatform` and the connector's REST operation ID (`CreateRecord`) with flat parameters.

That shapes how you write skills:

- Name REST operation IDs in the skill, not MCP tool names.
- Tools that exist only in the connector's MCP script and have no REST operation are out of reach in Cowork. Rebuild them in the skill from the operations that do exist.
- Body fields are flattened into the parameter list, so a skill can name the fields directly.

## MCP tools from the same connector

A connector that implements an MCP endpoint keeps its tools. I called the connector's `/mcp` path through its runtime URL with a token for `https://apihub.azure.com`. The server answered a full handshake: `initialize` returned the script's server info, `tools/list` returned all 37 tools, and `tools/call` ran two of them against the backend. That's the call a Copilot Studio MCP client makes.

So one connector can serve two audiences. Cowork uses its REST operations today, and any host that speaks MCP to the connector gets the full tool set. I haven't seen Cowork call the MCP endpoint, so don't plan around it until that changes.

## Build the plugin

You need `wiqd` 0.21.0 or later (`npm install -g @microsoft/wiqd@latest`). Earlier versions can't add an OpenAPI custom connector.

1. **Deploy the connector first.** The plugin can't create it. See the next section.
2. **Scaffold the plugin and add the connector.**

   ```powershell
   wiqd plugin create --name "My Plugin" --output "My Plugin"
   wiqd plugin add connector --kind openapi --name "My Connector" `
       --description "<what it does>" --auth-reference-id "<connector API name>" --dev-preview
   ```

   `--url`, `--tool-description`, and `--auth-type` are rejected for this kind. `plugin create --output` nests the project one folder deep, so move the contents up.
3. **Replace the scaffold placeholders** in `appPackage/manifest.json` and add skills under `appPackage/skills/`.
4. **Provision, package, deep-validate, and share.**

   ```powershell
   wiqd plugin provision --env dev
   wiqd plugin package --env dev
   wiqd plugin validate --mode deep --env dev
   wiqd plugin share --scope users --email <address> --env dev
   ```

Static `validate` reports "No declarative-agent surface to validate" and passes for a skills-plus-connector plugin, so package first and run `validate --mode deep`. Deep validation accepted the `openApiConnector` shape with zero errors and zero warnings. Bump `version` in the manifest before every re-provision, and add `--env dev` to `package` and `share` because both default to `local`.

### The reference value

The `referenceId` is the connector's API name, in the form `shared_<name>-<suffix>`. It isn't the Dataverse logical name that `pac connector list` shows. Read it from the API Id column of `pac connection list`, the part after `/apis/`.

It changes per environment. Keep it out of source control: use `${{MY_CONNECTOR_REFERENCE_ID}}` in the manifest and put the value in a gitignored `env/.env.dev.user` file with a committed `.sample`. `package` reads the variable from the shell, so set `$env:MY_CONNECTOR_REFERENCE_ID` before you run it.

## Deploy the connector to the Cowork environment

Cowork doesn't look in your default or demo environment. It uses its own Power Platform environment, named **Copilot Cowork**. When my connector lived only in the demo environment, Connect failed with "Could not verify connection," and a browser HAR showed the connections gateway answering `Connector not found`. After I deployed to the Cowork environment, Connect opened the OAuth dialog and finished with "You're connected."

I expect plugins to move out of the Cowork environment and into a broader Copilot environment over time. That's my read, not something Microsoft has announced, so check where your host looks before you deploy, and expect to redeploy or repoint the connector if that changes.

The Cowork environment has no Dataverse, so `pac connector create` fails with "No Dataverse organization was found." Use `paconn`:

```powershell
paconn login
paconn create --env <environment id> --api-def apiDefinition.swagger.json --api-prop apiProperties.json --script script.csx --secret <client secret>
```

A few notes from the field:

- `paconn login` is a device-code sign-in. If you redirect its output to a file, set `PYTHONUNBUFFERED=1` or the code never appears.
- A connector with a non-empty `scriptOperations` must be deployed with its script.
- `--secret` puts the client secret on the command line. Read it from an environment variable, and delete temp copies of `apiProperties.json`.
- A connection in one environment doesn't carry over to another. Create one in the Cowork environment.
- To find which environment a host uses, capture a HAR of the failing Connect click and read `environment_id` from the `GET /v1/connections` response.

Each environment produces a different redirect URL. Read it from the deployed connector (`properties.connectionParameters.token.oAuthSettings.redirectUrl`) and add it to your identity provider's allowed callbacks. Keep the earlier ones.

## Give every operation a static body

This was the surprise. `CreateRecord` and `UpdateRecord` in my connector take a body whose fields come from `x-ms-dynamic-schema`. That works well in Power Automate and Power Apps, where the designer shows per-object fields.

In Cowork, `CreateRecord` failed with "Couldn't complete 'Invoke connector operation'." A HAR of the approval calls showed Cowork trying three shapes: flat parameters, a wrapped body, and finally a different operation whose body has a fixed schema. That last one succeeded. When I asked, Cowork explained that its view of `CreateRecord` had only the path parameters and no request body, so the backend received an empty POST.

Declaring 206 static properties next to the dynamic schema didn't help. Removing `x-ms-dynamic-schema` and keeping the static properties did. Cowork then called `CreateRecord` with flat parameters, and the backend returned `201`.

Cowork drops a body parameter that carries `x-ms-dynamic-schema`, even with static `properties` beside it. For a Cowork connector:

1. Remove `x-ms-dynamic-schema` from request bodies.
2. Declare the fields you need under `properties`.
3. Keep the dynamic version for any copy used in Power Automate or Power Apps.

I applied the same change to the update operation, but haven't tested an update in Cowork yet.

The platform enforced a few rules while I declared properties:

- Enum values must be unique. Picklists that repeat values across countries made the definition fail with `InvalidSwagger ... valid against no schemas from 'oneOf'`.
- Send compact ASCII JSON. The pretty-printed definition was about 374 KB and the update dropped the connection. Compacted, it was about 132 KB and succeeded.
- A `paconn update` that prints `Expecting value: line 1 column 1` can still have applied. Read the connector back to check.

## Writes need a yes

Cowork showed an "Approved 1 action" step before a write ran, but the first test's trace didn't, so don't rely on it alone. Start every skill that has write operations with a rule: no write without a yes, and name each write operation. In testing, Cowork showed the exact change, noted a similar existing record, and asked "Go ahead?" before doing anything. Reads ran without a prompt.

Every call runs as the signed-in user, so the backend's own permissions still apply.

## Why not a plain OpenAPI plugin

The documented route for Microsoft 365 Copilot chat is a declarative agent with an API plugin built from an OpenAPI file (`wiqd agent add action`). It worked for me, but it bypasses the Power Platform connection. Token refresh is expected to fail, and users will have to sign in again. The connector route keeps refresh with the connection platform.

If you take the OpenAPI route, two details will save you an afternoon:

- The OAuth client that `wiqd agent add action` registers had PKCE off. A provider that requires PKCE answers with `missing required code challenge`.
- `oauth/register` only creates a registration when `OAUTH2_AUTH_REGISTRATION_ID` is empty. Setting `isPKCEEnabled: true` and re-provisioning changed nothing until I deleted that line from `env/.env.<env>`, bumped the version, and provisioned again.

I also tried a `remoteMcpServer` with `ConnectionVault` authorization. The Developer Portal rejected it with a 422 in my tenant, while the same value provisioned fine on an `openApiConnector`.

## Known limits

- Open Plugin export isn't supported for `ConnectionVault` connectors.
- The plugin showed as **Available** under Agents > Tools in the Microsoft 365 admin center, but its Users tab said the owner hadn't shared the tool even after a successful `wiqd plugin share`. It still appeared in Cowork for the owner.
- Replace the default plugin icons (`color.png` at 192x192 and `outline.png` at 32x32) before you publish.

## Resources

- [Salesforce PP Plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Plugins/Salesforce%20PP%20Plugin) (the test case)
- [Power Platform connector plugin learnings](https://github.com/troystaylor/SharingIsCaring/blob/main/Copilot%20Plugins/Salesforce%20PP%20Plugin/Power%20Platform%20Connector%20Plugins%20-%20Learnings.md)
- [Salesforce MCP connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20MCP) (the connector behind it)
