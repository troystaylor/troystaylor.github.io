---
layout: post
title: "Coupa procurement MCP connector for Power Platform"
date: 2026-04-01 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Coupa, Procurement, MCP, Copilot Studio, Custom Connectors, Power Platform, Invoices, Purchase Orders]
description: "Power Platform custom connector for the Coupa procurement platform—manage purchase orders, invoices, requisitions, suppliers, contracts, and approvals through 13 MCP tools and 47 REST operations."
---

Coupa runs procurement for thousands of enterprises—purchase orders, invoices, requisitions, supplier management, contracts, approvals, and expense reports. My connector brings the Coupa Core API into Power Platform with 13 MCP tools for Copilot Studio and 47 REST operations for Power Automate and Power Apps. OAuth 2.0 handles authentication through Coupa's OpenID Connect client.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Coupa)

## Tools

### MCP tools for Copilot Studio

| Tool | Description |
|------|-------------|
| `list_purchase_orders` | Query POs with filters for status, supplier, PO number, and date |
| `get_purchase_order` | Get full PO details including line items |
| `list_invoices` | Query invoices with status, number, supplier, and date filters |
| `get_invoice` | Get invoice details with line items, taxes, and payment info |
| `list_requisitions` | Query requisitions by status and date |
| `get_requisition` | Get requisition details with all lines |
| `list_suppliers` | Query suppliers by name, status |
| `get_supplier` | Get full supplier details |
| `list_approvals` | Query approvals by status and approvable type |
| `list_contracts` | Query contracts by status and date |
| `get_contract` | Get contract details |
| `list_users` | Query users by email, login, or active status |
| `list_expense_reports` | Query expense reports by status and date |

### How it works

```
User: "Show me all purchase orders from Contoso that are still in draft"

1. Orchestrator calls list_purchase_orders({
     supplier_name: "Contoso",
     status: "draft"
   })
   → Returns POs with number, status, supplier, total, and line items

User: "Get me the details on PO-2026-0431"

2. Orchestrator calls get_purchase_order({ id: 12345 })
   → Returns full PO with all line items, ship-to address,
     payment terms, currency, and transmission status
```

All list tools support `limit`, `offset`, and `updated_after` parameters for pagination and incremental sync.

## REST operations for Power Automate and Power Apps

The connector exposes 47 typed operations across two categories:

### Reference data (22 operations)

| Operation | Operation ID | Method |
|-----------|-------------|--------|
| List Suppliers | `ListSuppliers` | GET |
| Get Supplier | `GetSupplier` | GET |
| Create Supplier | `CreateSupplier` | POST |
| Update Supplier | `UpdateSupplier` | PUT |
| List Users | `ListUsers` | GET |
| Get User | `GetUser` | GET |
| Create User | `CreateUser` | POST |
| Update User | `UpdateUser` | PUT |
| List Accounts | `ListAccounts` | GET |
| Get Account | `GetAccount` | GET |
| List Departments | `ListDepartments` | GET |
| Get Department | `GetDepartment` | GET |
| List Addresses | `ListAddresses` | GET |
| Get Address | `GetAddress` | GET |
| List Items | `ListItems` | GET |
| Get Item | `GetItem` | GET |
| List Currencies | `ListCurrencies` | GET |
| List Payment Terms | `ListPaymentTerms` | GET |
| List Exchange Rates | `ListExchangeRates` | GET |
| List Lookup Values | `ListLookupValues` | GET |
| List Projects | `ListProjects` | GET |
| Get Project | `GetProject` | GET |

### Transactional (25 operations)

| Operation | Operation ID | Method |
|-----------|-------------|--------|
| List Purchase Orders | `ListPurchaseOrders` | GET |
| Get Purchase Order | `GetPurchaseOrder` | GET |
| Create Purchase Order | `CreatePurchaseOrder` | POST |
| Update Purchase Order | `UpdatePurchaseOrder` | PUT |
| Issue Purchase Order | `IssuePurchaseOrder` | PUT |
| Cancel Purchase Order | `CancelPurchaseOrder` | PUT |
| Close Purchase Order | `ClosePurchaseOrder` | PUT |
| List Purchase Order Lines | `ListPurchaseOrderLines` | GET |
| List Invoices | `ListInvoices` | GET |
| Get Invoice | `GetInvoice` | GET |
| Create Invoice | `CreateInvoice` | POST |
| Update Invoice | `UpdateInvoice` | PUT |
| Submit Invoice | `SubmitInvoice` | PUT |
| Void Invoice | `VoidInvoice` | PUT |
| List Requisitions | `ListRequisitions` | GET |
| Get Requisition | `GetRequisition` | GET |
| Create Requisition | `CreateRequisition` | POST |
| Update Requisition | `UpdateRequisition` | PUT |
| List Approvals | `ListApprovals` | GET |
| Get Approval | `GetApproval` | GET |
| List Expense Reports | `ListExpenseReports` | GET |
| Get Expense Report | `GetExpenseReport` | GET |
| List Contracts | `ListContracts` | GET |
| Get Contract | `GetContract` | GET |
| List Receipts | `ListReceipts` | GET |

### PO lifecycle operations

The connector supports the full purchase order lifecycle through dedicated endpoints:

