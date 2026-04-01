---
layout: post
title: "ppcv: offline Power Platform custom connector validator"
date: 2026-04-01 14:00:00 -0500
categories: [Power Platform, Developer Tools]
tags: [Custom Connectors, CLI, Validation, Node.js, CI/CD, Power Platform, paconn]
description: "A Node.js CLI tool that validates Power Platform custom connector files offline—checks apiDefinition.swagger.json, apiProperties.json, and script.csx against Microsoft's documented requirements."
---

The `paconn validate` command requires signing into Power Platform, connecting to an environment, and waiting for a round trip to the service. That friction adds up when you're iterating on a connector locally, and it doesn't work at all in offline or air-gapped environments.

I built [ppcv](https://www.npmjs.com/package/ppcv) (Power Platform Connector Validator) to solve this. It runs entirely offline, checks all three connector files against Microsoft's documented schemas and requirements, and returns structured output for CI/CD pipelines. No sign-in, no environment, no network calls.

Source: [GitHub repository](https://github.com/troystaylor/ppcv)

## Install

```bash
npm install -g ppcv
```

Or run without installing:

```bash
npx ppcv ./MyConnector
```

## Usage

```
ppcv [path] [options]

Arguments:
  path          Path to a connector folder or apiDefinition.swagger.json
                (defaults to current directory)

Options:
  --json, -j    Output results as JSON (for CI/CD pipelines)
  --help, -h    Show help
  --version, -v Show version
```

Point it at a connector folder containing `apiDefinition.swagger.json`, `apiProperties.json`, and optionally `script.csx`. It validates all three files and reports errors and warnings.

```bash
# Validate a connector folder
ppcv ./MyConnector

# Validate the current directory
ppcv

# JSON output for CI/CD
ppcv ./MyConnector --json

# Pipe JSON to jq to extract just errors
ppcv ./MyConnector -j | jq '.errors'
```

## What it checks

### apiDefinition.swagger.json

- **Required fields**: `swagger`, `info`, `paths` must exist
- **Swagger version**: Must be `"2.0"` (Power Platform doesn't support OpenAPI 3.x)
- **Host and basePath format**: Validates structure
- **Unique operationIds**: Catches duplicates that cause silent failures during import
- **Response definitions**: Every operation must define at least one response
- **Parameter completeness**: Every parameter must have `name`, `in`, `type`, and `required`
- **Path parameter encoding**: Path parameters must include `x-ms-url-encoding` (Power Platform requires this to handle special characters)
- **Array schemas**: Array types must include `items` definition
- **Security definitions**: Must include `type` field
- **Connector metadata**: Checks for `x-ms-connector-metadata` presence

### apiProperties.json

- **Icon brand color**: `properties.iconBrandColor` must exist and be valid hex format
- **Connection parameters**: Validates parameter types and OAuth `identityProvider` values
- **Script operations cross-reference**: Every entry in `scriptOperations` is checked against the swagger's `operationId` values—catches typos and stale references after renaming operations
- **Capabilities**: Validates against known capability values

### script.csx

These checks follow the [documented requirements for custom connector code](https://learn.microsoft.com/connectors/custom-connectors/write-code):

- **File size**: Must be under 1 MB (the platform limit)
- **Class structure**: Must contain a class named `Script` that extends `ScriptBase`
- **Entry point**: Must implement `ExecuteAsync` method
- **Namespace restrictions**: Only validates `using` statements against the [supported namespace allowlist](https://learn.microsoft.com/connectors/custom-connectors/write-code#supported-namespaces)
- **No direct HttpClient**: Flags `new HttpClient()` — custom connector code must use `this.Context.SendAsync` instead
- **Formatting ambiguity**: Flags bare `Formatting.None` or `Formatting.Indented` — must be fully qualified as `Newtonsoft.Json.Formatting.None` to avoid ambiguous reference errors at runtime
- **Balanced braces**: Catches truncated files where the upload was cut off mid-script

## Why offline matters

`paconn validate` is the official Microsoft tool, but it requires:

1. A Power Platform environment
2. A valid sign-in session
3. Network connectivity to the service
4. Python installed (paconn is a Python CLI)

That's fine for final validation before publishing, but it's too much friction for the inner development loop. When you're editing a swagger file and want to catch a missing `x-ms-url-encoding` or a typo in `scriptOperations`, you want feedback in seconds without leaving your terminal.

ppcv fills that gap. It catches the structural issues that cause connector imports to fail or operations to silently break—before you push to an environment.

## JSON output for CI/CD

The `--json` flag outputs structured results:

```json
{
  "connector": "MyConnector",
  "path": "/path/to/MyConnector",
  "valid": true,
  "operations": 12,
  "errors": [],
  "warnings": ["..."],
  "files": {
    "apiDefinition.swagger.json": { "valid": true, "errors": [], "warnings": [] },
    "apiProperties.json": { "valid": true, "errors": [], "warnings": [] },
    "script.csx": { "valid": true, "errors": [], "warnings": [] }
  }
}
```

The `valid` field is `false` if any file has errors. Warnings don't affect the `valid` flag. Each file gets its own validation result so you can pinpoint which file has problems.

## GitHub Actions integration

Add connector validation to your CI pipeline:

```yaml
- name: Validate connectors
  run: |
    npx ppcv ./MyConnector --json > result.json
    if [ $(jq '.valid' result.json) = "false" ]; then
      jq '.errors[]' result.json
      exit 1
    fi
```

### Batch validate all connectors in a repo

```bash
for dir in */; do
  if [ -f "$dir/apiDefinition.swagger.json" ]; then
    ppcv "$dir" --json
  fi
done
```

This loops through every subdirectory that contains an `apiDefinition.swagger.json` and validates each one. Use this to validate an entire connector repository in one pass.

## GitHub Copilot integration

ppcv works well as part of a GitHub Copilot workflow. Since Copilot can run terminal commands, you can ask it to validate your connector at any point during development.

### Copilot instructions

Add a rule to your `.github/copilot-instructions.md` or a `.instructions.md` file so Copilot runs validation automatically after editing connector files:

```markdown
## Connector validation

After editing `apiDefinition.swagger.json`, `apiProperties.json`, or `script.csx`,
run `npx ppcv .` in the connector directory and fix any errors before committing.
```

With this instruction, Copilot validates your connector files as part of its workflow—catching missing `x-ms-url-encoding`, duplicate operationIds, or stale `scriptOperations` references before you push.

### Ask Copilot to validate

In any Copilot chat session, ask directly:

- "Run ppcv on the Coupa connector folder"
- "Validate all connectors in this repo"
- "Check if my swagger file has any issues"

Copilot runs the command, reads the output, and explains any errors or warnings in context. The `--json` flag gives Copilot structured output that's easier to parse than the human-readable format.

### Fix errors in the same conversation

The real value is the feedback loop. Copilot can run ppcv, see that `scriptOperations` references an operationId that doesn't exist in the swagger, and fix the typo in the same conversation—without you switching between the terminal and editor.

## Resources

- [ppcv on npm](https://www.npmjs.com/package/ppcv)
- [ppcv source code](https://github.com/troystaylor/ppcv)
- [Write code in a custom connector](https://learn.microsoft.com/connectors/custom-connectors/write-code) — Microsoft Learn
- [paconn CLI](https://learn.microsoft.com/connectors/custom-connectors/paconn-cli) — the official online validator
