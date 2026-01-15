---
title: "SharePoint Term Store Connector: Managed Metadata for Power Automate"
author: Troy Taylor
date: 2026-01-15
category: Power Platform
layout: post
tags: [Power Platform, Power Automate, SharePoint, Custom Connectors, Graph API, Taxonomy, MCP, Copilot Studio]
---

Ever tried to automate managed metadata in Power Automate? The standard SharePoint connector lets you create list items, but working with the term store—the taxonomy behind those managed metadata columns—requires custom Graph API calls. And that can be a lot of HTTP actions.

This connector fixes that. The **SharePoint Term Store Connector** wraps the Microsoft Graph term store API into simple Power Automate actions. List term groups, create term sets, build hierarchical taxonomies—all without writing Graph queries. And for Copilot Studio users, the connector includes MCP support for natural language taxonomy management.

## Why automate the term store?

Managed metadata columns are powerful, but the taxonomy behind them is locked away in the term store admin UI. Common automation scenarios include:

- **Taxonomy sync**: Keep term stores consistent across dev, test, and production environments
- **Bulk updates**: Add hundreds of terms from a spreadsheet or external system
- **Dynamic classification**: Look up valid terms before tagging documents in flows
- **Governance workflows**: Route approval requests when new terms are created
- **Onboarding automation**: Spin up department-specific term groups when new teams are created

The Graph API supports all of this, but building raw HTTP requests in Power Automate is tedious. This connector gives you proper actions with typed inputs and outputs.

## Common use cases

### Building content taxonomies

Create hierarchical term structures for document classification:

1. Create a term group for "Document Types"
2. Add term sets like "Contracts," "Reports," "Proposals"
3. Build nested terms (Contracts → Legal Contracts → NDAs)

### Metadata-driven search

Enable faceted search and filtering:

1. Apply terms to documents and list items
2. Users filter by term sets (Department, Location, Status)
3. Search results grouped by taxonomy

### Governance and consistency

Centrally manage organizational vocabulary:

1. Define approved terms in the term store
2. Prevent ad-hoc metadata creation
3. Maintain consistent tagging across sites

### Onboarding automation

When new projects or departments spin up:

1. Agent creates appropriate term groups and sets
2. Inherits from global taxonomy templates
3. Site columns automatically pick up new terms

## What's in the connector

The connector exposes **12 actions** for complete taxonomy management:

| Action | Purpose |
|--------|---------|
| `get_term_store` | Retrieve term store configuration and available languages |
| `list_term_groups` | List all taxonomy groups (Departments, Locations, etc.) |
| `create_term_group` | Create a new term group |
| `list_term_sets` | Get term sets within a group |
| `create_term_set` | Create a new term set with localized names |
| `list_terms` | List root-level terms in a set |
| `create_term` | Add a term with multilingual labels |
| `list_child_terms` | Navigate hierarchical term structures |
| `create_child_term` | Build nested taxonomy hierarchies |
| `update_term` | Modify term labels, descriptions, or properties |
| `delete_term` | Remove a term (cascades to children) |
| `get_term` | Get details of a specific term |

Each action maps directly to Graph API operations but handles authentication, URL construction, and response parsing for you.

## Term store hierarchy

For those unfamiliar with SharePoint taxonomy, here's the structure:

```
Term Store (site-level or tenant-level)
└── Term Groups (organizational containers)
    └── Term Sets (collections of related terms)
        └── Terms (the actual metadata values)
            └── Child Terms (hierarchical nesting, up to 7 levels)
```

A practical example:

```
Term Store
└── Corporate Taxonomy (Term Group)
    ├── Departments (Term Set)
    │   ├── Engineering
    │   │   ├── Software Engineering
    │   │   └── Hardware Engineering
    │   ├── Sales
    │   └── Marketing
    └── Document Types (Term Set)
        ├── Contracts
        │   ├── NDAs
        │   └── Service Agreements
        └── Reports
```

## Example: Building a document taxonomy

One of the more useful capabilities is building nested taxonomies programmatically. Here's a typical flow pattern:

**Step 1: Create the parent term**

Use the `create_term` action with:
- **siteId**: `root` (or your specific site ID)
- **setId**: The term set GUID from `list_term_sets`
- **label**: `Contracts`
- **languageTag**: `en-US`
- **description**: `Legal and business contracts`

**Step 2: Add child terms**

Loop through your source data and call `create_child_term` for each:
- **siteId**: `root`
- **setId**: Same term set GUID
- **termId**: The parent term ID from step 1
- **label**: `Non-Disclosure Agreements`
- **languageTag**: `en-US`

