# -*- coding: utf-8 -*-
"""导入 chiyunxian/408 真题题库（720题/2009-2026）为新科目「408」
数据源：https://github.com/chiyunxian/408 （jsDelivr CDN 拉取）
用法: python tools/import_408.py
"""
import json, urllib.request, os, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
IMG = os.path.join(BASE, "img", "408")
os.makedirs(IMG, exist_ok=True)
UA = {"User-Agent": "curl/8"}
CDN = "https://cdn.jsdelivr.net/gh/chiyunxian/408@main/"

def fetch(url, timeout=40):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def main():
    # 1. 拉题库+元数据（questions.js：window.__408_DATA__ = {...};）
    raw = fetch(CDN + "data/questions.js").decode("utf-8", "ignore")
    j = raw.index("{")
    d, _ = json.JSONDecoder().raw_decode(raw[j:])
    books, questions = d["books"], d["questions"]
    print(f"source: {len(questions)} questions, {len(books)} books", flush=True)

    by_ch = {}
    for q in questions:
        by_ch.setdefault(q["chapter"], []).append(q)

    # 2. 幂等：清掉旧 408 章节文件与旧科目条目
    import glob
    for old in glob.glob(os.path.join(DATA, "408-*.json")):
        os.remove(old)

    idx_path = os.path.join(DATA, "index.json")
    idx = json.load(open(idx_path, encoding="utf-8"))
    idx["subjects"] = [s for s in idx["subjects"] if s.get("id") != "408"]

    # 3. 写章节文件 + 科目条目
    subject = {"id": "408", "name": "408", "sections": []}
    n_q = n_img_ok = n_img_fail = 0
    for b in books:
        sec = {"name": b["name"], "chapters": []}
        for c in b["chapters"]:
            cid = f"408-{c['id']}"
            out = []
            for i, q in enumerate(by_ch.get(c["id"], []), 1):
                opts = q.get("options") or {}
                entry = {
                    "id": f"{cid}#{i}",
                    "type": "single",
                    "stem": q.get("stem", ""),
                    "options": [opts[k] for k in ("A", "B", "C", "D") if k in opts],
                    "answer": q.get("answer", ""),
                    "explanation": "",
                }
                imgs = []
                for k, ip in enumerate(q.get("imgs") or [], 1):
                    fn = f"408/{c['id']}_{i}_{k}.png"
                    local = os.path.join(BASE, "img", fn)
                    try:
                        if not os.path.exists(local):
                            data_b = fetch(CDN + ip)
                            open(local, "wb").write(data_b)
                            time.sleep(0.12)
                        imgs.append("img/" + fn)
                        n_img_ok += 1
                    except Exception as e:
                        n_img_fail += 1
                        print(f"IMG-FAIL {ip}: {e}", flush=True)
                if len(imgs) == 1:
                    entry["img"] = imgs[0]
                elif imgs:
                    entry["img"] = imgs
                out.append(entry)
            with open(os.path.join(DATA, cid + ".json"), "w", encoding="utf-8") as fp:
                json.dump({"questions": out}, fp, ensure_ascii=False)
            sec["chapters"].append({"id": cid, "name": c["title"],
                                    "file": f"data/{cid}.json", "count": len(out)})
            n_q += len(out)
            print(f"OK {b['name']}/{c['title']}: {len(out)}q", flush=True)
        subject["sections"].append(sec)
    idx["subjects"].append(subject)
    json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 4. 408 题池（复用 build_pools，同种子不扰动既有科目）
    sys.path.insert(0, os.path.join(BASE, "tools"))
    from reclassify import build_pools
    build_pools(idx)

    print(f"DONE: {n_q} questions, images ok={n_img_ok} fail={n_img_fail}", flush=True)

if __name__ == "__main__":
    main()
