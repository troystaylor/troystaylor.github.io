---
title: Beyond Microsoft's Frontier User Server - 51 MCP Tools for User Profiles
author: Troy Taylor
date: 2026-01-12 16:50:37 -0500
category: Power Platform
layout: post
---

Microsoft's Frontier M365 User Profile server provides 6 basic tools—this connector expands that to 51 tools, giving your agents access to user profiles, org charts, presence status, people search, and the entire Profile API (still in beta).

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Users).

## Why Go Beyond Microsoft's Frontier Server?

Microsoft is previewing a first-party User Profile MCP Server (Frontier) with basic functionality. This connector expands on that foundation with significantly more capabilities:

| Capability | Microsoft Frontier | This Connector |
|-----------|--------------|----------------|
| Basic profile access | ✅ 6 tools | ✅ 51 tools |
| Presence/availability | ❌ | ✅ My + user + batch |
| People search | ❌ | ✅ Relevance-ranked |
| Profile photos | ❌ | ✅ My + user photos |
| Schedule availability | ❌ | ✅ Free/busy lookup |
| Group memberships | ❌ | ✅ Groups, Teams, roles |
| License details | ❌ | ✅ My + user licenses |
| Mail tips/OOO status | ❌ | ✅ |
| Auth methods | ❌ | ✅ |
| Owned objects | ❌ | ✅ Apps and groups |
| **Profile API (Beta)** | ❌ | ✅ **26 tools** |
| Skills | ❌ | ✅ Find expertise |
| Projects | ❌ | ✅ Project history |
| Certifications | ❌ | ✅ Verify qualifications |
| Languages | ❌ | ✅ Find multilingual staff |
| Positions/Jobs | ❌ | ✅ Job history |
| Education | ❌ | ✅ Educational background |
| Awards & honors | ❌ | ✅ Recognition tracking |
| Interests | ❌ | ✅ Shared interests |
| Web accounts | ❌ | ✅ GitHub, LinkedIn, etc. |

## The 51 MCP Tools

The connector exposes comprehensive user management across nine categories:

### Core Profile Tools (7 tools)
- `get_my_profile` - Get signed-in user's profile
- `get_my_manager` - Get signed-in user's manager
- `get_my_direct_reports` - Get signed-in user's direct reports
- `get_user_profile` - Get any user's profile by ID or UPN
- `get_users_manager` - Get any user's manager
- `get_direct_reports` - Get any user's direct reports
- `list_users` - List/search users with OData support

### Presence Tools (3 tools)
- `get_my_presence` - Get signed-in user's availability
- `get_user_presence` - Get any user's availability
- `get_batch_presence` - Get presence for multiple users (up to 650)

### People & Photo Tools (3 tools)
- `search_people` - Search relevant people (ranked by collaboration)
- `get_my_photo_url` - Get signed-in user's photo URL
- `get_user_photo_url` - Get any user's photo URL

### Schedule & Availability Tools (2 tools)
- `get_schedule_availability` - Get free/busy times for users (find meeting times)
- `get_mail_tips` - Get out-of-office status, mailbox info for recipients

### Group & Team Tools (3 tools)
- `get_my_memberships` - Get groups, Teams, roles signed-in user belongs to
- `get_user_memberships` - Get groups, Teams, roles a user belongs to
- `get_my_joined_teams` - Get Microsoft Teams the signed-in user is in

### License Tools (2 tools)
- `get_my_licenses` - Get signed-in user's Microsoft 365 license details
- `get_user_licenses` - Get any user's license details

### Security & Auth Tools (1 tool)
- `get_my_auth_methods` - Get signed-in user's registered auth methods

### Ownership Tools (2 tools)
- `get_my_owned_objects` - Get apps/groups owned by signed-in user
- `get_user_owned_objects` - Get apps/groups owned by a user

