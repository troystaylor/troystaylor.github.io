---
layout: post
title: "MCP Apps support in Power MCP template"
date: 2026-01-27 09:00:00 -0500
categories: [Power Platform, MCP, Custom Connectors]
tags: [Power MCP, MCP Apps, Copilot Studio, Custom Connectors, Model Context Protocol, JSON-RPC, Application Insights, Templates]
description: "Production-ready MCP server template for Power Platform custom connectors with full MCP Apps support."
---

The MCP Apps extension for MCP is now generally available as of yesterday, Jan 26, 2026. It formalizes interactive `ui://` resources, enables hosts to prefetch and review templates, and uses MCP JSON-RPC via `@modelcontextprotocol/ext-apps` in sandboxed iframes. It is security-first, auditable, and backward compatible with text-only MCP hosts.

This Power MCP template gives you a production-ready Power Platform connector-enabled MCP server for Copilot Studio agents and previews full MCP Apps support with the code needed for five built-in UIs. Once the UI support is available in Copilot Studio, you’ll configure identity, declare tools, serve `ui://` resources, and test in your agents, all with Power Platform guardrails, telemetry, and typed helpers.

## What is the Power MCP template?

A production-ready **MCP server template** for **Power Platform custom connectors** with full **MCP Apps** support. It implements JSON-RPC 2.0, the MCP Apps (2026-01-26) spec, and the `@modelcontextprotocol/ext-apps` SDK across five built-in UI components. It’s tested with **Copilot Studio**, but UI support for the components is not yet available.

## Why this matters
- Get rich MCP Apps UIs (color picker, charts, forms, tables, confirmation) out of the box
- Support tools, prompts, resources, cancellation, logging, retries, caching, pagination, binary content
- Wire telemetry with Application Insights and keep flows inside Power Platform guardrails

## Architecture
```
Power Platform custom connector → script.csx MCP server → tools/resources/prompts/Apps
```

## Features
### Core MCP protocol
- **Full MCP compliance**: JSON-RPC 2.0, MCP methods (initialize, tools/list, tools/call, resources, prompts, logging)
- **Batch requests** and **cancellation**
- **Prompts**: `analyze_data`, `summarize`, `code_review` with arguments
- **Resource templates**: `data://{type}/{id}`, `config://{section}`, `log://{level}/{count}`
- **Structured content**: `content` + `structuredContent`

### MCP Apps (5 built-in UIs)
- **Color picker**: theme-aware, history, `requestDisplayMode`, `sendLog`
- **Data visualizer**: Chart.js (bar/line/pie/doughnut), click selection
- **Form input**: dynamic forms, validation, draft persistence
- **Data table**: sort/filter, row selection, export
- **Confirmation dialog**: info/warning/danger variants

All components implement **all notification handlers** (`ontoolinput*`, `ontoolresult`, `oncalltool`, `onlisttools`, `onhostcontextchanged`, `onerror`, `onteardown`) and **all SDK methods** (`updateModelContext`, `sendMessage`, `callServerTool`, `requestDisplayMode`, `openLink`, `sendLog`, `sendSizeChanged`). State persists via `localStorage`; theme via `applyDocumentTheme()`.

### Developer experience
- Typed argument helpers: `RequireArgument`, `GetIntArgument`, `GetBoolArgument`, `GetDateTimeArgument`, `GetArrayArgument`, `GetObjectArgument`
- Query string builder: `BuildQueryString()`
- Retry logic: exponential backoff on 429/502/503/504
- External API helpers: `SendGetRequestAsync`, `SendPostRequestAsync`, `SendDeleteRequestAsync`, `SendExternalRequestAsync`
- Caching, pagination, image/binary helpers

### Operations & telemetry
- Application Insights integration (events: `McpRequestReceived`, `McpToolCall*`, `McpError`, etc.)
- Logging levels (`debug`–`emergency`) with `logging/setLevel`

## Quick start
1. **Configure identity** in `script.csx`
   ```csharp
   private const string ServerName = "your-server-name"; // lowercase-with-dashes
   private const string ServerVersion = "1.0.0";
   private const string ServerTitle = "Your Server Title";
   private const string ServerDescription = "Description";
   private const string ServerInstructions = ""; // optional
   ```
2. **Define tools** in `BuildToolsList()`
   ```csharp
   new JObject {
     ["name"] = "your_tool",
     ["description"] = "Clear description",
     ["inputSchema"] = new JObject { ... },
     ["annotations"] = new JObject { ["readOnlyHint"] = true, ["idempotentHint"] = true, ["openWorldHint"] = false }
   }
   ```
3. **Route execution** in `ExecuteToolAsync()`
   ```csharp
   switch (toolName.ToLowerInvariant())
   {
       case "your_tool": return await ExecuteYourToolAsync(arguments);
   }
   ```
4. **Implement tool logic**
   ```csharp
   private async Task<JObject> ExecuteYourToolAsync(JObject arguments)
   {
       var param1 = RequireArgument(arguments, "param1");
       // ...
       return new JObject { ["result"] = "ok" };
   }
   ```
5. **Connector contract**
   - `apiDefinition.swagger.json`: streamable MCP endpoint with `x-ms-agentic-protocol: mcp-streamable-1.0`
   - `apiProperties.json`: `routeRequestToCode` policy for `InvokeMCP`

## MCP Apps: add a UI tool
```csharp
new JObject
{
  ["name"] = "my_ui_tool",
  ["description"] = "Tool with interactive UI",
  ["inputSchema"] = new JObject { ... },
  ["_meta"] = new JObject
  {
    ["ui"] = new JObject { ["resourceUri"] = "ui://my-component" }
  }
}
```

Register UI resource:
```csharp
new JObject { ["uri"] = "ui://my-component", ["name"] = "My Component", ["mimeType"] = "text/html" };
```

Serve UI:
```csharp
case "ui://my-component": return GetMyComponentUI();
```

UI HTML/JS (uses `@modelcontextprotocol/ext-apps`):
```html
<script type="module">
  import { App, applyDocumentTheme } from 'https://esm.sh/@modelcontextprotocol/ext-apps@1.0.1';
  const app = new App();
  app.ontoolresult = (result) => console.log(result);
  await app.connect();
</script>
```

## Testing
**curl**
```bash
curl -X POST https://your-connector/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2026-01-26","clientInfo":{"name":"test"}}}'
```
- `tools/list`, `resources/list`, `resources/read` (`ui://color-picker`), `tools/call` (`echo`, `data_visualizer`)

**Copilot Studio**
- Import connector → add as action → tools appear automatically → test with agent prompts

## Guardrails
- Keep connector in a locked-down environment; enforce DLP/approvals
- CLI defaults to `--allow-all` (file system, git); restrict tools in SDK/CLI and audit outputs
- Run the proxy where file access is appropriate; treat as privileged
- Add retries/timeouts; log tool calls

## Resources
- Power MCP Apps Template: https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Apps%20Template
- Model Context Protocol Blog announcement: https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/ 
- MCP Apps extension (official): https://modelcontextprotocol.io/docs/extensions/apps
- MCP Apps blog (background): https://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/
- `@modelcontextprotocol/ext-apps`: https://github.com/modelcontextprotocol/ext-apps
