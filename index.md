---
layout: home
title: Home
---

# Power Platform Integrations
## Sharing Is Caring

<img src="/assets/images/profile.jpg" alt="Troy Taylor" width="150" style="border-radius: 50%; margin-bottom: 20px;" />

This blog covers technical topics including:

- **Power Platform** - Custom connectors and automation
- **MCP Servers** - Model Context Protocol integrations
- **Copilot Studio** - AI-driven agents and solutions
- **Microsoft Graph** - API integrations and best practices
- **Enterprise Integrations** - Snowflake, Dataverse, SharePoint Embedded

Check out my [GitHub repository](https://github.com/troystaylor/SharingIsCaring) for code samples and connectors.

## Latest Posts

{% for post in site.posts limit:5 %}
- [{{ post.title }}]({{ post.url }}) - {{ post.date | date: "%B %d, %Y" }}
{% endfor %}
