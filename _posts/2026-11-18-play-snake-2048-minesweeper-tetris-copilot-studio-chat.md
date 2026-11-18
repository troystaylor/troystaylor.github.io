---
layout: post
title: "Play Minesweeper, Snake, 2048, and Tetris in a Copilot Studio chat"
date: 2026-11-18 14:30:00 -0500
categories: [Power Platform, MCP, Copilot Studio]
tags: [MCP Apps, Copilot Studio, Custom Connectors, Power MCP, Microsoft 365 Copilot, PAC CLI, Games]
description: "Power MCP Games is a custom connector script that serves Snake, 2048, Minesweeper, and Tetris as MCP Apps. Ask a Copilot Studio agent to play and the game opens in the conversation. Here's how the games work, where they render, and how to deploy and extend them."
---

Yesterday's [Power MCP Cards post](/power%20platform/mcp/copilot%20studio/2026-11-17-approval-form-cards-copilot-studio-no-adaptive-cards.html) showed MCP Apps doing serious work: approvals, forms, and status cards. [Power MCP Games](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20MCP%20Games) uses the same pattern for something more fun. Ask a Copilot Studio agent to play Snake, 2048, Minesweeper, or Tetris and the game appears in the conversation.

One connector serves the MCP endpoint, the tools, and the game views. The script hosts the HTML for each game as a `ui://` resource, so there's no web app, storage account, or CDN to deploy. It shares its MCP framework, Fluent styles, and host bridge with the [Power MCP Cards Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Cards%20Template).

## The four games

| Tool | Game | Argument | Ways to play |
| --- | --- | --- | --- |
| `play_snake` | Steer the snake to the food without hitting a wall or yourself | `speed`: `slow`, `normal`, `fast` | Arrow keys or WASD, swipe, on-screen arrows |
| `play_2048` | Slide tiles so matching numbers merge, up to 2048 | `gridSize`: 3 to 6 (default 4) | Arrow keys or WASD, swipe, on-screen arrows |
| `play_minesweeper` | Reveal every safe cell. Your first click is always safe | `difficulty`: `easy` (9×9, 10 mines), `medium` (16×16, 40), `hard` (30×16, 99) | Click to reveal, right-click or flag mode to flag |
| `play_tetris` | Clear lines with falling blocks. A ghost piece shows where the block will land | `level`: 1 to 20 (default 1) | Arrow keys, space to drop, `P` to pause, on-screen buttons |

Every tool returns a plain-text note with the game's settings. The note tells the agent the game is shown, to keep its reply to one short sentence, and what to say if the user can't see the game. A client that can't render MCP Apps still gets a sensible reply, and the agent doesn't try to play the game in text.

## How the games work

Each game is a card with a title, a score, the board, and two actions: a primary button and **Expand**. The primary button is **Start**, **Pause**, **Resume**, or **Restart** for Snake and Tetris, and **New game** for 2048 and Minesweeper.

- **More than one way to play.** A card in a sandboxed frame might never get keyboard focus, so every game also works with on-screen buttons. Snake and 2048 respond to swipes. Minesweeper has a flag-mode toggle for touch screens, where there's no right-click.
- **Pausing.** Snake and Tetris pause when the card is hidden or loses focus, so a game doesn't end while you type in the chat.
- **Expand.** The button asks the host for full screen and the board gets larger. If the host refuses, the button hides itself.
- **Results.** Snake and Tetris draw **GAME OVER** and the score on the board. 2048 shows an overlay with **Try again** (or **Keep going** after you reach 2048). Minesweeper's smiley changes face. A hidden announcement tells screen readers the result.
- **Theme.** Each game has its own look from a classic reference: a Nokia 3310 green LCD for Snake, a cream and orange phone bezel for 2048, a Windows 95 window for Minesweeper, and a Super NES-style screen for Tetris. The colors are fixed, so the games look the same in light and dark themes.

When a game ends, the card tells the agent with `ui/update-model-context`, for example "The user finished a game of Snake with a score of 12." The agent can congratulate the player or offer another round. The connector keeps no scores itself.

## Where games render

| Surface | Renders the game? |
| --- | --- |
| Copilot Studio preview chat | Yes. All four games have been played there |
| Microsoft 365 Copilot | Yes |
| Teams and web chat | No |
| Any client without MCP Apps support | No. The tool result carries a plain-text note instead |

See [Use MCP apps in Copilot Studio](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/mcp-apps) for the current host support.

## Deploy it

