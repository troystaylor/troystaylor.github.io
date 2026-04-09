---
layout: post
title: "Salesforce Client Credentials MCP connector for Power Platform"
date: 2026-04-09 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Salesforce, MCP, Copilot Studio, Custom Connectors, Power Platform, CRM, Service Cloud, Knowledge Management, OAuth]
description: "Power Platform custom connector for Salesforce Cloud using OAuth 2.0 client_credentials flow—35 MCP tools and 40+ REST operations covering SOQL, sObject CRUD, Composite API, Reports, Chatter, Knowledge, Case Management, and search synonyms."
---

Power Platform already has a Salesforce connector. It uses interactive OAuth—each user signs in with their Salesforce credentials. But right now it OAuth refresh token is currently broken, so your connections will fail after 2-12 hours.

This MCP connector uses the OAuth 2.0 `client_credentials` grant flow instead. A Salesforce Connected App authenticates with Client ID and Client Secret so all tools and operations are performed under the identity of a "Run As" user configured in the Connected App. No interactive login, no refresh tokens, no session management.

Otherwise, this connector is pretty much the same as my other custom Salesforce connector.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20Client%20Credentials)

## How authentication works

1. Power Platform sends Client ID and Client Secret as Basic Authentication (`Authorization: Basic base64(client_id:client_secret)`)
2. The script forwards the auth header to `https://{instanceUrl}/services/oauth2/token` with `grant_type=client_credentials`—[Salesforce natively accepts this format](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_client_credentials_flow.htm&type=5)
3. Salesforce returns an access token and canonical `instance_url`
4. The script uses the `instance_url` from the token response (not the connection parameter) for API calls, ensuring correct routing even if Salesforce redirects
5. Subsequent calls use `Authorization: Bearer {token}`

The token and instance URL are cached within a single request execution to avoid redundant token calls during MCP tool chains.

## Operations by category

### Query

| Operation | Description |
|-----------|-------------|
| Execute SOQL Query | Run SOQL queries against any object |
| Get More Query Results | Paginate through large result sets |
| Execute SOSL Search | Full-text search across objects |

### Records

| Operation | Description |
|-----------|-------------|
| Create Record | Create records in any sObject (dynamic schema) |
| Get Record | Retrieve a single record by ID |
| Update Record | Update record fields (dynamic schema) |
| Delete Record | Delete a record |

The Create and Update operations use `x-ms-dynamic-schema` to populate field lists based on the selected sObject. Pick "Account" and the connector fetches Account fields. Pick "Contact" and you see Contact fields.

### Composite API

| Operation | Description |
|-----------|-------------|
| Composite | Multiple operations with references between requests |
| Composite Batch | Up to 25 independent subrequests |
| Composite Tree | Create parent + child records in one call |
| Composite Graph | Dependent operations across multiple graphs |

### Analytics

| Operation | Description |
|-----------|-------------|
| List/Get/Run Reports | Report metadata and execution |
| List/Get/Refresh Dashboards | Dashboard management |

### Chatter

| Operation | Description |
|-----------|-------------|
| Get Feed / Post Feed Element | Social feeds |
| Get/Like Feed Element / Post Comment | Engagement |
| Get/List Users / Groups | User and group management |
| Join Group / List Topics | Community features |

### Knowledge

| Operation | Description |
|-----------|-------------|
| List / Get / Create / Update / Delete Articles | Full article lifecycle |
| Search Suggestions | AI-powered article search |
| Suggest Title Matches | Title-based article matching |

### Case Management

| Operation | Description |
|-----------|-------------|
| Create / Get / Update Case | Full case lifecycle |
| Add Case Comment | Internal or published comments |
| Case Timeline | Comments, emails, and feed items via Composite API |
| Send Case Email | Outbound email linked to a case |
| Suggest KB for Case | Article recommendations based on case content |
| Draft KB Article from Case | Create articles from resolved cases |
| Categorize Case | Classify type, reason with internal comment |

### Reporting

| Operation | Description |
|-----------|-------------|
| Case Volume Trends | Cases grouped by type, reason, priority over time |
| Deflection Metrics | Copilot interaction outcomes with deflection rates |
| SLA Compliance | First-response analysis against SLA thresholds |

### Tooling

| Operation | Description |
|-----------|-------------|
| Tooling Query | Query Salesforce metadata |
| Synonym Group CRUD | Create, read, update, delete search synonym groups |

## MCP tools (35 tools)

The connector exposes 35 MCP tools for Copilot Studio covering all operation categories. The orchestrator can chain tools conversationally:

