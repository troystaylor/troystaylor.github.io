---
layout: post
title: "Find, evaluate, and contain Copilot Studio agents with one connector"
date: 2026-08-20 10:00:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Copilot Studio, Custom Connectors, MCP, Power Automate, Evaluations, Governance, Quarantine, Agent Inventory, GitHub Copilot Harness, Power Platform API]
description: "A Power Platform custom connector covering all 13 Bots operations in the Power Platform API — maker evaluation, quarantine, consent bypass, reassignment, and deletion — plus a tenant-wide inventory that flags which agents run on the expensive GitHub Copilot harness."
---

The [Bots operation group](https://learn.microsoft.com/en-us/rest/api/power-platform/copilotstudio/bots) in the Power Platform API covers two jobs that belong together: measuring whether a Copilot Studio agent answers well, and containing it when it doesn't. [Copilot Studio Bots](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Bots) is a custom connector for all 13 documented operations, with MCP support for agents and REST actions for flows.

It also answers the question the Bots API can't: which agents are worth containing. The API quarantines an agent by ID but exposes no harness, template, or recognizer field, so the connector reads the Power Platform resource query API for a tenant-wide inventory that flags GitHub Copilot harness agents — the ones billing 100 to 500+ Copilot Credits per task.

This replaces an earlier connector, [Copilot Studio Evaluations](/power%20platform/custom%20connectors/2026-04-17-copilot-studio-evaluations-mcp-connector.html), which covered five operations from the same API group and stopped at measurement. A nightly quality check that quarantines a regressed agent needs the administrative half too, so all 13 operations now share one connection.

## What the 13 operations do

| Operation | Method | Endpoint |
|---|---|---|
| Get Agent Test Sets | GET | `{base}/api/makerevaluation/testsets` |
| Get Agent Test Set Details | GET | `{base}/api/makerevaluation/testsets/{testSetId}` |
| Start Agent Evaluation | POST | `{base}/api/makerevaluation/testsets/{testSetId}/run` |
| Get Agent Test Runs | GET | `{base}/api/makerevaluation/testruns` |
| Get Agent Test Run Details | GET | `{base}/api/makerevaluation/testruns/{testRunId}` |
| Download Agent Evaluation Snapshot | GET | `{base}/api/makerevaluation/testruns/{testRunId}/snapshot` |
| Get Agent Quarantine Status | GET | `{base}/api/botQuarantine` |
| Quarantine Agent | POST | `{base}/api/botQuarantine/SetAsQuarantined` |
| Release Agent From Quarantine | POST | `{base}/api/botQuarantine/SetAsUnquarantined` |
| Get Connector Consent Bypass | GET | `{base}/api/connectorConsentBypass` |
| Set Connector Consent Bypass | PUT | `{base}/api/connectorConsentBypass` |
| Reassign Agent Owner | POST | `{base}/api/botAdminOperations/reassign` |
| Delete Agent | DELETE | `{base}/api/botAdminOperations` |

`{base}` is `/environments/{environmentId}/bots/{botId}` on `https://api.powerplatform.com/copilotstudio`, with `api-version` pinned to `2024-10-01`.

The first six are maker operations — anyone with access to the agent can run them. The last seven need Power Platform or Dynamics 365 administrator rights, and the API returns `403` to everyone else no matter how the connector or DLP policy is configured. The inventory reads tenant-wide resources, so it needs administrator rights too.

Each operation is also an MCP tool: `get_test_sets`, `get_test_set_details`, `start_evaluation`, `list_test_runs`, `get_run_details`, `download_evaluation_snapshot`, `get_quarantine_status`, `quarantine_agent`, `unquarantine_agent`, `get_connector_consent_bypass`, `set_connector_consent_bypass`, `reassign_agent`, and `delete_agent`. Three more tools — `list_agents`, `find_containment_candidates`, and `contain_agents` — come from the inventory rather than the Bots API, for 16 in total.

Tooling reports a third number. `ppcv` and PAC CLI count 17 operations in the OpenAPI definition: the 13 Bots operations, `List Agents`, two internal dropdown sources, and the JSON-RPC endpoint. The Power Automate action list shows 16, since the internal two are hidden. That the MCP count also lands on 16 is a coincidence — the REST side includes two dropdown operations that aren't tools, and the MCP side includes two containment tools that have no REST equivalent.

## The metrics are booleans, not scores

`get_run_details` returns results nested three levels deep:

```text
run
├── state              Pending | Running | Completed | Failed
├── totalTestCases
└── testCaseResults[]
    ├── testCaseId
    ├── state          Passed | Failed | Error
    ├── errorReason    populated when the case failed
    ├── aiResultReason AI-generated explanation of the outcome
    └── metricsResults[]
        ├── type       e.g. GeneralQuality, Hallucination
        └── result
            ├── abstention    boolean
            ├── relevance     boolean
            └── completeness  boolean
```

Abstention, relevance, and completeness are true or false per test case. There's no percentage or confidence value anywhere in the response, so a quality figure has to be aggregated yourself — "relevance false in 3 of 20 cases" rather than "85% relevant." Models left to their own devices report these as percentages, which is why the sample system prompt says not to.

Read `abstention: true` as neutral. An agent that declines an out-of-scope question is behaving correctly. And `aiResultReason` is the field worth quoting to a human, since it explains why a case landed where it did.

## Guards on the destructive operations

Handing an agent a tool that permanently deletes a copilot needs a gate. Three are built in:

- **`delete_agent` refuses to run without `confirm: true`.** The API has no undelete, so an ambiguous instruction can't cost you an agent. The REST `Delete Agent` action has no such guard — treat it carefully in flows.
- **`contain_agents` accepts no filter and requires `confirm: true`.** It takes an explicit list of agents, so no single call can quarantine a population the caller hasn't already seen and named.
- **`reassign_agent` converts `204 No Content` to `{ "status": 204, "succeeded": true }`.** An empty body reads like a failure to a calling model, which then retries a reassignment that already worked.

Quarantine is the reversible option and usually the right first move. A quarantined agent stays editable for makers and administrators; only end users lose access. Enabling connector consent bypass goes the other way — it removes an end user safeguard, so audit which connections the agent uses before turning it on.

## Snapshots are binary

`download_evaluation_snapshot` returns a ZIP. The connector reads the response as bytes rather than text, because string handling corrupts the archive. Files 4 MB or smaller come back as an MCP `resource` with a base64 `blob`. Larger ones return metadata and a pointer to the REST operation, which is the better path anyway — stream the archive to SharePoint or OneDrive in a flow instead of through a conversation. The file name comes from `Content-Disposition`, falling back to `evaluation-snapshot-{testRunId}.zip`.

## Which agents run the expensive harness

`list_agents` returns `isCLIAgent` for every agent in the tenant:

| `isCLIAgent` | `harness` | Cost profile |
|---|---|---|
| `"true"` | GitHub Copilot | 100–500+ Copilot Credits per task, billed regardless of M365 Copilot licensing |
| `"false"` | Standard or Copilot Chat | 1–20 credits per run, no charge for licensed employees |
| `"unknown"` | unknown | Not reported — investigate, don't assume |

Three things to know before building on it:

- **It's a string, not a boolean.** A flow condition testing it as a boolean silently never matches.
- **`"unknown"` is not `"false"`.** An absent field isn't evidence of the cheap harness, and that's the direction you least want a cost report to guess in.
- **`"false"` covers two harnesses.** It can't separate Standard from Copilot Chat, so the `harness` label says `Standard or Copilot Chat` rather than inventing precision the source doesn't have.

To confirm a single agent definitively, clone it with the VS Code extension. The GitHub Copilot harness projects `template: cliagent-1.0.0` and `recognizer.kind: CLICopilotRecognizer`, against `default-2.1.0` and `GenerativeAIRecognizer` for Standard.

## Plan, then apply

Discovery and containment are separate tools on purpose.

`find_containment_candidates` is read-only and quarantines nothing. It returns each matching agent with the `reasons` it qualified, plus `skippedUnknownHarness` and `skippedAlreadyQuarantined` counts so you can see what it declined to touch.

| Parameter | Default | Effect |
|---|---|---|
| `environmentId` | all | Scope to one environment |
| `requireTenantWide` | `true` | Only agents shared with the entire tenant |
| `requireNeverPublished` | `false` | Only agents that have never been published |
| `includeUnknownHarness` | `false` | Include agents whose harness wasn't reported |

`contain_agents` takes an explicit array of `{ environmentId, botId }` pairs and `confirm: true`. Failures are per-agent, so one `403` doesn't abandon the rest of the batch, and the result reports `succeeded`, `failed`, and a per-agent breakdown.

```text
User: "Find GitHub Copilot harness agents shared with everyone that were never published"
Agent:
  1. find_containment_candidates { requireNeverPublished: true }
     → 2 candidates, each with reasons
       [githubCopilotHarness, sharedWithEntireTenant, neverPublished]
     → skippedUnknownHarness: 1   (reported, not contained)
  2. Presents them with owners and environments
User: "Quarantine both"
  3. contain_agents { agents: [ {...}, {...} ], confirm: true }
     → succeeded: 2
```

The three composite tools break the usual error convention. They report outcomes inside the payload and set `isError` only when the whole operation failed, so a batch where some agents were quarantined and others rejected returns `isError: false` with the failures itemized in `results`. Read `succeeded` and `failed`, not the flag.

Two limits shape the inventory. It pages 1,000 rows at a time and stops after 10 pages, setting `truncated: true` rather than quietly returning a partial estate — scope to an environment if you hit it. And `SkipToken` doesn't work: the service returns one but it never advances, so the connector pages with `Skip` offsets ordered by a unique tiebreaker to keep the window stable.

The inventory reads `resourcequery` at `api-version=2022-03-01-preview`, which returns the resource provider's raw property bag. `isCLIAgent` isn't in the published reference and can change shape or disappear without notice. Use it for reporting and chargeback triage, not as a hard enforcement gate.

## Pickers, and what can't be one

Environment ID, Agent ID, Test Set ID, and Test Run ID are all dropdowns in the Power Automate and Logic Apps designers, each cascading from the one before it.

The environment picker runs on an internal operation at `/metadata/environments` that the script rewrites to `https://api.powerplatform.com/environmentmanagement/environments`. That endpoint reports the environment identifier inconsistently, sometimes as a bare GUID in `name` and sometimes as an ARM-style path in `id`, so the connector normalizes both to the bare GUID the Bots operations expect.

The agent picker works the same way from `/metadata/agents`, backed by the inventory query. Because it already knows the harness, it appends `(GitHub Copilot)` to those entries — you see which agent is the expensive one at the moment you pick it.

Owner ID isn't a picker. Resolving users means Microsoft Graph, a different host, and a connector can't reach across hosts to back a dropdown.

Dropdowns are a designer convenience. MCP tools receive raw IDs, so an agent calling `quarantine_agent` still needs both GUIDs.

## The flow that motivated the merge

```text
1. Trigger: Scheduled (daily at 2 AM)
2. Get Agent Test Sets
3. For Each test set (Apply-to-each concurrency OFF)
   4. Start Agent Evaluation
   5. Poll Get Agent Test Run Details until state is Completed or Failed
   6. Count test cases where relevance or completeness is false
   7. Condition: failing count above your threshold
      8. Quarantine Agent
      9. Download Agent Evaluation Snapshot and save to SharePoint
      10. Email the agent owner with the failing cases and aiResultReason
```

Concurrency stays off for a reason. An agent runs one evaluation at a time, and `Start Agent Evaluation` returns `422` if a run is already in progress. Poll each run to completion before starting the next, and treat `Failed` as terminal so the loop can't spin forever. Test sets also have to be Active — inactive sets come back from `Get Agent Test Sets` but won't run.

A second flow reclaims ownership drift: `List Agents` weekly with a blank environment ID, check each `ownerId` against Entra ID, and reassign anything owned by a disabled account to a governance service account.

A third reports cost exposure monthly — `List Agents` across the tenant, filter `isCLIAgent` equal to `'true'`, and mail a table of display name, environment, owner, and `lastPublishedAt`. Filter `'unknown'` separately and label those "harness unresolved," never Standard.

Three details catch flow authors out. `List Agents` returns an object, not an array, so apply-to-each over `agents` and check `truncated` before treating the result as the whole estate. An empty `lastPublishedAt` means never published, not an unknown date. And `channels` and `reasons` are string arrays — flatten with `join(item()?['reasons'], ', ')` for a table or email body.

## Status codes

| Status | Meaning | What to do |
|---|---|---|
| 400 | Malformed body | Check `adminConsentBypass` is a boolean and `NewOwnerAadUserId` is a valid Entra object ID |
| 401 | Token invalid or expired | Reauthorize the connection and confirm the app registration has Power Platform API permission |
| 403 | Caller lacks tenant admin rights | Sign in as a Power Platform or Dynamics 365 administrator |
| 404 | Agent, environment, test set, or run not found | A 404 on snapshot usually means a wrong run ID or a run that never completed |
| 422 | An evaluation run is already in progress | Wait for `Completed` or `Failed`, then retry |
| 500 | Service-side failure on reassign | Retry; if it persists, confirm the new owner has access to the environment |
| Empty agent dropdown | The inventory query failed or returned nothing | The picker swallows errors to avoid breaking the designer. Call `List Agents` directly to see the real one |
| `List Agents` returns 400 | The resource query was rejected | Usually a schema change in the preview API. Confirm you can still read agents in PPAC, then check whether the query shape changed |

MCP tool calls surface these as `isError: true` with the status code in the message text, so an agent can read and explain the failure. JSON-RPC errors (`-32601`, `-32602`) are reserved for unknown methods and malformed tool calls.

## Setup

Register an Entra application with Power Platform API permissions and the `https://api.powerplatform.com/.default` scope, then put the client ID in `apiProperties.json`. Deploying with `REPLACE_WITH_CLIENT_ID` still in place succeeds, but no connection can be created, so set the real value first.

Validate with `ppcv "./Copilot Studio Bots"`, then deploy. `--script-file` is mandatory:

```powershell
pac connector create `
    --api-definition-file apiDefinition.swagger.json `
    --api-properties-file apiProperties.json `
    --script-file script.csx
```

Omitting it fails with `InvalidScriptDefinitionUrlWithNonNullOperations`, because `apiProperties.json` declares `scriptOperations` and the service won't accept them with no script to route them to. A second failure, `CustomScriptProvisioningFailed` or `FindAndAssignFunctionApp`, means the region has no unassigned function app for custom code — creating a new script-enabled connector draws from that pool, while updating an existing one reuses its assignment and usually still works.

Without the script the 13 Bots operations still pass through untouched, but the MCP endpoint, both dropdowns, `List Agents`, and the containment tools don't.

Evaluation with an authenticated agent connection needs an MCS Connection ID. Open the Connections page in Power Automate, select the Microsoft Copilot Studio connection, and copy `mcsConnectionId` from the URL.

Application Insights telemetry ships in `script.csx`, disabled by default. Set `APP_INSIGHTS_ENABLED = true`, drop in your instrumentation key, and redeploy to log every MCP request, tool call, and exception. That gives you an audit trail for the administrative tools:

```kusto
customEvents
| where name == "MCP_ToolCall"
| summarize Count = count() by tostring(customDimensions.tool), tostring(customDimensions.status)
```

## Related connectors

| Connector | Coverage |
|---|---|
| [Power Platform Admin](/power%20platform/custom%20connectors/mcp/2026-08-06-power-platform-admin-agent-inventory.html) | Environment settings, and the original tenant-wide agent inventory that `List Agents` is ported from |
| [Copilot Studio Analytics](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Analytics) | Dataverse conversation transcripts and session analytics |
| [Microsoft 365 Copilot Package Management](/power%20platform/custom%20connectors/mcp/2026-08-07-microsoft-365-copilot-package-management-agent-registry.html) | Package catalog: block, unblock, and reassign |

## Resources

- [Copilot Studio Bots connector on GitHub](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Studio%20Bots)
- [Power Platform API Bots operations](https://learn.microsoft.com/en-us/rest/api/power-platform/copilotstudio/bots)
- [Agent evaluations in Copilot Studio](https://learn.microsoft.com/microsoft-copilot-studio/analytics-agent-evaluation-overview)
- [Quarantine noncompliant agents with the Power Platform API](https://learn.microsoft.com/microsoft-copilot-studio/admin-api-quarantine)