**Pro tip**: Store the term IDs returned from each create action—you'll need them for nested hierarchies or to update terms later.

## Multilingual support

Enterprise deployments often require terms in multiple languages. The connector supports multilingual labels through the `languageTag` parameter on create and update actions:

1. Create the term with your default language (e.g., `en-US`)
2. Call `update_term` with additional language tags (`fr-FR`, `de-DE`, etc.)
3. Users see terms in their preferred language based on SharePoint settings

This is especially useful for global organizations syncing taxonomy from a master list that includes translations.

## Copilot Studio integration

The connector also supports MCP (Model Context Protocol) for Copilot Studio agents. Add it as an action, and agents can interact with the term store using natural language:

- "List all term groups in the root site"
- "Create a new term called 'Acquisition Documents' under Contracts"
- "What terms are available in the Departments term set?"

The `/mcp` endpoint implements MCP Streamable 1.0, so Copilot Studio automatically discovers all 12 tools and their input schemas.

## Application Insights telemetry

The connector includes optional Application Insights logging. Track which actions your flows use most, monitor for Graph API errors, and identify taxonomy patterns across your organization. Set the connection string in `apiProperties.json` during deployment.

## Setup and permissions

### Prerequisites

1. SharePoint site with term store enabled
2. Microsoft 365 account with appropriate permissions
3. Azure AD app registration with Graph API permissions

### Required permissions

The connector requires these Microsoft Graph permissions:

| Permission | Purpose |
|------------|---------|
| `TermStore.Read.All` | Read term store data |
| `TermStore.ReadWrite.All` | Create and modify terms |
| `Sites.Read.All` | Access SharePoint sites |
| `Sites.ReadWrite.All` | Full site access (for some operations) |

### Deployment

1. Import via Power Platform maker portal → Custom connectors → Import OpenAPI
2. Upload `apiDefinition.swagger.json`
3. Enable custom code in the "Code" tab
4. Paste contents of `script.csx`
5. Configure OAuth 2.0 security with your Azure AD app registration
6. Create connection and test

### Power Automate usage

1. Add a new action in your flow
2. Search for "SharePoint Term Store"
3. Select the action you need (e.g., `list_term_groups`)
4. Provide the site ID and any required parameters

## Known limitations

A few things to keep in mind:

- **Elevated permissions**: Term store operations require more permissions than typical SharePoint access
- **Cascading deletes**: Deleting parent terms removes all children
- **Hierarchy depth**: Maximum 7 levels of nested terms
- **Scope boundaries**: Site-scoped term groups only accessible within that site collection
- **Tenant admin**: Global term groups require tenant administrator permissions

## Try it yourself

The complete connector is available in my [SharingIsCaring](https://github.com/troystaylor/SharingIsCaring/tree/main/SharePoint%20Term%20Store) repository:

- `apiDefinition.swagger.json` — OpenAPI 2.0 with MCP endpoint
- `apiProperties.json` — Connector metadata and OAuth configuration
- `script.csx` — C# implementation with MCP protocol handling
- `readme.md` — Full documentation

## What's next

With the term store connector, Power Automate can finally participate in taxonomy management. Some ideas I'm exploring:

- **Environment sync**: Flow that exports terms from production and imports to dev/test
- **Excel import**: Bulk create terms from a spreadsheet with nested hierarchy columns
- **Cross-system sync**: Keep Dataverse option sets and SharePoint term stores aligned
- **Governance dashboard**: Track term usage and flag orphaned or duplicate terms

The combination of this connector with document management actions enables end-to-end classification workflows—upload a document, look up valid terms, apply metadata, all in a single flow.

## Related connectors

- [Graph Hashes MCP](https://troystaylor.com/power%20platform/2026-01-13-graph-hashes-mcp-connector.html) — File integrity and deduplication

## Resources

- [Microsoft Graph termStore API Reference](https://learn.microsoft.com/graph/api/resources/termstore-store)
- [SharePoint Taxonomy Documentation](https://learn.microsoft.com/sharepoint/managed-metadata)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Power Platform Custom Connectors](https://learn.microsoft.com/connectors/custom-connectors/)

---

Managed metadata is the backbone of enterprise content organization, but it's been stuck in manual admin mode for too long. This connector brings taxonomy management into Power Automate where it belongs. What would you automate first?

Connect with me on [LinkedIn](https://www.linkedin.com/in/introtroytaylor/) or check out more connectors on [GitHub](https://github.com/troystaylor/SharingIsCaring)!
