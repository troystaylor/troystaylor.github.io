---
layout: post
title: "Read Dataverse hierarchies in one call with the Dataverse Catalog Tree MCP connector"
date: 2026-09-18 09:00:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Dataverse, Custom Connectors, MCP, Copilot Studio, Power Automate, Hierarchy]
description: "Dataverse Catalog Tree is a custom MCP connector that returns a whole Dataverse subtree in one call, with explicit accounting for anything it left out, so agents stop inventing branches."
---

Ask an agent to walk a product catalog, an org chart, or a territory hierarchy in Dataverse and it will get the first two levels right and then start making things up. That isn't a model quality problem. It's what happens when a tree has to be assembled through a generic query tool.

[Dataverse Catalog Tree](https://github.com/troystaylor/SharingIsCaring/tree/main/Dataverse%20Catalog%20Tree) is a custom MCP connector for recursive 1:N hierarchies in Dataverse. It serves two consumers from one traversal engine.

| Audience | Surface | What they get |
|---|---|---|
| Copilot Studio | MCP endpoint at `/mcp` | Nine catalog tools over JSON-RPC 2.0 |
| Power Automate, Power Apps | Typed operations | Named actions with schemas, IntelliSense, and dynamic dropdowns |

## Why chaining produces hallucinations

Traversing a tree through a generic query tool means the model chains calls, and at every hop it supplies a relationship name, a lookup column, and a GUID. Each of those is a chance to invent something plausible. By the fourth hop the model is reasoning about records it never read.

The worse failure is quieter. A branch that was never expanded looks exactly like a branch that ends. The agent reports a leaf node with total confidence, and nothing in the response contradicts it.

This connector removes the chaining. One call returns the finished subtree, assembled server-side, with explicit accounting for anything left out.

## Two shapes, both supported

| Shape | Example | Configuration |
|---|---|---|
| Self-referencing, one table pointing at itself | `Category` with a `Parent Category` lookup | None. The connector finds the self-referencing relationship in metadata. |
| Heterogeneous levels, a different table per level | `Category` > `Subcategory` > `Product` | Pass `levels` as an ordered relationship path, such as `tst_category_subcategories>tst_subcategory_products`. |

Call `describe_catalog` once and it returns the exact `levelsPath` string to use. Paste that into the agent instructions and the value is fixed from then on.

If you get to choose the data model, use a self-referencing table and mark the relationship hierarchical. That unlocks the single-query strategy below and makes arbitrary depth free.

## Three traversal strategies, chosen automatically

`strategy=auto` picks the cheapest correct engine. Force one when you're testing.

| Strategy | Requests | When `auto` picks it | Trade-off |
|---|---|---|---|
| `hierarchy` | 1 data call for the entire subtree, any depth | Self-referencing relationship marked hierarchical, and a root id was supplied | Can't apply a `filter`. Dataverse caps hierarchical recursion at 100 levels. |
| `levels` | One batched call per level | Everything else, the general case | Costs a call per level, but keeps full control of ordering, paging, and limits. |
| `expand` | 1 call | Never automatically. Opt in. | Dataverse forbids `$top` and `$orderby` anywhere in a query containing a nested one-to-many `$expand`, so result size can't be bounded. |

The `levels` engine batches by level, not by node. All parents at a depth go out in one request using a chunked `or` filter, so a 500-node tree four levels deep costs about five calls instead of 500.

## What stops the hallucinations

**One call, no chaining.** `get_catalog_tree` returns the whole subtree. The model never assembles a path across turns.

**Errors name the valid values.** An unknown relationship returns the real ones, so the model corrects itself from data instead of guessing again:

```json
{
  "error": "unknown_relationship",
  "message": "'product_lines' is not a relationship from 'tst_category'.",
  "providedValue": "product_lines",
  "validValues": [
    { "value": "tst_category_subcategories", "description": "Children in tst_subcategory via tst_parentcategoryid" }
  ],
  "hint": "Retry with one of these relationship schema names."
}
```

**Unexpanded branches are counted, not hidden.** Every node carries `childCount` and `hasMoreChildren`. When depth runs out, one extra batched query counts the children at the boundary, so the agent says "12 more below Seattle" instead of inferring a leaf.

**Truncation is explicit.** `stats.truncated` and `stats.truncationReason` (`depthLimit`, `nodeBudget`, `pageLimit`, `rootLimit`) mean an incomplete tree can't pass for a complete one. Exhausting the per-invocation Dataverse call budget is deliberately not a truncation. It raises a `request_budget_exceeded` error, because a tree that stopped growing for an internal reason should never be presented as data.

**Identity flows one way.** Every node returns `id`, `table`, and `path`. Write operations validate GUIDs and reject anything malformed with `invalid_id`, so a fabricated identifier fails loudly instead of silently targeting nothing.

**`search_catalog` grounds names in records.** It resolves user-typed text to real ids with full paths, which is the step that belongs before any traversal or write.

**Cycles can't run away.** A visited-set guards traversal, `move_catalog_node` refuses a parent that sits below the node, and `cyclesDetected` reports anything skipped.

## The outline format is the one to ask for

Set `format` to `tree` (default), `flat`, `outline`, or `all`. Indented text with ids costs a fraction of the tokens of nested JSON and gives the model nothing to reassemble:

```text
Contoso Catalog Root (account, bdce4b86-dcb2-f111-aaae-70a8a5b2ff44)
  Contoso East (account, c3ce4b86-dcb2-f111-aaae-70a8a5b2ff44)
    Contoso East - Boston (account, 99005488-dcb2-f111-aaae-6045bd061c5d)
  Contoso West (account, cda82982-dcb2-f111-aaae-6045bd061c5d)
    Contoso West - Seattle (account, c8ce4b86-dcb2-f111-aaae-70a8a5b2ff44) [3 more children not expanded]
```

The full response carries the definition and the traversal stats alongside the roots:

```json
{
  "definition": { "mode": "selfReference", "hierarchical": true, "levelsPath": "tst_category_parent", "levels": [ ] },
  "stats": {
    "nodeCount": 7, "maxDepthReached": 3, "depthRequested": 5,
    "truncated": false, "truncationReason": "", "cyclesDetected": 0,
    "strategy": "hierarchy", "dataverseRequests": 2, "elapsedMs": 380
  },
  "roots": [ { "id": "...", "label": "Contoso Catalog Root", "childCount": 2, "hasMoreChildren": false, "children": [ ] } ]
}
```

`stats` is there so a person debugging a flow can see which engine ran and what it cost, without turning on telemetry.

## Nine operations

| MCP tool | Typed operation | Purpose |
|---|---|---|
| `describe_catalog` | `GET /catalog/describe` | Read the hierarchy shape from metadata and get the exact `levelsPath`. |
| `get_catalog_tree` | `GET /catalog/tree` | Return a whole subtree. The main operation. |
| `get_node_children` | `GET /catalog/children` | One level of children, for drilling into a truncated branch. |
| `get_node_ancestors` | `GET /catalog/ancestors` | Breadcrumb from a node up to its root. |
| `search_catalog` | `GET /catalog/search` | Find nodes by name across levels, with full paths. |
| `create_catalog_node` | `POST /catalog/node` | Create a record and attach it to a parent. |
| `update_catalog_node` | `POST /catalog/node/update` | Rename a node or set other columns. Parent lookups are rejected here. |
| `move_catalog_node` | `POST /catalog/node/move` | Reparent a node, with a cycle guard. |
| `delete_catalog_node` | `POST /catalog/node/delete` | Delete a node, with explicit child handling. |

Two more operations, `GET /metadata/tables` and `GET /metadata/childrelationships`, populate the dynamic dropdowns in Power Automate.

## Deleting refuses rather than improvises

A destructive operation is the worst place for an agent to fill in a blank. `onChildren` controls what happens when the node isn't a leaf:

| Mode | Behavior |
|---|---|
| `refuse` (default) | Fails with `node_has_children`, reporting the exact count and offering the other two modes in `validValues`. Nothing changes. |
| `reparent` | Attaches the children to the node's own parent, or detaches them to become roots if the node was a root, then deletes the node. |
| `cascade` | Deletes the node and every descendant, deepest first. |

`reparent` and `cascade` need a self-referencing catalog. For heterogeneous levels they return `child_handling_unavailable`, because the children of a node live in a different table from that node's parent.

Two more refusals protect against half-finished destruction. A cascade whose subtree exceeds `maxNodes` raises `subtree_too_large`, and one that would run past the 80-call budget raises `delete_budget_exceeded`. Both are checked before any record is deleted.

## Limits

Defaults are conservative, and every one is a parameter.

| Limit | Default | Maximum |
|---|---|---|
| `depth` | 3 | 10 |
| `maxNodes` | 500 | 5000 |
| `rootTop`, roots returned when no `id` is given | 50 | 500 |
| Children per request | | 500 |
| Dataverse calls per invocation | | 80 |
| Parent ids per batched filter | 25 | |

Custom connector code has to finish within two minutes and the script has to stay under 1 MB. Both are comfortable here, since the `hierarchy` strategy costs two calls regardless of tree size.

## Three Dataverse Web API behaviors worth recording

Each of these was confirmed by request rather than by documentation.

A nested `$expand` on a collection-valued 1:N does work, to at least three nested levels. The documented restriction to many-to-one applies to N:N relationships.

It's rejected on a key-addressed URL. `accounts(<id>)?$expand=children($expand=children(...))` returns "Only many-to-one relationships are supported for nested expansion", while the same expand against `accounts?$filter=accountid eq <id>` succeeds. The `expand` strategy uses the collection form for this reason.

`$top` and `$orderby` are forbidden anywhere in a query containing a nested one-to-many `$expand`, including at the top level. That's why `expand` is never the automatic choice: the result size can't be bounded.

## Deploy it

Set `host` in `apiDefinition.swagger.json` to your environment, such as `contoso.crm.dynamics.com`. It ships as the placeholder `org.crm.dynamics.com`. Set `AzureActiveDirectoryResourceId` and `resourceUri` in `apiProperties.json` to the matching `https://<org>.crm.dynamics.com` value, and replace `[YOUR_CLIENT_ID]` with your Entra app registration client id. Leave `[YOUR_REDIRECT_URL]` alone, because the platform generates and overwrites it on deploy.

```powershell
pac connector create `
    --api-definition-file .\apiDefinition.swagger.json `
    --api-properties-file .\apiProperties.json `
    --script-file .\script.csx
```

Then read the generated redirect URL back and register it on the app registration, or OAuth consent fails:

```powershell
pac connector download --connector-id <id> --outputDirectory ./verify
# properties.connectionParameters.token.oAuthSettings.redirectUrl
```

That URL encodes both the connector name and the environment, so dev and prod produce two different URLs and both need registering.

## Using it from Copilot Studio

Add the connector to the agent as an MCP server and Copilot Studio lists the tools automatically. Add it once. If the same connector is added both as an MCP server and as individual connector actions, the agent sees two overlapping sets of the same capability, and wrong-tool selection is the failure mode this design exists to prevent.

An agent instruction that matches how the tools are built:

```text
The catalog is stored in Dataverse. Use search_catalog to turn any name the user mentions
into a record id before doing anything else. Use get_catalog_tree with format=outline to
read structure. Never invent ids, table names or relationship names. If a tool returns
validValues, retry with one of them. If a node reports hasMoreChildren, say how many
children were not shown rather than listing or guessing them.
```

In Power Automate the typed operations show up as ordinary actions. `GetTree` with `format=flat` returns an array that feeds straight into Apply to each.

## Verified behavior

The connector was built and tested against a live Dataverse environment using a four-level self-referencing account hierarchy and a three-level `account` > `contact` > `task` chain: 76 assertions covering both shapes, all three strategies, depth and node-budget truncation, boundary child counts, search path resolution, ancestor breadcrumbs, create, rename, reparent, all three delete modes, cycle rejection on move, MCP protocol handling, and every structured error path. It was then deployed with `pac connector create` to confirm it compiles in the connector runtime.

Telemetry is off by default. Set `APP_INSIGHTS_ENABLED` to `true` and fill in `APP_INSIGHTS_KEY` in `script.csx` to turn it on. Events cover MCP tool calls, structured catalog errors, and unhandled exceptions. Telemetry failures are swallowed and never affect the operation.

## Resources

- [Dataverse Catalog Tree connector source](https://github.com/troystaylor/SharingIsCaring/tree/main/Dataverse%20Catalog%20Tree)
- [Query hierarchical data](https://learn.microsoft.com/power-apps/developer/data-platform/query-hierarchical-data)
- [Define and query hierarchically related data](https://learn.microsoft.com/power-apps/maker/data-platform/define-query-hierarchical-data)
- [Write code in a custom connector](https://learn.microsoft.com/connectors/custom-connectors/write-code)
- [Model Context Protocol specification](https://modelcontextprotocol.io/)
