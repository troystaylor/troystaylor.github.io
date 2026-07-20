---
layout: post
title: "Azure AI Image Search connector: multimodal embeddings meet Power Platform"
date: 2026-07-20 10:00:00 -0500
categories: [Power Platform, MCP]
tags: [Azure AI Search, MCP, Copilot Studio, Custom Connectors, Power Automate, Azure Container Apps, Multimodal Embeddings, Image Search]
description: "A dual-mode Power Platform custom connector for natural language image search over your own image collections. Uses Azure AI Search multimodal embeddings for semantic retrieval and Azure Blob Storage for image delivery."
---

Azure AI Search already handles text. But what about searching your own image collections with natural language — "sunset over mountains" or "diagram showing network topology" — and getting actual image thumbnails back for an agent to reason over?

This MCP connector wraps Azure AI Search multimodal embeddings in a dual-mode Power Platform connector. Copilot Studio agents get MCP tools that return `ImageContent` blocks. Power Automate flows get typed operations with full schemas. Both share the same FastAPI + FastMCP backend running on Azure Container Apps.

Inspired by Pamela Fox's [Beyond text: Returning images and interactive apps from MCP servers](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/beyond-text-returning-images-and-interactive-apps-from-mcp-servers/4535865) and the [Azure-Samples/image-search-aisearch](https://github.com/Azure-Samples/image-search-aisearch) reference implementation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Power Platform / Copilot Studio                                │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │  Power Automate  │  │  Copilot Studio (MCP)                │ │
│  │  Typed ops:      │  │  Tools: image_search,                │ │
│  │  SearchImages    │  │         search_by_image,             │ │
│  │  SearchByImage   │  │         get_image_details,           │ │
│  │  GetImageDetails │  │         display_images               │ │
│  │  GetImageUrl     │  │                                      │ │
│  │  UploadImage     │  │                                      │ │
│  └────────┬─────────┘  └──────────────────┬───────────────────┘ │
└───────────┼───────────────────────────────┼─────────────────────┘
            │        Custom Connector       │
            └───────────────────┬───────────┘
                                │ HTTPS + X-API-Key
            ┌───────────────────▼────────────────────┐
            │  Azure Container Apps (FastAPI + MCP)  │
            │  • /health — liveness probe            │
            │  • /mcp — MCP endpoint                 │
            │  • /api/search — text search           │
            │  • /api/search-by-image — reverse      │
            │  • /api/images/{f} — details           │
            │  • /api/images/{f}/url — SAS           │
            │  • /api/upload — add images            │
            └──────────────┬──────────┬──────────────┘
                           │          │
          ┌────────────────▼──┐  ┌────▼──────────────────┐
          │  Azure AI Search  │  │  Azure Blob Storage   │
          │  (multimodal      │  │  (image files)        │
          │   embeddings)     │  │                       │
          └───────────────────┘  └───────────────────────┘
