---
layout: post
title: "Give your agents directions: Azure Maps routing in Copilot"
date: 2026-11-05 18:15:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [Azure Maps, Custom Connectors, MCP, MCP Apps, Copilot Studio, Copilot Cowork, Container Apps, GeoJSON, Power Automate]
description: "An Azure Maps Route custom connector for Power Automate and Copilot Studio, a hosted MCP server with a Fluent 2 map widget, and a Copilot plugin with five skills. Here's how the three pieces fit and why only two of them share a server."
---

Azure Maps can plan a route, compare travel times, draw a reachable area, and snap a GPS trace to the road network. I packaged those tools three ways, because the places you use them don't support the same features.

- A **Power Platform custom connector** for Power Automate, Power Apps, Logic Apps, and Copilot Studio.
- A **hosted MCP server** on Azure Container Apps that adds a map widget.
- A **Copilot plugin** for Microsoft 365 Copilot and Cowork that uses the hosted server and ships five skills.

The connector doesn't use the Container App. Copilot Studio doesn't show MCP Apps yet, so a map widget would have nowhere to render. The connector returns the route as data and an image, and the hosted server serves the widget for hosts that can display it.

## Pick a piece

| You want to | Use |
| --- | --- |
| Route in a flow, app, or Logic App | Custom connector |
| Give a Copilot Studio agent routing tools | Custom connector (`InvokeMCP`) |
| See a map inline in Cowork | Plugin and hosted MCP server |
| Share the tools with another MCP client by URL | Hosted MCP server |

## The custom connector

The Azure Maps Route API (version `2025-01-01`) reads and returns `application/geo+json`. Power Platform connectors expect `application/json`, so the connector script sends your request as GeoJSON and returns the response as JSON with the GeoJSON unchanged. The result is a standard FeatureCollection you can pass to a map control, a Parse JSON action, or another service.

The connector has two flavors of each route operation:

| Operation | Azure Maps endpoint | Returns |
| --- | --- | --- |
| Get Route Directions | `POST /route/directions` | Route line, summary, and optional turn-by-turn itinerary |
| Get Route Matrix | `POST /route/matrix` | Time and distance for every origin and destination pair |
| Get Route Range | `POST /route/range` | Polygon reachable within a time or distance budget |
| Snap Points to Roads | `POST /route/snapToRoads` | Points matched to roads, optionally with speed limits |
| Get Static Map Image | `GET /map/static` | PNG or JPEG with optional pins, lines, polygons, and traffic |
| Invoke Azure Maps Route MCP | Connector script | JSON-RPC 2.0 for Copilot Studio |

Each route operation has a **(GeoJSON)** version and a **(simple inputs)** version. Use the GeoJSON operations in flows and apps when you already have GeoJSON or need vehicle specifications for truck routes. Use the simple operations from Copilot Studio agents. Agents can't pass the nested arrays of objects the GeoJSON operations take, and the call fails with a `ConnectorPowerFxError`. Both versions return the same GeoJSON.

The simple operations take points as text, `longitude,latitude` pairs separated by semicolons, and lists such as `avoid` as comma-separated values:

```json
{
  "originLongitude": -122.335167,
  "originLatitude": 47.608013,
  "destinationLongitude": -122.12151,
  "destinationLatitude": 47.67399,
  "travelMode": "driving",
  "optimizeRoute": "fastestWithTraffic",
  "routeOutputOptions": ["routeSummary", "routePath"]
}
```

`routeOutputOptions` controls what comes back. The Azure Maps default is `itinerary` only, so add `routePath` when you want a line to draw on a map. Distances are in meters and times are in seconds. Coordinates are always longitude first, then latitude.

### Deploy the connector

You need an Azure Maps account key and the Power Platform CLI signed in to your environment.

```powershell
pac connector create `
  --api-definition-file apiDefinition.swagger.json `
  --api-properties-file apiProperties.json `
  --script-file script.csx
