# -*- coding: utf-8 -*-
"""导入五个软考证书题库为新科目
- 系统架构设计师: Zhang-986/ruankao-architect-practice data/bank.json
- 系统分析师:     Bucky2216/sa-exam-trainer outputs/index.html（jsx_extract 提取 QUESTION_BANK/CASE_BANK）
- 信息系统项目管理师: xmgzxmgz/ruankao-cli questions.json
- 软件设计师:     yutils/ruankao-se-designer chapters+exam JS（js2json 转换）
- 信息安全工程师:  MrBaoquan/infosec-exam static/questions/*.json
用法: python tools/import_ruankao.py [cert ...]   # 不带参数=全部
"""
import json, urllib.request, os, sys, re, base64, subprocess, time, glob

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
TMP = os.path.join(BASE, "_tmp_ruankao")
os.makedirs(TMP, exist_ok=True)
UA = {"User-Agent": "curl/8", "Accept": "application/vnd.github+json"}
CDN_MAIN = "https://cdn.jsdelivr.net/gh/{}@main/"
CDN_MASTER = "https://cdn.jsdelivr.net/gh/{}@master/"

def fetch(url, timeout=90):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def fetch_json(url):
    return json.loads(fetch(url))

def cache_get(name, url):
    p = os.path.join(TMP, name)
    if os.path.exists(p) and os.path.getsize(p) > 500:
        return p
    print(f"  fetch {name} ...", flush=True)
    open(p, "wb").write(fetch(url))
    return p

# ---------- 通用规范化 ----------
def first(it, keys):
    for k in keys:
        v = it.get(k)
        if v not in (None, "", [], {}):
            return v
    return None

def opts_to_list(opts):
    if isinstance(opts, dict):
        ks = [k for k in sorted(opts.keys()) if k.upper() in "ABCDEF"]
        return [str(opts[k]) for k in ks] if ks else [str(v) for v in opts.values()]
    if isinstance(opts, list):
        if opts and isinstance(opts[0], dict):
            return [str(o.get("text", "")) for o in sorted(opts, key=lambda o: str(o.get("label", "A")))]
        return [str(o) for o in opts]
    return None

def ans_to_letters(ans):
    """→ 字母串（多选可多位），无法识别返回 ''"""
    if isinstance(ans, list):
        out = ""
        for a in ans:
            if isinstance(a, int) and 0 <= a < 7:
                out += "ABCDEFG"[a]
            elif isinstance(a, str) and re.fullmatch(r"[A-Fa-f]", a.strip()):
                out += a.strip().upper()
        return out
    if isinstance(ans, int):
        return "ABCDEFG"[ans] if 0 <= ans < 7 else ""
    s = str(ans).strip()
    return s.upper() if re.fullmatch(r"[A-Fa-f]+", s) else ""

def convert_choice(it, stem_keys=("stem", "question", "q", "title", "scenario")):
    stem = first(it, stem_keys)
    opts = opts_to_list(first(it, ("options", "opts", "choices")))
    ans = first(it, ("answer", "ans", "answers", "correct", "key"))
    expl = first(it, ("analysis", "exp", "explanation", "solution"))
    if not isinstance(stem, str) or not stem.strip() or not opts:
        return None
    letters = ans_to_letters(ans)
    if not letters or len(letters) > len(opts):
        return None
    if isinstance(expl, (dict, list)):
        expl = json.dumps(expl, ensure_ascii=False)
    return {
        "type": "multi" if len(letters) > 1 else "single",
        "stem": stem.strip(),
        "options": opts,
        "answer": letters,
        "explanation": (expl or "").strip(),
    }

def convert_subjective(stem, ans_text, expl):
    if not isinstance(stem, str) or not stem.strip():
        return None
    if isinstance(expl, (dict, list)):
        expl = json.dumps(expl, ensure_ascii=False)
    parts = []
    if ans_text and not re.fullmatch(r"[A-Fa-f]+", str(ans_text).strip()):
        parts.append("【参考答案】" + str(ans_text).strip())
    if expl:
        parts.append(str(expl).strip())
    return {"type": "subjective", "stem": stem.strip(), "options": [],
            "answer": "", "explanation": "\n\n".join(parts)}

