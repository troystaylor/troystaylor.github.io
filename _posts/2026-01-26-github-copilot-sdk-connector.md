---
layout: post
title: "GitHub Copilot SDK connector for Power Platform"
date: 2026-01-26 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [GitHub Copilot SDK, Copilot, Copilot Studio, Computer Use, Copilot Plugins, Cloudflare Tunnel, Power Platform, MCP, JSON-RPC]
description: "MCP-compliant Power Platform custom connector that proxies GitHub Copilot SDK over Cloudflare Tunnel with JSON-RPC tools."
---

GitHub Copilot SDK brings the Copilot CLI agent runtime to Python, TypeScript, Go, and .NET. You define agent behavior and tools. Copilot handles planning, calls tools, edits files, and routes models over JSON-RPC to the Copilot CLI in server mode. Add Work IQ work context, Copilot plugins or MCP servers, and local files so Copilot grounds answers in your organization’s knowledge—owners, specs, meeting transcripts, and design docs. The SDK inherits that context and toolchain.

This connector bridges that SDK into Power Platform with MCP-friendly JSON-RPC tools. Keep auth local, add DLP and approvals, and orchestrate Copilot agents from flows, apps, or Copilot Studio—without desktop control or computer-use sessions.

## What is the GitHub Copilot SDK connector?

MCP-compliant **Power Platform custom connector** that proxies JSON-RPC calls to the **GitHub Copilot SDK** through a Cloudflare Tunnel. It reuses your local Copilot authentication and exposes tools to manage sessions, send prompts, list models, and check status.

## Why this matters
- Orchestrate GitHub Copilot SDK sessions from Power Automate, Power Apps, or Copilot Studio
- Keep auth local—no secrets in the connector
- Reuse JSON-RPC tools in flows, apps, or agents

## Use case: alternative to Copilot Studio computer-use
- Keep AI actions inside Power Platform scopes and connectors (DLP, approvals, logging)
- Use explicit JSON-RPC tools with typed arguments instead of full desktop control
- Run the SDK locally—no remote desktop or screen control
- Pair with Power Automate RPA for desktop steps when needed

### Comparison

| Capability | Copilot Studio computer-use | Copilot SDK connector |
|------------|-----------------------------|------------------------|
| Execution | Windows session with UI control | Node service + JSON-RPC over HTTP |
| Control surface | Desktop automation | Power Platform flows, apps, agents |
| Auth | Windows user session | GitHub Copilot auth (local) |
| Guardrails | Screen/keyboard control | Explicit tools, DLP, approvals |
| Audit | Session transcripts | Flow run history, connector logs |
| Network | Remote desktop required | Local tunnel (Cloudflare) |

## Architecture
```
Power Platform → Cloudflare Tunnel → localhost:3000 → GitHub Copilot SDK
```

## Setup
1. **Install dependencies**
   ```bash
   cd "GitHub Copilot SDK"
   npm install
   ```
2. **Start the proxy server**
   ```bash
   npm start
   # or
   node proxy-http-to-sdk.mjs
   ```
3. **Start Cloudflare Tunnel**
   ```bash
   cloudflared tunnel --url http://localhost:3000
   ```
   Copy the generated URL (e.g., `https://abc-xyz.trycloudflare.com`).
4. **Update the connector script** (`script.csx`)
   ```csharp
   private const string DefaultSdkUrl = "https://abc-xyz.trycloudflare.com/jsonrpc";
   ```
5. **Deploy to Power Platform**
   ```bash
   pac connector update --environment <env-id> --connector-id <connector-id> --script-file script.csx
   ```

## Copilot Studio setup
1. Import the connector into your environment (`apiDefinition.swagger.json`, `apiProperties.json`, `script.csx`).
2. In Copilot Studio, go to **Tools → Add a tool → Model Context Protocol**.
3. Set the endpoint to your tunnel URL + `/jsonrpc`.
4. Optional: Add environment variables for default model/session naming; keep secrets empty (auth is local).
5. Apply DLP and approvals in the environment for guardrails.

