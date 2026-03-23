---
layout: post
title: "Azure AI Search MCP connector for Copilot Studio agents"
date: 2026-03-23 14:00:00 -0600
categories: [Power Platform, Custom Connectors]
tags: [Azure AI Search, Copilot Studio, MCP, Power Mission Control, search, indexing]
---

Azure AI Search has 37 REST API operations across indexes, documents, indexers, data sources, skillsets, and synonym maps. Wrapping each one as a typed MCP tool would consume roughly 18,000 tokens on every `tools/list` call. This connector uses the [Power Mission Control template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20Mission%20Control%20Template) to expose the entire API surface through three tools and eight MCP resources—about 1,500 tokens total.

## What this connector does

The Azure AI Search MCP connector gives Copilot Studio agents full access to the [Azure AI Search REST API (2025-09-01)](https://learn.microsoft.com/rest/api/searchservice/). Agents can search indexes, manage index definitions, run indexers, configure data sources, build skillsets, and monitor service health—all through progressive discovery.

## Tools

The connector exposes three tools to the planner:

| Tool | Description |
|------|-------------|
| `scan_search` | Search for available operations matching your intent |
| `launch_search` | Execute any Azure AI Search API endpoint |
| `sequence_search` | Execute a sequence of multiple operations in one call |

### How it works

```
User: "Search my products index for wireless headphones"

1. Planner calls scan_search({query: "search documents"})
   → Returns: search_documents (POST /indexes/{indexName}/docs/search)

2. Planner calls launch_search({
     endpoint: "/indexes/products/docs/search",
     method: "POST",
     body: { search: "wireless headphones", queryType: "semantic" }
   })
   → Returns: matching documents with highlights and scores
```

The planner discovers the right operation first, then executes it with the correct endpoint and parameters. No upfront schema loading required.

## Operations (37)

The capability index covers the full API surface:

### Indexes

| Operation | Endpoint | Method |
|-----------|----------|--------|
| `list_indexes` | /indexes | GET |
| `create_index` | /indexes | POST |
| `get_index` | /indexes/{indexName} | GET |
| `update_index` | /indexes/{indexName} | PUT |
| `delete_index` | /indexes/{indexName} | DELETE |
| `get_index_statistics` | /indexes/{indexName}/stats | GET |
| `analyze_text` | /indexes/{indexName}/analyze | POST |

### Search and documents

| Operation | Endpoint | Method |
|-----------|----------|--------|
| `search_documents` | /indexes/{indexName}/docs/search | POST |
| `get_document` | /indexes/{indexName}/docs/{key} | GET |
| `count_documents` | /indexes/{indexName}/docs/$count | GET |
| `index_documents` | /indexes/{indexName}/docs/index | POST |
| `autocomplete` | /indexes/{indexName}/docs/autocomplete | POST |
| `suggest` | /indexes/{indexName}/docs/suggest | POST |

### Indexers

| Operation | Endpoint | Method |
|-----------|----------|--------|
| `list_indexers` | /indexers | GET |
| `create_indexer` | /indexers | POST |
| `get_indexer` | /indexers/{indexerName} | GET |
| `update_indexer` | /indexers/{indexerName} | PUT |
| `delete_indexer` | /indexers/{indexerName} | DELETE |
| `run_indexer` | /indexers/{indexerName}/run | POST |
| `get_indexer_status` | /indexers/{indexerName}/status | GET |
| `reset_indexer` | /indexers/{indexerName}/reset | POST |

### Data sources

| Operation | Endpoint | Method |
|-----------|----------|--------|
| `list_datasources` | /datasources | GET |
| `create_datasource` | /datasources | POST |
| `get_datasource` | /datasources/{dataSourceName} | GET |
| `update_datasource` | /datasources/{dataSourceName} | PUT |
| `delete_datasource` | /datasources/{dataSourceName} | DELETE |

### Skillsets

| Operation | Endpoint | Method |
|-----------|----------|--------|
| `list_skillsets` | /skillsets | GET |
| `create_skillset` | /skillsets | POST |
| `get_skillset` | /skillsets/{skillsetName} | GET |
| `update_skillset` | /skillsets/{skillsetName} | PUT |
| `delete_skillset` | /skillsets/{skillsetName} | DELETE |

### Synonym maps

| Operation | Endpoint | Method |
|-----------|----------|--------|
| `list_synonym_maps` | /synonymmaps | GET |
| `create_synonym_map` | /synonymmaps | POST |
| `get_synonym_map` | /synonymmaps/{synonymMapName} | GET |
| `update_synonym_map` | /synonymmaps/{synonymMapName} | PUT |
| `delete_synonym_map` | /synonymmaps/{synonymMapName} | DELETE |

### Admin

| Operation | Endpoint | Method |
|-----------|----------|--------|
| `get_service_statistics` | /servicestats | GET |

## MCP resources

Beyond tools, the connector exposes eight MCP resources for knowledge grounding. The planner can read these to understand what's available before making tool calls.

| Resource | URI | Description |
|----------|-----|-------------|
| Search Indexes | `search://indexes` | All indexes in the service |
| Index Schema | `search://indexes/{indexName}/schema` | Field definitions, types, semantic config |
| Index Statistics | `search://indexes/{indexName}/stats` | Document count and storage size |
| Service Statistics | `search://service/stats` | Service-level usage and capacity |
| Data Sources | `search://datasources` | Configured data connections |
| Skillsets | `search://skillsets` | AI enrichment pipelines |
| Synonym Maps | `search://synonymmaps` | Query expansion rules |
| Indexer Status | `search://indexers/{indexerName}/status` | Run history, errors, documents processed |

## Prerequisites

- Azure AI Search service ([create one](https://learn.microsoft.com/azure/search/search-create-service-portal))
- Admin API key (full access) or query API key (search only)
- Power Platform environment with Copilot Studio

## Setting up the connector

### 1. Create the custom connector

1. Go to [make.powerapps.com](https://make.powerapps.com/) > **Custom connectors**
2. Select **New custom connector** > **Import an OpenAPI file**
3. Upload `apiDefinition.swagger.json`
4. On the **Code** tab, paste the contents of `script.csx`
5. Save and test

### 2. Create a connection

When creating a connection, provide:

| Parameter | Value |
|-----------|-------|
| Search Service URL | `https://your-service.search.windows.net` |
| API Key | Your admin or query API key from the Azure portal |

Get your keys from the Azure portal: **Search service** > **Settings** > **Keys**.

### 3. Add to Copilot Studio

1. Open your agent in Copilot Studio
2. Go to **Tools** > **Add a tool** > **Custom connector**
3. Select **Azure AI Search MCP**
4. The agent now has access to `scan_search`, `launch_search`, and `sequence_search`

## Authentication

This connector uses API key authentication. The API key is stored as a connection parameter and injected as the `api-key` header on every request. Use an admin key for full access to all operations or a query key for read-only search and document retrieval.

## Architecture

```
Copilot Studio Agent
    │
    ├─ tools/list → [scan_search, launch_search, sequence_search]
    │
    ├─ resources/list → [search://indexes, search://service/stats, ...]
    │   └─ resources/read → index schemas, stats, data source configs
    │
    ├─ scan_search({query: "search documents"})
    │   └─ Searches embedded capability index (37 operations)
    │
    ├─ launch_search({endpoint, method, body})
    │   ├─ Builds URL: {serviceUrl}/{endpoint}?api-version=2025-09-01
    │   ├─ Injects api-key header from connection parameter
    │   ├─ Handles 429 retry with Retry-After
    │   └─ Summarizes response (strip HTML, truncate)
    │
    └─ sequence_search({requests: [...]})
        └─ Executes requests sequentially, returns aggregated results
```

## Resources

- [Full source code on GitHub](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20AI%20Search)
- [Azure AI Search REST API reference](https://learn.microsoft.com/rest/api/searchservice/)
- [Azure AI Search data plane operations](https://learn.microsoft.com/rest/api/searchservice/operation-groups)
- [Power Mission Control template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20Mission%20Control%20Template)
