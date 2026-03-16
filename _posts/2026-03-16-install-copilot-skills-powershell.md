---
layout: post
title: "Use a Copilot skill to install Copilot skills"
date: 2026-03-16 09:00:00 -0500
categories: [Copilot Studio, Automation]
tags: [GitHub Copilot, VS Code, PowerShell, Skills, Agent Mode, Copilot Studio, Automation, Developer Tools]
description: "A Copilot skill that bootstraps itself—ask Copilot to install skills from any GitHub repository and it clones the repo, configures VS Code settings, and registers the skill paths automatically."
---

GitHub Copilot's agent mode in VS Code supports custom skills—reusable instruction sets that teach Copilot how to handle domain-specific tasks. Microsoft published an official [skills-for-copilot-studio](https://github.com/microsoft/skills-for-copilot-studio) repository with ready-made skills, but getting them wired into VS Code requires cloning the repo to the right location and manually editing `settings.json`. That's two steps too many.

The best fix for that problem? A skill that installs skills.

## The bootstrap problem

Skills live in markdown files on disk. VS Code discovers them through the `chat.agentSkillsLocations` setting. To use a new skill repository, you need to clone it somewhere, then add the path to that setting. Do that once and it's fine. Do it for five repositories and you're copying paths and editing JSON by hand.

