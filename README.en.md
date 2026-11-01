# ai-workspace

**One workspace for all your AI tools.** ChatGPT, Claude, Codex, Grok, Kimi, Qwen, ZCode — use any of them and switch
between them without losing your rules, memory, skills, connections or project history.

[Русская версия →](README.md)

---

## Why

Usually everything important lives **inside** a particular AI: instructions in its settings, memory in its
cloud, skills in its folder, chats in its history. Account banned, a better model came out, or you just want
a change — and you start from scratch.

ai-workspace flips it: **everything lives in one folder you own, in open formats (markdown, JSON)**, and AI
tools just plug into it. Switch AI — point the new one at the same folder, and it immediately knows who you
are, how to work with you, and where each project stands.

## What you get

```
~/AI/
├── rules/core.md        how to work with me — rules for any AI
├── memory/profile.md    who I am and what I do — profile
├── skills/              skills (open SKILL.md format)
├── mcp/servers.json     connections (MCP) — no keys inside
├── projects/            projects; each has:
│   └── Project/
│       ├── AGENTS.md        project map for the AI
│       ├── STATUS.md        where we are now
│       └── chronicle/       what was done, by whom, when and why
├── chats/               ChatGPT/Claude export archive (optional)
└── prompts/             utility prompts
```

One command, `aiw sync` (also runs every evening), pushes it to your AI tools:

| | Rules & profile | Skills | File access (MCP) | Chronicle |
|---|---|---|---|---|
| **Claude Code** | `~/.claude/CLAUDE.md` | ✓ | ✓ | ✓ enforced by a hook |
| **Claude Desktop** | text for settings | — | ✓ | by rule |
| **Codex** | `~/.codex/AGENTS.md` | ✓ | ✓ | by rule |
| **Grok Build** | `~/.grok/AGENTS.md` | ✓ (reads Claude skills and `~/.agents`) | ✓ | by rule |
| **Kimi Code** | `~/.kimi-code/AGENTS.md` | ✓ (`~/.agents/skills`) | ✓ | by rule |
| **Qwen Code** | `~/.qwen/QWEN.md` + reads `AGENTS.md` in projects | ✓ | ✓ | by rule |
| **ZCode, other agents** | `AGENTS.md` in the project folder | — | — | by rule |
| **ChatGPT, Grok (web)** | text ≤ 1500 chars in instructions | — | — | gives the entry as text |
| **Kimi, Qwen Chat, Meta AI (web)** | messages for "memory" | — | — | gives the entry as text |

Agents are linked only if installed: install Grok Build or Qwen Code later and the next `aiw sync`
picks it up. Meta AI isn't available in every country and has no instructions besides memory.

## Secure by default

- **Keys and passwords never live in the workspace.** For MCP use `aiw secret set NAME` (macOS Keychain,
  system keyring or `~/.secrets` readable only by you); configs reference `"secret:NAME"`.
- **Only the core goes to the git backup** (rules, profile, skills, settings). Projects and keys never do.
- **Every commit is scanned for tokens and private keys.** Anything suspicious — the commit is cancelled.
- **Your existing files are never overwritten:** anything in the way goes to `.aiw/backups/`, and skills you
  created directly in an AI tool are adopted into `skills/`.
- AI tools are instructed not to read `.secrets`, `.env` or keys without a direct request.

## Install

**macOS / Linux** — in Terminal:
```bash
curl -fsSL https://raw.githubusercontent.com/sobolevandrey/ai-workspace/main/install.sh | bash
```

**Windows** — in PowerShell:
```powershell
irm https://raw.githubusercontent.com/sobolevandrey/ai-workspace/main/install.ps1 | iex
```

The installer adds what's missing (git, Python; Node.js if you agree), asks for language, folder and name,
creates the workspace and links it to the AI tools it finds. The engine lives separately in `~/.ai-workspace`,
your data in `~/AI`, so updates never touch your files.

## After installing — 3 steps

1. **Describe yourself.** `~/AI/memory/profile.md` (who you are, projects, tools), and optionally tweak
   `~/AI/rules/core.md` (how to answer you). Any AI can help you fill these in.
2. **Run `~/AI/aiw sync`** and paste the texts from `~/AI/.aiw/out/` into web apps:
   - **Claude** → Settings → instructions for Claude ← `custom-instructions.txt` (already in your clipboard);
   - **ChatGPT** → Settings → Personalization → Custom instructions ← `chatgpt.txt`;
   - **Grok** → Settings → Customize → instructions ← `chatgpt.txt`;
   - **Kimi, Qwen Chat, Meta AI** and other apps with memory → as chat messages ← `memory-messages.txt`.
