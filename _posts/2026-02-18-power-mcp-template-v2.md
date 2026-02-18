---
layout: post
title: "Power MCP Template v2: fluent API and Copilot instructions"
date: 2026-02-18 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Power MCP, MCP, Copilot Studio, Custom Connectors, Model Context Protocol, GitHub Copilot, Templates]
description: "Power MCP Template v2 replaces manual tool wiring with a fluent AddTool API, a built-in McpRequestHandler, and a copilot-instructions.md file that teaches Copilot how to extend your connector."
---

The [Power MCP Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Template) now ships as v2. The original template worked, but adding a tool meant touching three places: build a JObject definition in `BuildToolsList()`, add a case to the switch in `ExecuteToolAsync()`, and write the handler method. Miss one step and the tool silently doesn't show up. You also had to remember which namespaces the Power Platform sandbox allows, how to avoid ambiguous type references, and where Copilot Studio diverges from the MCP spec—all on your own.

v2 replaces that with a fluent `AddTool()` API that handles definition, routing, and schema in a single call. A reusable `McpRequestHandler` class owns the protocol so you never touch JSON-RPC wiring. And a `McpSchemaBuilder` gives you typed methods for strings, integers, arrays, and nested objects instead of raw JObject construction.

The biggest addition is a `copilot-instructions.md` file that ships with the template. It teaches GitHub Copilot the sandbox constraints, the two-section file structure, and the exact patterns for adding tools. Drop the template into your project, ask Copilot to add a tool, and it generates sandbox-safe code with the right schema builder syntax—no hand-holding required.

## What changed

### Two-section architecture

The `script.csx` file is now split into two clearly marked sections:

1. **Section 1: MCP Framework** (~lines 1--430) — `McpRequestHandler`, `McpSchemaBuilder`, content helpers, and all supporting types. Don't modify this section unless you're extending the framework itself.
2. **Section 2: Connector Entry Point** (~lines 430+) — Server config, `RegisterTools()` with tool definitions, `ExecuteAsync()`, helpers, and Application Insights telemetry. This is where all your work happens.

When Microsoft enables the official MCP SDK namespaces in the Power Platform sandbox, Section 1 becomes a `using` statement instead of inline code.

### Fluent AddTool API

v1 required three separate steps to add a tool: build a JObject definition in `BuildToolsList()`, add a case to the switch in `ExecuteToolAsync()`, and write the handler method. v2 collapses that into a single `AddTool()` call:

```csharp
handler.AddTool("tool_name", "What this tool does — be descriptive for AI.",
    schema: s => s
        .String("param1", "Description", required: true)
        .Integer("top", "Max results", defaultValue: 10),
    handler: async (args, ct) =>
    {
        var param1 = RequireArgument(args, "param1");
        var top = args.Value<int?>("top") ?? 10;
        // Tool logic here
        return new JObject { ["result"] = "value" };
    },
    annotations: a => { a["readOnlyHint"] = true; });
```

No switch statement. No manual JSON schema. The handler maps tool names to handlers automatically.

### McpSchemaBuilder

A typed fluent API for building JSON Schema objects. Supports all the types you need:

```csharp
s.String("name", "desc", required: true, format: "date-time", enumValues: new[] { "a", "b" })
s.Integer("count", "desc", defaultValue: 10)
s.Number("price", "desc", required: true)
s.Boolean("active", "desc")
s.Array("items", "desc", itemSchema: new JObject { ["type"] = "string" })
s.Object("address", "desc", nested => nested.String("city", "City").String("zip", "ZIP"))
```

### Rich content helpers

Return images, audio, embedded resources, or mixed content from tool handlers using static helper methods:

```csharp
// Mixed content
return McpRequestHandler.ToolResult(new JArray
{
    McpRequestHandler.TextContent("Description text"),
    McpRequestHandler.ImageContent(base64Data, "image/png")
});

// Structured content (requires outputSchemaConfig on the tool)
return McpRequestHandler.ToolResult(
    content: new JArray { McpRequestHandler.TextContent("65°F") },
    structuredContent: new JObject { ["temp"] = 65 });
```

### Output schema support

Tools can declare an output schema for structured content using `outputSchemaConfig`:

```csharp
handler.AddTool("weather", "Get current weather",
    schema: s => s.String("city", "City name", required: true),
    handler: async (args, ct) => { /* ... */ },
    outputSchemaConfig: s => s
        .Number("temp", "Temperature in Fahrenheit")
        .String("condition", "Current condition"));
```

