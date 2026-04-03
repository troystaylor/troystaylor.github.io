---
layout: post
title: "Microsoft Foundry Rerank MCP connector for Power Platform"
date: 2026-04-03 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Rerank, Cohere, Microsoft Foundry, MCP, Copilot Studio, Custom Connectors, Power Platform, RAG, Search]
description: "Power Platform custom connector for Cohere Rerank v4 models on Microsoft Foundry—rerank search results by semantic relevance and filter by score threshold for RAG pipelines."
---

Keyword search returns results that match terms. Semantic reranking returns results that match meaning. The gap between those two is where RAG pipelines lose quality—an LLM generates a mediocre answer because the most relevant documents were buried behind keyword-matched noise.

This connector adds Cohere Rerank v4 to Power Platform. Pass a query and a list of documents from any source—SharePoint, Dataverse, Azure AI Search, a custom API—and get them back ordered by semantic relevance. A second operation filters out everything below a score threshold so only high-quality context reaches your LLM.

Two MCP tools for Copilot Studio. Two REST operations for Power Automate and Power Apps. Supports 14 languages.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20Rerank)

## How reranking works

Traditional search (BM25, keyword matching) retrieves documents that contain the right words. Semantic reranking goes further—it scores how well each document answers the query, regardless of exact word overlap.

The Cohere Rerank v4 model reads each document alongside the query and produces a relevance score between 0 and 1. A document about "quarterly revenue growth" scores high against the query "How did the company perform financially last quarter?" even if those exact words never appear together.

This matters most in RAG pipelines:

1. **Retrieve** — Pull 50-100 candidate documents from search
2. **Rerank** — Score each document's relevance to the actual question
3. **Filter** — Keep only documents above a quality threshold
4. **Generate** — Send the top results as context to an LLM

Without reranking, the LLM sees whatever keyword search returned first. With reranking, it sees what actually answers the question.

## Available models

| Model | Best for | Latency | Quality |
|-------|----------|---------|---------|
| Cohere-rerank-v4.0-pro | Maximum relevance accuracy | Higher | Best |
| Cohere-rerank-v4.0-fast | High-throughput, latency-sensitive flows | Lower | Good |

Both models support 14 languages: English, French, Spanish, Italian, German, Portuguese, Japanese, Chinese, Arabic, Vietnamese, Hindi, Russian, Indonesian, and Dutch.

## Tools

### MCP tools for Copilot Studio

| Tool | Description |
|------|-------------|
| `rerank_documents` | Rerank documents by relevance score |
| `rerank_and_filter` | Rerank and filter out documents below a score threshold |

### How it works

```
User: "What's our return policy for international orders?"

1. Agent retrieves 20 documents from SharePoint search

2. Agent calls rerank_documents({
     query: "return policy international orders",
     documents: ["...", "...", ...],
     top_n: 5
   })

   → Returns 5 most relevant documents ordered by score:
     [0.92] International Returns & Exchange Policy
     [0.87] Cross-Border Shipping and Returns FAQ
     [0.71] Customer Service Procedures Manual
     [0.54] General Terms and Conditions
     [0.41] Warehouse Operations Guide

3. Agent uses the top-scoring documents as context
   to generate an accurate answer
```

### Rerank and filter

The `rerank_and_filter` tool adds a `min_score` threshold. Documents below the threshold are excluded entirely.

```
Agent calls rerank_and_filter({
  query: "return policy international orders",
  documents: ["...", "...", ...],
  min_score: 0.6
})

→ Returns only documents above 0.6:
  total_input: 20
  total_passed: 3
  total_filtered: 17
  results: [0.92, 0.87, 0.71]
```

This prevents low-relevance documents from polluting the LLM's context window, reducing hallucinations.

## REST operations for Power Automate and Power Apps

| Operation | Operation ID | Method | Path |
|-----------|-------------|--------|------|
| Rerank Documents | `RerankDocuments` | POST | `/v2/rerank` |
| Rerank and Filter | `RerankAndFilter` | POST | `/rerank/filter` |

### Parameter reference

| Operation | Parameter | Type | Default | Required |
|-----------|-----------|------|---------|----------|
| Rerank Documents | `query` | string | — | Yes |
| Rerank Documents | `documents` | string[] | — | Yes |
| Rerank Documents | `model` | enum | Cohere-rerank-v4.0-pro | No |
| Rerank Documents | `top_n` | int | all | No |
| Rerank Documents | `max_tokens_per_doc` | int | 4096 | No |
| Rerank and Filter | `query` | string | — | Yes |
| Rerank and Filter | `documents` | string[] | — | Yes |
| Rerank and Filter | `min_score` | float (0-1) | — | Yes |
| Rerank and Filter | `model` | enum | Cohere-rerank-v4.0-pro | No |
| Rerank and Filter | `top_n` | int | all passing | No |
| Rerank and Filter | `max_tokens_per_doc` | int | 4096 | No |

