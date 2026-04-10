---
layout: post
title: "Copilot Cowork Skills MCP connector for Power Platform"
date: 2026-04-10 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Copilot Cowork, Microsoft 365 Copilot, MCP, Copilot Studio, Custom Connectors, Power Platform, Skills, OneDrive]
description: "Power Platform custom connector for managing Copilot Cowork custom skills—list, create, update, validate, and delete SKILL.md files stored in OneDrive through six MCP tools."
---

[Copilot Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/) is Microsoft 365 Copilot's work delegation engine. It carries out tasks on your behalf—sending emails, scheduling meetings, creating documents—using specialized skills. Beyond the 13 built-in skills, Cowork supports up to 20 custom skills stored as `SKILL.md` files in your OneDrive `/Documents/Cowork/Skills/` folder.

Right now, creating and managing those custom skills means manually editing Markdown files in OneDrive. This connector makes that programmatic—six MCP tools that let a Copilot Studio agent or Power Automate flow list, read, create, update, validate, and delete custom skills on behalf of users.

Copilot Cowork is currently available through the [Frontier preview program](https://adoption.microsoft.com/en-us/copilot/frontier-program/).

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Cowork%20Skills)

## Six tools

| Tool | Description |
|------|-------------|
| `list_skills` | List all custom skills in the Cowork Skills folder |
| `get_skill` | Read the SKILL.md content of a specific skill |
| `create_skill` | Create a new custom skill (folder + SKILL.md) |
| `update_skill` | Update an existing skill's SKILL.md file |
| `delete_skill` | Delete a skill folder |
| `validate_skill` | Validate SKILL.md content without saving |

## SKILL.md format

Each custom skill is a `SKILL.md` file with YAML frontmatter and Markdown instructions:

```yaml
---
name: Weekly Report
description: Generates a weekly status report from my recent emails and calendar.
---

Gather my sent emails and calendar events from the past week, then create
a summary document organized by project.
```

### Requirements

- **name** (required): Display name shown in Cowork
- **description** (required): One-line description used by Cowork to decide when to load the skill
- **Instructions** (required): Markdown content after the frontmatter that tells Cowork how to execute the skill
- Maximum file size: 1 MB
- Maximum custom skills: 20

## How it works

```
User: "Create a Cowork skill that prepares my standup notes"

1. Orchestrator calls create_skill({
     name: "Daily Standup Summary",
     content: "---\nname: Daily Standup Summary\n
               description: Prepares a daily standup summary
               from yesterday's work items and today's calendar.\n---\n
               1. Check my calendar for meetings I attended yesterday...
               2. Review my sent emails from yesterday...
               3. Look at today's calendar...
               4. Create a brief standup summary..."
   })

   → Skill created at /Documents/Cowork/Skills/Daily Standup Summary/SKILL.md
```

```
User: "What Cowork skills do I have?"

2. Orchestrator calls list_skills({})

   → Returns: ["Daily Standup Summary", "Client Follow-Up Drafter",
               "Expense Report Prep"]
```

```
User: "Update the standup skill to also include Planner tasks"

3. Orchestrator calls get_skill({ name: "Daily Standup Summary" })
   → Returns current SKILL.md content

4. Orchestrator calls update_skill({
     name: "Daily Standup Summary",
     content: "... updated with Planner task step ..."
   })
```

The `validate_skill` tool checks SKILL.md content for proper frontmatter, required fields, and size limits before saving—useful for catching formatting errors in agent-generated skills.

## Storage

Skills live in the user's OneDrive:

```
OneDrive
└── Documents/
    └── Cowork/
        └── Skills/
            ├── Daily Standup Summary/
            │   └── SKILL.md
            ├── Client Follow-Up Drafter/
            │   └── SKILL.md
            └── Expense Report Prep/
                └── SKILL.md
```

The connector wraps Microsoft Graph OneDrive API endpoints:

| Operation | Graph API path |
|-----------|---------------|
| List skills | `GET /me/drive/root:/Documents/Cowork/Skills:/children` |
| Read skill | `GET /me/drive/root:/Documents/Cowork/Skills/{name}/SKILL.md:/content` |
| Create/update | `PUT /me/drive/root:/Documents/Cowork/Skills/{name}/SKILL.md:/content` |
| Delete skill | `DELETE /me/drive/root:/Documents/Cowork/Skills/{name}` |

## Example skills

