---
layout: post
title: "Build approval and form cards for Copilot Studio without Adaptive Cards"
date: 2026-11-17 18:45:00 -0500
categories: [Power Platform, MCP, Copilot Studio]
tags: [MCP Apps, Copilot Studio, Custom Connectors, Adaptive Cards, Fluent 2, Power MCP, Microsoft 365 Copilot, PAC CLI]
description: "Power MCP Cards Template is a custom connector script that serves approval, form, table, and status cards as MCP Apps, with no remote MCP server to host. Copilot Studio preview chat now renders MCP apps, announced at Ignite today. Here's what the template includes and how to deploy it."
---

Microsoft announced [MCP apps in Copilot Studio](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/mcp-apps) at Ignite today. An MCP server can now declare a UI for a tool, and the host renders it in the conversation. Copilot Studio preview chat and Microsoft 365 Copilot support it. Teams and web chat don't (yet).

The [Power MCP Cards Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Cards%20Template) puts that to work for the cases where you'd otherwise build an Adaptive Card: approvals, forms, tables, and job status. One custom connector script serves the MCP endpoint, the tools, and the card HTML. There's no remote MCP server to host. The script answers the MCP requests and serves each card as a `ui://` resource, so there's no web app, storage account, or CDN to deploy either.

## How a card works

A tool declares its UI in `_meta.ui.resourceUri`, which points at a `ui://` resource. The template's flow looks like this:

1. The agent calls a `show_*` tool.
2. The host reads the card's HTML from the connector with `resources/read` and renders it in a sandboxed frame.
3. The host sends the tool result to the card, and the card draws itself from `structuredContent`.
4. When the user acts, the card calls a card-only tool on the connector, then sends the agent a message describing what the user did.

The agent continues from that message. The card doesn't repeat chat features, and the model writes the reply.

## What's in the template

| Tool | What it does |
| --- | --- |
| `show_approval` | Approve and Reject buttons, request details, an optional comment, and an optional required comment on reject |
| `show_form` | Text, email, number, date, multi-line, choice, and checkbox fields with required-field and format validation |
| `show_table` | Inline preview of the first five rows. Expand to search, sort, and see up to 500 rows, with optional row selection |
| `show_status` | Status badge, progress bar, and step list, with an optional Refresh button |
| `submit_decision` | Records the approval decision from the card, or from chat |
| `submit_form` | Records the form values from the card, or from chat |
| `refresh_status` | Fetches the latest job status for the Refresh button, or when the user asks |

The connector folder has four files: `apiDefinition.swagger.json`, `apiProperties.json`, `script.csx`, and a readme.

## Fallback when no card appears

Every `show_*` tool returns a text summary next to the card data. The summary tells the agent the card is shown and to keep its reply short. If the user says the card didn't appear, the agent presents the details in chat, collects the answer, and records it with the matching `submit_*` tool.

That means the connector works on a host that can't render MCP Apps. The card is the primary experience, and the conversation still finishes without it.

The `submit_*` and `refresh_status` tools are visible to the model for that reason. If your host honors `_meta.ui.visibility`, set `AppToolsVisibleToModel` to `false` in `script.csx` to hide them.

## Fluent 2 styling

