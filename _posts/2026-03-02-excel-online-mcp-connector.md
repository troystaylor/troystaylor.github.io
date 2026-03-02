---
layout: post
title: "Excel in Copilot Studio: Excel Online MCP Connector"
date: 2026-03-02 10:00:00 -0500
categories: [Power Platform, MCP, Copilot Studio]
tags: [excel, mcp, custom-connectors, microsoft-graph, copilot-studio]
author: Troy Taylor
---

Spreadsheet automation just got conversational with my new Excel Online connector for Copilot Studio. While Excel isn't yet part of Microsoft's [Frontier Agents platform](https://learn.microsoft.com/en-us/microsoft-agent-365/tooling-servers-overview), this connector brings the full power of Excel's Graph API to your AI agents right now, enabling natural language manipulation of workbooks, worksheets, tables, ranges, and formulas—all through the Model Context Protocol (MCP).

Find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Excel%20Online%20MCP).

## What is Excel Online?

Excel Online (Excel for the web) is Microsoft's cloud-based spreadsheet solution that provides programmatic access through the Graph API. Organizations use it to:

- Create and manage workbooks stored in OneDrive and SharePoint
- Manipulate worksheets with cell ranges, formulas, and formatting
- Work with structured tables for data analysis
- Generate charts and visualizations
- Define named items for reusable references
- Perform calculations and trigger recalculations
- Apply conditional formatting and data validation

The Graph API provides comprehensive Excel capabilities, but traditionally required learning complex API patterns, cell addressing schemes, and workbook object models. This MCP connector simplifies everything into natural language tools that handle the complexity for you.

## MCP Tools and Operations

The connector exposes six categories of tools with enum-based parameters that provide over 150 discrete operations for complete Excel management:

### Workbook Management (4 tools)
- `create_workbook` - Create new workbook in OneDrive or SharePoint
- `get_workbook` - Get workbook metadata and properties
- `list_worksheets` - List all sheets in a workbook
- `create_session` - Create persistent session for batching operations

### Worksheet Operations (6 tools)
- `get_worksheet` - Get worksheet details by name or ID
- `add_worksheet` - Add new worksheet to workbook
- `update_worksheet` - Rename or reposition worksheet
- `delete_worksheet` - Remove worksheet from workbook
- `get_used_range` - Get the smallest range containing all used cells
- `calculate_worksheet` - Trigger recalculation of formulas

### Range Operations (8 tools)
- `get_range` - Get values and properties from a cell range
- `update_range` - Set values, formulas, or formatting
- `clear_range` - Clear values, formats, or both
- `insert_range` - Insert cells and shift existing cells
- `delete_range` - Delete cells and shift remaining cells
- `merge_range` - Merge cells into single cell
- `unmerge_range` - Unmerge previously merged cells
- `format_range` - Apply number formats, colors, fonts, and borders

### Table Operations (6 tools)
- `list_tables` - List all tables in worksheet or workbook
- `get_table` - Get table details and properties
- `create_table` - Convert range to structured table
- `add_table_row` - Append row to table
- `add_table_column` - Add column to table
- `delete_table` - Remove table (keeps data)

### Named Items (2 tools)
- `list_named_items` - List all named ranges and constants
- `add_named_item` - Create named range or constant

### Chart Operations (2 tools)
- `list_charts` - List all charts in worksheet
- `create_chart` - Create new chart from data range

## Conversational Excel Automation

Once integrated with Copilot Studio, your agents handle Excel operations naturally:

**User:** "Create a new workbook called Q1 Sales Report"  
**Agent:** *Calls `create_workbook` tool with the name*

**User:** "Add a worksheet called Regional Data"  
**Agent:** *Calls `add_worksheet` with worksheet name*

**User:** "Put the headers Product, Region, Revenue in cells A1 through C1"  
**Agent:** *Calls `update_range` with A1:C1 and the header values*

**User:** "Convert the range A1:C10 to a table named SalesData"  
**Agent:** *Calls `create_table` with range and table name*

**User:** "Add a row with values Laptop West 15000"  
**Agent:** *Calls `add_table_row` with the data array*

**User:** "Calculate the sum of revenue in cell D11"  
**Agent:** *Calls `update_range` with formula =SUM(C2:C10)*

