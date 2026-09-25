---
layout: post
title: "Call Azure Functions hosted skills from Power Automate and Copilot Studio"
date: 2026-09-25 09:00:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Azure Functions, Hosted Skills, Custom Connectors, MCP, Copilot Studio, Power Automate, Azure]
description: "Azure Functions Hosted Skills is a Power Platform custom connector that calls a hosted skill on demand, returns its answer with the session and tool calls, and exposes five MCP tools to Copilot Studio agents."
---

An Azure Functions hosted skill is a unit of AI work defined in an `.agent.md` file: natural-language instructions, a trigger, and whatever tools you bind to it. Most hosted skills start themselves — a timer fires, a queue message arrives, a connector trigger sees new mail. [Azure Functions Hosted Skills](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Functions%20Hosted%20Skills) covers the other direction. It calls a skill on demand, waits for the answer, and hands it back to a flow or an agent.

Hosted skills are in [preview](https://learn.microsoft.com/azure/azure-functions/functions-hosted-skills), so endpoint names and configuration keys can still change.

## Turn on the chat API first

The built-in endpoints are off by default. Switch them on in each `.agent.md` file you want to call:

```markdown
---
name: Order Triage
description: Classifies an order problem and drafts a reply.
builtin_endpoints:
  chat_api: true
---

You classify order problems. Given a customer message, return the severity,
the responsible team, and a draft reply.
```

A skill with `builtin_endpoints` enabled needs no `trigger`. It can have both — a timer trigger for its scheduled run and a chat API for on-demand calls. `builtin_endpoints: true` is shorthand for everything: the chat API, the browser debug UI, and the runtime's own MCP surface.

The skill's slug is its file name. `order_triage.agent.md` has the slug `order_triage`, and that slug is what every operation takes. Skills can sit at the app root or in an `agents/` folder; the slug carries no folder either way.

Only built-in endpoints are reachable here. A skill whose `trigger` is `http_trigger` gets its own route, such as `/summarize`, and needs a plain HTTP action — or add `builtin_endpoints` alongside the trigger.

## Six operations

| Operation | What it does |
|---|---|
| Invoke a hosted skill | Sends a prompt and returns the response, the session it ran in, and the tools it called |
| Get session transcript | Returns the user and assistant turns in a session, oldest first |
| List dynamic workflows for a session | Lists durable workflows the skill started in a session |
| Get dynamic workflow status | Returns runtime status and, once finished, the output of one workflow run |
| List hosted skills | Lists the app's skills and the endpoints each one exposes |
| Invoke Azure Functions Hosted Skills MCP | The endpoint Copilot Studio connects to |

Both surfaces hit the same endpoints, so a skill you expose to a flow is immediately available to an agent.

## Discovery costs you a key choice

**Skill** is a dropdown, not a free-text box, filled by **List hosted skills**. That operation reads the function app's admin API, which accepts only the app's `_master` key. So the picker works on one condition:

| Key on the connection | Skill operations | Skill list |
|---|---|---|
| Host or function key | Work | Empty, with the reason in `message` |
| Master key | Work | Populated |

A host key is the least-privilege choice and costs you only the picker. You type slugs instead, and the slug is always the `.agent.md` file name without its extension. Nothing else changes. Discovery also stops working when the function app has admin isolation enabled, since the runtime itself publishes no catalogue endpoint.

## Sessions carry the conversation

Omit the session ID on the first call and the runtime mints one, returns it in `session_id`, and stores the transcript in the app's `AzureWebJobsStorage` account. Pass that value back and the skill sees everything said before. Two calls without a session ID are two unrelated conversations, even against the same skill.

In a flow, capture `session_id` from the first response and feed it into every later call in the same run. Supplying your own is fine — session IDs accept letters, digits, dots, hyphens, and underscores up to 128 characters, so a support ticket number makes a good one because it resumes the same conversation days later.

**Get session transcript** returns at most the 200 most recent turns and sets `truncated` when older ones were dropped. The skill's own memory is unaffected; only the transcript you read back is capped.

## Tool calls come back with the answer

`tool_calls` reports what the skill did to produce its response: one entry per tool, with the name, the arguments it was given, and what it returned. The `type` field reads `tool_start` even on a completed call, because the runtime merges the call and its result into a single entry on this path.

Arguments and results arrive as text, with structured values rendered as JSON. They map onto a single string column, so you can show them in an approval card or write them to a log table.

## Two minutes, and what to do about it

A Power Platform request times out at roughly 120 seconds. A skill that searches the web, runs sandboxed Python, and calls three connectors can exceed that. Two ways around it:

**Let the skill start a dynamic workflow.** Skills with `workflows.enabled: true` in their front matter return quickly with work running in the background. Poll it with **Get dynamic workflow status** until `runtime_status` leaves `Running`, then read `output`. The **Workflow ID** field is a dropdown, filled from the workflows the chosen skill started in the session you name, each labelled with its status and start time.

**Trigger the skill instead of calling it.** If nothing in the flow needs the answer, give the skill a queue or Event Grid trigger and let the function app own the run.

Stopping a workflow is not an operation here. The runtime's `cancel_workflow` and `terminate_workflow` are tools the skill holds, not HTTP endpoints, so there's nothing for a connector to call. To stop a run, send the skill a prompt in the same session asking it to cancel that workflow.

A workflow that fans out to specialist skills doesn't make those specialists visible here. Subagents are separate `.agent.md` files that usually have no `builtin_endpoints` of their own, so they won't appear in the Skill list and can't be invoked directly — which is the intent.

## Retries stop at the skill boundary

Reads — transcript, workflow list, workflow status, and skill discovery — are retried up to three times on 429, 502, 503, or 504, honoring `Retry-After` when the app sends one. A function app scaling from zero produces exactly these codes, and retrying is invisible to your flow.

Invoking a skill is never retried. A hosted skill can send mail, update a record, or start a workflow before the throttle was applied, so replaying it risks doing that work twice. A throttled invoke fails with the wait time the app asked for, and whether repeating it is safe is your call.

## Five tools for an agent

Add the connector to a Copilot Studio agent as an MCP tool and it publishes:

| Tool | Purpose |
|---|---|
| `list_skills` | Discover which hosted skills the app offers and what each supports |
| `invoke_skill` | Send a prompt to a hosted skill and get its response |
| `get_session_history` | Recall what was said earlier in a session |
| `list_session_workflows` | Check on long-running work the skill started |
| `get_workflow_status` | Read the result of one workflow run |

Every tool except `list_skills` takes an optional `agent` argument naming the skill. Omit it and the connector resolves the skill itself when the app hosts exactly one callable skill, which means a single-skill app needs no configuration at all. When the app hosts several, or the skills can't be listed, the tool returns an error telling the agent to call `list_skills` and choose. Auto-resolution needs the skill list, so it works on the same terms as discovery.

The connector also sends a short set of instructions when Copilot Studio connects: discover skills before guessing at one, carry `session_id` between turns, and poll a dynamic workflow rather than assuming the skill finished. That guidance reaches the orchestrator without you writing it into every agent.

`invoke_skill` returns `session_id` in its result, which lets an agent continue the same hosted-skill conversation across turns by passing that value back. The agent has to carry it deliberately — Copilot Studio's conversation state and the hosted skill's session are separate things.

This is worth doing when the hosted skill knows something the agent does not. A skill wired to a Connector Namespace can reach SAP, Salesforce, or a line-of-business SQL database, run model reasoning over what it finds, and return a conclusion. The agent gets one clean tool instead of a dozen raw API calls.

You don't need `builtin_endpoints.mcp: true` for any of this. That setting exposes the skill on the runtime's own MCP endpoint, which the Functions MCP extension owns and which requires a separate system key. This connector builds its MCP surface from the chat API instead, so one key covers everything and you get five tools rather than one.

Tool results are trimmed before they reach the agent. A skill that scraped a dozen pages can return more than an agent's context window holds, so oversized results have their tool-call detail shortened first and, if that isn't enough, are truncated with a note saying so. The skill's own answer is preserved, and **Invoke a hosted skill** always returns the complete payload.

## Deploy it

Deploy the function app with `chat_api` enabled on every skill you plan to call. Then collect two values from the Azure portal: the default domain from the function app's **Overview** page, such as `contoso-skills.azurewebsites.net`, and a host key from **Functions** → **App keys**. A host key works for every skill in the app. Use the `_master` key instead if you want the Skill picker populated, or scope access to one skill by copying a key from that skill's `_builtin_chat` function.

```powershell
pac connector create `
    --api-definition-file ./apiDefinition.swagger.json `
    --api-properties-file ./apiProperties.json `
    --script-file ./script.csx
```

Create a connection with the hostname and the key — those are the only two settings — and run **Invoke a hosted skill** with a slug and a prompt. A successful call returns `response`, `session_id`, and `tool_calls`.

The route prefix needs no configuration. The runtime registers its endpoints under the Functions route prefix, which defaults to `api` but is empty in the official quickstart's `host.json`. The connector tries the declared path first and retries the other layout on a 404, so both work.

`script.csx` ships with Application Insights logging off. Set `APP_INSIGHTS_ENABLED` to `true` and replace `APP_INSIGHTS_KEY` with your instrumentation key to record skill invocations, MCP tool calls, and failures. Telemetry failures are swallowed and never affect a call.

## Signing in with Microsoft Entra ID

Import `apiProperties-entra.json` instead of `apiProperties.json` to authenticate with Microsoft Entra ID. Everything else — the Swagger definition, the script, the operations — is identical. Use it when your skills set `http_auth.mode: entra`, or when your tenant disables function keys.

This path is built from the runtime's documented behavior but hasn't been exercised against a live Entra-protected app, so treat it as a starting point rather than a verified recipe. The function-key path is tested end to end.

The function app must have App Service Authentication turned on. The runtime doesn't validate tokens itself; it accepts an Entra caller only when the platform has already done that work. Register an application for the function app with an Application ID URI such as `api://<app-id>` and a `user_impersonation` scope, point App Service Authentication at it, then fill in the client ID and both Application ID URI placeholders in `apiProperties-entra.json`. After importing, read back the redirect URL the platform generated and add it to the app registration. That value is specific to the connector *and* the environment, so a connector in two environments produces two URLs.

Skill discovery is unavailable in this mode. The admin API accepts only the master key, and this configuration has no key parameter to put it in — deliberately, since the reason to run in Entra mode is usually that you don't want master keys stored in connections. Type slugs instead, and name the skill explicitly on every MCP tool call.

## Resources

- [Azure Functions Hosted Skills connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Functions%20Hosted%20Skills)
- [Azure Functions hosted skills](https://learn.microsoft.com/azure/azure-functions/functions-hosted-skills)
- [Hosted skills reference](https://learn.microsoft.com/azure/azure-functions/functions-hosted-skills-reference)
- [Dynamic workflows](https://learn.microsoft.com/azure/azure-functions/functions-hosted-skills-dynamic-workflows)
- [Azure Functions Agents Runtime](https://azure.github.io/azure-functions-agents-runtime/)
