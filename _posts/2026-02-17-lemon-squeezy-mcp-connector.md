---
layout: post
title: "Lemon Squeezy MCP connector for Power Platform"
date: 2026-02-17 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Lemon Squeezy, MCP, Custom Connectors, Power Platform, Copilot Studio, Digital Products, Subscriptions, License Keys]
description: "Power Platform custom connector for Lemon Squeezy digital products platform with 35+ operations for products, subscriptions, license keys, discounts, and MCP tools for Copilot Studio."
---

I looked at Stripe first. Great API, well-documented, but I didn't want to deal with sales tax compliance myself—calculating rates, filing returns, handling exemptions across jurisdictions. Lemon Squeezy is a merchant of record, which means they handle all of that. They collect payment, calculate and remit taxes, and send you the net amount. For digital products—software, courses, ebooks, memberships—it's one less thing to manage.

This connector wraps 35+ operations across the Lemon Squeezy API into a Power Platform custom connector with MCP tools for Copilot Studio agents and Application Insights telemetry.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Lemon%20Squeezy).

## What's included

### Account (1 operation)

Get the authenticated user account. Useful for verifying API key validity and retrieving account details.

### Stores (2 operations)

List all stores the authenticated user has access to and get details for a specific store. Most filtering operations use store ID as a parameter.

### Products (4 operations)

| Operation | Description |
|-----------|-------------|
| List Products | Returns products, filterable by store |
| Get Product | Retrieves a specific product |
| List Variants | Returns product variants, filterable by product |
| Get Variant | Retrieves a specific variant with pricing details |

### Customers (4 operations)

List, get, create, and update customers. Filter by store or email when listing. Customer records link to orders and subscriptions.

### Orders (5 operations)

| Operation | Description |
|-----------|-------------|
| List Orders | Returns orders, filterable by store or email |
| Get Order | Retrieves order details including payment info |
| Generate Invoice | Creates a PDF invoice for an order |
| List Order Items | Returns line items for an order |
| Get Order Item | Retrieves a specific order item |

### Subscriptions (6 operations)

Full subscription lifecycle: list, get, update, cancel, and retrieve invoices. The Update Subscription operation handles upgrades, downgrades, pausing, and resuming.

### License Keys (3 operations)

List, get, and update license keys. Update lets you change activation limits, expiration dates, or disable keys entirely. Useful for managing software licenses from Power Automate.

### Discounts (4 operations)

Create, list, get, and delete discount codes. Supports percentage and fixed-amount discounts with optional usage limits and expiration dates.

### Webhooks (5 operations)

Manage webhook subscriptions programmatically. Create webhooks for events like `order_created`, `subscription_cancelled`, or `license_key_updated` without logging into the Lemon Squeezy dashboard.

## MCP tools for Copilot Studio

The connector exposes 22 MCP tools via JSON-RPC 2.0:

| Tool | Description |
|------|-------------|
| `list_stores` | List all stores for the authenticated user |
| `get_store` | Get store details |
| `list_products` | List products, optionally filtered by store |
| `get_product` | Get product details |
| `list_variants` | List product variants |
| `get_variant` | Get variant details |
| `list_customers` | List customers, filter by store or email |
| `get_customer` | Get customer details |
| `create_customer` | Create a new customer |
| `update_customer` | Update customer info |
| `list_orders` | List orders with filters |
| `get_order` | Get order details |
| `list_order_items` | List order line items |
| `list_subscriptions` | List subscriptions with filters |
| `get_subscription` | Get subscription details |
| `cancel_subscription` | Cancel a subscription |
| `pause_subscription` | Pause a subscription |
| `resume_subscription` | Resume a paused subscription |
| `list_license_keys` | List license keys |
| `get_license_key` | Get license key details |
| `update_license_key` | Update activation limit or disable |
| `list_discounts` | List discount codes |
| `get_discount` | Get discount details |
| `create_discount` | Create a new discount code |
| `delete_discount` | Delete a discount |

Add the connector as an action in Copilot Studio, and the agent discovers the tools automatically:

**User:** "Show me all active subscriptions for my SaaS product"
**Agent:** *Calls `list_subscriptions` with status filter*

**User:** "Create a 25% off discount code LAUNCH25 for the next 30 days"
**Agent:** *Calls `create_discount` with the parameters*

**User:** "How many license keys have been activated for ProductX?"
**Agent:** *Calls `list_license_keys` filtered by product*

