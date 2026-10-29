---
name: save-to-memory
description: Saves stable facts about the user and work outcomes into workspace files instead of the AI's built-in memory. Use when the user says "remember", "save to memory", "note this".
---

# Save to memory

1. What to save:
   - a stable fact / preference about the user → `memory/profile.md` (right section);
   - project context → `memory/projects/<project>.md`;
   - a decision or outcome in a project → the project chronicle (`project-chronicle` skill).
2. Short, one or two lines, no duplicates.
3. Never save passwords, keys, card or ID numbers.
4. Show what you saved and where. If `memory/profile.md` changed, remind the user to run `aiw sync`.

No file access — give the ready text and name the file to paste it into.