# ---------- 各证书加载器 ----------
def load_architect():
    p = cache_get("architect_bank.json", CDN_MAIN.format("Zhang-986/ruankao-architect-practice") + "data/bank.json")
    raw = json.load(open(p, encoding="utf-8"))
    items = None
    for k in ("questions", "items", "data", "bank", "list"):
        if isinstance(raw, dict) and isinstance(raw.get(k), list):
            items = raw[k]; break
    if items is None:
        for v in raw.values() if isinstance(raw, dict) else []:
            if isinstance(v, list) and len(v) > 100 and isinstance(v[0], dict):
                items = v; break
    assert items, "architect bank: 找不到题数组"
    MOD = {"architecture": "系统架构设计", "software_engineering": "软件工程",
           "new_technology": "新技术应用", "database": "数据库系统",
           "network": "计算机网络", "security": "信息安全",
           "project_management": "项目管理", "embedded": "嵌入式系统",
           "operating_system": "操作系统", "system": "系统工程",
           "other": "其他", "management": "管理科学",
           "computer_foundation": "计算机系统基础", "legal_ip": "法律法规与知识产权",
           "english": "专业英语"}
    groups, stat = {}, {"choice": 0, "case": 0, "essay": 0, "skip": 0}
    mods_seen = []
    for it in items:
        st = str(it.get("sourceType") or it.get("type") or "").lower()
        term = it.get("term") or it.get("paper") or "综合"
        if st in ("choice", "single", "multi") or (it.get("options") and ans_to_letters(it.get("answer"))):
            e = convert_choice(it)
            if not e:
                stat["skip"] += 1; continue
            mod_raw = str(it.get("module") or "综合知识")
            mod = MOD.get(mod_raw, mod_raw.replace("_", " ").title() if mod_raw.isascii() else mod_raw)
            if mod_raw not in mods_seen:
                mods_seen.append(mod_raw)
            groups.setdefault((mod, term), []).append(e)
            stat["choice"] += 1
        else:
            stat["skip"] += 1
    # 案例：subQuestions 逐问成主观题
    for c in (raw.get("cases") or []):
        term = c.get("term") or c.get("paper") or "综合"
        base = ((c.get("title") or "") + "\n\n" + (c.get("description") or "")).strip()
        subs = c.get("subQuestions") or []
        if not subs:
            e = convert_subjective(base, None, None)
            if e:
                groups.setdefault(("案例分析", term), []).append(e); stat["case"] += 1
            continue
        for sub in subs:
            q = first(sub, ("q", "question", "stem", "prompt")) or ""
            a = first(sub, ("answer", "reference", "explanation", "points", "answerText"))
            if isinstance(a, list):
                a = "\n".join(str(x) for x in a)
            e = convert_subjective((base + "\n\n【问题】" + str(q)).strip() if q else base, a, None)
            if e:
                groups.setdefault(("案例分析", term), []).append(e); stat["case"] += 1
    # 论文：prompt + writingPoints
    for s in (raw.get("essays") or []):
        term = s.get("term") or s.get("paper") or "综合"
        stem = ((s.get("title") or "") + "\n\n" + (s.get("prompt") or "")).strip()
        wp = s.get("writingPoints")
        if isinstance(wp, list):
            wp = "\n".join(str(x) for x in wp)
        e = convert_subjective(stem, None, (str(wp) if wp else "") or None)
        if e:
            groups.setdefault(("论文", term), []).append(e); stat["essay"] += 1
    print(f"  architect: {stat} | modules: {mods_seen}", flush=True)
    # 选择模块排序按题量降序，案例/论文殿后
    order = sorted({s for s, _ in groups if s not in ("案例分析", "论文")},
                   key=lambda s: -sum(len(v) for (a, b), v in groups.items() if a == s))
    if "案例分析" in {s for s, _ in groups}: order.append("案例分析")
    if "论文" in {s for s, _ in groups}: order.append("论文")
    return "系统架构设计师", "架构", groups, order

