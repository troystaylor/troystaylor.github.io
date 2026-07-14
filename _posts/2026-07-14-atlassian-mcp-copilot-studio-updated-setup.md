---
layout: post
title: "Atlassian Rovo MCP server in Copilot Studio after the SSE sunset"
date: 2026-07-14 10:00:00 -0500
categories: [Copilot Studio, MCP]
tags: [MCP, Atlassian, Jira, Confluence, Copilot Studio, OAuth, Dynamic Client Registration]
description: "Atlassian sunset /v1/sse on June 30, 2026, and their docs recommend /v1/mcp/authv2 as the replacement. That endpoint grants :agent-interface scopes that cause 401s on every Jira and Confluence tool call in Copilot Studio. Use /v1/mcp instead."
---

Atlassian's Rovo MCP server gives Copilot Studio agents direct access to Jira, Confluence, and Compass — JQL search, issue creation, page lookups — without a custom connector. The Copilot Studio CAT team published the [original walkthrough](https://microsoft.github.io/mcscatblog/posts/atlassian-jira-remote-mcp-copilot-studio/) in May 2026 using `https://mcp.atlassian.com/v1/sse`. That endpoint was [sunset on June 30, 2026](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/setting-up-clients/). The admin UI and permissions model have also changed.

This post documents the current state: the correct endpoint for Copilot Studio, the updated admin prerequisites, and the scope mismatch between what Atlassian's docs recommend and what actually works.

## Server URL: `/v1/mcp`, not `/v1/mcp/authv2`

Atlassian's docs recommend this endpoint for MCP clients:

```
https://mcp.atlassian.com/v1/mcp/authv2
```

That works for Claude, Cursor, and other clients. Copilot Studio's Dynamic discovery flow requires a different endpoint:

```
https://mcp.atlassian.com/v1/mcp
```

The difference is scope negotiation. `/authv2` grants `:agent-interface` scopes during Dynamic Client Registration. Those scopes don't match what the Jira and Confluence tools expect at runtime. The result: `getAccessibleAtlassianResources` succeeds (it only needs `read:account` and `read:me`), but `searchJiraIssuesUsingJql`, `createJiraIssue`, and every other useful tool call returns 401 "scope does not match."

`/v1/mcp` grants the correct scopes — `read:jira-work`, `write:jira-work`, `search:confluence`, and others — and works with Dynamic discovery.

| Endpoint | Scopes granted | Works in Copilot Studio |
|----------|---------------|------------------------|
| `/v1/sse` | Correct | No (sunset June 30, 2026) |
| `/v1/mcp/authv2` | `:agent-interface` | No (401 on tool calls) |
| `/v1/mcp` | `read:jira-work`, `write:jira-work`, `search:*` | Yes |

## Admin prerequisites

Atlassian consolidated the admin UI and added a permissions layer. Six prerequisites must be in place before the Copilot Studio side works.

| # | Prerequisite | Where to check | Notes |
|---|-------------|----------------|-------|
| 1 | Atlassian Cloud site | Your URL is `*.atlassian.net` | Server and Data Center don't support Remote MCP |
| 2 | Rovo MCP server enabled | **Atlassian Administration > Rovo > Rovo MCP server** | Single settings page — Rovo activation and MCP enablement are no longer separate toggles. Rovo Free doesn't support MCP tool execution; Standard (Beta) or higher is required |
| 3 | Domain allowlisting permits Copilot Studio | Same Rovo MCP server page | Default "Atlassian-supported domains" already includes `global.consent.azure-apim.net` and `token.botframework.com`. If your org locked down to an explicit allowlist, add `https://global.consent.azure-apim.net/**` |
| 4 | IP allowlists include the user's network | **Atlassian Administration** (org-level) | [IP allowlisting](https://support.atlassian.com/security-and-access-policies/docs/specify-ip-addresses-for-product-access/) applies to MCP connections. The consent screen still renders for blocked IPs, but tool calls fail |
| 5 | MCP server permissions allow Read + Search | **Rovo MCP server > Permissions tab** | New since the original post. Three permission types: Read, Write, Search. Use **Edit details** for per-app control |
| 6 | Test user has product access | **Atlassian Administration > Apps > Atlassian Apps** | Without a Jira/Confluence/Compass seat, the server returns an empty resource list |