### Agent instruction
> Maintain one Copilot SDK session per conversation. If missing, call `copilot_create_session` with `sessionId` = conversationId and `model`. Use `copilot_send` to answer user requests. Use `copilot_list_sessions` to reuse sessions; clean up with `copilot_delete_session`.

### Tool calling pattern (Copilot Studio)
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 1,
  "params": {
    "name": "copilot_send",
    "arguments": {
      "sessionId": "conversation-id",
      "prompt": "draft an email about ..."
    }
  }
}
```

## Tools

| Tool | JSON-RPC | Description |
|------|----------|-------------|
| `copilot_create_session` | `session.create` | Create a new session (optional: `model`, `sessionId`) |
| `copilot_send` | `session.send` | Send prompt to a session |
| `copilot_resume_session` | `session.resume` | Resume an existing session |
| `copilot_list_sessions` | `session.list` | List all sessions |
| `copilot_delete_session` | `session.delete` | Delete a session |
| `copilot_ping` | `ping` | Ping the server |
| `copilot_list_models` | `models.list` | List available models |
| `copilot_get_status` | `status.get` | Get server status |
| `copilot_get_auth_status` | `auth.status` | Get authentication status |

> **Note:** Copilot CLI defaults to `--allow-all`, enabling file system and git tools. Configure SDK client `tools` to disable or limit, or run CLI with restricted tools. This connector forwards JSON-RPC; it does not add extra sandboxing.

## Example: create session
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 1,
  "params": {
    "name": "copilot_create_session",
    "arguments": {
      "model": "claude-sonnet-4",
      "sessionId": "my-session"
    }
  }
}
```

## Authentication
Uses your local GitHub Copilot auth. Verify with:
```bash
copilot auth status
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Ensure `node proxy-http-to-sdk.mjs` is running |
| Tunnel not reachable | Verify `Cloudflare Tunnel` is running and the script URL is updated |
| Auth required | Run `copilot auth login` on your machine |

## Files

| File | Purpose |
|------|---------|
| `proxy-http-to-sdk.mjs` | Proxy HTTP JSON-RPC server using GitHub Copilot SDK |
| `script.csx` | Power Platform connector script |
| `apiDefinition.swagger.json` | OpenAPI definition |
| `apiProperties.json` | Connector properties |

## Guardrails and safety
- Use a named/persistent tunnel and restrict access; avoid exposing publicly without auth
- Keep the connector in a locked-down environment; enforce DLP and approvals
- File access: CLI defaults to file system/git tools; restrict tools in the SDK client or CLI, and audit outputs
- Log tool calls (flows) and add retries/timeouts in `proxy-http-to-sdk.mjs`
- For desktop actions, pair with Power Automate RPA rather than exposing the desktop

## Limitations
- No direct desktop automation; you must wire actions through flows/apps
- Tunnel URLs rotate unless you use a named tunnel
- SDK sessions persist locally; clean up with `copilot_delete_session`

## Tips
- Use a named/persistent Cloudflare Tunnel to avoid URL changes; update `DefaultSdkUrl` when it changes
- Run the proxy where file access is appropriate; treat it as a privileged process
- Clean up sessions with `copilot_list_sessions` + `copilot_delete_session`
- Add logging/telemetry (for example, Application Insights) if you need observability

## Resources
- Connector repo: [SharingIsCaring/GitHub Copilot SDK](https://github.com/troystaylor/SharingIsCaring/tree/main/GitHub%20Copilot%20SDK)
- GitHub Copilot SDK docs: https://docs.github.com/en/copilot/building-copilot-extensions/github-copilot-sdk
- GitHub Copilot SDK repo: https://github.com/github/copilot-sdk
- Copilot CLI docs: https://docs.github.com/en/copilot/github-copilot-cli
- Copilot plugin marketplace: `/plugin marketplace` (see Copilot CLI; docs: https://aka.ms/copilot-cli-plugins)
- Work IQ MCP server: https://aka.ms/WorkIQMCP