**User:** "Create a column chart showing revenue by region"  
**Agent:** *Calls `create_chart` with appropriate data range and chart type*

**User:** "Format cells A1 through C1 as bold with blue background"  
**Agent:** *Calls `format_range` with font and fill properties*

The agent automatically extracts cell references, validates ranges, handles A1 notation, and provides helpful error messages when operations fail.

## Understanding Excel Object Model

Excel's object hierarchy follows a clear structure:

```
Workbook (file in OneDrive/SharePoint)
  ├── Worksheets (individual sheets)
  │     ├── Ranges (cells A1:B5)
  │     ├── Tables (structured data)
  │     │     ├── Columns
  │     │     └── Rows
  │     ├── Charts (visualizations)
  │     └── Named Items (defined names)
  └── Workbook-level Named Items
```

The connector handles this hierarchy automatically, letting you reference objects by name or ID without managing relationships manually.

## Range Addressing Made Simple

One of Excel's complexities is range addressing. The connector supports multiple formats:

**A1 Notation:** `A1:C10` (traditional Excel style)  
**Named Ranges:** `SalesData` (user-defined names)  
**Entire Rows:** `1:5` (rows 1 through 5)  
**Entire Columns:** `A:C` (columns A through C)  
**Single Cells:** `B5` (individual cell)

The agent understands natural language and converts it to proper range references:
- "cells A1 through C10" → `A1:C10`
- "column B" → `B:B`
- "row 5" → `5:5`
- "cell D11" → `D11`

## Technical Architecture

### Dual Operation Modes

Like my other MCP connectors, this supports two modes:

1. **MCP Mode** - For Copilot Studio with conversational tools exposing 150+ operations
2. **REST Mode** - For Power Automate flows with direct Graph API operations

Use MCP for conversational AI scenarios and REST operations for traditional automation workflows.

### MCP Protocol Implementation

The connector implements standard MCP methods:

**initialize** - Establishes protocol capabilities
```json
{
  "protocolVersion": "2025-12-01",
  "capabilities": {
    "tools": { "listChanged": false }
  },
  "serverInfo": {
    "name": "excel-online-mcp",
    "version": "1.0.0",
    "title": "Excel Online MCP"
  }
}
```

**tools/list** - Returns all tools with complete schemas including enum parameters

**tools/call** - Executes tools with validated arguments and returns results

**notifications/initialized** - Confirms initialization complete

### Dynamic Graph API Construction

The connector dynamically builds Graph API calls based on tool invocations:

```csharp
private async Task<HttpResponseMessage> ExecuteToolAsync(string toolName, JObject args, JToken id)
{
    var driveItemId = Arg(args, "driveItemId");
    var worksheetId = Arg(args, "worksheetId");
    
    switch (toolName)
    {
        case "get_workbook":
            return await CallGraphAsync("GET", 
                $"/drives/{driveItemId}/items/{itemId}/workbook", args, id);
                
        case "update_range":
            var rangeAddress = Arg(args, "rangeAddress");
            return await CallGraphAsync("PATCH", 
                $"/drives/{driveItemId}/items/{itemId}/workbook/worksheets/{worksheetId}/range(address='{rangeAddress}')",
                args["rangeData"], id);
                
        case "create_table":
            return await CallGraphAsync("POST",
                $"/drives/{driveItemId}/items/{itemId}/workbook/worksheets/{worksheetId}/tables/add",
                BuildTableBody(args), id);
                
        // ... additional tools with enum-based operations
    }
}
```

This approach provides:
- Centralized API communication
- Consistent error handling with detailed messages
- Standardized telemetry and logging
- Easy maintenance and updates
- Automatic token management

### Workbook Sessions for Efficiency

Excel's Graph API supports sessions that optimize performance for multiple operations:

```csharp
// Create session
POST /drives/{id}/items/{id}/workbook/createSession
{
  "persistChanges": true
}

// Use session header for subsequent requests
Workbook-Session-Id: {session-id}

// Close session when done
POST /drives/{id}/items/{id}/workbook/closeSession
```

The `create_session` tool creates a persistent session that:
- Batches changes for better performance
- Reduces API calls
- Maintains consistency across operations
- Automatically saves when closed

