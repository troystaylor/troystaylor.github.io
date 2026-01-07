---
title: Adding Application Insights Telemetry to Power Platform Custom Connectors
author: Troy Taylor
date: 2026-01-07
category: Power Platform
layout: post
---

One of the most powerful features of Power Platform custom connectors is the ability to add custom code through C# scripts. Today, I want to share a template script that demonstrates how to integrate Azure Application Insights telemetry into your custom connectors for enhanced monitoring and debugging.

## Why Add Telemetry?

When building enterprise-grade custom connectors, you need visibility into:
- Request patterns and volume
- Error rates and failure scenarios
- Performance bottlenecks
- User behavior and API usage

While Power Platform provides basic logging through `this.Context.Logger`, integrating Application Insights gives you:
- **Rich querying** with KQL (Kusto Query Language)
- **Dashboards and alerts** for proactive monitoring
- **Distributed tracing** across your integration landscape
- **Long-term retention** of telemetry data

## The Template Script

I've created a comprehensive template that shows how to combine both `this.Context.Logger` (built-in logging) and Application Insights telemetry in a custom connector script. You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/blob/main/Connector-Code/Application%20Insights%20Logging/script.csx).

### Key Features

The script demonstrates:

1. **Dual Logging Strategy**
   - Basic logging with `this.Context.Logger` for immediate visibility
   - Enhanced telemetry with Application Insights for deep analysis

2. **Correlation Tracking**
   - Every request gets a unique correlation ID
   - Track requests across logs and distributed systems

3. **Error Handling with Context**
   - Comprehensive error capture with stack traces
   - Errors logged to both systems for reliability

4. **Performance Metrics**
   - Request duration tracking
   - Operation timing for bottleneck identification

### Configuration

The script uses a single configuration point - your Application Insights connection string:

```csharp
private const string APP_INSIGHTS_CONNECTION_STRING = 
    "InstrumentationKey=YOUR-KEY;IngestionEndpoint=https://REGION.in.applicationinsights.azure.com/";
```

Leave it empty to disable telemetry entirely, allowing the connector to function normally while you're in development.

### How It Works

The script intercepts requests and:

1. **Generates a correlation ID** for tracking
2. **Logs basic info** using `Context.Logger`
3. **Sends rich events** to Application Insights asynchronously
4. **Processes your custom logic** (the TODO section)
5. **Tracks completion** with timing metrics
6. **Handles errors gracefully** with full context

Here's the event flow:

```
RequestReceived → OperationProcessed → RequestCompleted
                ↓ (on error)
            RequestError
```

### Sample Event Logging

The template shows how to log custom events with structured properties:

```csharp
await LogToAppInsights("OperationProcessed", new {
    CorrelationId = correlationId,
    Operation = operationName,
    HasPayload = payload.Count > 0
});
```

These events appear in Application Insights where you can query them with KQL:

```kusto
customEvents
| where name == "OperationProcessed"
| extend operation = tostring(customDimensions.Operation)
| summarize count() by operation
```

## Best Practices

1. **Fire and Forget** - The script sends telemetry asynchronously to avoid slowing down your connector
2. **Suppressed Errors** - Telemetry failures don't impact the main request flow
3. **Privacy Conscious** - Body previews are truncated to avoid logging sensitive data
4. **Configurable** - Easy to enable/disable by setting the connection string

## Getting Started

1. Create an Application Insights resource in Azure
2. Copy the connection string from the Overview blade
3. Update the `APP_INSIGHTS_CONNECTION_STRING` constant
4. Add your custom logic in the TODO section
5. Deploy to your custom connector

## Next Steps

This template provides a solid foundation for production custom connectors. You can extend it with:
- **Dependency tracking** for external API calls
- **Custom metrics** for business KPIs
- **Sampling strategies** for high-volume connectors
- **Security filtering** to redact sensitive data

Check out the [full script on GitHub](https://github.com/troystaylor/SharingIsCaring/blob/main/Connector-Code/Application%20Insights%20Logging/script.csx) to see all the implementation details.

Have questions or improvements? Feel free to open an issue or submit a PR in the repository!
