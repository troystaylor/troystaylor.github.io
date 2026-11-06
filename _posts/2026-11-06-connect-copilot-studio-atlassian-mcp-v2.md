---
layout: post
title: "Connect Copilot Studio to Atlassian MCP v2 in five steps"
date: 2026-11-06 09:15:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [Atlassian, Jira, Confluence, Bitbucket, Custom Connectors, MCP, Copilot Studio, OAuth, PAC CLI]
description: "The quickest way to connect a Copilot Studio agent to the Atlassian MCP server v2 for Jira, Confluence, and Bitbucket, plus a versioned connector option, scope settings, and troubleshooting."
---

The official Atlassian MCP server at `https://mcp.atlassian.com/v2/mcp` gives Copilot Studio agents access to Jira, Confluence, Jira Service Management, Bitbucket Cloud, Loom, Goals, Projects, Teams, and Teamwork Graph. Every call runs as the signed-in user with that user's Atlassian permissions.

The quickest way to connect is the Copilot Studio Add MCP wizard. It takes five steps and needs no files. If you want a connector you can version and deploy across environments, the [Atlassian MCP V2 connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Atlassian%20MCP%20V2) covers that later in this post.

## Connect in five steps

1. In Copilot Studio, open your agent and go to **Tools > Add a tool > New tool > Model Context Protocol**.
2. Enter a name such as `Atlassian`, a description, and the server URL `https://mcp.atlassian.com/v2/mcp`.
3. For authentication, choose **OAuth 2.0** and select **Dynamic discovery**. If discovery fails, try **Dynamic**.
4. Select **Create**, then **Create new connection**, and sign in to Atlassian. Approve the consent screen for your site.
5. Select **Add and configure**.

