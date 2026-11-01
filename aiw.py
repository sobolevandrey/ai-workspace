#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai-workspace — одно рабочее пространство для всех нейросетей / one workspace for all your AI tools.

  aiw setup              первичная настройка                 first-time setup
  aiw sync               разложить всё по нейросетям          sync rules, skills, hook, MCP, backup
  aiw update             обновить ai-workspace                update the engine
  aiw doctor             проверка                             health check
  aiw new-project NAME   новый проект (Группа/Имя — в группе)  new project (Group/Name for groups)
  aiw secret set NAME    сохранить ключ для MCP                store a secret for MCP
  aiw import-chats       экспорт ChatGPT/Claude → markdown     chat exports → markdown
  aiw uninstall          отключить от нейросетей (данные остаются)  unlink from tools (data stays)
"""
import argparse
import getpass
import json
import locale
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import common as C  # noqa: E402
from common import t  # noqa: E402

ENGINE = C.ENGINE
HOME = C.HOME


def say(*a):
    print(*a, flush=True)


def ask(q, default=""):
    try:
        a = input(f"{q} [{default}]: ").strip()
    except EOFError:
        a = ""
    return a or default


def yes(q, default=True):
    a = ask(q + (" (Y/n)" if default else " (y/N)"), "y" if default else "n").lower()
    return a.startswith(("y", "д"))


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ws_paths(cfg):
    ws = Path(cfg["workspace"])
    return ws, ws / ".aiw" / "out", ws / ".aiw" / "backups" / C.TS


# ---------------------------------------------------------------- файлы, которыми управляем
def is_managed(p: Path):
    if p.is_dir():
        return (p / ".aiw-managed").exists()
    try:
        with open(p, encoding="utf-8") as f:
            return C.MARK in f.readline()
    except Exception:
        return False


def remove(p: Path):
    if p.is_symlink() or p.is_file():
        p.unlink()
    elif p.is_dir():
        shutil.rmtree(p)


def place(src: Path, dst: Path, bak: Path, log=True):
    """Симлинк src → dst. Если симлинки недоступны (Windows без режима разработчика) — копия с меткой.
    Чужой файл на месте dst уезжает в бэкап."""
    if dst.is_symlink():
        try:
            if Path(os.readlink(dst)) == src:
                return
        except OSError:
            pass
        dst.unlink()
    elif dst.exists():
        if is_managed(dst):
            remove(dst)
        else:
            keep = bak / dst.relative_to(HOME) if str(dst).startswith(str(HOME)) else bak / dst.name
            keep.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst), str(keep))
            say(t(f"  ! прежний {dst} сохранён в {keep.parent}", f"  ! previous {dst} saved to {keep.parent}"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(src, dst, target_is_directory=src.is_dir())
    except OSError:
        if src.is_dir():
            shutil.copytree(src, dst)
            (dst / ".aiw-managed").write_text("ai-workspace copy\n", encoding="utf-8")
        else:
            shutil.copy2(src, dst)
    if log:
        say(f"  + {dst}")


# ---------------------------------------------------------------- setup
def detect_lang():
    loc = (os.environ.get("LANG") or "") + (locale.getlocale()[0] or "")
    return "ru" if re.search(r"ru|Russian", loc, re.I) else "en"


def copy_templates(ws: Path, lang, name):
    src = ENGINE / "templates" / lang
    made = 0
    for f in src.rglob("*"):
        if f.is_dir():
            continue
        rel = f.relative_to(src)
        dst = ws / rel
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = f.read_text(encoding="utf-8")
            text = text.replace("{{NAME}}", name).replace("{{DATE}}", date.today().isoformat())
            dst.write_text(text, encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(f, dst)
        made += 1
    return made


def write_launchers(ws: Path):
    py = sys.executable
    sh = ws / "aiw"
    sh.write_text(f'#!/bin/sh\nexec "{py}" "{ENGINE / "aiw.py"}" "$@"\n', encoding="utf-8")
    try:
        os.chmod(sh, 0o755)
    except Exception:
        pass
    (ws / "aiw.cmd").write_text(f'@echo off\r\n"{py}" "{ENGINE / "aiw.py"}" %*\r\n', encoding="utf-8")


def cmd_setup(a):
    lang = a.lang or detect_lang()
    C.LANG = lang
    say(t("\n=== ai-workspace: настройка ===\n", "\n=== ai-workspace: setup ===\n"))
    if not a.yes and not a.lang:
        lang = "ru" if ask("Язык / Language (ru/en)", lang).lower().startswith("r") else "en"
        C.LANG = lang
    ws = Path(a.workspace or (str(HOME / "AI") if a.yes else
                              ask(t("Папка рабочего пространства", "Workspace folder"), str(HOME / "AI")))).expanduser()
    old = {}
    if (ws / ".aiw.json").exists():
        old = json.loads((ws / ".aiw.json").read_text(encoding="utf-8"))
        say(t(f"Найдено существующее пространство {ws} — ваши файлы не тронем.",
              f"Existing workspace found at {ws} — your files stay untouched."))
    name = a.name or old.get("name") or (getpass.getuser() if a.yes else ask(t("Как вас зовут?", "Your name?"), getpass.getuser()))
    cfg = {"lang": old.get("lang", lang), "name": name, "names": old.get("names", C.NAMES[old.get("lang", lang)]),
           "schedule": not a.no_schedule and old.get("schedule", True), "version": C.VERSION, "workspace": str(ws)}
    C.LANG = cfg["lang"]
    C.save_config(cfg)
    n = copy_templates(ws, cfg["lang"], name)
    say(t(f"✓ Пространство: {ws} (новых файлов: {n})", f"✓ Workspace: {ws} (new files: {n})"))
    sec = HOME / ".secrets"
    sec.mkdir(exist_ok=True)
    try:
        os.chmod(sec, 0o700)
    except Exception:
        pass
    say(t(f"✓ Ключи и пароли — только в {sec} (вне пространства и вне git)",
          f"✓ Keys and passwords go to {sec} only (outside the workspace and git)"))
    write_launchers(ws)
    if shutil.which("git") and not (ws / ".git").exists():
        run(["git", "init", "-q", str(ws)])
    say("")
    cmd_sync(argparse.Namespace(quiet=False, log=False))

    # приватный бэкап на GitHub
    if shutil.which("git") and run(["git", "-C", str(ws), "remote", "get-url", "origin"]).returncode != 0:
        gh = shutil.which("gh")
        if gh and run([gh, "auth", "status"]).returncode == 0 and not a.yes:
            if yes(t("\nСоздать ПРИВАТНЫЙ репозиторий на GitHub для бэкапа ядра?", "\nCreate a PRIVATE GitHub repo to back up the core?")):
                repo = ask(t("Название репозитория", "Repository name"), "my-ai-workspace")
                r = run([gh, "repo", "create", repo, "--private", "--source", str(ws), "--remote", "origin", "--push"])
                say("✓ " + repo if r.returncode == 0 else "⚠ " + (r.stderr or r.stdout).strip()[:300])
        else:
            say(t("\nБэкап на GitHub (по желанию): установи GitHub CLI (gh), выполни «gh auth login», затем снова «aiw setup».",
                  "\nGitHub backup (optional): install GitHub CLI (gh), run “gh auth login”, then “aiw setup” again."))

    launcher = ws / ("aiw.cmd" if C.OS == "Windows" else "aiw")
    say(t(f"""
