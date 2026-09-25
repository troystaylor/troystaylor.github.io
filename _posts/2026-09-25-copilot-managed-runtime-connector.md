---
layout: post
title: "Drive Copilot Managed Runtime apps from Power Automate and Copilot Studio"
date: 2026-09-25 14:00:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Copilot Managed Runtime, Managed Apps, Custom Connectors, MCP, Copilot Studio, Power Automate, OAuth]
description: "Copilot Managed Runtime is a dual-mode Power Platform custom connector that wraps the same API the ms CLI uses, with 22 typed operations for Power Automate and an MCP endpoint for Copilot Studio agents."
---

[Microsoft Copilot Managed Runtime](https://www.microsoft.com/en-us/copilot/blog/copilot-studio/build-where-you-want-run-with-confidence-now-microsoft-hosts-and-manages-the-code-created-by-copilot/) lets you build web apps with React, TypeScript, and Vite, then host, deploy, and share them through Power Platform. The shipped tooling is a terminal command — `ms`, from the `@microsoft/managed-apps-cli` npm package. [Copilot Managed Runtime](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Managed%20Runtime) wraps the same server API so you can drive that lifecycle from a flow or an agent instead.

The connector runs in two modes off one definition: 22 typed REST operations for Power Automate and Power Apps, and a `/mcp` endpoint that gives a Copilot Studio agent the same surface as tools.

## Finding the API

There's no published REST reference for this service yet, so the surface here was derived from the shipped CLI and then confirmed against the live tenant. The confirmation came from contrasting two responses on an environment-scoped host:

| Request | Response |
|---|---|
| `GET /appframework/apps?api-version=1` | `403` — `InsufficientDelegatedPermissions` |
| `GET /appframework/totally-not-a-route?api-version=1` | `404` — `RouteNotFound` |

An unknown path is rejected by routing. `/appframework/apps` gets past routing and fails only on authorization, so the route is real and serving traffic. The 403 body names exactly what it wants:

```json
{
  "code": "Forbidden",
  "innererror": {
    "code": "InsufficientDelegatedPermissions",
    "message": "Authorization denied: Application missing required delegated permissions: [PowerApps.Apps.Read, ManagedApps.ReadWrite.All, All.All.ReadWrite]"
  }
}
```

`ManagedApps.ReadWrite.All` is a published delegated scope on the first-party Power Platform API application `8578e004-a5c6-46e7-913e-12f58912df43`, and it's user-consentable. That makes this a supported surface rather than an internal backchannel.

## The host isn't the host

Copilot Managed Runtime calls don't go to `api.powerplatform.com`. They go to an environment-scoped host derived from the environment ID: lowercase it, strip the dashes, then split the last two characters off into their own label.

```
b5e65502-f2e4-ecc7-8e66-df670e46b100
  → b5e65502f2e4ecc78e66df670e46b1.00.environment.api.powerplatform.com
```

The swagger declares `api.powerplatform.com` to satisfy Power Platform, and `script.csx` rewrites every request to the real host. That's why every operation takes an `environmentId` and why all of them are listed in `scriptOperations`. Default environments carry a `Default-` prefix on the ID, and the same normalization handles them.

In the designer the `environmentId` comes from a dynamic dropdown, so you pick an environment by name.

## What you get

Every operation except **Get environment dropdown** takes an `environmentId`.

**Apps**

| Operation | Description |
|---|---|
| `ListApps` | List apps in an environment, filtered by `read` or `write` permission, with `$skiptoken` paging |
| `CreateApp` | Create an app and its backing repository |
| `GetApp` | Get one app by ID |
| `DeleteApp` | Delete an app, reporting whether it existed |
| `LocateApp` | Resolve the tenant, environment, and geo hosting an app |

**Build and deploy**

| Operation | Description |
|---|---|
| `BuildApp` | Start a server-side build from the backing repository |
| `GetBuildOperation` | Poll build status and result |
| `GetBuildOperationLog` | Fetch the build log for diagnosing failures |
| `DeployApp` | Deploy a built commit so users can reach it |
| `UploadBuild` | Upload a prebuilt zip; the service commits it and returns a commit SHA |

**Sharing and access**

| Operation | Description |
|---|---|
| `ListShareLinks` | List share links granting access to an app |
| `CreateShareLink` | Create a share link |
| `DeleteShareLink` | Revoke a share link |
| `ListRoleAssignments` | List users and groups assigned roles, with paging |
| `ModifyRoleAssignments` | Grant and revoke roles in one call |

**Connectivity**

| Operation | Description |
|---|---|
| `ListConnectors` | Connectors available as app data sources |
| `GetConnector` | Metadata for one connector |
| `ListConnections` | The caller's existing connections for a connector |

**Repository binding**

| Operation | Description |
|---|---|
| `StartGitHubAuth` | Start authorization for a repository URL; returns a one-time code, verification URI, and session ID |
| `GetGitHubAuthStatus` | Poll the session until it reaches a terminal state |

## Two ways to ship a build

The normal path is `BuildApp`, then poll `GetBuildOperation`, then `DeployApp`.

`UploadBuild` skips the server-side build. Send a zip of the built output, the service commits it and returns a `commitSha`, and you pass that SHA to `DeployApp`. It's the one operation that writes code into the app's repository, and it isn't a substitute for Git — ordinary source control stays `git add`, `git commit`, `git push`, which is what the repository binding operations exist to authorize.

Watch the size. Power Platform caps the total payload through a custom connector at 100 MB while the service itself accepts 500 MB, so the connector ceiling is the one you hit first. The script checks before sending, so an oversized artifact fails immediately with a clear message instead of a late `413`. Over MCP the effective limit is lower still, since the zip has to be base64 encoded and base64 adds roughly a third. For anything larger, run `ms deploy --artifact <file>.zip`.

## Binding a GitHub repository

Pointing an app at your own repository requires the repository owner to authorize the Managed Apps GitHub App, which runs as a device code flow across two operations.

`StartGitHubAuth` takes a full repository URL such as `https://github.com/owner/repo` and parses out the owner, repository, and GitHub base URI. GitHub Enterprise Cloud hosts work too. Show the user the returned `userCode` and `verificationUri`, then poll `GetGitHubAuthStatus` no faster than `pollIntervalSeconds` until `expiresIn` elapses.

| State | Meaning |
|---|---|
| `Pending` | Sign-in isn't finished. Keep polling |
| `Complete` | Authorized. `githubLogin` and `mappingExpiresAt` are populated |
| `Denied` | The user declined. Binding can't proceed |
| `NotFound` | The session is unknown, usually a server restart. Start a new one |
| `Expired` | The window closed before sign-in finished. Start a new one |

Pass the `oauthBaseUri` from `StartGitHubAuth` straight back into `GetGitHubAuthStatus`. It defaults to `https://github.com`, which is wrong for GitHub Enterprise Cloud repositories.

## The agent side

The `/mcp` endpoint speaks JSON-RPC 2.0 and implements `initialize`, `tools/list`, `tools/call`, `resources/list`, `ping`, and the `notifications/*` methods. Tools carry a `managedapps_` prefix and mirror the REST operations, plus one extra: `managedapps_list_environments`, so an agent can find the `environmentId` every other tool needs.

A few requests an agent handles end to end:

- *"Which apps can I edit in the Contoso environment?"* → `managedapps_list_environments`, then `managedapps_list_apps` with `permission: "write"`
- *"Deploy the latest build of the expense tracker."* → `managedapps_list_apps`, `managedapps_build_app`, poll `managedapps_get_build_operation`, then `managedapps_deploy_app`
- *"Why did that build fail?"* → `managedapps_get_build_log`
- *"Who has access to this app?"* → `managedapps_list_role_assignments` and `managedapps_list_share_links`
- *"Connect my app to github.com/contoso/expenses."* → `managedapps_start_github_auth`, show the code and URI, then poll `managedapps_get_github_auth_status`

`managedapps_upload_build` takes the zip as base64 in `zipContentBase64`.

## A note on naming

The product was called Managed Apps before the rename to Copilot Managed Runtime, and the old name survives in identifiers that aren't safe to change:

| Identifier | Value |
|---|---|
| npm packages | `@microsoft/managed-apps-cli`, `@microsoft/managed-apps` |
| API route prefix | `/appframework` |
| User portal domain | `managedapps.cloud.microsoft` |

The connector's operation IDs and MCP tool names keep the `managedapps` prefix for the same reason. Renaming them would break agents and flows already bound to them.

## Licensing

Everyone who runs an app needs coverage, including you while you're developing.

| Option | Behavior |
|---|---|
| Power Apps Premium plan | Covers all app operations without consuming Copilot Credits |
| Copilot Credits | Charged per app launch and per API call, at 0.1 credit per call |

Without sufficient credits a user is warned first and can keep working, then blocked at 20 app operations or five minutes of use, whichever comes first. Power Apps Premium users aren't subject to those limits.

## Deploy it

Register an app in Microsoft Entra ID and add these delegated permissions from the Power Platform API (`8578e004-a5c6-46e7-913e-12f58912df43`):

| Scope | Purpose |
|---|---|
| `ManagedApps.ReadWrite.All` | App lifecycle — required |
| `PowerApps.Apps.Read` | Reading app metadata |
| `PowerApps.Environments.Read` | Environment dropdown |

All three are user-consentable, so admin consent is optional unless your tenant requires it.

Replace `[YOUR_CLIENT_ID]` in `apiProperties.json` with your application ID. Leave `[YOUR_REDIRECT_URL]` alone — the platform generates a per-connector redirect URL on deploy and discards whatever you supply.

Because `scriptOperations` is non-empty, the script and the definition must always travel together. Omit `--script-file` and you get `InvalidScriptDefinitionUrlWithNonNullOperations`.

Create the connector in two steps. A script-enabled connector needs a function app assigned from a regional pool when it's first created, and requesting that during `create` frequently fails:

```powershell
pac auth create --environment <environment-id>

# Step 1 - create without the script
$p = Get-Content apiProperties.json -Raw | ConvertFrom-Json
$p.properties.PSObject.Properties.Remove('scriptOperations')
$p | ConvertTo-Json -Depth 40 | Set-Content "$env:TEMP\noscript.json" -Encoding UTF8

pac connector create `
  --api-definition-file apiDefinition.swagger.json `
  --api-properties-file "$env:TEMP\noscript.json"

# Step 2 - attach the script using the ID returned above
pac connector update `
  --connector-id <connector-id> `
  --api-definition-file apiDefinition.swagger.json `
  --api-properties-file apiProperties.json `
  --script-file script.csx
```

Updating an existing connector is a single `pac connector update`, since it already holds an assigned function app.

A success message means the row was written, not that the definition survived intact. Download it back and check for 22 operations, `x-ms-agentic-protocol: mcp-streamable-1.0` on the `/mcp` path, and the environment dropdowns:

```powershell
pac connector download --connector-id <connector-id> --outputDirectory ./verify
```

The generated redirect URL sits at `properties.connectionParameters.token.oAuthSettings.redirectUrl` in the downloaded file. Register it, or OAuth consent fails:

```powershell
az ad app update --id <appId> --web-redirect-uris `
  "https://global.consent.azure-apim.net/redirect" "<per-connector-url>"
```

That URL encodes both the connector name and the environment, so a connector deployed to dev and prod produces two different URLs and both need registering.

## Caveats

This is public preview, and explicitly volatile. The `microsoft/managed-apps` README states that APIs, templates, and tooling may change before general availability, and there's no versioned public contract for these routes. Treat the connector as tracking a moving target.

Repository create and delete are excluded. The CLI builds routes under `/appframework/git/repositories`, but that path returned `RouteNotFound` during testing while `/appframework/apps` did not — feature-gated or not uniformly deployed. Those operations are left out rather than shipped broken. The GitHub device code routes under `/appframework/github/auth` are a separate surface and are included.

Response schemas are best-effort, reconstructed from the CLI's own mock fixtures and type usage. The script projects responses defensively, reading both flat and `properties`-nested shapes, so a server-side shape change degrades to null fields rather than a hard failure.

`api-version=1` is pinned. Deployment has a newer `manageddevops` backend behind a CLI feature gate; this connector uses the stable `appframework` path.

## When something comes back wrong

| Symptom | Cause | Fix |
|---|---|---|
| `pac connector create` fails when `--script-file` is supplied | A new script-enabled connector couldn't be assigned a function app | Create without the script, then attach it with `pac connector update` |
| `InvalidScriptDefinitionUrlWithNonNullOperations` | `scriptOperations` is declared but no script was uploaded | Add `--script-file script.csx`, or remove `scriptOperations` |
| `401` on every call after deploying | The generated per-connector redirect URL isn't registered | Read it back with `pac connector download` and add it |
| A connection can't be created at all | `clientId` is still `[YOUR_CLIENT_ID]` | Set your real app registration ID and redeploy |
| `403 InsufficientDelegatedPermissions` | The app registration is missing `ManagedApps.ReadWrite.All` | Add the delegated permission and reconsent |
| `UploadBuild` rejects the artifact before sending | The zip exceeds 100 MB, or the content isn't a zip | Use `ms deploy --artifact` for large artifacts |
| `UploadBuild` returns an invalid artifact error | The zip doesn't contain the built output and its configuration file | Package the build output directory, not the source tree |
| `DeployApp` reports no successful build | No green build exists for the commit | Upload or push a commit and wait for its build to succeed |
| GitHub authorization never leaves `Pending` | Sign-in isn't finished at the verification URI | Resend the code and URI; the session ends after `expiresIn` seconds |

Telemetry is off by default. Replace `APP_INSIGHTS_CONNECTION_STRING` in `script.csx` with your connection string to record MCP method calls, tool invocations, and tool errors. Telemetry failures are swallowed and never affect the caller.

## Resources

- [Copilot Managed Runtime connector source](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Managed%20Runtime)
- [Announcing Copilot Managed Runtime](https://www.microsoft.com/en-us/copilot/blog/copilot-studio/build-where-you-want-run-with-confidence-now-microsoft-hosts-and-manages-the-code-created-by-copilot/)
- [What is Copilot Managed Runtime](https://learn.microsoft.com/microsoft-365/managed-apps/)
- [Copilot Managed Runtime SDK overview](https://learn.microsoft.com/microsoft-365/managed-apps/developer/)
- [Copilot Managed Runtime for admins](https://learn.microsoft.com/microsoft-365/admin/manage/apps/)
- [microsoft/managed-apps](https://github.com/microsoft/managed-apps)
- [`@microsoft/managed-apps-cli`](https://www.npmjs.com/package/@microsoft/managed-apps-cli)
- [Power Platform API reference](https://learn.microsoft.com/power-platform/admin/programmability-and-extensibility/powerplatform-api-reference)
- [Write code in a custom connector](https://learn.microsoft.com/connectors/custom-connectors/write-code)
