---
layout: post
title: "OpenDataLoader PDF MCP connector for Copilot Studio"
date: 2026-04-27 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Copilot Studio, MCP, PDF, OpenDataLoader, Azure Container Apps, Power Platform, Accessibility]
description: "Extract structured text, tables, and metadata from PDFs in Copilot Studio and Power Automate using a dual-mode MCP connector backed by OpenDataLoader PDF on Azure Container Apps."
---

PDFs are everywhere in enterprise workflows, and getting structured data out of them usually means either a paid API or a fragile parsing script. OpenDataLoader PDF is the top-ranked open-source PDF parser (0.907 overall accuracy), and this connector brings it directly into Copilot Studio and Power Automate.

The connector wraps OpenDataLoader PDF in a Flask API running on Azure Container Apps. Documents are processed entirely within the container—no external API calls, no data leaving the tenant.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/OpenDataLoader%20PDF%20MCP)

## What this connector does

The connector exposes five capabilities as both MCP tools and REST operations:

| Tool | Purpose |
|------|---------|
| `convert_pdf` | Convert PDF to Markdown, JSON (with bounding boxes), HTML, or text |
| `extract_tables` | Extract tables with row/column structure and cell content |
| `get_page_elements` | Get elements with bounding boxes and semantic types for RAG citations |
| `check_accessibility` | Check PDF accessibility tags for EAA/ADA/Section 508 compliance |
| `get_server_info` | Get service version, capabilities, and configuration |

MCP tools work in Copilot Studio agents. The matching REST operations work in Power Automate flows. Same connector, both modes.

## Why local processing matters

Every PDF stays within your Azure Container Apps instance. The processing pipeline runs locally inside the container using the OpenDataLoader PDF library and a Java 21 JRE. No document content is sent to external services unless you opt into hybrid mode for advanced features like OCR or formula extraction.

This matters for:

- Sensitive financial documents and contracts
- Documents under data residency requirements
- Scenarios where you need deterministic, repeatable output

## OpenDataLoader PDF capabilities

| Feature | Mode | Cost |
|---------|------|------|
| Text extraction with reading order | Local | Free (Apache 2.0) |
| Bounding boxes for every element | Local | Free |
| Table extraction (simple) | Local | Free |
| Table extraction (complex/borderless) | Hybrid | Free |
| Heading hierarchy detection | Local | Free |
| Image extraction with coordinates | Local | Free |
| OCR for scanned PDFs (80+ languages) | Hybrid | Free |
| Formula extraction (LaTeX) | Hybrid | Free |
| AI chart/image descriptions | Hybrid | Free |
| Prompt injection filtering | Local | Free |

## Architecture

```
┌────────────────────┐     ┌──────────────────────────────┐
│  Copilot Studio    │     │  Azure Container Apps        │
│  Agent             │     │                              │
│                    │ MCP │  ┌──────────────────────┐    │
│  ┌──────────────┐  │────>│  │  Flask API (Python)  │    │
│  │ OpenDataLoader│  │     │  │  + OpenDataLoader PDF│    │
│  │ PDF MCP      │  │<────│  │  + Java 21 JRE       │    │
│  │ (connector)  │  │     │  └──────────────────────┘    │
│  └──────────────┘  │     │                              │
└────────────────────┘     └──────────────────────────────┘
```

The Flask API accepts PDFs via URL or base64-encoded content and returns structured output. All POST endpoints use the same input format:

```json
{
  "source": "https://example.com/document.pdf",
  "sourceType": "url"
}
```

Or for base64:

```json
{
  "source": "<base64-encoded-pdf>",
  "sourceType": "base64"
}
```

## Quick deploy with pre-built image

The fastest path uses the pre-built image from GitHub Container Registry:

```powershell
cd "OpenDataLoader PDF MCP/infra"
.\deploy.ps1 -ResourceGroup rg-opendataloader -UseGhcrImage
```

This provisions Azure Container Apps infrastructure and deploys `ghcr.io/troystaylor/opendataloader-pdf-api:latest`. The script outputs your service URL and API key.

## Deploy from source

Build the container image in your own Azure Container Registry:

```powershell
cd "OpenDataLoader PDF MCP/infra"
.\deploy.ps1 -ResourceGroup rg-opendataloader
```

### Deploy script parameters

| Parameter | Required | Default | Purpose |
|-----------|----------|---------|---------|
| `ResourceGroup` | Yes | — | Azure resource group (created if needed) |
| `Location` | No | westus2 | Azure region |
| `ApiKey` | No | auto-generated | API key for the service |
| `SkipInfra` | No | false | Skip Bicep deployment |
| `SkipBuild` | No | false | Skip container image build |
| `ImageTag` | No | latest | Container image tag |
| `UseGhcrImage` | No | false | Use pre-built GHCR image |

## Azure resources deployed

The Bicep template provisions:

| Resource | SKU | Purpose |
|----------|-----|---------|
| Container Registry | Basic | Stores container image |
| Log Analytics Workspace | PerGB2018 | Container logs |
| Application Insights | Web | Telemetry and monitoring |
| Container Apps Environment | — | Hosting environment |
| Container App | 1 CPU / 2 GiB | OpenDataLoader PDF API |

The container app scales from 0 to 3 replicas and includes liveness and readiness probes on the `/health` endpoint.

## Connector setup

After deployment, the script outputs the service URL and API key.

1. Update `apiDefinition.swagger.json` host field to your service FQDN
2. Deploy the connector:

```powershell
pac connector create `
  --settings-file apiProperties.json `
  --api-definition apiDefinition.swagger.json `
  --script script.csx
```

3. Create a connection using your API key

## Use cases

### PDF to Markdown for RAG

Convert documents to clean Markdown for grounding AI responses:

> "Convert this PDF to markdown so I can analyze its contents"

### Table extraction

Extract structured tables from financial reports, invoices, or data sheets:

> "Extract all tables from this quarterly report PDF"

### Document analysis with citations

Get element-level data with bounding boxes for source citations:

> "Analyze this research paper and show me where each finding is located"

### Accessibility compliance

Check if organizational PDFs meet accessibility standards:

> "Check if this PDF has proper accessibility tags for EAA compliance"

## Observability with Application Insights

The deploy script outputs the App Insights instrumentation key. Enable telemetry in the connector by editing `script.csx`:

```csharp
private const string APP_INSIGHTS_KEY = "your-instrumentation-key-here";
```

## CI/CD with GitHub Actions

A workflow at `.github/workflows/opendataloader-pdf-build.yml` builds and publishes the container image to `ghcr.io/troystaylor/opendataloader-pdf-api`.

Triggers:

- Manual dispatch (`workflow_dispatch`) with optional version tag
- Push to `main` when files in `OpenDataLoader PDF MCP/container-app/` change

Tags applied: `latest` and git SHA.

## Files in this project

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | Swagger with MCP + REST operations |
| `apiProperties.json` | Connector properties (API key auth) |
| `script.csx` | MCP protocol handler |
| `container-app/app.py` | Flask REST API wrapping opendataloader-pdf |
| `container-app/Dockerfile` | Python 3.12 + Java 21 JRE |
| `container-app/requirements.txt` | Python dependencies |
| `infra/main.bicep` | Azure infrastructure template |
| `infra/deploy.ps1` | Deployment script |

## When to use this connector

Use this connector when you need PDF processing inside Copilot Studio or Power Automate and want the data to stay within your Azure tenant. It fits well for:

- RAG pipelines that need clean Markdown from source PDFs
- Document intake workflows that extract tables for downstream processing
- Compliance checks for accessibility standards across document libraries
- Citation-aware analysis where bounding box data ties findings back to source locations

## Resources

- [OpenDataLoader PDF MCP source code](https://github.com/troystaylor/SharingIsCaring/tree/main/OpenDataLoader%20PDF%20MCP)
- [OpenDataLoader PDF GitHub](https://github.com/opendataloader-project/opendataloader-pdf)
- [OpenDataLoader documentation](https://opendataloader.org/)
- [Custom connectors overview](https://learn.microsoft.com/connectors/custom-connectors/)
- [Copilot Studio documentation](https://learn.microsoft.com/microsoft-copilot-studio/)
