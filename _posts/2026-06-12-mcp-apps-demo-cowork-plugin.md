---
layout: post
title: "MCP Apps Demo: interactive widgets in Copilot Cowork"
date: 2026-06-12 16:00:00 -0000
categories: [MCP (Model Context Protocol), Copilot Studio, Integration]
tags: [MCP Apps, Microsoft 365 Copilot, Copilot Cowork, Azure Container Apps, Interactive Widgets, Elicitation]
---

## Why a widget demo plugin

Microsoft published the [MCP apps plugin author guide for Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/mcp-apps-support) yesterday. It covers the full widget contract: how Cowork renders `ui://` resources in sandboxed iframes, which `_meta.ui` fields it honors, the three JSON-RPC methods widgets can call back through (`resources/read`, `tools/call`, `ui/message`), the 64 KiB inline result limit, the CSP restrictions, and the fixed permissions allowlist. It's the definitive reference for what Cowork does and doesn't implement from the [MCP Apps Extension (SEP-1865)](https://github.com/modelcontextprotocol/ext-apps) spec.

What the guide doesn't include is a working reference implementation. This plugin fills that gap — 24 tools that exercise all four Cowork interaction patterns (text only, read-only widgets, interactive widgets with bidirectional communication, and app-only tools) so you can see the author guide's contract in running code.

It ships 24 tools across three categories: custom business demos with elicitation forms, ports of the official MCP Apps examples, and four classic games. Zero authentication, all mock data, designed to be forked and adapted.

Plugin folder: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/MCP%20Apps%20Demo)

## What's included

Four skills, one MCP connector, 24 tools.

### Custom business demos (with elicitation forms)

| Tool | Widget | Elicitation inputs |
|------|--------|--------------------|
| `show_sales_dashboard` | KPI cards, revenue chart, pipeline bars, deal table | Date range, region |
| `show_it_dashboard` | Severity donut, SLA gauge, incident table | Department, severity |
| `show_kanban` | Draggable card columns (To Do / In Progress / Done) | Project name |
| `show_weather` | Current conditions, temperature chart, daily cards | City, forecast days |
| `convert_units` | No widget — text-only elicitation demo | Value, from-unit, to-unit |

### Ext-Apps ports

| Tool | Description |
|------|-------------|
| `generate_qr` | QR code from text/URL |
| `basic_demo` | MCP Apps data-flow hello world |
| `allocate_budget` | Donut chart budget allocator with sliders |
| `segment_customers` | Scatter chart — 50 customers, 4 segments |
| `show_cohort_heatmap` | Monthly retention heatmap |
| `model_scenario` | SaaS revenue projector with line chart |
| `show_map` | Interactive OpenStreetMap (requires CDN) |
| `explore_wiki` | Wikipedia article network graph (requires CDN) |
| `show_3d_scene` | Three.js 3D scene with orbit controls (inlined) |
| `show_shader` | Real-time GLSL fragment shader (pure WebGL) |
| `show_sheet_music` | ABC notation renderer (requires CDN) |
| `show_system_monitor` | CPU per-core + memory usage bars |
| `transcribe_audio` | Live speech-to-text via Web Speech API |
| `show_video` | Video player (requires CDN for media) |
| `show_pdf` | PDF viewer (requires CDN for PDF.js) |

### Classic games

| Tool | Description |
|------|-------------|
| `play_snake` | Arrow keys to move, eat food, grow |
| `play_2048` | Slide tiles, combine matching numbers |
| `play_minesweeper` | Click to reveal, right-click to flag |
| `play_tetris` | Falling blocks — arrow keys + space to drop |

All mock-data tools display a demo data disclaimer in both the widget footer and the tool response text.

## The four interaction patterns

This is the part that took the most iteration. Cowork supports four distinct ways a tool can interact with the user, and each one has different plumbing.