### Profile API Tools (28 tools - Beta)
- `get_my_full_profile` / `get_user_full_profile` - Complete profile
- `get_my_skills` / `get_user_skills` - Professional skills
- `get_my_projects` / `get_user_projects` - Project history
- `get_my_certifications` / `get_user_certifications` - Professional certifications
- `get_my_awards` / `get_user_awards` - Awards and honors
- `get_my_languages` / `get_user_languages` - Language proficiencies
- `get_my_positions` / `get_user_positions` - Job history
- `get_my_education` / `get_user_education` - Educational background
- `get_my_interests` / `get_user_interests` - Personal and professional interests
- `get_my_web_accounts` / `get_user_web_accounts` - GitHub, LinkedIn, etc.
- `get_my_addresses` / `get_user_addresses` - Physical addresses
- `get_my_websites` / `get_user_websites` - Personal/professional websites
- `get_my_anniversaries` / `get_user_anniversaries` - Birthdays, work anniversaries
- `get_my_notes` / `get_user_notes` - Profile notes

## Conversational User Discovery

Once integrated with Copilot Studio, your agents handle user queries naturally:

**User:** "Who is my manager?"  
**Agent:** *Calls `get_my_manager` tool and displays manager details*

**User:** "Find people in Engineering with Azure expertise"  
**Agent:** *Calls `search_people` with query and `get_user_skills` for expertise matching*

**User:** "Is Sarah available for a meeting?"  
**Agent:** *Calls `get_user_presence` to check availability status*

**User:** "Find a time when the leadership team can meet this week"  
**Agent:** *Calls `get_schedule_availability` with team member emails*

**User:** "Who speaks Spanish in our company?"  
**Agent:** *Calls `list_users` with search, then `get_user_languages` to verify*

**User:** "What certifications does John have?"  
**Agent:** *Calls `get_user_certifications` to display qualifications*

**User:** "Is my manager out of office today?"  
**Agent:** *Calls `get_my_manager` followed by `get_mail_tips` for OOO status*

**User:** "Show me Dana's project history"  
**Agent:** *Calls `get_user_projects` to display work experience*

The agent automatically extracts parameters, validates inputs, and handles errors based on the tool schemas.

## Technical Architecture

### Dual Operation Modes

Like my other connectors, this supports two modes:

1. **MCP Mode** - For Copilot Studio with 51 conversational tools
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
    "name": "microsoft-users-mcp",
    "version": "1.0.0",
    "title": "Microsoft Users MCP"
  }
}
```

**tools/list** - Returns all 51 tools with complete schemas

**tools/call** - Executes tools with validated arguments

**notifications/initialized** - Confirms initialization

### Dynamic Graph API Execution

The connector dynamically constructs Graph API calls based on tool invocations:

```csharp
private async Task<HttpResponseMessage> ExecuteToolAsync(string toolName, JObject args, JToken id)
{
    switch (toolName)
    {
        case "get_my_profile":
            return await CallGraphAsync("GET", "/me", args, id, new[] { "select", "expand" });
        case "get_user_presence":
            return await CallGraphAsync("GET", $"/users/{Arg(args, "userIdentifier")}/presence", args, id);
        case "get_batch_presence":
            return await CallGraphAsync("POST", "/communications/getPresencesByUserId", args, id);
        case "search_people":
            return await CallGraphAsync("GET", "/me/people", args, id, new[] { "search", "top" });
        case "get_user_skills":
            return await CallGraphAsync("GET", $"/users/{Arg(args, "userIdentifier")}/profile/skills", args, id);
        // ... 51 tools total
    }
}
```

This approach provides:
- Centralized API communication
- Consistent error handling
- Standardized telemetry
- Easy maintenance

### Profile API (Beta) Integration

The Profile API tools access Microsoft Graph's beta endpoint to provide rich user profile data:

- **Skills** - Find subject matter experts in your organization
- **Projects** - Discover who worked on specific initiatives
- **Certifications** - Verify professional qualifications
- **Languages** - Find multilingual team members
- **Positions** - View career progression
- **Education** - Access educational backgrounds
- **Awards** - Recognize achievements
- **Interests** - Find colleagues with shared interests
- **Web Accounts** - Discover GitHub, LinkedIn, Twitter profiles

Profile data is populated by People Data Connectors or manual entry by users. Availability depends on profile completeness in your organization.

## Setup and Configuration

### Prerequisites
- Microsoft 365 tenant
- Azure AD app registration with delegated permissions:
  - `User.Read` - Read signed-in user's profile
  - `User.ReadBasic.All` - Read basic profiles
  - `User.Read.All` - Read full profiles
  - `People.Read` - Search people
  - `Presence.Read` / `Presence.Read.All` - Read presence
  - `Calendars.Read` / `Calendars.Read.Shared` - Read calendars
  - `MailboxSettings.Read` - Read mailbox settings
  - `Group.Read.All` - Read group memberships
  - `Directory.Read.All` - Read directory objects
  - `Team.ReadBasic.All` - Read joined Teams
  - `UserAuthenticationMethod.Read.All` - Read auth methods
- Power Platform environment

### Installation Steps

1. **Create Azure AD app registration**
   - Go to Azure Portal → Microsoft Entra ID → App registrations
   - Create new registration with name "Microsoft Users Connector"
   - Set redirect URI: `https://global.consent.azure-apim.net/redirect`

