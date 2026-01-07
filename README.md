# Troy Taylor's Technical Blog

A Jekyll blog using the [jekyll-gitbook](https://github.com/sighingnow/jekyll-gitbook) theme, covering Power Platform, MCP servers, Copilot Studio, and enterprise integrations.

## Live Site

[https://troystaylor.github.io](https://troystaylor.github.io)

## Local Development

1. Install Ruby and Bundler
2. Install dependencies:
   ```bash
   bundle install
   ```
3. Run locally:
   ```bash
   bundle exec jekyll serve
   ```
4. Visit http://localhost:4000

## Adding Posts

Create new posts in the `_posts` directory with the format:
```
YYYY-MM-DD-title.md
```

Front matter example:
```yaml
---
title: Your Post Title
author: Troy Taylor
date: 2026-01-07
category: Power Platform
layout: post
---
```

## Theme

This blog uses the jekyll-gitbook theme as a remote theme. See the [theme documentation](https://github.com/sighingnow/jekyll-gitbook) for customization options.

## Code Repository

All code samples and connectors are available at [SharingIsCaring](https://github.com/troystaylor/SharingIsCaring).

## License

MIT License