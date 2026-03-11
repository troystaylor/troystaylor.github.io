---
layout: post
title: "Fix Salesforce custom connector OAuth refresh token failures"
date: 2026-03-11 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Salesforce, OAuth, Troubleshooting, Copilot Studio, Power Automate]
---

A Power Platform custom connector that works perfectly on the first request and then breaks an hour later is a frustrating puzzle. The connection tests fine, every action returns data, and then the access token expires and the connector goes silent.

The root cause: Power Platform's default refresh token request doesn't include `client_secret` in the body, but Salesforce requires it.

## How OAuth refresh tokens work

When a connector authenticates with OAuth 2.0, the authorization server returns both an access token and a refresh token. The access token is short-lived (Salesforce defaults to one hour). When it expires, the connector sends the refresh token to the token endpoint to get a new access token.

[RFC 6749 Section 6](https://datatracker.ietf.org/doc/html/rfc6749#section-6) defines only three parameters for a refresh request:

- `grant_type` (required, value: `refresh_token`)
- `refresh_token` (required)
- `scope` (optional)

Client authentication is handled separately. The spec says confidential clients **MUST** authenticate when refreshing, but the preferred method is HTTP Basic authentication in the `Authorization` header. Including `client_id` and `client_secret` in the request body is an alternative the spec describes as "NOT RECOMMENDED" ([RFC 6749 Section 2.3.1](https://datatracker.ietf.org/doc/html/rfc6749#section-2.3.1)).

[RFC 9700](https://datatracker.ietf.org/doc/html/rfc9700) (the January 2025 OAuth Security Best Current Practice) goes further. Section 2.5 RECOMMENDS asymmetric cryptography for client authentication, such as mutual TLS or signed JWTs, because authorization servers then don't need to store sensitive symmetric keys. The direction of the spec is moving away from shared secrets entirely, which makes Salesforce's body-parameter requirement an even larger deviation from current best practice.

## Where Salesforce diverges

Salesforce requires `client_id` and `client_secret` as body parameters in the refresh POST request, not in the `Authorization` header. The [Salesforce help documentation](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_refresh_token_flow.htm&type=5) shows this explicitly:

```http
POST /services/oauth2/token HTTP/1.1
Host: login.salesforce.com
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token=your_refresh_token
&client_id=your_client_id
&client_secret=your_client_secret
```

This is a valid implementation choice, but it means any client that relies on the spec's default behavior (header-based auth or no `client_secret` in the body) will fail when refreshing Salesforce tokens.

## Why the default connector behavior breaks

Power Platform custom connectors handle OAuth token refresh automatically. When the access token expires, the platform sends a refresh request using its default template: `grant_type`, `refresh_token`, and `redirect_uri`. No `client_secret`.

Salesforce rejects this request because it can't authenticate the client without the secret. The connector returns an authentication error instead of silently refreshing, and every subsequent call fails.

## The fix: customize refreshBodyTemplate

The solution is to add `refreshBodyTemplate` to your connector's `apiProperties.json` file. This property lets you override the default refresh request body with a template that includes `client_secret`.

Here's the relevant section from the [fixed apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Salesforce%20MCP/apiProperties.json):

```json
{
  "properties": {
    "connectionParameters": {
      "token": {
        "type": "oauthSetting",
        "oAuthSettings": {
          "identityProvider": "oauth2generic",
          "clientId": "YOUR_CLIENT_ID",
          "scopes": ["refresh_token api"],
          "redirectMode": "GlobalPerConnector",
          "properties": {
            "IsFirstParty": "False",
            "IsOnbehalfofLoginSupported": false
          },
          "customParameters": {
            "authorizationUrlTemplate": {
              "value": "https://instance.my.salesforce.com/services/oauth2/authorize"
            },
            "authorizationUrlQueryStringTemplate": {
              "value": "?response_type=code&client_id={ClientId}&redirect_uri={RedirectUrl}&scope={Scopes}&state={State}"
            },
            "tokenUrlTemplate": {
              "value": "https://instance.my.salesforce.com/services/oauth2/token"
            },
            "tokenBodyTemplate": {
              "value": "grant_type=authorization_code&code={Code}&client_id={ClientId}&client_secret={ClientSecret}&redirect_uri={RedirectUrl}"
            },
            "refreshUrlTemplate": {
              "value": "https://instance.my.salesforce.com/services/oauth2/token"
            },
            "refreshBodyTemplate": {
              "value": "grant_type=refresh_token&refresh_token={RefreshToken}&client_id={ClientId}&client_secret={ClientSecret}"
            }
          }
        }
      }
    }
  }
}
```

The critical addition is `refreshBodyTemplate` with `&client_secret={ClientSecret}`. Power Platform replaces `{ClientSecret}` with the actual secret value at runtime.

Notice that `tokenBodyTemplate` also includes `client_secret`, which follows the same pattern for the initial token exchange.

## Where to find the documentation

One thing that makes this harder to troubleshoot is the documentation gap around these custom parameters.

The [Power Platform connection parameters documentation](https://learn.microsoft.com/en-us/connectors/custom-connectors/connection-parameters#oauth-20) describes the Refresh URL field in the connector wizard but doesn't explain how to customize the refresh body. The `refreshBodyTemplate`, `tokenBodyTemplate`, and related `customParameters` properties are part of the `apiProperties.json` schema used by the [Power Platform Connectors CLI](https://learn.microsoft.com/en-us/connectors/custom-connectors/paconn-cli), but they're not prominently documented for the web-based wizard.

The [Copilot Studio authentication configuration page](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configuration-authentication-azure-ad) does document the **Refresh body template** field with an example that includes `client_secret`:

```
refresh_token={RefreshToken}&redirect_uri={RedirectUrl}&grant_type=refresh_token&client_id={ClientId}&client_secret={ClientSecret}
```

## Diagnosing the problem

If your Salesforce custom connector works initially but fails after the access token expires, check for these signs:

1. **Actions succeed immediately after creating the connection** but fail after roughly one hour (Salesforce's default token lifetime).
2. **Re-creating the connection fixes it temporarily** because you get a fresh access token.
3. **Error messages reference authentication or authorization** rather than the API action itself.

## Key takeaways

- **Salesforce requires `client_secret` in the refresh POST body**, which differs from the OAuth 2.0 spec's preferred approach of HTTP Basic authentication.
- **Power Platform's default refresh template doesn't include `client_secret`**, so you must override it with `refreshBodyTemplate` in `apiProperties.json`.
- **Use the CLI tooling** (`paconn`) to deploy connectors with custom `apiProperties.json` settings that aren't exposed in the web wizard.
- **Test token refresh explicitly**, not just the initial connection. The connector should still work after the access token's one-hour lifetime expires.

The complete connector files, including the corrected `apiProperties.json`, are available in the [SharingIsCaring/Salesforce MCP repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20MCP).
