---
layout: post
title: "Microsoft Foundry MAI Speech MCP connector for Power Platform"
date: 2026-04-06 12:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [MAI-Transcribe-1, Microsoft Foundry, MCP, Copilot Studio, Custom Connectors, Power Platform, Speech-to-Text, Transcription, AI]
description: "Power Platform custom connector for Microsoft Foundry speech-to-text models—transcribe and translate audio with MAI-Transcribe-1 and Whisper, plus a borrowed chat completion tool for summarizing transcriptions through MCP."
---

MAI-Transcribe-1 launched April 2, 2026, as part of [Microsoft's three-model MAI announcement](https://microsoft.ai/news/today-were-announcing-3-new-world-class-mai-models-available-in-foundry/) alongside MAI-Voice-1 and MAI-Image-2. It delivers state-of-the-art speech-to-text accuracy at 3.9% average word error rate, 2.5x faster batch transcription than Azure Fast, and ranks first on the FLEURS benchmark in 11 core languages across the top 25 most-used languages.

Built for messy, real-world audio environments—not clean studio recordings. Meeting rooms with background chatter, phone calls with connection noise, field recordings with wind and traffic.

This connector brings MAI-Transcribe-1 and Whisper into Power Platform with two MCP tools for Copilot Studio and three REST operations for Power Automate and Power Apps. A borrowed chat completion operation lets agents summarize, analyze, or discuss transcription results within a conversation.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20MAI%20Speech)

## The models

| Model | Accuracy | Languages | Pricing |
|-------|----------|-----------|---------|
| MAI-Transcribe-1 | 3.9% avg WER, #1 on FLEURS in 11 core languages | 25+ | $0.36 per hour of audio |
| Whisper | Varies by deployment | 50+ | Varies by deployment |

Both models support the same operations—transcription and translation—through separate REST endpoints that take a deployment ID parameter. Select the model at deployment time.

## Tools

### MCP tools for Copilot Studio

| Tool | Description |
|------|-------------|
| `transcribe_audio` | Transcribe audio from a URL to text, with optional deployment ID, language, and response format |
| `chat_completion` | Send a chat message to summarize or discuss transcriptions (borrowed from parent Foundry connector) |

### How it works

```
User: "Transcribe the recording from today's standup meeting"
      [provides audio URL]

1. Orchestrator calls transcribe_audio({
     audio_url: "https://storage.blob.core.windows.net/.../standup.mp3",
     language: "en",
     response_format: "verbose_json"
   })

   → Returns:
     text: "Good morning everyone. Let's start with updates..."
     language: "en"
     duration: 847.5
     segments: [{ start: 0.0, end: 3.2, text: "Good morning everyone." }, ...]
```

```
User: "Summarize that meeting and pull out the action items"

2. Orchestrator calls chat_completion({
     prompt: "Summarize this transcript and list action items:
              Good morning everyone. Let's start with updates...",
     system_prompt: "You are a meeting notes assistant"
   })

   → Returns structured meeting summary with action items
```

## REST operations for Power Automate and Power Apps

| Operation | Operation ID | Method | Path |
|-----------|-------------|--------|------|
| Transcribe Audio | `TranscribeAudio` | POST | `/openai/deployments/{deployment_id}/audio/transcriptions` |
| Translate Audio to English | `TranslateAudio` | POST | `/openai/deployments/{deployment_id}/audio/translations` |
| Chat Completion | `ChatCompletion` | POST | `/models/chat/completions` |

### Parameter reference

| Operation | Parameter | Type | Default | Required |
|-----------|-----------|------|---------|----------|
| Transcribe Audio | `deployment_id` | string | — | Yes |
| Transcribe Audio | `file` | file | — | Yes |
| Transcribe Audio | `language` | string | — | No |
| Transcribe Audio | `prompt` | string | — | No |
| Transcribe Audio | `response_format` | enum | — | No |
| Transcribe Audio | `temperature` | float | 0 | No |
| Translate Audio | `deployment_id` | string | — | Yes |
| Translate Audio | `file` | file | — | Yes |
| Translate Audio | `prompt` | string | — | No |
| Translate Audio | `response_format` | enum | — | No |
| Translate Audio | `temperature` | float | 0 | No |
| Chat Completion | `messages` | array | — | Yes |
| Chat Completion | `temperature` | float | 0.7 | No |
| Chat Completion | `max_tokens` | int | 4096 | No |

