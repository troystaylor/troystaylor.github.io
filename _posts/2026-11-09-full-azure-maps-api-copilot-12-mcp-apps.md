---
layout: post
title: "Put the full Azure Maps API in Copilot with 12 MCP Apps"
date: 2026-11-09 13:45:00 -0500
categories: [Power Platform, MCP, Copilot Studio]
tags: [Azure Maps, MCP, MCP Apps, Copilot Plugins, Container Apps, Microsoft Entra, Cowork, Weather, Routing]
description: "A hosted MCP server for the full Azure Maps REST API with 59 tools and 12 MCP Apps, plus a shareable Copilot plugin with 14 skills. Here's what's in it, how sign-in works, and how to deploy it."
---

Last week's [Azure Maps Route post](/power%20platform/2026-11-05-give-agents-directions-azure-maps-routing-copilot.html) covered routing only. The new Azure Maps MCP server covers the rest of the REST API: geocoding, search, routing, weather, traffic, time zones, map rendering, and IP geolocation. It has 59 tools and 12 interactive apps that open inline in Microsoft 365 Copilot and Cowork.

A matching Copilot plugin with 14 skills is ready to share. It has no IDs, secrets, or server addresses, so you can hand the folder to a colleague and they set it up against their own tenant.

## What's in the repo

