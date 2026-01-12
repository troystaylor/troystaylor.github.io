---
title: Manage Physical Spaces with Microsoft Places MCP Connector
author: Troy Taylor
date: 2026-01-12 12:13:40 -0500
category: Power Platform
layout: post
---

Workplace management just got easier with my new Microsoft Places connector for Copilot Studio. This connector brings the full power of Microsoft Places API to your conversational AI agents, enabling natural language management of buildings, floors, rooms, desks, and workspaces—all through the Model Context Protocol (MCP).

Find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Places).

## What is Microsoft Places?

Microsoft Places is a comprehensive workspace management solution that helps organizations:

- Map physical office buildings with addresses and WiFi details
- Organize floors within buildings with proper hierarchy
- Define sections (neighborhoods/zones) within floors
- Manage meeting rooms with capacity, A/V equipment, and booking settings
- Track workspaces for collaboration areas
- Configure individual desks with booking modes (reservable, drop-in, assigned, unavailable)
- Create room lists for Room Finder integration

The Graph API provides programmatic access to all these capabilities, but traditionally required understanding complex API patterns and hierarchical relationships. This MCP connector simplifies everything into natural language tools.

## The 13 MCP Tools

The connector exposes comprehensive workspace management through conversational tools:

### Discovery Tools (7 tools)
- `list_buildings` - List all buildings in organization
- `list_floors` - List all floors, optionally filtered by building
- `list_sections` - List all sections/neighborhoods
- `list_rooms` - List meeting rooms with capacity and A/V info
- `list_workspaces` - List all workspaces
- `list_desks` - List all desks with booking modes
- `list_room_lists` - List all room lists for Room Finder

### Lookup Tools (3 tools)
- `get_place` - Get details of a specific place by ID or email
- `list_rooms_in_room_list` - List rooms in a specific room list
- `list_workspaces_in_room_list` - List workspaces in a room list

### Management Tools (3 tools)
- `create_place` - Create buildings, floors, sections, desks, rooms, or workspaces
- `update_place` - Update properties of any place
- `delete_place` - Delete buildings, floors, sections, or desks

## Conversational Workspace Management

Once integrated with Copilot Studio, your agents handle workspace queries naturally:

**User:** "List all buildings in our organization"  
**Agent:** *Calls `list_buildings` tool and displays results*

**User:** "Show me all conference rooms with capacity over 10"  
**Agent:** *Calls `list_rooms` tool with filtering*

**User:** "Find available desks in the Engineering Wing"  
**Agent:** *Calls `list_desks` filtered by section*

**User:** "Create a new section called Marketing Hub on Floor 3"  
**Agent:** *Calls `create_place` with section type and parent reference*

**User:** "What's the booking mode for desk A1?"  
**Agent:** *Calls `get_place` and displays desk details*

The agent automatically extracts parameters, validates inputs, and handles errors based on the tool schemas.

## Understanding Place Hierarchy

Microsoft Places follows a strict hierarchy that ensures logical organization:

```
Building
  └── Floor (parentId = building)
        └── Section (parentId = floor)
              ├── Desk (parentId = section)
              ├── Workspace (parentId = section)
              └── Room (parentId = floor or section)
```

This hierarchy is enforced by the API and must be respected when creating places. The connector handles validation to ensure you maintain proper parent-child relationships.

## Technical Architecture

### Dual Operation Modes

Like my Bookings connector, this supports two modes:

1. **MCP Mode** - For Copilot Studio with 13 conversational tools
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
    "name": "microsoft-places-mcp",
    "version": "1.0.0",
    "title": "Microsoft Places MCP"
  }
}
```

**tools/list** - Returns all 13 tools with complete schemas

**tools/call** - Executes tools with validated arguments

**notifications/initialized** - Confirms initialization

### Dynamic Graph API Execution

The connector dynamically constructs Graph API calls based on tool invocations:

```csharp
private async Task<HttpResponseMessage> ExecuteToolAsync(string toolName, JObject args, JToken id)
{
    switch (toolName)
    {
        case "list_buildings": 
            return await CallGraphAsync("GET", "/places/microsoft.graph.building", args, id, new[] { "top", "filter", "select" });
        case "create_place":
            return await CallGraphAsync("POST", "/places", BuildPlaceBody(args), id);
        case "update_place":
            return await CallGraphAsync("PATCH", $"/places/{Arg(args, "placeId")}", args["properties"], id);
        // ... 13 tools total
    }
}
```

This approach provides:
- Centralized API communication
- Consistent error handling
- Standardized telemetry
- Easy maintenance

### Desk and Workspace Modes

Places supports four booking modes for desks and workspaces:

| Mode | Description |
|------|-------------|
| `microsoft.graph.reservablePlaceMode` | Can be reserved/booked |
| `microsoft.graph.dropInPlaceMode` | First-come, first-served |
| `microsoft.graph.assignedPlaceMode` | Permanently assigned to user |
| `microsoft.graph.unavailablePlaceMode` | Not available for use |

The connector validates these modes during creation and updates.

## Setup and Configuration

### Prerequisites
- Microsoft 365 tenant with Microsoft Places enabled
- Azure AD app registration with Places permissions:
  - `Place.Read.All` (Delegated) - For read operations
  - `Place.ReadWrite.All` (Delegated) - For create, update, delete
- Exchange Admin role (required for write operations)
- Power Platform environment

### Installation Steps

1. **Create Azure AD app registration**
   - Go to Azure Portal → Microsoft Entra ID → App registrations
   - Create new registration with name "Microsoft Places Connector"
   - Set redirect URI: `https://global.consent.azure-apim.net/redirect`