## The copilot-instructions.md file

This is the biggest quality-of-life improvement. The template now includes a `copilot-instructions.md` file that teaches GitHub Copilot (and any Copilot-powered editor) exactly how to extend the connector. It covers:

- **Power Platform sandbox constraints**: allowed namespaces, forbidden namespaces, no DI, no ASP.NET Core, stateless execution, single-file requirement
- **Ambiguous type references**: always fully qualify `Newtonsoft.Json.Formatting.None` to avoid CS0104 errors
- **MCP protocol rules**: tool errors are tool results (not protocol errors), Copilot Studio requires responses for all methods including notifications
- **What NOT to change**: Section 1 classes, the HandleAsync switch, serialization methods, content helpers
- **What IS safe to change**: server options, instructions, `RegisterTools()` contents, helper methods
- **Stateless limitations**: tasks, server-to-client requests and notifications can't be implemented in the Power Platform sandbox

Drop the template folder into your project, and Copilot already knows the rules. Ask it to add a tool, and it generates the correct `AddTool()` call with the right schema builder syntax, proper error handling, and sandbox-safe code.

## AddTool parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `name` | Yes | Tool identifier (snake_case) |
| `description` | Yes | AI-readable description of what the tool does |
| `schema` | Yes | `McpSchemaBuilder` lambda for `inputSchema` |
| `handler` | Yes | `Func<JObject, CancellationToken, Task<JObject>>` — the tool logic |
| `annotations` | No | MCP annotations: `readOnlyHint`, `idempotentHint`, `openWorldHint` |
| `title` | No | Human-readable display name |
| `outputSchemaConfig` | No | `McpSchemaBuilder` lambda for `outputSchema` (enables `structuredContent`) |

## Quick start

1. **Configure server identity** — update the `McpServerOptions` block in Section 2
2. **Register tools** — add `handler.AddTool()` calls in `RegisterTools()`
3. **Deploy** — paste `script.csx` into the connector's custom code, use the provided `apiDefinition.swagger.json` and `apiProperties.json`
4. **Test** — add the connector as an action in Copilot Studio; tools appear automatically

## v1 vs. v2

| Area | v1 | v2 |
|------|----|----|
| Tool definition | Manual JObject construction | Fluent `AddTool()` with `McpSchemaBuilder` |
| Tool routing | Switch statement in `ExecuteToolAsync()` | Automatic handler dispatch |
| Schema building | Raw JSON | Typed builder: `.String()`, `.Integer()`, `.Object()` |
| Rich content | Manual JObject wrapping | `TextContent()`, `ImageContent()`, `ToolResult()` |
| Output schema | Not supported | `outputSchemaConfig` parameter |
| Copilot guidance | None | `copilot-instructions.md` with constraints, patterns, and rules |
| Code structure | Flat — everything mixed together | Two sections: framework (don't touch) and entry point (your code) |

## Helper methods

| Method | Description |
|--------|-------------|
| `RequireArgument(args, "name")` | Get required string argument; throws `ArgumentException` if missing |
| `GetArgument(args, "name", "default")` | Get optional string argument with fallback |
| `GetConnectionParameter("name")` | Read a connector connection parameter (null-safe) |
| `SendExternalRequestAsync(method, url, body)` | Forward-auth HTTP request to external API |

## Files in the template

| File | Purpose |
|------|---------|
| `script.csx` | MCP framework + connector entry point (866 lines) |
| `copilot-instructions.md` | Teaches GitHub Copilot the template's rules and patterns |
| `readme.md` | Quick start, helper docs, testing, setup |
| `apiDefinition.swagger.json` | Minimal MCP contract with `x-ms-agentic-protocol: mcp-streamable-1.0` |
| `apiProperties.json` | Routes requests to custom code (`InvokeMCP`) |

## Resources

- Power MCP Template: [github.com/troystaylor/SharingIsCaring/.../Power MCP Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Template)
- Original Power MCP post: [Power MCP: run MCP inside a Power Platform custom connector](https://troystaylor.com/power%20platform/custom%20connectors/2026-01-20-power-mcp-custom-connector.html)
- MCP Apps variant: [MCP Apps support in Power MCP template](https://troystaylor.com/power%20platform/mcp/custom%20connectors/2026-01-27-mcp-apps-power-mcp-template.html)
- MCP specification: [modelcontextprotocol.io](https://modelcontextprotocol.io/)
