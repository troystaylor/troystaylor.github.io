---
layout: post
title: "Copilot Change Notifications MCP connector for Copilot Studio"
date: 2026-04-21 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Copilot Studio, MCP, Microsoft Graph, Change Notifications, Webhooks, Power Platform, AI Governance]
description: "Monitor Microsoft 365 Copilot interactions and meeting AI insights in near real time by combining Graph change notifications with a dual-mode Power Platform custom connector for REST and MCP workflows."
---

If you want visibility into how Copilot is being used across your organization, polling APIs is slow and expensive. Change notifications give you a better model: subscribe once, receive events as activity happens, and then fetch details only when needed.

This connector does exactly that for Microsoft 365 Copilot scenarios. It combines REST operations and MCP tools so you can use the same connector in Power Automate flows and in Copilot Studio agents.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Change%20Notifications)

## What this connector covers

The connector focuses on three workflows:

1. Create and manage Microsoft Graph subscriptions for Copilot interaction and meeting insight resources
2. Validate and process incoming webhook payloads
3. Retrieve full interaction or insight records for downstream automation and analysis

## REST and MCP in one connector

This project exposes:

- 10 REST operations for subscription management, webhook connectivity testing, and direct Graph passthrough
- 11 MCP tools for conversational orchestration in Copilot Studio

That split matters in practice. REST operations are great for deterministic flow design, while MCP tools are better when an orchestrator needs to choose the next action dynamically.

## MCP tools included

The connector exposes these MCP tools:

| Tool | Purpose |
|------|---------|
| `create_tenant_interaction_subscription` | Subscribe to tenant-wide Copilot interactions |
| `create_user_interaction_subscription` | Subscribe to interactions for one user |
| `create_meeting_insight_subscription` | Subscribe to AI insights for a meeting |
| `list_subscriptions` | List active subscriptions |
| `delete_subscription` | Delete a subscription |
| `renew_subscription` | Extend subscription expiration |
| `process_interaction_notification` | Parse and validate interaction webhook payloads |
| `process_insight_notification` | Parse and validate meeting insight payloads |
| `get_interaction` | Fetch full interaction details by ID |
| `get_meeting_insight` | Fetch a specific meeting insight |
| `list_interactions` | Query recent interactions with optional OData filtering |

## Why change notifications are a strong fit

For Copilot governance and observability, you usually need two things at the same time:

- Fast signals that something changed
- Rich detail only when the signal is relevant

This connector keeps those concerns separate. Notifications trigger quickly, and tool calls such as `get_interaction` or `get_meeting_insight` retrieve full records only when your workflow actually needs them.

## Prerequisites

Before you import the connector, make sure you have:

1. A Microsoft 365 tenant with Copilot features enabled
2. An app registration with Graph permissions for your scenario
3. A secure HTTPS webhook endpoint for notification delivery
4. Copilot licensing and Power Platform licensing required for your environment

From the project documentation, common Graph permissions include:

- `AiEnterpriseInteraction.Read.All` for tenant-wide interaction access
- `AiEnterpriseInteraction.Read` for delegated per-user access
- `OnlineMeetingAiInsight.Read.All` for meeting insight scenarios

## Setup flow

### 1. Register your app in Microsoft Entra ID

Create an app registration, generate a client secret, and grant required Graph permissions with admin consent.

### 2. Configure connector connection values

Provide:

- Tenant ID
- Client ID
- Client secret

### 3. Validate the webhook endpoint before creating subscriptions

Use the webhook connectivity test operation so you can catch certificate, routing, or firewall issues early.

### 4. Create the right subscription type

Choose one of three models:

- Tenant-wide interactions
- Per-user interactions
- Meeting insight notifications

## Webhook design notes

Your webhook should:

- Accept HTTPS POST requests
- Validate client state before processing
- Respond quickly so Graph does not treat the endpoint as unhealthy
- Offload heavy processing asynchronously

A common production pattern is:

1. Accept notification
2. Validate minimal fields
3. Queue payload for background processing
4. Fetch full interaction or insight details after queueing

## Validation guardrails built into the script

The script includes input validation before making Graph calls. Examples include:

- Webhook URL must be HTTPS
- Subscription expiration must be in a valid future window
- User ID, meeting ID, and subscription ID length checks

That defensive layer helps prevent avoidable failures and gives clear errors back to the caller.

## Subscription lifecycle behavior to plan for

One detail worth calling out: when expiration is set beyond 60 minutes in some subscription paths, the script includes `lifecycleNotificationUrl`. This helps support lifecycle events and renewal workflows.

You should still design for:

- Expiration tracking
- Automatic renewals before expiry
- Recovery when subscriptions are deleted after repeated webhook failures

## Example usage prompts for Copilot Studio

Try prompts like:

- "Create a tenant-wide Copilot interaction subscription for our compliance webhook"
- "List active Copilot change notification subscriptions"
- "Process this interaction webhook payload and return interaction IDs"
- "Get interaction details for this resource ID"
- "Renew this subscription for another 60 minutes"

## Observability with Application Insights

The script supports telemetry and logs events such as:

- Request received and request errors
- Graph request success and Graph request errors
- MCP protocol and tool execution failures
- Webhook test outcomes

Add your instrumentation key in `script.csx` to enable this.

## Deploy with Power Platform CLI

```powershell
pac auth create --environment "https://yourorg.crm.dynamics.com"

pac connector create \
  --api-definition-file apiDefinition.swagger.json \
  --api-properties-file apiProperties.json \
  --script-file script.csx
```

If your environment blocks script upload via CLI, create the connector first, then upload `script.csx` in the connector Code tab.

## Files in this project

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI operations and MCP protocol operation metadata |
| `apiProperties.json` | OAuth and connector parameter configuration |
| `script.csx` | MCP router, Graph request handlers, webhook testing, and validation logic |
| `readme.md` | Setup, usage patterns, and payload examples |

## When to use this connector

Use this connector when you need near real-time Copilot event monitoring and want one implementation that works for both automation and conversational orchestration.

It is especially useful for:

- AI usage governance
- Audit and compliance workflows
- Meeting summary automation
- Copilot adoption analytics

## Resources

- [Copilot Change Notifications source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Change%20Notifications)
- [Microsoft Graph change notifications](https://learn.microsoft.com/graph/change-notifications-overview)
- [Custom connectors overview](https://learn.microsoft.com/connectors/custom-connectors/)
- [Power Platform CLI overview](https://learn.microsoft.com/power-platform/developer/cli/introduction)
- [Copilot Studio documentation](https://learn.microsoft.com/microsoft-copilot-studio/)