```

## MCP tools

When connected via Copilot Studio, the server exposes four tools:

| Tool | Purpose |
|------|---------|
| `image_search` | Search by natural language query, returns thumbnails + metadata |
| `search_by_image` | Find visually similar images by providing an image URL |
| `get_image_details` | Full metadata and larger preview for a specific image |
| `display_images` | Render selections as ImageContent blocks for the agent/user |

The agent workflow follows a two-stage pattern:

1. **Search** — `image_search` returns thumbnails (resized to 512×512 for token-efficient model inspection) plus structured metadata
2. **Curate** — The agent reviews results, selects the best matches
3. **Display** — `display_images` renders selections in an interactive carousel via an MCP App resource

## Typed operations (Power Automate)

| Operation | Method | Path |
|-----------|--------|------|
| SearchImages | POST | /api/search |
| SearchByImage | POST | /api/search-by-image |
| GetImageDetails | GET | /api/images/{filename} |
| GetImageUrl | GET | /api/images/{filename}/url |
| UploadImage | POST | /api/upload |

`SearchImages` accepts a natural language query and returns results with base64 thumbnails and AI-generated descriptions. `GetImageUrl` returns a time-limited SAS URL for full-resolution download.

## How the search works

The server uses hybrid retrieval — combining full-text search with vector similarity via `VectorizableTextQuery`:

```python
results = search_client.search(
    search_text=query,
    top=max_results,
    vector_queries=[
        VectorizableTextQuery(
            k_nearest_neighbors=max_results,
            fields="embedding",
            text=query,
        )
    ],
    select=["metadata_storage_path", "metadata_storage_name", "verbalized_image"],
)
```

The index uses an integrated vectorizer (`aiServicesVision`) so queries are auto-vectorized at search time — no client-side embedding calls needed. If the vector search fails (wrong index schema, missing vectorizer), it falls back gracefully to text-only search.

For reverse image search, `VectorizableImageUrlQuery` vectorizes an image URL and finds nearest neighbors in embedding space:

```python
results = search_client.search(
    search_text="",
    top=max_results,
    vector_queries=[
        VectorizableImageUrlQuery(
            url=image_url,
            k_nearest_neighbors=max_results,
            fields="embedding",
        )
    ],
)
```

## Lightweight mode

Not every deployment needs Blob Storage access. Set `LIGHTWEIGHT_MODE=true` to return URLs and metadata only — no image bytes fetched, no thumbnails generated. Useful when the consumer (a flow or agent) only needs the image URL for downstream processing.

## Index requirements

The AI Search index needs:

- An `embedding` field (`Collection(Edm.Single)`, 1024 dimensions, HNSW profile)
- A `verbalized_image` field (AI-generated text description per image)
- A `metadata_storage_name` field (blob filename)
- A `metadata_storage_path` field (full blob URL)
- An integrated vectorizer using `aiServicesVision`

The [Azure-Samples/image-search-aisearch](https://github.com/Azure-Samples/image-search-aisearch) repo includes a complete indexing pipeline you can adapt.

## Deployment

### Build in ACR

```powershell
az acr build --registry yourregistry --image ai-image-search:latest --file server/Dockerfile server/
```

No local Docker required — ACR builds remotely.

### Deploy infrastructure

The `infra/` folder contains Bicep templates. Deploy with:

```powershell
$acrPwd = az acr credential show --name yourregistry --query "passwords[0].value" -o tsv
az deployment group create --resource-group rg-ai-image-search `
    --template-file infra/main.bicep `
    --parameters containerImage="yourregistry.azurecr.io/ai-image-search:latest" `
                 apiKey="your-api-key" `
                 acrServer="yourregistry.azurecr.io" `
                 acrUsername="yourregistry" `
                 acrPassword=$acrPwd
```

This deploys an Azure Container Apps environment + app, Azure AI Search (Basic tier), and a Storage account with an images container.

### Deploy the connector

```powershell
pac connector create `
    -df apiDefinition.swagger.json `
    -pf apiProperties.json `
    -sf script.csx `
    -e c4f149b0-9f42-e8c4-97d8-bc69b59f971c
```

Create a connection using the API key from deployment output.

## How it differs from Azure MCP Server's AI Search tools

Azure MCP Server already provides [AI Search tools](https://learn.microsoft.com/azure/developer/azure-mcp-server/tools/azure-ai-search) (`search index query`, `search knowledge base retrieve`), but those return raw JSON document fields — no image handling. This connector adds:

- Fetches actual image bytes and returns `ImageContent` blocks
- Resizes images to thumbnails for token-efficient model inspection
- Supports reverse image search via `VectorizableImageUrlQuery`
- Generates time-limited SAS URLs for full-resolution download
- Provides an upload endpoint to grow the collection
- Includes an MCP App carousel resource for interactive display

## Use cases

**Product catalog search** — A Copilot Studio agent searches product images by description ("red running shoes size 10") and presents matching products in a carousel.

**Digital asset management** — Power Automate flows search a brand asset library by concept ("corporate headshot outdoors") and return SAS URLs for direct download.

**Visual similarity matching** — An agent accepts an uploaded image and finds visually similar items in the collection — useful for "find more like this" workflows.

**Content moderation preview** — Before publishing, a flow searches for recently uploaded images, retrieves thumbnails for human review, and routes approvals.

The full source is available in the [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20AI%20Image%20Search).
