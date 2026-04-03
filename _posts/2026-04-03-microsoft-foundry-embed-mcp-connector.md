---
layout: post
title: "Microsoft Foundry Embed MCP connector for Power Platform"
date: 2026-04-03 14:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Embeddings, Cohere, Microsoft Foundry, MCP, Copilot Studio, Custom Connectors, Power Platform, Vector Search, Azure AI Search, RAG]
description: "Power Platform custom connector for Cohere Embed v4 on Microsoft Foundry—generate text and image embeddings, compute semantic similarity, index documents to Azure AI Search, and run vector search."
---

Embeddings turn text and images into numbers that capture meaning. Two sentences about the same topic produce vectors that are close together; unrelated content produces vectors that are far apart. This is the foundation of semantic search, duplicate detection, recommendation engines, and RAG pipelines.

This connector brings Cohere Embed v4 into Power Platform with three tiers of functionality:

- **Basic** — Compute similarity between any two inputs (text or image) with a single call. No vector store needed.
- **Intermediate** — Generate raw embedding vectors for text or images. Store and compare them however you want.
- **Advanced** — Index documents to Azure AI Search with auto-generated vectors and run vector search. A complete RAG retrieval pipeline from Power Automate.

Five MCP tools for Copilot Studio. Five REST operations for Power Automate and Power Apps.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20Embed)

## Model details

| Feature | Details |
|---------|---------|
| Model | Cohere Embed v4 (`embed-v-4-0`) |
| Text input | 512 tokens per string |
| Image input | Up to 2M pixels (PNG recommended) |
| Vector dimensions | 256, 512, 1024 (default), or 1536 |
| Languages | 10: English, French, Spanish, Italian, German, Portuguese, Japanese, Korean, Chinese, Arabic |
| Cross-modal | Text and image embeddings share the same vector space |
| Deployment | Global Standard (serverless, all regions) |

The cross-modal capability is key—text embeddings and image embeddings land in the same vector space. You can compare a product photo against a text description and get a meaningful similarity score.

## Tools

### MCP tools for Copilot Studio

| Tool | Description |
|------|-------------|
| `embed_text` | Generate text embeddings for one or more strings |
| `embed_image` | Generate an image embedding, optionally paired with text |
| `compute_similarity` | Compute cosine similarity between two inputs (text or image) |
| `index_document` | Embed text and push to Azure AI Search |
| `search_similar` | Vector search against an Azure AI Search index |

### How similarity works

```
User: "Are these two product descriptions duplicates?"

1. Agent calls compute_similarity({
     input_a: "Wireless noise-canceling headphones with 30-hour battery",
     input_a_type: "text",
     input_b: "Bluetooth headphones, active noise cancellation, 30h playtime",
     input_b_type: "text"
   })

   → similarity: 0.89
     interpretation: "Very similar"
```

The connector embeds both inputs, computes cosine similarity, and returns a score with a human-readable interpretation:

| Score range | Interpretation |
|-------------|---------------|
| 0.8 - 1.0 | Very similar |
| 0.6 - 0.8 | Similar |
| 0.4 - 0.6 | Somewhat related |
| 0.2 - 0.4 | Loosely related |
| 0.0 - 0.2 | Unrelated |

### Cross-modal comparison

Compare text against images:

```
User: "Does this product photo match our catalog description?"

Agent calls compute_similarity({
  input_a: "https://storage.blob.core.windows.net/products/headphones.png",
  input_a_type: "image",
  input_b: "Over-ear wireless headphones in matte black with cushioned ear cups",
  input_b_type: "text"
})

→ similarity: 0.74
  interpretation: "Similar"
```

## REST operations for Power Automate and Power Apps

| Operation | Operation ID | Method | Path |
|-----------|-------------|--------|------|
| Embed Text | `EmbedText` | POST | `/embed/text` |
| Embed Image | `EmbedImage` | POST | `/embed/image` |
| Compute Similarity | `ComputeSimilarity` | POST | `/embed/similarity` |
| Index Document to AI Search | `IndexDocument` | POST | `/embed/index` |
| Search Similar Documents | `SearchSimilar` | POST | `/embed/search` |

### Embed Text

Generate embedding vectors for one or more text strings.

| Parameter | Type | Default | Required |
|-----------|------|---------|----------|
| `texts` | string[] | — | Yes |
| `input_type` | enum | document | No |
| `dimensions` | enum | 1024 | No |

The `input_type` parameter matters. Use `document` when embedding content for storage/indexing. Use `query` when embedding a search query. The model applies different transformations for each to optimize retrieval accuracy.

### Embed Image

Generate an embedding vector for an image, optionally paired with text.

| Parameter | Type | Default | Required |
|-----------|------|---------|----------|
| `image_url` | string | — | Yes |
| `text` | string | — | No |
| `dimensions` | enum | 1024 | No |

