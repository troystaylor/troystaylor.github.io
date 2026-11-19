---
layout: post
title: "Skip the Teams Dev OAuth: Atlassian in Microsoft 365 Copilot with DCR"
date: 2026-11-19 09:00:00 -0500
categories: [Power Platform, Copilot Studio, MCP]
tags: [Atlassian, Jira, Confluence, Bitbucket, MCP, Microsoft 365 Copilot, Federated Connectors, OAuth, DCR]
description: "Connect the Atlassian MCP server to Microsoft 365 Copilot with a custom Federated connector and dynamic client registration. No OAuth app, client secret, or Teams Developer Portal registration."
---

The Atlassian MCP server at `https://mcp.atlassian.com/v2/mcp` can reach Jira, Confluence, and Bitbucket Cloud from Microsoft 365 Copilot without an OAuth app. You add it as a custom Federated connector in the Microsoft 365 admin center and choose dynamic client registration (DCR) for authentication.

With DCR, Copilot reads Atlassian's `.well-known` metadata, registers its own OAuth client ([RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591)), and signs each user in with the authorization code flow and PKCE. You don't copy a client ID or secret, and you don't register anything in the Teams Developer Portal. Each user keeps their own Atlassian permissions, and every call lands in your organization's Atlassian audit log.

This post covers the admin center route, a fallback for tenants that don't have DCR yet, and a plugin route if you want to ship skills with the connector. For the Copilot Studio version, see [Connect Copilot Studio to Atlassian MCP v2 in five steps](https://troystaylor.com/power%20platform/custom%20connectors/mcp/2026-11-06-connect-copilot-studio-atlassian-mcp-v2.html).