3. **Work in projects.** `~/AI/aiw new-project Name` (group: `Clients/Name`) and open the project folder in
   Codex, Claude, Kimi, ZCode — they read the map, the status and the chronicle.

## Commands

| Command | What it does |
|---|---|
| `aiw sync` | Links rules, skills, hook, MCP; backs up. Runs daily at 21:07 on its own |
| `aiw new-project Name` | New project from the template (`Group/Name` for groups) |
| `aiw secret set NAME` | Store a key for an MCP connection |
| `aiw doctor` | Install check: what's found and configured |
| `aiw check` | Chronicle debts and bloat per project (read-only) |
| `aiw update` | Update ai-workspace (your files are untouched) |
| `aiw import-chats` | ChatGPT/Claude exports from `chats/_raw/` → markdown archive |
| `aiw uninstall` | Unlink from AI tools. Your data stays |

`aiw` is `~/AI/aiw` (`~/AI/aiw.cmd` on Windows).

## Projects: status and chronicle instead of hoarding chats

Keeping every chat is noise. Instead each project has two files (the same idea as Anthropic's progress
file for long-running agents and Cline's Memory Bank):

- **`STATUS.md`** — where we are: in progress, blockers, next step. Overwritten.
- **`chronicle/YYYY-MM.md`** — a short entry per meaningful session: when, which AI, why, what was done,
  what was decided and why, which files. Append-only.

Every AI reads the status and latest entries at the start and updates them at the end. Claude Code is
forced to (hook). With [SpecStory](https://specstory.com) installed, full agent transcripts are saved
into the project automatically too.

## Nightly check: the system heals itself

AI tools forget. So every evening `aiw sync` compares what changed in each project with what was logged
and puts a "⚠ Needs attention" block at the top of `STATUS.md`: unlogged work, status behind the
chronicle, last month not summarized, a file has bloated. Every AI reads the status first — and closes
the debt first. Once closed, the block disappears on its own. An overview of all projects is in `PROJECTS.md`.

## Still lean after two years

Only a little goes into each conversation: rules and profile (~6000-char budget), `STATUS.md` (≤ 1 page),
`SUMMARY.md` and the 2–3 latest entries. Everything else stays on disk but out of the context.

| What grows | How it's kept in check |
|---|---|
| Chronicle | one file per month; monthly 5–10-line summary in `chronicle/SUMMARY.md` |
| `STATUS.md`, `AGENTS.md` | line limits, the check warns about bloat |
| Rules and profile | a character budget; narrow rules move into skills (loaded only when needed) |
| Skills | a warning after 60; unused ones go to `skills/_archive/` |
| Projects | `PROJECTS.md` with last activity; inactive > 90 days — candidates for `projects/_archive/` |

## Skills and connections

- Found a skill? Ask your AI to put it into `~/AI/skills/<name>/` and run `aiw sync` — it shows up in Claude
  and Codex. Skills installed directly into Claude/Codex are adopted into `skills/` by `aiw sync`.
- Connections (MCP) are described once in `~/AI/mcp/servers.json` and pushed to Claude Desktop, Claude Code
  and Codex. Access to the `~/AI` folder itself is on by default.

## Backups — honestly

| What | How |
|---|---|
| Core: rules, profile, skills, settings | a private GitHub repo (the installer offers to create it) |
| Projects and keys | **Time Machine** / a cloud backup (Backblaze, Arq) / File History on Windows |

GitHub isn't for everything: it rejects files over 100 MB, and keys don't belong in git even in a private
repo. No project backup = a dead laptop takes your projects with it.

## Switching AI — checklist

1. A new AI with file access → open the project folder (or `~/AI`) in it. Done.
2. A web app → paste the text from `~/AI/.aiw/out/` into its settings.
3. A new tool with its own rules/skills folders → add the paths in `aiw.py` (or open an issue).

## Requirements

macOS 12+, Linux (systemd or cron), Windows 10/11. Python 3.9+, git. Node.js — for file access from Claude Desktop.
Tested on macOS and Linux; the Windows part follows the docs — please report issues.

## License

MIT. Author — [Andrey Sobolev](https://github.com/sobolevandrey).
