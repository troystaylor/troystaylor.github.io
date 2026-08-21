---
layout: post
title: "Fill emailed forms in Copilot Cowork with skills alone"
date: 2026-08-21 15:00:00 -0400
categories: [Copilot Studio, Automation]
tags: [Copilot Cowork, Microsoft 365 Copilot, Agent Skills, Forms, PDF, AcroForm, Purview, Privacy, Automation]
description: "A Copilot Cowork plugin that triages emailed PDF, Word, and Excel attachments, fills what it can resolve, asks about the rest in one batch, verifies the result, and drafts a reply to the sender. No MCP server, no connector, nothing to configure."
---

Somebody emails you a new starter packet: a Word form, a travel spreadsheet, a benefits guide you're not supposed to touch, and a PDF declaration. Half the fields are already in your directory profile. The other half you've typed into three forms this year. [Form Autofill for Copilot Cowork](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Form%20Autofill) triages the attachments, fills what it can resolve, asks you about the rest in one batch, verifies the files, and drafts a reply back to the sender for your approval.

It needs Copilot Cowork and nothing else. No MCP server, no custom connector, no OAuth app, no API keys, no Azure resources. The `manifest.json` has no `agentConnectors` block at all, because there's nothing to connect to. Testing also ruled out a hosted PDF-filling tool: Cowork fills AcroForms natively and keeps the form layer editable.

## Three skills

| Skill | Role |
|---|---|
| `form-autofill` | Orchestrates triage, fill, verify, and reply |
| `profile-interview` | Collects missing details in one batched ask |
| `profile-vault` | Persists reusable answers so you aren't asked twice |

## Every field lands in one of three tiers

The tier decides the behavior, and the behavior is the whole design.

| Tier | Source | Persisted | Behavior |
|---|---|---|---|
| 1 | Directory profile, fetched live | No | Filled silently |
| 2 | You, once | Yes, in the vault | Filled from the vault if fresh |
| 3 | You, every time | **Never** | Always asked, never stored |

Tier 3 covers government identifiers, tax numbers, bank and payment details, passports, visas, health information, credentials, and signatures. The friction is deliberate. If you ask the vault to save one of these for convenience, it declines and explains why.

Tier 1 values are never cached. Caching them creates a second source of truth that goes stale without telling you. When the directory profile can't be retrieved, those fields drop to Tier 2 and get asked instead of guessed. Degrading into more questions is always correct; inventing a value never is.

For Tier 3 fields the skills go further and recommend leaving the field blank so you complete it by hand before sending. Typing a national ID into a conversation is a disclosure on its own, whatever happens to it afterwards. A form returned with three blanks and a note explaining them beats one filled at that cost.

## The vault is optional, and it lives outside the skills folder

Saved answers go to `/Documents/Personal/form-profile.md` in your OneDrive, as plain Markdown you can read, correct, or delete yourself.

The location matters. Cowork lets you share skills with colleagues, and a vault stored inside a skill folder would be shared along with it. Keeping the data separate means sharing the skill shares the protocol and nothing else.

The vault is opt-in and nothing depends on it. Decline, and the skills ask you for Tier 2 details each time. Filling, verification, and the reply all behave identically. The vault exists only to stop you retyping the same answers. It's never created silently either: on first use the skill explains what it will hold, where it lives, what it will never hold, and that you can delete it whenever you want.

The file keeps a permanent **Never Stored** section listing the fields that are deliberately absent, so a later session doesn't helpfully fill the gap. Apply a **Confidential sensitivity label** once it exists. Purview governs Cowork, so the label gives you real DLP enforcement and audit instead of relying on the skills' own good behavior.

## Completed forms are not data sources

Testing surfaced a contamination path worth knowing about, whether or not you use this plugin.

A filled form sitting in OneDrive becomes discoverable to later runs. In testing, a completed travel questionnaire was found by name and used as a data source for an external credit application. Output from one task became input to another, with a different audience and no confirmation the values were still current.

The skills now prohibit that explicitly. Values come from exactly three places: the directory profile, the vault, and answers you give in the current run. An absent vault means ask. No searching OneDrive for a lookalike file, no reading a completed form as a stand-in. If a file that looks like a profile turns up, the skill says it exists and asks whether you want it used rather than reading it for values.

Two things follow for anyone running agents over a document library:

- Clear out completed forms you don't need. They're findable.
- A governed vault beats an ad-hoc file. One confirmed source with provenance dates and an explicit prohibited-field list is safer than whatever a filename search happens to surface.

## What the skills can and cannot promise

The skills control one thing: whether a value is written to the vault. They don't control platform-level retention, and they don't claim to.

