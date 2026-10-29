#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stop-хук Claude Code: если в сессии менялись файлы проекта, а летопись и статус — нет,
просит Claude их обновить (не чаще раза в 30 минут). Любая ошибка — молча пропускаем.

Claude Code Stop hook: if project files changed this session but the chronicle/status didn't,
asks Claude to update them (at most every 30 min). Never breaks the session."""
import json
import sys
import tempfile
import time
import unicodedata
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
COOLDOWN = 30 * 60


def nfc(s):
    return unicodedata.normalize("NFC", s)


def project_root(path, projects):
    try:
        rel = Path(nfc(str(Path(path).resolve()))).relative_to(projects)
    except Exception:
        return None
    parts = rel.parts
    if not parts or parts[0].startswith(("_", ".")):
        return None
    root = projects / parts[0]
    if (root / ".aiw-group").exists() and len(parts) > 1:      # группа проектов, напр. «Клиенты/…»
        root = root / parts[1]
    return root


def ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return
    cfg = C.load_config()
    status, chron = cfg["names"]["status"], cfg["names"]["chronicle"]
    projects = Path(nfc(str((Path(cfg["workspace"]) / "projects").resolve())))
    root = project_root(data.get("cwd", ""), projects)
    if not root:
        return
    last = None
    for line in open(data["transcript_path"], encoding="utf-8"):
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if ev.get("type") != "assistant":
            continue
        for c in (ev.get("message") or {}).get("content") or []:
            if not isinstance(c, dict) or c.get("type") != "tool_use" or c.get("name") not in EDIT_TOOLS:
                continue
            inp = c.get("input") or {}
            fp = inp.get("file_path") or inp.get("notebook_path") or ""
            if project_root(fp, projects) != root:
                continue
            n = nfc(fp).replace("\\", "/")
            if f"/{chron}/" in n or n.endswith(status):
                continue
            last = max(last or 0, ts(ev.get("timestamp", "")) or time.time())
    if not last:
        return
    marks = [p.stat().st_mtime for p in [root / status, *(root / chron).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].md")] if p.exists()]
    if marks and max(marks) >= last:
        return
    flag = Path(tempfile.gettempdir()) / "ai-workspace-hook" / str(data.get("session_id", "x"))
    flag.parent.mkdir(exist_ok=True)
    if flag.exists() and time.time() - flag.stat().st_mtime < COOLDOWN:
        return
    flag.touch()
    name = root.relative_to(projects).as_posix()
    month = f"{datetime.now():%Y-%m}"
    reason = C.t(
        f"В этой сессии менялись файлы проекта «{name}», а летопись и {status} не обновлены. По скилу project-chronicle: "
        f"допиши (или дополни, если уже есть) запись этой сессии в {name}/{chron}/{month}.md и перепиши {name}/{status}. "
        "Коротко, 5–10 строк. Если сессия ещё не закончена — ответь одной фразой, что запишешь в конце.",
        f"Project files in “{name}” changed this session, but the chronicle and {status} were not updated. Following the "
        f"project-chronicle skill: add (or extend) this session's entry in {name}/{chron}/{month}.md and rewrite {name}/{status}. "
        "Keep it to 5–10 lines. If the session isn't finished yet, reply in one sentence that you'll log it at the end.")
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
