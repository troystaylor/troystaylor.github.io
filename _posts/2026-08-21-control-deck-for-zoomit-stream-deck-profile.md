---
layout: post
title: "Control Deck for ZoomIt: drive Sysinternals ZoomIt from a Stream Deck"
date: 2026-08-21 17:00:00 -0400
categories: [Developer Tools, Automation]
tags: [ZoomIt, Stream Deck, Sysinternals, PowerToys, Windows, Presentation, Screen Recording, Elgato]
description: "A free Stream Deck profile that puts ZoomIt's zoom, annotation, recording, and snipping shortcuts on physical keys, built by reverse-engineering the Stream Deck profile format and reading ZoomIt's source."
---

ZoomIt has 45 addressable keyboard shortcuts. Mid-presentation, you'll remember four of them. [Control Deck for ZoomIt](https://github.com/troystaylor/Control-Deck-for-ZoomIt) is a free Stream Deck profile that puts the rest on physical keys: zoom, draw, pens, highlighters, the break timer, screen recording, snips, OCR, and scrolling panorama capture.

It's a profile, not a plugin. That distinction turned out to be the whole design, so it's worth explaining before anything else.

**Submitted to the Elgato Marketplace.** If you want automatic updates, wait for that release rather than installing the GitHub build by hand. The [GitHub release](https://github.com/troystaylor/Control-Deck-for-ZoomIt/releases) works today, but you'll have to re-import it yourself when a new version ships.

## Why a profile beats a plugin here

ZoomIt exposes no API, no IPC, and no command-line trigger. Its entire control surface is global hotkeys plus single keystrokes while a mode is active. Stream Deck's built-in **Hotkey** action already sends those, for keys and dials alike.

That built-in action is marked `"PrivateAPI": true`, so third-party plugins can't call it, and the SDK has no keyboard API at all. A plugin would mean re-implementing keystroke injection in native code — FFI to `SendInput` or a helper executable — and shipping per-architecture binaries through review to do a worse job than the action Elgato already ships.

A plugin could add exactly two things a profile can't: live state feedback and reading the user's remapped hotkeys. ZoomIt exposes no state, and its defaults never touch disk, so neither is achievable. PowerToys writes to `HKCU\Software\Sysinternals\ZoomIt` only when a hotkey *changes* from its default, so a fresh install has one value: `EulaAccepted`.

## What's on the deck

Three pages on a 5×3 MK.2, 45 keys, 41 of ZoomIt's 45 shortcuts.

| Page | Contents |
|---|---|
| Main | Zoom, Draw, Break, Timer, Snip, Snip Save, OCR, Mirror, DemoType, Record, Rec Crop, Rec Window, Whiteboard |
| Pens | Undo, Erase All, Size +, Blur, five pens, five highlighters |
| Tools | LiveZoom, LiveDraw, Text, Text Right, Panorama, Pano Save, Size -, Center, Copy, Copy Crop, Save, Save Crop, Demo Prev |

Zoom, Draw, Break, LiveZoom, LiveDraw, DemoType, Record, and Panorama are toggles. A second press sends `Esc`, and the icon flips to show the mode is live.

Whiteboard is a Multi Action Switch: one press sends `Ctrl+1` → `K` → `Ctrl+W` — zoom, black pen, blank to white. Ordering matters. Send `K` after `Ctrl+W` and drawing reverts the blank.

Four shortcuts are impossible from a Stream Deck at all: straight line, rectangle, ellipse, and arrow each need a modifier *held* through a mouse drag, and a key only sends press-release.

## Three device layouts

The grid is parameterised in a `device` block, so a new variant is a config file rather than a code change. Model IDs and grid sizes came from Elgato's own per-device defaults in `Program Files\Elgato\StreamDeck\DefaultProfiles`.

| Layout | Device | Keys | Coverage |
|---|---|---|---|
| `layout.config.json` | MK.2 5×3 | 45 over 3 pages | 41 of 45 |
| `layout.xl.config.json` | XL 8×4 | 44 over 2 pages | 43 of 45 |
| `layout.mini.config.json` | Mini 3×2 | 18 over 3 pages | 16 essentials |

The Mini is deliberately minimal. Fitting the full set into six keys needs roughly nine folder pages, which is worse than useless mid-presentation, so it carries four desktop triggers, five pen colours, and five drawing tools.

Coordinates are validated against the declared grid, so a key that would land off the device fails the build instead of being silently dropped. One caution if you build your own variants: the shipped Stream Deck + default profile reports a 5×3 keypad, which contradicts the hardware. Treat 4×2 as correct.

## The profile format rules nobody documents

These came from diffing against working profiles and reading `logs\StreamDeck.log`. Break any of them and you get a silent or misleading failure.

| Requirement | Symptom if violated |
|---|---|
| Page directories named with **UPPERCASE** GUIDs, while manifest references stay lowercase | `RT ERROR: no pages in umbrella` → "content corrupted" |
| Each controller needs `"Type": "Keypad"`; page manifest needs `Name` and `Icon` | Imports successfully, every page is empty |
| `Pages.Default` must be a separate, empty page not listed in `Pages` | Malformed umbrella |
| Parent-folder ("back") action must sit at `0,0` | Stream Deck relocates it there, silently overwriting whatever was at `0,0` |

Folder pages aren't listed in `Pages` at all. They're reached only through a Create Folder action's `Settings.ProfileUUID`.

Key encoding was reverse-engineered from real configured Hotkey actions: `NativeCode` always matches `VKeyCode`, `QTKeyCode` matches for letters and digits but uses ASCII for punctuation and the Qt `0x01000000` enum range for special keys, and `KeyModifiers` is a bitmask with Shift=1, Ctrl=2, Alt=4, Cmd=8. Unconfigured slots use `VKeyCode: -1`, `QTKeyCode: 33554431`, `NativeCode: 146`.

Multi Action compatibility constrains what one key press can do. Hotkey, Delay, and Switch Profile combine; Create Folder, Parent Folder, and Hotkey Switch don't. That's why no key can both send a hotkey and open a folder.

## Import, don't hand-install

Stream Deck keeps its profile index in a binary `Devices` blob under `HKCU:\Software\Elgato Systems GmbH\StreamDeck`. A folder copied into `ProfilesV3` is never registered and is silently ignored. Import is the only reliable path, and the `streamdeck://app/openfile/<url-encoded-path>` deep link works more consistently than the Windows file association.

Two things cost real debugging time here:

- **Never force-kill Stream Deck.** After `Stop-Process -Force`, the next instance either wedges its import subsystem or exits outright. Imports then log `import:` with no `import finished` and hang forever, with no error.
- **Imports hang transiently for no visible reason.** No dialog, no error, nothing after the `import:` line. It isn't the package. Wait a minute and import again — a retry on the same instance usually succeeds.

Stream Deck also flushes profile edits to disk lazily, roughly every 12 seconds, so reading a file back immediately after saving in the UI can show stale data.

## ZoomIt's published shortcuts are wrong in four places

Reading ZoomIt's source in the PowerToys repository turned up four errors in the documented shortcut table:

| Docs say | Actually |
|---|---|
| Size adjust is "Ctrl + Mouse Scroll Up/Down **or Arrow Keys**" | Bare arrows always change zoom level; size needs `Ctrl+Arrow` |
| "Whiteboard \| **W**" and "Blackboard \| **K**" | Those are the white and black *pens*. The boards are `Ctrl+W` and `Ctrl+K`, gated on `GetKeyState(VK_CONTROL)` |
| Pen colours are R/G/B/Y/O/P | There are eight. `W` and `K` are undocumented pens |
| "Start/Stop Panorama **recording**" | Panorama is a scrolling screenshot, stitched to a still image |

Two shortcuts are missing from the table entirely: `Ctrl+Shift+8` for panorama to file and `Ctrl+9` for DemoMirror.

Whiteboard has undocumented conditions too. While the break timer runs, `Ctrl+W` and `Ctrl+K` change the timer background colour instead. Screen blanking is gated on being zoomed, and it's blocked in LiveDraw for user-driven input.

## Two things that will bite you

**Toggles track their own state, not ZoomIt's.** Exit ZoomIt with the physical `Esc` key or a right-click and the toggle desyncs, so the next press sends the wrong command. Press twice to resync. ZoomIt exposes no state to query, so a plugin couldn't fix this either.

**Elevation has to match.** If ZoomIt runs elevated, which PowerToys can be configured to do, but Stream Deck doesn't, UIPI blocks injected input entirely. Run both at the same integrity level.

If the zoom-to-whiteboard transition feels slow, that's ZoomIt's telescoping animation, not the profile. Turn off **Animate zoom** in ZoomIt Options → Zoom.

## Validation

Verified on 2026-08-18 against PowerToys ZoomIt v0.100.2 and Stream Deck 7.4.2:

| Check | Result |
|---|---|
| `Ctrl+1` via synthetic input | Spawned a `ZoomitClass` window |
| `Ctrl+2` via synthetic input | Spawned `ZoomitClass`, held foreground |
| `R` (in-mode red pen) | Accepted, overlay persisted |
| `Esc` | Dismissed cleanly |
| ZoomIt elevation | Not elevated |
| Stream Deck elevation | Not elevated |

Because ZoomIt's overlay takes foreground and both processes run at the same integrity level, injected keystrokes reach it through the same `SendInput` path the built-in Hotkey action uses.

One testing note worth passing on: GDI `CopyFromScreen` doesn't capture ZoomIt's overlay, so pixel sampling can't verify that a mode opened. Enumerate windows instead.

## Icons

The 47 icons are generated from [Fluent UI System Icons](https://github.com/microsoft/fluentui-system-icons). Fluent SVGs hardcode `fill="#212121"`, invisible against black keys, so the build recolours every glyph: recording actions red, pens and highlighters in their own ink colour, everything else white.

```bash
npm install
npm run build:icons       # -> dist/icons/*.png (144x144), dist/svg/*.svg
npm run contact-sheet     # -> dist/contact-sheet.png for visual QA
```

The build resolves the largest available source size, since Fluent redraws each size on its own grid and larger sources carry more detail, and prefers `filled` variants, which read better at key size. It fails loudly if a named icon doesn't exist or has no recolorable fill.

## Build it yourself

```bash
npm run build:profile            # MK.2 (5x3)
npm run build:profile:xl         # Stream Deck XL (8x4)
npm run build:profile:mini       # Stream Deck Mini (3x2)
npm run build:release:all        # every variant -> dist/release/*.streamDeckProfile
```

`--release` omits keys marked `"machineSpecific": true`, which is currently just the ZoomIt launcher key and its absolute path. Paths in configs use `%LOCALAPPDATA%`-style variables expanded at build time, so no username ever lands in source.

ZoomIt isn't included or redistributed here — install it free from [Sysinternals](https://learn.microsoft.com/en-us/sysinternals/downloads/zoomit) or as part of [Microsoft PowerToys](https://github.com/microsoft/PowerToys). This project isn't affiliated with, endorsed by, or sponsored by Microsoft Corporation.

## Resources

- [Control Deck for ZoomIt](https://github.com/troystaylor/Control-Deck-for-ZoomIt) — layout configs, generator scripts, and icon build
- [Releases](https://github.com/troystaylor/Control-Deck-for-ZoomIt/releases) — MK.2, XL, and Mini profiles
- [ZoomIt on Sysinternals](https://learn.microsoft.com/en-us/sysinternals/downloads/zoomit)
- [Microsoft PowerToys](https://github.com/microsoft/PowerToys)
- [Fluent UI System Icons](https://github.com/microsoft/fluentui-system-icons)