2. **Configure API permissions**
   - Add all delegated permissions listed above
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
   - Grant consent for all permissions
   - Test with `get_my_profile` tool

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

Monitor most-used tools:
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

## Real-World Use Cases

### Expertise Finder Copilot

Create an agent that helps discover talent:
- "Who in the company has Python and Azure certifications?"
- "Find someone who speaks French and has worked on mobile projects"
- "Which team members have awards for customer service?"
- "Show me people with machine learning skills in the Engineering department"

### Meeting Scheduler Assistant

Automate meeting coordination:
- "Find a time when the product team can meet this week"
- "Is my manager available for a quick sync this afternoon?"
- "Check if Dana is out of office next Monday"
- "Get presence status for the leadership team"

### Organizational Navigator

Help employees navigate company structure:
- "Who is the manager of the Marketing team?"
- "Show me the org chart starting from my VP"
- "Which teams is John a member of?"
- "What Microsoft Teams am I part of?"

### License & Compliance Tracker

Monitor licensing and access:
- "What licenses does Sarah have?"
- "Which users have Office 365 E5 licenses?"
- "Show me registered authentication methods for security review"
- "List all apps and groups owned by a departing employee"

### People Data Discovery

Leverage rich profile information:
- "Find team members who went to MIT"
- "Who has GitHub accounts I can collaborate with?"
- "Show me employees with project management experience"
- "Find colleagues interested in sustainability initiatives"

## Important Notes

1. **Use `get_my_*` tools** for signed-in user, not `get_user_*` with 'me'
2. **User identifiers** must be object ID (GUID) or userPrincipalName (UPN)
3. **If only display name available**, use `list_users` to look up the user first
4. **Expand limitation**: `$expand` can only expand one property per request (manager OR directReports)
5. **Advanced queries**: `ConsistencyLevel: eventual` is automatically set for complex searches
6. **Batch presence** supports up to 650 user IDs per request
7. **Profile API availability**: Beta endpoint data depends on profile completeness
8. **Profile data sources**: Populated by People Data Connectors or manual user entry

## Try It Yourself

The complete connector code is in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Users):

- [README with full documentation](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Users/readme.md)
- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Users/apiDefinition.swagger.json) - OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Users/script.csx) - MCP implementation
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Users/apiProperties.json) - Connector metadata

If you build something with this connector or have ideas for improvements, I'd love to hear about it! Open an issue or submit a PR in the repository.

## Additional Resources

- [User Resource](https://learn.microsoft.com/graph/api/resources/user)
- [List Users](https://learn.microsoft.com/graph/api/user-list)
- [Get Presence](https://learn.microsoft.com/graph/api/presence-get)
- [People API](https://learn.microsoft.com/graph/api/user-list-people)
- [Get Schedule](https://learn.microsoft.com/graph/api/calendar-getschedule)
- [Get Mail Tips](https://learn.microsoft.com/graph/api/user-getmailtips)
- [Profile API (Beta)](https://learn.microsoft.com/graph/api/resources/profile)
- [People Data Connectors](https://learn.microsoft.com/microsoft-365-copilot/extensibility/build-connectors-with-people-data)
- [Microsoft Frontier User Profile MCP Server](https://learn.microsoft.com/microsoft-agent-365/mcp-server-reference/me)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [My Previous Post on Microsoft Places MCP Connector](https://troystaylor.github.io/power%20platform/2026/01/12/microsoft-places-mcp-connector.html)
- [My Previous Post on Microsoft Bookings MCP Connector](https://troystaylor.github.io/power%20platform/2026/01/08/microsoft-bookings-mcp-connector.html)
