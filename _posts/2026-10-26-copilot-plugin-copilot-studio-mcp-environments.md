---
layout: post
title: "A Copilot plugin for Copilot Studio MCP in any environment"
date: 2026-10-26 16:50:00 -0400
categories: [MCP (Model Context Protocol), Copilot Studio, Integration]
tags: [Copilot Studio, Microsoft 365 Copilot, MCP, Azure Container Apps, Microsoft Entra ID, Power Platform, On-behalf-of, Agent Skills]
description: "Microsoft hosts the Copilot Studio MCP server once per environment. Publish one plugin per environment, or deploy an optional Container Apps gateway that lets a single plugin reach every environment a user can access. The gateway is the better fit for pro-devs."
---

Microsoft hosts the Copilot Studio MCP server once per Power Platform environment, and each environment has its own URL built from its environment ID. A Microsoft 365 Copilot plugin manifest can point at only one fixed URL, so there are two ways to give people Copilot Studio in Copilot:

- **One plugin per environment.** Publish a plugin for each environment you want to offer, all with the same base skills. Admins control exactly which environments Copilot can reach.
- **One plugin with a gateway.** Deploy a small gateway once, publish one plugin, and let each user reach every environment they have access to.

Both routes work. I built the gateway so an admin doesn't have to deploy a plugin for every environment, but it's optional. If you only want to offer a few environments in Copilot, the per-environment route is simpler and needs no Azure resources. If you build across many environments, especially as a pro-dev, the gateway is the one I recommend.

The [Copilot Studio MCP Server](https://github.com/troystaylor/SharingIsCaring/tree/main/Container%20Apps/Copilot%20Studio%20MCP%20Server) folder in my SharingIsCaring repository has the gateway source, the Bicep, and the deployment script. The [Copilot Studio plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Plugins/Copilot%20Studio) is the one that uses it.

## Which route fits

| | One plugin per environment | One plugin with the gateway |
| --- | --- | --- |
| Plugins to publish | One for each environment | One |
| Environments available | Only the ones you publish | Any the user can access |
| Azure resources to host | None | A Container App |
| Adding an environment | Publish another plugin | Nothing to do |
| Best for | A short, admin-controlled list | Pro-devs and makers working across many environments |

Pick the per-environment route when the list is short and you want to decide which environments Copilot can reach. Pick the gateway when you move between development, test, and production environments, or when new environments appear faster than you want to package plugins.

## What the gateway does

The plugin talks to the gateway at one URL. The gateway:

- Adds a required `environmentId` argument to every Copilot Studio tool.
- Adds a `list_environments` tool that returns the environments the signed-in user can access.
- Forwards each call to the environment the model chose.

It doesn't rewrite Copilot Studio's tools. It reads the tool list from Copilot Studio when it needs it, so new tools and schema changes appear without a redeploy.

| Tool | What it does |
| --- | --- |
| `list_environments` | Lists the environments the user can access |
| `get_copilot_studio_skills`, `manage_agents`, `manage_workflows`, `discover_resources`, `get_consumption` | Copilot Studio's own tools, each with `environmentId` as the first required argument |

Copilot asks which environment to use when it isn't clear, and names the environment before it changes anything.

## Each person signs in as themselves

The plugin signs the user in to the gateway's own Microsoft Entra API with the scope `access_as_user`. The gateway then:

1. **Checks the token.** It validates the signature, tenant, audience, lifetime, and scope. Requests from another tenant, for another audience, or without the scope are refused. A token issued for Power Platform is refused too.
2. **Exchanges it.** It trades the token for a Power Platform token for the same user with the on-behalf-of flow. Entra only does this when the app has consent for the Power Platform permissions, so consent is the control point.
3. **Calls Copilot Studio.** Copilot Studio and Power Platform permissions decide what the user can do.

A token issued for Power Platform carries a `nonce` in its header, so only Power Platform can verify its signature. A gateway that forwarded it would have to trust the caller. Issuing the token for the gateway itself avoids that.

A few design choices keep the gateway small and safe to run:

- **No secret to store.** The gateway proves it's the Entra app with a token from its user-assigned managed identity, trusted through a federated credential that `deploy.ps1` creates.
- **No user data stored.** Exchanged tokens stay in memory, keyed by a hash of the caller's token, and expire with it.
- **Power Platform only.** The hostname is built from a checked GUID plus the fixed suffix `environment.api.powerplatform.com`, so a model-supplied `environmentId` can't point the gateway at another host.
- **No retries on tool calls.** A retried call could create or change something twice.
- **Single tenant.** Tokens from other tenants are refused.

The server runs on .NET 10 as a stateless ASP.NET Core app, so any replica can answer any request. It uses plain JSON-RPC instead of the MCP C# SDK, so it can relay Copilot Studio's messages as they are, including fields newer than the SDK.

## Deploy the gateway

You need an Azure subscription, the Azure CLI, permission to register apps in Entra, and an admin to grant consent.

1. Create the Entra app that is both the plugin's sign-in client and the gateway's API:

   ```powershell
   .\scripts\New-PluginClientApp.ps1 -GrantAdminConsent
   ```

2. Deploy the gateway with the tenant ID and client ID from step 1:

   ```powershell
   .\infra\deploy.ps1 -ResourceGroup rg-copilot-studio-mcp -TenantId <your tenant ID> -ClientId <client ID>
   ```

   The script provisions Container Apps, Container Registry, Log Analytics, and Application Insights. It builds the image in Azure Container Registry, so you don't need local Docker. The last line prints the MCP endpoint, and the host without `https://` or `/mcp` is the plugin's `COPILOT_STUDIO_GATEWAY_HOST`.

3. Set the tenant ID, client ID, and gateway host in the [Copilot Studio plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Plugins/Copilot%20Studio), then provision, package, and share it with the `wiqd` CLI. Its readme covers each command and the Microsoft 365 admin center upload.

## Skills the plugin carries

The plugin ships two shared skills, `copilot-studio-access` and `write-safety`, and five scenario skills:

| Skill | Use it to | Changes things |
| --- | --- | --- |
| `agent-authoring` | Create or edit an agent as a draft, preview it, then publish | Yes, after confirmation |
| `workflow-authoring-and-diagnostics` | Build workflows, run real tests, diagnose failed runs | Yes, after confirmation |
| `agent-evaluation` | Create and run evaluation suites and read the results | Yes, after confirmation |
| `connector-discovery` | Find connector operations, schemas, connections, and parameter values | No |
| `consumption-review` | See credit consumption by agent or workflow and remaining capacity | No |

These are the base skills in either route. The Copilot Studio MCP server is in preview and its actions can change, so the skills tell Copilot to read each action's contract at run time instead of relying on fixed action names.

## Troubleshooting

- **`401` from `/mcp`:** The token is missing, expired, for another tenant, or not issued for the gateway's app. Check that the plugin requests `api://<client ID>/access_as_user`.
- **`403` from `/mcp`:** The token lacks `access_as_user`. Check that the Entra app exposes the scope and has consent for it.
- **"Environment not found or access denied":** The user has no Copilot Studio access in that environment, or it has no Dataverse database.
- **`list_environments` permission denied:** `EnvironmentManagement.Environments.Read` has no admin consent. Run `New-PluginClientApp.ps1 -GrantAdminConsent` again or ask an admin.

## Resources

- [Copilot Studio MCP Server gateway](https://github.com/troystaylor/SharingIsCaring/tree/main/Container%20Apps/Copilot%20Studio%20MCP%20Server)
- [Copilot Studio plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Plugins/Copilot%20Studio)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
- [Build plugins for Copilot Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
- [Configure plugin authentication](https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-authentication)
