---
name: project-chronicle
description: Keeps a project's history and current state in the workspace (usually ~/AI/projects/<project>/) — the chronicle (chronicle/YYYY-MM.md, what happened and why) and STATUS.md (where we are now). Use when starting work on a project (read), at the end of a meaningful session (update), when asked to "log this" or "update the status", and when asked "what did we do / when / why did we decide / where are we".
---

# Project chronicle and status

| File | Answers | How it's kept |
|---|---|---|
| `STATUS.md` | "Where are we now?" | **Overwritten.** Current state, ~1 page |
| `chronicle/YYYY-MM.md` | "What happened, who, why?" | **Append-only.** Newest entries on top |

Kept automatically: git history (what changed in files) and, if SpecStory is installed, full agent transcripts in `.specstory/history/`.

## Where
- Project: `<workspace>/projects/<project>/`.
- Project inside a group (the group folder contains `.aiw-group`): `<workspace>/projects/<group>/<project>/`.
- No `STATUS.md` or `chronicle/` yet — create them from `projects/_template/`.

## When starting
Read `STATUS.md` (the "⚠ Needs attention" block first), `chronicle/SUMMARY.md` if needed, and the 2–3 latest entries.

## At the end of a meaningful session
(something was decided, done or files changed; don't log quick questions or chit-chat)

1. **Chronicle** — use the file for the month of the entry: a November 1 entry goes to `2026-11.md`, not October’s (create it with a month heading if missing). One entry per session; if this session already has one, extend it.

```markdown
### 2026-01-31 18:40 · Claude · Name
**Why:** one line — the task and why now.
**Done:** 1–4 key points.
**Decision:** what was decided and why; rejected options briefly. (no decisions — omit the line)
**Files:** created/changed, relative paths.
**Next:** open questions, next step.
**Source:** chat title/link, if any.
```

2. **STATUS.md** — mandatory, the session isn't finished without it. Rewrite for the new state ("In progress", "Waiting / blockers", "Next step"),
   update the "Updated" line. Remove finished items — they're in the chronicle now.

Rules: keep it short (5–10 lines), never include passwords or tokens, don't edit old entries — fix
mistakes with a new entry. Always start decisions with `**Decision:**` so search can find them.

## The "⚠ Needs attention" block
The nightly `aiw sync` check puts it at the top of `STATUS.md`: unlogged work, status behind the chronicle,
month not summarized, a file has bloated. If you see it, start the session with it. Don't delete the block:
it disappears on its own once the check sees the debt is closed.

## Monthly summary (`chronicle/SUMMARY.md`)
One file per project, one section per month, newest on top:

```markdown
## 2026-10
- Key results: 2–4 points — what substantively changed.
- Decisions: the month's key `**Decision:**` lines, one line each.
- Carried over: what's still open.
```

Written in the first meaningful session of a new month, from that month's entries. A year later the
whole project history reads in a minute, and old monthly files no longer enter the context.

## Keeping it small
- `STATUS.md` ≤ ~1 page (80 lines): current state only. Finished work is in the chronicle.
- `AGENTS.md` ≤ ~2 pages: the project map. Details go into separate docs, linked.
- A chronicle entry is 5–10 lines. Details live in files; link them.
- Read only the status, `SUMMARY.md` and the 2–3 latest entries. Old months only when asked about history.
- Project finished — move its folder to `projects/_archive/` (chronicle and summary included).

## When asked
- "Where are we / what's next?" → `STATUS.md`.
- "What happened this year / how did the project evolve?" → `chronicle/SUMMARY.md`.
- "What did we do / when / why?" → the chronicle, newest first; search for `**Decision:**`.

## No file access (web chat)
Give a ready entry and the new status text and say which files to paste them into.
