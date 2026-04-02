---
layout: post
title: "Microsoft Foundry Phi-4 MCP connector for Power Platform"
date: 2026-04-02 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Phi-4, Microsoft Foundry, MCP, Copilot Studio, Custom Connectors, Power Platform, Vision, Multimodal, Microsoft Research]
description: "Power Platform custom connector for Microsoft's Phi-4 model family—vision reasoning, multimodal chat with image and audio, and lightweight text chat through three MCP tools and three REST operations."
---

Microsoft's Phi-4 family packs serious capability into small language models. Phi-4-Reasoning-Vision-15B does visual reasoning on math, science, and UI screenshots. Phi-4-multimodal-instruct handles text, images, and audio in a single request across 23 languages. Phi-4-mini-instruct runs fast text-only inference at 3.8 billion parameters with a 131K token context window.

This connector brings all three models into Power Platform with three MCP tools for Copilot Studio and three REST operations for Power Automate and Power Apps. Each model gets its own dedicated operation—no shared endpoints, no model selection parameters.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20Phi-4)

## The three models

| Model | Parameters | Context | Languages | Specialization | Status |
|-------|-----------|---------|-----------|---------------|--------|
| Phi-4-Reasoning-Vision-15B | 15B | 128K | English | Math, science, UI understanding, visual reasoning | Experiment |
| Phi-4-multimodal-instruct | 5.6B | 131K | 23 | Speech + vision + text simultaneously | Public Preview |
| Phi-4-mini-instruct | 3.8B | 131K | 23 | Fast text-only inference | Public Preview |

All three are self-sufficient—no borrowed tools or external dependencies. They produce human-readable outputs natively. Developer: Microsoft Research. License: MIT.

### Phi-4-Reasoning-Vision-15B

