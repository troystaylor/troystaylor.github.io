---
layout: post
title: "Salesforce MCP connector for Power Platform"
date: 2026-02-13 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Salesforce, MCP, Custom Connectors, Power Platform, Copilot Studio, CRM, SOQL, Chatter, Analytics]
description: "Comprehensive Power Platform custom connector for Salesforce REST API v66.0 with 40+ operations, dynamic sObject schema, MCP tools for Copilot Studio, and Application Insights telemetry."
---

Salesforce has one of the most complete CRM APIs available. Core REST API for SOQL queries and record CRUD, Composite API for batching operations, Reports & Dashboards API for analytics, and Chatter/Connect API for social collaboration. This connector wraps 40+ operations across 6 Salesforce API categories into a single Power Platform custom connector with dynamic sObject schema, MCP tools for Copilot Studio agents, and Application Insights telemetry.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20MCP).

## What's included

### Query API (3 operations)

Execute SOQL queries, get paginated results with QueryMore, and run SOSL full-text searches. SOQL gives you SQL-like syntax for querying Salesforce objects, while SOSL searches across multiple objects simultaneously.

### Records API (5 operations)

List, get, create, update, and delete records from any sObject. The connector includes **dynamic sObject schema**—when you select an object like Account or Opportunity in Power Automate, the body fields auto-populate with the actual fields from that object by querying Salesforce's describe endpoint.

### Metadata API (3 operations)

DescribeGlobal lists all sObjects in your org. DescribeObject returns field metadata for a specific object. GetLimits shows your API usage against daily limits.

### Composite API (4 operations)

| Operation | What it does |
|-----------|--------------|
| Composite | Execute multiple operations with cross-references between requests |
| CompositeBatch | Execute up to 25 independent requests in a single call |
| CompositeTree | Create parent-child record hierarchies |
| CompositeGraph | Complex multi-graph operations with dependencies |

The Composite API is essential for reducing API calls. Instead of creating an Account, then a Contact, then an Opportunity in three separate calls, you can do it in one request with references between the records.

### Analytics API (6 operations)

List and get reports, run reports with optional filters, list and get dashboards, and refresh dashboard components. Pull report data directly into Power Automate flows without screen scraping.

### Chatter API (11 operations)

Full social collaboration: get feeds, post feed elements, like and comment, get user profiles, list and search users and groups, join groups, and list topics. Build notification flows that post to Chatter when important events happen in Power Platform.

## Dynamic sObject schema

One of the most useful features. When you use CreateRecord or UpdateRecord in Power Automate:

1. Select an sObject (for example, `Account`, `Lead`, or `Opportunity`).
2. The connector calls Salesforce's describe endpoint for that object.
3. Body parameters show object-specific fields with proper labels and types.

No more guessing field API names or checking Salesforce Object Manager mid-flow.

## MCP tools for Copilot Studio

The connector exposes 15 MCP tools via JSON-RPC 2.0:

| Tool | Description |
|------|-------------|
| `query` | Execute SOQL queries |
| `search` | Execute SOSL searches |
| `get_record` | Get record by ID |
| `create_record` | Create new record |
| `update_record` | Update existing record |
| `delete_record` | Delete record |
| `list_objects` | List available sObjects |
| `describe_object` | Get object metadata |
| `get_limits` | Check API limits |
| `list_reports` | List reports |
| `run_report` | Execute report |
| `list_dashboards` | List dashboards |
| `post_to_chatter` | Post to Chatter |
| `get_chatter_feed` | Get feed elements |
| `composite` | Execute multiple operations |

### MCP resources

The connector also provides reference documentation that agents can read:

| Resource URI | Description |
|--------------|-------------|
| `salesforce://reference/soql` | Comprehensive SOQL guide with syntax, operators, date literals, aggregate functions, relationship queries, and common objects |

The SOQL reference helps agents construct valid queries without trial and error—complete operator reference, all date literals (TODAY, LAST_N_DAYS, THIS_MONTH), aggregate functions with GROUP BY/HAVING, and relationship query syntax.

Add the connector as an action in Copilot Studio, and the agent discovers the tools automatically. Users can then interact with Salesforce through natural conversation:

**User:** "Show me all accounts in the technology industry with annual revenue over $1 million"
**Agent:** *Calls `query` with the SOQL*

**User:** "Create a new lead for John Smith at Contoso, email john@contoso.com"
**Agent:** *Calls `create_record` with Lead object and fields*

**User:** "What opportunities are closing this month?"
**Agent:** *Calls `query` with CloseDate = THIS_MONTH*

## Setup

### Salesforce prerequisites

- **Salesforce Edition** with API access (Enterprise, Unlimited, Developer, or Performance)
- **My Domain** enabled (required for OAuth)
- **API Enabled** permission for the connecting user

### Create Connected App

Salesforce offers two options. As of Spring '26, External Client Apps are recommended for new integrations.

#### Option 1: External Client App (recommended)

1. Navigate to **Setup → Platform Tools → Apps → External Client App Manager**.
2. Click **New External Client App**.
3. Configure:
   - **Name:** Power Platform Connector
   - **Contact Email:** Your email
   - **Enable OAuth Settings:** Checked
   - **Callback URL:** `https://global.consent.azure-apim.net/redirect`
   - **Selected OAuth Scopes:**
     - Access the identity URL service (id, profile, email, address, phone)
     - Manage user data via APIs (api)
     - Perform requests at any time (refresh_token, offline_access)
4. Save and copy the Consumer Key and Consumer Secret.

#### Option 2: Connected App (legacy)