The cards follow [Fluent 2](https://fluent2.microsoft.design/) and the [UX guidelines for MCP apps in Copilot](https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-mcp-apps-ui-guidelines):

- Fluent web tokens for color, type, radius, and spacing, in light and dark
- Button, Input, Select, Textarea, Checkbox, MessageBar, Badge, ProgressBar, Table, and Skeleton components, with inline SVG icons and no external fonts
- At most two actions per inline card, with the primary action first
- A loading state, a success message, and a retryable error message for every action
- A skeleton on first paint instead of a blank frame
- Labels on every control, `aria-live` messages, `aria-sort` on table headers, a visible focus ring, and reduced-motion support

Inline cards are previews. The table shows five rows and nothing else. Search, sorting, and the full list open in the expanded view, which the card requests with `ui/request-display-mode`. If the host refuses, the table opens an expanded layout inline.

## Adaptive Cards compared

| | Adaptive Cards | MCP Apps cards |
| --- | --- | --- |
| Layout and styling | Fixed element set, host-controlled | Full HTML and CSS, themed from the host |
| Inputs | `Input.*` elements, limited validation | Any HTML input, your own validation |
| Submit | `Action.Submit` posts back to the agent | The card calls a tool on your connector, then messages the agent |
| Sorting, filtering, paging | Not available | Preview inline, sort and search in the expanded table |
| Refresh in place | Not available | The status card calls a tool and redraws |
| Host support | Broad | Growing |

If you're converting an existing card, `Input.Text`, `Input.Number`, `Input.Date`, `Input.ChoiceSet`, and `Input.Toggle` map to `show_form` field types. `FactSet` maps to the `facts` rows on `show_approval`, `Table` maps to `show_table`, and `ProgressBar` with status text maps to `show_status`. `Action.OpenUrl` becomes `App.openLink(url)`, which asks the host to open the link.

## Deploy it

You need a Power Platform environment where you can create custom connectors, a Copilot Studio agent in a tenant where MCP Apps rendering is available, and the [Power Platform CLI](https://learn.microsoft.com/power-platform/developer/cli/introduction).

1. Copy the template folder.
2. In `apiDefinition.swagger.json`, replace `your-api-host.com` with your own host name. The script handles the MCP request itself, so the host doesn't serve anything.
3. In `apiProperties.json`, set `publisher` to your name.
4. Deploy the connector:

   ```powershell
   pac connector create `
       --api-definition-file apiDefinition.swagger.json `
       --api-properties-file apiProperties.json `
       --script-file script.csx `
       --environment <YOUR_ENVIRONMENT_ID>
   ```

5. In Copilot Studio, open your agent, go to **Tools**, select **Add a tool**, choose **Connector**, and pick **Power MCP Cards**.
6. Add all the tools, including the `submit_*` and `refresh_status` tools.
7. Open the preview chat and ask for something that needs a card, such as "Ask me to approve purchase order PO-7731 for $12,400."

## Connect your own system

Each card-only tool has a `TODO` where the script echoes its input. Replace it with a call to your system using `SendExternalRequestAsync`:

| Tool | Replace the TODO with |
| --- | --- |
| `submit_decision` | A call that records the approval in your approval system |
| `submit_form` | A call that saves or forwards the submitted values |
| `refresh_status` | A lookup of the job's current state. The sample advances progress by 25 each time, so you can watch the card redraw. |

To add a card, write its HTML as a new method in `CardViews`, register it in `RegisterCardViews` with `AddUiResource`, and add a tool in `RegisterCardTools` with `uiResourceUri` set to the view's URI. Start from the closest existing card and keep it to two actions.

You can test a view without a host. Save the HTML that `resources/read` returns and open it in a browser. A view outside a host frame draws its built-in sample data.

## Security

- The views declare no content security policy, so the host applies its restrictive default: no network access and no external scripts or fonts.
- Tool result data reaches the page through `textContent`. Nothing is written with `innerHTML`.
- Form values and table selections go to the agent as a chat message. Don't collect secrets in a form card.
- Add authentication to the connector before you put real approvals behind it.

## Limits to know about

The connector is request and response, so it can't push updates to a card. The status card refreshes only when the user selects Refresh.

Copilot Studio's [supported capabilities table](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/mcp-apps#supported-mcp-apps-capabilities) lists what the host provides. The cards use `ui/initialize`, tool input and results, `tools/call`, `ui/message`, `ui/open-link`, `ui/update-model-context`, and size changes, all supported. Display modes are supported with limits: inline, and full-screen in the side pane. The host provides only theme, language and region, and display mode as context, so the cards use their built-in Fluent colors instead of host style variables.

Tool cancellation, partial tool input, file downloads, and MCP logging aren't supported, and the template doesn't depend on them.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| The agent answers in text and no card appears | You're in a surface that doesn't render MCP Apps, such as Teams or web chat. In preview chat, check that the `ui://` resource read isn't failing. A failed read hides the card without changing the tool result. |
| The agent says it has no `submit_decision` tool | The agent keeps the tool list from when you added the connector. Remove the connector's tools and add them again. |
| A tool is missing in Copilot Studio | Copilot Studio drops tools whose schema has `$ref` or multi-type arrays. Keep custom schemas flat. |
| The card or tool list looks old after an update | The script caches tool lists for five minutes and card HTML for one minute. Wait, then reload the card. |
| The agent calls `submit_decision` before the user answers | Tighten the connector's `Instructions` and the tool descriptions in `script.csx`. |

The [readme](https://github.com/troystaylor/SharingIsCaring/blob/main/Connector-Code/Power%20MCP%20Cards%20Template/readme.md) has the full list.

## Resources

- [Power MCP Cards Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Cards%20Template)
- [Power MCP Apps Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Apps%20Template), a larger set of reference views
- [Power MCP Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Template), the base both build on
- [Use MCP apps in Copilot Studio](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/mcp-apps)
- [MCP Apps support in Power MCP template](/power%20platform/2026-01-27-mcp-apps-power-mcp-template.html), the earlier post on the base template
