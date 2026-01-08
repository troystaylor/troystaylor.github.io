---
title: Building a Microsoft Bookings MCP Connector for Copilot Studio
author: Troy Taylor
date: 2026-01-08
category: Power Platform
layout: post
---

I'm excited to share my latest custom connector that brings Microsoft Bookings management directly into Copilot Studio through the Model Context Protocol (MCP). This connector exposes 30 natural language tools for managing booking businesses, services, staff, customers, and appointments—all accessible through conversational AI.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Bookings).

## Why Microsoft Bookings?

Microsoft Bookings is a powerful scheduling solution included with Microsoft 365 Business Premium that allows organizations to:

- Manage multiple booking businesses
- Define services with customizable durations and pricing
- Schedule staff members and track availability
- Handle customer information
- Book and manage appointments
- Publish public booking pages

The Microsoft Graph API provides comprehensive access to Bookings functionality, but traditionally required developers to understand complex API patterns. By wrapping this functionality in an MCP connector, we make Bookings management accessible through simple conversational requests.

## The 30 MCP Tools

The connector exposes four categories of tools:

### Business Management (7 tools)
- `listBookingBusinesses` - List all booking businesses in tenant
- `getBookingBusiness` - Get business details
- `createBookingBusiness` - Create new business
- `updateBookingBusiness` - Update business properties
- `deleteBookingBusiness` - Delete a business
- `publishBookingBusiness` - Make scheduling page public
- `unpublishBookingBusiness` - Hide scheduling page

### Service Management (5 tools)
- `listServices` - List services for a business
- `getService` - Get service details
- `createService` - Create new service
- `updateService` - Update service
- `deleteService` - Delete service

### Staff Management (6 tools)
- `listStaffMembers` - List staff members
- `getStaffMember` - Get staff details
- `createStaffMember` - Add staff member
- `updateStaffMember` - Update staff
- `deleteStaffMember` - Remove staff
- `getStaffAvailability` - Check availability

### Customer & Appointment Management (12 tools)
- `listCustomers` - List customers
- `getCustomer` - Get customer details
- `createCustomer` - Add customer
- `updateCustomer` - Update customer
- `deleteCustomer` - Remove customer
- `listAppointments` - List appointments
- `getAppointment` - Get appointment details
- `createAppointment` - Book appointment
- `updateAppointment` - Reschedule appointment
- `deleteAppointment` - Delete appointment
- `cancelAppointment` - Cancel with message
- `getCalendarView` - View appointments in date range

## Conversational Booking in Copilot Studio

Once you add this connector to your Copilot Studio agent, users can manage bookings naturally:

**User:** "List all my booking businesses"  
**Agent:** *Calls `listBookingBusinesses` tool and displays results*

**User:** "Create a new service called 'Strategy Consultation' for 1 hour at $200"  
**Agent:** *Calls `createService` with appropriate parameters*

**User:** "Book an appointment for Sarah Johnson at 2pm tomorrow for a strategy consultation"  
**Agent:** *Calls `createAppointment` with parsed details*

**User:** "Check Dana's availability next week"  
**Agent:** *Calls `getStaffAvailability` with date range*

**User:** "Cancel the appointment and notify the customer"  
**Agent:** *Calls `cancelAppointment` with notification enabled*

The agent handles parameter extraction, validation, and error handling automatically based on the tool schemas.

## Technical Architecture

### Dual Operation Modes

The connector supports two operation modes in the same connector:

1. **MCP Mode** - For Copilot Studio integration with 30 conversational tools
2. **REST Mode** - For Power Automate flows with direct Graph API operations

This dual approach gives you flexibility: use MCP for conversational AI scenarios and REST operations for traditional automation flows.

### MCP Protocol Implementation

The connector implements key MCP methods:

**initialize** - Establishes capabilities and protocol version
```json
{
  "protocolVersion": "2025-12-01",
  "capabilities": {
    "tools": { "listChanged": false }
  },
  "serverInfo": {
    "name": "microsoft-bookings-mcp",
    "version": "1.0.0",
    "title": "Microsoft Bookings MCP"
  }
}
```

**tools/list** - Returns all 30 available tools with schemas

**tools/call** - Executes a specific tool with provided arguments

**notifications/initialized** - Acknowledges initialization completion

## Implementation Highlights

### Dynamic Graph API Calls

The connector uses a helper method to construct Graph API calls dynamically:

```csharp
private async Task<HttpResponseMessage> ExecuteToolAsync(string toolName, JObject args, JToken id)
{
    switch (toolName)
    {
        case "listBookingBusinesses": 
            return await CallGraphAsync("GET", "/solutions/bookingBusinesses", args, id, new[] { "top", "filter" });
        case "createAppointment": 
            return await CallGraphAsync("POST", $"/solutions/bookingBusinesses/{Arg(args, "bookingBusinessId")}/appointments", BuildAppointmentBody(args), id);
        // ... 30 tools total
    }
}
```

This approach:
- Centralizes Graph API communication logic
- Standardizes error handling
- Enables consistent telemetry
- Simplifies maintenance

### Structured Error Responses

All errors follow JSON-RPC 2.0 error format:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": "unknown_method"
  }
}
```

Standard error codes:
- `-32700` - Parse error
- `-32601` - Method not found
- `-32602` - Invalid parameters
- `-32603` - Internal error


## Setup and Configuration

### Prerequisites
- Microsoft 365 Business Premium subscription
- Azure AD app registration with Bookings permissions:
  - `Bookings.Read.All` (Delegated)
  - `Bookings.ReadWrite.All` (Delegated)
  - `Bookings.Manage.All` (Delegated)
- Power Platform environment

### Installation Steps

1. **Import the connector**
   - Go to [Power Platform maker portal](https://make.powerapps.com) → Custom connectors
   - Import from OpenAPI: `apiDefinition.swagger.json`
   - Enable custom code and paste `script.csx`

2. **Configure OAuth**
   - Update client ID in connector security settings
   - Set redirect URI from connector to Azure AD app registration

3. **Optional: Configure Application Insights**
   - Create Application Insights resource
   - Update `APP_INSIGHTS_CONNECTION_STRING` in `script.csx`

4. **Create connection and test**
   - Create a new connection
   - Grant consent for Bookings permissions
   - Test with a simple tool call
   
## Application Insights Telemetry

The connector includes optional Application Insights integration for production monitoring:

### Tracked Events

| Event | Description |
|-------|-------------|
| `RequestReceived` | Every incoming request |
| `RequestCompleted` | Successful request with duration |
| `RequestError` | Failed request with error details |
| `MCPMethod` | MCP protocol method invoked |
| `ToolExecuting` | Tool execution started |
| `ToolExecuted` | Tool completed with duration |
| `ToolError` | Tool failed with error details |

### Sample KQL Queries

Monitor tool usage patterns:
```kusto
customEvents
| where name == "ToolExecuted"
| extend Tool = tostring(customDimensions.Tool)
| summarize Count = count(), AvgDuration = avg(todouble(customDimensions.DurationMs)) by Tool
| order by Count desc
```

Track errors in the last 24 hours:
```kusto
customEvents
| where name in ("RequestError", "ToolError", "MCPError")
| where timestamp > ago(24h)
| project timestamp, name, Error = customDimensions.ErrorMessage, Tool = customDimensions.Tool
```

Telemetry is completely optional—leave the connection string empty to disable it without affecting connector functionality.

## Real-World Use Cases

### Executive Assistant Copilot

Create a Copilot Studio agent that helps manage executive schedules:
- "Show me all available consultation slots next week"
- "Book a 30-minute strategy session with the CEO next Tuesday at 2pm"
- "Cancel all meetings for Friday and notify attendees"

### Customer Service Automation

Integrate with customer service workflows:
- "Find the customer record for sarah.johnson@contoso.com"
- "Reschedule their appointment to next Monday at the same time"
- "Check which services are available for booking"

### Resource Management

Monitor and optimize booking resources:
- "Which services are booked most frequently?"
- "Show me Dana's availability for the next two weeks"
- "List all appointments for the Marketing consultation service"

## Try It Yourself

The complete connector code is available in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Bookings):

- [README with full documentation](https://github.com/troystaylor/SharingIsCaring/blob/main/Bookings/readme.md)
- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Bookings/apiDefinition.swagger.json) - OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Bookings/script.csx) - MCP implementation
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Bookings/apiProperties.json) - Connector metadata

If you build something with this connector or have ideas for improvements, I'd love to hear about it! Feel free to open an issue or submit a PR in the repository.

## Additional Resources

- [Microsoft Bookings API Overview](https://learn.microsoft.com/en-us/graph/api/resources/booking-api-overview)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Power Platform Custom Connectors Documentation](https://learn.microsoft.com/en-us/connectors/custom-connectors/)
- [My Previous Post on Application Insights Telemetry](https://troystaylor.github.io/power%20platform/2026/01/07/power-platform-custom-connectors-application-insights.html)