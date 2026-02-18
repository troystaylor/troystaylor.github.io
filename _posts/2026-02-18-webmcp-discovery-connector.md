---
layout: post
title: "WebMCP Discovery connector for Power Platform"
date: 2026-02-18 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [WebMCP, MCP, Custom Connectors, Power Platform, Copilot Studio, Playwright, Browser Automation, Web Scraping]
description: "Power Platform custom connector that discovers and executes WebMCP tools from any web page, with Playwright browser automation as a fallback for traditional sites."
---

Most websites don't have APIs. Even when they do, they're often incomplete—missing endpoints for the exact data you need, or requiring enterprise contracts to access. But every website has a UI. If a human can click through it, an agent should be able to as well.

The traditional approach is screen scraping: parse HTML, find elements by CSS selectors, extract text. It works, but it's brittle. A site redesign breaks everything. A/B tests cause intermittent failures. Dynamic content loaded by JavaScript never appears in the initial HTML.

WebMCP changes this. It's a browser specification that lets websites expose structured tools for AI agents—like an API, but running in the browser context with full access to the page's JavaScript environment. A site registers tools with names, descriptions, and input schemas. An agent discovers them, calls them, and gets structured responses back.

The catch: almost no sites implement WebMCP yet. So this connector takes a hybrid approach. It checks if the target page has WebMCP tools. If yes, it uses them. If not, it falls back to Playwright browser automation—headless Chromium controlled by the agent. The agent can click, type, scroll, screenshot, and extract text from any website, WebMCP or not.