```

Create a connection and paste your key when prompted. The connector sends it in the `subscription-key` header. To send telemetry to Application Insights, set `APP_INSIGHTS_ENABLED` and your instrumentation key in the constants at the top of `script.csx` before you deploy.

### MCP tools for Copilot Studio

Add the connector to an agent as a tool and it exposes six MCP tools through `InvokeMCP`:

| Tool | Purpose |
| --- | --- |
| `get_route_directions` | Route between an origin and destination with optional stops |
| `get_route_matrix` | Travel times and distances between origins and destinations |
| `get_route_range` | Area reachable within a time or distance budget |
| `snap_to_roads` | Match GPS points to roads |
| `get_static_map` | Map image for a center point and zoom, or a bounding box |
| `get_route_map` | Directions drawn on a map image in one step |

`get_route_map` gets the route and draws it, so the agent doesn't pass route coordinates between tools. The map is framed to fit the route, long routes are reduced to 100 points, and pins A and B mark the start and end.

The map tools return the image as MCP image content, and how it displays depends on the client. Not every client shows it, so `get_route_map` and `get_route_directions` also return a Bing Maps link that opens the route with its origin, stops, and destination. A large PNG can be several hundred KB. Set `format` to `jpeg` for a smaller image.

The tools take coordinates, not addresses. Give your agent coordinates, or add a geocoding tool next to this one.

## The hosted MCP server

A plugin connects to an MCP server by URL and can't call a custom connector, so the repo includes a small Node.js server with the same tools. It runs on Azure Container Apps and adds one more: `render_map_image`, an app-only tool the widget calls and the agent never sees.

Authentication is Microsoft Entra, and the server never holds an Azure Maps key:

1. The user signs in once and the plugin sends their access token.
2. The server accepts the token only if your tenant signed it, your app registration is the audience, it hasn't expired, and it carries the `access_as_user` scope.
3. The server calls Azure Maps with its own managed identity, which has the **Azure Maps Data Reader** role on your account.

Discovery calls (`initialize`, `tools/list`, `resources/list`, `resources/read`) are open so clients can read tool descriptions and the widget. `tools/call` returns `401` with a `WWW-Authenticate` header without a valid token.

Three settings configure it:

| Setting | Value |
| --- | --- |
| `TENANT_ID` | Your Microsoft Entra tenant ID |
| `CLIENT_ID` | The app registration's client ID |
| `MAPS_CLIENT_ID` | The Azure Maps account's client ID, sent as `x-ms-client-id` |

Deploy it with a container build and one Container Apps command:

```powershell
az acr create -n <registry> -g <resource-group> -l <region> --sku Basic
az acr build -r <registry> -t azure-maps-route-mcp:v7 .

az containerapp env create -n <environment> -g <resource-group> -l <region>
az containerapp create -n azure-maps-route-mcp -g <resource-group> `
  --environment <environment> `
  --image <registry>.azurecr.io/azure-maps-route-mcp:v7 `
  --registry-server <registry>.azurecr.io --registry-identity system `
  --target-port 8080 --ingress external --min-replicas 1 --cpu 0.25 --memory 0.5Gi `
  --env-vars TENANT_ID=<tenant-id> CLIENT_ID=<client-id> MAPS_CLIENT_ID=<maps-client-id>

az role assignment create --assignee-object-id <app-identity-principal-id> `
  --assignee-principal-type ServicePrincipal `
  --role "Azure Maps Data Reader" --scope <azure-maps-account-resource-id>
```

The MCP endpoint is the app URL plus `/mcp`. Keep `--min-replicas 1` so the first call after an idle period doesn't wait for a cold start.

## How the map widget works

`get_route_map` and `get_static_map` declare an MCP Apps widget at `ui://azure-maps-route/map.html`. The server serves it through `resources/read` with the MIME type `text/html;profile=mcp-app`, and hosts that support MCP Apps, such as Cowork, render it inline.

The image takes three steps to reach the user:

1. The tool validates the request and returns the distance, the travel time, a Bing Maps link, and the map request in `structuredContent`. The route line is simplified to at most 100 points, which keeps it far below the 64 KiB widget limit. The tool doesn't render an image.
2. The widget calls `render_map_image` back through the host, which attaches the user's sign-in.
3. The server renders the image with its managed identity and returns it, and the widget shows it as a `data:` URL.

There's no public image link, no image storage, and no signing secret. The widget needs no network access, and its Content Security Policy declares no external domains.

The widget follows Fluent 2. It uses the Segoe UI type ramp, light and dark themes that follow the host, a 4 px radius card, a skeleton loader, and a message bar for errors. It also honors reduced motion and forced colors.

### Keep results small

