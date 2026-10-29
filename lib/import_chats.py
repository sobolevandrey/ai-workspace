#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Конвертирует экспорт переписок ChatGPT и Claude в markdown-архив.
Converts ChatGPT / Claude data exports into a markdown archive.

1. Скачай экспорт:
   ChatGPT → Settings → Data controls → Export data  (придёт письмо со ссылкой на .zip)
   Claude  → Settings → Privacy → Export data        (тоже .zip на почту)
2. Положи .zip (или распакованную папку) в ~/AI/chats/_raw/
3. aiw import-chats

Результат: ~/AI/chats/<chatgpt|claude>/<год>/<дата>_<название>.md + chats/INDEX.md.
Повторный запуск безопасен: файлы перезаписываются, дублей нет.
Файлы проектов Claude попадают в chats/claude/_projects/.
"""
import json, re, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "AI" / "chats"   # переопределяется из aiw / overridden by aiw
RAW = ROOT / "_raw"


def slug(s, n=60):
    s = re.sub(r"[^\w\-]+", "-", (s or "без-названия").strip().lower(), flags=re.U).strip("-")
    return (s or "без-названия")[:n].rstrip("-")


def ts(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v, tz=timezone.utc)
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None


def write(src, title, created, cid, msgs):
    d = created or datetime(1970, 1, 1, tzinfo=timezone.utc)
    folder = ROOT / src / d.strftime("%Y")
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / f"{d:%Y-%m-%d}_{slug(title)}_{str(cid)[:8]}.md"
    lines = [f"# {title or 'Без названия'}", "",
             f"- Источник: {src}", f"- Дата: {d:%Y-%m-%d %H:%M} UTC", f"- ID: {cid}", ""]
    for who, when, text in msgs:
        hdr = "🧑 Я" if who == "user" else "🤖 " + ("ChatGPT" if src == "chatgpt" else "Claude")
        lines += [f"## {hdr}" + (f" · {when:%Y-%m-%d %H:%M}" if when else ""), "", text.strip(), ""]
    p.write_text("\n".join(lines), encoding="utf-8")
    return p, title, d


# ---------- ChatGPT ----------

def chatgpt_text(content):
    ct = content.get("content_type")
    if ct in ("text", "multimodal_text"):
        out = []
        for part in content.get("parts") or []:
            if isinstance(part, str):
                out.append(part)
            elif isinstance(part, dict):
                out.append(f"[вложение: {part.get('content_type') or part.get('asset_pointer') or 'файл'}]")
        return "\n".join(out)
    if ct == "code":
        return f"```\n{content.get('text','')}\n```"
    return ""  # thoughts, tool output и т.п. — пропускаем


def import_chatgpt(convs):
    res = []
    for c in convs:
        mapping, node, chain = c.get("mapping") or {}, c.get("current_node"), []
        while node and node in mapping:
            chain.append(mapping[node]); node = mapping[node].get("parent")
        msgs = []
        for n in reversed(chain):
            m = n.get("message") or {}
            role = (m.get("author") or {}).get("role")
            if role not in ("user", "assistant"):
                continue
            if (m.get("metadata") or {}).get("is_visually_hidden_from_conversation"):
                continue
            t = chatgpt_text(m.get("content") or {})
            if t.strip():
                msgs.append((role, ts(m.get("create_time")), t))
        if msgs:
            res.append(write("chatgpt", c.get("title"), ts(c.get("create_time")), c.get("id") or c.get("conversation_id") or "x", msgs))
    return res


# ---------- Claude ----------

def import_claude(convs):
    res = []
    for c in convs:
        msgs = []
        for m in c.get("chat_messages") or []:
            parts = [x.get("text", "") for x in (m.get("content") or []) if isinstance(x, dict) and x.get("type") == "text"]
            t = "\n\n".join(p for p in parts if p) or m.get("text") or ""
            for a in (m.get("attachments") or []) + (m.get("files") or []):
                t += f"\n\n[вложение: {a.get('file_name') or a.get('file_uuid') or 'файл'}]"
            if t.strip():
                msgs.append(("user" if m.get("sender") == "human" else "assistant", ts(m.get("created_at")), t))
        if msgs:
            res.append(write("claude", c.get("name"), ts(c.get("created_at")), c.get("uuid") or "x", msgs))
    return res


def import_claude_projects(projects):
    n = 0
    for p in projects:
        d = ROOT / "claude" / "_projects" / slug(p.get("name"))
        d.mkdir(parents=True, exist_ok=True)
        info = [f"# {p.get('name')}", "", p.get("description") or "", ""]
        if p.get("prompt_template"):
            info += ["## Инструкции проекта", "", p["prompt_template"], ""]
        (d / "README.md").write_text("\n".join(info), encoding="utf-8")
        for doc in p.get("docs") or []:
            (d / Path(doc.get("filename") or "doc.txt").name).write_text(doc.get("content") or "", encoding="utf-8"); n += 1
    return n


# ---------- обход _raw ----------

def json_sources():
    for p in sorted(RAW.rglob("*")):
        if p.suffix == ".json":
            yield p.name, lambda p=p: json.loads(p.read_text(encoding="utf-8"))
        elif p.suffix == ".zip":
            z = zipfile.ZipFile(p)
            for name in z.namelist():
                if name.endswith(".json"):
                    yield Path(name).name, lambda z=z, name=name: json.loads(z.read(name).decode("utf-8"))


def main(root=None):
    global ROOT, RAW
    if root:
        ROOT, RAW = Path(root), Path(root) / "_raw"
    RAW.mkdir(parents=True, exist_ok=True)
    if not any(RAW.iterdir()):
        sys.exit(f"Положи экспорт (.zip или папку) в {RAW} и запусти снова. / Put the export (.zip or folder) into {RAW} and run again.")
    written, projects = [], 0
    for name, load in json_sources():
        if name.startswith("conversations") or name == "projects.json":
            data = load()
            if not isinstance(data, list) or not data:
                continue
            first = data[0]
            if name == "projects.json":
                projects += import_claude_projects(data)
            elif "mapping" in first:
                written += import_chatgpt(data)
            elif "chat_messages" in first:
                written += import_claude(data)
    # индекс по всем файлам архива (а не только по этому запуску)
    rows = []
    for f in list((ROOT / "chatgpt").rglob("*.md")) + list((ROOT / "claude").rglob("*.md")):
        if "_projects" in f.parts:
            continue
        head = f.read_text(encoding="utf-8").split("\n", 4)
        title = head[0].lstrip("# ").strip()
        rows.append((f, title, f.name[:10]))
    rows.sort(key=lambda r: r[2], reverse=True)
    idx = ["# Архив переписок", "", f"Обновлено: {datetime.now():%Y-%m-%d %H:%M} · диалогов: {len(rows)}", "",
           "| Дата | Источник | Диалог |", "|---|---|---|"]
    for p, title, d in rows:
        rel = p.relative_to(ROOT)
        idx.append(f"| {d} | {rel.parts[0]} | [{title.replace('|', '/')}]({rel.as_posix().replace(' ', '%20')}) |")
    (ROOT / "INDEX.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    print(f"Готово: {len(written)} диалогов, {projects} файлов проектов Claude → {ROOT}")


if __name__ == "__main__":
    main()