## Setup

### Get your API key

1. Log in to your [Lemon Squeezy dashboard](https://app.lemonsqueezy.com/).
2. Navigate to **Settings → API**.
3. Click **Create API Key**.
4. Copy the key immediately—it won't be shown again.

### Import the connector

1. Go to [Power Automate](https://make.powerautomate.com/) or [Power Apps](https://make.powerapps.com/) → Custom connectors.
2. Import from OpenAPI file: upload `apiDefinition.swagger.json`.
3. Create a connection and enter your API key when prompted.

Or use PAC CLI:

```bash
pac connector create --api-definition apiDefinition.swagger.json --api-properties apiProperties.json
```

## Status values reference

### Subscription status

| Status | Description |
|--------|-------------|
| `on_trial` | In trial period |
| `active` | Active and paid |
| `paused` | Manually paused |
| `past_due` | Payment failed, in grace period |
| `unpaid` | Payment failed, service suspended |
| `cancelled` | Cancelled but active until period end |
| `expired` | Subscription ended |

### Order status

| Status | Description |
|--------|-------------|
| `pending` | Payment pending |
| `failed` | Payment failed |
| `paid` | Payment successful |
| `refunded` | Fully refunded |
| `partial_refund` | Partially refunded |
| `fraudulent` | Marked as fraudulent |

### License key status

| Status | Description |
|--------|-------------|
| `inactive` | Not yet activated |
| `active` | Currently active |
| `expired` | Past expiration date |
| `disabled` | Manually disabled |

## Examples

### List active subscriptions

In Power Automate, use the List Subscriptions action with:
- **Status:** `active`
- **Store ID:** Your store ID (optional)

### Create a discount code

Use the Create Discount action:
- **Name:** Internal reference (for example, "Launch Promo")
- **Code:** What customers enter (for example, `SAVE20`)
- **Amount:** Discount value (20 for 20% or 2000 for $20.00)
- **Amount Type:** `percent` or `fixed`
- **Store ID:** Your store ID

### Pause a subscription

Call Update Subscription with:
- **Subscription ID:** The subscription to pause
- **Pause:** `true`

## API notes

- **Rate limit:** 300 requests per minute
- **Response format:** JSON:API specification with `data`, `attributes`, and `relationships` structure
- **Pagination:** Use `page[number]` and `page[size]` parameters
- **Filtering:** Most list endpoints support `filter[field]` parameters
- **Test mode:** Products and orders created in test mode have `test_mode: true`

## Webhook events

Common events you can subscribe to:

- `order_created`, `order_refunded`
- `subscription_created`, `subscription_updated`, `subscription_cancelled`, `subscription_resumed`, `subscription_expired`, `subscription_paused`, `subscription_unpaused`
- `subscription_payment_success`, `subscription_payment_failed`, `subscription_payment_recovered`, `subscription_payment_refunded`
- `license_key_created`, `license_key_updated`

## Application Insights (optional)

Update the connection string in `script.csx`:

```csharp
private const string APP_INSIGHTS_CONNECTION_STRING = "InstrumentationKey=xxx;IngestionEndpoint=https://xxx.in.applicationinsights.azure.com/";
```

Events logged: `RequestReceived`, `RequestCompleted`, `RequestError`, `MCPRequest`, `MCPToolCall`, `MCPToolError`.

Sample KQL query:

```kql
customEvents
| where name startswith "Lemon"
| extend CorrelationId = tostring(customDimensions.CorrelationId)
| extend Tool = tostring(customDimensions.Tool)
| summarize count() by Tool, bin(timestamp, 1h)
| render timechart
```

## Try it yourself

The complete connector code is available in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Lemon%20Squeezy):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Lemon%20Squeezy/apiDefinition.swagger.json) — OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Lemon%20Squeezy/script.csx) — Connector script with MCP tools
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Lemon%20Squeezy/apiProperties.json) — Connector metadata
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Lemon%20Squeezy/readme.md) — Full documentation

## Resources

- [Lemon Squeezy API documentation](https://docs.lemonsqueezy.com/api)
- [Lemon Squeezy developer guide](https://docs.lemonsqueezy.com/guides)
- [JSON:API specification](https://jsonapi.org/)
- [Application Insights telemetry for connectors](https://troystaylor.github.io/power%20platform/2026/01/07/power-platform-custom-connectors-application-insights.html)
