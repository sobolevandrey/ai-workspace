# -*- coding: utf-8 -*-
"""Общие функции ai-workspace / shared helpers."""
import json
import os
import platform
import subprocess
import time
from pathlib import Path

HOME = Path.home()
OS = platform.system()                      # Darwin | Linux | Windows
ENGINE = Path(__file__).resolve().parent.parent
POINTER = HOME / ".ai-workspace.json"       # где лежит рабочее пространство / where the workspace is
TS = time.strftime("%Y%m%d-%H%M%S")
MARK = "ai-workspace:managed"               # метка файлов, которыми управляет aiw
SECRET_SERVICE = "ai-workspace"
VERSION = "0.1.0"

NAMES = {
    "ru": {"status": "СТАТУС.md", "chronicle": "летопись"},
    "en": {"status": "STATUS.md", "chronicle": "chronicle"},
}

LANG = "en"


def t(ru, en):
    """Строка на языке пользователя / string in the user's language."""
    return ru if LANG == "ru" else en


def load_config():
    global LANG
    ws = None
    if os.environ.get("AIW_WORKSPACE"):
        ws = Path(os.environ["AIW_WORKSPACE"]).expanduser()
    elif POINTER.exists():
        try:
            ws = Path(json.loads(POINTER.read_text(encoding="utf-8"))["workspace"]).expanduser()
        except Exception:
            ws = None
    ws = ws or HOME / "AI"
    cfg = {"lang": "en", "name": "", "schedule": True}
    f = ws / ".aiw.json"
    if f.exists():
        try:
            cfg.update(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    cfg["workspace"] = str(ws)
    if cfg.get("lang") not in NAMES:
        cfg["lang"] = "en"
    cfg.setdefault("names", NAMES[cfg["lang"]])
    LANG = cfg["lang"]
    return cfg


def save_config(cfg):
    ws = Path(cfg["workspace"])
    ws.mkdir(parents=True, exist_ok=True)
    data = {k: v for k, v in cfg.items() if k != "workspace"}
    (ws / ".aiw.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    POINTER.write_text(json.dumps({"workspace": str(ws)}, indent=2) + "\n", encoding="utf-8")


# ---------- секреты / secrets ----------
# В servers.json пишется "secret:ИМЯ". Значение ищется: macOS Keychain → keyring (если установлен) → ~/.secrets/ИМЯ

def secret_get(name):
    if OS == "Darwin":
        r = subprocess.run(["security", "find-generic-password", "-s", f"{SECRET_SERVICE}.{name}", "-w"],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    try:
        import keyring  # type: ignore
        v = keyring.get_password(SECRET_SERVICE, name)
        if v:
            return v
    except Exception:
        pass
    f = HOME / ".secrets" / name
    if f.is_file():
        return f.read_text(encoding="utf-8").strip()
    return None


def secret_set(name, value):
    if OS == "Darwin":
        r = subprocess.run(["security", "add-generic-password", "-U", "-a", os.environ.get("USER", "user"),
                            "-s", f"{SECRET_SERVICE}.{name}", "-w", value], capture_output=True)
        if r.returncode == 0:
            return "macOS Keychain"
    try:
        import keyring  # type: ignore
        keyring.set_password(SECRET_SERVICE, name, value)
        return "system keyring"
    except Exception:
        pass
    d = HOME / ".secrets"
    d.mkdir(exist_ok=True)
    f = d / name
    f.write_text(value, encoding="utf-8")
    for p, mode in ((d, 0o700), (f, 0o600)):
        try:
            os.chmod(p, mode)
        except Exception:
            pass
    return str(f)


def claude_desktop_config():
    if OS == "Darwin":
        return HOME / "Library/Application Support/Claude/claude_desktop_config.json"
    if OS == "Windows":
        return Path(os.environ.get("APPDATA", HOME / "AppData/Roaming")) / "Claude" / "claude_desktop_config.json"
    return HOME / ".config/Claude/claude_desktop_config.json"
