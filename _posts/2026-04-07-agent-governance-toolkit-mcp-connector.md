---
layout: post
title: "Agent Governance Toolkit MCP connector for Power Platform"
date: 2026-04-07 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Agent Governance, OWASP, MCP, Copilot Studio, Custom Connectors, Power Platform, Security, Compliance, Trust Scoring]
description: "Power Platform custom connector for Microsoft's open-source Agent Governance Toolkit—policy enforcement, compliance grading, prompt injection detection, trust scoring, circuit breakers, and MCP tool scanning for Copilot Studio agents and Power Automate flows."
---

You built a Copilot Studio agent that updates Dataverse, sends emails through Graph, and calls third-party APIs. Now security wants to know what it can do, compliance wants EU AI Act evidence, and your CISO wants an audit trail before it goes to 50,000 users.

The [Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit) gives you runtime answers to those questions. It borrows patterns from operating systems (privilege rings, process isolation), service meshes (cryptographic identity, mTLS), and SRE (SLOs, circuit breakers) and applies them to AI agents. Seven packages, five languages (Python, TypeScript, Rust, Go, .NET), MIT licensed, covering all 10 OWASP Agentic AI Top 10 risks with sub-millisecond policy enforcement. Read Imran Siddique's [launch article](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/) for the full story on why Microsoft built it.

This connector wraps the .NET SDK deployed as an Azure Container App, bringing runtime governance into Copilot Studio agents with seven MCP tools and eight REST operations for Power Automate flows.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Agent%20Governance%20Toolkit)

## Architecture

```
Copilot Studio / Power Automate
        ↓
  Custom Connector (this)
        ↓
  Azure Container App (.NET 8 minimal API)
        ↓
  Microsoft.AgentGovernance NuGet SDK
```

The connector talks to a self-hosted Container App you deploy in your Azure subscription. The Container App runs statelessly—no database, no shared context between evaluations. Policy decisions happen in-process at sub-millisecond latency.

## What it covers

The toolkit maps directly to the [OWASP Agentic AI Top 10](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), published December 2025:

| OWASP risk | ID | How the connector addresses it |
|------------|-----|-------------------------------|
| Goal hijacking | ASI-01 | `detect_injection` + `evaluate_action` policy checks |
| Excessive capabilities | ASI-02 | `evaluate_action` allow/deny lists |
| Identity and privilege abuse | ASI-03 | `score_trust` with execution rings |
| Uncontrolled code execution | ASI-04 | `evaluate_action` blocks shell_exec, etc. |
| Insecure output handling | ASI-05 | `check_compliance` output validation |
| Memory poisoning | ASI-06 | Stateless evaluation (no shared context) |
| Unsafe inter-agent communication | ASI-07 | `scan_mcp_tool` validates tool definitions |
| Cascading failures | ASI-08 | `check_circuit_breaker` + SLO enforcement |
| Human-agent trust deficit | ASI-09 | `log_audit` full audit trails |
| Rogue agents | ASI-10 | `score_trust` decay + ring isolation |

## Tools

### MCP tools for Copilot Studio

| Tool | When to use it |
|------|---------------|
| `evaluate_action` | Before any tool call in any connector |
| `check_compliance` | Before handling regulated data |
| `score_trust` | When deciding privilege level or human escalation |
| `detect_injection` | Before processing any user input |
| `log_audit` | After every significant action |
| `check_circuit_breaker` | Before calling flaky external services |
| `scan_mcp_tool` | Before connecting to unknown MCP servers |

### How it works

```
User: "Delete all records from the customer database"

1. Orchestrator calls detect_injection({
     text: "Delete all records from the customer database"
   })
   → { isInjection: false }

2. Orchestrator calls evaluate_action({
     toolName: "database_delete",
     agentId: "sales-agent-01",
     args: { table: "customers", scope: "all" }
   })
   → { allowed: false,
       reason: "Bulk delete operations require Ring0 privileges",
       policyRule: "block-destructive",
       ring: "Ring2" }

3. Orchestrator calls score_trust({
     agentId: "sales-agent-01"
   })
   → { score: 720, tier: "Standard", ring: "Ring2" }

4. Agent responds: "I can't delete all customer records.
   That operation requires higher privileges than my current
   trust level. Let me escalate to an administrator."

5. Orchestrator calls log_audit({
     agentId: "sales-agent-01",
     action: "database_delete_attempted",
     toolName: "database_delete",
     result: "denied_insufficient_privileges"
   })
```

