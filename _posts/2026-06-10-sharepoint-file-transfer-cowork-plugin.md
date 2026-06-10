---
layout: post
title: "SharePoint File Transfer Cowork plugin: upload files from any URL into SharePoint"
date: 2026-06-10 14:00:00 -0000
categories: [MCP (Model Context Protocol), Copilot Studio, Integration]
tags: [SharePoint, Microsoft Graph, MCP, Copilot Cowork, Azure Container Apps, File Transfer]
---

## What this plugin does

The SharePoint File Transfer Cowork plugin manages files across SharePoint from Copilot Cowork. Browse sites, document libraries, and folders. Upload files from public HTTPS URLs — small files upload inline, large files (250 MB+) stream in the background with resumable chunked uploads. Copy files and folders across sites and libraries with no size limit. Move and rename items within a library, create folders, set metadata columns, and generate sharing links.

The plugin is backed by a .NET MCP server deployed to Azure Container Apps with Microsoft Entra SSO and On-Behalf-Of (OBO) token exchange for Microsoft Graph.

### Key capabilities

- **Browse** any SharePoint site, library, and folder the signed-in user has access to
- **Upload** files from any publicly reachable HTTPS URL (GitHub releases, CDN links, public downloads) into any SharePoint library the user can write to
- **Copy** files and folders across sites and libraries — `copy_item` uses Graph's native async copy, so there's no file size limit and no download/re-upload
- **Move / rename** items within the same document library
- **Create folders**, **set metadata** columns, and **generate sharing links**
- **Resume** or **cancel** large in-flight uploads

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/SharePoint%20File%20Transfer)

## Architecture

The runtime flow is straightforward:

```
Copilot Cowork ──SSO token──▶ Azure Container App (MCP server)
                                 │
                                 ├─ OBO exchange ──▶ Microsoft Graph (SharePoint)
                                 └─ Managed Identity ──▶ Azure Table Storage (session tracking)
```

The SSO token from Cowork gets exchanged via OBO for a Graph token scoped to SharePoint. Upload sessions are tracked in Azure Table Storage so large chunked uploads can resume after failures.

## MCP tools

The plugin exposes 15 tools covering the full file lifecycle:

| Tool | Description |
|------|-------------|
| `list_sites` | Search SharePoint sites the signed-in user can access |
| `list_drives` | List document libraries (drives) inside a SharePoint site |
| `list_folder` | List items in a folder within a drive |
| `get_item` | Get a drive item's metadata |
| `upload_from_url` | Server-side ingest from a public HTTPS URL into SharePoint |
| `start_upload_session` | Create a Graph upload session and return the pre-signed upload URL |
| `resume_upload_from_url` | Resume a failed or partial upload |
| `get_upload_status` | Check status of an in-flight or completed upload |
| `cancel_upload` | Cancel an in-flight upload session |
| `create_folder` | Create a new folder inside a drive |
| `move_item` | Move and/or rename an item within the same drive |
| `set_metadata` | Set SharePoint list-item column values on a drive item |
| `copy_item` | Copy a file or folder to another drive/site (async, cross-site supported) |
| `check_copy_status` | Check progress of an async copy operation |
| `create_link` | Create a shareable link for a SharePoint item |

That tool surface covers four workflow patterns: browse and discover, upload and transfer, copy across sites, and organize and share.

### Current limitations

- **Move is same-drive only.** `move_item` moves items within a single document library. For cross-library or cross-site moves, use `copy_item` followed by deleting the original (not yet automated as a single tool).

## Why resumable uploads matter

Graph's simple upload endpoint caps out at 250 MB. For anything larger, you need a chunked upload session. The plugin handles that automatically — `upload_from_url` picks the right strategy based on file size, and `start_upload_session` gives you explicit control when you need it.

If a large upload fails mid-stream, `resume_upload_from_url` picks up where it left off. `get_upload_status` lets you monitor progress without polling the MCP server directly.

## Cross-site copy with no size limit

