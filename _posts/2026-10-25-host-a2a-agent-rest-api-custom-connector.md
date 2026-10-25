---
layout: post
title: "Host an A2A agent for any REST API in a custom connector"
date: 2026-10-25 14:55:00 -0400
categories: [Power Platform, Custom Connectors]
tags: [A2A, Agent-to-Agent, Copilot Studio, Custom Connectors, Power Automate, REST API, PAC CLI, Microsoft Entra ID]
description: "Power A2A Template v2 is a new implementation, separate from v1: a custom connector with a script.csx that hosts an Agent2Agent (A2A) agent for a REST API with no A2A support. Define skills in C#, then use them as a native agent in Copilot Studio and as typed actions in Power Automate."
---

Most REST APIs don't speak the [Agent2Agent (A2A) protocol](https://a2a-protocol.org/). Copilot Studio can add an A2A agent, but it needs an agent to add.

[Power A2A Template v2](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20A2A%20Template%20v2) is that agent. Despite the version number, v2 is a new implementation, not an update to the [first Power A2A Template](/power%20platform/custom%20connectors/2026-05-05-agent-to-agent-a2a-connector-work-iq.html). It lives in its own folder with its own script and operations, and it doesn't replace v1. It's a custom Power Platform connector whose `script.csx` hosts the agent for you. You define skills in the script. The script routes each message to a skill, the skill calls your API, and the answer goes back as an A2A task.

Copilot Studio adds the connector under **Agents → Add agent**. Power Automate calls the same skills with typed inputs.

## v2 is a new implementation, not an upgrade

The [first Power A2A Template](/power%20platform/custom%20connectors/2026-05-05-agent-to-agent-a2a-connector-work-iq.html) is a client for an agent that already speaks A2A. v2 is the other half: it hosts the agent. The two solve different problems, so there's no migration path. You can't upgrade a v1 connector to v2, and a flow built on v1 actions doesn't carry over. Deploy v2 as a separate connector, and keep v1 where you call an existing agent.

| | v1 | v2 |
|---|---|---|
| Role | Client that forwards to a remote A2A agent | Hosts the agent for a REST API |
| Copilot Studio | MCP tools | Native A2A agent (`InvokeA2A`) |
| Power Automate | Send, get, list, and cancel tasks, push configs | Send Message, Run Skill, List Skills, Test Routing, Get Agent Card |
| Skills | None | Defined in the script, with typed arguments and confirmation |

To call an agent that already exists, use v1. v2 has no proxy mode, no MCP endpoint, and no task or push-notification operations, because a hosted agent finishes every task in one call.

If you only need one fixed API call, a plain connector action is simpler. v2 pays off when you want the orchestrator to delegate a whole area of an API to one agent, with skills, clarifying questions, and a card that describes what the agent can do. For an agent that already exists but needs Entra ID or PKCE sign-in, see the [A2A Connector Template post](/power%20platform/custom%20connectors/2026-10-06-a2a-connector-template-copilot-studio.html).

## How a message becomes an API call

1. A message arrives from Copilot Studio, a flow, or any A2A client that calls the connector.
2. The script picks a skill and works out its arguments.
3. If an argument is missing or a value isn't acceptable, the agent asks. If the skill changes data, the agent asks for confirmation.
4. The skill calls your API with the connection's `Authorization` header.
5. The result goes back as an A2A task with a Markdown answer and structured data.

## Try the demo first