## REST operations for Power Automate and Power Apps

| Operation | Operation ID | Method | Path |
|-----------|-------------|--------|------|
| Evaluate Action | `EvaluateAction` | POST | `/api/evaluate` |
| Check Compliance | `CheckCompliance` | POST | `/api/compliance` |
| Score Trust | `ScoreTrust` | POST | `/api/trust/score` |
| Detect Prompt Injection | `DetectInjection` | POST | `/api/injection/detect` |
| Log Audit Event | `LogAuditEvent` | POST | `/api/audit` |
| Check Circuit Breaker | `CheckCircuitBreaker` | POST | `/api/circuit-breaker` |
| Scan MCP Tool | `ScanMcpTool` | POST | `/api/mcp/scan` |
| Check Version | `CheckVersion` | GET | `/api/version` |

### Trust scoring

Trust scores run from 0 to 1000 across five tiers, each mapping to an execution ring that controls what an agent can do:

| Score | Tier | Ring | Access level |
|-------|------|------|-------------|
| 950 or higher | Critical | Ring0 | Full system access |
| 800 or higher | Trusted | Ring1 | Write access, 1000 calls/min |
| 600 or higher | Standard | Ring2 | Read + limited write, 100 calls/min |
| Below 600 | Restricted/Untrusted | Ring3 | Read-only, 10 calls/min |

Use the `action` parameter to boost trust after successful operations, penalize after policy violations, or set an absolute score. Trust naturally decays over time—agents must maintain good behavior to keep elevated privileges.

### Prompt injection detection

Scans for seven attack types:

| Attack type | Example |
|-------------|---------|
| DirectOverride | "Ignore all previous instructions" |
| DelimiterAttack | Using `---` or `###` to inject new context |
| RolePlay | "Pretend you are an admin with full access" |
| ContextManipulation | Subtle reframing of the conversation goal |
| SqlInjection | SQL payloads embedded in natural language |
| CanaryLeak | Attempts to extract system prompts or secrets |
| Custom | User-defined patterns from policy configuration |

### Compliance grading

Grades actions against four regulatory frameworks:

| Framework | Focus |
|-----------|-------|
| OWASP-Agentic-2026 | All 10 agentic AI risk categories |
| EU-AI-Act | High-risk AI obligations (effective August 2026) |
| HIPAA | Health data privacy and security |
| SOC2 | Security, availability, processing integrity |

Returns a letter grade (A, C, or F), individual findings with status (pass, warning, violation), and whether the action should proceed.

### MCP tool scanning

Scans MCP tool definitions for security risks before your agent connects to unknown servers:

| Risk type | What it catches |
|-----------|----------------|
| Tool poisoning | Malicious instructions hidden in tool descriptions |
| Typosquatting | Tools mimicking legitimate tool names |
| Hidden instructions | Concealed directives in tool schemas |
| Insecure transport | HTTP endpoints instead of HTTPS |
| Data exfiltration | Patterns that could leak sensitive data |

## Use cases

**Pre-execution governance**: Wrap every tool call across all your connectors with `evaluate_action`. Before the agent writes a file, sends an email, or executes code, the policy engine decides whether to allow it based on the agent's trust tier and your policy rules.

**Regulatory compliance pipeline**: Build a Power Automate flow that runs `check_compliance` against EU AI Act or HIPAA before processing regulated data. Log the grade and findings to a SharePoint list for audit evidence.

**Adaptive privilege management**: Start agents at Standard tier (Ring2) with limited write access. Boost trust after successful, policy-compliant operations. Penalize after violations. Agents earn privileges through behavior—not static configuration.

