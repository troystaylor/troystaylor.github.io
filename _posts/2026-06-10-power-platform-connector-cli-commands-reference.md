---
layout: post
title: "Power Platform connector CLI commands reference"
date: 2026-06-10 10:00:00 -0000
categories: [Power Platform, Custom Connectors]
tags: [CLI, pac, paconn, DevOps, API Development]
---

Two CLIs exist for managing Power Platform custom connectors, and each has different strengths. The Power Platform CLI (`pac`) works with solution-aware connectors in Dataverse. The Power Platform Connectors CLI (`paconn`) works with all custom connectors, solution-aware or not. This reference covers every command across both tools so you can pick the right one for each task.

The full reference document lives in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/blob/main/connector-cli-commands.md).

## Quick comparison

| | pac (Power Platform CLI) | paconn (Connectors CLI) |
|---|---|---|
| **Install** | `dotnet tool install --global Microsoft.PowerApps.CLI.Tool` or VS Code extension | `pip install paconn` (requires Python 3.5+) |
| **Auth** | `pac auth create` (supports SPN, interactive, device-code) | `paconn login` (device-code only; no SPN) |
| **Scope** | Solution-aware connectors in Dataverse | All custom connectors (solution-aware or not) |
| **Docs** | [pac connector](https://learn.microsoft.com/power-platform/developer/cli/reference/connector) | [paconn CLI](https://learn.microsoft.com/connectors/custom-connectors/paconn-cli) |

## pac connector commands

These commands operate on solution-aware connectors in Dataverse.

### pac connector init

Scaffolds a new connector project with the required files.

```powershell
pac connector init `
  --connection-template "OAuthAAD" `
  --generate-script-file `
  --generate-settings-file `
  --outputDirectory "MyConnector"
```

| Parameter | Alias | Description |
|---|---|---|
| `--connection-template` | `-ct` | Auth template: `NoAuth`, `BasicAuth`, `ApiKey`, `OAuthGeneric`, `OAuthAAD` |
| `--generate-script-file` | | Switch. Generate an initial `script.csx` file. |
| `--generate-settings-file` | | Switch. Generate an initial `settings.json` file. |
| `--outputDirectory` | `-o` | Output directory for generated files. |

### pac connector create

Creates a new connector row in the Dataverse Connector table.

```powershell
pac connector create `
  --api-definition-file ./apiDefinition.json `
  --api-properties-file ./apiProperties.json `
  --environment 00000000-0000-0000-0000-000000000000
```

| Parameter | Alias | Required | Description |
|---|---|---|---|
| `--api-definition-file` | `-df` | No | Path to the OpenAPI definition file. |
| `--api-properties-file` | `-pf` | No | Path to the API properties file. |
| `--environment` | `-env` | No | Target Dataverse environment (GUID or URL). Defaults to active auth profile. |
| `--icon-file` | `-if` | No | Path to an icon `.png` file. |
| `--script-file` | `-sf` | No | Path to a script `.csx` file. |
| `--settings-file` | | No | Path to a connector settings file. |
| `--solution-unique-name` | `-sol` | No | Solution to add the connector to. |

### pac connector list

Lists connectors registered in Dataverse. Only solution-aware connectors are returned.

```powershell
pac connector list
pac connector list --environment 00000000-0000-0000-0000-000000000000
```

| Parameter | Alias | Required | Description |
|---|---|---|---|
| `--environment` | `-env` | No | Target Dataverse environment (GUID or URL). |
| `--json` | | No | Return output as JSON. |

### pac connector download

Downloads a connector's OpenAPI definition and API properties file.

```powershell
pac connector download `
  --connector-id 00000000-0000-0000-0000-000000000000 `
  --environment 00000000-0000-0000-0000-000000000000 `
  --outputDirectory "MyConnector"
```

| Parameter | Alias | Required | Description |
|---|---|---|---|
| `--connector-id` | `-id` | **Yes** | The connector ID (must be a valid GUID). |
| `--environment` | `-env` | No | Target Dataverse environment (GUID or URL). |
| `--outputDirectory` | `-o` | No | Output directory. |

### pac connector update

Updates an existing connector entity in Dataverse.

```powershell
pac connector update `
  --api-definition-file ./apiDefinition.json `
  --api-properties-file ./apiProperties.json `
  --environment 00000000-0000-0000-0000-000000000000
```

| Parameter | Alias | Required | Description |
|---|---|---|---|
| `--api-definition-file` | `-df` | No | Path to the OpenAPI definition file. |
| `--api-properties-file` | `-pf` | No | Path to the API properties file. |
| `--connector-id` | `-id` | No | Connector ID (GUID). |
| `--environment` | `-env` | No | Target Dataverse environment (GUID or URL). |
| `--icon-file` | `-if` | No | Path to an icon `.png` file. |
| `--script-file` | `-sf` | No | Path to a script `.csx` file. |
| `--settings-file` | | No | Path to a connector settings file. |
| `--solution-unique-name` | `-sol` | No | Solution to add the connector to. |

## pac connection commands

These commands manage Dataverse connections—the runtime instances that link a connector to credentials.

### pac connection create

```powershell
pac connection create `
  --name "MyConnection" `
  --application-id 00000000-0000-0000-0000-000000000000 `
  --tenant-id 00000000-0000-0000-0000-000000000000 `
  --client-secret "secret"
```

| Parameter | Alias | Required | Description |
|---|---|---|---|
| `--name` | `-n` | **Yes** | Connection name. |
| `--application-id` | `-a` | **Yes** | Application (client) ID. |
| `--tenant-id` | `-t` | **Yes** | Tenant ID. |
| `--client-secret` | `-cs` | **Yes** | Client secret. |
| `--environment` | `-env` | No | Target Dataverse environment (GUID or URL). |

### pac connection list

```powershell
pac connection list
pac connection list --environment 00000000-0000-0000-0000-000000000000
```

| Parameter | Alias | Required | Description |
|---|---|---|---|
| `--environment` | `-env` | No | Target Dataverse environment (GUID or URL). |

### pac connection update

```powershell
pac connection update `
  --connection-id 00000000-0000-0000-0000-000000000000 `
  --application-id 00000000-0000-0000-0000-000000000000 `
  --tenant-id 00000000-0000-0000-0000-000000000000 `
  --client-secret "newSecret"
```

| Parameter | Alias | Required | Description |
|---|---|---|---|
| `--connection-id` | `-id` | **Yes** | Connection ID. |
| `--application-id` | `-a` | **Yes** | Application (client) ID. |
| `--tenant-id` | `-t` | **Yes** | Tenant ID. |
| `--client-secret` | `-cs` | **Yes** | Client secret. |
| `--environment` | `-env` | No | Target Dataverse environment (GUID or URL). |

### pac connection delete

```powershell
pac connection delete --connection-id 00000000-0000-0000-0000-000000000000
```

| Parameter | Alias | Required | Description |
|---|---|---|---|
| `--connection-id` | `-id` | **Yes** | Connection ID. |
| `--environment` | `-env` | No | Target Dataverse environment (GUID or URL). |

## paconn commands

The `paconn` CLI is a Python-based tool designed specifically for custom connector lifecycle management. It works with all custom connectors, not just solution-aware ones.

### paconn login

Authenticates to Power Platform using device-code flow.

```bash
paconn login
```

> **Note:** Service Principal authentication is not supported by `paconn`.

### paconn logout

```bash
paconn logout
```

### paconn download

Downloads custom connector files (OpenAPI definition, API properties, icon, script) into a subdirectory named with the connector ID. Also writes a `settings.json` file.

```bash
paconn download
paconn download -e <environment-guid> -c <connector-id>
paconn download -s settings.json
```

| Parameter | Alias | Description |
|---|---|---|
| `--env` | `-e` | Power Platform environment GUID. |
| `--cid` | `-c` | Custom connector ID. |
| `--dest` | `-d` | Destination directory. |
| `--overwrite` | `-w` | Overwrite existing connector and settings files. |
| `--pau` | `-u` | Power Platform URL. |
| `--pav` | `-v` | Power Platform API version. |
| `--settings` | `-s` | Path to `settings.json` (overrides other arguments). |

If environment or connector ID are omitted, the CLI prompts interactively.

### paconn create

Creates a new custom connector from local files. Prints the new connector ID on success.

```bash
paconn create --api-prop apiProperties.json --api-def apiDefinition.swagger.json
paconn create -e <environment-guid> --api-prop apiProperties.json --api-def apiDefinition.swagger.json --icon icon.png --secret <oauth2-secret>
paconn create -s settings.json --secret <oauth2-secret>
```

| Parameter | Alias | Description |
|---|---|---|
| `--api-def` | | Path to the OpenAPI definition JSON. |
| `--api-prop` | | Path to the API properties JSON. |
| `--env` | `-e` | Power Platform environment GUID. |
| `--icon` | | Path to icon file. |
| `--script` | `-x` | Path to script `.csx` file. |
| `--secret` | `-r` | OAuth2 client secret for the connector. |
| `--pau` | `-u` | Power Platform URL. |
| `--pav` | `-v` | Power Platform API version. |
| `--settings` | `-s` | Path to `settings.json`. |

> **Tip:** After creating, update your `settings.json` with the new connector ID before running subsequent updates.

### paconn update

Updates an existing custom connector. Prints the updated connector ID on success.

```bash
paconn update --api-prop apiProperties.json --api-def apiDefinition.swagger.json
paconn update -e <environment-guid> -c <connector-id> --api-prop apiProperties.json --api-def apiDefinition.swagger.json --icon icon.png --secret <oauth2-secret>
paconn update -s settings.json --secret <oauth2-secret>
```

| Parameter | Alias | Description |
|---|---|---|
| `--api-def` | | Path to the OpenAPI definition JSON. |
| `--api-prop` | | Path to the API properties JSON. |
| `--cid` | `-c` | Custom connector ID. |
| `--env` | `-e` | Power Platform environment GUID. |
| `--icon` | | Path to icon file. |
| `--script` | `-x` | Path to script `.csx` file. |
| `--secret` | `-r` | OAuth2 client secret for the connector. |
| `--pau` | `-u` | Power Platform URL. |
| `--pav` | `-v` | Power Platform API version. |
| `--settings` | `-s` | Path to `settings.json`. |

### paconn validate

Validates a swagger/OpenAPI definition file against Power Platform connector rules.

```bash
paconn validate --api-def apiDefinition.swagger.json
paconn validate -s settings.json
```

| Parameter | Alias | Description |
|---|---|---|
| `--api-def` | | Path to the OpenAPI definition JSON. |
| `--pau` | `-u` | Power Platform URL. |
| `--pav` | `-v` | Power Platform API version. |
| `--settings` | `-s` | Path to `settings.json`. |

## Connector file structure

Both CLIs work with the same set of connector artifacts:

```
<connector-id>/
  ├── apiDefinition.swagger.json   # OpenAPI/Swagger definition (required)
  ├── apiProperties.json           # Auth, branding, policies, script ops (required)
  ├── icon.png                     # Connector icon (optional)
  ├── script.csx                   # C# script for custom code (optional)
  └── settings.json                # CLI argument store (optional, not part of connector)
```

## settings.json reference

Used by both `pac connector` and `paconn` to store CLI arguments. The `paconn` variant includes additional Power Apps-specific fields.

```json
{
  "connectorId": "CONNECTOR-ID",
  "environment": "ENVIRONMENT-GUID",
  "apiProperties": "apiProperties.json",
  "apiDefinition": "apiDefinition.swagger.json",
  "icon": "icon.png",
  "script": "script.csx",
  "powerAppsApiVersion": "2016-11-01",
  "powerAppsUrl": "https://api.powerapps.com"
}
```

| Field | Used by | Description |
|---|---|---|
| `connectorId` | paconn | Connector ID. Required for download/update; not needed for create/validate. |
| `environment` | both | Environment GUID. Required for all operations except validate. |
| `apiProperties` | both | Path to `apiProperties.json`. |
| `apiDefinition` | both | Path to the swagger file. |
| `icon` | both | Path to icon file. |
| `script` | both | Path to script `.csx` file. |
| `powerAppsUrl` | paconn | API URL (default: `https://api.powerapps.com`). |
| `powerAppsApiVersion` | paconn | API version (default: `2016-11-01`). |

## Known limitations

| Limitation | Applies to |
|---|---|
| Only solution-aware connectors are shown in `pac connector list`. | `pac` |
| No Service Principal authentication support. | `paconn` |
| Cannot update connector when `stackOwner` is in `apiProperties.json`. Workaround: maintain two versions of artifacts (one with `stackOwner` for certification, one without for dev updates). | `paconn` |
| Limited to custom connectors only; cannot download swagger for first-party connectors. | `paconn` |

## Which CLI should you use?

Use `pac` when you're working with solution-aware connectors and need Service Principal authentication for CI/CD pipelines. Use `paconn` when you need to work with any custom connector regardless of solution awareness, or when you want interactive validation of your OpenAPI definitions.

For most connector development workflows, keep both tools installed. Use `paconn` during local development and validation, then switch to `pac` for automated deployments through your CI/CD pipeline.

## Resources

- [Full CLI commands reference](https://github.com/troystaylor/SharingIsCaring/blob/main/connector-cli-commands.md)
- [pac connector reference](https://learn.microsoft.com/power-platform/developer/cli/reference/connector)
- [pac connection reference](https://learn.microsoft.com/power-platform/developer/cli/reference/connection)
- [paconn CLI documentation](https://learn.microsoft.com/connectors/custom-connectors/paconn-cli)