The wizard creates the connector and registers the OAuth client with Atlassian for you. If your Atlassian admin blocks sign-in, see [Troubleshooting](#troubleshooting).

If you work in Microsoft 365 Copilot or Copilot Cowork instead, the [Atlassian plugin](https://troystaylor.com/mcp%20(model%20context%20protocol)/copilot%20studio/integration/2026-10-15-atlassian-copilot-plugin-read-only-oauth-scopes.html) covers that surface with sixteen skills.

## How the server exposes tools

Atlassian doesn't send its whole tool catalog up front. The server lists a handful of primary tools, such as `getJiraIssue`, `searchJiraIssuesUsingJql`, `createJiraIssue`, `getConfluenceContent`, and `searchConfluence`. Everything else is reachable through four meta tools:

| Tool | Use |
| --- | --- |
| `discover` | Describe a goal in plain language and get back the matching tool |
| `executeRead` | Run a read tool |
| `executeWrite` | Run a tool that creates or updates data |
| `executeDestructive` | Run a tool that deletes data |

Your agent calls `discover`, then runs the tool it returns. New Atlassian tools show up without any change to the connector.

Some tools, including `search`, `searchAtlassian`, and the Teamwork Graph tools, use Rovo credits from your organization's shared pool. See [Rovo usage limits](https://support.atlassian.com/rovo/docs/rovo-usage-limits/) before you enable them for a large group.

## Deploy a versioned connector

The connector in the repo is for teams that want to version, share, and deploy the same connector across environments. It has one operation, `InvokeMCP`, and no `script.csx`, so Power Platform sends MCP traffic straight to Atlassian and there's no code to maintain.

| File | Purpose |
| --- | --- |
| `apiDefinition.swagger.json` | The `InvokeMCP` operation and the OAuth endpoints |
| `apiProperties.json` | OAuth settings for the `oauth2pkcewithdcr` identity provider (public client with PKCE) |
| `apiProperties.oauth2pkce.json` | OAuth settings for the `oauth2pkce` identity provider (client secret with PKCE) |
| `Register-AtlassianClient.ps1` | Creates an Atlassian OAuth client for your connector's callback URL |

## Why there's a registration script

Atlassian has no developer console app for its MCP server. Clients come from dynamic client registration (DCR), where you post your redirect URL to the authorization server and get a client ID back.

`Register-AtlassianClient.ps1` reads the registration endpoint from the server's metadata, posts your callback URL, and prints the `client_id`. With `-Confidential` it requests a client secret instead, copies it to your clipboard, and never prints it.

### Choose an identity provider

| Type | Identity provider | Use it when |
| --- | --- | --- |
| **Public client** | `oauth2pkcewithdcr` | You want the default for a versioned connector |
| **Client secret** | `oauth2pkce` | The public client signs in but token refresh fails, or you want a confidential client |

`oauth2pkcewithdcr` and `oauth2pkce` are hidden Power Platform identity providers that you can only set in `apiProperties.json`. They aren't documented, so test sign-in and token refresh in a non-production environment first.

### Deploy with a public client

Run these commands from the connector folder and replace `<ENV>` with your environment ID or URL.

1. Deploy the connector. Leave `[YOUR_CLIENT_ID]` and `[YOUR_REDIRECT_URL]` as they are. Power Platform replaces the redirect URL with the callback URL it generates.

   ```powershell
   pac connector create `
       --environment <ENV> `
       --api-definition-file .\apiDefinition.swagger.json `
       --api-properties-file .\apiProperties.json
   ```

   Don't pass `--script-file`. Note the connector ID that PAC returns.

2. Download the deployed connector and read its callback URL.

   ```powershell
   pac connector download --environment <ENV> --connector-id <CONNECTOR_ID> --outputDirectory .\deployed
   (Get-Content .\deployed\apiProperties.json -Raw | ConvertFrom-Json).properties.connectionParameters.token.oAuthSettings.redirectUrl
   ```

   The URL looks like `https://global.consent.azure-apim.net/redirect/<your-connector>` and is specific to this connector and environment.

3. Register an Atlassian client for that URL.

   ```powershell
   .\Register-AtlassianClient.ps1 -RedirectUrl "<CALLBACK_URL>"
   ```

   Copy the `client_id` it prints.

4. Put the client ID in a working copy of `apiProperties.json` and update the connector.

   ```powershell
   $props = Join-Path $env:TEMP 'apiProperties.json'
   (Get-Content .\apiProperties.json -Raw).Replace('[YOUR_CLIENT_ID]', '<CLIENT_ID>') | Set-Content $props
   pac connector update `
       --environment <ENV> `
       --connector-id <CONNECTOR_ID> `
       --api-definition-file .\apiDefinition.swagger.json `
       --api-properties-file $props
   ```

5. Create the connection. In [Power Automate](https://make.powerautomate.com), open **Custom connectors**, edit **Atlassian MCP V2**, go to the **Test** tab, select **New connection**, and sign in to Atlassian. Leave any client secret field blank.

6. Add the connector to your agent. In Copilot Studio, go to **Tools > Add a tool > Connector**, choose **Atlassian MCP V2**, and select the connection.

If you change the connector later, delete and recreate any connection made before the change.

### Deploy with a client secret

Follow the public client steps with these differences:

- Use `apiProperties.oauth2pkce.json` in place of `apiProperties.json`.
- In step 3, run `Register-AtlassianClient.ps1` with `-Confidential`.
- After step 4, open the connector in Power Automate, go to the **Security** tab, enter the client ID and client secret, and select **Update connector**. Clear your clipboard afterward.

## Set scopes to set limits

Scopes are what the token can do, so they cap the connector no matter what an agent attempts. These settings apply to the versioned connector. The default set is:

| Scope | Grants |
| --- | --- |
| `read:me`, `read:account`, `offline_access` | Your profile, and a refresh token so you stay signed in |
| `read:jira:agent-interface`, `search:jira:agent-interface` | Read and search Jira |
| `write:jira:agent-interface` | Create and update work items, comments, worklogs, and links |
| `read:confluence:agent-interface`, `search:confluence:agent-interface` | Read and search Confluence |
| `write:confluence:agent-interface` | Create and update pages and comments |
| `read:bitbucket:agent-interface` | Read Bitbucket Cloud repositories, pull requests, and pipelines |

For a read-only connector, remove the two `write:` scopes. To add more, append them to the `scopes` array in `apiProperties.json` and to both `securityDefinitions.oauth2_auth.scopes` and `security[0].oauth2_auth` in `apiDefinition.swagger.json`. Then update the connector and recreate your connections.

| Add this scope | For |
| --- | --- |
| `read:jsm:agent-interface`, `write:jsm:agent-interface` | Jira Service Management requests and operations alerts |
| `read:loom:agent-interface`, `write:loom:agent-interface` | Loom videos, transcripts, and meeting action items |
| `read:goals:agent-interface`, `read:projects:agent-interface`, `read:teams:agent-interface` | Goals, Projects, and Teams |
| `search:code:agent-interface` | Code search across connected code providers |
| `read:all:twg`, `search:rovo:agent-interface` | Teamwork Graph and Rovo search (uses Rovo credits) |

Leave out `delete:jira:agent-interface` and `manage:jira:agent-interface` unless you need them. Atlassian disables those tool groups by default, and an admin must enable them.

Your Atlassian organization admin also controls which tools, scopes, and client domains are allowed under **Atlassian Administration > Rovo MCP server**.

## Tell the agent how the server works

Add instructions that explain the discovery pattern. For example:

> Start every Atlassian task by calling `getAccessibleAtlassianResources` to get the `cloudId`. If the tool you need isn't listed, call `discover` with your goal, then run the tool it returns with `executeRead` for reads or `executeWrite` for changes. Confirm with me before any write.

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| Sign-in page says the redirect URI isn't registered | The client was registered for a different callback URL. Run the script again with the exact `redirectUrl` from `pac connector download` and put the new client ID in the connector. |
| Sign-in is blocked for your organization | An Atlassian admin restricts client domains or tools. Ask them to allow `global.consent.azure-apim.net` under **Atlassian Administration > Rovo MCP server**. |
| Sign-in works but tool calls return 401 | Delete the connection and create a new one. Do this after every connector update. |
| A tool is missing or returns access denied | The scope wasn't requested or consented, an admin disabled the tool's permission group, or you lack permission in the product. |
| Tools stop working after about an hour | Token refresh failed. Confirm `offline_access` is in the scopes, then switch to the client secret connector. |
| Jira Service Management tools are missing | Add the `read:jsm:agent-interface` scope and reconsent. |
| Bitbucket tools return nothing | They work only for Bitbucket Cloud workspaces linked to your Atlassian organization. |

## Good to know

- Atlassian plans to move v1 callers to v2 tools on March 1, 2027. This connector targets v2 only.
- Gateways that need every tool in one `tools/list` response use `https://mcp.atlassian.com/v2/mcp?tools=all`. A connector's base path can't carry a query string, so that URL isn't available here.
- Atlassian records every call in your organization's audit log.

## Resources

- [Atlassian MCP V2 source](https://github.com/troystaylor/SharingIsCaring/tree/main/Atlassian%20MCP%20V2)
- [Atlassian MCP V2 Copilot plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Plugins/Atlassian%20MCP%20V2)
- [Atlassian remote MCP server](https://support.atlassian.com/atlassian-ai-gateway/docs/get-started-with-the-atlassian-remote-mcp-server/)
- [PAC CLI introduction](https://learn.microsoft.com/power-platform/developer/cli/introduction)