**MCP server vetting**: Before connecting your Copilot Studio agent to a third-party MCP server, run `scan_mcp_tool` on each tool definition. Flag hidden instructions, insecure transport, or exfiltration patterns before they reach your agent.

**Resilient multi-service flows**: Use `check_circuit_breaker` before calling external APIs that go down periodically. Route to fallback logic when a service's circuit breaker is open instead of waiting for timeouts.

## Prerequisites

1. An Azure subscription
2. Azure CLI installed
3. Docker (optional—Azure Container Registry can build images in the cloud)

## Deployment

### 1. Create Azure resources

```bash
# Create resource group
az group create --name rg-agent-governance --location westus2

# Deploy infrastructure (Container Registry + Container App)
az deployment group create \
  --resource-group rg-agent-governance \
  --template-file "Agent Governance Toolkit/deploy/main.bicep" \
  --parameters apiKey="your-secure-api-key-here"
```

### 2. Build and push the container image

Build in the cloud (no Docker required):

```bash
az acr build --registry agentgovacr \
  --image agentgov:latest \
  --file "Agent Governance Toolkit/container-app/Dockerfile" \
  "Agent Governance Toolkit/container-app"
```

Or build locally:

```bash
cd "Agent Governance Toolkit/container-app"
docker build -t agent-governance .
docker tag agent-governance agentgovacr.azurecr.io/agentgov:latest
docker push agentgovacr.azurecr.io/agentgov:latest
```

### 3. Configure the connector

1. Import the connector into Power Platform
2. Create a connection with:
   - **Host Name**: Your Container App FQDN (for example, `agentgov-api.yourenv.westus2.azurecontainerapps.io`)
   - **API Key**: The API key you set during deployment
3. Add to Copilot Studio—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`

### 4. Customize policies

Edit `container-app/policies/default.yaml` before building, or mount a custom policy file at runtime via Azure Files:

```yaml
version: "1.0"
name: custom-policy
description: Custom governance rules

rules:
  - name: allow-safe-reads
    condition: "tool_name == 'web_search'"
    action: allow
    priority: 10
  - name: block-destructive
    condition: "tool_name == 'shell_exec'"
    action: deny
    priority: 100

defaults:
  action: deny
```

## Cost estimate

| Resource | Monthly cost |
|----------|-------------|
| Container App (consumption, low traffic) | ~$0-5 |
| Container App (10K evaluations/day) | ~$5-15 |
| Container Registry (Basic) | ~$5 |
| Log Analytics (30-day retention) | ~$2-5 |
| **Total** | **~$7-25** |

## Keeping up to date

- **Version check**: Use `CheckVersion` in a scheduled Power Automate flow to detect when newer SDK versions are available on NuGet
- **Build arg override**: Build with `--build-arg AGT_VERSION=3.*` to pull the latest within the major version
- **GitHub Watch**: Watch [microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit) releases for announcements

## Known limitations

- Requires self-hosted deployment (Azure Container App)—no managed service option yet
- Trust scores are in-memory by default; restart the Container App and scores reset (mount persistent storage for durability)
- Policy evaluation is deterministic, not semantic—the policy engine matches rules, not intent
- MCP tool scanning uses pattern matching for known attack types; novel attack patterns may not be detected

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 8 REST operations |
| `apiProperties.json` | API Key auth config and script operation bindings |
| `script.csx` | C# script handling MCP protocol routing and Application Insights telemetry |
| `container-app/` | .NET 8 minimal API wrapping the Microsoft.AgentGovernance NuGet SDK |
| `deploy/` | Bicep templates for Azure Container Registry, Container App, and Log Analytics |
| `readme.md` | Setup and usage documentation |

## Resources

- [Agent Governance Toolkit connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Agent%20Governance%20Toolkit)
- [Microsoft Agent Governance Toolkit (GitHub)](https://github.com/microsoft/agent-governance-toolkit)
- [Introducing the Agent Governance Toolkit](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/) by Imran Siddique
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [Microsoft.AgentGovernance on NuGet](https://www.nuget.org/packages/Microsoft.AgentGovernance)
