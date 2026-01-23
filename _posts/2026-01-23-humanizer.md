---
layout: post
title: "Humanizer: Copilot Studio connector for AI-sounding text"
date: 2026-01-23 09:00:00 -0500
categories: [Power Platform]
tags: [Humanizer, Content lint, PowerShell, GitHub Actions, Power Platform]
description: "Use the Humanizer MCP Power Platform connector in Copilot Studio to detect AI writing patterns and guide rewrites."
---

## What is Humanizer?

Humanizer is an **MCP-compliant Power Platform custom connector** (Copilot Studio compatible) that detects 24 AI writing patterns across content, language, style, communication, and filler, based on Wikipedia's "Signs of AI writing" guide. It exposes tools like `humanize`, `detect_patterns`, and `get_patterns`, returns an AI score (0–100), rewrite guidelines, and optional Application Insights telemetry.

> Treat findings as prompts to revise, not absolute blockers. The goal is a clear, human tone.

## Why this matters
- Use Humanizer’s 24 AI-writing patterns to keep content grounded
- Replace vague claims with specific facts, sources, and plain language
- Publish posts that read like you wrote them

## Setup (Copilot Studio)
1. Import the **Humanizer** custom connector into your Power Platform environment using `Humanizer/apiProperties.json` and `Humanizer/script.csx` from the repo.
2. In **Copilot Studio**, go to **Actions → Add an action → Power Platform connector** and select **Humanizer**.
3. Create a connection (no auth required by default; add App Insights connection string in `script.csx` if you want telemetry).

## Usage (Copilot Studio)
**Agent instruction**
> Before responding, call the `humanize` action with the draft text. If `aiScore` > 25, revise using `rewriteGuidelines` and respond with the improved text.

**Call `humanize` (full analysis + guidelines)**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 1,
  "params": {
    "name": "humanize",
    "arguments": {
      "text": "Sample draft text for analysis...",
      "mode": "full",
      "preserveTone": true
    }
  }
}
```

**Call `detect_patterns` (fast check by category)**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 1,
  "params": {
    "name": "detect_patterns",
    "arguments": {
      "text": "Sample draft text for analysis...",
      "category": "Communication"
    }
  }
}
```

**Call `get_patterns` (educate the user/agent)**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 1,
  "params": {
    "name": "get_patterns",
    "arguments": {
      "category": "Language",
      "includeExamples": true
    }
  }
}
```

### Sample response (`humanize`)
```json
{
  "success": true,
  "aiScore": 42,
  "aiScoreDescription": "Moderate - Several AI patterns present",
  "patternsDetected": 3,
  "detectedPatterns": [
    {
      "patternId": "chatbot_artifacts",
      "patternName": "Chatbot Artifacts",
      "category": "Communication",
      "matchedText": "sample text",
      "suggestion": "Remove chatbot phrases entirely."
    },
    {
      "patternId": "significance_inflation",
      "patternName": "Significance Inflation",
      "category": "Content",
      "matchedText": "sample text",
      "suggestion": "State facts directly."
    }
  ],
  "rewriteGuidelines": "## Rewrite Guidelines\n- Remove chatbot artifacts...\n- Replace vague claims with specific facts...\n"
}
```

## Customize patterns
Edit `AIPatterns` inside `Humanizer/script.csx` to add or adjust patterns (24 provided). Deploy the connector after updates.

## Copilot Studio tips
- Use `detect_patterns` for quick checks; use `humanize` when you need guidelines.
- Keep `preserveTone` = true to retain formal/technical voice; set false to allow aggressive rewrites.
- Show `get_patterns` content to users to explain why their text was flagged.

## Resources
- Humanizer connector: [SharingIsCaring/Humanizer](https://github.com/troystaylor/SharingIsCaring/tree/main/Humanizer)
- Tools: `humanize`, `detect_patterns`, `get_patterns`; Prompts: `humanize_text`, `quick_check`, `rewrite_as_human`, `match_voice`
- Wikipedia: [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)