### Rerank Documents response

```json
{
  "results": [
    { "index": 3, "relevance_score": 0.92, "document": "..." },
    { "index": 7, "relevance_score": 0.87, "document": "..." },
    { "index": 1, "relevance_score": 0.71, "document": "..." }
  ],
  "id": "request-id",
  "meta": {
    "api_version": { "version": "2" },
    "billed_units": { "search_units": 1 }
  }
}
```

The `index` field references the original position in the input array—use it to correlate reranked results back to your source data.

### Rerank and Filter response

```json
{
  "results": [
    { "index": 3, "relevance_score": 0.92, "document": "..." },
    { "index": 7, "relevance_score": 0.87, "document": "..." }
  ],
  "total_input": 20,
  "total_passed": 2,
  "total_filtered": 18
}
```

The `total_passed` and `total_filtered` counts let you monitor filter effectiveness. If `total_passed` is consistently zero, lower the `min_score`. If `total_filtered` is consistently zero, raise it.

## Power Automate RAG pipeline example

Build a complete RAG pipeline in Power Automate:

1. **Search** — Query SharePoint or Dataverse for documents matching the user's question
2. **Collect** — Extract text content from each result into an array of strings
3. **Rerank and Filter** — Pass the text array + user question to the `RerankAndFilter` operation with `min_score: 0.5`
4. **Generate** — Send only the high-relevance documents as context to a chat completion connector (Microsoft Foundry, Azure OpenAI, or any LLM connector)

This pipeline reduces hallucinations by ensuring the LLM only sees documents that semantically match the question, not just keyword-matched results.

## Pricing

Cohere Rerank is billed per **search unit**. One search unit equals one query with up to 100 documents. If you send 250 documents with one query, that's 3 search units.

Documents longer than 4,096 tokens (including the query) are split into chunks internally. Each chunk counts as a separate document toward billing.

## Prerequisites

1. An Azure subscription with access to Microsoft Foundry
2. Deploy **Cohere-rerank-v4.0-pro** or **Cohere-rerank-v4.0-fast** from the [Foundry Model Catalog](https://ai.azure.com/explore/models?selectedCollection=Cohere)
3. Note the **Resource Name** and **API Key** from the deployment

## Setting up the connector

### 1. Deploy a Cohere Rerank model

1. Go to the [Foundry Model Catalog](https://ai.azure.com/explore/models?selectedCollection=Cohere)
2. Select **Cohere-rerank-v4.0-pro** (best quality) or **Cohere-rerank-v4.0-fast** (lower latency)
3. Select **Deploy** and choose your Azure AI Services resource
4. Copy the **Resource Name** and **API Key**

### 2. Create the custom connector

1. Go to [Power Platform Maker Portal](https://make.powerapps.com/)
2. Navigate to **Custom connectors** > **+ New custom connector** > **Import an OpenAPI file**
3. Upload `apiDefinition.swagger.json`
4. On the **Security** tab:
   - **Authentication type:** API Key
   - **Parameter label:** API Key
   - **Parameter name:** `api-key`
   - **Parameter location:** Header
5. On the **Code** tab:
   - Enable **Code**
   - Upload `script.csx`
6. Select **Create connector**

### 3. Create a connection

1. Select **Test** > **+ New connection**
2. Enter your **Resource Name** and **API Key**
3. Select **Create connection**

### 4. Test the connector

Test `RerankDocuments` with a sample query and documents:

```json
{
  "query": "What is the company vacation policy?",
  "documents": [
    "Employees receive 15 days of paid time off per year.",
    "The office dress code is business casual.",
    "Vacation requests must be submitted two weeks in advance.",
    "The company was founded in 2015."
  ]
}
```

Verify the response returns documents ordered by relevance, with the vacation-related documents scoring highest.

### 5. Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. The agent can use `rerank_documents` or `rerank_and_filter` to improve search quality before answering

## Known limitations

- Maximum recommended 1,000 documents per request
- Long documents are automatically truncated to `max_tokens_per_doc` (default 4,096 tokens)
- The model reranks by text similarity—it doesn't understand document structure like tables or images
- Relevance scores are relative within a single request—scores aren't comparable across different queries
- The filter operation runs in the connector script layer after the rerank API call, not in the model itself

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 2 REST operations |
| `apiProperties.json` | API Key auth config and script operation bindings |
| `script.csx` | C# script handling MCP protocol, rerank API calls, and score filtering |
| `readme.md` | Setup and usage documentation |

## Resources

- [Rerank connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20Rerank)
- [Cohere Rerank models in Foundry Catalog](https://ai.azure.com/explore/models?selectedCollection=Cohere)
- [Microsoft Foundry API](https://learn.microsoft.com/en-us/rest/api/aifoundry/)
- [Cohere Rerank documentation](https://docs.cohere.com/docs/rerank-2)