def load_analyst():
    p = cache_get("analyst_bank.json", "LOCAL")  # 已由 jsx_extract 生成
    d = json.load(open(p, encoding="utf-8"))
    groups, stat = {}, {"choice": 0, "case": 0, "skip": 0}
    mod_order = []
    for q in d.get("QUESTION_BANK", []):
        e = convert_choice(q)
        if not e:
            stat["skip"] += 1; continue
        mod = str(q.get("module") or "综合知识")
        if mod not in mod_order: mod_order.append(mod)
        year = str(q.get("year") or "综合")
        groups.setdefault((mod, year), []).append(e)
        stat["choice"] += 1
    for c in d.get("CASE_BANK", []):
        scen = c.get("scenario") or ""
        for sub in (c.get("questions") or []):
            stem = (scen + "\n\n【问题】" + (sub.get("q") or "")).strip()
            e = convert_subjective(stem, sub.get("answer"), None)
            if e:
                mod = str(c.get("module") or "综合")
                groups.setdefault(("案例分析", mod), []).append(e); stat["case"] += 1
    print(f"  analyst: {stat} | modules: {mod_order}", flush=True)
    order = mod_order + ["案例分析"]
    return "系统分析师", "分析", groups, order

def load_gaoxiang():
    p = cache_get("gaoxiang_q.json", CDN_MAIN.format("xmgzxmgz/ruankao-cli") + "questions.json")
    raw = json.load(open(p, encoding="utf-8"))
    items = raw["questions"] if isinstance(raw, dict) and "questions" in raw else raw
    groups, stat = {}, {"q": 0, "skip": 0}
    sec_order = []
    for it in items:
        cat = str(it.get("cat") or "综合")
        if "/" in cat:
            sec, chap = [x.strip() for x in cat.split("/", 1)]
        else:
            sec, chap = cat, "综合"
        # 整卷类（真题/模拟卷名当 cat 的）归入「真题与模拟卷」，卷名做章节
        if re.search(r"(真题|模拟题|模拟密卷|模拟卷|^\d{4}年)", sec):
            chap, sec = sec, "真题与模拟卷"
        if sec not in sec_order: sec_order.append(sec)
        e = convert_choice(it, stem_keys=("q", "stem", "question", "title"))
        if not e:
            stat["skip"] += 1; continue
        groups.setdefault((sec, chap), []).append(e)
        stat["q"] += 1
    print(f"  gaoxiang: {stat} | sections: {len(sec_order)}", flush=True)
    return "信息系统项目管理师", "高项", groups, sec_order

def load_designer():
    # 章节（知识点标题）
    chap_titles, sec_titles = {}, {}
    for i in range(1, 14):
        cid = f"ch{i:02d}"
        src = cache_get(f"designer_{cid}.js", CDN_MASTER.format("yutils/ruankao-se-designer") + f"src/data/chapters/{cid}.js")
        out = os.path.join(TMP, f"designer_{cid}.json")
        subprocess.run(["node", os.path.join(BASE, "tools", "js2json.mjs"), src, out],
                       check=True, capture_output=True, cwd=BASE)
        data = json.load(open(out, encoding="utf-8"))
        chap_titles[cid] = data.get("title") or cid
        for s in data.get("sections") or []:
            if s.get("id"): sec_titles[s["id"]] = s.get("title") or s["id"]
    # 题库（真题+模拟）
    groups, stat, seen_ids = {}, {"q": 0, "dup": 0, "skip": 0}, set()
    for fn in ["real", "real-imported", "mock-a", "mock-b", "mock-c", "mock-d", "mock-e", "mock-f"]:
        src = cache_get(f"designer_{fn}.js", CDN_MASTER.format("yutils/ruankao-se-designer") + f"src/data/exam/{fn}.js")
        out = os.path.join(TMP, f"designer_{fn}.json")
        r = subprocess.run(["node", os.path.join(BASE, "tools", "js2json.mjs"), src, out],
                           capture_output=True, text=True, cwd=BASE)
        if r.returncode != 0:
            print(f"  designer {fn}: 跳过 ({r.stderr.strip()[:60]})", flush=True)
            continue
        items = json.load(open(out, encoding="utf-8"))
        if isinstance(items, dict):
            for v in items.values():
                if isinstance(v, list): items = v; break
        for it in items if isinstance(items, list) else []:
            iid = it.get("id")
            if iid in seen_ids:
                stat["dup"] += 1; continue
            seen_ids.add(iid)
            e = convert_choice(it)
            if not e:
                stat["skip"] += 1; continue
            ch_id = str(it.get("chapterId") or "")
            sec = chap_titles.get(ch_id) or "综合知识"
            secid = str(it.get("sectionId") or "")
            chap = sec_titles.get(secid) or (str(it.get("year") or "综合"))
            groups.setdefault((sec, chap), []).append(e)
            stat["q"] += 1
    order = [t for _, t in sorted(((k, chap_titles[k]) for k in chap_titles), key=lambda x: x[0])]
    order = [t for t in order if any(s == t for s, _ in groups)]
    print(f"  designer: {stat} | sections: {len(order)}", flush=True)
    return "软件设计师", "软设", groups, order

