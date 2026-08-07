---
layout: post
title: "Update custom connector OAuth identity providers with PAC CLI"
date: 2026-08-07 13:00:00 -0400
categories: [Power Platform, Custom Connectors]
tags: [PAC CLI, OAuth, PKCE, Custom Connectors, Power Automate, Copilot Studio]
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
| `oauth2pkce` | Generic OAuth 2.0 with PKCE |
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

Change `identityProvider` and retain the connection parameters required by the provider. The following example configures `oauth2pkce`:

```json
{
  "properties": {
    "connectionParameters": {
      "token": {
        "type": "oauthSetting",
        "oAuthSettings": {
          "identityProvider": "oauth2pkce",
          "clientId": "YOUR_CLIENT_ID",
          "clientSecret": "YOUR_CLIENT_SECRET",
          "scopes": [
            "read write offline_access"
          ],
          "redirectMode": "GlobalPerConnector",
          "redirectUrl": "https://global.consent.azure-apim.net/redirect/UNIQUE_IDENTIFIER_FOR_THIS_ENVIRONMENT",
          "customParameters": {
            "AuthorizationUrl": {
              "value": "https://api.contoso.com/oauth2/authorize"
            },
            "TokenUrl": {
              "value": "https://api.contoso.com/oauth2/token"
            },
            "RefreshUrl": {
              "value": "https://api.contoso.com/oauth2/token"
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

`oauth2pkce` generates the code verifier for you. It appends `code_challenge` and `code_challenge_method=S256` to the authorization request and sends `code_verifier` on the token exchange, so don't add those values yourself.

The provider requires `AuthorizationUrl`, `TokenUrl`, and `RefreshUrl`. Two optional parameters are also available:

- `IdpHint` sends an `idp_hint` value on the authorization request
- `Audience` sends an `audience` value on the authorization request

`clientSecret` is optional. Omit it for a public client that authenticates with PKCE alone.

Retain the environment-specific `redirectUrl` from the downloaded connector and register the same URL in the provider's OAuth application. Store the client secret outside source control and inject it during deployment.

The provider has no token introspection, so Power Platform learns the token lifetime only from an `expires_in` value in the token response. If the authorization server returns an opaque token without `expires_in`, the connection goes stale instead of refreshing.

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
- [PKCE (RFC 7636)](https://datatracker.ietf.org/doc/html/rfc7636)
- [Power Platform connector CLI commands reference](/power%20platform/custom%20connectors/2026/06/10/power-platform-connector-cli-commands-reference.html)
