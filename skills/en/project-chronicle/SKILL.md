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
Read `STATUS.md` and the 2–3 latest chronicle entries.

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

2. **STATUS.md** — rewrite for the new state ("In progress", "Waiting / blockers", "Next step"),
   update the "Updated" line. Remove finished items — they're in the chronicle now.

Rules: keep it short (5–10 lines), never include passwords or tokens, don't edit old entries — fix
mistakes with a new entry. Always start decisions with `**Decision:**` so search can find them.

## When asked
- "Where are we / what's next?" → `STATUS.md`.
- "What did we do / when / why?" → the chronicle, newest first; search for `**Decision:**`.

## No file access (web chat)
Give a ready entry and the new status text and say which files to paste them into.