def load_infosec():
    SEC = {"application": "应用安全", "crypto": "密码学", "network": "网络安全",
           "system": "系统安全", "others": "其他"}
    groups, stat = {}, {"q": 0, "skip": 0}
    order = []
    for key, cn in SEC.items():
        p = cache_get(f"infosec_{key}.json", CDN_MAIN.format("MrBaoquan/infosec-exam") + f"static/questions/{key}.json")
        items = json.load(open(p, encoding="utf-8"))
        if cn not in order: order.append(cn)
        for it in items:
            e = convert_choice(it, stem_keys=("question", "stem", "q"))
            if not e:
                stat["skip"] += 1; continue
            topic = str(it.get("topic") or "综合")
            groups.setdefault((cn, topic), []).append(e)
            stat["q"] += 1
    print(f"  infosec: {stat} | sections: {order}", flush=True)
    return "信息安全工程师", "信安", groups, order

# ---------- 写盘 ----------
def write_subject(subj_name, prefix, groups, section_order):
    for old in glob.glob(os.path.join(DATA, f"{prefix}-*.json")):
        os.remove(old)
    ipath = os.path.join(DATA, "index.json")
    full = json.load(open(ipath, encoding="utf-8"))
    full["subjects"] = [s for s in full["subjects"] if s.get("id") != subj_name]

    def safe(x):
        return re.sub(r'[\\/#:*?"<>|\s]+', "-", str(x)).strip("-")[:28] or "x"

    secs = list(section_order) + [s for s in dict.fromkeys(a for a, _ in groups) if s not in section_order]
    subject = {"id": subj_name, "name": subj_name, "sections": []}
    n_total = 0
    for sec in secs:
        chaps = [(c, v) for (a, c), v in groups.items() if a == sec]
        if not chaps:
            continue
        s_entry = {"name": sec, "chapters": []}
        for chap, entries in chaps:
            cid = f"{prefix}-{safe(sec)}-{safe(chap)}"
            for i, e in enumerate(entries, 1):
                e["id"] = f"{cid}#{i}"
            with open(os.path.join(DATA, cid + ".json"), "w", encoding="utf-8") as fp:
                json.dump({"questions": entries}, fp, ensure_ascii=False)
            s_entry["chapters"].append({"id": cid, "name": str(chap),
                                        "file": f"data/{cid}.json", "count": len(entries)})
            n_total += len(entries)
        subject["sections"].append(s_entry)
    full["subjects"].append(subject)
    json.dump(full, open(ipath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    secs_print = [(s["name"], len(s["chapters"]), sum(c["count"] for c in s["chapters"])) for s in subject["sections"]]
    print(f"  -> {subj_name}: {n_total} q | sections: {secs_print}", flush=True)
    return n_total

LOADERS = {"架构": load_architect, "分析": load_analyst, "高项": load_gaoxiang,
           "软设": load_designer, "信安": load_infosec}

def main():
    want = sys.argv[1:] or list(LOADERS)
    n_all = 0
    for key in want:
        print(f"== {key} ==", flush=True)
        try:
            name, prefix, groups, order = LOADERS[key]()
            n_all += write_subject(name, prefix, groups, order)
        except Exception as e:
            import traceback
            print(f"  FAIL {key}: {e}", flush=True)
            traceback.print_exc()
    if n_all:
        sys.path.insert(0, os.path.join(BASE, "tools"))
        from reclassify import build_pools
        full = json.load(open(os.path.join(DATA, "index.json"), encoding="utf-8"))
        build_pools(full)
    print(f"DONE: {n_all} questions imported", flush=True)

if __name__ == "__main__":
    main()
