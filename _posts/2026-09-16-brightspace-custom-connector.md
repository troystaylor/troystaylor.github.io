---
layout: post
title: "Reach the Brightspace Valence API from Power Automate and Copilot Studio with one connector"
date: 2026-09-16 13:30:00 -0400
categories: [Power Platform, Custom Connectors, MCP]
tags: [Brightspace, D2L, Valence, Custom Connectors, MCP, Copilot Studio, Power Automate, OAuth]
description: "Brightspace is a custom connector that gives Power Automate 30 typed actions against the D2L Valence API and gives Copilot Studio an MCP endpoint that can call any Brightspace route."
---

A learning management system holds the answers to most operational questions a school has. Who's enrolled, who submitted, who's failing, which course shells exist for next term. Getting at those answers from Power Automate has meant hand-rolling HTTP calls against the D2L Valence API, guessing at versions, and re-solving paging every time.

[Brightspace](https://github.com/troystaylor/SharingIsCaring/tree/main/Brightspace) is a custom connector that covers both audiences from one definition.

| Audience | Surface | What they get |
|---|---|---|
| Power Automate, Power Apps | 30 typed REST actions | Named actions with real schemas, IntelliSense, and field pickers |
| Copilot Studio | MCP endpoint at `/mcp` | `scan` / `launch` / `sequence` over the entire Brightspace API, plus version and paging helpers |

The REST half covers the operations people build flows against. The MCP half isn't limited to those. `launch_brightspace` calls any Brightspace route, so an agent never stalls on an operation nobody thought to declare in the Swagger.

## Three things to collect before you deploy

**The host name.** Brightspace has no fixed tenant host pattern. It's whatever hostname your institution runs on, such as `school.brightspace.com`.

**An OAuth 2.0 application registration.** Create it in **Admin Tools** > **Manage Extensibility** > **OAuth 2.0** > **Register an app**. Pick the **Authorization grant** workflow, enable **Prompt for user consent**, and enable **refresh tokens**. Skipping refresh tokens breaks every connection the moment the access token expires. Brightspace returns a Client ID and Client Secret.

Brightspace's documentation never mentions PKCE, so don't assume it's supported. This connector uses a confidential client with a client secret, matching the documented Authorization Code Grant.

**The scopes** the registration is allowed to request. More on those below.

### The redirect URI is a chicken-and-egg step

Power Platform generates the redirect URL when the connector is created, so you can't register it in Brightspace up front. Deploy first with the `[YOUR_REDIRECT_URL]` placeholder in place, then read the generated value back:

```powershell
pac connector download --connector-id <id> --outputDirectory ./verify
# properties.connectionParameters.token.oAuthSettings.redirectUrl
```

The result looks like this:

```text
https://global.consent.azure-apim.net/redirect/new-5fbrightspace-5ff5dc2f63c87a6469
```

That URL encodes both the connector name and the environment, so a connector deployed to dev and prod produces two different redirect URLs. Register both on the Brightspace application.

## `core:*:*` is not a master key

Brightspace scopes are `<resource-group>:<resource>:<action>`, space-delimited, with `*` and comma wildcards (`users:userdata:create,read,update`, no spaces around the commas).

`core:*:*` reads like an admin scope and isn't one. It's the general fallback, and it only covers API actions that have no specific scope assigned yet. Any action that does have a specific scope still needs that scope explicitly. Ship both: the fallback for the unscoped remainder, and the specific scopes for everything else.

The connector's default set is read-focused, with write access to grades and announcements:

| Area | Read | Write |
|---|---|---|
| Users | `users:userdata:read` `users:profile:read` `users:own_profile:read` | `users:userdata:create,update,delete` |
| Organization | `organizations:organization:read` | |
| Courses, org structure | `orgunits:course:read` `managecourses:courses:read` | `orgunits:course:create,update,delete` `managecourses:courses:write` |
| Enrollments | `enrollment:own_enrollment:read` `enrollment:orgunit:read` | `enrollment:orgunit:create,delete` |
| Grades | `grades:gradeobjects:read` `grades:gradevalues:read` `grades:gradecategories:read` | `grades:gradevalues:write` `grades:gradeobjects:write` |
| Content | `content:toc:read` `content:modules:readonly` `content:topics:readonly` | `content:topics:manage` `content:modules:manage` |
| Assignments | `dropbox:folders:read` | `dropbox:folders:write` |
| Announcements | `news:newsitems:read` | `news:newsitems:manage` |
| Discussions | `discussions:forums:readonly` `discussions:topics:readonly` `discussions:posts:readonly` | `discussions:posts:manage` |
| Quizzes | `quizzing:quizzes:read` `quizzing:attempts:read` | `quizzing:quizzes:write` |

Add the write scopes you need to both `apiProperties.json` and the Brightspace registration. A token can only request scopes the registration already holds.

Scopes gate which API actions the token may call. They don't widen what the user can do, because the signed-in user's role in each org unit still decides that. A `403` almost always means a permissions problem rather than a malformed request.

## Versions are pinned to the oldest supported release

Brightspace versions each product component separately, and the version sits in the path: `/d2l/api/{component}/{version}/{path}`.

| Component | Covers | Pinned version |
|---|---|---|
| `lp` | Learning Platform: users, org structure, courses, enrollments | **1.49** |
| `le` | Learning Environment: grades, content, assignments, discussions, quizzes, news | **1.82** |

Both pin to the oldest version D2L still supports, so the connector works on any current tenant. Later contract versions are supersets, so raise a version only when you need a route added after that point.

REST actions expose `version` as an advanced path parameter, pre-filled with the pinned default. MCP tools read it from the `LP_VERSION` and `LE_VERSION` constants at the top of `script.csx`, so changing it there shifts every tool at once. To see what your tenant supports, call the **Get API Versions** action or have the agent call `check_brightspace_versions`.

## 30 typed actions, and only three of them run through the script

The typed actions cover users, org structure, courses, enrollments, grades, content, assignments, announcements, discussions, and quizzes:

| Action | Route |
|---|---|
| Get API Versions | `GET /d2l/api/versions/` |
| Get Current User | `GET /lp/{version}/users/whoami` |
| List Users | `GET /lp/{version}/users/` |
| Find User By Username | `GET /lp/{version}/users/?userName=` |
| Find Users By Org Defined ID | `GET /lp/{version}/users/?orgDefinedId=` |
| Get Org Unit Descendants | `GET /lp/{version}/orgstructure/{orgUnitId}/descendants/paged/` |
| Get My Enrollments | `GET /lp/{version}/enrollments/myenrollments/` |
| Enroll User | `POST /lp/{version}/enrollments/` |
| Get Grade Objects | `GET /le/{version}/{orgUnitId}/grades/` |
| Set Grade Value | `PUT /le/{version}/{orgUnitId}/grades/{gradeObjectId}/values/{userId}` |
| Get Assignment Submissions | `GET /le/{version}/{orgUnitId}/dropbox/folders/{folderId}/submissions/` |
| Create Announcement | `POST /le/{version}/{orgUnitId}/news/` |
| Get Quizzes | `GET /le/{version}/{orgUnitId}/quizzes/` |

That's a sample. The [readme](https://github.com/troystaylor/SharingIsCaring/blob/main/Brightspace/readme.md) lists all 30.

Only three operations run through `script.csx`: `InvokeMCP`, which is the MCP server itself, and the two user-lookup actions. Everything else passes straight through to Brightspace, because the Swagger paths are the real Brightspace paths. There's nothing to transform, and a script hop would only add a failure mode.

The two user-lookup actions exist because `GET /users/` changes its response shape depending on which query parameter it receives:

| Parameter | Response |
|---|---|
| `userName` | A single user object |
| `orgDefinedId` or `externalEmail` | A plain array of users |
| none, or `bookmark` | A bookmark-paged result set |

Precedence is `orgDefinedId`, then `userName`, then `externalEmail`, then `bookmark`, regardless of the order in the URL. One Swagger operation can't describe three shapes honestly, so the connector declares three operations with accurate response schemas and the script maps the lookup variants back onto the real route.

## Five MCP tools cover 57 operations

Add the connector to a Copilot Studio agent as an MCP tool and it exposes five tools:

| Tool | Purpose |
|---|---|
| `scan_brightspace` | Find the right operation from a natural-language intent. Always call first. |
| `launch_brightspace` | Execute any Brightspace route, with `{placeholder}` segments filled in. |
| `sequence_brightspace` | Run up to 20 operations in one call. |
| `check_brightspace_versions` | Compare the pinned versions against what the tenant supports. |
| `follow_brightspace_page` | Fetch the next page of a `Next`/`Objects` response. |

The capability index embedded in the script describes 57 operations across ten domains. Scanning that index costs a few hundred tokens instead of the tens of thousands that 57 typed tools would add to every agent turn. `launch_brightspace` isn't restricted to the index either. It calls any route and warns when the endpoint is unrecognized, so the index serves discovery rather than enforcement.

Here's how an agent answers "what's the average grade on the midterm in BIO-101?":

1. `scan_brightspace("find a course by name")` returns `get_org_unit_descendants`
2. `launch_brightspace` on `/lp/1.49/orgstructure/6606/descendants/paged/?ouTypeId=3` finds BIO-101 as org unit `7421`
3. `scan_brightspace("grade items in a course")` returns `list_grade_objects`
4. `launch_brightspace` on `/le/1.82/7421/grades/` finds the midterm as grade object `19`
5. `launch_brightspace` on `/le/1.82/7421/grades/19/values/` returns grades, paged by `Next`
6. `follow_brightspace_page` runs until `Next` is empty

## Brightspace has two paging schemes

They're not interchangeable, and picking the wrong one silently returns one page.

**Bookmark paging** returns a `PagedResultSet`:

```json
{
  "PagingInfo": { "Bookmark": "...", "HasMoreItems": true },
  "Items": [ ... ]
}
```

Pass `PagingInfo.Bookmark` back as the `bookmark` query parameter and stop when `HasMoreItems` is `false`. List Users, Get My Enrollments, Get Org Unit Enrollments, Get Org Unit Children, and Get Org Unit Descendants use this scheme.

**URL paging** returns an `ObjectListPage`:

```json
{
  "Next": "https://...",
  "Objects": [ ... ]
}
```

Follow the `Next` URL verbatim, since it already carries the filters you used, and stop when `Next` is empty. Get Quizzes, the paged classlist, and per-grade-item values use this scheme.

Agents should use `follow_brightspace_page` for the second scheme. It rejects any URL pointing at a different host, so a returned URL can't redirect the bearer token somewhere else.

Get Classlist is unbounded and returns every member of a course in one response. For large courses, prefer Get Org Unit Enrollments, which is bookmark-paged.

## Conventions worth knowing before the first `403`

| Topic | Detail |
|---|---|
| Identifiers | `D2LID` values are positive 64-bit integers. Passing a non-numeric value into a route segment can make Brightspace match the wrong route handler, not just fail. |
| Org units | A course is an org unit. So is a department, a semester, and the organization itself. `orgUnitId` is used throughout. |
| Dates | UTC ISO 8601 with milliseconds: `yyyy-MM-ddTHH:mm:ss.fffZ`, every element zero-padded. Some fields are Unix timestamps instead. |
| Rich text in | `{ "Content": "...", "Type": "Text" }` where `Type` is `Text` or `Html` |
| Rich text out | `{ "Text": "...", "Html": "..." }`, a different shape from the input |
| Rate limits | Token-bucket. Watch `X-Rate-Limit-Remaining`, `X-Request-Cost`, and `Retry-After`. A `429` means the bucket is empty, and the MCP layer retries those automatically. |
| Errors | RFC 7807 problem details: `{ "type", "status", "title", "detail", "instance" }` |
| `404` isn't always missing | It can also mean the tool isn't enabled for that tenant. Not every deployment has quizzes or ePortfolio. |
| `403` versus empty | Most routes return `403` when the user can't see anything. `GET /quizzes/` returns an empty page instead. Handle both. |
| Unknown query params | Silently ignored rather than rejected, so a typo fails quietly. |

## Deploy it

Replace the host placeholder in `apiDefinition.swagger.json` with your institution's hostname:

```jsonc
"host": "[YOUR_INSTITUTION].brightspace.com"   // -> "school.brightspace.com"
```

This is the only place the host appears. The script derives the API base URL from the incoming request, so MCP tools automatically target the same host. You can't deploy without replacing it, because square brackets aren't legal in a hostname and Power Platform rejects the definition:

```text
Error: ApiHubsRequestFailed
Invalid Api definition object. Please specify a valid Swagger 2.0 Url and valid list of ServiceUrls.
```

That failure is intentional. Deployment stops loudly rather than publishing a connector pointed at nothing.

Then replace `[YOUR_CLIENT_ID]` in `apiProperties.json`, and supply the client secret at deploy time or in the portal **Security** tab. Never commit it.

```powershell
pac auth create --environment <environment-id>

pac connector create `
    --api-definition-file ./apiDefinition.swagger.json `
    --api-properties-file ./apiProperties.json `
    --script-file ./script.csx
```

Validate first with `ppcv ./Brightspace`. Two of its warnings are expected: it reports unbalanced braces on `script.csx`, because its brace counter doesn't understand C# verbatim strings, and it flags most operations as absent from `scriptOperations`, which is the deliberate pass-through design described above.

Deployment was verified on PAC CLI 2.11.2 against a live environment, then downloaded and compared. All 31 operations deployed, `x-ms-agentic-protocol` survived as `mcp-streamable-1.0`, `script.csx` round-tripped byte for byte, and all 24 OAuth scopes and both auth URLs were preserved. The platform rewrote `redirectMode` from `Global` to `GlobalPerConnector` and replaced `redirectUrl` with the generated per-connector URL, which is exactly the behavior the redirect step above depends on.

Telemetry is off by default. Set `APP_INSIGHTS_CONNECTION_STRING` near the top of `script.csx` to turn it on. Telemetry failures are swallowed, so they never break a call.

## Resources

- [Brightspace connector source](https://github.com/troystaylor/SharingIsCaring/tree/main/Brightspace)
- [Brightspace API reference](https://docs.valence.desire2learn.com/reference.html)
- [Calling conventions, paging, and rate limits](https://docs.valence.desire2learn.com/basic/apicall.html)
- [OAuth 2.0 and scopes](https://docs.valence.desire2learn.com/basic/oauth2.html)
- [Scopes index](https://docs.valence.desire2learn.com/http-scopestable.html)
- [API versioning](https://docs.valence.desire2learn.com/basic/version.html)
- [Write code in a custom connector](https://learn.microsoft.com/connectors/custom-connectors/write-code)
