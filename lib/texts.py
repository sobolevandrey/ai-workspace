# -*- coding: utf-8 -*-
"""Собирает из rules/core.md + memory/profile.md тексты для всех нейросетей.
Builds per-tool texts from rules/core.md + memory/profile.md."""
import re
from pathlib import Path

import common as C


def _clean(t):
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)                      # подсказки / hints
    t = re.sub(r"^>.*\n", "", t, flags=re.M)                          # служебные цитаты / notes
    t = re.sub(r"^## [^\n]*\n\s*(?=^#|\Z)", "", t, flags=re.M)       # пустые разделы / empty sections
    return re.sub(r"\n{3,}", "\n\n", t).strip() + "\n"


def _sections(text):
    out = []
    for block in re.split(r"(?m)^## ", text)[1:]:
        lines = block.strip().splitlines()
        items = []
        for l in lines[1:]:
            l = l.strip()
            if l.startswith("-"):
                items.append(l)
            elif l and items and not l.startswith("#"):
                items[-1] += " " + l
        out.append((lines[0].strip(), items))
    return out


def _plain(l):
    l = re.sub(r"\s*\(`[^`]*`\)", "", l)
    return l.replace("**", "").replace("`", "")


def build(ws: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    rules_raw = (ws / "rules/core.md").read_text(encoding="utf-8")
    about_raw = (ws / "memory/profile.md").read_text(encoding="utf-8")

    # 1. AGENTS.md — для агентов с доступом к файлам (Codex, Claude Code, Kimi, ZCode…)
    head = C.t("<!-- {m} — НЕ РЕДАКТИРУЙ. Правь rules/core.md и memory/profile.md, затем: aiw sync -->",
               "<!-- {m} — DO NOT EDIT. Edit rules/core.md and memory/profile.md, then run: aiw sync -->")
    (out / "AGENTS.md").write_text(head.format(m=C.MARK) + "\n\n" + rules_raw.rstrip() + "\n\n" + about_raw,
                                   encoding="utf-8")

    rules, about = _clean(rules_raw), _clean(about_raw)
    # 2. Claude (Settings → instructions): полный текст / full text
    (out / "custom-instructions.txt").write_text(rules + "\n" + about, encoding="utf-8")

    # 3. ChatGPT: одно поле ≤ 1500 символов / one field ≤ 1500 chars
    tail = C.t("- Файлы и проекты у меня в рабочем пространстве (в каждом проекте: AGENTS.md, {s}, {c}/). "
               "Если попрошу «запиши в летопись» — дай готовую запись: дата · ИИ · зачем · сделано · решение · файлы · дальше.",
               "- My files and projects live in my workspace (each project: AGENTS.md, {s}, {c}/). "
               "If I say “log this”, give me a ready chronicle entry: date · AI · why · done · decision · files · next.")
    cfg = C.load_config()
    tail = tail.format(s=cfg["names"]["status"], c=cfg["names"]["chronicle"])
    items = []
    for _, its in _sections(about) + _sections(rules):
        items += [_plain(i) for i in its]
    compact, used, seen = [], len(tail) + 1, set()
    for i in items:
        if i in seen:
            continue
        seen.add(i)
        if used + len(i) + 1 > 1480:
            break
        compact.append(i)
        used += len(i) + 1
    one = "\n".join(compact + [tail]) + "\n"
    (out / "chatgpt.txt").write_text(one, encoding="utf-8")

    # 4. Kimi и другие с «памятью»: по записи ≤ 500 символов / memory entries ≤ 500 chars
    word = C.t("Запомни", "Remember")
    chunks = []
    for head_, its in _sections(rules) + _sections(about):
        cur = ""
        for i in its:
            i = _plain(i).lstrip("- ").strip()
            if cur and len(cur) + len(i) > 420:
                chunks.append(f"{word} ({head_}): {cur.strip()}")
                cur = ""
            cur += " " + i
        if cur.strip():
            chunks.append(f"{word} ({head_}): {cur.strip()}")
    intro = C.t("Отправляй по одному абзацу как отдельное сообщение:", "Send each paragraph as a separate message:")
    (out / "memory-messages.txt").write_text(intro + "\n\n" + "\n\n".join(chunks) + "\n", encoding="utf-8")
    return {"full": len(rules) + len(about), "chatgpt": len(one)}
