---
layout: post
title: "Microsoft Foundry custom connector for Power Platform"
date: 2026-02-09 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Microsoft Foundry, Azure AI, Copilot Studio, MCP, Custom Connectors, Power Platform, AI Agents, Content Safety, Document Intelligence, AI Search]
description: "Comprehensive Power Platform custom connector for Microsoft Foundry covering model inference, AI agents, content safety, vision, evaluation, speech, translation, language analysis, document intelligence, and MCP protocol."
---

Microsoft Foundry (formerly Azure AI Foundry) consolidates dozens of Azure AI services behind a single endpoint and API key. This connector brings all of that into Power Platform as one custom connector—chat completions, AI agents, content safety, vision, embeddings, evaluation, speech, translation, language analysis, document intelligence, and more. It also exposes an MCP endpoint so Copilot Studio agents can call those same capabilities through conversational tools.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry).

## Why one connector?

Most Azure AI integrations require separate connectors for each service—one for OpenAI, another for Content Safety, another for Translator, and so on. Each needs its own connection, auth configuration, and DLP policy. This connector collapses 20+ API surfaces into a single import. Deploy one Foundry resource, import one connector, create one connection, and access everything from flows, apps, or agents.

## What's included

The connector covers these API surfaces:

### Model inference

| Operation | Method | Path |
|-----------|--------|------|
| Chat Completion | POST | `/models/chat/completions` |
| Chat Completion (Azure OpenAI) | POST | `/openai/deployments/{deployment}/chat/completions` |
| Get Text Embeddings | POST | `/models/embeddings` |
| Get Image Embeddings | POST | `/models/images/embeddings` |
| Get Model Info | GET | `/models/info` |

Two chat completion operations cover both deployment models. **Foundry Models (Serverless)** use the `/models/` path and require a `model` parameter in the request body. **Azure OpenAI (Traditional)** use the `/openai/deployments/{deployment}/` path with the deployment name in the URL.

### AI agents (Assistants v2)

| Operation | Method | Path |
|-----------|--------|------|
| List Assistants | GET | `/openai/assistants` |
| Create Assistant | POST | `/openai/assistants` |
| Get/Delete Assistant | GET/DELETE | `/openai/assistants/{id}` |
| Create/Get/Delete Thread | POST/GET/DELETE | `/openai/threads` |
| List/Create Messages | GET/POST | `/openai/threads/{id}/messages` |
| List/Create Runs | GET/POST | `/openai/threads/{id}/runs` |
| Get Run | GET | `/openai/threads/{id}/runs/{run_id}` |
| Create Thread and Run | POST | `/openai/threads/runs` |

Use the assistants workflow to create an agent with instructions, start a thread, add messages, run the assistant, and retrieve responses. Or use **Create Thread and Run** to do it in one call.

### Content safety

Analyze text and images for harmful content across four categories: Hate, SelfHarm, Sexual, and Violence. Returns severity levels from 0 (safe) to 6 (high).

### Image analysis (Vision)

Extract captions, dense captions, tags, detected objects, OCR text, smart crop regions, and people detection from images in a single call.

### AI evaluation

Submit AI responses for quality evaluation (groundedness, relevance, coherence, fluency, similarity on a 1–5 scale) or safety evaluation (severity 0–6). Also includes locally computed NLP metrics: F1, BLEU, ROUGE, GLEU, and METEOR.

### Speech services

Transcribe and translate audio using OpenAI Whisper deployments. Supports mp3, mp4, mpeg, mpga, m4a, wav, and webm formats.

### Translator

Translate text across 100+ languages, transliterate between scripts, and detect input language—all in a single request with multiple targets.

### Language services

Analyze text for sentiment, named entities, key phrases, PII detection and redaction, entity linking, and language detection through a unified endpoint.

### Document intelligence

Extract text, tables, key-value pairs, and structured data from documents using prebuilt models: `prebuilt-read`, `prebuilt-layout`, `prebuilt-document`, `prebuilt-invoice`, `prebuilt-receipt`, and `prebuilt-businessCard`.

### Additional services

| Service | What it does |
|---------|-------------|
| Question Answering | Query custom knowledge bases with multi-turn conversations |
| Conversational Language Understanding | Detect intents and extract entities from conversational text |
| Anomaly Detector | Detect anomalies in time series data (real-time and batch) |
| Health Text Analytics | Extract healthcare entities and relations from clinical text |
| Face Detection | Detect faces and analyze attributes (age, emotion, glasses) |
| Text-to-Speech | Convert text to speech audio using SSML |
| Speaker Recognition | Voice biometrics for speaker verification and enrollment |
| Custom Vision | Image classification and object detection with custom models |
| Personalizer | Contextual personalization with reinforcement learning |
| AI Search | Full-text, semantic, and vector search over Azure AI Search indexes |
| OCR / Read API | Extract printed and handwritten text from images (164+ languages) |
| Batch Transcription | Large-scale audio transcription with diarization |

### MCP protocol

The connector exposes a `/mcp` endpoint implementing JSON-RPC 2.0 for Copilot Studio integration. Available MCP tools:

- `chat_completion` — Send prompts to AI models
- `get_embeddings` — Generate text embeddings
- `create_assistant` / `run_assistant` — Create and run AI agent conversations
- `analyze_content_safety` — Check text for harmful content
- `analyze_image` — Analyze images for tags, objects, captions
- `evaluate_response` — Evaluate AI responses for quality and safety
- `transcribe_audio` — Convert audio to text
- `translate_text` — Translate text between languages
- `analyze_language` — Analyze text for sentiment, entities, PII
- `analyze_document` — Extract content from documents