The `copy_item` tool uses Graph's native async copy operation. The file never downloads to the MCP server and re-uploads — Graph handles the copy server-side. That means no file size limit and no timeout risk for large files. Use `check_copy_status` to monitor progress on long-running copies.

## Deploy to Azure

The deployment uses Azure Developer CLI (`azd`) and Bicep templates:

### 1. Create the Entra app registration

Register a multi-tenant app in Microsoft Entra ID with these delegated Microsoft Graph permissions (admin consent required):

- `Sites.ReadWrite.All`
- `Files.ReadWrite.All`
- `Sites.Read.All`
- `User.Read`

Expose an API scope (for example, `access_as_user`) and note the Application ID URI.

### 2. Provision and deploy

```bash
azd init
azd provision
azd deploy
```

This creates a resource group, Azure Container Registry, Container Apps environment with a container app, Azure Storage account with an `uploadSessions` table, Application Insights, and RBAC assignments for ACR pull and Table Data Contributor.

### 3. Configure OBO credentials

After deployment, add the OBO client ID and secret to the container app:

```bash
CA_NAME="<container-app-name>"
RG_NAME="<resource-group-name>"

# Add the client secret as a Container App secret
az containerapp secret set -n $CA_NAME -g $RG_NAME \
  --secrets obo-client-secret="<your-client-secret>"

# Set environment variables
az containerapp update -n $CA_NAME -g $RG_NAME \
  --set-env-vars \
    OBO_CLIENT_ID="<your-client-id>" \
    OBO_CLIENT_SECRET=secretref:obo-client-secret
```

Use `secretref:` for the client secret — plain-text env vars get overwritten by `azd deploy`.

### 4. Register the Cowork plugin

1. Update `manifest.json` — replace `{{GUID}}`, `<YOUR-CONTAINER-APP-FQDN>`, and `<YOUR-OAUTH-REFERENCE-ID>`
2. Package: `Compress-Archive -Path manifest.json, color.png, outline.png, skills -DestinationPath "SharePoint File Transfer.zip"`
3. Upload the `.zip` in M365 Admin Center > Settings > Integrated apps > Upload custom apps
4. Grant admin consent when prompted

## Project structure

```
├── azure.yaml              # azd service definition
├── manifest.json           # Cowork plugin manifest
├── color.png               # Plugin icon (color)
├── outline.png             # Plugin icon (outline)
├── infra/                  # Bicep infrastructure-as-code
│   ├── main.bicep
│   ├── main.parameters.json
│   └── modules/
├── server/                 # .NET MCP server
│   ├── Program.cs
│   ├── Dockerfile
│   ├── Auth/               # SSO + OBO token exchange
│   ├── Endpoints/          # MCP JSON-RPC endpoint
│   ├── Graph/              # Graph client, upload runner, session store
│   └── Tools/              # MCP tool implementations
└── skills/                 # Cowork agent skill definitions
```

## Why this pattern is useful

Moving files into SharePoint is a surprisingly common workflow step. Reports land on external portals, vendors share files via download links, data pipelines produce artifacts at public endpoints. Today those files get downloaded to a laptop, then manually uploaded to SharePoint.

This plugin lets Copilot handle that transfer server-side. The file streams directly from the source URL into SharePoint through the MCP server — it never touches the user's machine. That's faster, works for large files, and leaves an audit trail in SharePoint.

The cross-site copy capability fills another gap. Reorganizing files across SharePoint sites normally means downloading and re-uploading. With `copy_item`, Graph handles the copy natively — no data leaves Microsoft's infrastructure.

The resumable upload pattern also makes this viable for production workloads where network reliability isn't guaranteed.

## Resources

- [SharePoint File Transfer Cowork plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/SharePoint%20File%20Transfer)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
- [Copilot Cowork plugin development](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
- [Plugin authentication](https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-authentication)
- [Microsoft Graph DriveItem upload](https://learn.microsoft.com/graph/api/driveitem-createuploadsession?view=graph-rest-1.0)