| Pattern | Example tool | How it works |
|---------|-------------|--------------|
| Text only | `convert_units` | No `_meta.ui` — returns plain text, uses elicitation for input |
| Read-only widget | `show_sales_dashboard` | `_meta.ui.resourceUri` + `structuredContent` renders HTML |
| Interactive widget | `show_kanban` | Widget calls `window.__mcpCallTool()` to invoke server tools |
| App-only tools | `refresh_sales` | `visibility: ["app"]` — the agent can't call it, only the widget can |

The interactive pattern is the interesting one. The Kanban board widget renders draggable cards. When you drag a card to a new column, the widget calls `__mcpCallTool("move_card", { taskId, newStatus })` which sends a JSON-RPC request back to the MCP server through Cowork's host bridge. The server processes the move and returns updated state.

App-only tools make this possible without cluttering the agent's tool list. `refresh_sales` exists only for the sales dashboard widget to call — Cowork hides it from the agent's tool selection entirely.

## Widget handshake without an SDK

Cowork renders widgets in sandboxed iframes with a strict CSP that blocks CDN imports. Every widget needs to implement the [MCP Apps JSON-RPC 2.0 handshake](https://github.com/modelcontextprotocol/ext-apps) inline — no external SDK allowed.

The bootstrap sequence:

1. Widget sends `ui/initialize` to the host via `postMessage`
2. Host responds with capabilities
3. Widget sends `ui/notifications/initialized`
4. Host sends `ui/notifications/tool-result` with `structuredContent`

The plugin's shared bootstrap script handles all of this in ~120 lines of vanilla JavaScript. It also re-dispatches the tool result data as a standard `MessageEvent` so each widget's render function works unchanged from standalone testing.

```typescript
// widget-bootstrap.ts — exposed as an inline <script> block
window.__mcpCallTool = function(name, args) {
  return sendRequest("tools/call", {
    name: name,
    arguments: args || {}
  });
};
```

### Auto-resize

The bootstrap attaches a `ResizeObserver` on `document.body` with a 200ms debounce. It reports content height via `ui/notifications/size-changed` but uses `window.innerWidth` for width — letting Cowork control width avoids resize feedback loops that plague early MCP Apps implementations.

## Elicitation forms

Five of the custom tools use elicitation to collect user input before rendering. The sales dashboard asks for a date range and region. The weather tool asks for a city and forecast days. The unit converter asks for value, from-unit, and to-unit.

Elicitation works through the MCP protocol's `elicitation/create` method. The tool returns a schema describing the form fields, Cowork renders a native form UI, and the user's responses come back as structured arguments on the next tool call.

A shared `elicitation.ts` helper standardizes form creation across all five tools, so adding a new elicitation-based tool means defining the schema and the render function — the plumbing is already wired.

## Architecture

```
MCP Apps Demo/
├── manifest.json                    # M365 devPreview manifest
├── color.png / outline.png          # Fluent UI Apps icons
├── package.ps1                      # Plugin validation & packaging
├── skills/                          # 4 Cowork skills
│   ├── explore-widgets/SKILL.md
│   ├── manage-tasks/SKILL.md
│   ├── analyze-data/SKILL.md
│   └── play-games/SKILL.md
├── server/                          # Node.js MCP server
│   ├── package.json
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── src/
│   │   ├── index.ts                 # Express + Streamable HTTP transport
│   │   ├── server.ts                # Tool/resource registration
│   │   ├── shared/
│   │   │   ├── disclaimer.ts        # Demo data disclaimer injection
│   │   │   ├── elicitation.ts       # Elicitation helper
│   │   │   └── widget-bootstrap.ts  # Inline MCP Apps handshake
│   │   ├── custom/                  # Business demo tools + widgets
│   │   └── ext-apps/                # Ext-apps ports + games
│   └── widgets/                     # Widget HTML (inline in TS)
└── infra/                           # Azure Bicep (azd)
    ├── main.bicep
    ├── main.parameters.json
    └── modules/resources.bicep
```

The server uses Express with the MCP SDK's Streamable HTTP transport. Each tool module exports a `register*` function that takes the `McpServer` instance and registers its tools. The widget HTML is inlined as TypeScript template literals — no separate HTML files to serve or CSP-manage.

## Deploy

### Prerequisites

- [Node.js](https://nodejs.org/) 22+
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- An Azure subscription
- [Frontier preview program](https://adoption.microsoft.com/copilot/frontier-program/) access for Cowork
- M365 Admin access to sideload apps

### Steps

1. Install dependencies and run locally:

   ```bash
   cd server
   npm install
   npm run dev
   # Server at http://localhost:8080, MCP at http://localhost:8080/mcp
   ```

2. Deploy to Azure:

   ```bash
   azd init
   azd env set AZURE_LOCATION westus2
   azd up
   ```

3. After first deploy, bind the ACR registry:

   ```bash
   az containerapp registry set \
     -g rg-mcp-apps-demo \
     -n mcp-apps-demo \
     --server <your-acr>.azurecr.io \
     --identity system
   ```

4. Update `manifest.json` — replace `{% raw %}{{YOUR_CONTAINER_APP_FQDN}}{% endraw %}` with your Container App's FQDN

5. Package and sideload:

   ```powershell
   .\package.ps1            # Validates and creates .zip
   # Upload at M365 Admin Center → Agents → All Agents → Add Agent
   ```

6. In Cowork, go to **Sources & Skills** and enable MCP Apps Demo

### No auth required

Unlike most Cowork plugins, this one uses `"authorization": { "type": "None" }`. All data is mock/demo, so there's no user context to protect. This makes it the fastest path to seeing MCP Apps widgets in action — no Entra app registration, no SSO setup, no OAuth configuration.

## Manifest details

The plugin uses the `devPreview` Teams manifest schema. Only the `devPreview` path binds the MCP connector in Cowork's current runtime — a `v1.28` manifest loads skills but silently drops the connector.

```json
{
  "agentConnectors": [{
    "id": "mcp-apps-demo-server",
    "displayName": "MCP Apps Demo",
    "toolSource": {
      "remoteMcpServer": {
        "mcpServerUrl": "https://your-app.azurecontainerapps.io/mcp",
        "authorization": { "type": "None" }
      }
    }
  }]
}
```

Four skills map to the tool categories: `explore-widgets` covers dashboards and ext-apps ports, `manage-tasks` handles the Kanban board, `analyze-data` covers charts and data visualization tools, and `play-games` triggers the four classic games.

## Known limitations

- **CDN-dependent widgets**: Map (Leaflet), Wiki Explorer (force-graph), Sheet Music (abcjs), Video, and PDF (PDF.js) require CDN access that Cowork's iframe CSP may block
- **No outbound HTTPS from Container Apps**: The server can't call external APIs (for example, Open-Meteo). All data is mock/demo
- **Widget-to-server tool calls**: `__mcpCallTool()` may not work for all tool types in Cowork's current preview

## What to build next

This plugin is a reference implementation. Fork it and keep the tools you need:

- **Replace mock data with real APIs** — swap the demo data generators with actual service calls
- **Add authentication** — follow the SSO pattern from the [Decision Duck Cowork plugin](https://troystaylor.com/mcp%20(model%20context%20protocol)/copilot%20studio/integration/2026-06-12-decision-duck-cowork-plugin.html) to protect real data
- **Create new widget types** — the bootstrap script and shared helpers work for any HTML you can inline
- **Add elicitation to ext-apps ports** — most ext-apps tools accept fixed arguments; adding elicitation makes them conversational

## Resources

- [MCP Apps Demo plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/MCP%20Apps%20Demo)
- [MCP Apps Extension specification (SEP-1865)](https://github.com/modelcontextprotocol/ext-apps)
- [Cowork MCP Apps Plugin Author Guide](https://learn.microsoft.com/microsoft-365/copilot/cowork/mcp-apps-support)
- [Build plugins for Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
