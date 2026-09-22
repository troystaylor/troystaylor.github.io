---
layout: post
title: "Fabric ontology in one custom MCP connector"
date: 2026-09-22 09:00:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Microsoft Fabric, Ontology, Custom Connectors, MCP, Copilot Studio, Power Automate, OAuth, OBO]
description: "Fabric Ontology is a Power Platform custom connector that pairs the ontology REST API with the ontology MCP endpoint, decodes base64 definition payloads, and turns 202 responses into readable bodies."
---

Microsoft Fabric ontology (preview) ships two things worth connecting to: a REST API for managing ontology items and their definitions, and an MCP server that exposes one ontology to an agent. [Fabric Ontology](https://github.com/troystaylor/SharingIsCaring/tree/main/Fabric%20Ontology) puts both in a single Power Platform custom connector, on one host, one app registration, and one connection.

| Surface | What it does | Who uses it |
|---|---|---|
| REST API | Create, list, read, update, and delete ontology items and their definitions | Power Automate flows, makers, ALM pipelines |
| MCP server | Exposes one ontology item to a Copilot Studio agent over Model Context Protocol | Copilot Studio generative orchestration |

## Why the two surfaces belong together

The ontology MCP endpoint is addressed per item:

```
https://api.fabric.microsoft.com/v1/mcp/dataPlane/workspaces/{workspaceId}/items/{ontologyItemId}/ontologyEndpoint
```

Those GUIDs have to be literals in the swagger path. An operation carrying `x-ms-agentic-protocol` must not declare a `parameters` key, and Copilot Studio rejects the operation if one is present. The MCP side is pinned to a single ontology as a result.

That's where the REST operations start paying for themselves. `List Workspaces` and `List Ontologies` hand you the two GUIDs to paste in, with dropdowns, instead of reading them out of a portal URL. After setup they keep working for definition round-trips, ALM, and provisioning.

## Fourteen operations

Seven cover ontology items themselves:

| Operation | Method | Path |
|---|---|---|
| List ontologies | GET | `/v1/workspaces/{workspaceId}/ontologies` |
| Create ontology | POST | `/v1/workspaces/{workspaceId}/ontologies` |
| Get ontology | GET | `/v1/workspaces/{workspaceId}/ontologies/{ontologyId}` |
| Update ontology | PATCH | `/v1/workspaces/{workspaceId}/ontologies/{ontologyId}` |
| Delete ontology | DELETE | `/v1/workspaces/{workspaceId}/ontologies/{ontologyId}` |
| Get ontology definition | POST | `/v1/workspaces/{workspaceId}/ontologies/{ontologyId}/getDefinition` |
| Update ontology definition | POST | `/v1/workspaces/{workspaceId}/ontologies/{ontologyId}/updateDefinition` |

Six more exist to feed them. `List Workspaces`, `List Folders`, `List Lakehouses`, and `List Lakehouse Tables` populate dropdowns and supply data binding sources. `Get Operation State` and `Get Operation Result` poll long running operations.

The fourteenth is `Invoke Fabric Ontology MCP`, the JSON-RPC endpoint above.

## Dropdowns instead of GUID copy-paste

Each dependent picker passes its parent through `x-ms-dynamic-values.parameters`, so choosing a workspace refilters everything below it:

```
List Workspaces ──▶ workspaceId
                      ├──▶ List Ontologies  ──▶ ontologyId
                      ├──▶ List Folders     ──▶ rootFolderId
                      └──▶ List Lakehouses  ──▶ lakehouseId ──▶ List Lakehouse Tables
```

`List Lakehouse Tables` is the exception. Table names belong in the body of an entity type data binding, at `sourceTableProperties.sourceTableName`, and Swagger 2.0 dynamic values can't populate a nested body property inside an array. Run it as its own action and read the names off the result.

## Definitions arrive readable

Fabric returns and accepts ontology definitions as base64 parts:

```json
{ "path": "definition.json", "payload": "e30=", "payloadType": "InlineBase64" }
```

`script.csx` removes the encode and decode steps on both sides. On read, each part gains a `payloadText` field holding the decoded JSON, with the original `payload` preserved. A part whose payload isn't valid base64 is left alone rather than failing the call. On write, supply readable JSON in `payloadText` and the script encodes it into `payload` and sets `payloadType`.

A definition round-trip becomes: get definition, edit `payloadText`, update definition. No base64 actions in the flow.

## A 202 with an empty body is still useful

`Create Ontology`, `Get Ontology Definition`, and `Update Ontology Definition` can return **202** with nothing in the body and everything in the headers. Power Automate can't read those headers off a connector response, so the script builds a body from them:

```json
{
  "status": "Accepted",
  "operationId": "0acd697c-1550-43cd-b998-91bfbfbd47c6",
  "location": "https://api.fabric.microsoft.com/v1/operations/0acd697c-1550-43cd-b998-91bfbfbd47c6",
  "retryAfter": 30
}
```

Poll `Get Operation State` with that `operationId` until `status` is `Succeeded`, then call `Get Operation Result`.

One detail matters if you fork the script. In some regions Power Platform delivers `Context.OperationId` base64 encoded, so the script handles both forms. Drop that decoding and the definition and LRO transformations quietly stop running in affected regions while calls still return 200.

## The scope that separates ontology from data agents

Register an Entra app for a single tenant and add these delegated permissions, then grant admin consent:

| Scope | Needed for |
|---|---|
| `Item.ReadWrite.All` | Create, update, and both definition operations |
| `Item.Read.All` | Get ontology, and item metadata reads during MCP `tools/list` |
| `Item.Execute.All` | The ontology MCP data-plane endpoint |
| `Workspace.Read.All` | List workspaces, ontologies, lakehouses, and folders |
| `Lakehouse.Read.All` | List lakehouse tables |

`Item.Execute.All` is easy to miss. A Fabric data agent uses `DataAgent.Execute.All`; ontology and Power BI semantic model endpoints use `Item.Execute.All`. Leave it out and every REST operation works while the MCP endpoint returns 403.

Two more auth settings decide whether connections behave. Set the OAuth tenant to your tenant GUID rather than `common`, which causes intermittent per-user failures against the Fabric data-plane endpoints. For on-behalf-of single sign-on, preauthorize **Azure API Connections** (`fe053c5f-3692-4f14-aef2-ee34fc081cae`) under **Expose an API** → **Authorized client applications** on an `access_as_user` scope.

The connector requests `https://api.fabric.microsoft.com/.default`, so it inherits whatever is consented on the app registration. Adding a scope later means re-consenting *and* recreating connections, because a connection caches its token audience.

## Deploy it

```powershell
cd "Fabric Ontology"

pac connector create `
  --environment <YOUR_ENVIRONMENT_ID> `
  --api-definition-file apiDefinition.swagger.json `
  --api-properties-file apiProperties.json `
  --script-file script.csx
```

`--script-file` is required. The connector declares `scriptOperations`, and omitting the script fails deployment with `InvalidScriptDefinitionUrlWithNonNullOperations`.

A returned connector ID means the record was written, not that the definition arrived intact. Download it back and confirm 14 operations, the dynamic dropdowns, and a matching `script.csx`:

```powershell
pac connector download --connector-id <id> --outputDirectory ./verify
```

Read the generated redirect URL from that download at `properties.connectionParameters.token.oAuthSettings.redirectUrl` and register it on the app registration. The URL encodes both the connector name and the environment, so dev and prod produce two different values and both need registering.

Then point the MCP operation at a real ontology. Create a connection, run `List Workspaces` and `List Ontologies` in the Test tab, and replace `WORKSPACE_ID` and `ONTOLOGY_ITEM_ID` in the MCP path before redeploying. Both GUIDs also appear in the Fabric portal URL when the ontology is open:

```
https://app.fabric.microsoft.com/groups/<workspace-ID>/ontologies/<ontology-item-ID>
```

## Test the MCP side before wiring an agent

In the Test tab with **Raw Body** on, send an initialize call:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": { "name": "power-platform-test", "version": "1.0.0" }
  }
}
```

Expect HTTP 200 with `result.protocolVersion` and `result.serverInfo`, then follow with `tools/list`. The operation ID is not an MCP method: `InvokeMCP` is the Power Platform operation, while `method` in the body must be `initialize`, `tools/call`, or `tools/list`.

In Copilot Studio, add the connector as a tool, select **Invoke Fabric Ontology MCP**, enable generative orchestration, and publish. Keep the tool on user authentication. Ontology honors Fabric RBAC, and a shared maker connection would show every user the maker's view of the data.

## What it can't do

One connector serves one ontology on the MCP side. Ten ontologies means ten connectors, or ten copies of the MCP operation with different literal paths. The REST operations stay fully parameterized and cover every ontology in the tenant from one connection.

There are no unattended MCP scenarios either. Delegated auth means an autonomous agent fired by a schedule has no signed-in user and no identity for the data-plane call. Service principals and managed identities work for the REST operations, so ALM automation is fine.

Ontology items, the ontology MCP server, and the lakehouse tables API are all in preview, with no SLA and endpoint shapes that can change.

## Resources

- [Fabric Ontology connector source](https://github.com/troystaylor/SharingIsCaring/tree/main/Fabric%20Ontology)
- [Ontology items REST API](https://learn.microsoft.com/rest/api/fabric/ontology/items)
- [Ontology definition structure](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/ontology-definition)
- [Consume ontology as an MCP server](https://learn.microsoft.com/fabric/iq/ontology/how-to-use-ontology-mcp-server)
- [Fabric REST API scopes](https://learn.microsoft.com/rest/api/fabric/articles/scopes)
- [Configure OBO authentication for custom connectors](https://learn.microsoft.com/microsoft-copilot-studio/advanced-custom-connector-on-behalf-of)
