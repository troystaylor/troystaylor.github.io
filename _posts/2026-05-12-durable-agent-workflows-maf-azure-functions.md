---
layout: post
title: "Durable agent workflows with Microsoft Agent Framework and Azure Functions"
date: 2026-05-12 11:00:00 -0500
categories: [Power Platform, MCP]
tags: [MCP, Copilot Studio, Microsoft Agent Framework, Azure Functions, Durable Workflows, Human-in-the-Loop]
---

Most AI agent demos run a single prompt and return a response. Enterprise processes don't work that way. A helpdesk ticket needs sentiment analysis, category classification, and KB search—all at once—followed by a manager's approval before anyone gets assigned. A document needs legal, compliance, brand, and technical review in parallel, then two separate sign-offs before it ships.

Microsoft Agent Framework (MAF) durable workflows handle exactly this. They checkpoint each step, survive failures, fan out to parallel AI agents, and pause at human-in-the-loop (HITL) gates until someone responds. This project packages three enterprise workflows into a single Azure Functions app, exposes them as MCP tools, and wraps them in an M365 Copilot declarative agent.

## What you get

Three workflows, each demonstrating different orchestration patterns:

| Workflow | Pattern | Description |
|----------|---------|-------------|
| **TriageTicket** | Sequential → fan-out/fan-in → HITL → sequential | Parses an IT ticket, runs sentiment, category, and KB search agents in parallel, merges results, pauses for manager approval, then assigns |
| **EvaluateResponse** | Fan-out/fan-in → HITL | Scores an AI agent's output on safety, accuracy, groundedness, and relevance using four parallel evaluators, aggregates scores, pauses for human review |
| **ReviewDocument** | Fan-out/fan-in → chained HITL | Routes a document through four parallel reviewers (legal, compliance, brand, technical), consolidates feedback, then gates through author revision **and** final approval |

The architecture looks like this:

```
M365 Copilot Declarative Agent
        │
        ▼  (native MCP plugin)
Azure Functions  /runtime/webhooks/mcp
        │
        ├── TriageTicket
        │     ParseTicket → [Sentiment, Category, KBSearch] → MergeAnalysis
        │       → ManagerApproval (HITL) → AssignTicket
        │
        ├── EvaluateResponse
        │     CaptureOutput → [Safety, Accuracy, Groundedness, Relevance]
        │       → AggregateScores → HumanReview (HITL) → PublishReport
        │
        └── ReviewDocument
              IngestDocument → [Legal, Compliance, Brand, Technical]
                → ConsolidateFeedback → AuthorRevision (HITL)
                → FinalApproval (HITL) → Publish
```

## Key MAF APIs

The entire workflow graph is built with a handful of MAF primitives:

| API | Purpose |
|-----|---------|
| `Executor<TIn, TOut>` | Unit of work in a workflow |
| `WorkflowBuilder` | Wire executors into a directed graph |
| `chatClient.AsAIAgent()` | Turn a `ChatClient` into an AI agent executor |
| `AddFanOutEdge` | Send input to multiple executors in parallel |
| `AddFanInBarrierEdge` | Wait for all parallel executors to complete |
| `RequestPort.Create<TReq, TRes>()` | Human-in-the-loop approval gate |
| `ConfigureDurableWorkflows` | Register workflows with Azure Functions host |
| `exposeMcpToolTrigger: true` | Auto-generate MCP tool for each workflow |

## How the code works

### Workflow registration

`Program.cs` builds all three workflows and registers them with the Azure Functions host in a single call:

```csharp
AzureOpenAIClient openAiClient = new(new Uri(endpoint), new AzureCliCredential());
ChatClient chatClient = openAiClient.GetChatClient(deploymentName);

Workflow triageWorkflow = TriageWorkflowBuilder.Build(chatClient);
Workflow evaluationWorkflow = EvaluationWorkflowBuilder.Build(chatClient);
Workflow docReviewWorkflow = DocReviewWorkflowBuilder.Build(chatClient);

using IHost app = FunctionsApplication
    .CreateBuilder(args)
    .ConfigureFunctionsWebApplication()
    .ConfigureDurableWorkflows(workflows =>
    {
        workflows.AddWorkflow(triageWorkflow,
            exposeMcpToolTrigger: true,
            exposeStatusEndpoint: true);

        workflows.AddWorkflow(evaluationWorkflow,
            exposeMcpToolTrigger: true,
            exposeStatusEndpoint: true);

        workflows.AddWorkflow(docReviewWorkflow,
            exposeMcpToolTrigger: true,
            exposeStatusEndpoint: true);
    })
    .Build();

app.Run();
```