=== Готово. Дальше 3 шага ===
1. Заполни о себе: {ws / 'memory' / 'profile.md'}
   и правила: {ws / 'rules' / 'core.md'}
2. Запусти «{launcher} sync» и вставь тексты из {ws / '.aiw' / 'out'} в веб-версии (см. README).
3. Работай в проектах: «{launcher} new-project Имя» → открывай папку проекта в любой нейросети.
""", f"""
=== Done. 3 next steps ===
1. Describe yourself: {ws / 'memory' / 'profile.md'}
   and your rules: {ws / 'rules' / 'core.md'}
2. Run “{launcher} sync” and paste the texts from {ws / '.aiw' / 'out'} into web apps (see README).
3. Work in projects: “{launcher} new-project Name” → open the project folder in any AI tool.
"""))


# ---------------------------------------------------------------- sync
def skill_set(cfg):
    ws = Path(cfg["workspace"])
    skills = {}
    for root in (ENGINE / "skills" / cfg["lang"], ws / "skills"):
        if root.exists():
            for d in sorted(root.iterdir()):
                if d.is_dir() and (d / "SKILL.md").exists():
                    skills[d.name] = d            # пользовательский скил перекрывает встроенный
    return skills


def cmd_sync(a):
    cfg = C.load_config()
    ws, out, bak = ws_paths(cfg)
    if not (ws / "rules" / "core.md").exists():
        say(t(f"Пространство {ws} не найдено. Сначала: aiw setup", f"Workspace {ws} not found. Run: aiw setup"))
        sys.exit(1)
    if getattr(a, "log", False):
        out.mkdir(parents=True, exist_ok=True)
        f = open(ws / ".aiw" / "sync.log", "a", encoding="utf-8")
        sys.stdout = sys.stderr = f
        say(f"\n=== {C.TS} ===")

    import texts
    say(t("1) Правила и досье → тексты", "1) Rules and profile → texts"))
    st = texts.build(ws, out)
    say(t(f"   полный: {st['full']} симв., ChatGPT: {st['chatgpt']} симв.", f"   full: {st['full']} chars, ChatGPT: {st['chatgpt']} chars"))

    say(t("2) Правила → агенты", "2) Rules → agents"))
    targets = [ws / "AGENTS.md"]
    if (HOME / ".claude").exists():
        targets.append(HOME / ".claude" / "CLAUDE.md")
    if (HOME / ".codex").exists():
        targets.append(HOME / ".codex" / "AGENTS.md")
    grok = Path(os.environ.get("GROK_HOME", HOME / ".grok"))
    kimi = Path(os.environ.get("KIMI_CODE_HOME", HOME / ".kimi-code"))
    for d, f in ((HOME / ".agents", "AGENTS.md"), (grok, "AGENTS.md"), (kimi, "AGENTS.md"), (HOME / ".qwen", "QWEN.md")):
        agents_std = d.name == ".agents" and any((HOME / x).exists() for x in (".codex", ".kimi-code", ".grok"))
        if d.exists() or agents_std:                 # только если инструмент установлен
            targets.append(d / f)
    for tg in targets:
        place(out / "AGENTS.md", tg, bak)

    say(t("3) Скилы", "3) Skills"))
    dirs = []
    if (HOME / ".claude").exists():
        dirs.append(HOME / ".claude" / "skills")
    if (HOME / ".codex").exists():
        dirs += [HOME / ".codex" / "skills"]
    if any((HOME / x).exists() for x in (".codex", ".agents", ".kimi-code", ".grok")):
        dirs.append(HOME / ".agents" / "skills")     # общий стандарт: Codex, Kimi Code, Grok Build
    if (HOME / ".qwen").exists():
        dirs.append(HOME / ".qwen" / "skills")       # Qwen Code ищет скилы только у себя
    skills = skill_set(cfg)
    for d in dirs:                                   # забрать скилы, созданные прямо в инструментах
        if not d.exists():
            continue
        for s in d.iterdir():
            if s.name.startswith(".") or ".bak-" in s.name or s.is_symlink() or not s.is_dir():
                continue
            if (s / "SKILL.md").exists() and not is_managed(s) and s.name not in skills:
                shutil.copytree(s, ws / "skills" / s.name)
                say(t(f"  ← забрал скил «{s.name}» в {ws / 'skills'}", f"  ← adopted skill “{s.name}” into {ws / 'skills'}"))
    skills = skill_set(cfg)
    for d in dirs:
        for n, src in skills.items():
            place(src, d / n, bak)
        if d.exists():                               # убрать отключённые/удалённые
            for l in d.iterdir():
                if l.name in skills:
                    continue
                if l.is_symlink():
                    tgt = os.readlink(l)
                    if (str(ws) in tgt or str(ENGINE) in tgt) and not l.exists():
                        l.unlink()
                elif l.is_dir() and is_managed(l):
                    shutil.rmtree(l)

    say(t("4) Хук летописи для Claude Code", "4) Chronicle hook for Claude Code"))
    install_hook()

    say(t("5) Подключения (MCP)", "5) Connections (MCP)"))
    import mcp_sync
    mcp_sync.sync(ws)

    say(t("6) Переписки агентов (SpecStory, по желанию)", "6) Agent transcripts (SpecStory, optional)"))
    if shutil.which("specstory"):
        n = 0
        for p in project_dirs(ws):
            n += run(["specstory", "sync"], cwd=p, stdin=subprocess.DEVNULL).returncode == 0
        say(t(f"  выгружено в .specstory/history/ ({n} проектов)", f"  exported to .specstory/history/ ({n} projects)"))
    else:
        say(t("  не установлен (см. README)", "  not installed (see README)"))

    say(t("7) Бэкап (git)", "7) Backup (git)"))
    git_backup(ws)

    if cfg.get("schedule", True):
        say(t("8) Автозапуск каждый вечер", "8) Daily auto-sync"))
        install_schedule(cfg)

    if not getattr(a, "quiet", False) and sys.stdout.isatty():
        if copy_clipboard(out / "custom-instructions.txt"):
            say(t("\n✓ Полный текст инструкций — в буфере обмена.", "\n✓ Full instructions text copied to clipboard."))
        say(t(f"""✓ Готово. Тексты для веб-версий — в {out}:
  Claude   → Настройки → инструкции для Claude     ← custom-instructions.txt
  ChatGPT  → Настройки → Персонализация            ← chatgpt.txt
  Grok     → Настройки → Customize → инструкции     ← chatgpt.txt
  Kimi, Qwen, Meta AI (память) → сообщениями в чат  ← memory-messages.txt""",
              f"""✓ Done. Texts for web apps are in {out}:
  Claude   → Settings → instructions for Claude   ← custom-instructions.txt
  ChatGPT  → Settings → Personalization           ← chatgpt.txt
  Grok     → Settings → Customize → instructions   ← chatgpt.txt
  Kimi, Qwen, Meta AI (memory) → as chat messages  ← memory-messages.txt"""))


def project_dirs(ws):
    pr = ws / "projects"
    if not pr.exists():
        return []
    res = []
    for p in sorted(pr.iterdir()):
        if not p.is_dir() or p.name.startswith(("_", ".")):
            continue
        if (p / ".aiw-group").exists():
            res += [c for c in sorted(p.iterdir()) if c.is_dir() and not c.name.startswith(("_", "."))
                    and c.name != C.load_config()["names"]["chronicle"]]
        else:
            res.append(p)
    return res


def install_hook():
    settings = HOME / ".claude" / "settings.json"
    if not settings.parent.exists():
        return say(t("  Claude Code не найден — пропуск", "  Claude Code not found — skipped"))
    cfg = json.loads(settings.read_text(encoding="utf-8") or "{}") if settings.exists() else {}
    cmd = f'"{sys.executable}" "{ENGINE / "lib" / "hook_chronicle.py"}"'
    stop = cfg.setdefault("hooks", {}).setdefault("Stop", [])
    for g in stop:
        for h in g.get("hooks", []):
            if "hook_chronicle.py" in h.get("command", ""):
                if h["command"] == cmd:
                    return say(t("  уже установлен", "  already installed"))
                h["command"] = cmd
                settings.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
                return say(t("  обновлён", "  updated"))
    if settings.exists():
        shutil.copy2(settings, settings.with_name(f"settings.json.bak-{C.TS}"))
    stop.append({"hooks": [{"type": "command", "command": cmd, "timeout": 10}]})
    settings.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    say(t("  + Stop-хук в ~/.claude/settings.json", "  + Stop hook in ~/.claude/settings.json"))


SECRET_PATTERNS = [r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"ghp_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{30,}",
                   r"glpat-[A-Za-z0-9_\-]{20,}", r"sk-ant-[A-Za-z0-9_\-]{20,}", r"sk-(proj-)?[A-Za-z0-9_\-]{20,}",
                   r"AKIA[0-9A-Z]{16}", r"AIza[0-9A-Za-z_\-]{35}", r"xox[baprs]-[A-Za-z0-9\-]{10,}",
                   r"\b\d{8,10}:AA[A-Za-z0-9_\-]{33}\b"]


def scan_secrets(ws, files):
    hits = []
    rx = re.compile("|".join(SECRET_PATTERNS))
    for f in files:
        p = ws / f
        try:
            for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{f}:{i}")
        except Exception:
            pass
    return hits


def git_backup(ws):
    if not shutil.which("git"):
        return say(t("  git не установлен — пропуск", "  git not installed — skipped"))
    if not (ws / ".git").exists():
        run(["git", "init", "-q", str(ws)])
    g = ["git", "-C", str(ws)]
    run(g + ["add", "-A"])
    files = [f for f in run(g + ["diff", "--cached", "--name-only", "-z"]).stdout.split("\0") if f]
    hits = scan_secrets(ws, files)
    if hits:
        run(g + ["reset", "-q"])
        say(t("  ⛔ похоже на ключи/токены — коммит отменён. Перенеси их в ~/.secrets:",
              "  ⛔ looks like keys/tokens — commit cancelled. Move them to ~/.secrets:"))
        for h in hits[:20]:
            say("     " + h)
        return
    ident = [] if run(g + ["config", "user.email"]).stdout.strip() else ["-c", "user.name=ai-workspace", "-c", "user.email=ai-workspace@localhost"]
    r = run(["git"] + ident + ["-C", str(ws), "commit", "-q", "-m", f"sync {C.TS}"])
    say(t("  изменения сохранены", "  changes committed") if r.returncode == 0 else t("  без изменений", "  nothing new"))
    if run(g + ["remote", "get-url", "origin"]).returncode == 0:
        r = run(g + ["push", "-q", "origin", "HEAD"])
        say(t("  отправлено на GitHub", "  pushed to GitHub") if r.returncode == 0 else t("  ⚠ push не удался", "  ⚠ push failed"))
    else:
        say(t("  только локально (GitHub-бэкап не настроен)", "  local only (no GitHub backup set up)"))


def install_schedule(cfg):
    py, script = sys.executable, str(ENGINE / "aiw.py")
    if C.OS == "Darwin":
        label = "com.ai-workspace.sync"
        plist = HOME / "Library" / "LaunchAgents" / f"{label}.plist"
        body = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{label}</string>
  <key>ProgramArguments</key><array><string>{py}</string><string>{script}</string><string>sync</string><string>--quiet</string><string>--log</string></array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>21</integer><key>Minute</key><integer>7</integer></dict>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
</dict></plist>
"""
        if plist.exists() and plist.read_text(encoding="utf-8") == body:
            return say(t("  уже настроен (21:07)", "  already set (21:07)"))
        plist.parent.mkdir(parents=True, exist_ok=True)
        uid = str(os.getuid())
        run(["launchctl", "bootout", f"gui/{uid}", str(plist)])
        plist.write_text(body, encoding="utf-8")
        ok = run(["launchctl", "bootstrap", f"gui/{uid}", str(plist)]).returncode == 0
    elif C.OS == "Linux":
        if shutil.which("systemctl") and run(["systemctl", "--user", "show-environment"]).returncode == 0:
            d = HOME / ".config" / "systemd" / "user"
            d.mkdir(parents=True, exist_ok=True)
            svc = f"[Unit]\nDescription=ai-workspace sync\n\n[Service]\nType=oneshot\nExecStart=\"{py}\" \"{script}\" sync --quiet --log\n"
            tmr = "[Unit]\nDescription=ai-workspace daily sync\n\n[Timer]\nOnCalendar=*-*-* 21:07\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n"
            if (d / "ai-workspace.service").exists() and (d / "ai-workspace.service").read_text() == svc:
                return say(t("  уже настроен (21:07)", "  already set (21:07)"))
            (d / "ai-workspace.service").write_text(svc)
            (d / "ai-workspace.timer").write_text(tmr)
            run(["systemctl", "--user", "daemon-reload"])
            ok = run(["systemctl", "--user", "enable", "--now", "ai-workspace.timer"]).returncode == 0
        elif shutil.which("crontab"):
            cur = run(["crontab", "-l"]).stdout
            if "aiw.py sync" in cur:
                return say(t("  уже настроен (21:07)", "  already set (21:07)"))
            line = f'7 21 * * * "{py}" "{script}" sync --quiet --log\n'
            ok = subprocess.run(["crontab", "-"], input=cur + line, text=True).returncode == 0
        else:
            return say(t("  нет systemd/cron — запускай «aiw sync» вручную", "  no systemd/cron — run “aiw sync” manually"))
    elif C.OS == "Windows":
        pyw = Path(py).with_name("pythonw.exe")
        exe = str(pyw if pyw.exists() else py)
        cur = run(["schtasks", "/Query", "/TN", "ai-workspace-sync"])
        if cur.returncode == 0:
            return say(t("  уже настроен (21:07)", "  already set (21:07)"))
        ok = run(["schtasks", "/Create", "/F", "/SC", "DAILY", "/ST", "21:07", "/TN", "ai-workspace-sync",
                  "/TR", f'"{exe}" "{script}" sync --quiet --log']).returncode == 0
    else:
        return
    say(t("  + каждый день в 21:07 (пропущенный — при включении). Лог: .aiw/sync.log",
          "  + daily at 21:07 (missed runs catch up on wake). Log: .aiw/sync.log") if ok
        else t("  ⚠ не удалось — запускай «aiw sync» вручную", "  ⚠ failed — run “aiw sync” manually"))