You need a Power Platform environment where you can create custom connectors, a Copilot Studio agent in a tenant with MCP Apps rendering, and the [Power Platform CLI](https://learn.microsoft.com/power-platform/developer/cli/introduction).

1. Copy the [Power MCP Games folder](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20MCP%20Games).
2. In `apiDefinition.swagger.json`, replace `your-api-host.com` with your own host name. The script handles the MCP request itself, so the host doesn't need to serve anything.
3. In `apiProperties.json`, set `publisher` to your name.
4. Deploy the connector:

   ```powershell
   pac connector create `
       --api-definition-file apiDefinition.swagger.json `
       --api-properties-file apiProperties.json `
       --script-file script.csx `
       --environment <YOUR_ENVIRONMENT_ID>
   ```

5. In Copilot Studio, open your agent, go to **Tools**, select **Add a tool**, choose **Connector**, and pick **Power MCP Games**.
6. Add all four tools and open the preview chat.

Try these prompts:

| Prompt | What you should see |
| --- | --- |
| "Let's play Snake." | A board with a three-segment snake and a Start button |
| "Play Snake on fast." | The same game at a faster speed |
| "Start a game of 2048 on a 5 by 5 grid." | A 5×5 board with two tiles |
| "Play hard Minesweeper." | A 30×16 board with 99 mines. Use Expand for more room |
| "Play Tetris starting at level 5." | A 10×20 board, a next-piece preview, and controls beside it |
| After a game ends: "How did I do?" | The agent knows your score from the result the card reported |

Click the board before you use the keyboard, so the card has focus.

## Add your own game

1. Add a `ui://` URI constant and register the view in `RegisterGameViews` with `handler.AddUiResource(...)`.
2. Add a `play_*` tool in `RegisterGameTools`. Return `GameResult(text, data)`, where `data` holds the settings the game needs. Keep the schema flat, with no `$ref` and no multi-type arrays, because Copilot Studio drops tools that use them. Clamp numeric arguments in the handler with `GetInt` instead of putting bounds in the schema.
3. Add a view method to `GameViews`, with a CSS constant and a JavaScript constant.
4. In the JavaScript, call `gameShell({ title, board, stats, controls })`. It builds the card and returns a small kit with `stat`, `status`, `announce`, `label`, `onPrimary`, `onKey`, `onSwipe`, `onAway`, `onStop`, and `report`.
5. End the script with `start('Name', sampleData, yourFunction, ['inline', 'fullscreen'])`. The sample data lets the page run on its own in a browser for development.

The JavaScript lives in C# verbatim strings, so use single quotes only. Show data with `textContent`, never `innerHTML`.

## Security and limits

The views declare no content security policy, so the host applies its restrictive default: no network access and no external scripts. The games load nothing from a CDN. They run entirely in the card, and the connector stores no scores. It makes no outbound calls unless you set `APP_INSIGHTS_CONNECTION_STRING` in `script.csx`, which turns on optional Application Insights telemetry. Add authentication before you expose the connector beyond a test environment.

- The connector is request and response. It can't push updates to a card, and a high score lasts only as long as the card is open.
- Copilot Studio provides only theme, language and region, and display mode as host context. It doesn't support tool cancellation, partial tool input, file downloads, or MCP logging.
- Minesweeper's hard board is about 690 pixels wide and scrolls sideways in a narrow card. Use Expand.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| The agent answers in text and no game appears | You're in a surface that doesn't render MCP Apps, such as Teams or web chat. In preview chat, check that the `resources/read` for the game isn't failing. A failed read hides the card without changing the tool result. |
| The game appears but the keyboard does nothing | Click the board, or use the on-screen buttons or a swipe. |
| Right-click doesn't flag a cell | Some hosts block the context menu. Turn on **Flag mode** under the board. |
| Expand does nothing and then disappears | The host doesn't offer full screen. The board stays inline. |
| A tool is missing in Copilot Studio | Copilot Studio drops tools whose schema has `$ref` or multi-type arrays. Keep custom schemas flat. |
| The agent says it can't see a tool you added | The agent keeps the tool list from when you added the connector. Remove the connector's tools and add them again. |

The [readme](https://github.com/troystaylor/SharingIsCaring/blob/main/Power%20MCP%20Games/readme.md) has the full list.

## Resources

- [Power MCP Games](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20MCP%20Games)
- [Power MCP Cards Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Cards%20Template), the companion for approvals, forms, and status cards
- [Use MCP apps in Copilot Studio](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/mcp-apps)
- [MCP Apps support in Power MCP template](/power%20platform/mcp/custom%20connectors/2026-01-27-mcp-apps-power-mcp-template.html), the earlier post on the base template
