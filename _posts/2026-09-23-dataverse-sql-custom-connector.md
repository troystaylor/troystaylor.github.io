---
layout: post
title: "Dataverse SQL queries from Power Automate and Copilot Studio"
date: 2026-09-23 09:00:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Dataverse, SQL, Custom Connectors, MCP, Copilot Studio, Power Automate, OAuth]
description: "Dataverse SQL is a Power Platform custom connector that wraps the Dataverse Web API sql query option with typed actions, design-time column resolution, auto-paging, and an MCP endpoint for Copilot Studio agents."
---

The Dataverse Web API accepts a read-only T-SQL subset through the [`sql` query option](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/query/sql). [Dataverse SQL](https://github.com/troystaylor/SharingIsCaring/tree/main/Dataverse%20SQL) puts a usable surface on it: typed actions for flows and apps, and an MCP endpoint that gives a Copilot Studio agent discovery tools so it writes SQL against columns it has confirmed exist.

## Two rough edges the connector absorbs

Calling the `sql` option directly means dealing with both of these yourself.

**The entity set in the URL must match the base table of the query.** A query beginning `FROM account` has to go to `/accounts`, and `FROM msdyn_botsession` to `/msdyn_botsessions`. The connector reads the `FROM` clause, resolves the entity set from table metadata, and builds the URL. You write the table name and never the entity set.

**The supported subset is narrow, and a rejected statement returns a raw fault.** Every statement is checked locally first. Anything unsupported comes back as a named issue — `select_star`, `having`, `unsupported_join` — describing what to write instead, with no round trip to Dataverse.

Everything is read-only. A statement must be a single `SELECT`, and write keywords are rejected before the request is built.

## Seven visible operations

| Operation | Purpose |
|---|---|
| Execute SQL | Run a `SELECT` and return rows, with a next link when more are available |
| Get next page | Follow the next link from a previous result |
| Count rows | `COUNT(*)` against a table, with an optional filter |
| Validate SQL | Check a statement and resolve its base table without running it |
| List tables | Table logical names, entity set names, and display names |
| List columns | Columns of one table, for building a `SELECT` list |
| Invoke Dataverse SQL MCP | JSON-RPC 2.0 endpoint for Copilot Studio |

An eighth operation, **Get row schema**, is marked internal and backs the dynamic content below.

**Execute SQL** takes the statement, a page size, an optional row budget, and a switch for formatted values. Formatted values add display text for choice, lookup, and date columns as `@OData.Community.Display.V1.FormattedValue` annotations next to the raw values.

## Column names come from a sample row, not a prediction

The designer resolves the columns your statement returns and offers them as typed dynamic content, so you pick `name` or `revenue` directly instead of writing `item()?['name']`. Types come from Dataverse metadata for whichever table each alias refers to, so in a join `c.birthdate` is typed from `contact` rather than the base table. Aggregates are typed from their function: `COUNT(*)` is a whole number, `SUM()` a decimal, and `MIN()`/`MAX()` inherit the type of the column they wrap.

Two behaviors shape how that works.

Alias your aggregates. Dataverse names an aggregate column after its alias, so `SELECT COUNT(*) AS total` produces a `total` field while a bare `SELECT COUNT(*)` produces a field this connector cannot name and therefore omits.

Dataverse also decides what comes back, not your `SELECT` list. A plain query returns the primary key and `@odata.etag` on top of what you asked for, and some tables add more — `systemuser` and `team` return `ownerid` unselected, while `queue` and `role` do not. An aggregate query returns *only* its aliased columns. That pattern isn't derivable from metadata, so the connector runs your statement once for a single row at design time and reads the real column names:

```csharp
var sampled = await SampleRowAsync(table, validation.Statement).ConfigureAwait(false);
```

An empty table has no row to inspect, so the schema falls back to the `SELECT` list plus the primary key and etag, and the response reports `sampled: false`.

Resolution happens at design time against the statement in the box. Build the statement from an expression and there's nothing to inspect yet, so `rows` stays untyped. The action still runs normally.

## Six tools for an agent

Add the connector as a tool in Copilot Studio and the MCP endpoint exposes:

| Tool | Purpose |
|---|---|
| `list_tables` | Find the logical name for a `FROM` clause |
| `describe_table` | Confirm column names and types before writing a `SELECT` |
| `validate_sql` | Check a statement without running it |
| `run_sql` | Execute and return rows, optionally collecting several pages |
| `next_page` | Continue a paged result |
| `count_rows` | Count rows, optionally filtered |

The tool descriptions carry the supported subset, so an agent generally writes a valid statement on the first attempt. When it doesn't, failures come back as tool results rather than protocol errors, and the agent reads the issues and valid values and retries instead of stalling. An unknown table name returns near matches from your environment.

The intended path is `list_tables` → `describe_table` → `run_sql`. An agent that skips discovery and guesses column names gets corrected by `unknown_column`, but those round trips are avoidable.

## What the subset covers

| Feature | Supported |
|---|---|
| Select | `SELECT`, `SELECT DISTINCT` |
| Joins | `INNER JOIN`, `LEFT JOIN`, across multiple tables |
| Filtering | `WHERE` with `=` `!=` `>` `<` `>=` `<=` `LIKE` `IN` `NOT IN` `IS NULL` `IS NOT NULL` `BETWEEN` `AND` `OR`, and nested parentheses |
| Aggregation | `GROUP BY` with `COUNT` `SUM` `AVG` `MIN` `MAX` |
| Sorting | `ORDER BY [ASC\|DESC]` over plain columns |
| Functions | `DATEADD` and `GETUTCDATE`, in `WHERE` and `ON` only |

Out of scope: `SELECT *`, subqueries, CTEs, `HAVING`, `UNION`, `RIGHT JOIN`, `FULL JOIN`, `CROSS JOIN`, `CASE`, `COALESCE`, window functions, and string, date, or math functions beyond the two above. `WHERE` cannot compare two literals or two columns, and cannot apply a function to a column value. `ORDER BY` and `GROUP BY` take columns only, including date parts, so `GROUP BY MONTH(createdon)` is rejected.

A statement that fits looks like this:

```sql
SELECT a.name, COUNT(*) AS contact_count
FROM account AS a
INNER JOIN contact AS c ON a.accountid = c.parentcustomerid
WHERE a.createdon >= DATEADD(day, -30, GETUTCDATE())
GROUP BY a.name
ORDER BY a.name
```

## Paging without a loop

Set the page size on **Execute SQL** and it becomes `Prefer: odata.maxpagesize`. When more rows exist, `hasMore` is true and `nextLink` carries the continuation — pass it to **Get next page** unchanged. Next links are checked against your environment before they're followed.

**Get next page** returns the same shape, but `sql`, `table`, and `entitySet` come back empty. A next link carries the continuation token, not the statement that produced it, so carry those values forward from the first call if you need them.

To collect several pages in one action, set **Maximum rows**. The connector follows next links itself until it has that many rows, and `stoppedBecause` reports which limit ended the run:

| `stoppedBecause` | Meaning |
|---|---|
| `complete` | No more rows exist |
| `page` | A single page was requested and more rows remain |
| `maxRows` | The row budget was reached |
| `timeBudget` | Paging stopped early to stay inside the script time limit |

The final page may carry the total slightly past **Maximum rows**, because pages are never split. Whenever paging stops with rows remaining, `nextLink` still comes back, so a flow resumes exactly where it left off. Leave **Maximum rows** at 0 for a single page.

`TOP` and `OFFSET … FETCH` are accepted but flagged with a warning. The Dataverse reference lists them as supported syntax while its paging guidance says they aren't honored. Prefer the page size, or page by filtering on the last id you saw:

```sql
SELECT name, accountid
FROM account
WHERE accountid > '00000000-0000-0000-0000-000000000000'
ORDER BY accountid
```

## Throttling that outlasts the script

Dataverse enforces [service protection limits](https://learn.microsoft.com/power-apps/developer/data-platform/api-limits) by returning `429` with a `Retry-After` header. The connector waits and retries automatically when that wait is short.

The wait scales with how demanding the previous five minutes were, so it can exceed the two minutes a connector script is allowed to run. When it does, the call returns a `throttled` error carrying `retryAfterSeconds` rather than being killed mid-wait. Handle it in a flow with a **Delay** of that many seconds followed by a retry.

Other ceilings worth knowing:

| Limit | Value | Effect |
|---|---|---|
| Script execution | 2 minutes | Bounds auto-paging and throttle retries; both stop early and hand back a next link |
| Aggregate evaluation | 50,000 records | Error `8004E023`, reported as `aggregate_limit_exceeded` |
| Page size | 5,000 rows | Values above this are clamped |
| Columns per describe | 250 | Use the search parameter on wide tables |
| Tables per list | 1,000 default, 5,000 max | Adjust with the limit parameter |

For the aggregate limit, add a filter — typically a date range or a subset of a choice column — and combine the results of several runs.

## Deploy it

Register an app in Microsoft Entra ID, add the **Dynamics CRM → user_impersonation** delegated permission, grant consent, and create a client secret. Add `https://global.consent.azure-apim.net/redirect` as a web redirect URI.

Then point the files at your environment. In `apiDefinition.swagger.json`, set `host` to your environment hostname. In `apiProperties.json`, replace `[YOUR_CLIENT_ID]` with your application ID and replace `https://org.crm.dynamics.com` in both `AzureActiveDirectoryResourceId` and `resourceUri` with your environment URL. Leave `redirectUrl` as `[YOUR_REDIRECT_URL]`, since the platform substitutes the real value at deploy time.

```powershell
pac auth create --environment <your-environment-url>

pac connector create `
  --api-definition-file apiDefinition.swagger.json `
  --api-properties-file apiProperties.json `
  --script-file script.csx
```

`pac` has no parameter for the client secret. Paste it in **Power Apps → Custom connectors → Dataverse SQL → Edit → Security**, or add it as `clientSecret` inside `oAuthSettings` in a temporary copy of `apiProperties.json`, deploy from that copy, and delete it afterwards. Never put a secret in the file you keep.

The platform generates a redirect URL unique to this connector and environment. Read it back and register it:

```powershell
pac connector download --connector-id <connector-id> --outputDirectory ./verify
```

The value sits at `properties.connectionParameters.token.oAuthSettings.redirectUrl`. It encodes the publisher prefix, the connector name, and the environment, with characters escaped — `_` becomes `-5f` and a space becomes `-20`:

```
https://global.consent.azure-apim.net/redirect/new-5fdataverse-20sql-5f<ENVIRONMENT_SUFFIX>
```

Copy the whole value exactly as downloaded rather than assembling it by hand, and add it to the app registration alongside the generic one. OAuth consent fails until it's registered, and a second environment produces a different URL that also needs registering.

Create a connection, then run **List tables** with no parameters. A list of your tables confirms auth, host, and script are all wired up.

## When something comes back wrong

| Symptom | Cause | Fix |
|---|---|---|
| `invalid_sql` with an `issues` list | The statement uses an unsupported construct | Each issue names the rule and what to write instead |
| `entity_set_in_from` | The `FROM` clause names an entity set, such as `accounts` | Use the table name, `account` |
| `unknown_table` | No such table in this environment | Use a name from **List tables**; near matches come back in `validValues` |
| `unknown_column` | A column in the `SELECT` list does not exist | Confirm names with **List columns** |
| `invalid_next_link` | The next link was edited, or came from another environment | Pass it back exactly as returned |
| No dynamic content for `rows` | The statement is built from an expression | Expected. Type a literal statement to pick up the fields |
| Sign-in fails during connection creation | The generated redirect URL is not on the app registration | Register the downloaded value |
| `401` on every call | Missing `user_impersonation`, or `resourceUri` doesn't match the environment | Check the permission and both URLs in `apiProperties.json` |

Telemetry is off by default. Set `APP_INSIGHTS_ENABLED` to `true` in `script.csx` and replace `APP_INSIGHTS_KEY` with your instrumentation key to record executed statements, MCP tool calls, validation failures, and unhandled errors. Telemetry failures never fail an operation.

## Resources

- [Dataverse SQL connector source](https://github.com/troystaylor/SharingIsCaring/tree/main/Dataverse%20SQL)
- [Use SQL to query data with the Dataverse Web API](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/query/sql)
- [Page results](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/page-results)
- [Service protection API limits](https://learn.microsoft.com/power-apps/developer/data-platform/api-limits)
- [Query anti-patterns](https://learn.microsoft.com/power-apps/developer/data-platform/query-antipatterns)
- [Write code in a custom connector](https://learn.microsoft.com/connectors/custom-connectors/write-code)
