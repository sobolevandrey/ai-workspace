---
name: aiw-onboarding
description: First-time ai-workspace setup through conversation — interview the person, fill the profile and rules, create first projects, sync, and walk them through pasting instructions into ChatGPT/Claude/Grok/Kimi. Use when asked to "run the ai-workspace onboarding", "set the system up for me", right after installing ai-workspace, or when memory/profile.md is nearly empty.
---

# ai-workspace onboarding

Goal: in 10–15 minutes of conversation the person gets a configured system and knows how to use it.
They may know nothing about tech — you do all the file and command work yourself.

## How to talk
- Plain and friendly, no jargon ("folder", "rules file", not "config", "repository").
- One or two questions at a time. Short answers are fine — don't interrogate.
- End each block with a short "saved: …" so the person sees progress.
- Never ask for or store passwords, keys, card or ID numbers.
- Never delete or move anything without an explicit "yes".

## 0. Check the install
- The workspace is usually `~/AI` (exact path in `~/.ai-workspace.json`, field `workspace`).
- Health check: `~/AI/aiw doctor` (Windows: `%USERPROFILE%\AI\aiw.cmd doctor`).
- Not installed → install per `~/.ai-workspace/docs/install-prompt.en.md` or the README.
- No terminal/file access → say so plainly and suggest the desktop app with computer access; meanwhile
  you can still run the interview and hand over ready file texts.

## 1. Interview
Explain in one sentence: "I'll ask a few questions so any AI immediately knows who you are and how to work
with you. Your answers stay on your computer."

Blocks (skip anything the person doesn't want to discuss):
1. **Who you are.** Name, what you do, role (founder, specialist, student…), field.
2. **Areas and projects.** 2–5 main ones: name + one line on what it is + what's happening now.
   Any clients worth grouping ("Clients/Name")?
3. **Tools.** Which AI tools and services they use (ChatGPT, Claude, Kimi, Grok, Notion, Slack…).
4. **How to answer.** Language; short or detailed; lists or prose; pet peeves about AI answers.
5. **How they write** (optional). Ask for 1–2 of their messages or posts — for style.
6. **Never** (optional). Things to never do: topics, actions, tone.

## 2. Write it down
- `memory/profile.md` — "Who I am", "My areas", "Tools", "Preferences", "How I write".
  Facts, short bullets. Remove the `<!-- … -->` hints from filled sections.
- `rules/core.md` — "Who I am" (one line), "How to talk to me" (language, length, format, don'ts),
  "Never". Leave the other sections alone: they hold the system rules (chronicle, files, skills).
- Budget: `core.md` + `profile.md` together — up to ~6000 characters. This is read in every conversation.

## 3. Create projects
For each project mentioned (with consent):
- `~/AI/aiw new-project Name` (client in a group: `~/AI/aiw new-project Clients/Name`).
- Fill "Goal" and "Context" in the project's `AGENTS.md` from their words.
- In `STATUS.md` — "In progress" and "Next step".
- First entry in `chronicle/YYYY-MM.md`: "Project created in ai-workspace" + what's known.
Existing folders with work? Offer to move them into `~/AI/projects/`. Move only after a "yes";
on macOS/Linux leave a link at the old place (`ln -s new_path old_path`) so nothing breaks.

## 4. Sync
Run `~/AI/aiw sync`. Tell them which AI tools got connected (shown in the output).

## 5. Paste instructions into web apps — together
The texts are in `~/AI/.aiw/out/`. Show the needed text right in the chat (so they can copy it) and walk
them through it step by step — only for the tools they actually use:
- **Claude** → Settings → the instructions field (may be called "Instructions for Claude" / personal preferences) ← `custom-instructions.txt`.
- **ChatGPT** → Settings → Personalization → Custom instructions ← `chatgpt.txt` (fits one field).
- **Grok** → Settings → Customize → Custom instructions ← `chatgpt.txt`.
- **Kimi, Qwen Chat, Meta AI** (memory) → send the messages from `memory-messages.txt` one by one.
Interfaces change: if a setting is named differently, ask for a screenshot and guide from it.

## 6. Backups — honestly
- Say the key thing: projects live only on this computer. No backup = a dead laptop takes your projects.
- macOS: Time Machine to an external drive (Settings → General → Time Machine). Windows: File History.
  Optionally a cloud backup (Backblaze, Arq).
- GitHub backup of rules and profile — optional, if they have an account: install GitHub CLI,
  `gh auth login`, then `~/AI/aiw setup` offers to create a private repo.

## 7. How to use it — 5 lines to finish
1. Working on a project — open your AI in its folder (`~/AI/projects/…`) or say which project you're on.
2. At the end, say "log this" — the AI records what was done and updates the status.
3. Every evening the system syncs and checks itself; anything unlogged shows up in the status for the AI.
4. Learned something new about yourself — "remember this": it goes into your profile, not one service's memory.
5. Switching AI — just open the `~/AI` folder in the new one. Everything is there.

Finally ask: "Anything you'd like to change?" — and edit the files if so.
