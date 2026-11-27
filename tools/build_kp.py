# -*- coding: utf-8 -*-
"""知识点/背诵 数据构建 → data/kp.json

卡片粒度 = 一个具体知识点（一个公式、一个概念、一条规律），不是章节目录。
- 撰写正文：tools/kp_author/s_*.json（name / order / groups / cards）
- 公共科目：从行测同源卡片映射重组 + 追加国防和军队，避免重复维护
- 法律：法考 knowledge.json（考点 + 详解）
- 软件设计师：本地缓存章节知识块

用法: python tools/build_kp.py
"""
import json, urllib.request, os, sys, re, glob, copy

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(BASE, "_tmp_ruankao")
AUTHOR_DIR = os.path.join(BASE, "tools", "kp_author")
UA = {"User-Agent": "curl/8"}
MIN_BODY = 80


def get(url, timeout=40):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def load_authored():
    """载入 s_*.json → {科目名: 原始定义}"""
    out = {}
    for f in sorted(glob.glob(os.path.join(AUTHOR_DIR, "s_*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            sys.exit(f"作者文件解析失败 {os.path.basename(f)}: {e}")
        name = (d.get("name") or "").strip()
        if not name:
            sys.exit(f"作者文件缺 name: {os.path.basename(f)}")
        if name in out:
            sys.exit(f"科目重复定义: {name}")
        out[name] = d
    return out


def check_cards(subj, groups, seen=None, min_body=MIN_BODY):
    seen = seen if seen is not None else set()
    for g in groups:
        if not g.get("name"):
            sys.exit(f"{subj}: 分组名为空")
        if not g.get("cards"):
            sys.exit(f"{subj} / {g['name']}: 没有卡片")
        for c in g["cards"]:
            q, a = (c.get("q") or "").strip(), (c.get("a") or "").strip()
            if not q:
                sys.exit(f"{subj} / {g['name']}: 卡片标题为空")
            if q in seen:
                sys.exit(f"{subj}: 卡片标题重复: {q}")
            if len(a) < min_body:
                sys.exit(f"{subj} / {q}: 正文 {len(a)} 字 < {min_body}，讲不透知识点")
            c["q"], c["a"] = q, a
            seen.add(q)


def compose_common(host, base):
    """公共科目 = 行测卡片按映射重组 + 自身追加分组"""
    spec = host.get("from") or {}
    gm = spec.get("map") or {}
    skip = set(spec.get("skip") or [])
    buckets = {}
    for g in host.get("groups") or []:
        buckets.setdefault(g["name"], []).extend(copy.deepcopy(g["cards"]))
    for g in base["groups"]:
        mod = g["name"].split(" · ")[0]
        if mod in skip:
            continue
        tgt = gm.get(g["name"]) or gm.get(mod)
        if not tgt:
            continue
        buckets.setdefault(tgt, []).extend(copy.deepcopy(g["cards"]))
    order = host.get("group_order") or list(buckets)
    groups = [{"name": n, "cards": buckets[n]} for n in order if n in buckets]
    groups += [{"name": n, "cards": c} for n, c in buckets.items() if n not in order]
    return groups


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
    authored = load_authored()
    subs = []

    # ① 撰写科目（公共科目依赖行测，故先全部就绪再组装）
    raw = {}
    for name, d in authored.items():
        if d.get("from"):
            continue
        check_cards(name, d.get("groups") or [], min_body=d.get("min_body") or MIN_BODY)
        raw[name] = d.get("groups") or []

    for name, d in authored.items():
        if not d.get("from"):
            continue
        src = d["from"].get("subject")
        if src not in raw:
            sys.exit(f"{name}: inherit 源科目不存在: {src}")
        groups = compose_common(d, {"groups": raw[src]})
        check_cards(name, groups, min_body=d.get("min_body") or MIN_BODY)
        raw[name] = groups

    order = {name: (d.get("order") or 99) for name, d in authored.items()}
    for name in sorted(raw, key=lambda n: (order.get(n, 99), n)):
        subs.append({"name": name, "groups": raw[name]})

    # ② 法律：法考 knowledge.json（subject 分组）
    try:
        data = json.loads(get("https://cdn.jsdelivr.net/gh/DADA-dcc/fakao-pwa@main/knowledge.json"))
        by_s = {}
        for k in data:
            by_s.setdefault(k.get("subject") or "综合", []).append(
                {"q": k.get("point", ""), "a": k.get("detail", "")})
        groups = [{"name": s, "cards": c} for s, c in by_s.items()]
        subs.append({"name": "法律", "groups": groups})
        print(f"法律: {len(groups)} 组 / {sum(len(g['cards']) for g in groups)} 卡", flush=True)
    except Exception as e:
        print("法律失败:", e, flush=True)

    # ③ 软件设计师：本地缓存的章节知识块
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
                if re.search(r"第\s*\d+\s*题", s.get("title") or ""):
                    continue  # 真题讲解不是知识点
                txt = blocks_to_text(s.get("blocks"))
                if txt:
                    cards.append({"q": s.get("title", ""), "a": txt})
            if cards:
                groups.append({"name": ch.get("title") or f.get("title", "章"), "cards": cards})
        if groups:
            subs.append({"name": "软件设计师", "groups": groups})
            print(f"软件设计师: {len(groups)} 组 / {sum(len(g['cards']) for g in groups)} 卡", flush=True)
        else:
            print("软件设计师: 缓存章节缺失（跳过，先跑 import_ruankao.py 软设）", flush=True)
    except Exception as e:
        print("软件设计师失败:", e, flush=True)

    for s in subs:
        n = sum(len(g["cards"]) for g in s["groups"])
        lens = sorted(len(c["a"]) for g in s["groups"] for c in g["cards"])
        print(f"{s['name']}: {len(s['groups'])} 组 / {n} 卡，正文中位 {lens[len(lens)//2]} / 最短 {lens[0]}", flush=True)

    out = os.path.join(BASE, "data", "kp.json")
    json.dump({"subjects": subs}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"DONE -> kp.json {os.path.getsize(out)//1024} KB", flush=True)


if __name__ == "__main__":
    main()
