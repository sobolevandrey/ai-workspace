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
- Starting work in a project: read `STATUS.md` and the 2–3 latest `chronicle/` entries. If the status has a
  "⚠ Needs attention" block, handle its items first.
- A session is finished only when BOTH files are updated: an entry in `chronicle/YYYY-MM.md` (month of the
  entry) and a rewritten `STATUS.md`. One without the other is not finished. Details — `project-chronicle` skill.
- First session of a new month: summarize the previous month in `chronicle/SUMMARY.md` (5–10 lines).
- Quick questions outside projects are not logged. Finished projects go to `projects/_archive/`.

## Skills and connections
- Install new skills into the workspace `skills/<name>/` (a folder with SKILL.md), not into a specific AI's folder.
  New MCP connections go to `mcp/servers.json`. Then run `aiw sync` (no terminal — ask me to run it).

## Code
<!-- languages, style, tests, git rules -->

## Never
<!-- things to never do -->