### Daily standup summary

```yaml
---
name: Daily Standup Summary
description: Prepares a daily standup summary from yesterday's work items
  and today's calendar.
---

1. Check my calendar for meetings I attended yesterday and extract key
   action items.
2. Review my sent emails from yesterday for completed tasks or decisions made.
3. Look at today's calendar for upcoming meetings and commitments.
4. Create a brief standup summary with three sections:
   - What I accomplished yesterday
   - What I'm working on today
   - Any blockers or concerns
```

### Client follow-up drafter

```yaml
---
name: Client Follow-Up Drafter
description: Drafts follow-up emails after client meetings using meeting
  notes and transcripts.
---

After I mention a client meeting:
1. Find the most recent meeting with that client from my calendar.
2. If a transcript exists, summarize the key discussion points and commitments.
3. Draft a professional follow-up email that includes:
   - Thank them for the meeting
   - Recap the key decisions and action items
   - Suggest next steps with proposed dates
4. Show me the draft for review before sending.
```

### Expense report prep

```yaml
---
name: Expense Report Prep
description: Gathers travel and expense information from emails and calendar
  to prepare an expense report.
---

When asked to prepare an expense report for a specific time period:
1. Search my email for receipts, booking confirmations, and expense-related
   messages.
2. Check my calendar for business travel events during that period.
3. Create an Excel spreadsheet with columns: Date, Vendor, Category, Amount,
   Description.
4. Categorize expenses as: Travel, Meals, Accommodation, Transportation,
   or Other.
5. Include a summary total at the bottom.
```

## Use cases

**Skill provisioning for teams**: Build a Power Automate flow that provisions a standard set of Cowork skills for new employees. When someone joins the team, create their Daily Standup Summary, Client Follow-Up, and Expense Report skills automatically.

**Self-service skill creation**: Let users tell a Copilot Studio agent what they want automated. "I need a skill that drafts my weekly report every Friday." The agent generates the SKILL.md, validates it, and creates it in the user's OneDrive.

**Skill templates and governance**: Maintain approved skill templates in SharePoint. When a user requests a skill, the agent picks the closest template, customizes it for the user's context, validates it, and deploys it. IT controls the templates, users get personalized skills.

**Skill auditing**: Use `list_skills` and `get_skill` in a scheduled flow to inventory what custom skills exist across your organization. Identify skills that reference deprecated services or violate data handling policies.

## Prerequisites

1. Microsoft 365 Copilot license with [Frontier preview](https://adoption.microsoft.com/en-us/copilot/frontier-program/) access
2. OneDrive for Business
3. An Azure AD app registration with `Files.ReadWrite` delegated permission

## Setting up the connector

1. Go to [Power Platform Maker Portal](https://make.powerapps.com/)
2. Navigate to **Custom connectors** > **+ New custom connector** > **Import an OpenAPI file**
3. Upload `apiDefinition.swagger.json`
4. On the **Code** tab:
   - Enable **Code**
   - Upload `script.csx`
5. Select **Create connector**
6. Create a connection using your Microsoft 365 account
7. Grant `Files.ReadWrite` permission when prompted

### Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "List my Cowork skills" or "Create a skill that drafts meeting follow-ups"

## Known limitations

- Requires Copilot Cowork Frontier preview access for the skills to actually run in Cowork
- Maximum 20 custom skills per user
- Maximum 1 MB per SKILL.md file
- Skills are per-user (stored in individual OneDrive)—no shared org-wide skill library
- The connector manages skill files but doesn't execute them—Cowork handles execution

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with single MCP endpoint |
| `apiProperties.json` | OAuth 2.0 config with Files.ReadWrite scope |
| `script.csx` | C# script handling MCP protocol, OneDrive Graph API calls, skill validation |
| `readme.md` | Setup and usage documentation |

## Resources

- [Copilot Cowork Skills connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Copilot%20Cowork%20Skills)
- [Copilot Cowork overview](https://learn.microsoft.com/microsoft-365/copilot/cowork/)
- [Copilot Cowork custom skills](https://learn.microsoft.com/microsoft-365/copilot/cowork/use-cowork#create-custom-skills)
- [Copilot Cowork FAQ](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-faq)
- [Frontier preview program](https://adoption.microsoft.com/en-us/copilot/frontier-program/)
- [OneDrive Graph API](https://learn.microsoft.com/graph/api/resources/onedrive)