Two timing notes on prerequisite 2:

- Plan changes can take **24–48 hours** to propagate. During that window, `getAccessibleAtlassianResources` works but all Jira, Confluence, and Search tools return 401.
- After upgrading plans, revoke the old app consent at [id.atlassian.com/manage-profile/apps](https://id.atlassian.com/manage-profile/apps) and create a fresh connection.

## Copilot Studio setup

The Copilot Studio side is unchanged from the [original walkthrough](https://microsoft.github.io/mcscatblog/posts/atlassian-jira-remote-mcp-copilot-studio/). The only difference is the URL.

1. **Add a tool** > Model Context Protocol > New tool
2. Server URL: `https://mcp.atlassian.com/v1/mcp`
3. Authentication: **Dynamic discovery**
4. Create the connection (first-time consent)
5. Activate the connection and click **Add and configure**
6. Test: "List the Jira sites I have access to" → "Find all open issues in my Jira site"
7. Publish

## Common failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| `getAccessibleAtlassianResources` works, all other tools return 401 "scope does not match" | Using `/v1/mcp/authv2` endpoint | Change server URL to `/v1/mcp` |
| Same 401 pattern after switching to `/v1/mcp` | Rovo Free plan, or plan upgrade hasn't propagated | Upgrade to Standard; wait 24–48 hours; revoke old consent and re-create connection |
| No tools discovered | Admin toggle off, or domain blocked | Verify Rovo MCP server is enabled and domain allowlist includes Copilot Studio |
| Tools discovered but every call returns "Access denied... not authorized the search permission" | MCP server Permissions tab has Search blocked | Enable Read + Search in **Rovo MCP server > Permissions** |
| Consent screen appears but tool calls return permissions error | IP allowlisting blocks the user's network | Add egress IPs to the org allowlist |
| 401 "scope mismatch" after initially working connection | Dynamic Client Registration didn't request full scope set | Delete the connection in Power Platform and re-create it |
| Empty resource list, agent has no tools to call | Test user lacks Jira/Confluence/Compass product access | Grant product access under Atlassian Administration |

## What changed from the original post

| Area | May 2026 (original) | July 2026 (current) |
|------|---------------------|---------------------|
| Server URL | `https://mcp.atlassian.com/v1/sse` | `https://mcp.atlassian.com/v1/mcp` |
| Protocol | Server-Sent Events | Streamable HTTP |
| Admin path | Separate Rovo toggle + Products > Remote MCP server | Single page: Atlassian Administration > Rovo > Rovo MCP server |
| Domain control | Security > External app policies | Rovo MCP server settings > domain allowlist |
| Permissions | Not configurable | Permissions tab — Read, Write, Search per app |
| Prerequisites | 5 | 6 |

## References

- [Wiring up the Jira (Atlassian) Remote MCP server in Copilot Studio — The Custom Engine](https://microsoft.github.io/mcscatblog/posts/atlassian-jira-remote-mcp-copilot-studio/)
- [Setting up clients — Atlassian Support](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/setting-up-clients/)
- [Control Atlassian Rovo MCP server settings — Atlassian Support](https://support.atlassian.com/security-and-access-policies/docs/control-atlassian-rovo-mcp-server-settings/)
- [Configure Atlassian Rovo MCP server permissions — Atlassian Support](https://support.atlassian.com/security-and-access-policies/docs/Configure-Atlassian-Rovo-MCP-server-permission/)
- [Using with other supported MCP clients — Atlassian Support](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/using-with-other-supported-mcp-clients/)