## Setup

### 1. Create the Foundry resource

1. Create a Microsoft Foundry resource in the [Azure Portal](https://portal.azure.com/).
2. Note the endpoint URL (for example, `https://your-resource.services.ai.azure.com/`).
3. Copy one of the API keys from **Keys and Endpoint**.

### 2. Deploy a model

**Foundry Models (Serverless)** — Deploy via CLI:

```bash
az cognitiveservices account deployment create \
    -n "your-resource" \
    -g "your-rg" \
    --deployment-name "Phi-4" \
    --model-name "Phi-4" \
    --model-version 7 \
    --model-format Microsoft \
    --sku-capacity 1 \
    --sku-name GlobalStandard
```

**Azure OpenAI** — Deploy via [Azure Portal](https://portal.azure.com/) → your Cognitive Services resource → Model deployments → Deploy model. Note the deployment name.

### 3. Import the connector

1. Go to [Power Automate](https://make.powerautomate.com/) or [Power Apps](https://make.powerapps.com/) → Custom connectors.
2. Import from OpenAPI file: upload `apiDefinition.swagger.json`.
3. Update the **Host** field to your Foundry endpoint (for example, `your-resource.services.ai.azure.com`).
4. Save the connector.

### 4. Create a connection

1. Create a new connection or test the connector.
2. Enter your API key when prompted.
3. Verify with the **Get Model Info** action.

### Application Insights (optional)

Add your Application Insights connection string to `script.csx`:

```csharp
private const string APP_INSIGHTS_CONNECTION_STRING = "InstrumentationKey=YOUR-KEY;IngestionEndpoint=https://REGION.in.applicationinsights.azure.com/;...";
```

## Copilot Studio integration

1. Import the connector into your environment (`apiDefinition.swagger.json`, `apiProperties.json`, `script.csx`).
2. In Copilot Studio, go to **Tools → Add a tool → Model Context Protocol**.
3. Point the MCP endpoint to your connector's `/mcp` path.
4. Copilot Studio discovers the available tools automatically.

## Example scenarios

### Chat completion (Foundry Models)

```json
{
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "What is the capital of France?" }
  ],
  "model": "Phi-4",
  "temperature": 0.7,
  "max_tokens": 800
}
```

### AI agents workflow

1. **Create Assistant** with a model and instructions.
2. **Create Thread** to start a conversation.
3. **Create Message** to add user messages.
4. **Create Run** to execute the assistant.
5. **Get Run** to check status.
6. **List Messages** to retrieve the response.

Or use **Create Thread and Run** to do it in one call.

### Content safety moderation

```json
{
  "text": "User input to check for harmful content"
}
```

Review `categoriesAnalysis` for each harm category. Block or flag content with severity >= 4.

### Language analysis

```json
{
  "kind": "SentimentAnalysis",
  "analysisInput": {
    "documents": [
      {
        "id": "1",
        "language": "en",
        "text": "I absolutely love this product! It exceeded all my expectations."
      }
    ]
  }
}
```

### AI evaluation

```json
{
  "evaluationType": "groundedness",
  "response": "The AI's response to evaluate",
  "context": "The source material the response should be grounded in",
  "query": "The original user question"
}
```

Quality metrics return a score from 1–5. Safety metrics return severity from 0–6. NLP metrics (F1, BLEU, ROUGE, GLEU, METEOR) return 0–1 when you provide `response` and `groundTruth`.

## AI evaluation technical notes

The evaluation functionality reverse-engineers the `azure-ai-evaluation` Python SDK. Safety evaluations use the Content Safety API. Quality evaluations use LLM-based assessment via Chat Completion. This approach provides comparable results without requiring an Azure ML workspace.

**Not implemented:** IndirectAttack, ProtectedMaterial, composite evaluators, adversarial simulators, and batch evaluation via the `evaluate()` API. For batch processing, use Power Automate's **Apply to each** loop and store results in Dataverse or SharePoint.

## Try it yourself

The complete connector code is available in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Foundry/apiDefinition.swagger.json) — OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Foundry/script.csx) — Connector script with MCP implementation
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Foundry/apiProperties.json) — Connector metadata
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Foundry/readme.md) — Full documentation

## Resources

- [Microsoft Foundry API](https://learn.microsoft.com/en-us/rest/api/aifoundry/)
- [Foundry Models Inference](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/deployments-overview)
- [Foundry Agent Service](https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-foundry)
- [Azure Content Safety API](https://learn.microsoft.com/en-us/rest/api/contentsafety/)
- [Azure Computer Vision API](https://learn.microsoft.com/en-us/rest/api/computervision/image-analysis/analyze)
- [Azure Speech Services](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#audio-transcription)
- [Azure Translator API](https://learn.microsoft.com/en-us/azure/ai-services/translator/reference/v3-0-reference)
- [Azure Language Services](https://learn.microsoft.com/en-us/azure/ai-services/language-service/overview)
- [Azure Document Intelligence](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- [MCP Specification](https://modelcontextprotocol.org/)
- [Power Platform Custom Connectors](https://learn.microsoft.com/en-us/connectors/custom-connectors/)
- [Application Insights telemetry for connectors](https://troystaylor.github.io/power%20platform/2026/01/07/power-platform-custom-connectors-application-insights.html)