1. Navigate to **Setup → Platform Tools → Apps → App Manager**.
2. Click **New Connected App**.
3. Configure:
   - **Connected App Name:** Power Platform Connector
   - **API Name:** Power_Platform_Connector
   - **Contact Email:** Your email
   - **Enable OAuth Settings:** Checked
   - **Callback URL:** `https://global.consent.azure-apim.net/redirect`
   - **Selected OAuth Scopes:** Same as above
4. Save and wait 2-10 minutes for propagation.
5. Copy the Consumer Key and Consumer Secret.

### Import the connector

1. Go to [Power Automate](https://make.powerautomate.com/) or [Power Apps](https://make.powerapps.com/) → Custom connectors.
2. Import from OpenAPI file: upload `apiDefinition.swagger.json`.
3. Update OAuth settings with your Consumer Key and Secret.
4. Create a connection—you'll be prompted for your Salesforce Instance (My Domain name, for example `mycompany` for `mycompany.my.salesforce.com`).

Or use PAC CLI:

```bash
pac connector create --api-definition apiDefinition.swagger.json --api-properties apiProperties.json
```

## SOQL query reference

Salesforce Object Query Language (SOQL) syntax:

| Clause | Example |
|--------|---------|
| SELECT | `SELECT Id, Name, Industry` |
| FROM | `FROM Account` |
| WHERE | `WHERE Industry = 'Technology'` |
| AND/OR | `WHERE Industry = 'Technology' AND AnnualRevenue > 1000000` |
| IN | `WHERE Industry IN ('Technology', 'Finance')` |
| LIKE | `WHERE Name LIKE 'Acme%'` |
| ORDER BY | `ORDER BY CreatedDate DESC` |
| LIMIT | `LIMIT 100` |
| OFFSET | `OFFSET 10` |

### Common SOQL examples

```sql
-- Get accounts in technology industry
SELECT Id, Name, Industry FROM Account WHERE Industry = 'Technology' LIMIT 10

-- Get contacts with email
SELECT Id, FirstName, LastName, Email FROM Contact WHERE Email != null

-- Get opportunities closing this month
SELECT Id, Name, Amount, CloseDate FROM Opportunity WHERE CloseDate = THIS_MONTH

-- Get accounts with related contacts
SELECT Id, Name, (SELECT Id, Name FROM Contacts) FROM Account LIMIT 5
```

## Examples

### Create an Account

```json
{
  "Name": "Acme Corporation",
  "Industry": "Technology",
  "Website": "https://acme.com",
  "Phone": "555-1234"
}
```

### Update a Contact

```json
{
  "Phone": "555-5678",
  "Title": "VP of Sales"
}
```

### Execute Composite request

Create an Account and then a related Contact in one call:

```json
{
  "allOrNone": true,
  "compositeRequest": [
    {
      "method": "POST",
      "url": "/services/data/v66.0/sobjects/Account",
      "referenceId": "newAccount",
      "body": {
        "Name": "New Account"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v66.0/sobjects/Contact",
      "referenceId": "newContact",
      "body": {
        "LastName": "Smith",
        "AccountId": "@{newAccount.id}"
      }
    }
  ]
}
```

### Run a Report with filters

```json
{
  "reportMetadata": {
    "reportFilters": [
      {
        "column": "ACCOUNT.INDUSTRY",
        "operator": "equals",
        "value": "Technology"
      }
    ]
  }
}
```

### Post to Chatter

```json
{
  "body": {
    "messageSegments": [
      {
        "type": "Text",
        "text": "Check out this new opportunity!"
      }
    ]
  },
  "feedElementType": "FeedItem",
  "subjectId": "005XXXXXXXXXXXX"
}
```

## Application Insights (optional)

Update the connection string in `script.csx`:

```csharp
private const string APP_INSIGHTS_CONNECTION_STRING = "InstrumentationKey=xxx;IngestionEndpoint=https://xxx.in.applicationinsights.azure.com/";
```

Events logged: `RequestReceived`, `RequestCompleted`, `RequestError`, `MCPRequest`, `MCPToolCall`, `MCPToolError`.

## Common sObjects

| Object | API Name | Description |
|--------|----------|-------------|
| Account | `Account` | Business accounts |
| Contact | `Contact` | Individual contacts |
| Lead | `Lead` | Sales leads |
| Opportunity | `Opportunity` | Sales opportunities |
| Case | `Case` | Support cases |
| Task | `Task` | Activities/tasks |
| Event | `Event` | Calendar events |
| User | `User` | Salesforce users |
| Campaign | `Campaign` | Marketing campaigns |
| Product | `Product2` | Products |
| Price Book | `Pricebook2` | Price books |
| Order | `Order` | Orders |

## Try it yourself

The complete connector code is available in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20MCP):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Salesforce%20MCP/apiDefinition.swagger.json) — OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Salesforce%20MCP/script.csx) — Connector script with MCP and dynamic schema
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Salesforce%20MCP/apiProperties.json) — Connector metadata
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Salesforce%20MCP/readme.md) — Full documentation

## Resources

- [Salesforce REST API documentation](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/)
- [SOQL and SOSL reference](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/)
- [Chatter REST API](https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/)
- [Reports and Dashboards API](https://developer.salesforce.com/docs/atlas.en-us.api_analytics.meta/api_analytics/)
- [Official Power Platform connector for Salesforce](https://learn.microsoft.com/en-us/connectors/salesforce/)
- [Application Insights telemetry for connectors](https://troystaylor.github.io/power%20platform/2026/01/07/power-platform-custom-connectors-application-insights.html)