Use sessions when making multiple related changes to the same workbook.

## Working with Tables

Excel tables provide structured data management with headers, automatic formatting, and calculated columns. The connector makes table operations straightforward:

**Creating Tables:**
```json
{
  "tool": "create_table",
  "arguments": {
    "driveItemId": "drive-id",
    "itemId": "workbook-id",
    "worksheetId": "Sheet1",
    "rangeAddress": "A1:C10",
    "hasHeaders": true,
    "tableName": "SalesData"
  }
}
```

**Adding Data:**
```json
{
  "tool": "add_table_row",
  "arguments": {
    "driveItemId": "drive-id",
    "itemId": "workbook-id",
    "tableId": "SalesData",
    "values": ["Laptop", "West", 15000]
  }
}
```

Tables automatically expand as you add rows, maintain referential integrity in formulas, and provide structured references like `SalesData[Revenue]` for sum calculations.

## Chart Visualization

Create visual representations of your data with the chart tools:

```json
{
  "tool": "create_chart",
  "arguments": {
    "driveItemId": "drive-id",
    "itemId": "workbook-id",
    "worksheetId": "Sheet1",
    "chartType": "ColumnClustered",
    "sourceData": "A1:C10",
    "seriesBy": "Auto"
  }
}
```

Supported chart types include:
- Column (Clustered, Stacked, 100% Stacked)
- Bar (Clustered, Stacked, 100% Stacked)
- Line (Line, Stacked, Markers)
- Pie (Pie, Exploded, Doughnut)
- Scatter (XY Scatter, Bubble)
- Area (Area, Stacked, 100% Stacked)

Charts automatically update as the underlying data changes.

## Formula and Calculation Support

The connector supports both values and formulas in range operations:

**Setting Values:**
```json
{
  "rangeData": {
    "values": [["Product", "Price"], ["Laptop", 999]]
  }
}
```

**Setting Formulas:**
```json
{
  "rangeData": {
    "formulas": [["=SUM(B2:B10)"], ["=AVERAGE(B2:B10)"]]
  }
}
```

Use `calculate_worksheet` to manually trigger recalculation when automatic calculation is disabled.

## Formatting Options

The `format_range` tool provides comprehensive formatting:

```json
{
  "tool": "format_range",
  "arguments": {
    "rangeAddress": "A1:C1",
    "format": {
      "font": { "bold": true, "size": 14, "color": "#FFFFFF" },
      "fill": { "color": "#4472C4" },
      "borders": {
        "bottom": { "style": "Continuous", "weight": "Medium" }
      },
      "numberFormat": "$#,##0.00"
    }
  }
}
```

Formatting options include:
- **Font:** bold, italic, underline, size, color, name
- **Fill:** background color, pattern
- **Borders:** top, bottom, left, right, outline styles and colors
- **Alignment:** horizontal, vertical, text wrap, indent
- **Number Format:** currency, percentage, date, custom patterns

## Authentication and Permissions

The connector uses OAuth 2.0 with Microsoft Graph and requires these permissions:

**Application Permissions (for daemon scenarios):**
- `Files.ReadWrite.All` - Full workbook access across organization

**Delegated Permissions (for user context):**
- `Files.ReadWrite` - Access user's workbooks
- `Files.ReadWrite.All` - Access all files user can access

Configure these in Azure AD app registration under **API Permissions**.

## Setting Up the Connector

1. **Register Azure AD Application:**
   - Navigate to Azure Portal → App Registrations
   - Create new registration with redirect URI
   - Add Graph API permissions: `Files.ReadWrite.All`
   - Create client secret
   - Note Application (client) ID and Directory (tenant) ID

2. **Deploy the Connector:**
   - Clone the repository
   - Update `appsettings.json` with your tenant and app details
   - Deploy to Azure App Service or run locally
   - Note the connector endpoint URL

3. **Import to Power Platform:**
   - Go to Power Apps → Data → Custom Connectors
   - Create new connector from OpenAPI
   - Import the `swagger.json` from the repository
   - Configure authentication with your Azure AD app
   - Test the connection

