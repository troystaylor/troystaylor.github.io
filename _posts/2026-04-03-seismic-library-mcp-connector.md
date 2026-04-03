---
layout: post
title: "Seismic Library Content Management MCP connector for Power Platform"
date: 2026-04-03 22:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Seismic, Content Management, MCP, Copilot Studio, Custom Connectors, Power Platform, Sales Enablement]
description: "Power Platform custom connector for Seismic Library Content Management—manage files, folders, URLs, and teamsites through MCP tools and 24 REST operations."
---

Sales teams live in Seismic. Their decks, case studies, battle cards, and training materials are all organized in Library teamsites. But connecting that content to Power Platform workflows has meant building custom integrations from scratch.

This connector wraps the Seismic Library Content Management API with MCP tools for Copilot Studio and 24 REST operations for Power Automate and Power Apps. Upload files, browse folders, download content, manage metadata, query items, handle versioning, and copy content across folders—all from one connector.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Seismic%20Library%20Content%20Management)

## Tools

### MCP tools for Copilot Studio

The MCP endpoint exposes tools for browsing and managing library content conversationally:

- List teamsites and browse their folder structures
- Query items by name, type, or modification date
- Get file and folder metadata with custom properties
- Download file content
- Create folders and upload files
- Update metadata (name, description, owner, expiration)
- Delete items

### How it works

```
User: "What teamsites do we have?"

1. Agent calls list_teamsites
   → Returns list of teamsites with IDs and names

User: "Show me the files in the Q4 Assets folder"

2. Agent calls list_folder_items({
     teamsiteId: "...",
     folderId: "..."
   })
   → Returns files, folders, and URLs in that folder
     with names, types, and modification dates

User: "Download the latest sales deck"

3. Agent calls download_file({
     teamsiteId: "...",
     fileId: "..."
   })
   → Returns download URL and base64 content
```

## REST operations for Power Automate and Power Apps

### Teamsite operations (2)

| Operation | Operation ID | Method |
|-----------|-------------|--------|
| List Teamsites | `ListTeamsites` | GET |
| Get Teamsite | `GetTeamsite` | GET |

### File operations (7)

| Operation | Operation ID | Method |
|-----------|-------------|--------|
| Add a File | `AddFile` | POST |
| Get File Information | `GetFileInfo` | GET |
| Update File Information | `UpdateFileInfo` | PATCH |
| Download a File | `DownloadFile` | GET |
| Add a New File Version | `AddFileVersion` | PUT |
| Download a File Version | `DownloadFileVersion` | GET |
| Copy a File | `CopyFile` | POST |

### Folder operations (6)

| Operation | Operation ID | Method |
|-----------|-------------|--------|
| Add a Folder | `AddFolder` | POST |
| Get Folder Information | `GetFolderInfo` | GET |
| Update Folder Information | `UpdateFolderInfo` | PATCH |
| List Items in a Folder | `ListFolderItems` | GET |
| Copy a Folder | `CopyFolder` | POST |
| Get or Create Folder by Path | `GetOrCreateFolderByPath` | PUT |

### Item operations (5)

| Operation | Operation ID | Method |
|-----------|-------------|--------|
| Get Item Information | `GetItemInfo` | GET |
| Delete an Item | `DeleteItem` | DELETE |
| Query Items | `QueryItems` | GET |
| Get Item Versions | `GetItemVersions` | GET |
| Copy an Item | `CopyItem` | POST |

### URL operations (4)

| Operation | Operation ID | Method |
|-----------|-------------|--------|
| Add a URL | `AddUrl` | POST |
| Get URL Information | `GetUrlInfo` | GET |
| Update URL Information | `UpdateUrlInfo` | PATCH |
| Copy a URL | `CopyUrl` | POST |

### File upload and download

File uploads use base64-encoded content. The connector's script layer transforms the JSON request into the `multipart/form-data` format that the Seismic API requires. Maximum file size is 2 GB.

Downloads return both a download URL and the base64-encoded file content. For large files, use the download URL directly to avoid Power Platform response size limits.

### Version management

Every file in Seismic Library tracks versions. Use `AddFileVersion` to upload a new version of an existing file, `GetItemVersions` to list all versions, and `DownloadFileVersion` to retrieve a specific historical version.

### Folder path creation

The `GetOrCreateFolderByPath` operation takes a path string like `Marketing/Q4 Assets/Presentations` and either returns the existing folder or creates the entire path. This simplifies folder setup in automation flows—no need to check existence and create each level separately.

## Use cases

**Content distribution automation**: When a new sales deck is approved, a Power Automate flow uploads it to the right Seismic teamsite folder, sets metadata (owner, expiration, description), and assigns it to the appropriate profiles.

**Content lifecycle management**: Query items by modification date to find stale content. Flag files that haven't been updated in 90 days for review. Set expiration dates on seasonal materials so they're automatically flagged.

**Cross-platform content sync**: Download files from Seismic and push them to SharePoint, Teams, or other systems. Or pull content from other sources and upload to Seismic with proper metadata.

**Conversational content discovery**: Your Copilot Studio agent can browse teamsites, search for files by name, and retrieve content directly in conversation. A sales rep asks "Find me the latest competitive battle card for Zava" and gets the file without opening the Seismic UI.

**Bulk content organization**: Use `CopyItem`, `CopyFolder`, and `UpdateFileInfo` to reorganize content across folders. Move files, rename items, and update metadata at scale through flows.

## Prerequisites

1. A Seismic account with access to the Library Content Management API
2. An OAuth2 application registered in Seismic with `seismic.library.view` and `seismic.library.manage` scopes

## Setting up the connector

### 1. Register an OAuth2 application in Seismic

1. Log in to your Seismic tenant
2. Navigate to **Settings** > **Integration** > **API Token Management**
3. Register an OAuth2 application with the authorization code flow
4. Set the **Redirect URI** to `https://global.consent.azure-apim.net/redirect`
5. Note the **Client ID** and **Client Secret**

### 2. Create the custom connector

1. Go to [Power Platform Maker Portal](https://make.powerapps.com/)
2. Navigate to **Custom connectors** > **+ New custom connector** > **Import an OpenAPI file**
3. Upload `apiDefinition.swagger.json`
4. On the **Security** tab, configure OAuth 2.0 with your Seismic client credentials
5. On the **Code** tab:
   - Enable **Code**
   - Upload `script.csx`
6. Select **Create connector**

### 3. Test the connector

Test `ListTeamsites` first—it requires no parameters and confirms the connection works. Then test `QueryItems` to search for files by name.

### 4. Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "List all teamsites" or "Find files modified this week"

## Known limitations

- File upload accepts base64-encoded content; extremely large files may exceed Power Platform request size limits
- Download operations return base64-encoded content; very large files may exceed response size limits—use the download URL directly instead
- Rate limiting: 600 requests per 60 seconds for most endpoints, 60 requests per 60 seconds for List Items in a Folder
- Maximum 1,000 items returned per list request
- Copy operations work within the same teamsite only

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 24 REST operations |
| `apiProperties.json` | OAuth 2.0 config and script operation bindings |
| `script.csx` | C# script handling MCP protocol, multipart file upload transformation, and download content assembly |
| `readme.md` | Setup and usage documentation |

## Resources

- [Seismic connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Seismic%20Library%20Content%20Management)
- [Seismic Library Content Management API](https://developer.seismic.com/seismicsoftware/reference/seismiclibrarycontentmanagementaddafile)