The `demo` folder holds a product-catalog demo for [DummyJSON](https://dummyjson.com), a free API with no sign-in. DummyJSON simulates writes and saves nothing, so every skill is safe to run.

```powershell
.\Deploy-PowerA2A.ps1 -Environment <YOUR_ENVIRONMENT_ID> -Demo DummyJson
```

`-Demo` swaps the demo's skills into a temporary copy of `script.csx` and deploys that. The released script contains no demo. Try "Get product 12", "Find phones", "Is the API working?", and "Set the price of product 12 to 19.99". Add `-DryRun` to build and inspect the connector files without deploying.

## Define skills

Everything you edit is at the top of `script.csx`:

| Section | What it holds |
|---|---|
| **1. Agent settings** | The agent's name and description, and your API's base URL |
| **2. Your skills** | `RegisterHostedSkills`, where you define what the agent can do |
| **3. Advanced settings** | The signing key, limits, retries, the intent resolver, and Application Insights |

Everything below section 3 is the framework. Start with section 1:

```csharp
private const string HOST_AGENT_NAME = "Your API Agent";
private const string HOST_AGENT_DESCRIPTION = "Describe what your API does and which requests the agent should handle.";
private const string HOST_API_BASE_URL = "https://api.example.com";
```

The description is what the Copilot Studio orchestrator reads to decide when to use the agent, so write it for that. The deploy script copies the name, the description, and your API's host into the connector definition, so you don't edit `apiDefinition.swagger.json`.

Here's a skill in full:

```csharp
_skills.Add(new HostedSkill("get_order", "Get order")
    .Describe("Looks up one order by its number.", "Where is order 1042?", "Show me order A-77")
    .Match(@"\border\s+#?(?<orderId>[A-Za-z0-9-]+)")
    .Arg("orderId", "The order number", true, "Which order number should I look up?")
    .Handle(async call =>
    {
        var order = await HostCallApiAsync(HttpMethod.Get,
            HOST_API_BASE_URL + "/orders/" + Uri.EscapeDataString(call.Arg("orderId")));
        return HostResult.FromRecord(order, new[] { "number", "customer.name:Customer", "status" },
            "Order " + call.Arg("orderId"));
    }));
```

| Method | Purpose |
|---|---|
| `Describe` | What the skill does, and example requests. They appear in the agent card. |
| `Match` | A case-insensitive regular expression. Each named group becomes an argument. |
| `Arg` | Declares an argument. If a required argument is missing, the agent asks the prompt. |
| `Confirm` | Asks the user to confirm before the handler runs |
| `Returns` | Declares the shape of the skill's data, so flows show its fields as dynamic content |
| `Default` | Handles messages that no skill's pattern matches |
| `Handle` | Calls your API and returns a `HostResult` |

The template ships with six starter skills: `get_item`, `search_items`, `create_item`, `update_item_status`, `delete_item`, and `check_connection`. Keep the ones that fit your API and delete the rest. Run `check_connection` first. If the connector can't reach your API or the sign-in is wrong, the answer says what the API returned, for example `The API returned 401`.

A built-in `help` skill answers "help" and "what can you do?" with a list of your skills and an example for each, without calling your API. Set `HOST_INCLUDE_HELP` to `false` to remove it.

## Control how messages are routed

The first rule that applies wins:

1. **A data part with a skill ID**, for callers that know your skills and want exact control
2. **A pending skill**, when the message answers a question or a confirmation
3. **A pattern match**, the first skill whose `Match` pattern matches the text
4. **The intent resolver**, if you've turned it on
5. **The default skill**, or the only skill

If none apply, the task comes back `rejected` with a list of what the agent can do. Register skills that change data before skills with broad patterns, because the first match wins.

**Test Routing** shows which skill a phrase reaches, with its arguments and whether it needs confirmation, without calling your API. Run it with the phrases your users say, including the awkward ones, then adjust your patterns.

### Add a model as a fallback

Patterns are exact but narrow. The optional intent resolver sends the message and your skill catalog to a chat-completions endpoint, which picks the skill and pulls out its arguments. Set `HOST_INTENT_RESOLVER` to `off`, `fallback`, or `always`. Use `fallback` unless you have a reason not to. Patterns stay fast and predictable, and the model handles only what they miss.

The model sees the message text and your skill catalog. It never sees your API's data, the user's token, or earlier messages. It can only pick a skill you defined, every value it supplies goes through your argument rules, and `Confirm` still applies. If the endpoint is slow or down, the connector falls back to patterns.

## Ask questions and confirm writes

When a required argument is missing or a value isn't acceptable, the task comes back with state `input_required` and the question in its status message. The connector keeps no state, so it stores the arguments collected so far in the task ID. The client sends that task ID back with the answer.

Declare a type, choices, a default, or limits in the `Arg` lambda:

```csharp
.Arg("status", "The new status", a => a.OneOf("open", "closed", "archived"))
.Arg("limit", "How many results to return", a => a.OfType("integer").Between(1, 25).DefaultTo("10").Optional())
.Arg("email", "The customer's email", a => a.Matches(@"^[^@\s]+@[^@\s]+$", "That doesn't look like an email address."))
```

When a value fails a check, the agent says why and asks again, and your handler doesn't run. The same rules fill in the **Run Skill** form: choices become dropdowns, and optional arguments appear under advanced options.

Add `Confirm` to any skill that changes data:

```csharp
.Confirm("Set item {itemId} to {status}?")
```

**Yes** runs the handler. **No** cancels with state `canceled`, and your API isn't called. A model that routes the message can choose a write skill, but it can't skip the confirmation.

### Signed task IDs

Because questions and confirmations travel in the task ID, the connector signs them. The ID can't be edited, expires after 15 minutes, and only works for the context it came from. The signature uses `HOST_SIGNING_KEY` plus the caller's identity: the tenant and user claims for an Entra ID token, or the whole `Authorization` header otherwise.

`Deploy-PowerA2A.ps1` generates a random signing key on every deployment. Pass `-SigningKey` to keep the same one so confirmations that are waiting survive a redeployment. A skill with `Confirm` fails with a message naming the missing key instead of running unconfirmed.

## Shape the answer

A skill returns a `HostResult` with text for the model, structured data for flows, or both:

| Builder | Result |
|---|---|
| `HostResult.FromText(text)` | Text only |
| `HostResult.FromData(json, text)` | Data, with optional text |
| `HostResult.FromRows(json, columns, maxRows, title, rowsPath)` | A Markdown table and trimmed data for a list |
| `HostResult.FromRecord(json, columns, title)` | A Markdown list for one record |

`FromRows` puts only `maxRows` rows into the table and the data, and adds "Showing 10 of 240." when it trims. That keeps answers small, which matters because everything a skill returns goes into the model's context on every later turn.

`HostCallApiAsync` handles the rest of the API call. It retries a 429 up to twice, honoring `Retry-After`, and retries a GET after a 502, 503, or 504. It doesn't retry a write after a server error, because the write might have gone through. Errors come back as one short line, such as `The API returned 404: Product not found`, so a long error page doesn't fill the model's context.

## Choose how users sign in

Pick a sign-in option with `-Auth` when you deploy:

| Option | Use when | Parameters |
|---|---|---|
| **None** | The API is public, or you're trying a demo | `-Auth None` |
| **API key** | Each user enters a key when they create a connection | `-Auth ApiKey -ApiKeyHeader X-Acme-Key` |
| **Microsoft Entra ID** | Entra ID protects your API | `-Auth EntraId -ClientId <id> -ResourceUri api://your-api -Scope <permission>` |

```powershell
.\Deploy-PowerA2A.ps1 -Environment <YOUR_ENVIRONMENT_ID> -Auth None
```

The script builds the connector in a temporary folder, deploys it with [PAC CLI](https://aka.ms/PowerAppsCLI), and deletes the folder. It never changes the files in your repository, so keys and secrets don't end up in a file you commit. Add `-ConnectorId <id>` to update an existing connector.

With Entra ID, create an app registration with the delegated permission your API requires and a client secret. After the first deployment, the script prints the connector's redirect URL. Register it on the app, then run the script again with `-ConnectorId` and `-ClientSecret` to store the secret.

## Use the agent in Copilot Studio

`InvokeA2A` is marked `x-ms-agentic-protocol: a2a-1.0`, so Copilot Studio treats it as a native A2A agent.

1. Open Copilot Studio in the same environment, open your agent, and go to **Agents → Add agent**.
2. Select your connector by its `info.title`. Don't select **A2A agent**, which creates a separate connector.
3. Create a connection, then select **Add and configure**.

Copilot Studio copies the title and description once, when you add the agent, so later connector updates don't change an agent you've already added. When you test, ask for the task, not the tool.

Copilot Studio sends A2A 0.3 requests. `InvokeA2A` also accepts A2A 1.0 and answers in the version the caller used.

## Use the skills in Power Automate

**Run Skill** is the most direct way to call your API from a flow. Pick the skill, and the **Inputs** form changes to match it. It never asks follow-up questions, a failed skill fails the action, and it doesn't ask for confirmation because you chose the inputs. Don't expose a write skill to people who shouldn't run it.

**Send Message** takes natural language. Check **State** before you rely on the answer:

| State | Meaning |
|---|---|
| `completed` | The skill ran |
| `input_required` | The agent needs an answer. Call **Send Message** again with the answer, the same **Context ID**, and the **Task ID**. |
| `failed` | Your API returned an error. **Status Message** has the detail. |
| `rejected` | No skill matched |
| `canceled` | The user declined the confirmation |

Add `.Returns(sampleJson)` to a skill so the fields of **Data** appear as dynamic content, and you don't need **Parse JSON**.

## What a hosted agent doesn't do

A connector returns one buffered response and keeps no state between calls, so:

- Every task finishes in the call, within the connector's two-minute limit. `GetTask` and `CancelTask` return `-32001 Task not found`.
- Streaming returns error `-32004`, so use `SendMessage`.
- Push notifications return `-32003`, and there's no extended agent card.

For work that takes longer, have the skill start the job and return a job ID, and add a second skill that checks it.

## Test before you deploy

`tests\Run-Tests.ps1` compiles `script.csx` with a fake connector runtime and a fake API, and runs about 200 checks across six variants. It builds in a temporary folder, restores only from your local NuGet cache, and never contacts nuget.org. After you replace the starter skills, replace the `shipped` checks in `tests\Program.cs` with checks for your own.

When you deploy for real, work through this checklist in order. Each step tests one thing, so a failure tells you where the problem is:

1. **Get Agent Card** confirms that the connector deployed and your skills load.
2. **Send Message** with "Is the API working?" confirms the connector reaches your API and the sign-in works.
3. **Test Routing** shows which skill each phrase reaches.
4. **Run Skill** on a read skill checks that the form and **Data** fields match.
5. **Send Message** on a write skill checks that **State** is `input_required`, then send **Yes**.
6. **Copilot Studio** confirms the orchestrator delegates to the agent.

## Resources

- [Power A2A Template v2 source](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20A2A%20Template%20v2)
- [Power A2A Template (v1)](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20A2A%20Template)
- [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)
- [Connect an agent over A2A in Copilot Studio](https://learn.microsoft.com/microsoft-copilot-studio/add-agent-agent-to-agent)
- [Use custom code in a custom connector](https://learn.microsoft.com/connectors/custom-connectors/write-code)
