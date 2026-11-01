# -*- coding: utf-8 -*-
"""Раскладывает <workspace>/mcp/servers.json по клиентам: Claude Desktop, Claude Code, Codex.
Трогает только свои серверы; файл переписывает, только если он реально изменился (с .bak-копией)."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import common as C

BEGIN = "# >>> ai-workspace MCP (managed, edit <workspace>/mcp/servers.json) >>>"
END = "# <<< ai-workspace MCP <<<"


def log(m):
    print("  " + m, flush=True)


def _resolve(name, spec, ws):
    s = {k: v for k, v in spec.items() if k not in ("enabled", "targets", "_comment")}
    def expand(a):
        if not isinstance(a, str):
            return a
        a = a.replace("$WORKSPACE", str(ws))
        return os.path.expanduser(a) if a.startswith("~") else a
    if "args" in s:
        s["args"] = [expand(a) for a in s["args"]]
    if "command" in s:
        found = shutil.which(s["command"])
        if not found:
            hint = C.t(" — установи Node.js (см. README)", " — install Node.js (see README)") if s["command"] in ("npx", "node") else ""
            log(C.t(f"⚠ {name}: команда «{s['command']}» не найдена{hint}. Пропущено.",
                    f"⚠ {name}: command “{s['command']}” not found{hint}. Skipped."))
            return None
        if C.OS == "Windows" and found.lower().endswith((".cmd", ".bat")):
            s["args"] = ["/c", found] + s.get("args", [])
            s["command"] = os.environ.get("COMSPEC", "cmd.exe")
        else:
            s["command"] = found          # абсолютный путь: GUI-приложения не видят PATH терминала
    env = {}
    for k, v in (s.get("env") or {}).items():
        if isinstance(v, str) and v.startswith(("secret:", "keychain:")):
            key = v.split(":", 1)[1]
            val = C.secret_get(key)
            if val is None:
                log(C.t(f"⚠ {name}: нет секрета «{key}» — добавь: aiw secret set {key}. Пропущено.",
                        f"⚠ {name}: secret “{key}” is missing — add it: aiw secret set {key}. Skipped."))
                return None
            env[k] = val
        else:
            env[k] = v
    if env:
        s["env"] = env
    return s


def _save(p: Path, text):
    if p.exists() and p.read_text(encoding="utf-8") == text:
        return False
    if p.exists():
        shutil.copy2(p, p.with_name(p.name + f".bak-{C.TS}"))
    p.write_text(text, encoding="utf-8")
    return True


def _claude_desktop(servers, prev):
    cfgp = C.claude_desktop_config()
    if not cfgp.parent.exists():
        return log(C.t("Claude Desktop не найден — пропуск", "Claude Desktop not found — skipped"))
    cfg = json.loads(cfgp.read_text(encoding="utf-8") or "{}") if cfgp.exists() else {}
    mcp = cfg.setdefault("mcpServers", {})
    for n in prev:
        if n not in servers:
            mcp.pop(n, None)
    n_local = 0
    for n, s in servers.items():
        if "url" in s:
            log(C.t(f"Claude Desktop: «{n}» — удалённый, добавь вручную: Settings → Connectors → {s['url']}",
                    f"Claude Desktop: “{n}” is remote, add it manually: Settings → Connectors → {s['url']}"))
            mcp.pop(n, None)
            continue
        mcp[n] = {k: v for k, v in s.items() if k in ("command", "args", "env")}
        n_local += 1
    changed = _save(cfgp, json.dumps(cfg, ensure_ascii=False, indent=2))
    log(f"Claude Desktop: {n_local} " + (C.t("— изменено, перезапусти приложение", "— changed, restart the app") if changed else C.t("без изменений", "unchanged")))


def _claude_code(servers, prev):
    claude = shutil.which("claude")
    if not claude:
        return log(C.t("Claude Code (claude) не найден — пропуск", "Claude Code (claude) not found — skipped"))
    for n in set(prev) | set(servers):
        subprocess.run([claude, "mcp", "remove", "--scope", "user", n], capture_output=True)
    ok = 0
    for n, s in servers.items():
        cfg = {"type": "http", "url": s["url"]} if "url" in s else {"type": "stdio", **{k: v for k, v in s.items() if k in ("command", "args", "env")}}
        r = subprocess.run([claude, "mcp", "add-json", "--scope", "user", n, json.dumps(cfg)], capture_output=True, text=True)
        ok += r.returncode == 0
    log(f"Claude Code: {ok}/{len(servers)}")


def _q(v):
    return json.dumps(v, ensure_ascii=False)


def _toml(path, label, servers):
    if not path.parent.exists():
        return log(C.t(f"{label} не найден — пропуск", f"{label} not found — skipped"))
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", text, flags=re.S).rstrip() + "\n"
    out = []
    for n, s in servers.items():
        if re.search(rf"^\[mcp_servers\.{re.escape(n)}\]", text, flags=re.M):
            log(C.t(f"{label}: «{n}» уже задан вручную — не трогаю", f"{label}: “{n}” is defined manually — left as is"))
            continue
        out.append(f"\n[mcp_servers.{n}]")
        if "url" in s:
            out.append(f"url = {_q(s['url'])}")
        else:
            out.append(f"command = {_q(s['command'])}")
            out.append("args = [" + ", ".join(_q(a) for a in s.get("args", [])) + "]")
            if s.get("env"):
                out.append("env = { " + ", ".join(f"{_q(k)} = {_q(v)}" for k, v in s["env"].items()) + " }")
    changed = _save(path, text + "\n" + BEGIN + "\n".join(out) + "\n" + END + "\n")
    log(f"{label}: {len(servers)} " + (C.t("— изменено", "— changed") if changed else C.t("без изменений", "unchanged")))


def _json(path, label, servers, prev, extra=None):
    """mcpServers в JSON-конфиге (Kimi Code, Qwen Code); удалённые (url) пропускаем."""
    if not path.parent.exists():
        return log(C.t(f"{label} не найден — пропуск", f"{label} not found — skipped"))
    cfg = json.loads(path.read_text(encoding="utf-8") or "{}") if path.exists() else {}
    mcp = cfg.setdefault("mcpServers", {})
    for n in prev:
        if n not in servers:
            mcp.pop(n, None)
    k = 0
    for n, s in servers.items():
        if "url" in s:
            continue
        mcp[n] = {x: v for x, v in s.items() if x in ("command", "args", "env")}
        k += 1
    if extra:
        extra(cfg)
    changed = _save(path, json.dumps(cfg, ensure_ascii=False, indent=2))
    log(f"{label}: {k} " + (C.t("— изменено", "— changed") if changed else C.t("без изменений", "unchanged")))


def _codex(servers, prev):
    _toml(C.HOME / ".codex" / "config.toml", "Codex", servers)


def _grok(servers, prev):
    _toml(Path(os.environ.get("GROK_HOME", C.HOME / ".grok")) / "config.toml", "Grok Build", servers)


def _kimi(servers, prev):
    _json(Path(os.environ.get("KIMI_CODE_HOME", C.HOME / ".kimi-code")) / "mcp.json", "Kimi Code", servers, prev)


def _qwen(servers, prev):
    def ctx(cfg):   # по умолчанию Qwen Code читает только QWEN.md / reads only QWEN.md by default
        c = cfg.setdefault("context", {})
        names = c.get("fileName") or []
        names = [names] if isinstance(names, str) else list(names)
        for n in ("AGENTS.md", "QWEN.md"):
            if n not in names:
                names.append(n)
        c["fileName"] = names
    _json(C.HOME / ".qwen" / "settings.json", "Qwen Code", servers, prev, ctx)


CLIENTS = {"claude-desktop": _claude_desktop, "claude-code": _claude_code, "codex": _codex,
           "grok": _grok, "kimi-code": _kimi, "qwen": _qwen}


def sync(ws: Path):
    src = ws / "mcp" / "servers.json"
    if not src.exists():
        return log(C.t("нет mcp/servers.json — пропуск", "no mcp/servers.json — skipped"))
    spec = json.loads(src.read_text(encoding="utf-8")).get("servers", {})
    statef = ws / ".aiw" / "mcp-state.json"
    state = json.loads(statef.read_text(encoding="utf-8")) if statef.exists() else {}
    new = {}
    for client, fn in CLIENTS.items():
        servers = {}
        for name, s in spec.items():
            if s.get("enabled", True) is False or ("targets" in s and client not in s["targets"]):
                continue
            r = _resolve(name, s, ws)
            if r:
                servers[name] = r
        try:
            fn(servers, state.get(client, []))
            new[client] = sorted(servers)
        except Exception as e:
            log(f"⚠ {client}: {e}")
            new[client] = state.get(client, [])
    statef.parent.mkdir(parents=True, exist_ok=True)
    statef.write_text(json.dumps(new, indent=2), encoding="utf-8")
    log(C.t("Веб-версии (ChatGPT, Grok, Kimi, Qwen, Meta AI): удалённые MCP — вручную в их настройках.",
            "Web apps (ChatGPT, Grok, Kimi, Qwen, Meta AI): add remote MCP servers manually in their settings."))
