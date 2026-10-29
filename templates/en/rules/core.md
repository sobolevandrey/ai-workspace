# Core rules for any AI

> The single source of truth for instructions. Edit here → `aiw sync`.
> Keep it short: this text goes into the start of every conversation.

## Who I am
- {{NAME}}. <!-- what you do, role, company -->

## How to talk to me
- Language: English.
- Answer first, details after. No fluff, no preambles.
- If the task is ambiguous and a mistake would be costly — ask one clarifying question; otherwise just do it.
- Say honestly when you're not sure or don't know.

## Working with files
- My work hub is the workspace folder (`~/AI`). Projects live in `projects/`.
- In each project, read its `AGENTS.md` first.
- Save results as files in the project folder, not only in the chat.
- If you learn something stable and useful about me, suggest adding it to `memory/profile.md`.
- Never delete anything without explicit confirmation.
- `.secrets`, `.env`, SSH keys — don't read without a direct request and never print them in chat.

## Projects: status and chronicle
- When starting work in a project, read its `STATUS.md` (where we are) and the latest `chronicle/` entries.
- At the end of a meaningful session: add an entry to `chronicle/YYYY-MM.md` (when, which AI, why, done,
  decision, files, next) and rewrite `STATUS.md`. Details — the `project-chronicle` skill.
- Quick questions outside projects are not logged anywhere.

## Skills and connections
- Install new skills into the workspace `skills/<name>/` (a folder with SKILL.md), not into a specific AI's folder.
  New MCP connections go to `mcp/servers.json`. Then run `aiw sync` (no terminal — ask me to run it).

## Code
<!-- languages, style, tests, git rules -->

## Never
<!-- things to never do -->
