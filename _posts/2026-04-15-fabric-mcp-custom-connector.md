---
layout: post
title: "Fabric MCP custom connector for Copilot Studio"
date: 2026-04-15 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Microsoft Fabric, MCP, Copilot Studio, Custom Connectors, Power Platform, OAuth, OBO, Azure CLI, Streamable HTTP]
description: "A workaround for the Fabric MCP connector redirect URI error in Copilot Studio—create a custom app registration with On-Behalf-Of authentication and a custom connector that uses the MCP Streamable HTTP protocol."
---

The built-in Fabric MCP connector in Copilot Studio can fail with a redirect URI error. The Microsoft-managed app registration might not include the Power Platform redirect URI, so authentication breaks before you ever reach the Fabric API.

This guide creates a custom app registration and custom connector as a workaround, with **On-Behalf-Of (OBO) authentication** so each user authenticates with their own identity. Five steps: create the service principal, register the app with OBO, build the connector, test it, and add it to your agent.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Fabric%20MCP%20Custom)

## Prerequisites

- Azure CLI (`az`) installed and signed in as a tenant admin
- Access to [make.powerapps.com](https://make.powerapps.com/) maker portal
- Microsoft Fabric capacity (F2+ or trial) with at least one workspace
- Fabric MCP server enabled in Fabric Admin Settings → Integration settings

## Step 1: Create the Fabric MCP service principal

The Fabric MCP service principal may not exist in your tenant. Create it:

```powershell
az login
az ad sp create --id 3f021233-1542-41f0-8faa-ca8aca37ace4
```

Verify it was created:

```powershell
az ad sp show --id 3f021233-1542-41f0-8faa-ca8aca37ace4 `
  --query "{name:displayName, appId:appId, enabled:accountEnabled}" -o table
```

Expected output:

```
Name                             AppId                                 Enabled
-------------------------------  ------------------------------------  ---------
Fabric Data Agent MCP Connector  3f021233-1542-41f0-8faa-ca8aca37ace4  True
```

> **Note:** If the built-in Fabric MCP connector in Copilot Studio works after this step, you don't need the custom connector below.

## Step 2: Create a custom app registration

If the built-in connector still fails with a redirect URI error, create your own app registration:

```powershell
# Create the app registration
az ad app create `
  --display-name "Fabric MCP Custom Connector" `
  --sign-in-audience "AzureADMyOrg" `
  --query "appId" -o tsv
```

Save the **App ID** from the output. Then replace `<APP_ID>` in the commands below.

### Add Fabric API permissions

```powershell
az ad app permission add `
  --id <APP_ID> `
  --api 00000009-0000-0000-c000-000000000000 `
  --api-permissions "f3076109-ca66-412a-be10-d4ee1be95d47=Scope"

az ad app permission grant `
  --id <APP_ID> `
  --api 00000009-0000-0000-c000-000000000000 `
  --scope "user_impersonation"
```

### Create a client secret

```powershell
az ad app credential reset `
  --id <APP_ID> `
  --display-name "Copilot Studio Connector" `
  --years 1 `
  --query "{appId:appId, secret:password, tenant:tenant}" -o table
```

> **Important:** Save the client secret—it won't be shown again.

### Set application ID URI

```powershell
# Get the Object ID
$appObjId = az ad app show --id <APP_ID> --query "id" -o tsv

# Set the identifier URI
@{ identifierUris = @("api://<APP_ID>") } `
  | ConvertTo-Json | Set-Content "$env:TEMP\obo-uri.json"
az rest --method PATCH `
  --url "https://graph.microsoft.com/v1.0/applications/$appObjId" `
  --body "@$env:TEMP\obo-uri.json" `
  --headers "Content-Type=application/json"
```

### Add OBO scope and authorize Azure API Connections

```powershell
# Generate a scope ID
$scopeId = [guid]::NewGuid().ToString()
Write-Host "Scope ID: $scopeId"

# Create the scope and pre-authorize Azure API Connections
@{
  api = @{
    oauth2PermissionScopes = @(
      @{
        id = $scopeId
        adminConsentDescription = "Allow Azure API Connections to obtain tokens on behalf of the user"
        adminConsentDisplayName = "Access Fabric on behalf of user"
        userConsentDescription = "Allow connector to access Fabric on your behalf"
        userConsentDisplayName = "Access Fabric as you"
        isEnabled = $true
        type = "User"
        value = "access_as_user"
      }
    )
    preAuthorizedApplications = @(
      @{
        appId = "fe053c5f-3692-4f14-aef2-ee34fc081cae"
        delegatedPermissionIds = @($scopeId)
      }
    )
  }
} | ConvertTo-Json -Depth 5 | Set-Content "$env:TEMP\obo-scope.json"

az rest --method PATCH `
  --url "https://graph.microsoft.com/v1.0/applications/$appObjId" `
  --body "@$env:TEMP\obo-scope.json" `
  --headers "Content-Type=application/json"
```

Verify:

```powershell
az ad app show --id <APP_ID> --query "api" -o json
```

You should see `access_as_user` in `oauth2PermissionScopes` and `fe053c5f-3692-4f14-aef2-ee34fc081cae` (Azure API Connections) in `preAuthorizedApplications`.

Save these values for the next step:

- App (Client) ID
- Client Secret
- Tenant ID

## Step 3: Create the custom connector in Power Apps

1. Go to [make.powerapps.com](https://make.powerapps.com/) → Custom connectors → + New → Create from blank
2. Name: `Fabric MCP Custom Connector`

### General tab

| Setting | Value |
|---------|-------|
| Scheme | HTTPS |
| Host | `api.fabric.microsoft.com` |
| Base URL | `/v1/mcp` |

### Security tab

| Setting | Value |
|---------|-------|
| Authentication type | OAuth 2.0 |
| Identity provider | Azure Active Directory |
| Client ID | `<APP_ID>` from Step 2 |
| Client Secret | `<CLIENT_SECRET>` from Step 2 |
| Resource URL | `https://api.fabric.microsoft.com` |
| **Enable on-behalf-of login** | **true** |
| **Scope** | `https://api.fabric.microsoft.com/.default` |

3. Click **Create connector** (or **Update connector**)
4. Copy the generated **Redirect URL** from the security page

### Add the redirect URI to your app registration

```powershell
# Replace <APP_ID> and <REDIRECT_URI> with your values
az ad app update `
  --id <APP_ID> `
  --web-redirect-uris "<REDIRECT_URI>"
```

Verify:

```powershell
az ad app show --id <APP_ID> --query "web.redirectUris" -o json
```

### Definition tab

Import the operation definition from the MCP Streamable HTTP swagger:

1. Click **Swagger Editor** toggle (top of the Definition tab)
2. Replace the contents with:

```json
{
  "swagger": "2.0",
  "info": {
    "title": "Fabric MCP Custom Connector",
    "description": "This MCP Server will work with Streamable HTTP and is meant to work with Microsoft Copilot Studio",
    "version": "1.0.0"
  },
  "host": "api.fabric.microsoft.com",
  "basePath": "/v1/mcp",
  "schemes": ["https"],
  "paths": {
    "/": {
      "post": {
        "summary": "MCP Server Streamable HTTP",
        "x-ms-agentic-protocol": "mcp-streamable-1.0",
        "operationId": "InvokeMCP",
        "responses": {
          "200": {
            "description": "Success"
          }
        }
      }
    }
  },
  "securityDefinitions": {}
}
```

The `x-ms-agentic-protocol: mcp-streamable-1.0` property tells Copilot Studio to handle the connector as a native MCP tool—it automatically discovers and exposes the Fabric MCP server's tools to the agent.

3. Click **Update connector** to save

## Step 4: Test the connector

1. Go to the **Test** tab in the custom connector
2. Click **+ New connection** → sign in with your Entra ID account
3. Test with these request bodies:

**Initialize:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": {
      "name": "CopilotStudio",
      "version": "1.0.0"
    }
  }
}
```

**List available tools:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**List workspaces:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "fabric_list_workspaces",
    "arguments": {}
  }
}
```

