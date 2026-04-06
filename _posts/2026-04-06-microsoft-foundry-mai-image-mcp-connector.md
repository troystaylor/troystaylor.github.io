---
layout: post
title: "Microsoft Foundry MAI Image MCP connector for Power Platform"
date: 2026-04-06 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [MAI-Image-2, Microsoft Foundry, MCP, Copilot Studio, Custom Connectors, Power Platform, Image Generation, AI]
description: "Power Platform custom connector for Microsoft Foundry image generation models—photorealistic images from text prompts with MAI-Image-2 and gpt-image-1.5, plus a borrowed chat completion tool for describing generated images through MCP."
---

MAI-Image-2 launched April 2, 2026, as part of [Microsoft's three-model MAI announcement](https://microsoft.ai/news/today-were-announcing-3-new-world-class-mai-models-available-in-foundry/) alongside MAI-Transcribe-1 and MAI-Voice-1. It ranks in the top 3 on the Arena.ai text-to-image leaderboard and delivers at least 2x faster generation times on Foundry and Copilot based on real-world production traffic data. Accurate skin tones, natural lighting, and clear in-image text rendering—built for photographers, designers, and visual storytellers who need campaign-ready imagery from text prompts.

This connector brings MAI-Image-2 and gpt-image-1.5 into Power Platform with two MCP tools for Copilot Studio and two REST operations for Power Automate and Power Apps. A borrowed chat completion operation lets agents describe, interpret, or discuss generated images within a conversation.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20MAI%20Image)

## The models

| Model | Specialization | Pricing |
|-------|---------------|---------|
| MAI-Image-2 | Photorealistic images, accurate skin tones, natural lighting, in-image text | $5 per 1M text input tokens + $33 per 1M image output tokens |
| gpt-image-1.5 | General image generation | Varies by quality (low ~$0.009, medium ~$0.034, high ~$0.133 per 1024x1024) |

Both models accept the same parameters—prompt, size, quality, style, response format, and output format—through a single operation. Select the model at request time.

## Tools

### MCP tools for Copilot Studio

| Tool | Description |
|------|-------------|
| `generate_image` | Generate photorealistic images from text prompts, returns image URLs or base64 data |
| `chat_completion` | Send a chat message to describe, interpret, or discuss generated images (borrowed from parent Foundry connector) |

### How it works

```
User: "Create a product photo of a coffee mug on a wooden table
       with morning sunlight streaming through a window"

1. Orchestrator calls generate_image({
     prompt: "Product photo of a white ceramic coffee mug on a
              rustic wooden table, warm morning sunlight streaming
              through a curtained window, shallow depth of field,
              photorealistic",
     quality: "high",
     style: "natural"
   })

   → Returns:
     url: "https://..."  (temporary, expires in 60 minutes)
     revised_prompt: "A white ceramic coffee mug sitting on..."
     image_count: 1
     usage: { input_tokens: 42, output_tokens: 1024 }
```

```
User: "Describe this image and suggest how to improve the prompt"

2. Orchestrator calls chat_completion({
     prompt: "Describe this product photo and suggest prompt
              improvements for better composition",
     system_prompt: "You are an expert product photographer"
   })

   → Returns suggestions for prompt refinement
```

## REST operations for Power Automate and Power Apps

| Operation | Operation ID | Method | Path |
|-----------|-------------|--------|------|
| Generate Photorealistic Image | `GeneratePhotorealisticImage` | POST | `/images/generations` |
| Chat Completion | `ChatCompletion` | POST | `/chat/completions` |

### Parameter reference

| Operation | Parameter | Type | Default | Required |
|-----------|-----------|------|---------|----------|
| Generate Photorealistic Image | `prompt` | string | — | Yes |
| Generate Photorealistic Image | `model` | string | — | No |
| Generate Photorealistic Image | `n` | int | 1 | No |
| Generate Photorealistic Image | `size` | enum | 1024x1024 | No |
| Generate Photorealistic Image | `quality` | enum | auto | No |
| Generate Photorealistic Image | `style` | enum | — | No |
| Generate Photorealistic Image | `response_format` | enum | url | No |
| Generate Photorealistic Image | `output_format` | enum | — | No |
| Chat Completion | `messages` | array | — | Yes |
| Chat Completion | `temperature` | float | 0.7 | No |
| Chat Completion | `max_tokens` | int | 4096 | No |