Setting `exposeMcpToolTrigger: true` on each workflow tells the Functions host to generate an MCP endpoint at `/runtime/webhooks/mcp`. Any MCP client—M365 Copilot, Copilot Studio, VS Code, Claude Desktop—can discover and call these tools.

### Building a workflow graph

Each workflow builder wires executors into a directed graph. Here's the triage workflow:

```csharp
return new WorkflowBuilder(parseTicket)
    .WithName("TriageTicket")
    .WithDescription(
        "Triage an IT helpdesk ticket: parse the issue, analyze sentiment, "
        + "classify category, and search KB articles in parallel, then merge "
        + "results for manager approval before team assignment.")
    .AddFanOutEdge(parseTicket,
        [sentimentAgent, categoryAgent, kbSearchAgent])
    .AddFanInBarrierEdge(
        [sentimentAgent, categoryAgent, kbSearchAgent], mergeAnalysis)
    .AddEdge(mergeAnalysis, managerApproval)
    .AddEdge(managerApproval, assignTicket)
    .Build();
```

`AddFanOutEdge` sends the parsed ticket to three AI agents simultaneously. `AddFanInBarrierEdge` waits until all three complete before passing results to the merge executor. The `managerApproval` RequestPort pauses the entire workflow until a human responds.

### AI agents as executors

Each parallel branch is an AI agent created from a `ChatClient` with a system prompt:

```csharp
AIAgent sentimentAgent = chatClient.AsAIAgent(
    """
    You are a sentiment analyst for IT helpdesk tickets. Analyze the user's
    frustration level based on their language, tone, and urgency cues.

    Rate sentiment as one of: Calm, Mildly Frustrated, Frustrated,
    Very Frustrated, or Angry.

    Provide a 2-3 sentence explanation with specific evidence from the ticket.
    """,
    "SentimentAnalyst");
```

MAF handles the Azure OpenAI call, retry logic, and result routing. You write the prompt, the framework does the rest.

### Chained HITL gates

The document review workflow demonstrates chained approval gates—two sequential RequestPorts with a bridge executor between them:

```csharp
.AddEdge(consolidateFeedback, authorRevision)    // HITL gate #1
.AddEdge(authorRevision, prepareApproval)         // Bridge executor
.AddEdge(prepareApproval, finalApproval)          // HITL gate #2
.AddEdge(finalApproval, publish)
```

The `PrepareApprovalExecutor` bridges the author's revision response into a new `ApprovalRequest` for the final approver. This pattern lets you chain as many approval gates as you need—each gate pauses the workflow independently.

### Handling the 16KB CustomStatus limit

DurableTask limits `CustomStatus` to 16KB (UTF-16). With multiple AI agents producing verbose output and chained HITL gates accumulating metadata, you'll hit this limit fast. The `TextHelpers` class applies aggressive truncation:

```csharp
public static class TextHelpers
{
    private const int MaxSectionLength = 50;
    private const int MaxDetailsLength = 200;

    public static string Truncate(string text, int maxLength = MaxSectionLength)
    {
        if (string.IsNullOrEmpty(text) || text.Length <= maxLength)
            return text;
        return text[..maxLength] + "\n[truncated]";
    }

    public static string TruncateDetails(string text)
        => Truncate(text, MaxDetailsLength);
}
```

This is a framework-level limitation that MAF will likely address in a future release.

## MCP tools

When `exposeMcpToolTrigger: true` is set, the Functions host generates an MCP endpoint. Each workflow appears as a callable tool:

| Tool | Workflow | Input |
|------|----------|-------|
| `TriageTicket` | IT Helpdesk Triage | Ticket text |
| `EvaluateResponse` | Agent Evaluation Pipeline | Agent response (+ optional context) |
| `ReviewDocument` | Document Review Pipeline | Document text |