Some clients drop large tool results, so the server keeps them small. Images default to a 640 by 400 JPEG, about 60 KB, and larger requests are reduced in steps until they're under about 150 KB. `get_route_directions` returns distance and time by default. The route line, turn-by-turn instructions, and extra routes are opt-in, and the server removes route line coordinates when a result is still very large.

In a client without MCP Apps support, the agent gets the text and the Bing Maps link. Set `embedImage` on a map tool to also return the image bytes for a client that renders MCP image content but has no widget.

## The plugin and its skills

The plugin manifest points at the hosted server with `OAuthPluginVault`, so users sign in once through an Entra app registration you own. The connector authorization in `agentConnectors` has no Entra single sign-on option, and Cowork doesn't support API-key authorization. An Azure Maps key also can't go in the `subscription-key` header from a plugin.

To register the server:

1. In the [Teams Developer Portal](https://dev.teams.microsoft.com/tools), open **Tools** > **OAuth client registration** and select **Register client**.
2. Set **Base URL** to the server URL ending in `/mcp`, restrict usage to **My organization only** and **Any Teams app**, and enter the Entra app's client ID and secret.
3. Use the `login.microsoftonline.com` v2.0 authorize and token endpoints for your tenant, and the scope `api://<client-id>/access_as_user offline_access`.
4. Copy `env/.env.dev.user.sample` to `env/.env.dev.user` and set the server URL, its domain, and the OAuth registration ID the portal shows.

Then build and share the plugin with Work IQ Dev Tools:

```powershell
wiqd auth login --interactive
wiqd plugin validate
wiqd plugin provision --env dev
wiqd plugin package --env dev
wiqd plugin validate --mode deep --env dev
wiqd plugin share --scope users --email <address>
```

The plugin carries five skills, and each one tells Copilot which tools to call and what to watch for:

| Skill | What it does |
| --- | --- |
| Plan a Route | Directions with stops, travel mode, and traffic |
| Compare Travel Times | Origin and destination matrix with the fastest option highlighted |
| Find a Service Area | Area reachable within a time or distance budget |
| Clean a GPS Trace | Snap points to roads |
| Map a Route | One `get_route_map` call for a route, or `get_static_map` for places and areas |

The Map a Route skill tells Copilot to call `get_route_map` once instead of calling directions first, which saves a large result. It also says not to claim an image is attached, because only MCP Apps clients show the widget. Without one, Copilot shares the distance, the travel time, and the Bing Maps link.

## Limits

- Route directions supports up to 150 waypoints, with up to 10 via waypoints between any two.
- Route matrix supports up to 2,500 origin and destination pairs per call, and matrices over 100 pairs have extra restrictions in the [Route Matrix documentation](https://learn.microsoft.com/rest/api/maps/route/post-route-matrix?view=rest-maps-2025-01-01).
- Route range supports `driving` and `truck`, not `walking`.
- Static maps support PNG and JPEG up to 2000 by 1500 pixels, 25 pins, and 10 paths of up to 100 locations each.
- Batch and asynchronous Route API operations aren't included.
- Anyone in your tenant who holds the `access_as_user` scope can call the hosted server, and every call uses the server's Azure Maps identity. Turn on assignment required on the enterprise application to limit who can use it.

## Troubleshooting

- **401 from the connector:** The key is missing, wrong, or from a different Azure Maps account. Update the connection.
- **400 on directions:** Check longitude then latitude order, that `departAt` and `arriveAt` aren't both set, and that an origin and destination are present.
- **400 on a matrix:** Origins multiplied by destinations is over 2,500, or a feature is missing its `pointType`.
- **400 on a static map:** Send either `center` or `bbox`, not both, and don't combine `bbox` with `width` or `height`.
- **No route line:** Add `routePath` to `routeOutputOptions`.
- **`ConnectorPowerFxError` in Copilot Studio:** The agent called a GeoJSON operation. Use the simple inputs operation, or turn off the GeoJSON operations for that agent.

## Resources

- [Azure Maps Route connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Maps%20Route)
- [Azure Maps Route hosted MCP server](https://github.com/troystaylor/SharingIsCaring/tree/main/Container%20Apps/Azure%20Maps%20Route)
- [Azure Maps Route plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Plugins/Azure%20Maps%20Route)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
- [Azure Maps Route API](https://learn.microsoft.com/rest/api/maps/route)
- [Build plugins for Copilot Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
