---
layout: post
title: "Build a Slack Cowork plugin with an in-tenant MCP server"
date: 2026-05-22 09:00:00 -0000
categories: [MCP (Model Context Protocol), Copilot Studio, Integration]
tags: [Slack, Microsoft 365 Copilot, MCP, APIM, Azure Container Apps, Key Vault]
---

## Why Copilot Cowork plugins matter

Microsoft positions Cowork extensibility as a plugin package model for Microsoft 365 Copilot: package skills and connectors together in one Microsoft 365 app package, then deploy through Microsoft 365 admin controls.

If you want Copilot Cowork to work with Slack in an enterprise-safe way, you need more than a basic connector. You need a complete plugin that supports read and write actions, keeps OAuth manageable, and runs in your tenant.

This Slack Cowork plugin implementation does that. It combines:

- A Microsoft 365 Copilot Cowork plugin manifest
- An in-tenant MCP server running on .NET 10
- Azure infrastructure for hosting and secrets
- Skills that map directly to real Slack tasks

The result is a production-ready plugin pattern you can adapt for other SaaS platforms, not just Slack.

## What this plugin includes

The Slack plugin in the SharingIsCaring repo includes:

- A Cowork plugin manifest with remote MCP configuration
- Six skills for common Slack workflows
- A dual-route MCP server
- Infrastructure as code for Azure Container Apps, API Management (APIM), and Key Vault
- Packaging scripts for repeatable deployment

Plugin folder:

- https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Slack

Repository:

- https://github.com/troystaylor/SharingIsCaring

## Skills shipped in the plugin

This plugin ships with six focused skills:

- slack-channel-digest: Summarize channel activity
- slack-search-and-cite: Search messages and cite results
- slack-thread-recap: Recap a thread from a permalink
- slack-people-lookup: Resolve users and profiles
- slack-post-update: Post an update
- slack-remind-me: Create and manage reminders

This split keeps prompts focused and makes behavior easier to debug and tune.

## MCP tool surface and routing model

The server exposes typed tools and orchestration tools.

Typed read tools include:

- search_messages
- list_channels
- get_channel_history
- get_user_info
- list_users

Typed write tools include:

- send_message
- schedule_message
- pin_message
- add_bookmark
- complete_or_delete_reminder
- upload_file

For long-tail Slack operations, the plugin also includes orchestration tools:

- scan_slack
- launch_slack
- sequence_slack

## Dual-route server design

One backend exposes two MCP routes:

- /mcp/full for Cowork scenarios that need read and write capabilities
- /mcp/federated for optional read-only tenant grounding scenarios

This design lets you keep one codebase while supporting different trust and usage models.

## Azure architecture

This plugin uses:

- Azure Container Apps to host the MCP server
- API Management as a managed API gateway
- Azure Key Vault for Slack secrets
- Managed identity for service-to-service access

This keeps secrets out of source control and gives you a deployment path aligned with enterprise requirements.

## Slack OAuth setup notes that save time

Slack setup highlights:

1. Create a Slack app at api.slack.com/apps.
2. Add this redirect URL under OAuth & Permissions:

```text
https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect
```

3. Add the required user scopes.
4. Enable token rotation.
5. Reinstall the app after scope changes.

Cowork OAuth setup highlights:

1. Register OAuth in Teams Developer Portal.
2. Use Slack authorize and token endpoints.
3. Copy the generated OAuth registration ID.
4. Set manifest agentConnectors authorization referenceId.
5. Repackage and re-upload the plugin in Microsoft 365 admin center.

Reference:

- https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-authentication

## Current platform caveat

At the time of writing, Cowork runtime behavior may require a temporary workaround for write-class tool invocation. In this implementation, write-class tools are annotated to enable end-to-end testing while waiting for native write approval UX improvements.

If you adopt this pattern, keep this as a clearly documented temporary state and plan to revert annotations when first-party write approval UX is available.

## End-to-end implementation flow

Use this sequence to deploy confidently:

1. Configure Slack app and OAuth scopes.
2. Deploy Azure infrastructure and MCP backend.
3. Store secrets in Key Vault.
4. Register OAuth client in Teams Developer Portal.
5. Update manifest reference ID and version.
6. Package and upload the plugin.
7. Run smoke tests for read and write skills.

## What to customize first

When adapting this plugin for your tenant, start here:

- Skill trigger phrases and response style
- Scope minimization by use case
- APIM policies for throttling and observability
- Logging and correlation IDs across tool calls
- Error handling and user-safe fallback messages

## Final thoughts

This Slack Cowork plugin is a complete blueprint for enterprise-grade SaaS integration with Microsoft 365 Copilot. It gives you a clean balance of skill design, tool design, OAuth handling, and tenant-owned infrastructure.

If you are building Copilot integrations that need trustworthy read and write behavior, this is a practical foundation to build on.

## Resources

- Slack Cowork plugin:
  https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Slack
- SharingIsCaring repository:
  https://github.com/troystaylor/SharingIsCaring
- Build plugins for Cowork (Frontier):
  https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development
- Microsoft 365 Copilot plugin authentication:
  https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-authentication
- Frontier program information:
  https://adoption.microsoft.com/en-us/copilot/frontier-program/
