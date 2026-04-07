---
layout: post
title: "Microsoft Foundry MAI Voice MCP connector for Power Platform"
date: 2026-04-07 14:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [MAI-Voice-1, Microsoft Foundry, MCP, Copilot Studio, Custom Connectors, Power Platform, Text-to-Speech, Voice, AI]
description: "Power Platform custom connector for Microsoft Foundry text-to-speech models—generate natural speech with MAI-Voice-1 including custom voice cloning, emotional range, and SSML control through MCP tools and REST operations."
---

A flow triggers when a new blog post publishes. It generates an audio narration, uploads the MP3 to SharePoint, and links it in the post metadata. No recording studio, no human narrator, no manual steps.

MAI-Voice-1 launched April 2, 2026, as part of [Microsoft's three-model MAI announcement](https://microsoft.ai/news/today-were-announcing-3-new-world-class-mai-models-available-in-foundry/) alongside MAI-Transcribe-1 and MAI-Image-2. It generates 60 seconds of audio in 1 second with emotional range, speaker identity preservation, and custom voice cloning from just a few seconds of sample audio. Already powering Copilot Audio Expressions and Copilot Podcasts.

This connector brings MAI-Voice-1 and Azure Neural TTS voices into Power Platform with three MCP tools for Copilot Studio and three REST operations for Power Automate and Power Apps. A borrowed chat completion tool helps agents generate SSML markup and select voices within a conversation.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20MAI%20Voice)

## The model

| Model | Speed | Languages | Pricing |
|-------|-------|-----------|---------|
| MAI-Voice-1 | 60 seconds of audio in 1 second | Multiple | $22 per 1M characters |
| Azure Neural TTS | Standard | 100+ locales | Varies by region |

MAI-Voice-1 delivers top-tier voice generation with nuance, emotional range, and expression that preserves speaker identity across long-form content. Custom voice cloning requires separate enrollment through Azure Speech Studio.

## Tools

### MCP tools for Copilot Studio

| Tool | Description |
|------|-------------|
| `synthesize_speech` | Convert text to speech audio with voice, language, and format selection |
| `list_voices` | Get available voices with optional locale filtering |
| `chat_completion` | Generate SSML, suggest voices, or discuss speech parameters (borrowed from parent Foundry connector) |

### How it works

```
User: "Read this announcement in a warm, professional voice"

1. Orchestrator calls list_voices({
     locale_filter: "en-US"
   })

   → Returns available voices with styles:
     [
       { shortName: "en-US-JennyNeural", gender: "Female",
         styles: ["cheerful", "sad", "angry", "excited", ...] },
       { shortName: "en-US-GuyNeural", gender: "Male",
         styles: ["newscast", "angry", "cheerful", ...] },
       ...
     ]

2. Orchestrator calls synthesize_speech({
     text: "We're excited to announce...",
     voice: "en-US-JennyNeural",
     language: "en-US",
     output_format: "audio-48khz-192kbitrate-mono-mp3"
   })

   → Returns: { status: "success", audio_size_bytes: 48320,
                 voice: "en-US-JennyNeural" }
```

```
User: "Generate SSML with emphasis on the product name"

3. Orchestrator calls chat_completion({
     prompt: "Write SSML that emphasizes 'Power Platform'
              in this sentence: Power Platform now supports
              voice-enabled agents.",
     system_prompt: "You are an SSML expert"
   })

   → Returns SSML with prosody and emphasis tags
```

## REST operations for Power Automate and Power Apps

| Operation | Operation ID | Method | Path |
|-----------|-------------|--------|------|
| Synthesize Speech | `SynthesizeSpeech` | POST | `/cognitiveservices/v1` |
| List Available Voices | `ListVoices` | GET | `/cognitiveservices/voices/list` |
| Chat Completion | `ChatCompletion` | POST | `/models/chat/completions` |

### Parameter reference

| Operation | Parameter | Type | Default | Required |
|-----------|-----------|------|---------|----------|
| Synthesize Speech | `X-Microsoft-OutputFormat` | enum | audio-24khz-96kbitrate-mono-mp3 | Yes |
| Synthesize Speech | `body` (SSML) | string | — | Yes |
| Chat Completion | `messages` | array | — | Yes |
| Chat Completion | `temperature` | float | 0.7 | No |
| Chat Completion | `max_tokens` | int | 4096 | No |

### Audio output formats

| Format | Quality | Use case |
|--------|---------|----------|
| `audio-24khz-96kbitrate-mono-mp3` | General purpose | Default, good balance of quality and size |
| `audio-48khz-192kbitrate-mono-mp3` | High quality | Podcasts, professional narration |
| `riff-24khz-16bit-mono-pcm` | Uncompressed WAV | Post-processing, editing |
| `ogg-24khz-16bit-mono-opus` | Web optimized | Browser playback, streaming |

