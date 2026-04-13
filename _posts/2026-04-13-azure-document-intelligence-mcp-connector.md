---
layout: post
title: "Azure Document Intelligence MCP connector for Power Platform"
date: 2026-04-13 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Azure Document Intelligence, OCR, MCP, Copilot Studio, Custom Connectors, Power Platform, MarkItDown, Document Processing]
description: "Power Platform custom connector for Azure Document Intelligence—extract text, tables, and structured fields from documents using 20 REST operations and 11 MCP tools. A production-grade alternative to MarkItDown for enterprise document processing."
---

Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) is a popular open-source Python utility for converting documents to Markdown. With 106k GitHub stars and support for PDFs, Office files, images, and audio, it's a go-to tool for developers feeding documents into LLM pipelines. It even has an [MCP server](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp) for Claude Desktop integration.

But MarkItDown is a developer tool. It requires Python, runs locally or in a container, and has no built-in authentication, compliance controls, or enterprise deployment model. If you need document intelligence inside Power Platform—where a Copilot Studio agent extracts invoice fields, a Power Automate flow classifies incoming documents, or a Power App reads receipts—you need something that speaks the platform's language.

This connector wraps the [Azure Document Intelligence REST API](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/) (v4.0 GA, 2024-11-30) with 20 operations for Power Automate and Power Apps, plus 11 MCP tools for Copilot Studio agents. Same AI models that power Microsoft 365 Copilot's document understanding, deployed behind your Azure subscription with your compliance boundaries.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Document%20Intelligence)

## MarkItDown vs. Document Intelligence connector

| | MarkItDown | Document Intelligence connector |
|---|---|---|
| **Runtime** | Python 3.10+, local or container | Power Platform (cloud, no code) |
| **Output format** | Markdown text | Structured JSON with fields, tables, key-value pairs |
| **Document models** | Generic conversion (PDF, DOCX, PPTX, XLSX) | 15+ prebuilt AI models (invoices, receipts, tax forms, IDs) |
| **Custom models** | None | Build, compose, and deploy custom extraction models |
| **Classification** | None | Build and run document classifiers |
| **OCR** | Plugin with LLM Vision (requires OpenAI key) | Built-in, no additional keys |
| **Authentication** | None | Azure AD OAuth or API key |
| **Enterprise deployment** | DIY (Docker, pip) | Custom connector import, PAC CLI |
| **Copilot integration** | MCP server for Claude Desktop | MCP tools for Copilot Studio agents |
| **Compliance** | Your responsibility | Azure data residency, RBAC, audit logs |
| **Cost** | Free (plus OpenAI costs for OCR) | Azure consumption-based (500 pages/month free on F0) |

MarkItDown excels at bulk Markdown conversion for LLM training pipelines. This connector excels when you need structured extraction—pulling specific fields from invoices, classifying document types, or building custom models for your domain-specific forms.

## Supported prebuilt models

| Model | What it extracts |
|-------|-----------------|
| `prebuilt-read` | Printed and handwritten text |
| `prebuilt-layout` | Text, tables, and document structure |
| `prebuilt-invoice` | Invoice fields (vendor, total, line items) |
| `prebuilt-receipt` | Receipt fields (merchant, date, total) |
| `prebuilt-idDocument` | ID cards and passports |
| `prebuilt-tax.us.w2` | W-2 tax form fields |
| `prebuilt-tax.us` | Unified US tax form extraction |
| `prebuilt-bankStatement` | Bank statement details |
| `prebuilt-healthInsuranceCard.us` | Insurance card fields |
| `prebuilt-contract` | Contract details |
| `prebuilt-creditCard` | Credit card fields |
| `prebuilt-check.us` | Check fields |
| `prebuilt-payStub.us` | Pay stub fields |
| `prebuilt-marriageCertificate.us` | Marriage certificate fields |
| `prebuilt-mortgage.us.*` | Various mortgage form models |

## 11 MCP tools

When added as an MCP connector in Copilot Studio, the agent gets 11 curated tools:

| Category | Tools |
|----------|-------|
| Analysis | Analyze document (all prebuilt/custom models), get analyze result |
| Models | List models, get model details |
| Classifiers | List classifiers, get classifier, classify document, get classify result |
| Operations | List operations, get operation status |
| Service | Get service info |

## 20 REST operations

For Power Automate and Power Apps, 20 operations cover the full API surface:

### Document models (10 operations)

- Analyze document (async—returns Operation-Location header)
- Get analyze result
- Analyze document output (produces searchable PDF)
- List models
- Get model
- Delete model
- Build custom model
- Compose model
- Authorize model copy
- Copy model

### Document classifiers (6 operations)

- Build classifier
- List classifiers
- Get classifier
- Delete classifier
- Classify document
- Get classify result

