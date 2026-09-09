---
layout: post
title: "Archive Copilot Studio channel manifests with v1.2"
date: 2026-09-09 16:31:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Copilot Studio, Custom Connectors, MCP, Power Automate, Agent ALM, Channel Manifest, Microsoft 365, Power Platform API]
description: "Copilot Studio Bots v1.2 adds a Power Automate action and MCP tool to download Microsoft 365 channel manifest ZIPs, plus safer file handling and live-API reliability fixes."
---

A published Copilot Studio agent has another artifact worth keeping beside its source: the package sent to its channel.

[Copilot Studio Bots v1.2](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Bots) downloads that package for the Microsoft 365 channel. Save it before a release, archive it on a schedule, or compare two packages when a channel change behaves differently from the agent you tested.

The update adds the **Download Agent Channel Manifest** action for Power Automate and the `download_agent_channel_manifest` tool for Model Context Protocol (MCP) callers. It also hardens both ZIP download paths and fixes two problems found while testing the connector against the live Power Platform API.

## What's new in v1.2

| | v1.1 | v1.2 |
|---|---:|---:|
| Usable REST actions | 16 | 17 |
| MCP tools | 18 | 19 |
| OpenAPI operations, including MCP and two internal dropdowns | 19 | 20 |
| Channel manifest export | No | Microsoft 365 ZIP |

The new REST action and MCP tool use the same operation:

```http
GET https://api.powerplatform.com/copilotstudio/
    environments/{environmentId}/agents/{botId}/
    channels/{channelName}/download
    ?includeAgentSchema={true|false}
    &api-version=2024-10-01
```

This route differs from the other connector operations. Evaluations, quarantine, consent bypass, reassignment, deletion, and identity migration use `bots/{botId}`. Channel manifest export uses `agents/{botId}`.

Microsoft currently documents one channel value: `M365`. The connector defaults to it and rejects other values before making the request. When `includeAgentSchema` isn't supplied, the connector leaves the query parameter out instead of changing an omitted value to `false`.

## Keep the package that reaches Microsoft 365

The endpoint returns the channel manifest package as a ZIP. That makes it useful in agent application lifecycle management (ALM) workflows where the published package matters as much as the editable agent:

- Export the package before and after a release, then compare the contents
- Save each production package to a versioned SharePoint document library
- Capture a known-good package before changing channels, authentication, or actions
- Attach the package to a release record for review or incident analysis
- Include the agent schema when a downstream check needs it

A scheduled flow can inventory agents, call **Download Agent Channel Manifest** for each selected agent, and write the output directly to SharePoint or OneDrive. Keep the binary output out of string variables so the ZIP stays intact.

For an interactive MCP workflow, ask the agent to find the target first:

```text
User: List the agents in the production environment.

Agent:
  1. list_agents { environmentId: "<production-environment-id>" }
  2. Presents names, IDs, owners, harnesses, and publish states

User: Download the M365 channel manifest for Contoso Support.

Agent:
  3. download_agent_channel_manifest {
       environmentId: "<production-environment-id>",
       botId: "<contoso-support-agent-id>",
       channelName: "M365",
       includeAgentSchema: true
     }
```

Discovery stays separate from the download, so the user can confirm the named agent before retrieving its package.

## Binary downloads now share one path

The connector already downloaded evaluation snapshots. v1.2 moves snapshots and channel manifests onto one binary handler, with the same behavior for both:

- ZIPs up to 4 MB return to an MCP caller as a base64 `resource`
- Larger ZIPs return metadata and direct the caller to the REST action
- Power Automate receives the binary response without the MCP inline limit
- The file name comes from `Content-Disposition`, with a generated fallback

The 4 MB ceiling keeps large base64 payloads out of an agent conversation. Use the REST action in a flow when a package exceeds it, and send the action output straight to storage.

File names also get stricter handling. A service response header eventually becomes part of an MCP resource URI, so the connector no longer trusts that value as-is. It:

1. Removes directory components
2. Replaces characters that can break a URI
3. Forces a `.zip` extension
4. Caps the name at 120 characters
5. Falls back to `agent-channel-manifest-M365.zip` when the header is missing or malformed

The same checks now protect evaluation snapshot names.

## Read a 403 before checking the IDs

Microsoft's REST reference documents the request and `200` response but doesn't list error responses for this operation. Live testing exposed an important order of operations: authorization runs before identifier validation.

Without `CopilotStudio.MakerOperations.Read`, the service returned `403 Forbidden` for both an invalid channel and a nonexistent agent. A 403 therefore doesn't prove the agent ID or channel is wrong.

Read `innererror.code` and `innererror.message` first. An `InsufficientDelegatedPermissions` response names the accepted delegated permissions. Grant `CopilotStudio.MakerOperations.Read`, consent again, and retry before troubleshooting the identifiers.

This permission is also used for reading evaluation test sets, test runs, and snapshots. Starting an evaluation needs `CopilotStudio.MakerOperations.ReadWrite`, while the administrative operations use their own permission family.

## Two live-API fixes ship with the update

The source on `main` reports MCP server version `1.2.1` because testing found two defects after the channel export was added.

### Environment names appear in the picker again

The environment management API returns `displayName`, `type`, `state`, and `url` at the top level. The connector expected a nested `properties` object, so the environment picker showed raw GUIDs when that object was absent.

The parser now checks the flat response first and keeps a nested fallback for older response shapes.

### Agent inventory retries one transient 400

The undocumented `resourcequery` endpoint can intermittently return:

```text
400 Bad Request
"KQLOM format is wrong or it cannot be null"
```

Testing reproduced the response with a byte-for-byte identical payload that had succeeded moments earlier. The connector now retries that specific error up to three times with a short backoff. It also retries `429` and `5xx` responses, while unrelated `400` responses still fail immediately.

This matters beyond inventory. `List Agents`, the agent picker, `find_containment_candidates`, and `contain_agents` all depend on the same query.

## Update the connector

Replace `REPLACE_WITH_CLIENT_ID` in `apiProperties.json`, then validate and update the existing connector:

```powershell
ppcv "./Copilot Studio Bots"

pac connector update `
    --connector-id 00000000-0000-0000-0000-000000000000 `
    --api-definition-file apiDefinition.swagger.json `
    --api-properties-file apiProperties.json `
    --script-file script.csx
```

Keep `--script-file`. The MCP tool, binary handling, dropdown fix, and inventory retry all run through `script.csx`.

Existing flows keep their actions. The new channel manifest action appears with the evaluation, inventory, containment, identity migration, and administrative actions after the update.

## Resources

- [Copilot Studio Bots v1.2 source](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Bots)
- [v1.2 commit](https://github.com/troystaylor/SharingIsCaring/commit/c9b0ab6f6f45b4193f81d651074833750852649e)
- [Download Agent Channel Manifest](https://learn.microsoft.com/rest/api/power-platform/copilotstudio/agent-channels/download-agent-channel-manifest)
- [Original Copilot Studio Bots post](/power%20platform/custom%20connectors/mcp/2026-08-20-copilot-studio-bots-connector.html)
- [Copilot Studio Bots v1.1](/power%20platform/custom%20connectors/mcp/2026-08-27-copilot-studio-bots-v1-1-entra-agent-id-migration.html)