### SSML input

The Synthesize Speech operation takes SSML (Speech Synthesis Markup Language) as input, giving you control over voice selection, language, prosody, emphasis, breaks, and speaking styles:

```xml
<speak version='1.0' xml:lang='en-US'>
  <voice xml:lang='en-US' name='en-US-JennyNeural'>
    <prosody rate="medium" pitch="default">
      Welcome to today's update.
      <break time="500ms"/>
      Here's what's new.
    </prosody>
  </voice>
</speak>
```

Use the `chat_completion` tool or operation to have an LLM generate SSML from plain text with the right voice, pacing, and emphasis for your content.

### List Voices response

Each voice includes:

| Field | Description |
|-------|-------------|
| `ShortName` | Voice identifier for SSML (for example, `en-US-JennyNeural`) |
| `DisplayName` | Human-readable name |
| `Gender` | Male or Female |
| `Locale` | Language and region code |
| `StyleList` | Supported speaking styles (cheerful, sad, newscast, etc.) |

## Use cases

**Automated narration pipeline**: Build a Power Automate flow that watches for new content in SharePoint, synthesizes audio narration, and stores the MP3 alongside the original document. Training materials, policy updates, and announcements get audio versions automatically.

**Voice agent responses**: Give your Copilot Studio agent a voice. Use `synthesize_speech` to convert the agent's text responses to audio for phone-based or accessibility-first scenarios.

**Multilingual voice output**: List voices filtered by locale, select the right voice for the target language, and synthesize speech—all within the same flow. Support content in dozens of languages without maintaining separate voice configurations.

**Podcast and audio content generation**: Use high-quality output formats (`audio-48khz-192kbitrate-mono-mp3`) for professional-grade audio. Combine with MAI-Transcribe-1 for a full audio content pipeline—transcribe interviews, edit the text, re-synthesize as polished narration.

**Branded voice experiences**: Clone a specific voice through Azure Speech Studio, then use this connector to generate branded audio content at scale. Product announcements, customer communications, and training materials all sound consistent.

**Accessibility**: Convert text content to speech for users who prefer or need audio. Reports, dashboards, notifications—anything text-based can get an audio version through a simple flow.

## Prerequisites

1. An Azure subscription with access to Microsoft Foundry
2. Speech Services enabled on your Foundry resource (MAI-Voice-1 is available through the Foundry Model Catalog)
3. Note the **Resource Name**, **API Key**, and **Region** (for example, `eastus2`) from the Azure portal

## Setting up the connector

### 1. Enable Speech Services

1. Go to [Microsoft Foundry](https://ai.azure.com/)
2. Ensure Speech Services are enabled on your resource
3. Copy the **Resource Name**, **API Key**, and **Region** from the deployment page

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
2. Enter your **Resource Name**, **API Key**, and **Region**
3. Select **Create connection**

### 4. Test the connector

Test `ListVoices` first to see available voices. Then test `SynthesizeSpeech` with simple SSML:

```xml
<speak version='1.0' xml:lang='en-US'>
  <voice xml:lang='en-US' name='en-US-JennyNeural'>
    Hello, this is a test of the MAI Voice connector.
  </voice>
</speak>
```

### 5. Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "List available English voices" or "Convert this text to speech"

## Known limitations

- Audio output is capped at 10 minutes per request
- SSML body length is limited by the Speech Services API
- Custom voice cloning requires separate enrollment through Azure Speech Studio
- The MCP `synthesize_speech` tool generates audio but cannot return binary data directly to the agent—use the REST `SynthesizeSpeech` operation to retrieve audio files
- The connector uses two different host patterns: `{region}.tts.speech.microsoft.com` for speech operations and `.services.ai.azure.com` for chat and MCP
- Connection requires three parameters (Resource Name, API Key, Region) unlike other Foundry connectors that need only two

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 3 REST operations |
| `apiProperties.json` | API Key auth config, region-based dynamic host URL policies, and script operation bindings |
| `script.csx` | C# script handling MCP protocol, SSML generation, voice listing with locale filtering, and host routing |
| `readme.md` | Setup and usage documentation |

## Resources

- [MAI Voice connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20MAI%20Voice)
- [Microsoft Foundry Model Catalog](https://ai.azure.com/explore/models)
- [MAI-Voice-1 model card (PDF)](https://microsoft.ai/pdf/MAI-Voice-1-Model-Card.pdf)
- [3 new MAI models announcement](https://microsoft.ai/news/today-were-announcing-3-new-world-class-mai-models-available-in-foundry/)
- [SSML reference](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup)
- [Azure Speech Service voices](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts)
- [MAI Playground](https://playground.microsoft.ai/chat) (US only)