Microsoft 365 Copilot personalization and memory can retain details inferred from chat history, stored in your Exchange mailbox, and enhanced personalization is on by default. Whether anything is actually retained depends on tenant and user settings. In testing the memory store was queried directly and came back empty, so treat this as a capability to know about rather than an observed leak. Review what's kept under **Copilot > Settings > Personalization and memory**, where memories can be viewed and cleared. Admins can turn enhanced personalization off tenant-wide.

## What testing established

The plugin ships five fixtures in [test-fixtures/](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Form%20Autofill/test-fixtures) so a run can be scored rather than eyeballed: a 25-field Word form labeled entirely with synonyms, a 10-field Excel form that duplicates eight of those concepts under different labels, a prose benefits guide with no blanks, a real 17-field AcroForm PDF, and a flat scanned PDF with no form layer.

| Question | Answer |
|---|---|
| Can Cowork fill an AcroForm and preserve it? | Yes. Fields stayed editable, and the read-only field was left intact |
| Does it handle a flat, unfillable PDF honestly? | Yes. It reported the problem, offered an alternative, and asked first |
| Is the directory profile retrievable? | Yes. Tier 1 fields filled silently, and missing ones became questions |
| Does it tick consent checkboxes unasked? | No. It asked which consents to give and ticked only those |
| Does it dedupe fields across a packet? | Yes. Overlapping concepts were asked once, not once per form |
| Does the email trigger reach attachments? | Yes. Read from the triggering message with no re-upload |
| Does the reply wait for approval? | Yes. Drafted to the original sender, never sent |
| Does the reply body leak values? | No. Field names only, with every blank itemized |
| Does it flag an external recipient? | Yes. It warned that the form was leaving the tenant |
| Does it surface conflicting sources? | Yes. It disclosed that two sources held different addresses and asked which to use |

Three things remain unproven. The source-restriction rules were added after the contamination incident and haven't been re-exercised, which is the top priority for the next run. The vault itself has never been used in anger, so whether Cowork can reliably rewrite a file it also reads as context is still open. And concurrent event-driven runs may collide on vault writes.

## Trigger it from email

Set up an event-driven task in Cowork:

> When I receive an email with "Forms to complete" in the subject, triage any PDF, Word, or Excel attachments, fill out the ones that are forms, ask me about anything you can't fill, and draft a reply to the sender with the completed files attached.

Scope the trigger with a subject keyword. Without a filter it fires on every email with an attachment and starts drafting replies to real correspondents. Event-driven tasks default to draft-and-approve, so the reply waits for you, and attachments on the triggering message are readable directly.

Keep trigger instructions minimal. Anything in the trigger prompt overrides skill behavior. In testing, a prompt telling the agent to "use the profile vault / saved personal details" sent it searching OneDrive, where it read an unrelated file because no vault existed. Describe what you want done and let the skills decide how.

## Install it

As personal skills, copy the three folders under `skills/` into `/Documents/Cowork/skills/` in your OneDrive. Cowork discovers them at the start of your next session.

As a plugin, package it with the shared template:

```powershell
..\..\'Cowork Plugin Template'\package.ps1
```

Icons are included: `color.png` at 192x192 and `outline.png` at 32x32, rendered from the Fluent UI System Icons **Form** glyph. During development, `-SkipIcons` packages without them.

## Watch out for reserved skill names

Cowork's built-in skills silently override plugin skills with matching names. Observed built-ins include `PDF`, `Word`, `Excel`, `PowerPoint`, `html`, `Calendar Management`, `Daily Briefing`, `Meetings`, `Scheduling`, `Communications`, `Skill Management`, and `goal`. The list varies by tenant and release, so check **Customize > Skills** before naming a new skill. The three names here are clear of every built-in observed so far.

## A few design rules worth stealing

- **One batched ask, never field by field.** In a background run each round trip can sit unanswered for hours, so every outstanding field across every attachment is collected and asked once, grouped by theme, with sensitive questions last.
- **Blank beats wrong.** Nothing is inferred or approximated to make a form look finished. A blank field is a question; a wrong field is a defect that travels to a third party.
- **Verification is mandatory.** Files are re-read after filling to confirm values landed in the fields they were meant for. Silent write failures and off-by-one placement are the likeliest defects and are invisible unless checked.
- **Values never appear in summaries.** Progress narration, recaps, and email bodies reference field names, never values. A recap quoting your date of birth can be forwarded somewhere it doesn't belong.
- **Refusals are respected.** "Skip" is a valid answer to any question. The field is left blank, noted, and not raised again.

## Resources

- [Form Autofill for Copilot Cowork](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Form%20Autofill) — skills, manifest, icons, and test fixtures
- [Build plugins for Copilot Cowork](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development)
- [Copilot Cowork custom skills](https://learn.microsoft.com/microsoft-365/copilot/cowork/use-cowork#create-custom-skills)
- [Microsoft Purview sensitivity labels](https://learn.microsoft.com/en-us/purview/sensitivity-labels)
