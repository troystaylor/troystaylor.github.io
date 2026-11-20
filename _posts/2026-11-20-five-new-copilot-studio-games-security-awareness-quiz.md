---
layout: post
title: "Five new Copilot Studio games, including a security awareness quiz"
date: 2026-11-20 16:30:00 -0500
categories: [Power Platform, MCP, Copilot Studio]
tags: [MCP Apps, Copilot Studio, Custom Connectors, Power MCP, Microsoft Copilot, Games, Security Awareness]
description: "Power MCP Games now has nine games. The new five are Cyber Trivia, Word Guess, Sudoku, Breakout, and Solitaire, all served as MCP Apps from one custom connector script. Here's what each game does, how to tune it, and how to use the security quiz with your own questions."
---

[Power MCP Games](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20MCP%20Games) grew from four games to nine. Cyber Trivia, Word Guess, Sudoku, Breakout, and Solitaire join Snake, 2048, Minesweeper, and Tetris. Ask a Copilot Studio agent for one and it appears in the conversation.

Cyber Trivia is the one to look at first. It's a security awareness quiz for employees, played as a game show, and you can fill it with your own questions.

The [first post on the original four games](/power%20platform/mcp/copilot%20studio/2026-11-18-play-snake-2048-minesweeper-tetris-copilot-studio-chat.html) covers deployment, where games render, and how to add your own. This post covers what's new.

## The five new games

| Tool | Game | Main arguments | Ways to play |
| --- | --- | --- | --- |
| `play_cyber_trivia` | Security awareness quiz with a host, a money clock, and a double-value final question | `category`, `count` (5 to 20), `level`, `timed`, `tone`, `companyName`, `reportTo`, `customQuestions` | Tap or click an answer, or press `A` to `D` or `1` to `4`, then **Next** |
| `play_word_guess` | Find a hidden five-letter word | `word`, `maxGuesses` (4 to 8), `hardMode`, `highContrast` | On-screen keyboard, or type and press Enter |
| `play_sudoku` | Fill a 9×9 grid so every row, column, and box holds 1 to 9 | `difficulty`, `puzzle`, `seed` | Tap a cell, then a number. Keys `1` to `9`, arrows, `N` for notes, `Z` to undo, `H` for a hint |
| `play_breakout` | Bounce the ball off the paddle to break every brick, across five wall layouts | `level` (1 to 5), `lives` (1 to 5), `speed` | Drag or move the pointer, arrow keys, on-screen buttons. Tap or press space to launch |
| `play_solitaire` | Klondike in a Windows 98-style window with eight card backs | `drawCount` (1 or 3), `deal`, `cardBack` (1 to 8) | Tap a card, then where it goes. Double-tap sends a card to its pile |

As with the first four games, each tool returns a plain-text note. If the client can't render MCP Apps, the agent says so in one short sentence and doesn't try to play the game in text.

## Cyber Trivia

The quiz uses a fixed bank of 80 questions built into the script. The agent personalizes the quiz but doesn't write security guidance.

- **Topics.** Phishing, passwords and MFA, social engineering, safe browsing, data handling, devices, remote work, using AI safely, physical security, and reporting incidents. Each topic has eight questions, half basic and half intermediate. A mixed quiz takes questions from every topic in turn.
- **Basis.** The questions follow current guidance from CISA, NIST (SP 800-63B, for example, favors length over complexity and drops forced password changes), and Microsoft security documentation. Have your security awareness owner review the bank before you roll it out, and adjust it to your policies.
- **Your details.** `companyName` and `reportTo` fill in the questions, so an answer can say "report it to secops@contoso.com". The defaults are "your company" and "your security team".
- **Game show format.** A host named Pat Ching, an original character, comments on each answer. A question starts at $1,000 and rises by $100 a question up to $2,000, and the last question is worth double. In timed mode, the default, a 20-second clock ticks the value down. A right answer wins what's on the clock, a wrong answer costs the full starting amount, and running out of time costs nothing. Final cash can be negative.
- **Accessible modes.** Set `timed` to `false` for a flat value with no clock, which suits slow readers and screen reader users. Set `tone` to `plain` to turn the host off for a more formal audience.

Try these prompts:

| Prompt | What you should see |
| --- | --- |
| "Quiz me on phishing." | Ten phishing questions, a host introduction, a money clock, and an explanation after each answer |
| "Run a security quiz without the clock or the jokes." | The same quiz with `timed` off and `tone` set to plain |
| "Run a security awareness quiz for Contoso. Send problems to secops@contoso.com." | A mixed quiz whose answers mention Contoso and that address |

### Bring your own questions

Pass `customQuestions` as JSON text, up to 20 questions. Set `category` to `company` to play only your questions, or leave it alone to mix them into a quiz.