```
User: "Find all open cases from Zava
       that haven't been responded to in 48 hours"

1. Orchestrator calls soql_query({
     query: "SELECT Id, CaseNumber, Subject, Priority,
             CreatedDate, Status
             FROM Case
             WHERE Account.Name = 'Zava'
             AND Status != 'Closed'
             AND CreatedDate < LAST_N_DAYS:2
             ORDER BY Priority"
   })

   → Returns matching cases with details
```

```
User: "Categorize that first case as a Performance problem
       and suggest KB articles"

2. Orchestrator calls categorize_case({
     case_id: "500xx...",
     type: "Problem",
     reason: "Performance",
     internal_comments: "Customer reports slow load times
                         in dashboard view"
   })

3. Orchestrator calls suggest_kb_for_case({
     case_id: "500xx..."
   })

   → Returns relevant Knowledge articles
```

```
User: "Draft a KB article from the resolution"

4. Orchestrator calls draft_kb_article({
     case_id: "500xx...",
     title: "Resolving dashboard performance issues",
     url_name: "dashboard-performance-fix",
     content: "Steps to resolve..."
   })
```

## Use cases

**Service Cloud agent**: Build a Copilot Studio agent that handles case triage, Knowledge article lookup, categorization, and KB article drafting. The case management operations cover the full support lifecycle without opening the Salesforce console.

**Server-to-server sync**: Use the `client_credentials` flow for scheduled Power Automate flows that sync Salesforce records with Dataverse, SharePoint, or other systems. No interactive login required—the Connected App authenticates automatically.

**Composite operations**: Use the Composite API to create an Account with related Contacts and Opportunities in a single request. The Graph operation handles complex dependency chains across multiple objects.

**Support analytics**: Run deflection metrics, SLA compliance checks, and case volume trend reports from Power Automate. Feed the results into Power BI dashboards or Teams notifications.

**Knowledge management**: Search, create, update, and publish Knowledge articles from a Copilot Studio agent. Use search suggestions for AI-powered article discovery and title matching.

## Prerequisites

### Salesforce Connected App setup

1. In Salesforce Setup, go to **App Manager** and create a new Connected App
2. Enable **OAuth Settings**
3. Set the Callback URL to `https://global.consent.azure-apim.net/redirect` (not used by client_credentials but required by Salesforce)
4. Select the OAuth scope: **api** (Access and manage your data)
5. Enable **Client Credentials Flow**:
   - Under the Connected App settings, go to **Manage** > **Edit Policies**
   - Set **Permitted Users** to "Admin approved users are pre-authorized"
   - Under **Client Credentials Flow**, assign a **Run As** user—this is the user identity all API calls execute as
6. Note the **Consumer Key** (Client ID) and **Consumer Secret** (Client Secret)

The "Run As" user must have a Salesforce license that supports API access and appropriate permissions for the operations you intend to use.

## Connection parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| Client ID | Consumer Key from the Connected App | `3MVG9...` |
| Client Secret | Consumer Secret from the Connected App | `ABC123...` |
| Instance URL | Your Salesforce My Domain (without `https://`) | `myorg.my.salesforce.com` |

## Setting up the connector

1. Go to [Power Platform Maker Portal](https://make.powerapps.com/)
2. Navigate to **Custom connectors** > **+ New custom connector** > **Import an OpenAPI file**
3. Upload `apiDefinition.swagger.json`
4. On the **Code** tab:
   - Enable **Code**
   - Upload `script.csx`
5. Select **Create connector**
6. Create a connection with your **Client ID**, **Client Secret**, and **Instance URL**
7. Test with `DescribeGlobal` to verify the connection returns your Salesforce objects

### Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "Query all open cases" or "Search for Knowledge articles about performance"

## Known limitations

- Each API request acquires a new OAuth token (no token caching across requests—cached within a single request only)
- The `client_credentials` flow requires Salesforce API version 51.0+ and a properly configured Connected App
- The "Run As" user must have a Salesforce license that supports API access
- All operations execute under the "Run As" user's permissions—no per-user delegation
- No support for refresh tokens (by design—`client_credentials` doesn't use them)

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 40+ REST operations with dynamic schema |
| `apiProperties.json` | Basic auth config (Client ID/Secret as Basic) and script operation bindings |
| `script.csx` | C# script handling token acquisition, instance URL resolution, MCP protocol, and all operation routing |
| `readme.md` | Setup and usage documentation |

## Resources

- [Salesforce Client Credentials connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20Client%20Credentials)
- [Salesforce OAuth 2.0 Client Credentials Flow](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_client_credentials_flow.htm&type=5)
- [Salesforce REST API Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/)
- [Salesforce Composite API](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite.htm)
- [Salesforce Knowledge REST API](https://developer.salesforce.com/docs/atlas.en-us.knowledge_dev.meta/knowledge_dev/)
