# -*- coding: utf-8 -*-
"""导入 DADA-dcc/fakao-pwa 法考题库（9,707 题/12 科目）为新科目「法律」
章节 = 难度（基础/中等/困难）；题型单选多选映射站内；analysis → 解析
用法: python tools/import_falv.py
"""
import json, urllib.request, os, sys, time, base64

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
TMP = os.path.join(BASE, "_tmp_falv")
os.makedirs(TMP, exist_ok=True)
UA = {"User-Agent": "curl/8"}
CDN = "https://cdn.jsdelivr.net/gh/DADA-dcc/fakao-pwa@main/questions/"

# 法考大纲式顺序
ORDER = ["宪法", "法理学", "法制史", "国际法", "民法", "刑法", "行政法",
         "民诉法", "刑诉法", "商经法", "知识产权法", "司法制度与职业道德",
         "司法制度与道德", "法制史"]
DIFF_ORDER = ["基础", "中等", "困难"]

def fetch(url, timeout=90, dest=None):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
    if dest is None:
        return r.read()
    with open(dest, "wb") as f:
        while True:
            c = r.read(1 << 20)
            if not c:
                break
            f.write(c)
    return os.path.getsize(dest)

def load_json(enc_name, cache):
    """cdn → fastly → raw 三链"""
    if os.path.exists(cache) and os.path.getsize(cache) > 500:
        return json.load(open(cache, encoding="utf-8"))
    import urllib.parse
    paths = [enc_name, urllib.parse.quote(urllib.parse.unquote(enc_name))]
    for base in (CDN, CDN.replace("cdn.jsdelivr.net", "fastly.jsdelivr.net"),
                 "https://raw.githubusercontent.com/DADA-dcc/fakao-pwa/main/questions/"):
        try:
            data = fetch(base + paths[0], timeout=60)
            if data[:1] == b"[" or data[:1] == b"{":
                open(cache, "wb").write(data)
                return json.loads(data)
        except Exception as e:
            print(f"  fail {base.split('/')[2]}: {e}", flush=True)
            time.sleep(1)
    raise RuntimeError(f"all mirrors failed for {enc_name}")

def main():
    import urllib.parse
    idx = json.loads(fetch(CDN + urllib.parse.quote("index.json"), timeout=40))
    subjects = idx["subjects"]
    print(f"source: {idx['total']} q, {len(subjects)} subjects", flush=True)

    # 幂等清理
    import glob
    for old in glob.glob(os.path.join(DATA, "法律-*.json")):
        os.remove(old)
    ipath = os.path.join(DATA, "index.json")
    full = json.load(open(ipath, encoding="utf-8"))
    full["subjects"] = [s for s in full["subjects"] if s.get("id") not in ("法律",)]

    subject = {"id": "法律", "name": "法律", "sections": []}
    order = [n for n in ORDER if n in subjects] + [n for n in subjects if n not in ORDER]
    n_q = 0
    for name in order:
        meta = subjects[name]
        enc = urllib.parse.quote(meta["file"])
        qs = load_json(enc, os.path.join(TMP, meta["file"]))
        # 按难度分章
        groups = {}
        for q in qs:
            d = (q.get("difficulty") or "").strip() or "未分级"
            groups.setdefault(d, []).append(q)
        sec = {"name": name, "chapters": []}
        for d in DIFF_ORDER + [k for k in groups if k not in DIFF_ORDER]:
            g = groups.get(d)
            if not g:
                continue
            cid = f"法律-{name}-{d}"
            out = []
            for i, q in enumerate(g, 1):
                opts = q.get("options") or {}
                entry = {
                    "id": f"{cid}#{i}",
                    "type": "multi" if (q.get("type") or "").find("多") >= 0 else "single",
                    "stem": q.get("question", ""),
                    "options": [opts[k] for k in ("A", "B", "C", "D", "E", "F") if k in opts],
                    "answer": q.get("answer", ""),
                    "explanation": q.get("analysis") or "",
                }
                out.append(entry)
            with open(os.path.join(DATA, cid + ".json"), "w", encoding="utf-8") as fp:
                json.dump({"questions": out}, fp, ensure_ascii=False)
            sec["chapters"].append({"id": cid, "name": d, "file": f"data/{cid}.json", "count": len(out)})
            n_q += len(out)
        subject["sections"].append(sec)
        print(f"  {name}: {len(qs)} q -> {len(sec['chapters'])} ch", flush=True)
    full["subjects"].append(subject)
    json.dump(full, open(ipath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    sys.path.insert(0, os.path.join(BASE, "tools"))
    from reclassify import build_pools
    build_pools(full)
    print(f"DONE: {n_q} questions", flush=True)

if __name__ == "__main__":
    main()