### Operations and service (3 operations)

- List operations
- Get operation
- Get service info

## How it works

Document analysis is async. The POST request returns HTTP 202 with an `Operation-Location` header. Poll until the status is `succeeded`.

```
User: "Extract the line items from this invoice"

1. Agent calls analyze_document({
     model: "prebuilt-invoice",
     document_url: "https://storage.blob.core.windows.net/invoices/april-2026.pdf"
   })

   → Returns operation ID: "3b9a21c4-..."

2. Agent calls get_analyze_result({
     operation_id: "3b9a21c4-..."
   })

   → Returns structured JSON:
     Vendor: "Zava Corp"
     Invoice Date: "2026-04-01"
     Total: "$12,450.00"
     Line Items:
       - "Cloud hosting - $8,200.00"
       - "Support plan - $4,250.00"
```

The MCP script handles polling automatically for Copilot Studio agents. In Power Automate flows, use the separate POST + GET operations with a Do Until loop.

## Handling async operations in Power Automate

```
┌─────────────────────────────┐
│ Analyze Document (POST)     │
│ Model: prebuilt-invoice     │
│ Document: invoice.pdf       │
└─────────────┬───────────────┘
              │ HTTP 202 + Operation-Location
              ▼
┌─────────────────────────────┐
│ Do Until: status = succeeded│
│ ┌─────────────────────────┐ │
│ │ Get Analyze Result      │ │
│ │ (GET Operation-Location)│ │
│ └─────────────────────────┘ │
│ Delay: 2 seconds            │
└─────────────┬───────────────┘
              │ status: succeeded
              ▼
┌─────────────────────────────┐
│ Parse extracted fields      │
│ Use in downstream actions   │
└─────────────────────────────┘
```

## Use cases

**Accounts payable automation**: A Power Automate flow monitors a SharePoint library for new invoices. The connector extracts vendor, amount, and line items using `prebuilt-invoice`. Parsed data flows into Dataverse for approval routing—no manual data entry.

**Document triage agent**: A Copilot Studio agent accepts uploaded documents, classifies them (invoice, receipt, contract, or ID), and routes each to the appropriate extraction model. The agent returns a structured summary and files it in the right SharePoint folder.

**Tax season processing**: Use `prebuilt-tax.us.w2` and `prebuilt-tax.us` to bulk-extract fields from employee tax documents. A Power Automate flow processes a folder of scanned W-2s and populates a Dataverse table for payroll review.

**Custom model for domain forms**: Build a custom extraction model trained on your organization's specific forms—inspection reports, intake forms, or work orders. Deploy it through the connector and let agents or flows extract your custom fields.

**Contract review assistant**: A Copilot Studio agent uses `prebuilt-contract` to extract key terms, parties, and dates from uploaded contracts. The agent summarizes obligations and flags renewal dates, then creates follow-up tasks in Planner.

## Authentication

### Option 1: API key

1. Go to your Document Intelligence resource in the Azure portal.
2. Navigate to **Keys and Endpoint**.
3. Copy the resource name (for example, `my-doc-intel` from `https://my-doc-intel.cognitiveservices.azure.com`).
4. Copy either Key 1 or Key 2.

### Option 2: Microsoft Entra ID (OAuth)

1. Register an application in Microsoft Entra ID.
2. Grant it the **Cognitive Services User** role on your Document Intelligence resource.
3. Create a client secret.
4. Provide the Client ID, Client Secret, and Resource Name when creating the connection.

## Prerequisites

1. An [Azure subscription](https://azure.microsoft.com/free/)
2. An [Azure Document Intelligence resource](https://portal.azure.com/#create/Microsoft.CognitiveServicesFormRecognizer) (or Azure AI Services multi-service resource)
3. An API key or Entra ID app registration with Cognitive Services User role

## Known limitations

- Free tier (F0) is limited to 500 pages/month.
- Custom neural model builds have per-resource quotas (check via Get Service Info).
- Maximum document size varies by model (typically 500 MB for prebuilt models).
- Some add-on features (high-resolution OCR, formula extraction) incur additional costs.

## Setting up the connector

1. Download the connector files from the [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Document%20Intelligence)
2. Import into Power Platform:

```powershell
pac auth create --environment "https://yourorg.crm.dynamics.com"
pac connector create --api-definition apiDefinition.swagger.json --api-properties apiProperties.json --script script.csx
```

Or import manually through **Power Automate > Data > Custom Connectors > Import an OpenAPI file**.

## Resources

- [Azure Document Intelligence documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- [Azure Document Intelligence REST API](https://learn.microsoft.com/en-us/rest/api/aiservices/document-intelligence)
- [MarkItDown on GitHub](https://github.com/microsoft/markitdown)
- [Full connector source](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Document%20Intelligence)
