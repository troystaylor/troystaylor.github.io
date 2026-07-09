---
layout: post
title: "Building an ACA Playwright connector for Power Platform and Copilot Studio"
date: 2026-07-09 10:00:00 -0500
categories: [Power Platform, MCP]
tags: [ACA Sandboxes, MCP, Copilot Studio, Custom Connectors, Playwright, Browser Automation, Power Automate]
description: "A dual-mode Power Platform custom MCP connector that runs Playwright browser automation in isolated Azure Container Apps Sandbox microVMs. Navigate pages, take screenshots, fill forms, extract content, generate PDFs, and run arbitrary Playwright scripts — from Power Automate flows and Copilot Studio agents."
---

Browser automation from Power Automate has always meant desktop flows, attended RPA sessions, or external services. What if your flow could spin up a headless Chromium browser in an isolated cloud microVM, navigate to a page, fill a form, take a screenshot, and tear it down — all without a desktop or VM license?

This connector puts Playwright inside Azure Container Apps Sandboxes. Each session boots a fresh Linux microVM with Node.js 22, Playwright, and Chromium pre-installed. The browser runs headless, state persists across operations within a session, and the sandbox auto-suspends after 10 minutes idle.

## Operations

The connector exposes 11 typed operations plus an MCP endpoint:

| Operation | Purpose |
|-----------|---------|
| Create Browser Session | Boot a sandbox with custom viewport, user agent, locale, and HAR recording |
| Navigate to URL | Navigate with configurable wait conditions (load, DOMContentLoaded, networkidle) |
| Take Screenshot | Full page or element screenshot as PNG/JPEG |
| Click Element | Click by CSS, XPath, or Playwright locator with optional post-click wait |
| Fill Form Fields | Fill multiple inputs by selector/value pairs |
| Extract Content | Extract text, HTML, or attributes from elements |
| Run Playwright Script | Execute arbitrary Playwright JavaScript with full API access |
| Generate PDF | Export page as PDF with paper format, orientation, and background options |
| Get Console Log | Retrieve browser console messages from the session |
| Download Artifact | Download any file from the sandbox workspace |
| Destroy Session | Tear down sandbox and free resources |

The MCP endpoint (`/mcp`) exposes all 11 as tools for Copilot Studio agents.

## How it works under the hood

Each operation generates a self-contained Node.js script that:

1. Launches Chromium headless with `ignoreHTTPSErrors: true`
2. Loads saved browser state (cookies, localStorage) from `/workspace/.browser-state.json`
3. Restores the last visited URL from `/workspace/.last-url.txt`
4. Performs the requested action
5. Saves browser state and URL back to disk
6. Closes the browser

Scripts execute via the ACA Sandbox `executeShellCommand` API with `NODE_PATH` set so globally installed Playwright resolves correctly. The browser launches fresh on each operation (~1–2s overhead per call), but state persistence means you don't lose cookies or localStorage between steps.

## Persistent state across operations

This is the key design decision. Within a session, browser state carries forward:

```
1. Create Browser Session → sessionId: "abc123"
2. Navigate to URL → "https://app.example.com/login"
3. Fill Form Fields → [username: "user@zava.com", password: "***"]
4. Click Element → "#login-button"
5. Navigate to URL → "https://app.example.com/dashboard"
   (cookies from login persist — no re-authentication needed)
6. Take Screenshot → full page dashboard capture
7. Extract Content → "#revenue-total" → "$1,234,567"
8. Destroy Session
```

Each step picks up where the last one left off. The session maintains the authenticated browser context across all operations.

## Run Playwright Script

For scenarios that go beyond the typed operations, `Run Playwright Script` lets you execute arbitrary Playwright JavaScript:

```javascript
const table = await page.locator('table#results');
const rows = await table.locator('tr').all();
const data = [];
for (const row of rows) {
  const cells = await row.locator('td').allTextContents();
  data.push(cells);
}
console.log(JSON.stringify(data));
```

The script runs in a Node.js context with the full Playwright API available. Output goes to stdout, which the connector captures and returns.

## Disk image setup

The sandbox runs a custom disk image with Playwright and Chromium pre-installed (~2.4 GB). Build it in ACR using remote build:

```powershell
az acr build `
    --registry <your-acr-name> `
    --resource-group <your-rg> `
    --image playwright-sandbox:latest `
    --file Dockerfile .
```

Then register it as a disk image via the ACA Sandboxes data plane API. The response includes a GUID — set it as `ACA_DISK_IMAGE` in `script.csx`.

## Deployment

PAC CLI 2.8.1 has a known bug with OAuth `connectionParameters` in apiProperties.json. Deploy in two steps:

1. Deploy with PAC CLI (swagger + script only):

```powershell
pac connector create `
    -df "apiDefinition.swagger.json" `
    -pf "apiProperties.json" `
    -sf "script.csx" `
    -env <environment-id>
```

2. Configure OAuth in the portal Security tab:
   - Identity Provider: Azure Active Directory
   - Client ID: your Entra app client ID
   - Client Secret: your Entra app secret
   - Resource URL: `https://dynamicsessions.io`
   - Scope: `https://dynamicsessions.io/.default offline_access`

## Resource recommendations

| Scenario | CPU | Memory |
|----------|-----|--------|
| Simple screenshots/extraction | 2000m | 4096Mi |
| Complex SPAs, heavy JavaScript | 4000m | 8192Mi |

Playwright with Chromium needs more resources than a typical code execution sandbox. Start with 2 vCPU / 4 GiB and scale up if pages load slowly.

## Use cases

**Competitive monitoring** — A scheduled flow navigates to competitor pricing pages, extracts content, and stores it in Dataverse for trend analysis. No RPA license needed.

**Automated compliance screenshots** — Before a deployment goes live, a flow captures screenshots of every critical page and attaches them to the approval record.

**Form submission automation** — Fill and submit web forms from Power Automate for systems that don't have APIs. The connector handles login, navigation, form filling, and confirmation capture.

**Copilot Studio web research agent** — An agent navigates to URLs, extracts relevant content, takes screenshots, and summarizes findings — all conversationally via MCP tools.

**PDF report generation** — Navigate to a dashboard, wait for data to load, and export as PDF with custom paper format and orientation.

## Known limitations

- Browser launches fresh on each operation (~1–2s overhead per call)
- No video recording (would require a persistent process)
- Chromium only (Firefox/WebKit not pre-installed to save image size)
- Sandbox Chromium does not trust system CA certs — `ignoreHTTPSErrors: true` is set on all browser contexts

The full source is available in the [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/ACA%20Playwright).