> The steps follow [Set up custom federated connectors](https://learn.microsoft.com/microsoft-365/copilot/connectors/set-up-custom-federated-connectors) on Microsoft Learn. That article still lists only Microsoft Entra SSO, OAuth 2.0, and No Auth, so the DCR steps are based on [Configure dynamic client registration](https://learn.microsoft.com/plugins/plugin-authentication-dynamic-client-registration). Field names and order in your admin center can differ. Check them against the screen.

## How it works

1. You add the Atlassian MCP server as a custom connector and choose DCR.
2. When a user first connects, Copilot reads Atlassian's metadata and finds the registration endpoint.
3. Copilot registers an OAuth client with Atlassian and stores it in the Microsoft Enterprise token store.
4. The user signs in to Atlassian and consents. Copilot stores and refreshes the tokens.
5. Copilot calls the Atlassian tools at question time, as that user. Nothing is indexed in Microsoft Graph.

## Before you start

| You need | Notes |
| --- | --- |
| Microsoft 365 admin role | Global Administrator or AI Administrator in the [Microsoft 365 admin center](https://admin.microsoft.com/) |
| Copilot licenses | Users need a Microsoft 365 Copilot license |
| Atlassian Cloud site | Jira, Confluence, or Bitbucket Cloud, linked to your Atlassian organization |
| Atlassian organization admin | Allows Microsoft's callback domain in Atlassian |
| MCP server URL | `https://mcp.atlassian.com/v2/mcp` |
| Developer and legal details | Developer name, website, privacy policy URL, and terms of use URL, if the connector or a package asks for them |
| Network access | If your Atlassian organization uses an IP allowlist, allow the [static egress IP addresses for Microsoft 365 Copilot](https://learn.microsoft.com/microsoft-365/copilot/connectors/federated-connectors-network-requirements) |

## Allow Microsoft in Atlassian

Atlassian blocks OAuth clients from domains an admin hasn't allowed. Ask an Atlassian organization admin to:

1. Open **Atlassian Administration**, select your organization, then **Connectors** > **Atlassian MCP server**.
2. Select **Add domain** and allow `https://teams.microsoft.com/**`, Microsoft's OAuth callback host.
3. Confirm that OAuth 2.1 is on. API tokens aren't needed.

If sign-in is blocked later, read the `redirect_uri` in the failing authorization request and allow that host.

## Create the connector

1. Sign in to the [Microsoft 365 admin center](https://admin.microsoft.com/).
2. Select **Copilot** > **Connectors**, then the **Gallery** tab.
3. Under **Created by your org**, find **Create a new connector** and select **Add**.
4. On the **Custom connector** page, under **Connect to MCP server**, select **Add**.
5. Enter these details:

   | Field | Value |
   | --- | --- |
   | **Display name** | `Atlassian` |
   | **Description** | See below |
   | **Base URL** | `https://mcp.atlassian.com/v2/mcp` |

6. For authentication, choose **Dynamic client registration (DCR)**. You don't enter a registration ID, client ID, or client secret.
7. Select **Save**.

Copilot uses the description to decide when to call the connector, so make it specific. The [connector description generation skill](https://learn.microsoft.com/microsoft-365/copilot/connectors/generate-custom-connector-description) can draft one. This is a starting point:

> Real-time access to your organization's Atlassian Cloud work. Search, read, create and update Jira work items, search and read Confluence pages and spaces, and review Bitbucket Cloud pull requests, diffs, comments and pipelines. Use it for questions about project status, tickets, documentation and code review. Results respect the signed-in user's Atlassian permissions.

To change it later, open the connector in **Your connections**, select **Edit description**, and select **Save**.

## Test with a small audience

New custom connectors are governed by **Allow agents and plugins built by your organization** and **User access**. Stage the rollout so only testers see the connector first:

1. Under **Copilot** > **Connectors**, open **Your connections** and select the connector.
2. Select **Staged rollout**.
3. Choose **Users** or **Groups** and add your testers.
4. Confirm the testers are included in **Agents** > **Settings** > **User access**.

Changes can take up to 10 minutes. Testers might need to refresh Copilot or start a new conversation.

Each tester then connects once:

1. Open **Microsoft 365 Copilot Chat** > **Settings** > **Sources**.
2. Find **Atlassian** and select **Connect**.
3. Sign in to Atlassian and review the consent screen. The first sign-in registers the client.

Then ask a question for each product:

| Product | Try |
| --- | --- |
| Jira | "What's the status of PROJ-123?" or "List my open work items, oldest update first." |
| Confluence | "Summarize the Confluence page about our incident process." |
| Bitbucket | "Review pull request 42 in the web repository." |

Confirm that answers cite Atlassian records and that a user without access to a project can't see it. To test token refresh, return after the access token expires. The first call should work without a new sign-in.

## Deploy to everyone

When testing passes, open the connector in **Your connections** and select **Deploy to all users**. The connector then reaches everyone included in **User access**.

To pause it, select **Disable**, or set the staged rollout to **No users**. **Delete** removes the connector and its configuration permanently. You can also block or unblock the connector under **Agents** > **Tools**.

## Scopes and permissions

With DCR you don't type scopes into a registration. Copilot requests what Atlassian advertises, and each user's Atlassian permissions still decide what a call can read or change. Atlassian lists the supported scopes in `scopes_supported` at `https://mcp.atlassian.com/.well-known/oauth-protected-resource/v2/mcp`.

- Review the consent screen the first time you sign in, and decline if it asks for more than you intend to allow.
- Atlassian disables the delete and manage tool groups by default.
- The Teamwork Graph and Rovo search tools use Rovo credits from your organization's shared pool.
- Bitbucket tools work only for Bitbucket Cloud workspaces linked to your Atlassian organization.
- Atlassian write tools have no idempotency key, so ask users to review a write before they confirm it.

## If DCR isn't available in your tenant

The DCR option is new and might not have reached your tenant. Until it does, use OAuth 2.0 with a client you register yourself.

1. Register a client with Atlassian's registration endpoint, using Microsoft's callback `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect` as the redirect URI. The [Register-AtlassianClient.ps1](https://github.com/troystaylor/SharingIsCaring/tree/main/Atlassian%20MCP%20V2) script in the repo does this and copies the client secret to your clipboard without printing it:

   ```powershell
   .\Register-AtlassianClient.ps1 `
       -RedirectUrl "https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect" `
       -Confidential -ClientName "Atlassian for Microsoft 365 Copilot"
   ```

2. In the [Teams Developer Portal](https://dev.teams.microsoft.com/tools), select **Tools** > **OAuth client registration** > **New OAuth connection** and enter:

   | Field | Value |
   | --- | --- |
   | **Base URL** | `https://mcp.atlassian.com/v2/mcp` |
   | **Client ID** and **Client secret** | From the script. Keep the secret out of source control. |
   | **Authorization endpoint** | `https://auth.atlassian.com/authorize` |
   | **Token endpoint** and **Refresh endpoint** | `https://auth.atlassian.com/oauth/token` |
   | **Scope** | `offline_access read:me read:account search:jira:agent-interface read:jira:agent-interface search:confluence:agent-interface read:confluence:agent-interface read:bitbucket:agent-interface` |
   | **Restrict usage by app** | **Any Teams app** (tool calls return 404 if you bind an app ID) |
   | **PKCE** | On. Atlassian supports S256 only. |

3. Copy the **OAuth client registration ID**, create the connector as above, and choose **OAuth 2.0** with that ID.

Add `write:jira:agent-interface write:confluence:agent-interface` to the scope only if you want Copilot to create and update items. Users must sign in again after the scopes change.

## Build a plugin with Work IQ Dev Tools

Use a plugin when you want to ship skills with the connector, keep the package in source control, or target Copilot Cowork. The plugin lists the MCP server in `agentConnectors` in the Microsoft 365 app manifest. For `--auth-type dcr`, Work IQ Dev Tools (WIQD) writes no `authorization` node and no credential reference, so Copilot registers the client at runtime.

This route has different requirements:

- The `wiqd plugin` commands are in alpha and can change.
- Copilot Cowork requires a packaged tool description file.
- The Teams Developer Portal doesn't support DCR. WIQD, Microsoft 365 Agents Toolkit, and the declarative agent developer skill do.

### Install and sign in

```powershell
iex "& { $(irm 'https://aka.ms/wiqd/install.ps1') }"
wiqd auth login --interactive
wiqd doctor
```

### Capture the tool list

1. Start [MCP Inspector](https://github.com/modelcontextprotocol/inspector). It needs Node.js 20 or later.

   ```powershell
   npx @modelcontextprotocol/inspector
   ```

2. Set **Transport Type** to **Streamable HTTP** and **URL** to `https://mcp.atlassian.com/v2/mcp`. Select **Connect** and sign in to Atlassian.
3. Open **Tools** > **List Tools** and copy the result.
4. Save it as `toolDescription.json`, keeping each tool's `name`, `description`, and `inputSchema` exactly as returned:

   ```json
   {
     "tools": [
       {
         "name": "<tool name>",
         "description": "<tool description>",
         "inputSchema": { "type": "object", "properties": {}, "required": [] }
       }
     ]
   }
   ```

Atlassian lists a few primary tools and reaches the rest through `discover` plus `executeRead` and `executeWrite`, so the file stays short and new tools work without a plugin update. For a flat list of every tool, use `https://mcp.atlassian.com/v2/mcp?tools=all` here and in the next step. That list is long and paginated.

### Create the plugin and add the connector

```powershell
wiqd plugin create --name "Atlassian MCP DCR"
cd "Atlassian MCP DCR"
Copy-Item <path>\toolDescription.json .\appPackage\toolDescription.json

wiqd plugin add connector `
    --name "Atlassian MCP" `
    --description "Jira, Confluence and Bitbucket Cloud through the Atlassian MCP server." `
    --url https://mcp.atlassian.com/v2/mcp `
    --auth-type dcr `
    --tool-description toolDescription.json
```

`--tool-description` is relative to `appPackage/`, and the file must exist first. Open `appPackage/manifest.json` and check that:

- `developer.name`, `websiteUrl`, `privacyUrl`, and `termsOfUseUrl` are yours, with no scaffold placeholders left.
- `validDomains` includes `mcp.atlassian.com`. Add `auth.atlassian.com` if validation asks for it.
- No secrets appear anywhere.

### Add skills

The [Atlassian MCP V2 folder](https://github.com/troystaylor/SharingIsCaring/tree/main/Atlassian%20MCP%20V2) has skills that follow Atlassian's `discover`, `executeRead`, and `executeWrite` pattern. Copy the ones you want into `appPackage/skills`:

```powershell
$src = "<path to repo>\Atlassian MCP V2\appPackage\skills"
New-Item -ItemType Directory -Force .\appPackage\skills | Out-Null
foreach ($s in 'atlassian-v2-access','write-safety','jira-work-items','confluence-pages','bitbucket-pr-review') {
    Copy-Item "$src\$s" ".\appPackage\skills\$s" -Recurse
}
```

Register each folder in `appPackage/manifest.json`:

```json
"agentSkills": [
  { "folder": "skills/atlassian-v2-access" },
  { "folder": "skills/write-safety" },
  { "folder": "skills/jira-work-items" },
  { "folder": "skills/confluence-pages" },
  { "folder": "skills/bitbucket-pr-review" }
]
```

To write your own, run `wiqd plugin add skill --name "<skill name>"` and edit the generated `SKILL.md`. Each skill must name tools the server returns.

### Validate, provision, package, and share

Run these in order. `package` needs the environment file that `provision` writes.

```powershell
wiqd plugin validate --mode source --env dev
wiqd plugin provision --env dev
wiqd plugin package --env dev
wiqd plugin validate --mode package --env dev
wiqd plugin share --env dev --scope users --email <your address>
```

Raise `version` in `appPackage/manifest.json` before you provision a changed package again. `share` prints Cowork and Chat links. Open one, ask a Jira question, and sign in when Copilot asks you to connect.

To roll out to your organization, run `wiqd plugin publish --env dev` (check the current command surface first), then ask a Microsoft 365 admin to review and assign the plugin under **Agents** > **Tools**.

Install either the admin center connector or the plugin, not both, or Copilot sees duplicate Atlassian tools.

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| Connector isn't visible to a user | Check, in order: **Allow agents and plugins built by your organization** is on, the connector is enabled and not blocked under **Agents** > **Tools**, the user is in **User access** and the staged rollout, the user has a Copilot license, and 10 minutes have passed |
| Works only for the admin | The connector is staged only to the admin, **User access** targets another group, or other users haven't connected under **Settings** > **Sources** |
| Sign-in says the client or domain isn't allowed | An Atlassian admin hasn't allowed Microsoft's domain. Allow the `redirect_uri` host shown in the request |
| Connect fails with a registration error | Registration needs a reachable `registration_endpoint` that issues a client secret. Check the server's `.well-known` metadata |
| Sign-in works, but tool calls return 401 | Check the `Authorization` header and audience in the failing request. Atlassian can require a `resource` or `audience` parameter that Copilot doesn't send |
| Tool calls return 404 | Confirm the base URL is exactly `https://mcp.atlassian.com/v2/mcp`. For the OAuth 2.0 fallback, set **Restrict usage by app** to **Any Teams app** |
| Calls fail from your network | Your Atlassian organization uses an IP allowlist. Add the Copilot static egress IP addresses |
| Sign-in is required again after a day | Token refresh isn't working. Confirm Atlassian issued a refresh token (`offline_access`), or use the OAuth 2.0 fallback |
| Connector still appears after you disabled it | Wait up to 10 minutes, then refresh Copilot |
| (WIQD) "Could not verify connection" in Cowork | The tool description file is missing or doesn't match `tools/list`. Capture it again and repackage |
| (WIQD) `provision` fails with a version error | Raise `version` in `appPackage/manifest.json` |
| (WIQD) `package` can't resolve variables | Run `wiqd plugin provision --env dev` first |

## Known limits

- DCR in the Enterprise token store requires a client secret, so it fails if Atlassian registers only public clients. If registration succeeds but refresh fails, use the OAuth 2.0 fallback.
- A Federated connector exposes the server's tools only. It can't carry skills, which is the reason to choose the plugin route.
- Federated connectors are available in Microsoft 365 Copilot Chat and Cowork on web and desktop. See the [Federated connectors overview](https://learn.microsoft.com/microsoft-365/copilot/connectors/federated-connectors-overview) for the current list.
- To add this server as an MCP action on a declarative agent, use `wiqd agent add action --mcp-server-url https://mcp.atlassian.com/v2/mcp --mcp-auth-type oauth-dynamic`. That manifest model is different, so don't mix it with the plugin connector.
- Replace the placeholder icons in `appPackage/color.png` (192x192) and `appPackage/outline.png` (32x32) before you publish a plugin.

## Resources

- [Atlassian MCP V2 source in SharingIsCaring](https://github.com/troystaylor/SharingIsCaring/tree/main/Atlassian%20MCP%20V2)
- [Set up custom federated connectors](https://learn.microsoft.com/microsoft-365/copilot/connectors/set-up-custom-federated-connectors)
- [Configure dynamic client registration](https://learn.microsoft.com/plugins/plugin-authentication-dynamic-client-registration)
- [Configure remote MCP servers for Microsoft 365 Copilot plugins](https://learn.microsoft.com/plugins/configure-plugin-mcp-servers)
- [Build a plugin with Work IQ Dev Tools](https://microsoft.github.io/wiqd/getting-started/build-a-plugin/) and the [WIQD CLI reference](https://microsoft.github.io/wiqd/cli/reference/)
- [Get started with the Atlassian MCP server](https://support.atlassian.com/atlassian-ai-gateway/docs/get-started-with-the-atlassian-remote-mcp-server/)
- [Control Atlassian MCP server settings](https://support.atlassian.com/security-and-access-policies/docs/control-atlassian-mcp-server-settings/)
