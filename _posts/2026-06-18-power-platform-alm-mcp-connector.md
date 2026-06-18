---
layout: post
title: "Power Platform ALM MCP connector for solution and pipeline management"
date: 2026-06-18 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Power Platform, MCP, Custom Connectors, Copilot Studio, Power Automate, ALM, Solutions, Pipelines, DevOps]
description: "Dual-mode Power Platform custom connector that manages solutions and deployment pipelines across environments via the Dataverse Web API and Power Platform Admin API, with an MCP endpoint for Copilot Studio and typed operations for Power Automate."
---

Solution management in Power Platform still involves too many portal clicks. Export a solution, switch environments, import it, publish customizations, check the pipeline status — each step is a separate browser session. This connector collapses that workflow into operations that Copilot Studio agents and Power Automate flows can call directly.

The connector is dual-mode: a single `POST /mcp` endpoint for Copilot Studio agents, plus typed Power Automate operations with full schemas, dynamic dropdowns, and IntelliSense. It talks to the Dataverse Web API for solution and pipeline operations, and the Power Platform Admin API for environment discovery.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Platform%20ALM).

## What it does

The connector covers two ALM domains: solution lifecycle and deployment pipelines.

### Solution management

| Operation | MCP tool | API call |
|-----------|----------|----------|
| List Solutions | `alm_list_solutions` | `GET /api/data/v9.2/solutions` |
| Get Solution | `alm_get_solution` | `GET /api/data/v9.2/solutions?$filter=uniquename eq '{name}'` |
| Export Solution | `alm_export_solution` | `POST /api/data/v9.2/ExportSolution` |
| Import Solution | `alm_import_solution` | `POST /api/data/v9.2/ImportSolution` |
| Publish Customizations | `alm_publish_customizations` | `POST /api/data/v9.2/PublishAllXml` |
| Delete Solution | `alm_delete_solution` | `DELETE /api/data/v9.2/solutions({id})` |
| Set Solution Version | `alm_set_solution_version` | `PATCH /api/data/v9.2/solutions({id})` |
| Clone as Patch | `alm_clone_as_patch` | `POST /api/data/v9.2/CloneAsPatch` |
| Clone as Solution | `alm_clone_as_solution` | `POST /api/data/v9.2/CloneAsSolution` |
| Delete and Promote | `alm_delete_and_promote` | `POST /api/data/v9.2/DeleteAndPromote` |

The import operation supports holding solutions for staged upgrades. Export a solution as managed, import it as a holding solution in the target environment, validate, then call Delete and Promote to complete the upgrade. That three-step pattern is the safest way to push managed solutions without downtime, and now it's automatable in a single flow.

### Pipeline management

| Operation | MCP tool | Entity |
|-----------|----------|--------|
| List Pipelines | `alm_list_pipelines` | `deploymentpipelines` |
| List Pipeline Stages | `alm_list_pipeline_stages` | `deploymentstages` |
| Deploy to Pipeline | `alm_deploy_to_pipeline` | `deploymentstageruns` |
| Get Deployment Status | `alm_get_deployment_status` | `deploymentstageruns` |
| List Deployment History | `alm_list_deployment_history` | `deploymentstageruns` |

If your org already uses Power Platform pipelines, these operations let you trigger deployments and poll status from a flow or agent instead of the maker portal.

## Architecture

### Authentication

The connector uses OAuth 2.0 against `https://api.powerplatform.com` via the `aad` identity provider. It calls the Power Platform Admin API to list environments and resolve Dataverse org URLs, then forwards the auth token to individual Dataverse Web APIs via `Context.SendAsync`.

### Dynamic dropdowns

Three internal operations populate dropdowns in Power Automate:

- **GetEnvironmentDropdown** — filters to Dataverse-provisioned environments
- **GetSolutionDropdown** — filters to unmanaged solutions in the selected environment
- **GetPipelineDropdown** — populates pipelines for the selected host environment

These eliminate the need to look up environment IDs or solution GUIDs manually.

### Dual-mode pattern

The connector follows the standard dual-mode layout:

- `basePath: "/"` with the MCP endpoint at `path: "/mcp"`
- `x-ms-agentic-protocol: "mcp-streamable-1.0"` on the MCP operation
- All operations routed through `script.csx` via `scriptOperations` in `apiProperties.json`

## Example Copilot Studio prompts

With the MCP server attached as an action, a Copilot Studio agent can handle ALM tasks conversationally:

- "List all unmanaged solutions in the dev environment"
- "Export the Contoso CRM solution as managed"
- "Import the solution into production as a holding solution"
- "What's the status of the last pipeline deployment?"
- "Set the solution version to 2.1.0.0 and export it"

## Configuration

1. Create an Azure AD app registration (multi-tenant) with delegated permissions for Power Platform API:
   - `EnvironmentManagement.Environments.Read`
   - `EnvironmentManagement.Settings.Read`
   - `EnvironmentManagement.Settings.ReadWrite`
   - `AppManagement.ApplicationPackages.Read`
   - `AppManagement.ApplicationPackages.Install`

2. Add redirect URI: `https://global.consent.azure-apim.net/redirect`

3. Create a service principal and grant admin consent:

```bash
az ad sp create --id <appId>
az ad app permission grant --id <appId> --api 8578e004-a5c6-46e7-913e-12f58912df43 --scope "EnvironmentManagement.Environments.Read EnvironmentManagement.Settings.Read EnvironmentManagement.Settings.ReadWrite AppManagement.ApplicationPackages.Read AppManagement.ApplicationPackages.Install"
```

4. Replace `[INSERT_YOUR_CLIENT_ID]` in `apiProperties.json` with your app's client ID

5. Optionally replace `[INSERT_YOUR_APP_INSIGHTS_CONNECTION_STRING]` in `script.csx` for telemetry

6. Deploy with PAC CLI:

```powershell
pac connector create --api-definition-file apiDefinition.swagger.json --api-properties-file apiProperties.json --script-file script.csx
```

## Known limitations

- **Solution export size**: Custom connectors have an approximate 100 MB request body limit. Most solutions are well under this.
- **Pipeline entity names**: `deploymentpipelines`, `deploymentstages`, and `deploymentstageruns` are the expected Dataverse entity logical names. Verify against your environment's metadata if pipelines aren't returning results.
- **Token forwarding**: The `api.powerplatform.com` token is forwarded to Dataverse org URLs. If you see 401 errors during testing, the auth resource may need to change to a per-environment Dataverse org URL.

## Resources

- [solution EntityType](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/reference/solution)
- [ExportSolution Action](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/reference/exportsolution)
- [ImportSolution Action](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/reference/importsolution)
- [Pipelines in Power Platform](https://learn.microsoft.com/power-platform/alm/pipelines)
- [PAC CLI pipeline commands](https://learn.microsoft.com/power-platform/developer/cli/reference/pipeline)
- [Power Platform Admin API](https://learn.microsoft.com/power-platform/admin/programmability-and-extensibility/powerplatform-api-reference)