| Piece | What it is |
| --- | --- |
| [Azure Maps MCP Server](https://github.com/troystaylor/SharingIsCaring/tree/main/Container%20Apps/Azure%20Maps%20MCP%20Server) | Node.js MCP server for Azure Container Apps, with no npm dependencies |
| [Azure Maps plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Plugins/Azure%20Maps) | Copilot plugin manifest, 14 skills, and environment file samples |
| [EXAMPLES.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Container%20Apps/Azure%20Maps%20MCP%20Server/EXAMPLES.md) | Prompts and JSON arguments for every app and tool |

This server is the full-API companion to the Route-only server. Use the Route-only server if you want a smaller surface.

## Tools that take text

Most tools accept a place as text or as coordinates. An agent can ask for directions from Seattle Center to Microsoft Redmond in one call, and the server geocodes each place once and reuses the result.

| Area | Example tools |
| --- | --- |
| Geocoding | `geocode`, `reverse_geocode`, `batch_geocode`, `get_boundary` |
| Search | `search_poi`, `search_nearby`, `search_along_route`, `search_inside_geometry` |
| Routing | `get_route_directions`, `get_route_matrix`, `get_route_range`, `compare_departure_times`, `snap_to_roads` |
| Weather | `get_weather`, `get_minute_forecast`, `get_severe_weather_alerts`, `get_weather_along_route`, `get_tropical_storms` |
| Traffic | `get_traffic_incidents`, `get_traffic_flow_segment` |
| Time and place | `get_timezone`, `convert_windows_timezone`, `get_ip_location` |
| Maps | `show_map`, `show_weather_radar`, `get_static_map_image` |

The server uses the newest Azure Maps version for each service. Geocoding and batch calls use Search `2026-01-01`, routing uses `2025-01-01`, and weather uses `1.1`. Fuzzy, POI, nearby, and along-route search have no newer equivalent, so they stay on Search `1.0`. The two advanced routing tools also use Route `1.0`, which adds bicycle, motorcycle, bus, van, and taxi modes plus electric and combustion range.

Azure Maps Creator, Mobility, and Feature State are retired, and Elevation and Spatial aren't in the current REST reference, so none of them are included.

## The 12 apps

The apps are single-page widgets the host renders in a sandboxed frame. They load nothing from the network. Map tiles, searches, and re-routing go through the host, which calls the server's tools with the user's sign-in. That's what lets a user pan a map or drag a slider and get fresh data back.

| App | Opens from | What users can do |
| --- | --- | --- |
| Interactive map | `show_map`, `show_weather_radar`, `get_boundary` | Pan and zoom road, dark, satellite, hybrid, and terrain styles. Show live traffic. Play a weather radar loop covering the last 90 minutes and the next 2 hours |
| Place finder | Search and geocoding tools | Browse results on a map, sort by distance, see opening hours, and search the area after moving the map |
| Route planner | `get_route_directions` | Compare alternatives, switch between drive, truck, and walk, avoid tolls or highways, and step through directions |
| Reachable area | `get_route_range` | See nested 5 to 60 minute areas and find places inside them, such as EV chargers |
| Travel time matrix | `get_route_matrix` | Heat-map table of times, nearest origin per destination, and CSV export |
| Best time to leave | `compare_departure_times` | Chart travel time across the day and see the best and worst times |
| Weather dashboard | `get_weather` | Current conditions, a two-hour rain forecast, hourly chart, five-day forecast, alerts, and air quality |
| Weather along the route | `get_weather_along_route` | Route colored by hazard, with a "leave in" selector |
| Traffic | `get_traffic_incidents` | Incidents by type and severity, plus current speed on any road you tap |
| World clock | `get_timezone` | Live clocks and the working hours every participant shares |
| Batch geocoding | `batch_geocode` | Match quality table, inline fixes for misses, and CSV download |
| Storm tracker | `get_tropical_storms` | Active hurricanes, cyclones, and typhoons with past and forecast tracks |

In the place finder, selecting a result tells the agent what the user picked, so the conversation continues from that choice. In clients without MCP Apps support, every tool still returns a complete text answer.

## How sign-in works

Callers sign in with Microsoft Entra, and the server never holds an Azure Maps key.

1. The plugin sends the user's access token to the server.
2. The server accepts the token only if your tenant signed it, your app registration is the audience, it hasn't expired, and it has the `access_as_user` scope.
3. The server calls Azure Maps with its own managed identity, which needs the **Azure Maps Data Reader** role on your account.

Discovery calls (`initialize`, `tools/list`, `resources/list`, and `resources/read`) are open so clients can read tool descriptions and the apps. `tools/call` returns `401` with a `WWW-Authenticate` header without a valid token.

## Deploy the server

You need an Azure Maps Gen2 account, an Entra app registration with the application ID URI `api://<client-id>` and a delegated `access_as_user` scope, and access token version 2. Three settings configure the container:

| Setting | Value |
| --- | --- |
| `TENANT_ID` | Your Microsoft Entra tenant ID |
| `CLIENT_ID` | The app registration's client ID |
| `MAPS_CLIENT_ID` | The Azure Maps account's client ID, sent as `x-ms-client-id` |

An optional `RATE_LIMIT_PER_MINUTE` caps calls per signed-in user and defaults to 600. Interactive maps request many tiles, so keep it generous.

```powershell
az acr create -n <registry> -g <resource-group> -l <region> --sku Basic
az acr build -r <registry> -t azure-maps-mcp:v1 .

az containerapp env create -n <environment> -g <resource-group> -l <region>
az containerapp create -n azure-maps-mcp -g <resource-group> --environment <environment> `
  --image <registry>.azurecr.io/azure-maps-mcp:v1 `
  --registry-server <registry>.azurecr.io --registry-identity system `
  --target-port 8080 --ingress external --min-replicas 1 --cpu 0.5 --memory 1Gi `
  --env-vars TENANT_ID=<tenant-id> CLIENT_ID=<client-id> MAPS_CLIENT_ID=<maps-client-id>

az role assignment create --assignee-object-id <app-identity-principal-id> `
  --assignee-principal-type ServicePrincipal `
  --role "Azure Maps Data Reader" --scope <azure-maps-account-resource-id>
```

The MCP endpoint is the app URL plus `/mcp`, and `GET /health` returns `{"status":"ok"}`. Keep `--min-replicas 1` so the first call after an idle period skips a cold start. The server keeps a small in-memory tile cache, so memory grows a little under heavy map use, and 1 GiB is plenty.

## Try the apps locally

The repo includes a preview server with a stand-in MCP Apps host. Entra sign-in is off, and it needs an Azure Maps key that stays on your machine.

```powershell
$env:MAPS_SUBSCRIPTION_KEY = "<azure maps key>"
node test/dev-server.js
```

Open `http://127.0.0.1:8777/`, pick a tool, edit its arguments, and select **Run**. To jump straight to an app, use a URL such as `http://127.0.0.1:8777/?tool=get_weather&args={"location":{"query":"Seattle"}}` and add `&dark=1` for the dark theme. To call one tool from the command line:

```powershell
node test/call.js get_route_range '{"origin":{"query":"Seattle Center"},"timeBudgetsMinutes":[10,20]}'
```

`npm test` runs offline tests against canned Azure Maps responses. They check the tool catalog, that every app exists and loads nothing from the network, the sign-in behavior, and the retry and error handling in the Azure Maps client. They need no network or key.

## The plugin and its 14 skills

The plugin manifest connects to the server with Microsoft Entra OAuth. Each skill tells Copilot which tools to call and what to watch for.

| Skill | Tools it uses |
| --- | --- |
| Find Places | `search_poi`, `search_fuzzy`, `geocode`, `reverse_geocode` |
| Plan a Route | `get_route_directions`, `get_route_directions_advanced` |
| Best Time to Leave | `compare_departure_times` |
| Compare Travel Times | `get_route_matrix`, `start_route_matrix_async` |
| Find a Service Area | `get_route_range`, `get_reachable_range_advanced` |
| Find Stops Along a Route | `search_along_route` |
| Check the Weather | `get_weather` and the forecast, air quality, and history tools |
| Weather on the Road | `get_weather_along_route` |
| Check Traffic | `get_traffic_incidents`, `get_traffic_flow_segment` |
| Plan Across Time Zones | `get_timezone` |
| Geocode an Address List | `batch_geocode`, `batch_reverse_geocode` |
| Track a Storm | `get_tropical_storms` |
| Show a Map | `show_map`, `show_weather_radar`, `get_boundary` |
| Clean a GPS Trace | `snap_to_roads`, `snap_to_roads_batch` |

The skills encode the judgment calls. Best Time to Leave sets `timeMode` to `arriveAt` when someone has a deadline, caps a comparison at 24 tests, and says these are predictions rather than guarantees. If the spread is only a few minutes, it tells the user traffic barely changes the trip.

### Register the server and share the plugin

1. In the [Teams Developer Portal](https://dev.teams.microsoft.com/tools), open **Tools** > **OAuth client registration** and select **Register client**.
2. Set **Base URL** to the server URL ending in `/mcp`, restrict usage to **My organization only** and **Any Teams app**, and enter the Entra app's client ID and secret.
3. Use the `login.microsoftonline.com` v2.0 authorize and token endpoints for your tenant, and the scope `api://<client-id>/access_as_user offline_access`. Add `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect` as a redirect URI on the Entra app.
4. Copy the two `env/.env.dev*.sample` files, then set `AZURE_MAPS_MCP_SERVER_URL`, `AZURE_MAPS_MCP_SERVER_DOMAIN`, and `AZURE_MAPS_OAUTH_REFERENCE_ID` in `env/.env.dev.user`.

Then build and share with Work IQ Dev Tools:

```powershell
wiqd auth login --interactive
wiqd plugin validate
wiqd plugin provision --env dev
wiqd plugin package --env dev
wiqd plugin validate --mode deep --env dev
wiqd plugin share --scope users --email <address>
```

Bump `version` in `appPackage/manifest.json` before you upload a rebuilt package. After provisioning, ask your admin to review and assign the plugin in the Microsoft 365 admin center under **Agents** > **Tools**. When you share the folder, leave out `env/.env.dev`, `env/.env.dev.user`, and `appPackage/build/`. The `.gitignore` already excludes them.

## Limits and costs

- Anyone in your tenant who can sign in to the app registration and holds `access_as_user` can call the server, and every call uses the server's Azure Maps identity. Turn on **Assignment required** on the enterprise application to restrict who can use it.
- Interactive maps request tiles, and Azure Maps bills 15 tiles as one transaction. The server caches base map and satellite tiles for six hours, traffic tiles for one minute, and weather tiles for four minutes, and it shares one request between callers who ask for the same tile.
- Azure Maps weather along a route forecasts only the next 120 minutes, so `get_weather_along_route` checks the first two hours of longer trips.
- The apps need a client that supports MCP Apps, such as Cowork.
- The server retries `429` and `5xx` responses with backoff, times out after 30 seconds, and sends at most 16 requests to Azure Maps at once. Set `MAPS_MAX_CONCURRENT` to change that.

## Resources

- [Azure Maps MCP Server](https://github.com/troystaylor/SharingIsCaring/tree/main/Container%20Apps/Azure%20Maps%20MCP%20Server) and its [examples](https://github.com/troystaylor/SharingIsCaring/blob/main/Container%20Apps/Azure%20Maps%20MCP%20Server/EXAMPLES.md)
- [Azure Maps plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Plugins/Azure%20Maps)
- [Azure Maps REST API documentation](https://learn.microsoft.com/rest/api/maps/)
- [Model Context Protocol](https://modelcontextprotocol.io)
