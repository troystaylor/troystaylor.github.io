---
layout: post
title: "Power Compendium MCP connector for Power Platform"
date: 2026-04-14 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Power Compendium, Knowledge Base, MCP, Copilot Studio, Custom Connectors, Power Platform, Azure OpenAI, LLM Wiki, RAG]
description: "An organizational knowledge base connector for Power Platform and M365 Copilot that builds a persistent compendium of interlinked pages instead of re-deriving knowledge from raw documents on every query."
---

RAG re-reads your documents on every query. It retrieves chunks, feeds them to an LLM, and hopes the answer lands somewhere in the context window. It works, but it's wasteful—the LLM re-derives the same knowledge every time someone asks a similar question.

[Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) flips this. Instead of retrieval-at-query-time, the LLM processes documents once, extracts entities and concepts into interlinked pages, and maintains that knowledge base over time. Queries search the compendium, not the raw documents.

Power Compendium implements this pattern as an Azure Container App with a Power Platform connector—11 operations accessible via MCP (Copilot Studio, M365 Copilot, VS Code) and REST (Power Automate, Power Apps).

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Compendium)

## How it differs from RAG

| | Traditional RAG | Power Compendium |
|---|---|---|
| **Knowledge model** | Chunk retrieval at query time | Persistent interlinked pages built at ingest time |
| **LLM cost** | Every query processes raw chunks | Upfront cost at ingestion, queries search pre-built pages |
| **Knowledge quality** | Depends on chunk size and retrieval relevance | LLM-curated pages with cross-references and categories |
| **Updates** | Re-embed documents | Incremental—new sources update existing pages |
| **Cross-referencing** | None (isolated chunks) | Pages link to each other with `[[page-id]]` syntax |
| **Knowledge gaps** | Invisible | Lint operation detects gaps, contradictions, orphan pages |

## 11 operations

### Book operations

| Tool | What it does |
|------|-------------|
| `ingest_source` | Process a document—LLM extracts entities/concepts, creates/updates pages, maintains cross-references |
| `ingest_skill` | Process a multi-file agent skill—all files analyzed together, extracted as interlinked pages |
| `ingest_from_url` | Fetch a skill or document from a URL (GitHub repos, direct files) and auto-ingest |
| `query_book` | Search relevant pages, synthesize answer with citations, optionally save as new page |
| `lint_book` | Health-check for contradictions, stale claims, orphan pages, missing cross-references, knowledge gaps |

### Page management

| Tool | What it does |
|------|-------------|
| `list_pages` | List all pages with metadata (title, category, scope, last updated, source count) |
| `read_page` | Read full content and metadata of a specific page |
| `write_page` | Create or update a page with Markdown content |
| `delete_page` | Soft-delete a page (recoverable) |
| `promote_page` | Copy a page from your personal book to the shared org book |

## Three ways to ingest knowledge

### Single source

Feed in articles, meeting notes, API docs, papers—one document at a time. The LLM reads it, extracts key information, creates or updates relevant pages, and maintains cross-references.

```json
POST /api/book/ingest?scope=org
{
    "title": "Rubberducking with LLMs",
    "content": "Rubber duck debugging is a method where...",
    "sourceUrl": "https://deepgram.com/learn/llms-the-rubber-duck-debugger",
    "category": "article"
}
```

### Multi-file skill

Ingest an entire agent skill—instruction files, templates, and examples processed together. The LLM understands the relationships between files and extracts richer cross-references than individual ingestion.

```json
POST /api/book/ingest-skill?scope=org
{
    "skillName": "mcp-connector",
    "files": [
        {"path": "SKILL.md", "content": "# MCP Connector for Copilot Studio..."},
        {"path": "template/script.csx", "content": "public class Script : ScriptBase..."},
        {"path": "template/apiDefinition.swagger.json", "content": "{\"swagger\":\"2.0\",...}"}
    ]
}
```

### URL-based fetch

Point the compendium at a URL and it fetches the content automatically. GitHub repository tree URLs download all Markdown, code, JSON, and YAML files in the directory.

```json
POST /api/book/ingest-from-url?scope=org
{
    "url": "https://github.com/troystaylor/SharingIsCaring/tree/main/.github/skills/mcp-connector",
    "type": "agent-skill"
}
```

## The ingestion pipeline

Regardless of which option you use, the LLM processing pipeline is the same:

