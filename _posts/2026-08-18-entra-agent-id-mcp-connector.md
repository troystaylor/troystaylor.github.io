---
layout: post
title: "Govern agent identities with the Entra Agent ID connector"
date: 2026-08-18 11:30:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Entra Agent ID, Microsoft Graph, Custom Connectors, MCP, Copilot Studio, Power Automate, Governance, Workload Identity Federation]
description: "A dual-purpose Power Platform custom connector for Microsoft Entra Agent ID — 73 MCP tools for Copilot Studio and 116 REST operations for Power Automate, covering blueprints, agent identities, agent users, risk, and federation."
---

Agents need identities, and until recently the only way to give them one in Entra was an app registration and a set of conventions. [Microsoft Entra Agent ID](https://learn.microsoft.com/entra/agent-id/) replaces that with first-class objects in Microsoft Graph: blueprints, blueprint principals, agent identities, and agent users. [Entra Agent ID](https://github.com/troystaylor/SharingIsCaring/tree/main/Entra%20Agent%20ID) is a Power Platform custom connector for the whole lifecycle.

One connector, two ways to use it. The `InvokeMCP` operation speaks JSON-RPC 2.0 and exposes 73 tools, 7 resources, and 5 prompts to any MCP client — Copilot Studio, Microsoft Foundry, Agent Framework. The other 116 operations call Graph directly for Power Automate and Logic Apps. Both share one connection and one set of delegated permissions.

## Four layers, created in order

Getting this order wrong is the most common source of opaque `400` responses.

| Order | Resource | Graph collection | What it is |
|---|---|---|---|
| 1 | `agentIdentityBlueprint` | `/applications/microsoft.graph.agentIdentityBlueprint` | The application template for a class of agent, carrying the permissions its agent identities inherit |
| 2 | `agentIdentityBlueprintPrincipal` | `/servicePrincipals/microsoft.graph.agentIdentityBlueprintPrincipal` | The record of a blueprint being added to a tenant, required before any agent identity is created from it here |
| 3 | `agentIdentity` | `/servicePrincipals/microsoft.graph.agentIdentity` | What the agent authenticates as. Conditional Access, sign-in logs, and access reviews all act on this object |
| 4 | `agentUser` | `/users/microsoft.graph.agentUser` | The optional user-shaped account for agents needing a mailbox, a Teams presence, or a place in the org chart |

The `provision_agent` tool runs steps 2 through 4 in a single call and reports what it did at each one, including any step that was already satisfied.

Three rules save a lot of debugging:

- **Create an agent identity with the blueprint's `appId`, not its object `id`.** The `agentIdentityBlueprintId` property takes the client ID. Graph reports the mistake as `AgentIdentity_IncompatibleParentType`.
- **Deletion cascades downward, not upward.** Deleting a blueprint or blueprint principal starts an asynchronous background cleanup that soft-deletes every child agent identity and agent user. It can lag by hours or days and appears in audit logs as *Delete Agent Identities Task*. Deleting an agent identity on its own leaves its agent user behind, so remove that explicitly.
- **Everything soft-deletes with a 30 day restore window.** Restoring a blueprint principal after the cascade has run does not bring its children back — restore each one individually. Soft-deleted objects keep consuming quota until you permanently delete them.

## Tools worth knowing

The 73 MCP tools group into blueprints (13), blueprint principals (6), federation and inherited permissions (6), agent identities (18), agent users (10), lifecycle and governance (7), and risk, inherited permissions, and registry (13, beta).

A handful carry most of the weight:

| Tool | What it does |
|---|---|
| `provision_agent` | The ordered sequence in one call — instantiate the blueprint if needed, create the agent identity with its sponsors, optionally create the agent user and assign its manager |
| `get_agent_overview` | One call returns an agent's identity, blueprint, owners, sponsors, app role grants, group memberships, and agent user |
| `list_blueprint_principal_agents` | The blast radius of a blueprint. Run it before any blueprint deletion |
| `check_blocked_permissions` | Screens a proposed permission set against the list Entra refuses to grant to agents |
| `set_agent_identity_enabled` | The reversible kill switch. Prefer it over deletion when an agent misbehaves |
| `agent_id_graph_request` | A guarded passthrough for anything unnamed, restricted to the identity surface so it can't read mail or files |

Five prompts ship with the server — `onboard_agent`, `federate_third_party_agent`, `audit_agent_governance`, `investigate_agent_risk`, and `offboard_agent`. Each encodes the confirmation gates and ordering constraints so the model doesn't rediscover them. Seven resources expose the lifecycle model, federation patterns, the beta surface and its licensing, the blocked permission list, the error catalogue, the connector's scopes, and the directory roles each operation needs.

## Error codes that tell the model what to do

Graph returns agent identity failures as opaque code strings. Given only a code, a model retries the identical call. The connector maps all 17 documented [error codes](https://learn.microsoft.com/entra/agent-id/identity-platform/error-codes) to the concrete next step and appends it to the failure:

```csharp
["AgentIdentity_AgentBlueprintPrincipalDoesNotExist"] =
    "The blueprint has no blueprint principal in this tenant, which is a prerequisite for creating agent identities from it. Call create_blueprint_principal with the blueprint's appId first, or use provision_agent which handles the ordering.",
["AgentIdentity_CredentialsNotSupported"] =
    "Agent identities cannot hold credentials. Every secret, certificate, and federation trust belongs on the blueprint — use add_blueprint_password or add_blueprint_federated_credential instead.",
```

Two failures arrive without a usable code, so the connector reads the path instead. A `403` on a sponsors collection means Graph supports that route with application permissions only, and the message points at `get_agent_overview`, which expands sponsors from the identity itself. A `400` on `appRoleAssignments` suggests a blocked permission — Entra rejects those without naming the offender — and the message points at `check_blocked_permissions`.

## Third-party agents authenticate without secrets

An agent running on AWS, n8n, or Kubernetes shouldn't hold a client secret. A blueprint doubles as a token factory through workload identity federation: the external platform's own token is exchanged for an Entra token, with nothing stored on the agent.

| Pattern | How it works | Best for |
|---|---|---|
| Workload identity federation | The platform's native token — AWS STS, a Kubernetes service account, a GCP workload identity — is exchanged directly for an Entra token | AWS agents using STS and OIDC, and anywhere federation already exists |
| Auth SDK sidecar | A companion container acquires tokens on the agent's behalf, so agent code never touches credentials | Containerized agents, AWS Bedrock, local Docker Compose development |
| Blueprint as token factory | The blueprint trusts Entra itself and issues tokens for its own agent identities, supporting app-only and on-behalf-of flows | Platforms with a community node that acquires tokens per run, such as n8n |

Configure the trust with `add_blueprint_federated_credential`. Setting `platform: entra_agent_identity` builds the issuer from your tenant ID and uses the agent identity as the subject. Setting `platform: custom` takes the issuer and subject your external provider puts in its tokens — get those from that platform's own configuration, because a wrong value fails at runtime with an unhelpful error. The audience defaults to `api://AzureADTokenExchange`, a blueprint holds at most 20 credentials, and each issuer/subject pair must be unique.

Credentials live on the blueprint, never on the agent identity. Graph reports violations as `AgentIdentity_CredentialsNotSupported`.

## Inheritable permissions change what an audit means

A blueprint grants its agent identities delegated scopes automatically, with no separate consent prompt. Three patterns apply: `enumerated` inherits only the scopes you list, `all_allowed` inherits everything the resource application publishes, and `none` inherits nothing. Prefer `enumerated`.

An agent's effective access is its own assignments plus what its blueprint grants. Auditing only the former understates its reach — read the rest with `list_agent_inherited_permissions`. Moving to a more restrictive pattern means agents still needing a removed scope must obtain fresh consent, so check what's live with `list_inheritable_permissions` before narrowing.

## The beta surface

Four areas run on Graph beta. The connector's `basePath` is `/v1.0` and it rewrites the version segment for these operations only, so v1.0 and beta calls never cross over.

| Area | Tools | Requires |
|---|---|---|
| Agent risk | `list_risky_agents`, `get_risky_agent`, `list_agent_risk_detections`, `get_agent_risk_detection`, `confirm_agents_compromised`, `confirm_agents_safe`, `dismiss_agent_risk` | A Microsoft Agent 365 license, `IdentityRiskyAgent.*`, `IdentityRiskEvent.Read.All`. Security Reader to read, Security Administrator to act |
| Inherited permissions | `list_agent_inherited_permissions` | `Application.Read.All` or `Directory.Read.All` |
| Conditional Access what-if | `evaluate_conditional_access` | `Policy.Read.ConditionalAccess` |
| Agent registry | `list_agent_instances`, `get_agent_instance`, `list_agent_collections`, `quarantine_agent_instance` | `AgentInstance.*`, `AgentCollection.ReadWrite.All`. Agent Registry Administrator |

Containment is not blocking. Confirming an agent compromised raises its risk level, and quarantining moves it in the registry. Neither stops it authenticating — only `set_agent_identity_enabled` does that.

The agent registry is transitional. Microsoft replaces it with the [Agent Registry powered by Microsoft Agent 365](https://learn.microsoft.com/microsoft-agent-365/admin/graph-api) from May 2026. Every tenant reserves two immutable collections: Global (`…0001`) and Quarantined (`…0002`).

Skip the six beta scopes for a v1.0-only deployment.

## In Power Automate

Every operation other than `InvokeMCP` is a plain Graph call — 90 on v1.0 and 27 on beta. An onboarding flow runs the same four layers:

```text
1. CreateBlueprint          → displayName, sponsors@odata.bind
2. CreateBlueprintPrincipal → appId from step 1
3. CreateAgentIdentity      → agentIdentityBlueprintId = appId from step 1, sponsors@odata.bind
4. CreateAgentUser          → identityParentId = id from step 3
5. SetAgentUserManager      → @odata.id pointing at the human manager
```

Reference bodies use the OData bind syntax Graph expects:

```jsonc
// sponsors, on create
{ "sponsors@odata.bind": ["https://graph.microsoft.com/v1.0/users/{userId}"] }

// owners, sponsors, and managers, on $ref endpoints
{ "@odata.id": "https://graph.microsoft.com/v1.0/directoryObjects/{objectId}" }
```

A few limits shape flow design. An agent identity holds one agent user, and a second `CreateAgentUser` against the same `identityParentId` returns `400`. Agent users don't support `$skip`, so page with the returned `@odata.nextLink`. Blueprints, blueprint principals, and agent identities cap at 100 per page and 250 agent identities per blueprint. Soft-deleted objects still count against that ceiling, so `permanently_delete_agent_object` is what actually frees room.

## Setup

Register an Entra application with the redirect URI `https://global.consent.azure-apim.net/redirect`, then add the delegated Graph permissions. The v1.0 set covers `AgentIdentity.*`, `AgentIdentityBlueprint.*`, `AgentIdentityBlueprintPrincipal.*`, `AgentIdUser.ReadWrite.All`, `AppRoleAssignment.ReadWrite.All`, `User.Read`, and `offline_access`. Add `IdentityRiskyAgent.ReadWrite.All`, `IdentityRiskEvent.Read.All`, `Policy.Read.ConditionalAccess`, `AgentInstance.ReadWrite.All`, `AgentCollection.ReadWrite.All`, and `Application.Read.All` only if you want the beta tools. Grant admin consent for all of them.

Then edit `apiProperties.json` with your client ID and secret, import `apiDefinition.swagger.json` through the Maker portal or `paconn create`, and sign in as an Agent ID Administrator. Agent ID Developer works for blueprint creation only.

Watch ownership as closely as role assignments. A principal that creates a blueprint or blueprint principal becomes its owner automatically and can then manage the derived agent identities with no role at all.

## Where it fits

| Connector | Surface | Purpose |
|---|---|---|
| Entra Agent ID (this) | Graph Agent ID APIs | Identity lifecycle — blueprints, principals, agent identities, agent users — plus risk and the registry |
| [Agent 365 Blueprint](/power%20platform/mcp/2026-07-07-agent-365-blueprint-connector.html) | Graph `/applications` | The earlier app-registration approach, plus Work IQ permission grants |
| [Agent 365 MCP](/power%20platform/mcp/2026-07-07-agent-365-mcp-connector.html) | Agent 365 platform | Runtime access to Work IQ tools, MCPManagement, and AdminTools |

Use this connector for identity and governance. Use Agent 365 MCP for what the agent does at runtime.

## Resources

- [Entra Agent ID connector on GitHub](https://github.com/troystaylor/SharingIsCaring/tree/main/Entra%20Agent%20ID)
- [Microsoft Entra Agent ID APIs in Microsoft Graph](https://learn.microsoft.com/graph/api/resources/agentid-platform-overview?view=graph-rest-1.0)
- [What is Microsoft Entra Agent ID?](https://learn.microsoft.com/entra/agent-id/what-is-microsoft-entra-agent-id)
- [Agent identity blueprints](https://learn.microsoft.com/entra/agent-id/agent-blueprint)
- [The agent's user account](https://learn.microsoft.com/entra/agent-id/agent-users)
- [Integrate third-party agents](https://learn.microsoft.com/entra/agent-id/configure-third-party-agents)
- [Secure an Amazon Bedrock agent](https://learn.microsoft.com/entra/agent-id/integrate-aws-bedrock-agent)
- [Secure an n8n agent](https://learn.microsoft.com/entra/agent-id/integrate-n8n-agent)
- [ID Protection for agents](https://learn.microsoft.com/entra/id-protection/concept-risky-agents)
- [Conditional Access for agents](https://learn.microsoft.com/entra/identity/conditional-access/agent-id)
- [Agent identity platform error codes](https://learn.microsoft.com/entra/agent-id/identity-platform/error-codes)