The [install-skills](https://github.com/troystaylor/SharingIsCaring/tree/main/skills/install-skills) skill wraps a PowerShell script that handles the clone-and-configure workflow. Once the skill is loaded, you can ask Copilot to install more skills in natural language:

> "Install skills from https://github.com/microsoft/skills-for-copilot-studio"

Copilot reads the skill's `SKILL.md`, runs the underlying script with the right parameters, and reports back. No manual path editing.

## Get started

Download and run the script, pointing it at the SharingIsCaring repo to install the `install-skills` skill itself:

```powershell
irm https://raw.githubusercontent.com/troystaylor/SharingIsCaring/main/skills/install-skills/install-skills.ps1 -OutFile "$env:TEMP\install-skills.ps1"
& "$env:TEMP\install-skills.ps1" -RepoUrl "https://github.com/troystaylor/SharingIsCaring" -SkillsSubPath "skills"
```

This clones the SharingIsCaring repo, registers the skills path in VS Code, and gives Copilot access to the `install-skills` skill. Restart VS Code and you're ready to go.

From that point forward, ask Copilot to install any skills repository in natural language. For example, to install Microsoft's official Copilot Studio skills:

> "Install skills from https://github.com/microsoft/skills-for-copilot-studio"

## How the skill works

The skill has two parts: a `SKILL.md` that Copilot reads and a PowerShell script that does the actual work.

### The skill definition

The [SKILL.md](https://github.com/troystaylor/SharingIsCaring/blob/main/skills/install-skills/SKILL.md) file tells Copilot when and how to use the skill:

```yaml
---
name: install-skills
description: 'Install Copilot skills from GitHub repositories. Use when: adding
  skills, cloning skill repos, configuring chat.agentSkillsLocations, setting up
  skills for Copilot Studio.'
argument-hint: 'Optionally provide repo URL and skills subfolder path'
---
```

The body of the file includes a procedure section with exact commands Copilot should run, parameter documentation, and a description of what each step does. Copilot matches user requests like "install skills from this repo" to this skill and follows the procedure.

### The PowerShell script

The [install-skills.ps1](https://github.com/troystaylor/SharingIsCaring/blob/main/skills/install-skills/install-skills.ps1) script does three things:

1. **Creates the skills directory** at `%USERPROFILE%\.copilot\skills` if it doesn't exist
2. **Clones the repository** (or pulls latest if already cloned)
3. **Updates VS Code settings** by adding the skills path to `chat.agentSkillsLocations`

The script detects whether you're running VS Code Insiders or stable and updates the correct `settings.json` automatically. If neither exists, it creates a new settings file for Insiders.

## Use it with different repositories

The script accepts two parameters:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `-RepoUrl` | `https://github.com/microsoft/skills-for-copilot-studio` | The Git repository to clone |
| `-SkillsSubPath` | `skills` | Path inside the repo where skill files live |

Point it at any skills repository:

```powershell
# Default - Microsoft's Copilot Studio skills
& "$env:USERPROFILE\.copilot\skills\SharingIsCaring\skills\install-skills.ps1"

# Custom repo with skills at the root
& "$env:USERPROFILE\.copilot\skills\SharingIsCaring\skills\install-skills.ps1" -RepoUrl "https://github.com/org/custom-skills" -SkillsSubPath ""

# Custom repo with skills in a different folder
& "$env:USERPROFILE\.copilot\skills\SharingIsCaring\skills\install-skills.ps1" -RepoUrl "https://github.com/org/repo" -SkillsSubPath "src/copilot-skills"
```

Or skip the terminal entirely and tell Copilot:

> "Install skills from https://github.com/org/custom-skills with skills at the root"

Each invocation adds a separate path to `chat.agentSkillsLocations`, so you can stack multiple skill repositories without overwriting previous ones.

## Inside the script

The script breaks down into four sections.

### Clone or update the repo

```powershell
$SkillsRoot = "$env:USERPROFILE\.copilot\skills"
$RepoName = ($RepoUrl -split '/')[-1] -replace '\.git$', ''
$ClonePath = Join-Path $SkillsRoot $RepoName

if (Test-Path $ClonePath) {
    Write-Host "Repo already exists at $ClonePath - pulling latest..."
    git -C $ClonePath pull
} else {
    Write-Host "Cloning $RepoUrl..."
    git clone $RepoUrl $ClonePath
}
```

The repo name gets extracted from the URL automatically. Running the script again pulls latest changes instead of re-cloning.

### Find VS Code settings

```powershell
$SettingsPaths = @(
    "$env:APPDATA\Code - Insiders\User\settings.json",
    "$env:APPDATA\Code\User\settings.json"
)

$SettingsFile = $SettingsPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
```

VS Code Insiders takes priority. If neither settings file exists, the script creates one for Insiders with an empty JSON object.

### Update the settings

```powershell
$Settings = Get-Content $SettingsFile -Raw | ConvertFrom-Json

if (-not $Settings.'chat.agentSkillsLocations') {
    $Settings | Add-Member -NotePropertyName 'chat.agentSkillsLocations' -NotePropertyValue @()
}

$Locations = @($Settings.'chat.agentSkillsLocations')
if ($NestedSkillsPath -notin $Locations) {
    $Locations += $NestedSkillsPath
    $Settings.'chat.agentSkillsLocations' = $Locations
    $Settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile
}
```

The script reads existing settings, checks whether the path is already registered, and only writes if it needs to add something new. Your other VS Code settings stay untouched.

## What are Copilot skills?

Skills are markdown instruction files that extend what GitHub Copilot can do in agent mode. Each skill includes a `SKILL.md` file with a description, invocation patterns, and detailed instructions that Copilot follows when the skill matches a user request.

The `chat.agentSkillsLocations` setting tells VS Code where to scan for these skill files. Once configured, Copilot automatically discovers and loads them—no extension installation required.

Microsoft's [skills-for-copilot-studio](https://github.com/microsoft/skills-for-copilot-studio) repository includes skills for common workflows like project setup, code review patterns, and Copilot Studio integrations. Community repositories can follow the same structure to share domain-specific skills.

## Prerequisites

- [Git](https://git-scm.com/) installed and on your PATH
- [VS Code](https://code.visualstudio.com/) or VS Code Insiders
- [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) extension with agent mode enabled
- PowerShell 5.1+ (included with Windows)

## Resources

- [install-skills skill and script](https://github.com/troystaylor/SharingIsCaring/tree/main/skills/install-skills)
- [install-skills.ps1 script](https://github.com/troystaylor/SharingIsCaring/blob/main/skills/install-skills/install-skills.ps1)
- [Microsoft skills-for-copilot-studio repository](https://github.com/microsoft/skills-for-copilot-studio)
- [GitHub Copilot agent mode documentation](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