### Size options

| Value | Aspect ratio | Use case |
|-------|-------------|----------|
| `1024x1024` | Square | Social media posts, profile images |
| `1536x1024` | Landscape | Blog headers, presentation slides |
| `1024x1536` | Portrait | Story formats, mobile content |
| `auto` | Model decides | Let the model choose based on prompt |

### Generate Photorealistic Image response

| Field | Description |
|-------|-------------|
| `url` | Temporary download link (expires after 60 minutes) |
| `b64_json` | Base64-encoded image data (when `response_format` is `b64_json`) |
| `revised_prompt` | The revised prompt used to generate the image, if the model modified it |
| `usage` | Token usage (input, output, total) |

## Use cases

**Marketing content and campaign imagery**: Generate on-brand product photos, social media graphics, and ad visuals directly from Power Automate flows. Pair with the chat completion tool to iterate on prompts until the output matches creative direction.

**Product visualization and mockups**: Create realistic product renders from text descriptions before investing in physical photography. Adjust lighting, backgrounds, and compositions through prompt parameters.

**Branded asset creation**: Generate social media posts, banner ads, and presentation graphics with consistent visual style. Use the `natural` style for photorealistic results or `vivid` for bold, attention-grabbing imagery.

**Presentation graphics with in-image text**: MAI-Image-2 handles text rendering better than most image generation models. Generate slides, infographics, and labeled diagrams with readable text baked into the image.

**Creative concept exploration**: Use a Copilot Studio agent to brainstorm visual concepts interactively. Generate variations, get the agent to describe what it sees via `chat_completion`, and refine prompts in a conversational loop.

## Prerequisites

1. An Azure subscription with access to Microsoft Foundry
2. Deploy an image generation model from the Foundry Model Catalog:
   - MAI-Image-2 — for photorealistic image generation
   - gpt-image-1.5 — for general image generation
3. Note the **Resource Name** (for example, `my-foundry-resource` from `https://my-foundry-resource.services.ai.azure.com`) and **API Key** from the deployment

## Setting up the connector

### 1. Deploy an image model in Microsoft Foundry

1. Go to the [Foundry Model Catalog](https://ai.azure.com/explore/models)
2. Search for MAI-Image-2 or gpt-image-1.5 and deploy the model
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

Test `GeneratePhotorealisticImage` with a simple prompt:

```json
{
  "prompt": "A golden retriever sitting in a field of wildflowers at sunset, photorealistic"
}
```

The response includes an image URL you can open in a browser to verify the output.

### 5. Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "Generate a product photo of..." or "Create a banner image for..."

## Known limitations

- Image URLs expire after 60 minutes—use `b64_json` response format for persistent storage
- Base64 responses can be large (1 MB or more for high-quality PNG)
- Maximum 10 images per request
- Maximum 32,000 character prompt
- The `chat_completion` tool is borrowed from the parent Microsoft Foundry connector and requires a chat-capable model deployed to the same resource

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 2 REST operations |
| `apiProperties.json` | API Key auth config, dynamic host URL policy, and script operation bindings |
| `script.csx` | C# script handling MCP protocol, image generation forwarding, and chat completion with Application Insights telemetry |
| `readme.md` | Setup and usage documentation |

## Resources

- [MAI Image connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20MAI%20Image)
- [Microsoft Foundry Model Catalog](https://ai.azure.com/explore/models)
- [Microsoft Foundry API](https://learn.microsoft.com/en-us/rest/api/aifoundry/)
- [MAI-Image-2 model card (PDF)](https://microsoft.ai/pdf/MAI-Image-2-Model-Card.pdf)
- [3 new MAI models announcement](https://microsoft.ai/news/today-were-announcing-3-new-world-class-mai-models-available-in-foundry/)
- [MAI Playground](https://playground.microsoft.ai/chat) (US only)
- [Arena.ai text-to-image leaderboard](https://arena.ai/)
