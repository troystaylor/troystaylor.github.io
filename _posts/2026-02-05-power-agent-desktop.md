---
layout: post
title: "Power Agent Desktop: a native Windows client for Copilot Studio agents"
date: 2026-02-05 10:00:00 -0600
categories: [Copilot Studio, Power Platform]
tags: [copilot-studio, electron, mcp, voice, adaptive-cards, m365-agents-sdk]
---

Ever wanted a dedicated desktop app for your Copilot Studio agents—one with voice input, adaptive cards, and the ability to connect your local MCP clients with your agent? Power Agent Desktop does exactly that.

## What it does

Power Agent Desktop is a native Windows app built with Electron that connects to Microsoft Copilot Studio agents. It uses the official M365 Agents SDK to provide a rich conversational experience outside the browser—complete with adaptive cards, speech-to-text input, and text-to-speech responses.

The app goes beyond a simple chat window. It implements the Model Context Protocol (MCP), which means other AI clients on your machine can connect to your Copilot Studio agent. Start a conversation in Power Agent Desktop, then continue it from Claude Desktop or any other MCP-compatible client. Your agent becomes a shared resource across your local AI ecosystem.

Voice interaction is a first-class feature. The Azure Speech SDK powers both speech-to-text and text-to-speech, with smart microphone selection that automatically prefers raw audio devices over virtual ones (great if you use Elgato Wave Link or similar audio routing software). 

Here's what's included:

- 🎤 **Voice I/O** — Speech-to-text and text-to-speech via Azure Speech SDK
- 🃏 **Adaptive Cards** — Rich UI rendering with Microsoft SDK v3.0.5
- 🔌 **MCP Protocol** — Expose your agent to other local AI clients like Claude Desktop
- 🎨 **Fluent 2 UI** — Native Windows look with light/dark theme toggle
- ♿ **Accessibility** — WCAG 2.0 compliant with full keyboard navigation

![App Screenshot](https://github.com/troystaylor/SharingIsCaring/raw/main/Power%20Agent%20Desktop/docs/images/app-screenshot.png)

## Quick start

### Prerequisites

```powershell
# Node.js 18+ required
node --version

# Optional: Install WinApp CLI for MSIX packaging
winget install Microsoft.WinAppCli
```

### Configure environment

Copy the template and add your values:

```bash
cd src
cp .env.example .env
```

Edit `src/.env` with your configuration:

```bash
# Copilot Studio Connection (Option 1: Direct Connect URL)
directConnectUrl=https://YOUR_REGION.api.powerplatform.com/...

# Or Option 2: Manual Configuration
environmentId=your-environment-id
schemaName=your-agent-schema-name

# Azure Entra ID App Registration
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id

# Voice I/O (Optional)
AZURE_SPEECH_RESOURCE_ID=/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.CognitiveServices/accounts/xxx
AZURE_SPEECH_REGION=eastus
```

### Install and run

```bash
cd src
npm install
npm run build:all
npm run start:desktop
```

The app launches, starts the MCP server as a child process, opens authentication, and auto-starts conversation once authenticated.

## Azure app registration setup

1. **Create app registration** — Go to Azure Portal > App registrations > New registration
   - Name: `Power Agent Desktop`
   - Supported account types: Single tenant
   - Redirect URI: Public client/native > `http://localhost`

2. **Configure API permissions**:

   | API | Permission | Type |
   |-----|------------|------|
   | Microsoft Graph | User.Read | Delegated |
   | Power Platform API | CopilotStudio.Copilots.Invoke | Delegated |
   | Microsoft Cognitive Services | user_impersonation | Delegated |

3. **Enable public client** — Authentication > Advanced settings > Allow public client flows > Yes

4. **Copy IDs** — Note your Application (client) ID and Directory (tenant) ID for the `.env` file

## Voice setup

Voice uses Azure Speech SDK with Entra ID authentication:

1. **Create Azure Speech resource** — Azure Portal > Create a resource > "Speech"
2. **Assign RBAC role** — The signed-in user needs `Cognitive Services Speech User` on the Speech resource:

   ```bash
   az role assignment create \
     --assignee "user@example.com" \
     --role "Cognitive Services Speech User" \
     --scope "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.CognitiveServices/accounts/your-speech-resource"
   ```

3. **Configure environment** — Add `AZURE_SPEECH_RESOURCE_ID` and `AZURE_SPEECH_REGION` to your `.env`

## Packaging options

### Electron Builder (recommended)

```bash
npm run build:installer
# Creates: dist/Power Agent Desktop Setup.exe
```

### WinApp CLI (MSIX)

Use MSIX when you need Package Identity for Windows AI APIs, Microsoft Store distribution, or enterprise sideloading:

```bash
npx winapp init
npx winapp create-debug-identity
npx winapp pack
```

## MCP integration

The built-in MCP server exposes these tools:

| Tool | Description |
|------|-------------|
| `chat_with_agent` | Send messages to the Copilot Studio agent |
| `get_agent_capabilities` | Query what the agent can do |
| `start_conversation` | Begin a new conversation session |
| `render_adaptive_card` | Render Microsoft Adaptive Cards |
| `render_product_grid` | Display products in a visual card grid |
| `render_widget` | Render custom HTML in a sandboxed widget |

### Connect from VS Code

Add to your VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "power-agent": {
        "command": "node",
        "args": ["C:/path/to/src/dist/mcp-server/index.js"]
      }
    }
  }
}
```

Now GitHub Copilot can chat with your Copilot Studio agent through MCP.

### Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| Alt+M | Toggle microphone |
| Alt+T | Toggle text-to-speech |
| Alt+W | Toggle wake word listening |
| Alt+S | Open/close settings |
| Escape | Close settings panel |

## Get the code

🔗 [Power Agent Desktop on GitHub](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Agent%20Desktop)

## Learn more

- [M365 Agents SDK documentation](https://learn.microsoft.com/microsoft-copilot-studio/publication-integrate-web-or-native-app-m365-agents-sdk)
- [Copilot Studio documentation](https://learn.microsoft.com/microsoft-copilot-studio/)
- [Fluent UI Web Components](https://github.com/microsoft/fluentui)
- [Electron documentation](https://www.electronjs.org/docs)
