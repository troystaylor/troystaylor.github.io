---
layout: post
title: "LinkedIn Community Management MCP connector for Copilot Studio"
date: 2026-03-10 16:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, LinkedIn, Social Media, Community Management]
---

Managing a LinkedIn Page means juggling post creation, comment moderation, media uploads, and analytics across multiple screens. Multiply that across several organization pages and the context-switching adds up fast.

The LinkedIn Community Management connector puts all of that behind 28 MCP tools so your Copilot Studio agent can handle it conversationally.

## Seven operation categories

### Posts (5 tools)

Full lifecycle management for LinkedIn posts:

| Tool | Method | Description |
|------|--------|-------------|
| create_post | POST | Create text, image, video, article, document, or reshare posts |
| get_post | GET | Retrieve a post by URN |
| find_posts_by_author | GET | Find posts by a member or organization |
| update_post | POST | Update commentary or reshare settings |
| delete_post | DELETE | Remove a post |

The connector supports every LinkedIn post type: plain text, images, videos, articles with link previews, document carousel uploads, and reshares.

### Comments (4 tools)

| Tool | Method | Description |
|------|--------|-------------|
| get_comments | GET | List comments on a post |
| create_comment | POST | Add a comment to a post |
| get_comment | GET | Get a specific comment by ID |
| delete_comment | DELETE | Remove a comment |

### Reactions (3 tools)

| Tool | Method | Description |
|------|--------|-------------|
| get_reactions | GET | List reactions on a post |
| create_reaction | POST | React to a post (LIKE, PRAISE, EMPATHY, and more) |
| delete_reaction | DELETE | Remove a reaction |

### Organizations (4 tools)

| Tool | Method | Description |
|------|--------|-------------|
| get_organization | GET | Get organization details by numeric ID |
| find_org_by_vanity_name | GET | Look up an organization by its URL vanity name |
| get_follower_count | GET | Get total follower count |
| find_member_org_access | GET | Find organizations the member administers |

### Social metadata (2 tools)

| Tool | Method | Description |
|------|--------|-------------|
| get_social_metadata | GET | Get engagement stats (likes, comments, shares) |
| toggle_comments | POST | Enable or disable comments on a post |

### Media (7 tools)

Upload images, videos, and documents for use in posts:

| Tool | Method | Description |
|------|--------|-------------|
| initialize_image_upload | POST | Get an upload URL for an image |
| get_image | GET | Get image details by URN |
| initialize_video_upload | POST | Initialize video upload (returns chunk URLs) |
| finalize_video_upload | POST | Finalize after all chunks are uploaded |
| get_video | GET | Get video details and processing status |
| initialize_document_upload | POST | Get an upload URL for a document |
| get_document | GET | Get document details by URN |

**Video upload flow:**

Video files upload in 4 MB chunks:

1. Call `initialize_video_upload` with the file size to get chunk upload URLs and a video URN
2. PUT each 4 MB chunk to its corresponding upload URL and save the ETag from each response
3. Call `finalize_video_upload` with the video URN, upload token, and array of ETags

### Statistics (3 tools)

Analytics for your LinkedIn Page:

| Tool | Method | Description |
|------|--------|-------------|
| get_share_statistics | GET | Post and share engagement analytics |
| get_page_statistics | GET | Page view analytics segmented by demographics |
| get_follower_statistics | GET | Follower growth and demographic breakdowns |

Filter by time range using `start_time` and `end_time` as epoch milliseconds with optional `granularity` (DAY, WEEK, MONTH). Data is available for the past 12 months.

## Example agent scenarios

### Automated post creation and engagement monitoring

1. User tells the agent to draft a post about a new product launch
2. Agent uses `create_post` to publish text with an article link preview
3. Later, agent uses `get_social_metadata` to check likes, comments, and shares
4. Uses `get_comments` to surface any questions that need responses

### Community engagement workflow

1. Agent uses `find_posts_by_author` to list recent organization posts
2. For each post, calls `get_social_metadata` to rank by engagement
3. Uses `get_comments` to find unanswered questions
4. Flags posts that need attention with comment counts and topics

### Page analytics reporting

1. Agent uses `get_follower_statistics` to pull follower growth for the past quarter
2. Calls `get_page_statistics` to break down page views by audience demographics
3. Uses `get_share_statistics` to identify top-performing posts
4. Summarizes trends for the social media team

### Rich media posting

1. Agent calls `initialize_image_upload` to get an upload URL
2. Uploads the image to the returned URL
3. Uses `create_post` with the image URN to publish a visual post
4. Tracks performance with `get_social_metadata`

## LinkedIn API details

The connector handles several LinkedIn REST.li patterns automatically:

- **URN encoding**: Pass raw URN values like `urn:li:organization:123`. The connector URL-encodes them in API paths.
- **Post creation response**: LinkedIn returns the new post ID in the `x-restli-id` header. The connector extracts it and returns `{ "id": "urn:li:ugcPost:..." }` in the response body.
- **Partial updates**: `update_post` and `toggle_comments` wrap your changes in the required `{"patch":{"$set":{...}}}` envelope automatically.
- **Compound keys**: `delete_reaction` constructs the REST.li compound key path `/reactions/(actor:{urn},entity:{urn})` from individual parameters.
- **API versioning**: All requests include `Linkedin-Version: 202602` and `X-Restli-Protocol-Version: 2.0.0` headers automatically.

## Prerequisites

- A LinkedIn account with admin access to at least one LinkedIn Page
- A LinkedIn Developer App with the **Community Management** product enabled
- OAuth 2.0 credentials (Client ID and Client Secret) from your LinkedIn Developer App

### Required OAuth scopes

| Scope | Description |
|-------|-------------|
| w_member_social | Create and manage posts as a member |
| w_organization_social | Create and manage posts as an organization |
| r_organization_social | Read organization posts and social actions |
| rw_organization_admin | Read and write organization page administration |
| r_organization_admin | Read organization page details |

## Setup

1. Go to the [LinkedIn Developer Portal](https://developer.linkedin.com/) and sign in
2. Create a new app or select an existing one
3. Under **Products**, request access to **Community Management**
4. Under **Auth**, note your Client ID and Client Secret
5. Add the Power Platform redirect URL to **Authorized redirect URLs**

Deploy with PAC CLI:

```powershell
pac connector create `
  --api-definition-file apiDefinition.swagger.json `
  --api-properties-file apiProperties.json `
  --script-file script.csx
```

For Copilot Studio:

1. Open your agent
2. Go to **Actions** > **Add an action** > **Connector**
3. Search for your connector and add it
4. The agent discovers all 28 tools automatically

## Application Insights telemetry

Add your connection string to `script.csx` to track:

| Event | Description |
|-------|-------------|
| RequestReceived | Every incoming request with correlation ID |
| RequestCompleted | Success responses with duration |
| RequestError | Failed requests with error details |
| MCPRequest | MCP tool invocations |
| MCPToolCall | Individual tool calls with parameters |
| MCPToolError | MCP-specific errors |
| LinkedInAPIError | LinkedIn API failures |

## Resources

- [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/LinkedIn%20Community%20Management)
- [LinkedIn Community Management API documentation](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- [LinkedIn Developer Portal](https://developer.linkedin.com/)