Microsoft recently added [Computer use (preview)](https://learn.microsoft.com/microsoft-copilot-studio/computer-use) to Copilot Studio—their approach uses Computer-Using Agents (CUA), an AI model that takes screenshots and reasons about what to click. It's impressive, but it runs on Microsoft-managed infrastructure with usage throttling, costs 5 Copilot Credits per step, and doesn't support custom desktop apps or enterprise resource access in the hosted browser mode. This connector takes a different approach: self-hosted Playwright on Azure Container Apps that scales to zero when idle, with full control over networking, authentication, and the domains your agent can access. It also prioritizes WebMCP structured tools over CUA's pixel-based vision when available.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/WebMCP%20Discovery).

## How it works

```
Power Automate / Copilot Studio
            ↓
   WebMCP Discovery Connector
            ↓
    WebMCP Broker Service (Azure Container Apps)
            ↓
     Headless Chromium (Playwright)
            ↓
       Target Website
            ↓
    WebMCP tools OR Playwright fallback
```

The connector calls a broker service running in Azure Container Apps. The broker launches a headless browser, navigates to the target URL, and checks if the page implements WebMCP. If it does, the connector returns the structured tools that the page exposes. If not, it returns Playwright browser automation tools as a fallback.

## What's WebMCP?

WebMCP is a [browser specification](https://webmachinelearning.github.io/webmcp/) that lets websites expose AI-friendly tools. A site registers tools like this:

```javascript
navigator.modelContext.registerTool({
  name: "search_products",
  description: "Search the product catalog",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Search query" }
    },
    required: ["query"]
  },
  handler: async (input) => {
    return await fetch(`/api/search?q=${input.query}`).then(r => r.json());
  }
});
```

When a site implements WebMCP, the connector calls these structured tools directly—no screen scraping required. The handler runs in the browser context with full access to the page's JavaScript environment.

## Operations

### Discovery

| Operation | Description |
|-----------|-------------|
| Discover Tools | Scan a URL for WebMCP tools or get Playwright fallback tools |

### Sessions

| Operation | Description |
|-----------|-------------|
| Create Session | Start a persistent browser session |
| Get Session | Check session status and available tools |
| Close Session | End session and release resources |
| Navigate | Go to a new URL within session |
| List Session Tools | Get tools available on current page |

### Execution

| Operation | Description |
|-----------|-------------|
| Call Tool (Session) | Execute a tool within a session |
| Execute Tool (Stateless) | One-shot tool execution without session |

### Authentication

| Operation | Description |
|-----------|-------------|
| Inject Authentication | Set cookies, localStorage, or headers |

### Utility

| Operation | Description |
|-----------|-------------|
| Take Screenshot | Capture current page state |

## MCP tools for Copilot Studio

### High-level tools

| Tool | Description |
|------|-------------|
| `discover_tools` | Find available tools on a page |
| `create_session` | Start a browser session |
| `call_tool` | Execute any discovered tool |
| `execute_stateless` | One-shot execution |

### Playwright fallback tools

When a page doesn't implement WebMCP, these browser automation tools are available:

| Tool | Description |
|------|-------------|
| `browser_navigate` | Go to a URL |
| `browser_click` | Click an element |
| `browser_type` | Type into an input |
| `browser_select` | Select from dropdown |
| `browser_get_text` | Extract text content |
| `browser_get_attribute` | Get element attribute |
| `browser_screenshot` | Capture page |
| `browser_evaluate` | Run JavaScript |
| `browser_wait_for_selector` | Wait for element |
| `browser_scroll` | Scroll page/element |

### High-level action tools

Simplified tools that combine multiple browser actions:

| Tool | Description |
|------|-------------|
| `browser_login` | Fill username + password and submit |
| `browser_fill_form` | Fill multiple fields by label/name mapping |
| `browser_search_page` | Type into search box and submit |
| `browser_checkout` | Multi-step form fill (shipping, payment) |

### Smart selector tools

Find and interact with elements using human-readable descriptions:

| Tool | Description |
|------|-------------|
| `browser_click_text` | Click element by visible text content |
| `browser_click_nearest` | Click element nearest to a reference element |
| `browser_smart_fill` | Fill inputs by matching visible labels |

### Error recovery and recording

| Tool | Description |
|------|-------------|
| `browser_auto_retry` | Execute action with auto-retry and scroll-into-view |
| `browser_record_actions` | Start recording all page interactions |
| `browser_replay_actions` | Replay a recorded action sequence |

## Example flows

### Discover and execute WebMCP tools

```
1. Discover Tools from URL "https://example.com/app"
   ↓
2. Response shows WebMCP tools: ["search_products", "add_to_cart", "checkout"]
   ↓
3. Call Tool: search_products with input { "query": "laptop" }
   ↓
4. Response: { "products": [...] }
```

### Fallback to Playwright for traditional sites

```
1. Discover Tools from URL "https://legacy-site.com"
   ↓
2. Response: hasWebMCP = false, tools = [browser_click, browser_type, ...]
   ↓
3. Create Session with URL
   ↓
4. browser_type { selector: "#search", text: "laptop", submit: true }
   ↓
5. browser_get_text { selector: ".results-count" }
   ↓
6. Close Session
```

### Authenticated session

```
1. Create Session for "https://app.example.com/login"
   ↓
2. Inject Auth: cookies from your auth flow
   ↓
3. Navigate to "/dashboard"
   ↓
4. List Session Tools (now shows authenticated tools)
   ↓
5. Call Tool: get_user_data
   ↓
6. Close Session
```

## Deployment

### Deploy the broker service

```bash
cd broker-service

# Build the Docker image
docker build -t webmcp-broker:latest .

# Push to your container registry
docker tag webmcp-broker:latest ghcr.io/your-org/webmcp-broker:latest
docker push ghcr.io/your-org/webmcp-broker:latest

# Deploy to Azure Container Apps
az deployment group create \
  --resource-group your-resource-group \
  --template-file infra/main.bicep \
  --parameters apiKey="your-secure-api-key" \
               containerImage="ghcr.io/your-org/webmcp-broker:latest"
```

### Import the connector

1. Go to [Power Automate](https://make.powerautomate.com/) → Custom connectors.
2. Import from OpenAPI file: upload `apiDefinition.swagger.json`.
3. Create a connection with:
   - **Broker Service URL:** `https://your-app.azurecontainerapps.io`
   - **API Key:** The key you set during deployment

## Security

The broker service includes a full enterprise security stack.

### Authentication

Set `AUTH_MODE` environment variable:

| Mode | Description |
|------|-------------|
| `apikey` (default) | API key via X-API-Key header |
| `managed-identity` | Azure AD / Entra ID Bearer tokens only |
| `both` | Accepts either API key or Bearer token |

### Role-based access control

Set `RBAC_ENABLED=true` and configure `API_KEYS` as a JSON mapping:

```json
{
  "admin_key123": "admin",
  "user_key456": "user",
  "viewer_key789": "viewer"
}
```

| Role | Access |
|------|--------|
| `admin` | Full access: all tools, recording, config |
| `user` | All tools except browser_evaluate, tracing |
| `viewer` | Read-only: screenshots, getText, getPage—no navigation |

### URL allowlisting (SSRF protection)

Controls which domains the broker can navigate to:

| Variable | Description |
|----------|-------------|
| `ALLOWED_DOMAINS` | Comma-separated allowlist (empty = allow all) |
| `BLOCKED_DOMAINS` | Comma-separated blocklist |

Internal/metadata endpoints are always blocked: localhost, 127.0.0.1, 169.254.169.254 (Azure IMDS), etc.

### Network egress control

Set `NETWORK_EGRESS_CONTROL=true` (default) to enforce URL allowlisting at the browser level using Playwright route interception. All outbound requests from the browser—including sub-resources, XHR, images—are checked against the allowlist.

### Data redaction

Automatically masks sensitive data in tool results and logs:

| Variable | Description |
|----------|-------------|
| `REDACTION_FIELDS` | Field names to mask (default: password, ssn, credit_card, api_key, secret, token, authorization) |
| `REDACTION_PATTERNS` | Additional regex patterns (comma-separated) |

Built-in patterns detect credit card numbers, SSNs, emails, phone numbers, bearer tokens, and API key values. Screenshots automatically blur sensitive form fields.

### Audit logging

Set `AUDIT_LOG_LEVEL`:

| Level | What's logged |
|-------|---------------|
| `none` | No logging |
| `basic` (default) | Method, path, status, duration |
| `detailed` | + tool names, success/fail, page changes |
| `full` | + full request/response metadata |

Set `AZURE_MONITOR_ENDPOINT` to send audit entries to Azure Monitor / Log Analytics.

### Private networking (VNet)

Deploy with `enableVnet=true` in Bicep to:
- Create a VNet with Container Apps and private endpoint subnets
- Make the Container App internal-only (no public ingress)
- Set up private DNS zone for internal resolution

```bash
az deployment group create \
  --resource-group your-rg \
  --template-file infra/main.bicep \
  --parameters apiKey="your-key" \
               enableVnet=true \
               allowedDomains="example.com,contoso.com" \
               rbacEnabled=true \
               auditLogLevel="detailed"
```

## Cost considerations

- **Azure Container Apps:** Scale to zero when idle = ~$0 when not in use
- **Active usage:** ~$0.000016/vCPU-second, ~$0.000002/GiB-second
- **Typical session:** ~$0.01 for a 5-minute browser session
- Premium connector billing may apply in Power Platform

## Alternative hosting options

> **Note:** Microsoft Playwright Testing will be retired on March 8, 2026. If you were considering it as a managed backend, use [Azure App Testing](https://learn.microsoft.com/azure/playwright-testing/) instead. This connector uses self-hosted Azure Container Apps by default.

| Option | Pros | Cons |
|--------|------|------|
| Azure Container Apps (default) | Scale-to-zero, full control, low cost | Self-managed |
| Azure App Testing | Microsoft-managed Playwright | Additional service dependency |
| Azure Kubernetes Service | Enterprise-grade, existing infrastructure | More complex setup |

## Try it yourself

The complete connector code is available in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/WebMCP%20Discovery):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/WebMCP%20Discovery/apiDefinition.swagger.json) — OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/WebMCP%20Discovery/script.csx) — Connector script with MCP tools
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/WebMCP%20Discovery/apiProperties.json) — Connector metadata
- [broker-service/](https://github.com/troystaylor/SharingIsCaring/tree/main/WebMCP%20Discovery/broker-service) — Dockerized Playwright broker
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/WebMCP%20Discovery/readme.md) — Full documentation

## Resources

- [WebMCP specification](https://webmachinelearning.github.io/webmcp/)
- [Playwright documentation](https://playwright.dev/)
- [Azure Container Apps](https://docs.microsoft.com/azure/container-apps/)
- [Azure App Testing (Playwright)](https://learn.microsoft.com/azure/playwright-testing/)
- [Power Platform custom connectors](https://docs.microsoft.com/connectors/custom-connectors/)