1. **Create** (`CreatePurchaseOrder`) — Create an external PO with supplier, ship-to address, currency, payment terms, and order lines
2. **Update** (`UpdatePurchaseOrder`) — Modify status, shipping, payment terms, or mark as exported
3. **Issue** (`IssuePurchaseOrder`) — Issue and transmit PO to the supplier via the configured method (cXML, XML, email, or buy online)
4. **Cancel** (`CancelPurchaseOrder`) — Cancel an open PO
5. **Close** (`ClosePurchaseOrder`) — Close a PO after completion

### Invoice workflow

1. **Create** (`CreateInvoice`) — Create a draft invoice with supplier, currency, payment terms, and line items
2. **Update** (`UpdateInvoice`) — Modify dates, comments, internal notes, or mark as exported
3. **Submit** (`SubmitInvoice`) — Submit draft invoice for approval routing
4. **Void** (`VoidInvoice`) — Void an approved invoice (works on approved, pending_receipt, or draft status)

## Use cases

**Procurement visibility**: Ask your Copilot Studio agent "What POs are still in draft?" or "Show me all invoices pending approval from last week." The MCP tools query Coupa and return structured results directly in conversation.

**Supplier onboarding**: Create suppliers with full details—PO transmission method (cXML, XML, email), payment method (invoice, pcard, virtual card), invoice matching level (2-way, 3-way, 3-way-direct), tax ID, and DUNS number.

**Approval monitoring**: Query pending approvals filtered by status and approvable type. Surface approvals that need attention without switching to the Coupa UI.

**Spend reporting**: Combine list operations across POs, invoices, and contracts to build spend visibility flows. Filter by supplier, date range, and status to track commitments and actuals.

**ERP integration**: Use the `exported` flag on POs, invoices, and requisitions to track which records have been synced to downstream systems. Update marks after successful export.

## Prerequisites

1. A Coupa instance with API access enabled
2. An OAuth 2.0/OpenID Connect client configured in Coupa (**Setup** > **Integrations** > **OAuth2/OpenID Connect Clients**)
3. API scopes assigned to the OIDC client (see required scopes below)

## Setting up the connector

### 1. Configure the Coupa OIDC client

1. In Coupa, navigate to **Setup** > **Integrations** > **OAuth2/OpenID Connect Clients**
2. Select **Create**
3. Select **Authorization Code** as the grant type
4. Enter a name (for example, "Power Platform Connector")
5. Set the **Redirect URI** to `https://global.consent.azure-apim.net/redirect`
6. Assign the required scopes:
   - `core.purchase_order.read` / `core.purchase_order.write`
   - `core.invoice.read` / `core.invoice.write`
   - `core.requisition.read` / `core.requisition.write`
   - `core.supplier.read` / `core.supplier.write`
   - `core.user.read` / `core.user.write`
   - `core.accounting.read`
   - `core.common.read`
   - `core.expense.read`
   - `core.contract.read`
   - `core.approval.read`
   - `offline_access`
7. Save and note the **Client ID** and **Client Secret**

### 2. Update configuration files

**apiDefinition.swagger.json**: Replace `YOUR_INSTANCE.coupahost.com` in the `host` field and `securityDefinitions` URLs with your Coupa instance URL.

**apiProperties.json**: Replace `YOUR_CLIENT_ID` with your OIDC client identifier and `YOUR_INSTANCE` in the authorization, token, and refresh URLs.

### 3. Create the custom connector

1. Go to [Power Platform Maker Portal](https://make.powerapps.com/)
2. Navigate to **Custom connectors** > **+ New custom connector** > **Import an OpenAPI file**
3. Upload `apiDefinition.swagger.json`
4. On the **Security** tab, verify the OAuth 2.0 settings match your OIDC client configuration
5. On the **Code** tab:
   - Enable **Code**
   - Upload `script.csx`
6. Select **Create connector**

### 4. Create a connection

1. Select **Test** > **+ New connection**
2. Sign in with your Coupa credentials
3. Authorize the requested scopes

### 5. Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "List all issued purchase orders" or "Show me invoices pending approval"

## Authentication

| Setting | Value |
|---------|-------|
| Type | OAuth 2.0 (Authorization Code) |
| Authorization URL | `https://{instance}.coupahost.com/oauth2/authorizations/new` |
| Token URL | `https://{instance}.coupahost.com/oauth2/token` |
| Token expiry | 24 hours |
| Refresh token expiry | 90 days |

## Design notes

- **No DELETE operations**: Coupa doesn't support DELETE on any resource. Use PUT to deactivate records instead
- **Pagination**: List operations return up to 50 records by default. Use `offset` and `limit` parameters for pagination
- **JSON only**: The connector sets `Content-Type` and `Accept` headers to `application/json` on every request. The script layer handles this automatically
- **Rate limiting**: Coupa recommends a 5-second buffer between token generation and the first API call

## Known limitations

- Country-specific compliance fields aren't included in the schema definitions to keep the connector manageable
- The GraphQL endpoint isn't included—use the REST operations instead
- CSV flat file operations aren't supported through this connector

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 47 REST operations |
| `apiProperties.json` | OAuth 2.0 config and script operation bindings |
| `script.csx` | C# script handling MCP protocol, REST passthrough with header management, and query parameter mapping |
| `readme.md` | Setup and usage documentation |

## Resources

- [Coupa connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Coupa)
- [Coupa API documentation](https://compass.coupa.com/en-us/products/product-documentation/integration-technical-documentation/the-coupa-core-api)
- [Coupa OAuth setup guide](https://compass.coupa.com/en-us/products/product-documentation/integration-technical-documentation/oauth-2.0-getting-started-with-coupa-api)