2. **Configure API permissions**
   - Add `Place.Read.All` and `Place.ReadWrite.All` (Delegated)
   - Grant admin consent for your organization

3. **Create client secret**
   - Go to Certificates & secrets
   - Create new client secret and copy the value

4. **Import connector**
   - Go to [Power Platform maker portal](https://make.powerapps.com) → Custom connectors
   - Import from OpenAPI: `apiDefinition.swagger.json`
   - Enable custom code and paste `script.csx`
   - Update app ID in connector settings

5. **Create connection and test**
   - Create a new connection
   - Grant consent for Places permissions
   - Test with `list_buildings` tool

## Application Insights Telemetry

The connector includes optional Application Insights integration for production monitoring:

### Tracked Events

| Event | Description |
|-------|-------------|
| `RequestReceived` | Every incoming request |
| `RequestCompleted` | Successful completion with duration |
| `RequestError` | Failed request with error details |
| `MCPMethod` | MCP protocol method invoked |
| `ToolExecuting` | Tool execution started |
| `ToolExecuted` | Tool completed with duration |
| `ToolError` | Tool failed with error details |

### Sample KQL Queries

Monitor workspace tool usage:
```kusto
customEvents
| where name == "ToolExecuted"
| extend Tool = tostring(customDimensions.Tool)
| summarize Count = count(), AvgDuration = avg(todouble(customDimensions.DurationMs)) by Tool
| order by Count desc
```

Track errors:
```kusto
customEvents
| where name in ("RequestError", "ToolError", "MCPError")
| where timestamp > ago(24h)
| project timestamp, name, Error = customDimensions.ErrorMessage, Tool = customDimensions.Tool
```

Telemetry is completely optional—leave the connection string empty to disable without affecting functionality.

## Creating Places - Examples

### Create a Building

```json
{
  "@odata.type": "microsoft.graph.building",
  "displayName": "Headquarters",
  "address": {
    "street": "123 Main St",
    "city": "Seattle",
    "state": "WA",
    "postalCode": "98101",
    "countryOrRegion": "USA"
  }
}
```

### Create a Floor

```json
{
  "@odata.type": "microsoft.graph.floor",
  "displayName": "Floor 1",
  "parentId": "<building-id>",
  "sortOrder": 1
}
```

### Create a Section

```json
{
  "@odata.type": "microsoft.graph.section",
  "displayName": "Engineering Wing",
  "parentId": "<floor-id>"
}
```

### Create a Reservable Desk

```json
{
  "@odata.type": "microsoft.graph.desk",
  "displayName": "Desk A1",
  "parentId": "<section-id>",
  "mode": {
    "@odata.type": "microsoft.graph.reservablePlaceMode"
  }
}
```

### Create a Conference Room

```json
{
  "@odata.type": "microsoft.graph.room",
  "displayName": "Conference Room Alpha",
  "parentId": "<floor-or-section-id>",
  "capacity": 12,
  "bookingType": "standard",
  "audioDeviceName": "Conference Phone",
  "videoDeviceName": "4K Camera",
  "displayDeviceName": "75-inch Display"
}
```

## Real-World Use Cases

### Workplace Management Copilot

Create an agent that helps facility managers:
- "List all desks on Floor 3 that are available for booking"
- "Create a new hot desk in the Marketing section"
- "What conference rooms have video conferencing equipment?"
- "Update the capacity of Conference Room Alpha to 15 people"

### Space Planning Automation

Integrate with resource planning workflows:
- "How many reservable desks do we have in the building?"
- "Find all rooms with capacity over 20"
- "List all sections in the Engineering building"
- "What's the booking mode for workspaces in the Innovation Lab?"

### Desk Booking Assistant

Help employees find workspace:
- "Show me available drop-in desks near Engineering"
- "Which rooms in the Executive room list are available?"
- "Find quiet workspaces on Floor 2"
- "What A/V equipment is in Conference Room Beta?"

## Important Limitations

Be aware of these API constraints:

- **Cannot delete**: Rooms, workspaces, and room lists (API limitation)
- **Cannot update**: `id`, `placeId`, `emailAddress`, `displayName`, or `bookingType` properties
- **Permissions required**: Exchange Admin role for all write operations
- **No app permissions**: Only delegated permissions supported for write operations

The connector validates these constraints and provides clear error messages when limitations are encountered.

## Try It Yourself

The complete connector code is in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Places):

- [README with full documentation](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Places/readme.md)
- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Places/apiDefinition.swagger.json) - OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Places/script.csx) - MCP implementation
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Places/apiProperties.json) - Connector metadata

If you build something with this connector or have ideas for improvements, I'd love to hear about it! Open an issue or submit a PR in the repository.

## Additional Resources

- [Places API Overview](https://learn.microsoft.com/graph/api/resources/places-api-overview)
- [Place Resource](https://learn.microsoft.com/graph/api/resources/place)
- [Building Resource](https://learn.microsoft.com/graph/api/resources/building)
- [Room Resource](https://learn.microsoft.com/graph/api/resources/room)
- [Workspace Resource](https://learn.microsoft.com/graph/api/resources/workspace)
- [Desk Resource](https://learn.microsoft.com/graph/api/resources/desk)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [My Previous Post on Microsoft Bookings MCP Connector](https://troystaylor.github.io/power%20platform/2026/01/08/microsoft-bookings-mcp-connector.html)
- [My Previous Post on Application Insights Telemetry](https://troystaylor.github.io/power%20platform/2026/01/07/power-platform-custom-connectors-application-insights.html)
