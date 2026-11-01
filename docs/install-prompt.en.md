# Install via your AI (no Terminal)

Open an AI app that can work with files on your computer (Codex, Claude with computer access,
Kimi Work, ZCode, etc.) and send it this whole message:

```
Install ai-workspace for me — a system that keeps my rules, memory, skills and projects
in one folder for all AI tools. Repository: https://github.com/sobolevandrey/ai-workspace

1. Ask my name. Detect my OS and run the installer in the terminal:
   • macOS / Linux:
     curl -fsSL https://raw.githubusercontent.com/sobolevandrey/ai-workspace/main/install.sh | bash -s -- --yes --lang en --name "MY NAME"
   • Windows (PowerShell):
     & ([scriptblock]::Create((irm https://raw.githubusercontent.com/sobolevandrey/ai-workspace/main/install.ps1))) --yes --lang en --name "MY NAME"
   If a step needs my computer password or an install window pops up, explain in plain words
   what to click and wait for me. Never ask me to tell you my password.
2. When it's done, open ~/.ai-workspace/skills/en/aiw-onboarding/SKILL.md and follow it:
   interview me briefly and set the system up for me.

Talk to me in plain language, no jargon. Don't delete anything without my consent.
```

If your AI says it can't run commands, it's a web version without computer access. Open its
desktop app with file access, or install manually per the README (one Terminal command).
