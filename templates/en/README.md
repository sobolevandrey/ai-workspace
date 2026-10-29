# My AI workspace

Everything that shouldn't depend on a particular AI lives here: rules, profile, skills, connections,
projects and their history. ChatGPT, Claude, Codex, Kimi, ZCode and future tools just plug into this
folder. Switch AI — lose nothing.

| Folder | What's inside |
|---|---|
| `rules/core.md` | **How to work with me** — the main rules for any AI |
| `memory/profile.md` | **Who I am and what I do** — profile |
| `skills/` | My skills (SKILL.md format) |
| `mcp/servers.json` | Connections (MCP). Keys are not stored here — use `aiw secret set` |
| `projects/` | Projects: each has `AGENTS.md`, `STATUS.md`, `chronicle/` |
| `chats/` | ChatGPT/Claude export archive (optional) |
| `prompts/` | Utility prompts |
| `.aiw/` | Internal: generated texts, backups, log |

## Commands
```
./aiw sync                 push everything to your AI tools (also runs every evening)
./aiw new-project Name     new project ("Clients/Name" for a project inside a group)
./aiw secret set NAME      store a key for MCP
./aiw doctor               health check
./aiw update               update ai-workspace
```

## House rules
1. Work results go into project files, not just the chat.
2. A session in a project → an entry in `chronicle/` + an updated `STATUS.md`.
3. Change rules only in `rules/core.md`, facts about you in `memory/profile.md`, then `./aiw sync`.
4. Keys and passwords live only in `~/.secrets` / `aiw secret set`, never in this folder.