Pair an image with text to create a combined embedding that captures both visual and textual meaning.

### Compute Similarity

Compare any two inputs without a vector store.

| Parameter | Type | Default | Required |
|-----------|------|---------|----------|
| `input_a` | string | — | Yes |
| `input_a_type` | enum | text | No |
| `input_b` | string | — | Yes |
| `input_b_type` | enum | text | No |

Supports four combinations: text-to-text, text-to-image, image-to-text, image-to-image.

### Index Document to AI Search

Embed a document and push it with its vector to Azure AI Search in one call.

| Parameter | Type | Default | Required |
|-----------|------|---------|----------|
| `document_id` | string | — | Yes |
| `content` | string | — | Yes |
| `title` | string | — | No |
| `search_endpoint` | string | — | Yes |
| `search_index` | string | — | Yes |
| `search_api_key` | string | — | Yes |
| `vector_field` | string | contentVector | No |

### Search Similar Documents

Embed a query and run vector search against an Azure AI Search index.

| Parameter | Type | Default | Required |
|-----------|------|---------|----------|
| `query` | string | — | Yes |
| `top_k` | int | 5 | No |
| `search_endpoint` | string | — | Yes |
| `search_index` | string | — | Yes |
| `search_api_key` | string | — | Yes |
| `vector_field` | string | contentVector | No |

## Azure AI Search index requirements

For the `IndexDocument` and `SearchSimilar` operations, your AI Search index must have:

- A string field named `id` (set as the key field)
- A string field named `content`
- A `Collection(Edm.Single)` field for vectors (default name: `contentVector`) with dimensions matching the connector (1024 by default)
- An optional string field named `title`

## Example workflows

### Duplicate detection (no AI Search required)

1. User submits two product descriptions
2. `ComputeSimilarity` returns 0.87 ("Very similar")
3. Flow flags them as potential duplicates for review

No vector store, no index, no infrastructure—just two strings in, one score out.

### RAG pipeline with Azure AI Search

**Indexing phase** (run once per document):

1. Retrieve document text from SharePoint or Dataverse
2. Call `IndexDocument` with the text, a unique ID, and your AI Search credentials
3. The connector embeds the text and pushes it with its vector to the index

**Query phase** (run per user question):

1. User asks a question
2. Call `SearchSimilar` with the question and AI Search credentials
3. Get back the top 5 most semantically similar documents
4. Send those documents as context to an LLM for answer generation

### Cross-modal product matching

1. User uploads a photo of a product
2. `ComputeSimilarity` compares the image embedding against each product description text
3. Returns the closest matching product by semantic similarity

## Prerequisites

1. An Azure subscription with access to Microsoft Foundry
2. Deploy **embed-v-4-0** from the [Foundry Model Catalog](https://ai.azure.com/explore/models?selectedCollection=Cohere)
3. Note the **Resource Name** and **API Key** from the deployment
4. *(Advanced operations only)* An [Azure AI Search](https://azure.microsoft.com/products/ai-services/ai-search) service with a vector-enabled index

## Setting up the connector

### 1. Deploy Cohere Embed v4

1. Go to the [Foundry Model Catalog](https://ai.azure.com/explore/models?selectedCollection=Cohere)
2. Select **embed-v-4-0** and deploy to your Azure AI Services resource
3. Copy the **Resource Name** and **API Key**

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

### 3. Test the connector

Test `ComputeSimilarity` first—it's the simplest operation and doesn't need AI Search:

```json
{
  "input_a": "The quick brown fox jumps over the lazy dog",
  "input_b": "A fast auburn fox leaps above a sleeping hound"
}
```

Verify you get a high similarity score (should be around 0.8+).

### 4. Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "How similar are these two descriptions?" or "Search my knowledge base for documents about return policies"

## Known limitations

- Text input is limited to 512 tokens per string
- Image embeddings require PNG format; other formats may not work
- One image per embedding call (batch image embeddings not supported)
- AI Search operations pass credentials as parameters (not stored in the connection) because they connect to a separate service
- Cosine similarity scores are relative—they compare two specific inputs, not absolute quality measures
- The default vector dimensions (1024) must match your AI Search index configuration

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 5 REST operations |
| `apiProperties.json` | API Key auth config and script operation bindings |
| `script.csx` | C# script handling MCP protocol, embedding API calls, similarity computation, and AI Search integration |
| `readme.md` | Setup and usage documentation |

## Resources

- [Embed connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20Embed)
- [Cohere Embed v4 in Foundry Catalog](https://ai.azure.com/explore/models?selectedCollection=Cohere)
- [Azure AI Search documentation](https://learn.microsoft.com/azure/search/)
- [Microsoft Foundry API](https://learn.microsoft.com/en-us/rest/api/aifoundry/)
- [Cohere Embed documentation](https://docs.cohere.com/docs/embed-2)