## Step 5: Add to Copilot Studio

1. In Copilot Studio → your agent → **Tools** → **+ Add a Tool**
2. Search for your custom connector name
3. Select the **InvokeMCP** action
4. Configure the connection
5. With OBO enabled, users are prompted to sign in once—the agent then accesses Fabric with their identity and permissions
6. Enable **Generative AI orchestration** under Settings
7. **Publish** the agent

## How OBO authentication works

```
User → Copilot Studio Agent → Custom Connector → Azure API Connections
                                                        │
                                                        ▼
                                                 OBO token exchange
                                                  (user's identity)
                                                        │
                                                        ▼
                                                Fabric MCP Server
                                              (user's RBAC permissions)
```

- Each user authenticates once in the agent conversation
- Fabric API calls execute with **their** permissions (RBAC)
- No shared service account—proper audit trail per user
- Users can't access workspaces or data they don't have Fabric permissions for

## Troubleshooting

| Error | Fix |
|-------|-----|
| AADSTS50011: redirect URI mismatch | Copy the redirect URI from the custom connector security page and add it to the app registration with `az ad app update` |
| AADSTS65001: consent required | Run `az ad app permission grant` as shown in Step 2 |
| 401 Unauthorized | Verify the Resource URL is `https://api.fabric.microsoft.com` and the API permission is granted |
| Service principal not found | Run `az ad sp create --id 3f021233-1542-41f0-8faa-ca8aca37ace4` |
| Azure API Connections SP missing | A tenant admin needs to provision it—see [Microsoft docs](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/add-manage-connections#step-1-provision-microsofts-azure-api-connections-service-principal-in-your-microsoft-entra-tenant) |
| Connector times out | Ensure the Fabric MCP server is enabled in Fabric Admin Settings → Integration settings |

## Resources

- [MCP Streamable HTTP swagger](https://github.com/troystaylor/PowerPlatformConnectors/blob/dev/custom-connectors/MCP-Streamable-HTTP/apiDefinition.swagger.json)
- [Microsoft Fabric documentation](https://learn.microsoft.com/en-us/fabric/)
- [Full source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Fabric%20MCP%20Custom)