def copy_clipboard(p: Path):
    text = p.read_text(encoding="utf-8")
    cmds = {"Darwin": [["pbcopy"]], "Linux": [["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "-ib"]]}
    if C.OS == "Windows":
        return run(["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value ([IO.File]::ReadAllText('{p}'))"]).returncode == 0
    for c in cmds.get(C.OS, []):
        if shutil.which(c[0]):
            return subprocess.run(c, input=text, text=True).returncode == 0
    return False


# ---------------------------------------------------------------- прочие команды
def cmd_update(a):
    C.load_config()
    if (ENGINE / ".git").exists():
        r = run(["git", "-C", str(ENGINE), "pull", "--ff-only", "-q"])
        say(t("✓ движок обновлён", "✓ engine updated") if r.returncode == 0 else "⚠ " + r.stderr.strip())
    cmd_sync(argparse.Namespace(quiet=False, log=False))


def cmd_doctor(a):
    cfg = C.load_config()
    ws = Path(cfg["workspace"])
    ok = lambda b: "✓" if b else "✗"
    rows = [
        ("OS / Python", f"{C.OS} / {sys.version.split()[0]}", True),
        ("ai-workspace", f"{C.VERSION} · {ENGINE}", True),
        (t("Пространство", "Workspace"), str(ws), (ws / "rules" / "core.md").exists()),
        ("git", shutil.which("git") or "—", bool(shutil.which("git"))),
        (t("GitHub-бэкап", "GitHub backup"), run(["git", "-C", str(ws), "remote", "get-url", "origin"]).stdout.strip() or "—",
         run(["git", "-C", str(ws), "remote", "get-url", "origin"]).returncode == 0),
        ("Node.js (npx)", shutil.which("npx") or "—", bool(shutil.which("npx"))),
        ("Claude Desktop", str(C.claude_desktop_config().parent), C.claude_desktop_config().parent.exists()),
        ("Claude Code", str(HOME / ".claude"), (HOME / ".claude").exists()),
        ("Codex", str(HOME / ".codex"), (HOME / ".codex").exists()),
        ("Grok Build", str(HOME / ".grok"), (HOME / ".grok").exists()),
        ("Kimi Code", str(HOME / ".kimi-code"), (HOME / ".kimi-code").exists()),
        ("Qwen Code", str(HOME / ".qwen"), (HOME / ".qwen").exists()),
        ("SpecStory", shutil.which("specstory") or "—", bool(shutil.which("specstory"))),
        ("~/.secrets", str(HOME / ".secrets"), (HOME / ".secrets").exists()),
    ]
    for k, v, b in rows:
        say(f"{ok(b)} {k:16} {v}")


def cmd_new_project(a):
    cfg = C.load_config()
    ws = Path(cfg["workspace"])
    dst = ws / "projects" / a.name
    if dst.exists():
        sys.exit(t(f"Уже есть: {dst}", f"Already exists: {dst}"))
    parts = Path(a.name).parts
    if len(parts) == 2:                                  # Группа/Проект
        grp = ws / "projects" / parts[0]
        grp.mkdir(parents=True, exist_ok=True)
        (grp / ".aiw-group").write_text("", encoding="utf-8")
    shutil.copytree(ws / "projects" / "_template", dst)
    for f in dst.rglob("*.md"):
        f.write_text(f.read_text(encoding="utf-8").replace("{{PROJECT}}", parts[-1]).replace("{{DATE}}", date.today().isoformat()), encoding="utf-8")
    say(t(f"✓ Проект: {dst}\n  Опиши цель в AGENTS.md и открывай эту папку в любой нейросети.",
          f"✓ Project: {dst}\n  Describe the goal in AGENTS.md and open this folder in any AI tool."))


def cmd_secret(a):
    C.load_config()
    if a.action != "set":
        sys.exit("aiw secret set NAME")
    v = getpass.getpass(t(f"Значение для «{a.name}» (не отображается): ", f"Value for “{a.name}” (hidden): "))
    where = C.secret_set(a.name, v)
    say(t(f"✓ Сохранено: {where}\n  В mcp/servers.json пиши: \"secret:{a.name}\"",
          f"✓ Saved: {where}\n  In mcp/servers.json use: \"secret:{a.name}\""))


def cmd_import_chats(a):
    cfg = C.load_config()
    import import_chats
    import_chats.main(Path(cfg["workspace"]) / "chats")


def cmd_uninstall(a):
    cfg = C.load_config()
    ws = Path(cfg["workspace"])
    for p in [HOME / ".claude" / "CLAUDE.md", HOME / ".codex" / "AGENTS.md", HOME / ".agents" / "AGENTS.md",
              HOME / ".grok" / "AGENTS.md", HOME / ".kimi-code" / "AGENTS.md", HOME / ".qwen" / "QWEN.md"]:
        if p.is_symlink() or (p.exists() and is_managed(p)):
            remove(p)
    for d in [HOME / ".claude" / "skills", HOME / ".codex" / "skills", HOME / ".agents" / "skills", HOME / ".qwen" / "skills"]:
        if d.exists():
            for s in d.iterdir():
                if (s.is_symlink() and (str(ws) in os.readlink(s) or str(ENGINE) in os.readlink(s))) or (s.is_dir() and is_managed(s)):
                    remove(s)
    st = HOME / ".claude" / "settings.json"
    if st.exists():
        cfg_ = json.loads(st.read_text(encoding="utf-8") or "{}")
        for g in cfg_.get("hooks", {}).get("Stop", []):
            g["hooks"] = [h for h in g.get("hooks", []) if "hook_chronicle.py" not in h.get("command", "")]
        if "hooks" in cfg_:
            cfg_["hooks"]["Stop"] = [g for g in cfg_["hooks"].get("Stop", []) if g.get("hooks")]
        st.write_text(json.dumps(cfg_, ensure_ascii=False, indent=2), encoding="utf-8")
    if C.OS == "Darwin":
        plist = HOME / "Library/LaunchAgents/com.ai-workspace.sync.plist"
        run(["launchctl", "bootout", f"gui/{os.getuid()}", str(plist)])
        if plist.exists():
            plist.unlink()
    elif C.OS == "Linux":
        run(["systemctl", "--user", "disable", "--now", "ai-workspace.timer"])
        cur = run(["crontab", "-l"]).stdout
        if "aiw.py sync" in cur:
            subprocess.run(["crontab", "-"], input="".join(l for l in cur.splitlines(True) if "aiw.py sync" not in l), text=True)
    elif C.OS == "Windows":
        run(["schtasks", "/Delete", "/F", "/TN", "ai-workspace-sync"])
    say(t(f"✓ Отключено от нейросетей. Твои данные остались в {ws}; прежние файлы нейросетей — в {ws / '.aiw' / 'backups'}. MCP-записи убери в настройках приложений при желании.",
          f"✓ Unlinked from AI tools. Your data stays in {ws}; previous tool files are in {ws / '.aiw' / 'backups'}. Remove MCP entries in app settings if you wish."))


def main():
    p = argparse.ArgumentParser(prog="aiw", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("setup")
    s.add_argument("--lang", choices=["ru", "en"])
    s.add_argument("--name")
    s.add_argument("--workspace")
    s.add_argument("--yes", action="store_true", help="без вопросов / non-interactive")
    s.add_argument("--no-schedule", action="store_true")
    s = sub.add_parser("sync")
    s.add_argument("--quiet", action="store_true")
    s.add_argument("--log", action="store_true")
    sub.add_parser("update")
    sub.add_parser("doctor")
    s = sub.add_parser("new-project")
    s.add_argument("name")
    s = sub.add_parser("secret")
    s.add_argument("action", choices=["set"])
    s.add_argument("name")
    sub.add_parser("import-chats")
    sub.add_parser("uninstall")
    a = p.parse_args()
    fn = {"setup": cmd_setup, "sync": cmd_sync, "update": cmd_update, "doctor": cmd_doctor,
          "new-project": cmd_new_project, "secret": cmd_secret, "import-chats": cmd_import_chats,
          "uninstall": cmd_uninstall}.get(a.cmd)
    if not fn:
        p.print_help()
        return
    fn(a)


if __name__ == "__main__":
    main()
