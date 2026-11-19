# -*- coding: utf-8 -*-
"""知识点/背诵 P1 数据构建 → data/kp.json
源：行测 kp.json（三级考点树）/ 408 points（考点+关键词）/
    法考 knowledge.json（考点+详解）/ 软件设计师 chapters（知识块，本地已缓存）
用法: python tools/build_kp.py
"""
import json, urllib.request, os, sys, re, glob

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(BASE, "_tmp_ruankao")
UA = {"User-Agent": "curl/8"}

def get(url, timeout=40):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def blocks_to_text(blocks):
    """软设知识块 → 纯文本（防注入不渲染 HTML）"""
    out = []
    for b in blocks or []:
        t = b.get("t")
        if t == "key":
            out.append("【" + (b.get("title") or "要点") + "】" + str(b.get("c") or ""))
        elif t == "h":
            out.append("\n" + str(b.get("c") or ""))
        elif t == "p":
            out.append(str(b.get("c") or ""))
        elif t == "ul":
            out += ["· " + str(x) for x in (b.get("items") or [])]
        elif t == "table":
            head = " | ".join(str(x) for x in (b.get("head") or []))
            if head:
                out.append(head)
            for row in b.get("rows") or []:
                out.append(" | ".join(str(x) for x in row))
            if b.get("note"):
                out.append("注：" + str(b["note"]))
    return "\n".join(x for x in out if x).strip()

def main():
    subjects = []

    # ① 行测：三级考点树
    try:
        kp = json.loads(get("https://cdn.jsdelivr.net/gh/xiaogaostu/xingce-app@main/web/public/data/kp.json"))
        groups = []
        for m in kp.get("items") or []:
            for lv2 in m.get("children") or []:
                cards = []
                for lv3 in lv2.get("children") or []:
                    desc = lv3.get("description") or ""
                    cnt = lv3.get("questionCount")
                    a = desc + (f"（关联 {cnt} 道题）" if cnt else "")
                    cards.append({"q": lv3.get("name", ""), "a": a})
                if not cards and lv2.get("name"):
                    cards.append({"q": lv2.get("name", ""), "a": lv2.get("description", "")})
                if cards:
                    groups.append({"name": f"{m.get('name')} · {lv2.get('name')}", "cards": cards})
        subjects.append({"name": "行测", "groups": groups})
        print(f"行测: {len(groups)} 组 / {sum(len(g['cards']) for g in groups)} 卡", flush=True)
    except Exception as e:
        print("行测 kp 失败:", e, flush=True)

    # ② 408：points（书/章名来自同文件 books）
    try:
        raw = get("https://cdn.jsdelivr.net/gh/chiyunxian/408@main/data/questions.js").decode("utf-8", "ignore")
        d, _ = json.JSONDecoder().raw_decode(raw[raw.index("{"):])
        book_name = {b["id"]: b["name"] for b in d.get("books") or []}
        chap_name = {}
        for b in d.get("books") or []:
            for c in b.get("chapters") or []:
                chap_name[c["id"]] = c.get("title", c["id"])
        by_ch = {}
        for p in d.get("points") or []:
            book = book_name.get(p.get("book"), "")
            ch = chap_name.get(p.get("chapter"), p.get("chapter", ""))
            kw = p.get("kw") or []
            card = {"q": p.get("title", ""),
                    "a": ("关键词：" + "、".join(kw)) if kw else ""}
            by_ch.setdefault(f"{book} · {ch}", []).append(card)
        groups = [{"name": k, "cards": v} for k, v in by_ch.items()]
        subjects.append({"name": "408", "groups": groups})
        print(f"408: {len(groups)} 组 / {sum(len(g['cards']) for g in groups)} 卡", flush=True)
    except Exception as e:
        print("408 失败:", e, flush=True)

    # ③ 法律：knowledge.json（subject 分组）
    try:
        data = json.loads(get("https://cdn.jsdelivr.net/gh/DADA-dcc/fakao-pwa@main/knowledge.json"))
        by_s = {}
        for k in data:
            by_s.setdefault(k.get("subject") or "综合", []).append(
                {"q": k.get("point", ""), "a": k.get("detail", "")})
        groups = [{"name": s, "cards": c} for s, c in by_s.items()]
        subjects.append({"name": "法律", "groups": groups})
        print(f"法律: {len(groups)} 组 / {sum(len(g['cards']) for g in groups)} 卡", flush=True)
    except Exception as e:
        print("法律失败:", e, flush=True)

    # ④ 软件设计师：本地缓存的章节知识块
    try:
        groups = []
        for f in sorted(glob.glob(os.path.join(TMP, "designer_ch*.json"))):
            ch = json.load(open(f, encoding="utf-8"))
            if not isinstance(ch, dict):
                continue
            cards = []
            intro = (ch.get("intro") or "").replace("**", "")
            focus = ch.get("examFocus") or []
            if intro:
                cards.append({"q": "本章考什么", "a": intro + ("\n重点：" + "、".join(focus) if focus else "")})
            for s in ch.get("sections") or []:
                txt = blocks_to_text(s.get("blocks"))
                if txt:
                    cards.append({"q": s.get("title", ""), "a": txt})
            if cards:
                groups.append({"name": ch.get("title") or f.get("title", "章"), "cards": cards})
        if groups:
            subjects.append({"name": "软件设计师", "groups": groups})
            print(f"软件设计师: {len(groups)} 组 / {sum(len(g['cards']) for g in groups)} 卡", flush=True)
        else:
            print("软件设计师: 缓存章节缺失（跳过，先跑 import_ruankao.py 软设）", flush=True)
    except Exception as e:
        print("软件设计师失败:", e, flush=True)

    out = os.path.join(BASE, "data", "kp.json")
    json.dump({"subjects": subjects}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"DONE -> kp.json {os.path.getsize(out)//1024} KB", flush=True)

if __name__ == "__main__":
    main()
