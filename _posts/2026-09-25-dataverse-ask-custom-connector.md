---
layout: post
title: "Ask Dataverse questions in plain language from Power Automate and Copilot Studio"
date: 2026-09-25 16:00:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Dataverse, Work IQ, Custom Connectors, MCP, Copilot Studio, Power Automate, OAuth]
description: "Dataverse Ask is a Power Platform custom connector for the Dataverse Ask APIs, with typed actions for flows and apps, table and model pickers, and an MCP endpoint that gives Copilot Studio agents five tools over your business data."
---

The [Dataverse Ask APIs](https://learn.microsoft.com/power-apps/developer/data-platform/ask/) (preview) take a question in plain language and return the rows that answer it, a summary, and links to the source records. [Dataverse Ask](https://github.com/troystaylor/SharingIsCaring/tree/main/Dataverse%20Ask) wraps them in a custom connector with typed actions for Power Automate and Power Apps, and an MCP endpoint that a Copilot Studio agent can reason with.

No table relationships, column logical names, or query syntax on your side. You define which tables can answer, then ask.

## Not the Web API

The Ask APIs live at `/api/iq/v1.0/` and are deliberately not an OData service. There's no metadata document, and no `$select`, `$filter`, or `$expand`. Use the Web API when you need precise create, retrieve, update, delete, or query operations. Use this connector when the input is a question.

The connector makes one Web API call, to read your table list for the **Tables** picker, because the Ask API has no table endpoint of its own. That's the only place `/api/data/` appears.

## Semantic models define what can be answered

A semantic model names the Dataverse tables that can answer a question. Create one, then ask questions against it. The service decides how to answer from those tables, and returns only data the signed-in user is allowed to read.

**List semantic models** returns more than the models you create here, and the `source` property tells them apart.

| Kind | Created by | This connector can |
|---|---|---|
| API model | **Create semantic model**, `source` of `SemanticModelAPI` | Create, list, delete, ask against |
| Provisioned or app-associated model | Auto-provisioned when Copilot over Dataverse is enabled, or owned by a model-driven app, bot component, or agent | List, ask against |

You can't delete a model you didn't create through this API, and the maker portal can't create a brand-new one — creation is what this connector adds. Run **List semantic models** with **Include app and agent usage** set to `botinfo` to see which apps and agents depend on a model before you change or delete it.

## Five operations and three pickers

| Operation | Method | Description |
|---|---|---|
| Invoke Dataverse Ask MCP | `POST /mcp` | MCP endpoint for Copilot Studio |
| List semantic models | `GET /api/iq/v1.0/semanticmodel` | The models available in this environment |
| Create semantic model | `POST /api/iq/v1.0/semanticmodel` | Associate a unique name with one or more tables |
| Delete semantic model | `DELETE /api/iq/v1.0/semanticmodel/{id}` | Delete a model by ID |
| Ask a question | `POST /api/iq/v1.0/ask` | Submit a question against a model |

A sixth operation, **List tables**, is marked internal and backs the **Tables** picker.

| Field | Shows | Sends |
|---|---|---|
| **Semantic model name** on Ask | Model name | Model name |
| **Semantic model** on Delete | Model name | Model ID |
| **Tables** on Create | `Account (account)` | `account` |

The Delete picker matters most: that operation is keyed by ID while everything else is keyed by name, so choosing from the list saves a lookup.

Table **logical names** are the only names Create accepts — `account`, `contact`, `opportunity`. Display names, entity set names, and collection names are rejected. The picker handles that for you, filtering out private and intersect tables, and falling back to the logical name when a table has no localized label.

Include only the tables relevant to the questions the model answers. Creating a model indexes those tables, and that index consumes Dataverse database storage. You can see how much in the **DataverseSearch** table, counted against database storage on the **Summary** and **Dataverse** tabs.

## Five tools for an agent

Add the connector to a Copilot Studio agent and the MCP endpoint advertises:

| Tool | Purpose |
|---|---|
| `list_semantic_models` | Find the available models and their exact names |
| `ask_dataverse` | Ask a question against a model |
| `list_tables` | Find table logical names, with an optional search term |
| `create_semantic_model` | Create a model over a set of tables |
| `delete_semantic_model` | Delete a model created through this API |

The tool descriptions steer the agent to call `list_semantic_models` before `ask_dataverse`, because the model name has to match exactly, and `list_tables` before `create_semantic_model`, because table names must be logical names. Failures come back as tool results rather than protocol errors, so an agent that passes an invalid search mode is told the three valid values and retries instead of stalling.

`ask_dataverse` returns the summary, the rows, the citation links, and a `hasMore` flag. When more rows exist it also returns the paging token and tells the agent how to use it.

Try prompts such as *Which open opportunities have the highest estimated revenue?* or *Summarize the opportunities for Contoso.*

## Working with the answer

**Rows** (`rawResult`) is an array of dynamic objects. Its shape depends on the question and on the query the service generated to answer it, so there's no fixed schema and no design-time dynamic content for individual fields. Parse it with the property names you expect from the question, or run the question once and read the output to learn the shape.

**Summary**, **Citation links**, and **Rows** are all nullable. Display the summary when it's there, but don't require it before processing the rows.

Results are trimmed to the caller's Dataverse privileges. Record ownership, business unit access, sharing, and column-level security all change what comes back, so two users asking the same question can get different answers.

Search mode controls the tradeoff between speed and depth:

| Mode | Use when |
|---|---|
| `Auto` | Default. Let the service choose |
| `QuickResponse` | A faster answer matters more than depth |
| `ThinkDeeper` | The question needs deeper analysis and a longer wait is acceptable |

`ThinkDeeper` can take noticeably longer. In a flow, raise the action timeout; in an app, show progress.

Set **Row count** to cap the page size. When more rows exist, the response carries a **Paging token** — send the same question, model, search mode, and count again with that token to get the next page, and continue until the token comes back null or empty. Pass the token back exactly as returned; don't decode, edit, or construct one.

**List** and **Ask** are safe to retry after a transient failure. **Create** and **Delete** aren't, because model names must be unique. List the models first to find out whether the original request actually succeeded, and treat a missing model after an uncertain delete as a completed delete. Retry `429`, `500`, `502`, `503`, and `504`, honoring `Retry-After` when present and backing off exponentially with jitter otherwise.

## Indexing takes time

A model doesn't answer well the instant it's created. Initial generation can take **up to two hours**; later incremental changes typically settle within **30 minutes**. An Ask sent immediately after Create can return thin results or none. Models then regenerate automatically every 12 hours to pick up schema changes.

Semantic models don't support ALM. Environment copy and move operations don't carry them, and after either one an administrator has to turn the feature off and back on in the Power Platform admin center to force a restart.

## Fine-tuning a model

Answer quality comes from more than the table list. The model extracts signals from metadata you already have — table relationships, public and sub-grid views, form display names, table and column description summaries, and optionally sample data rows. Sample rows are off by default. System views such as Quick Find, Advanced Find, Associated, and Lookup are excluded, as are personal views.

Well-written table and column descriptions are the cheapest way to improve answers, because the model reads them directly.

Once a model exists, tune it on the **Semantic model** page in [Power Apps](https://make.powerapps.com):

- **Signals** — turn inferred signal types on or off, exclude sensitive tables, disable views and relationships that mislead
- **Glossary** — add acronyms, synonyms, and organization-specific vocabulary the system can't infer
- **Refresh** — trigger a manual regeneration to apply changes without waiting for the 12-hour cycle

## Deploy it

You need a Dataverse environment, and **Business Applications in Work IQ** turned on for it in the Power Platform admin center. Without that feature, every call returns `400`. The connection user also needs a security role that grants semantic model privileges: **Dataverse Search Role**, **Environment Maker**, **System Customizer**, or **System Administrator**. Ask API usage is billed through Copilot Credits.

Register an app in Microsoft Entra ID, add the delegated **Dynamics CRM → user_impersonation** permission, and add `https://global.consent.azure-apim.net/redirect` to its web redirect URIs. Copy the application ID and create a client secret.

In `apiDefinition.swagger.json`, set `host` to your environment hostname. In `apiProperties.json`, replace `[YOUR_CLIENT_ID]` with your application ID and replace `https://org.crm.dynamics.com` in both `AzureActiveDirectoryResourceId` and `resourceUri` with your environment URL. Leave `redirectUrl` as `[YOUR_REDIRECT_URL]`, since the platform substitutes the real value at deploy time.

```powershell
pac auth create --environment <your-environment-url>

pac connector create `
  --api-definition-file apiDefinition.swagger.json `
  --api-properties-file apiProperties.json `
  --script-file script.csx
```

`--script-file` is required. Without it the connector deploys, but the MCP endpoint returns nothing usable, because the script is what answers the JSON-RPC calls.

`pac` has no parameter for the client secret. Paste it in **Power Apps → Custom connectors → Dataverse Ask → Edit → Security**, or set `clientSecret` in a temporary copy of `apiProperties.json`, deploy from that copy, and delete it afterwards. Never put a secret in the file you keep.

The platform generates a redirect URL unique to this connector and environment. Read it back and register it:

```powershell
pac connector download --connector-id <connector-id> --outputDirectory ./verify
```

The value sits at `properties.connectionParameters.token.oAuthSettings.redirectUrl`. Add it to the app registration alongside the generic one. OAuth consent fails until it's registered, and a second environment produces a different URL that also needs registering.

## Test in the right order

Create a connection, then run **List semantic models** with no parameters. A `200` confirms auth, host, and feature enablement in one call, and it answers immediately without depending on indexing. An empty list is still a pass; the environment simply has no models yet.

Then run **Create semantic model** with a unique name and a couple of tables from the dropdown:

| Field | Value |
|---|---|
| Unique name | `Sales pipeline` |
| Tables | `Account (account)`, `Opportunity (opportunity)` |

A populated **Tables** dropdown is a second check on its own: it proves the connection can read table metadata.

Don't ask a question yet. Indexing starts on creation, and initial generation can take up to two hours. Come back afterwards and run **Ask a question** against `Sales pipeline` with something like *Which open opportunities have the highest estimated revenue?* Rows and a summary confirm the model is live.

To test the MCP endpoint without waiting on indexing, add the connector to a Copilot Studio agent and ask it what semantic models exist. That exercises discovery and a tool call.

## When something comes back wrong

| Symptom | Cause | Fix |
|---|---|---|
| `400` on every operation | Business Applications in Work IQ isn't enabled for the environment | Turn on the feature in the Power Platform admin center |
| `400` on Ask, other operations fine | No table in the model is one the caller may read, or the request is malformed | Check the caller's read access to the model's tables; don't retry unchanged |
| `401` on every call | Missing **Dynamics CRM → user_impersonation**, or `resourceUri` doesn't match the environment | Check the permission and both URLs in `apiProperties.json` |
| `403` on Create or Delete | The connection user has no semantic model privileges | Assign Dataverse Search Role, Environment Maker, System Customizer, or System Administrator |
| `404` on Ask | The semantic model name doesn't match | Names are exact — pick one from the dropdown |
| `404` on Delete | The model is already gone, or it belongs to an app module, bot, or agent | Models not created through this API can't be deleted here |
| `429` | More than 30 Ask requests per user per minute | Wait for `Retry-After` seconds; avoid retrying several requests in parallel |
| Sign-in fails during connection creation | The generated redirect URL isn't on the app registration | Register the downloaded value |
| Ask returns nothing just after Create | Indexing hasn't finished | Initial generation takes up to two hours; retry later |
| Answers ignore a business term or acronym | The term can't be inferred from metadata | Add a glossary entry, then regenerate the model |
| Answers got worse after a schema change | The model hasn't regenerated yet | Wait for the 12-hour cycle or trigger a manual regeneration |
| Models missing after an environment copy or move | Semantic models have no ALM support | Have an admin turn the feature off and back on to force a restart |
| No dynamic content for row fields | Rows are dynamic by design | Expected. Parse by property name, or run once to learn the shape |
| Tables dropdown is empty or errors | The connection can't read table metadata | The same **user_impersonation** permission covers it; check the user's security role |
| Agent doesn't see the tools | The connector was deployed without `--script-file` | Redeploy including the script |

Telemetry is off by default. Set `APP_INSIGHTS_ENABLED` to `true` in `script.csx` and replace `APP_INSIGHTS_KEY` with your instrumentation key to log tool calls with their outcome and failures with their error code and message. Telemetry never fails a tool call.

## Where it sits next to the others

| Connector | Use for |
|---|---|
| **Dataverse Ask** (this) | Natural-language questions over a defined set of Dataverse tables |
| **Dataverse SQL** | Precise read-only T-SQL queries against the Web API |
| **Work IQ** | Natural-language questions across Microsoft 365 — mail, meetings, documents, Teams, people |

Work IQ and Dataverse Ask complement each other. Once an administrator enables Business Applications in Work IQ, the Work IQ connector can also reach Dataverse. This connector is the direct path, and the only one that can create a semantic model.

## Resources

- [Dataverse Ask connector source](https://github.com/troystaylor/SharingIsCaring/tree/main/Dataverse%20Ask)
- [Dataverse Ask APIs](https://learn.microsoft.com/power-apps/developer/data-platform/ask/)
- [Work IQ API overview and licensing](https://learn.microsoft.com/microsoft-365/copilot/extensibility/work-iq/api-overview)
- [Manage feature settings](https://learn.microsoft.com/power-platform/admin/settings-features)
- [Write code in a custom connector](https://learn.microsoft.com/connectors/custom-connectors/write-code)