1. **Read** — The LLM reads the source content and the current book index
2. **Plan** — It determines what pages to create (entities, concepts, source summaries) and what existing pages to update
3. **Write** — New pages are created and existing pages are updated with new information
4. **Cross-reference** — Pages link to each other using `[[page-id]]` syntax
5. **Index** — All new/updated pages are indexed in Azure AI Search
6. **Log** — A chronological entry is appended to the book's activity log

## Scoping: personal and org books

Every operation accepts a `scope` parameter:

- **org** (default) — shared organizational book
- **personal** — your private book (keyed to your Entra ID)
- **all** — search across both (query and list only)

The `promote_page` tool copies a page from your personal book to the org book—useful when you've curated something worth sharing with the team.

## Page categories

| Category | What it represents | Example |
|----------|--------------------|---------|
| entity | A specific thing (person, product, API, service) | "Azure Container Apps", "Salesforce OAuth" |
| concept | An idea, pattern, or principle | "Token refresh patterns", "Rubberducking" |
| source | Summary of an ingested source document | "Karpathy LLM Wiki (2026-04)" |
| comparison | Side-by-side analysis of alternatives | "Blob Storage vs SharePoint Embedded" |
| overview | High-level synthesis across multiple pages | "Authentication patterns overview" |

## Lint: knowledge base health checks

The `lint_book` tool runs a health check across the entire compendium—detecting contradictions between pages, stale claims, orphan pages with no cross-references, missing cross-references, and knowledge gaps. Think of it as a linter for your organizational knowledge.

## Architecture

```
M365 Copilot / VS Code / Claude Desktop
    ↓ (MCP, native)
                                        Azure Container App
Copilot Studio / Power Automate             ↓
    ↓ (MCP via connector)              ASP.NET Core API
    Power Compendium Connector ──→          ├── BookService
                                            ├── BookStorageService (Azure Blob)
                                            ├── BookSearchService (Azure AI Search)
                                            ├── BookLlmService (Azure OpenAI)
                                            └── EasyAuth (Entra ID OAuth v2)
```

### Azure resources

| Resource | Purpose |
|----------|---------|
| Azure Container App | Hosts the ASP.NET Core API |
| Azure Blob Storage | Stores pages as JSON, sources, and activity logs |
| Azure AI Search | Indexes pages for query operations (RBAC auth) |
| Azure OpenAI | LLM processing for ingest, query, and lint (gpt-4.1-mini) |
| Azure Container Registry | Stores Docker images |
| Entra ID App Registration | OAuth v2 authentication for all consumers |

## Use cases

**Organizational knowledge base**: Ingest internal documentation, architecture decisions, runbooks, and tribal knowledge. Teams query the compendium through a Copilot Studio agent instead of searching SharePoint or asking the person who "just knows."

**Agent skill library**: Use `ingest_skill` and `ingest_from_url` to build a searchable compendium of all your agent skills—instructions, templates, and patterns. New team members ask the agent "how do we build an MCP connector?" and get a synthesized answer with cross-references to related skills.

**Continuous learning agent**: A Power Automate flow triggers `ingest_source` whenever a new document lands in a SharePoint library. The compendium grows automatically, and the `lint_book` tool flags when new information contradicts existing pages.

**Personal research assistant**: Use the personal scope to build your own knowledge base. Ingest articles, papers, and notes. Query your compendium for synthesized answers with citations. Promote useful pages to the org book when they're ready.

## Security

- EasyAuth validates Entra ID tokens before requests reach application code
- Managed Identity for all Azure service access (Blob, Search, OpenAI)—no keys stored
- Input validation—pageId allowlist (kebab-case only), content size limits (100 KB), question limits (1 KB)
- Rate limiting—30 requests/minute per user on LLM-bound endpoints
- Log sanitization—user-provided content stripped of Markdown injection before logging

## Deployment

### Deploy the Azure infrastructure

```powershell
.\infra\deploy.ps1 `
    -ResourceGroup rg-power-compendium `
    -OpenAiResourceGroup myResourceGroup `
    -OpenAiAccountName my-openai-resource `
    -OpenAiDeploymentName gpt-4o
```

The deploy script provisions all Azure resources (Storage, AI Search, ACR, Container Apps), builds and pushes the container image, assigns RBAC, and verifies the deployment.

### Deploy the connector

```powershell
pac connector create `
    --api-def connector/apiDefinition.swagger.json `
    --api-prop connector/apiProperties.json `
    --script connector/script.csx
```

Sign in with your Entra ID account when creating a connection. No additional configuration needed.

## Resources

- [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Azure AI Search documentation](https://learn.microsoft.com/en-us/azure/search/)
- [Azure OpenAI documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Full source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Compendium)