### Response format options

| Format | Output | Use case |
|--------|--------|----------|
| `json` | Simple JSON with text | Quick text extraction |
| `text` | Plain text only | Downstream text processing |
| `verbose_json` | JSON with timestamps and segments | Meeting minutes, indexed search |
| `srt` | SubRip subtitle format | Video subtitles |
| `vtt` | WebVTT subtitle format | Web video captions |

### Transcription response

| Field | Description |
|-------|-------------|
| `text` | The transcribed or translated text |
| `language` | Detected or specified language |
| `duration` | Audio duration in seconds |
| `segments` | Timestamped segments (verbose_json only) |

## Use cases

**Meeting transcription and minutes**: Transcribe a meeting recording, then use `chat_completion` to extract action items, decisions, and key discussion points. The `verbose_json` format provides timestamps for linking notes back to specific moments.

**Call recording analysis and compliance**: Process customer service or sales calls through `TranscribeAudio`, then analyze for compliance keywords, sentiment, or escalation triggers using the chat completion tool.

**Multilingual content transcription**: MAI-Transcribe-1 supports 25+ languages with auto-detection. Transcribe content in the original language or use `TranslateAudio` to translate any supported language into English text.

**Subtitle generation**: Use the `srt` or `vtt` response format to generate ready-to-use subtitle files for video content. Drop the output directly into your video publishing workflow.

**Voice memo processing**: Build a Power Automate flow that watches a SharePoint folder for audio uploads, transcribes each file, and stores the text alongside the original recording.

**Podcast and media transcription**: Process long-form audio content for searchable archives, show notes, or accessibility compliance.

## Prerequisites

1. An Azure subscription with access to Microsoft Foundry
2. Deploy a speech-to-text model from the Foundry Model Catalog:
   - MAI-Transcribe-1 — for state-of-the-art transcription accuracy
   - Whisper — for broad language support
3. Note the **Resource Name** (for example, `my-foundry-resource` from `https://my-foundry-resource.openai.azure.com`) and **API Key** from the deployment

## Setting up the connector

### 1. Deploy a speech model in Microsoft Foundry

1. Go to the [Foundry Model Catalog](https://ai.azure.com/explore/models)
2. Search for MAI-Transcribe-1 or Whisper and deploy the model
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

Test `TranscribeAudio` by uploading a short audio file (mp3, wav, or m4a) and setting the deployment ID to your model name (for example, `MAI-Transcribe-1`).

### 5. Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "Transcribe this audio file" or "What was discussed in this recording?"

The MCP `transcribe_audio` tool downloads audio from a URL, so provide publicly accessible links or SAS URLs for files in Azure Storage.

## Known limitations

- Audio files must be 25 MB or smaller
- Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
- For files larger than 25 MB, use the Azure Speech batch transcription API instead
- The MCP `transcribe_audio` tool downloads audio from the provided URL—files must be publicly accessible or use a SAS URL
- The `chat_completion` tool is borrowed from the parent Microsoft Foundry connector and requires a chat-capable model deployed to the same resource
- The connector uses two different host patterns: `.openai.azure.com` for audio operations and `.services.ai.azure.com` for chat and MCP

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 3 REST operations |
| `apiProperties.json` | API Key auth config, dual dynamic host URL policies, and script operation bindings |
| `script.csx` | C# script handling MCP protocol, audio file download and multipart forwarding, chat completion, and Application Insights telemetry |
| `readme.md` | Setup and usage documentation |

## Resources

- [MAI Speech connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20MAI%20Speech)
- [Microsoft Foundry Model Catalog](https://ai.azure.com/explore/models)
- [Microsoft Foundry API](https://learn.microsoft.com/en-us/rest/api/aifoundry/)
- [MAI-Transcribe-1 model card (PDF)](https://microsoft.ai/pdf/MAI-Transcribe-1-Model-Card.pdf)
- [3 new MAI models announcement](https://microsoft.ai/news/today-were-announcing-3-new-world-class-mai-models-available-in-foundry/)
- [MAI Playground](https://playground.microsoft.ai/chat) (US only)
