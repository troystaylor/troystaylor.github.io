---
layout: post
title: "Update custom connector OAuth identity providers with PAC CLI"
date: 2026-08-07 13:00:00 -0400
categories: [Power Platform, Custom Connectors]
tags: [PAC CLI, OAuth, Custom Connectors, Salesforce, Power Automate, Copilot Studio]
description: "Use Power Platform CLI to set an OAuth identity provider in apiProperties.json when the Power Platform custom connector UI doesn't offer the provider you need."
---

Use Power Platform CLI (`pac`) to configure an OAuth identity provider that isn't available in the Power Platform custom connector designer. The process downloads the connector's API properties, updates `identityProvider`, and uploads the modified file.

## OAuth identity provider configuration

The connector's OAuth configuration is stored in `properties.connectionParameters.token.oAuthSettings` in `apiProperties.json`:

```json
{
  "properties": {
    "connectionParameters": {
      "token": {
        "type": "oauthSetting",
        "oAuthSettings": {
          "identityProvider": "oauth2"
        }
      }
    }
  }
}
```

The `identityProvider` value selects the runtime OAuth implementation. Connector artifacts use identifiers including:

| Identifier | Use |
|---|---|
| `aad` | Microsoft Entra ID OAuth |
| `oauth2` | Generic OAuth 2.0 |
| `oauth2generic` | Template-based generic OAuth configuration |
| `DocuSign` | DocuSign-specific OAuth behavior |
| `SalesforceV2` | Salesforce OAuth |

Use the identifier and connection parameters from a tested connector artifact or provided by Microsoft support for the target provider.

## Prerequisites

- Power Platform CLI
- An authenticated PAC CLI profile
- A solution-aware custom connector
- The connector's Dataverse row ID
- Permission to update the connector
- The provider's OAuth client ID and client secret

`pac connector` commands operate on solution-aware connectors stored in Dataverse. Use `paconn` for a custom connector that isn't solution-aware.

## 1. Authenticate and get the connector ID

Authenticate to the target environment:

```powershell
pac auth create --environment "https://contoso.crm.dynamics.com"
```

List the solution-aware connectors:

```powershell
pac connector list `
  --environment "https://contoso.crm.dynamics.com" `
  --json
```

## 2. Download the connector

Use the connector ID returned by `pac connector list`:

```powershell
pac connector download `
  --connector-id "00000000-0000-0000-0000-000000000000" `
  --environment "https://contoso.crm.dynamics.com" `
  --outputDirectory ".\connector"
```

Back up the API properties file:

```powershell
Copy-Item `
  -Path ".\connector\apiProperties.json" `
  -Destination ".\connector\apiProperties.backup.json"
```

## 3. Update apiProperties.json

Open `connector\apiProperties.json`. Find:

```text
properties.connectionParameters.token.oAuthSettings
```

Change `identityProvider` and retain the connection parameters required by the provider. The following example configures `SalesforceV2`:

```json
{
  "properties": {
    "connectionParameters": {
      "token": {
        "type": "oauthSetting",
        "oAuthSettings": {
          "identityProvider": "SalesforceV2",
          "clientId": "YOUR_CLIENT_ID",
          "clientSecret": "YOUR_CLIENT_SECRET",
          "scopes": [
            "api refresh_token"
          ],
          "redirectMode": "GlobalPerConnector",
          "redirectUrl": "https://global.consent.azure-apim.net/redirect/UNIQUE_IDENTIFIER_FOR_THIS_ENVIRONMENT",
          "customParameters": {
            "LoginUri": {
              "value": "https://login.salesforce.com"
            }
          },
          "properties": {
            "IsFirstParty": "False",
            "IsOnbehalfofLoginSupported": false
          }
        }
      }
    }
  }
}
```

Retain the environment-specific `redirectUrl` from the downloaded connector and register the same URL in the provider's OAuth application. For Salesforce:

- Use `https://login.salesforce.com` for production
- Use `https://test.salesforce.com` for a sandbox
- Use `api refresh_token` for Salesforce REST APIs
- Use `mcp_api refresh_token` for Salesforce Hosted MCP Servers

Store the client secret outside source control and inject it during deployment.

## 4. Upload the updated API properties

Update only the API properties file:

```powershell
pac connector update `
  --connector-id "00000000-0000-0000-0000-000000000000" `
  --environment "https://contoso.crm.dynamics.com" `
  --api-properties-file ".\connector\apiProperties.json"
```

If the OpenAPI definition also changed, include it in the update:

```powershell
pac connector update `
  --connector-id "00000000-0000-0000-0000-000000000000" `
  --environment "https://contoso.crm.dynamics.com" `
  --api-properties-file ".\connector\apiProperties.json" `
  --api-definition-file ".\connector\apiDefinition.swagger.json"
```

## 5. Verify the identity provider

Download the connector again to a separate directory:

```powershell
pac connector download `
  --connector-id "00000000-0000-0000-0000-000000000000" `
  --environment "https://contoso.crm.dynamics.com" `
  --outputDirectory ".\connector-verify"
```

Confirm that `connector-verify\apiProperties.json` contains the expected provider.

Test the connection:

1. Delete any test connection created with the old OAuth configuration
2. Create a new connection for the custom connector
3. Complete the provider's sign-in and consent flow
4. Run a connector action
5. Test again after the access token expires to confirm refresh works

## 6. Roll back the update

If sign-in or refresh fails, restore the downloaded backup:

```powershell
pac connector update `
  --connector-id "00000000-0000-0000-0000-000000000000" `
  --environment "https://contoso.crm.dynamics.com" `
  --api-properties-file ".\connector\apiProperties.backup.json"
```

## Resources

- [PAC CLI connector reference](https://learn.microsoft.com/power-platform/developer/cli/reference/connector)
- [Create a custom connector with the CLI](https://learn.microsoft.com/connectors/custom-connectors/paconn-cli)
- [Microsoft Power Platform Connectors samples](https://github.com/microsoft/PowerPlatformConnectors)
- [DocuSign identity provider sample](https://github.com/microsoft/PowerPlatformConnectors/blob/dev/certified-connectors/DocuSignDemo/apiProperties.json)
- [Template-based OAuth sample](https://github.com/microsoft/PowerPlatformConnectors/blob/dev/certified-connectors/GetAccept/apiProperties.json)
- [Salesforce Hosted MCP connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20Hosted%20MCP)
- [Power Platform connector CLI commands reference](/power%20platform/custom%20connectors/2026/06/10/power-platform-connector-cli-commands-reference.html)