Discover tools with a standard MCP `tools/list` call:

```http
POST http://localhost:7071/runtime/webhooks/mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

## M365 Copilot declarative agent

The `agent-package/` folder contains a complete declarative agent that uses the MCP endpoint as a native plugin:

- **manifest.json** — Teams manifest v1.26
- **declarativeAgent.json** — Agent config with workflow-selection instructions and conversation starters
- **plugin.json** — MCP plugin v2.4 pointing to the Functions MCP endpoint

The agent's instructions tell it which tool to invoke based on the user's intent:

- IT issue or tech problem → `TriageTicket`
- Assess an AI agent's output → `EvaluateResponse`
- Submit content for review → `ReviewDocument`

Deploy the agent package through Teams Admin Center or Agents Toolkit after configuring OAuth in Teams Developer Portal.

## Running locally

### Prerequisites

- [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0)
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Docker](https://www.docker.com/) (for the DTS emulator)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) or `npx azurite`
- Azure OpenAI resource with a deployed chat model
- `Cognitive Services OpenAI User` role on your Azure OpenAI resource

### Start the emulators

```powershell
# Terminal 1 — DTS emulator
docker run -d --name dts-emulator `
  -p 8080:8080 -p 8082:8082 `
  mcr.microsoft.com/dts/dts-emulator:latest

# Terminal 2 — Azurite
npx azurite --silent --blobPort 10000 --queuePort 10001 --tablePort 10002
```

### Configure and run

```powershell
az login
```

Edit `functions-app/local.settings.json`:

```json
{
  "Values": {
    "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com",
    "AZURE_OPENAI_DEPLOYMENT": "gpt-4o"
  }
}
```

```powershell
cd functions-app
func start
```

Always run `az login` before `func start`. The Functions worker caches the credential at startup—if your token is expired, the AI agents will get 401 errors.

### Test a workflow

Start the triage workflow:

```http
POST http://localhost:7071/api/workflows/TriageTicket/run
Content-Type: text/plain
x-ms-wait-for-response: true

My Outlook keeps crashing when I open PDF attachments. This is the third time
this week.
```

Check status:

```http
GET http://localhost:7071/api/workflows/TriageTicket/status/{runId}
```

Submit approval:

```http
POST http://localhost:7071/api/workflows/TriageTicket/respond/{runId}
Content-Type: application/json

{
  "eventName": "ManagerApproval",
  "response": { "approved": true, "comments": "Assign to Desktop Engineering" }
}
```

Open `http://localhost:8082` to watch workflow runs, executor timelines, and parallel execution in the DTS Dashboard.

## Deploying to Azure

The `infra/` folder includes Bicep templates and a deployment script:

```powershell
./infra/deploy.ps1 `
    -ResourceGroupName "rg-durable-workflows" `
    -AzureOpenAIEndpoint "https://your-resource.openai.azure.com" `
    -DtsConnectionString "Endpoint=https://your-scheduler.azurewebsites.net;TaskHub=default;Authentication=ManagedIdentity"
```

The Bicep template deploys a Linux Consumption plan Function App with .NET 10 isolated worker, Application Insights, and managed identity RBAC for Storage (Blob Data Owner, Queue Data Contributor, Table Data Contributor). No shared keys—everything uses managed identity.

## Known issues

- **CustomStatus 16KB limit** — DurableTask limits `CustomStatus` to 16KB (UTF-16). With chained HITL gates, accumulated metadata can exceed this. The project mitigates with aggressive truncation.
- **Azure RBAC propagation** — After assigning `Cognitive Services OpenAI User` to a new identity, propagation across Azure OpenAI backend nodes can take up to 30 minutes. During that window, some parallel AI agents may get 401 errors while others succeed.

## Resources

- [Source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Durable%20Agent%20Workflows)
- [Durable workflows in MAF (blog)](https://devblogs.microsoft.com/dotnet/durable-workflows-in-microsoft-agent-framework/)
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Workflow samples](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples/03-workflows)
- [Azure Functions hosting samples](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples/04-hosting/DurableWorkflows/AzureFunctions)
- [M365 Copilot MCP plugins](https://learn.microsoft.com/microsoft-365/copilot/extensibility/build-mcp-plugins)