The largest of the three at 15 billion parameters. It takes an image and a text prompt, then returns structured output with two parts: step-by-step reasoning (the model's thinking process) and a final answer. The connector automatically extracts these from the model's output, which may include `<think>` tags for the reasoning section.

This model excels at tasks that require looking at an image and thinking through a problem: solving math equations from handwritten notes, interpreting scientific diagrams, reading invoices and forms, analyzing UI screenshots for testing, and understanding flowcharts or architecture diagrams.

### Phi-4-multimodal-instruct

Processes text, images, and audio in a single request. At 5.6 billion parameters with 23-language support, it handles scenarios that cross modality boundaries: transcribing audio while referencing a related image, translating text shown in a photo, or answering questions about a document that was read aloud.

Inputs can be URLs or base64 data URIs. One image and one audio file per request through the connector's simplified interface.

### Phi-4-mini-instruct

The lightweight option at 3.8 billion parameters. Text-only, but with a 131K token context window and 23-language support. Fast inference makes it suitable for high-volume scenarios: quick Q&A, content generation, code assistance, or lightweight agent backends with function-calling.

Uses the standard chat completion messages format with system, user, and assistant roles.

## Tools

### MCP tools for Copilot Studio

| Tool | Model | Description |
|------|-------|-------------|
| `reason_with_vision` | Phi-4-Reasoning-Vision-15B | Visual reasoning with image + text input, returns reasoning and answer |
| `chat_multimodal` | Phi-4-multimodal-instruct | Multimodal chat with optional image and audio |
| `chat_mini` | Phi-4-mini-instruct | Lightweight text-only chat |

### How it works

```
User: "What's the answer to this math problem?"
      [attaches photo of a handwritten equation]

1. Orchestrator calls reason_with_vision({
     prompt: "Solve this equation and show your work",
     image_url: "https://..."
   })

   → Returns:
     reasoning: "The equation shows 3x + 7 = 22.
                 Subtract 7 from both sides: 3x = 15.
                 Divide both sides by 3: x = 5."
     answer: "x = 5"
```

```
User: "What is this person saying in the audio clip?
       The whiteboard behind them might have context."
      [provides audio URL and image URL]

2. Orchestrator calls chat_multimodal({
     prompt: "Transcribe the audio and relate it to the whiteboard content",
     image_url: "https://...",
     audio_url: "https://..."
   })

   → Returns transcription with visual context
```

## REST operations for Power Automate and Power Apps

| Operation | Operation ID | Model | Method | Path |
|-----------|-------------|-------|--------|------|
| Reason With Vision | `ReasonWithVision` | Phi-4-Reasoning-Vision-15B | POST | `/phi4/reason` |
| Chat Multimodal | `ChatMultimodal` | Phi-4-multimodal-instruct | POST | `/phi4/multimodal` |
| Chat Mini | `ChatMini` | Phi-4-mini-instruct | POST | `/phi4/chat` |

### Parameter reference

| Operation | Parameter | Type | Default | Required |
|-----------|-----------|------|---------|----------|
| Reason With Vision | `prompt` | string | — | Yes |
| Reason With Vision | `image_url` | string | — | Yes |
| Reason With Vision | `system_prompt` | string | — | No |
| Reason With Vision | `temperature` | float | 0.7 | No |
| Reason With Vision | `max_tokens` | int | 4096 | No |
| Chat Multimodal | `prompt` | string | — | Yes |
| Chat Multimodal | `image_url` | string | — | No |
| Chat Multimodal | `audio_url` | string | — | No |
| Chat Multimodal | `system_prompt` | string | — | No |
| Chat Multimodal | `temperature` | float | 0.7 | No |
| Chat Multimodal | `max_tokens` | int | 4096 | No |
| Chat Mini | `messages` | array | — | Yes |
| Chat Mini | `temperature` | float | 0.7 | No |
| Chat Mini | `top_p` | float | 1.0 | No |
| Chat Mini | `max_tokens` | int | 4096 | No |

### Reason With Vision response

The vision reasoning operation returns a structured response that separates the model's thinking from its conclusion:

| Field | Description |
|-------|-------------|
| `reasoning` | Step-by-step thinking from the model |
| `answer` | The final answer after reasoning |
| `model` | Model identifier |
| `usage` | Token usage (prompt, completion, total) |

The connector handles extraction of reasoning content from `<think>` tags automatically. You get clean reasoning and answer fields without parsing raw model output.

## Use cases

**Document analysis with reasoning**: Send an invoice photo to `reason_with_vision` and ask "What are the line items and totals?" The model reasons through the document structure, identifies tables and amounts, and returns a structured answer.

**Visual math and science**: Students or analysts can photograph handwritten equations, circuit diagrams, or data charts. The vision reasoning model works through the problem step by step and provides the solution.

**UI testing from screenshots**: Send a screenshot to `reason_with_vision` with "Does this UI match the design spec? Check alignment, colors, and text." The model analyzes the visual layout and reports discrepancies.

**Multilingual multimodal processing**: Use `chat_multimodal` to process a photo of a sign in one language while providing audio instructions in another. The model handles 23 languages across all input modalities.

**Audio transcription with visual context**: Send a recording of someone presenting alongside an image of their slides. `chat_multimodal` transcribes the audio and relates it to the visual content.

**High-volume text processing**: Use `chat_mini` for tasks where speed matters more than model size—content classification, entity extraction, quick summaries, or lightweight agent backends in Power Automate flows.

## Prerequisites

1. An Azure subscription with access to Microsoft Foundry
2. Deploy one or more Phi-4 models from the Foundry Model Catalog:
   - [Phi-4-Reasoning-Vision-15B](https://ai.azure.com/explore/models/Phi-4-Reasoning-Vision-15B/version/1/registry/azureml-phi-prod) — for vision reasoning
   - [Phi-4-multimodal-instruct](https://ai.azure.com/explore/models/Phi-4-multimodal-instruct/version/1/registry/azureml) — for multimodal chat
   - [Phi-4-mini-instruct](https://ai.azure.com/explore/models/Phi-4-mini-instruct/version/1/registry/azureml) — for text chat
3. Note the **Resource Name** (for example, `my-foundry-resource` from `https://my-foundry-resource.services.ai.azure.com`) and **API Key** from the deployment

You don't need to deploy all three models. Only deploy the ones you plan to use—each operation targets a specific model.

## Setting up the connector

### 1. Deploy Phi-4 models in Microsoft Foundry

1. Go to the [Foundry Model Catalog](https://ai.azure.com/explore/models)
2. Search for Phi-4 and deploy the model(s) you need
3. Copy the **Resource Name** and **API Key** from the deployment page

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

Test `ReasonWithVision` with any publicly accessible image URL and a prompt like "Describe what you see in this image."

Test `ChatMini` with a simple messages array:

```json
{
  "messages": [
    { "role": "user", "content": "What is the capital of France?" }
  ]
}
```

### 5. Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "Analyze this image" or "What does this diagram show?"

## Known limitations

- Vision reasoning model outputs may include `<think>` tags—the connector extracts reasoning content automatically, but unusual output formats may not parse cleanly
- Audio input format for the multimodal model may vary by deployment configuration
- All three are small language models—they may not match larger models on complex tasks
- Image and audio inputs must be accessible via URL or provided as base64 data URIs
- Only one image and one audio file per multimodal request through the simplified interface; use Chat Mini with raw messages for multi-turn conversations
- Phi-4-Reasoning-Vision-15B currently supports English only; the other two models support 23 languages

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 3 REST operations |
| `apiProperties.json` | API Key auth config and script operation bindings |
| `script.csx` | C# script handling MCP protocol, vision reasoning extraction, multimodal message construction, and model routing |
| `readme.md` | Setup and usage documentation |

## Resources

- [Phi-4 connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20Phi-4)
- [Phi-4-Reasoning-Vision-15B in Foundry Catalog](https://ai.azure.com/explore/models/Phi-4-Reasoning-Vision-15B/version/1/registry/azureml-phi-prod)
- [Phi-4-multimodal-instruct in Foundry Catalog](https://ai.azure.com/explore/models/Phi-4-multimodal-instruct/version/1/registry/azureml)
- [Phi-4-mini-instruct in Foundry Catalog](https://ai.azure.com/explore/models/Phi-4-mini-instruct/version/1/registry/azureml)
- [Microsoft Foundry API](https://learn.microsoft.com/en-us/rest/api/aifoundry/)