```json
[
  {
    "stem": "A visitor asks to borrow your badge to reach the lab. What do you do?",
    "correct": "Say no and call reception",
    "wrong": ["Lend it for five minutes", "Lend it if they leave ID"],
    "explain": "Badges are personal.",
    "action": "Call reception on extension 100."
  }
]
```

### What the quiz doesn't do

- **No record.** The connector stores nothing, and the end screen says so. A result is practice, not a training record.
- **Coaching.** When the quiz ends, the card tells the agent your final cash, how many answers were right, and your weakest topics. The agent can offer follow-up coaching in the chat.
- **Answers aren't secret from the agent.** Not every host lets a card call tools, so the card checks answers itself and the correct answers travel in the tool result. The connector tells the agent not to reveal them, but don't use the quiz where cheating matters.

## Word Guess

The card picks a random word and the agent never sees it. Set `word` only for a themed round where you choose the answer. About 1,000 common words can be answers and about 5,000 words are accepted as guesses. Anything else shakes the row. The lists come from ENABLE, a public-domain word list, ranked with Peter Norvig's word counts.

`hardMode` requires each guess to use the hints already revealed. `highContrast` swaps green and amber for orange and blue.

## Sudoku

The card makes the puzzle, and every puzzle has exactly one solution. Difficulty sets the number of given numbers (40, 34, 28, or 24), which is a rough guide to how hard a puzzle feels. The same `difficulty` and `seed` always make the same puzzle, so you can replay one.

**Hint** fills in the correct number for a wrong cell, the selected empty cell, or the most constrained empty cell, and shows it in italic purple. Hints are counted and shown when you finish. **Check** marks wrong numbers as you go.

## Breakout and Solitaire

Breakout runs a real-time loop in the card, and the ball speeds up as bricks clear. If your host throttles animation in a card, use the on-screen arrow buttons.

Solitaire scores like Windows: +10 to a pile, +5 for turning a card over, −15 for taking a card back, and −100 for recycling in draw one. The same `deal` number always gives the same shuffle. Select **Deck** to cycle through eight card backs, or pass `cardBack` to start with one. The backs are small original drawings, not Microsoft's artwork.

Try these prompts:

| Prompt | What you should see |
| --- | --- |
| "Let's play Word Guess." | An empty 6×5 grid and an on-screen keyboard |
| "Give me a hard Sudoku." | A 9×9 grid with 28 given numbers, a number pad, and Notes, Erase, Undo, Hint, and Check buttons |
| "Play Breakout on fast." | A black board with six rainbow rows and a paddle. Tap to launch the ball |
| "Deal me a draw-three Solitaire game." | A Windows 98-style window with seven columns, a stock pile, four empty foundation piles, and a score and time bar |
| "Deal me Solitaire with the robot card back." | The same table with the robot design on the face-down cards |

## What changed in the shared card

The new games pushed a few changes into the shared `gameShell`, so they're available when you add your own game.

- **Fixed card height.** The frame height must not change while a game is played. Reserve space for anything that appears later. Cyber Trivia measures a hidden copy of its tallest question up front. As a safety net, the host bridge lets the frame grow but never shrink while it's inline.
- **No banners.** Show results on the board itself (a canvas overlay, a shaking row, a highlighted cell) or in the `intro` line, so the card never changes size.
- **New config.** `cls` adds a class for per-game styling (`w95` gives the shared Windows 95 window), `intro` adds a line under the header, `mid` places an element between the first and second stat, and `screen` puts the stats and board in one bordered screen.
- **New helpers.** `mulberry32(seed)` and `shuffle(list, rng)` give replayable randomness, `fmtTime(seconds)` formats a clock, `makeTimer(tick)` runs it, and `kit.disable(true)` turns off the primary button.

## Limits

- Cyber Trivia and the other games run in the card, so a score lasts only as long as the card is open.
- Solitaire doesn't support dragging. Tap a card, then tap where it goes.
- Sudoku's difficulty is a count of given numbers. A hard puzzle might still feel easy.
- Teams and web chat still don't render MCP Apps. Games appear in the Copilot Studio preview chat and Microsoft Copilot.

## Update an existing connector

If you deployed Power MCP Games already, copy the latest files from the folder and update the connector with the same `pac connector` command from the first post. Then remove the connector's tools from your agent and add them again. The agent keeps the tool list from when you added the connector, so it won't see the five new tools until you do.

## Resources

- [Power MCP Games](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20MCP%20Games)
- [Readme](https://github.com/troystaylor/SharingIsCaring/blob/main/Power%20MCP%20Games/readme.md) with the full tool reference and troubleshooting
- [Snake, 2048, Minesweeper, and Tetris in a Copilot Studio chat](/power%20platform/mcp/copilot%20studio/2026-11-18-play-snake-2048-minesweeper-tetris-copilot-studio-chat.html)
- [Use MCP apps in Copilot Studio](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/mcp-apps)
