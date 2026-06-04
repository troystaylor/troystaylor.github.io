---
layout: post
title: "Agent Governance Toolkit connector adds ACS lifecycle policies"
date: 2026-06-04 11:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Agent Governance, ACS, OWASP, MCP, Copilot Studio, Custom Connectors, Power Platform, Security]
description: "Update to the Agent Governance Toolkit custom connector adds Agent Control Specification (ACS) lifecycle policies — three new operations covering manifest load, intervention evaluation, and payload transform across 8 lifecycle points with warn, escalate, and transform verdicts."
---

The [Agent Governance Toolkit MCP connector I shipped in April](https://troystaylor.com/power%20platform/custom%20connectors/2026-04-07-agent-governance-toolkit-mcp-connector.html) gave Copilot Studio agents and Power Automate flows seven per-tool governance checks: evaluate action, check compliance, score trust, detect injection, log audit, check circuit breaker, and scan MCP tool. Allow or deny, one tool call at a time.

This update adds the [Agent Control Specification (ACS)](https://github.com/microsoft/agent-governance-toolkit/tree/main/policy-engine) — Microsoft's lifecycle-aware policy layer. A single YAML manifest now declares what to validate at each of 8 intervention points across `input → model → tool → output`, with verdicts that go beyond allow/deny: `warn`, `escalate`, and `transform`.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Agent%20Governance%20Toolkit).

## What's new

Three new operations and three new MCP tools, all calling the ACS endpoints on the Container App:

| Operation | MCP tool | Path |
|-----------|----------|------|
| `LoadAcsManifest` | `load_manifest` | `POST /api/acs/manifest/load` |
| `EvaluateIntervention` | `evaluate_intervention` | `POST /api/acs/evaluate` |
| `TransformPayload` | `transform_payload` | `POST /api/acs/transform` |

That brings the connector to 11 REST operations and 10 MCP tools. The original per-tool layer still works exactly as before — ACS is additive.

## The 8 intervention points

ACS evaluates a snapshot of the agent state at any of these points in the agent loop:

| Point | When the agent calls it |
|-------|------------------------|
| `agent_startup` | Once when the agent boots |
| `input` | User message arrives |
| `pre_model_call` | Before invoking the LLM |
| `post_model_call` | After the LLM returns |
| `pre_tool_call` | Before invoking a tool |
| `post_tool_call` | After a tool returns |
| `output` | Before sending a response to the user |
| `agent_shutdown` | Once when the agent terminates |

A single manifest can declare rules at any combination of these points. Tool name is required for `pre_tool_call` and `post_tool_call`; other points work off the snapshot alone.

## Beyond allow and deny

The per-tool layer returns a binary `allowed: true | false`. ACS returns one of five verdicts:

- `allow` — proceed as normal
- `deny` — block the action and return the policy reason
- `warn` — proceed but emit a warning the agent can surface
- `escalate` — route to a human approver or higher-trust agent
- `transform` — rewrite the payload before continuing (output redaction, input sanitization)

`TransformPayload` is the operation that surfaces the rewritten body when the verdict is `transform`. It returns the original payload for `allow` and `warn`, and the verdict for `deny` and `escalate`.

## A redaction example

Say you want to scrub PII from any model output before it reaches the user. With the per-tool layer you'd need to call `check_compliance` after the model returns and write the redaction logic yourself. With ACS, the manifest does both — detection and rewrite — in one call.

The agent calls `transform_payload` at the `output` intervention point with the model's response as the snapshot. ACS evaluates the manifest rule, detects the PII, and returns the redacted body. The agent forwards that body to the user without ever seeing the original.

The same pattern works for input sanitization (`input` point), tool argument rewriting (`pre_tool_call`), and post-tool result filtering (`post_tool_call`).

## When to use ACS vs. the per-tool layer

| Per-tool layer | ACS |
|----------------|-----|
| Allow/deny on tool name | warn, escalate, transform verdicts |
| Simple YAML rules per check | Composable manifests across the full loop |
| One snapshot point per call | 8 lifecycle intervention points |
| Sub-millisecond | Sub-millisecond per intervention, stateless |

Both layers live behind the same Container App, share the same API key, and respond at sub-millisecond latency. Use the per-tool layer when you just need an allow/deny on a single tool call. Reach for ACS when you need warn/escalate/transform verdicts, multi-point coverage, or a single declarative manifest for the whole agent loop.

## Loading a manifest

Manifests are YAML files in `MANIFEST_DIR` inside the Container App. Call `LoadAcsManifest` once at agent startup to register one:

```json
{
  "path": "redaction-policy.yaml",
  "id": "redaction"
}
```

The ID defaults to the filename without extension if you omit it. Use that ID in every subsequent `EvaluateIntervention` and `TransformPayload` call.

## Evaluating an intervention

`EvaluateIntervention` takes the manifest ID, the intervention point, and a snapshot of the current agent state:

```json
{
  "manifestId": "redaction",
  "interventionPoint": "output",
  "snapshot": {
    "output": {
      "text": "The customer's email is jane@example.com"
    }
  },
  "mode": "enforce"
}
```

The response carries the verdict and any policy metadata. Set `mode` to `evaluate_only` for dry runs that log what the policy would have done without actually enforcing it — useful when rolling out a new manifest in production.

## Default state and enabling the live engine

The three ACS endpoints are scaffolded in the container out of the box:

- `LoadAcsManifest` works immediately — it registers manifests and parses syntax
- `EvaluateIntervention` and `TransformPayload` return HTTP 501 with a setup pointer until the `AgentControlSpecification` .NET SDK is wired

To enable live ACS evaluation, build the SDK nupkg from the upstream toolkit (it's not on nuget.org yet) and flip a marker file. The toolkit ships a PowerShell script for it:

```powershell
cd "Agent Governance Toolkit/container-app"
.\scripts\build-acs-nupkg.ps1
```

This produces `local-packages/AgentControlSpecification.0.3.1-beta.0.nupkg` and writes a `local-packages/.acs-enabled` marker that flips the csproj into ACS-enabled mode automatically on the next container build. Requires Docker Desktop in Linux container mode. See [container-app/manifests/README.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Agent%20Governance%20Toolkit/container-app/manifests/README.md) for the details.

When `LoadAcsManifest` returns `"sdkBound": true`, the live Rust core is loaded inside the container and `EvaluateIntervention` / `TransformPayload` start returning real verdicts instead of 501.

## Smoke-testing ACS after deployment

Once the SDK is wired and the new image is pushed:

```powershell
$fqdn = "agentgov-api.<your-env>.westus3.azurecontainerapps.io"
$h = @{ 'X-API-Key' = $env:AGT_API_KEY; 'Content-Type' = 'application/json' }

Invoke-RestMethod -Method POST "https://$fqdn/api/acs/manifest/load" `
  -Headers $h `
  -Body '{"path":"example.yaml","id":"example"}'

Invoke-RestMethod -Method POST "https://$fqdn/api/acs/evaluate" `
  -Headers $h `
  -Body '{"manifestId":"example","interventionPoint":"input","snapshot":{"input":{"text":"hello"}}}'
```

If both calls return verdicts (not 501), the live engine is running.

## Deployment notes

Everything from the original deployment guide still applies: provision the resource group, generate the API key, deploy the Bicep template, push the container image, and re-run the deploy to wire the FQDN. The toolkit was validated end-to-end on Azure Container Apps in `westus3`. If `eastus2` returns `AKSCapacityHeavyUsage`, retry in `westus3`.

Cost remains in the $7–25/month range for typical workloads (Container App consumption + ACR Basic + Log Analytics).

## OWASP Agentic AI Top 10 coverage

The new ACS layer reinforces the same OWASP risks the per-tool layer covered. ACS adds depth at points the per-tool layer couldn't reach:

- ASI-01 Goal hijacking — `input` and `pre_model_call` interventions catch prompt injection before the model sees it
- ASI-05 Insecure output handling — `output` intervention rewrites or blocks unsafe model output
- ASI-07 Unsafe inter-agent communication — `pre_tool_call` and `post_tool_call` validate arguments and results
- ASI-09 Human-agent trust deficit — `escalate` verdict routes high-risk actions to humans without writing custom escalation code

## Try it yourself

The updated connector and Container App source are in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Agent%20Governance%20Toolkit):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Agent%20Governance%20Toolkit/apiDefinition.swagger.json) — OpenAPI specification (11 operations, 10 MCP tools)
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Agent%20Governance%20Toolkit/apiProperties.json) — Connector metadata
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Agent%20Governance%20Toolkit/script.csx) — Connector script
- [container-app/](https://github.com/troystaylor/SharingIsCaring/tree/main/Agent%20Governance%20Toolkit/container-app) — .NET 8 minimal API source and Dockerfile
- [deploy/main.bicep](https://github.com/troystaylor/SharingIsCaring/blob/main/Agent%20Governance%20Toolkit/deploy/main.bicep) — Azure deployment template
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Agent%20Governance%20Toolkit/readme.md) — Full documentation

## Resources

- [Original connector release post (April 2026)](https://troystaylor.com/power%20platform/custom%20connectors/2026-04-07-agent-governance-toolkit-mcp-connector.html)
- [Microsoft Agent Governance Toolkit (GitHub)](https://github.com/microsoft/agent-governance-toolkit)
- [Agent Control Specification (policy engine)](https://github.com/microsoft/agent-governance-toolkit/tree/main/policy-engine)
- [Introducing the Agent Governance Toolkit](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/) by Imran Siddique
- [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
