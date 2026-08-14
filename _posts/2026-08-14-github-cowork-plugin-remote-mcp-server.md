---
layout: post
title: "Bring GitHub workflows to Copilot Cowork"
date: 2026-08-14 16:26:00 -0400
categories: [MCP (Model Context Protocol), Copilot Studio, Integration]
tags: [GitHub, Microsoft 365 Copilot, Copilot Cowork, MCP, Agent Skills, GitHub Copilot]
description: "Connect Copilot Cowork to GitHub's hosted MCP server for repository search, issue triage, pull request reviews, release notes, engineering reports, and Copilot coding agent delegation."
---

Developers already ask GitHub Copilot to explain code and make changes. [GitHub for Copilot Cowork](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/GitHub%20Cowork) brings those workflows into Microsoft 365 Copilot Cowork, where a conversation can start with an engineering report and end with a pull request assigned to the Copilot coding agent.

The plugin connects directly to [GitHub's hosted MCP server](https://github.com/github/github-mcp-server). You don't need to deploy an MCP server or maintain another Azure resource. Each user signs in with their own GitHub identity, so the connector sees only the repositories that person can access.

## What the plugin includes

The package contains:

- A Microsoft 365 unified app manifest using schema version 1.30
- Six Agent Skills for common GitHub workflows
- A description file for 47 GitHub MCP tools
- OAuth configuration through the Microsoft Enterprise Token Store
- A PowerShell script that validates and packages the plugin
- An OAuth test script for separating GitHub failures from Cowork configuration failures

The architecture stays small:

```text
Copilot Cowork
    |
    |-- Agent Skills define workflows, output, and guardrails
    |
    |-- MCP connector sends JSON-RPC over HTTPS
    v
https://api.githubcopilot.com/mcp/
    |
    v
GitHub REST and GraphQL APIs
```

Most of my Cowork plugins use an in-tenant MCP server to keep a vendor-hosted intermediary out of the data path. GitHub is different because the remote endpoint is GitHub's own first-party service. If your organization requires GitHub traffic to leave from an Azure subscription you control, you can self-host the open-source GitHub MCP server and change `mcpServerUrl`.

## Six GitHub skills

Raw tools expose operations. Skills turn those operations into work someone would delegate.

| Skill | What it does | Example request |
|---|---|---|
| `explore-repositories` | Searches repositories and code, reads files, and checks history | "Find the repository that handles OAuth callbacks" |
| `triage-issues` | Finds, creates, labels, assigns, and closes issues | "Triage the unassigned bugs in this repository" |
| `review-pull-requests` | Reads diffs, checks status, comments, approves, and merges | "Review the open pull requests waiting on me" |
| `release-notes` | Builds changelogs and shipped-feature summaries | "Draft release notes for version 2.1" |
| `engineering-report` | Rolls up repository and team activity | "Write a sprint summary and call out blockers" |
| `delegate-to-copilot` | Assigns implementation work to the GitHub Copilot coding agent | "Have Copilot fix issue 42" |

The repository-search and issue-triage skills also include reference files. Search syntax and issue-field details load only when needed instead of taking space in every conversation.

## Why the tool description file matters

The manifest points to `tools/github-tools.json`, which contains the tool names and input schemas packaged with the plugin:

```json
"agentConnectors": [
  {
    "id": "github-mcp",
    "displayName": "GitHub",
    "toolSource": {
      "remoteMcpServer": {
        "mcpServerUrl": "https://api.githubcopilot.com/mcp/",
        "mcpToolDescription": {
          "file": "tools/github-tools.json"
        },
        "authorization": {
          "type": "OAuthPluginVault",
          "referenceId": "{{OAUTH_REFERENCE_ID}}"
        }
      }
    }
  }
]
```

Cowork calls `initialize` and `tools/list` at runtime, but the packaged description file is still required for upload. Microsoft documents this requirement in [Build plugins for Copilot Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development).

## Configure GitHub OAuth

GitHub's remote MCP server doesn't support Dynamic Client Registration. Register a GitHub OAuth App or GitHub App, then connect it to an OAuth client registration in Teams Developer Portal.

A GitHub App gives production deployments better controls, including selectable repository access and expiring user tokens. An OAuth App takes fewer steps for a first test, so the instructions below use one.

### 1. Register a GitHub OAuth App

Open [GitHub developer settings](https://github.com/settings/developers), select **OAuth Apps**, and create an app with these values:

| Field | Value |
|---|---|
| Application name | `GitHub for Copilot Cowork` |
| Homepage URL | Your repository or company URL |
| Authorization callback URL | `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect` |

Generate a client secret and copy it when GitHub displays it.

### 2. Register the OAuth client

Open [Teams Developer Portal](https://dev.teams.microsoft.com/tools), select **Tools** > **OAuth client registration**, and add this configuration:

| Field | Value |
|---|---|
| Registration name | `GitHub MCP` |
| Base URL | `https://api.githubcopilot.com/mcp` |
| Client ID | GitHub OAuth App client ID |
| Client secret | GitHub OAuth App client secret |
| Authorization endpoint | `https://github.com/login/oauth/authorize` |
| Token endpoint | `https://github.com/login/oauth/access_token` |
| Refresh endpoint | `https://github.com/login/oauth/access_token` |
| Scope | `repo read:org read:user offline_access` |
| Enable PKCE | On |

Use **My organization only** while testing in one tenant. Use **Any Microsoft 365 organization** when preparing the plugin for broader distribution.

The two MCP URLs intentionally differ:

- The manifest uses `https://api.githubcopilot.com/mcp/` **with** a trailing slash
- The OAuth registration uses `https://api.githubcopilot.com/mcp` **without** a trailing slash

Using a trailing slash in the OAuth registration's Base URL can let sign-in finish and then fail the connector binding.

The `repo` scope is broad because issue, pull request, and merge tools need write access to private repositories. GitHub doesn't offer a narrower OAuth App scope that preserves those operations. Review this access before distributing the plugin.

`offline_access` asks GitHub for an expiring access token and a refresh token. It doesn't add repository permissions. Enable expiring user tokens on the OAuth App to use the stronger token posture.

### 3. Add the registration ID

Teams Developer Portal returns an OAuth client registration ID after saving. Replace `{{OAUTH_REFERENCE_ID}}` in `manifest.json` with that value.

The committed package keeps the placeholder by design. It can't authenticate until you add a registration created for your tenant and rebuild the package.

## Package and upload

Run the packaging script from the plugin folder:

```powershell
cd "Cowork Plugins\GitHub Cowork"
.\package.ps1
```

The script validates the manifest, skill folders, skill front matter, icons, tool description, and OAuth placeholder before creating the zip file.

Upload the package through **Microsoft 365 admin center** > **Agents** > **Tools** > **Registry**. Choose the test users or groups that should receive it, then enable the GitHub source in a new Cowork session. Microsoft documents the admin flow in [Manage tools for agents](https://learn.microsoft.com/microsoft-365/admin/manage/manage-tools-for-agent).

Each user completes GitHub sign-in the first time a skill needs a tool. An administrator can't authorize GitHub on someone else's behalf.

## Try these requests

Start with a read operation before testing mutations:

```text
Find my repositories related to Model Context Protocol.

Show open issues without an assignee in troystaylor/SharingIsCaring.

Review pull request 123 and summarize any merge risks.

Draft release notes from pull requests merged since August 1.

Create an engineering report for this repository covering the last seven days.

Assign issue 42 to the GitHub Copilot coding agent.
```

Confirm the target repository before creating issues, commenting, merging, or delegating work. The skills include mutation guardrails, but clear repository names make the conversation safer.

## Fix common connection failures

| Symptom | Check |
|---|---|
| Connector fails after a successful sign-in | Remove the trailing slash from the OAuth registration's Base URL |
| GitHub reports a redirect mismatch | Set the callback URL exactly to `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect` |
| Personal repositories work, but organization repositories return 404 | Ask the GitHub organization to approve the OAuth App |
| Tools return 401 or 403 | Confirm the OAuth registration and installed plugin use the same Microsoft 365 tenant |
| A scope or credential fix appears to have no effect | Revoke the GitHub OAuth App grant, disconnect the source, and sign in again |
| Token exchange still fails | Run `.\Test-OAuthExchange.ps1` to test the client ID, secret, callback, and MCP call outside Cowork |

GitHub returns HTTP 200 for some token-exchange errors and puts the error in the response body. A generic connector error can therefore hide `incorrect_client_credentials`. The included test script prints the real response without storing or echoing the client secret.

## Resources

- [GitHub Cowork plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/GitHub%20Cowork)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
- [GitHub MCP server](https://github.com/github/github-mcp-server)
- [Build plugins for Copilot Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
- [Manage plugins for Copilot Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-manage-plugins)
- [Configure plugin authentication](https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-authentication)