4. **Add to Copilot Studio:**
   - Open your Copilot Studio agent
   - Go to Settings → Generative AI
   - Enable Knowledge and Dynamic chaining
   - Add the Excel Online connector as an action
   - Agent discovers all tools and enum operations automatically

## Real-World Scenarios

**Financial Report Generation:**
Create monthly reports with tables, formulas, and charts:
- "Create a workbook called Monthly Report"
- "Add sheets for Revenue, Expenses, and Summary"
- "Import the revenue data from the database"
- "Calculate totals and create a summary table"
- "Add a chart showing trends over time"

**Data Validation and Cleanup:**
Process and validate imported data:
- "Open the customer import workbook"
- "Remove all blank rows"
- "Convert column A to proper case"
- "Check for duplicate email addresses"
- "Flag rows where the phone number is invalid"

**Automated Invoice Processing:**
Generate invoices from structured data:
- "Create invoice workbook from template"
- "Fill in customer details in cells A5:B10"
- "Add line items to the Items table"
- "Calculate tax and total"
- "Format as currency with two decimal places"

**Collaborative Budget Planning:**
Manage team budgets with structured worksheets:
- "Create budget workbook for Q2 2026"
- "Add sheets for Marketing, Sales, Engineering"
- "Set up budget tables with categories and amounts"
- "Add formulas to calculate department totals"
- "Create a summary sheet with overall budget"

## Error Handling and Validation

The connector provides helpful error messages when operations fail:

**Invalid Range Reference:**
```
"Range address 'XYZ123' is not valid. 
Use Excel A1 notation like 'A1:C10'"
```

**Missing Required Parameters:**
```
"Required parameter 'driveItemId' not provided. 
Specify the OneDrive drive ID containing the workbook."
```

**Permission Issues:**
```
"Access denied to workbook. 
Verify the app has Files.ReadWrite.All permission."
```

**Worksheet Not Found:**
```
"Worksheet 'Data' not found in workbook. 
Available sheets: Sheet1, Summary, Report"
```

These messages help agents understand what went wrong and guide users toward resolution.

## Performance Considerations

When working with large workbooks:

**Use Sessions:** Create a session for batch operations to reduce API calls and improve performance

**Limit Range Size:** Work with smaller ranges (under 5MB) to avoid timeouts

**Batch Operations:** Group multiple updates into arrays rather than individual cell updates

**Async Processing:** For large imports, consider using Power Automate flows with chunking

**Named Ranges:** Use named ranges instead of large address strings for better maintainability

## Limitations and Workarounds

**File Size:** Workbooks over 150MB may have limited API functionality—consider splitting large files

**Concurrent Access:** Multiple simultaneous writes may cause conflicts—use sessions to serialize operations

**Formula Complexity:** Very complex formulas may not calculate immediately—use `calculate_worksheet` to force recalculation

**Chart Limitations:** Some advanced chart types and customizations require Excel desktop—focus on common chart types for API access

**Binary Format (.xlsx only):** The API works with .xlsx files—legacy .xls files must be converted first

## What's Next?

This connector demonstrates the power of combining Excel's rich API with conversational AI through MCP. Some areas I'm exploring:

**Pivot Tables:** Adding tools for pivot table creation and manipulation

**Conditional Formatting:** Expanding formatting tools to include rules and data bars

**Data Validation:** Tools for dropdown lists and input restrictions

**External Data Connections:** Importing from databases and web services

**Macro Conversion:** Converting VBA macros to Power Automate flows

**Template Management:** Creating and applying workbook templates

## Conclusion

The Excel Online MCP Connector bridges the gap between Excel's powerful API and natural language interfaces. By wrapping Graph API operations in conversational tools with enum-based parameters that expose over 150 discrete operations, it makes spreadsheet automation accessible to your Copilot Studio agents without requiring users to learn complex Excel object models or API patterns.

Whether you're generating reports, processing data, or managing collaborative workbooks, this connector handles the technical complexity while your agents focus on understanding user intent.

The complete source code, including OpenAPI specifications, authentication configuration, and deployment guides, is available in the [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Excel%20Online%20MCP).

Ready to make your spreadsheets conversational? Clone the repo and start building.

#PowerPlatform #CopilotStudio #MCP #Excel #MicrosoftGraph #Automation #AI
