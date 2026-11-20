# -*- coding: utf-8 -*-
"""导入 xiaogaostu/xingce-app 行测真题（22,298 题，2022-2026）为新科目「行测」
- 文本：jsDelivr 拉 6 个模块 JSON（50.6MB）
- 配图：GitHub Releases 下完整版 APK（116MB，即 ZIP）解出被引用的题目图
- 章节 = 题型（qtype），板块 = 模块；含解析/材料题材料拼干
用法: python tools/import_kaogong.py
"""
import json, urllib.request, os, sys, re, html as htmllib, zipfile, hashlib, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
IMG = os.path.join(BASE, "img", "gk")
TMP = os.path.join(BASE, "_tmp_xingce")
os.makedirs(IMG, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

UA = {"User-Agent": "curl/8"}
CDN = "https://cdn.jsdelivr.net/gh/xiaogaostu/xingce-app@main/web/public/data/"
MODULES = {  # 文件名(已URL编码) -> 板块
    "%E6%94%BF%E6%B2%BB%E7%90%86%E8%AE%BA.json": "政治理论",
    "%E5%B8%B8%E8%AF%86%E5%88%A4%E6%96%AD.json": "常识判断",
    "%E8%A8%80%E8%AF%AD%E7%90%86%E8%A7%A3%E4%B8%8E%E8%A1%A8%E8%BE%BE.json": "言语理解与表达",
    "%E6%95%B0%E9%87%8F%E5%85%B3%E7%B3%BB.json": "数量关系",
    "%E5%88%A4%E6%96%AD%E6%8E%A8%E7%90%86.json": "判断推理",
    "%E8%B5%84%E6%96%99%E5%88%86%E6%9E%90.json": "资料分析",
}
APK_URL = "https://github.com/xiaogaostu/xingce-app/releases/download/v1.10.0/xingce-app-v29-full.apk"

def fetch(url, timeout=120, dest=None):
    """下载；dest 给定时流式写文件（APK 116MB）"""
    req = urllib.request.Request(url, headers=UA)
    r = urllib.request.urlopen(req, timeout=timeout)
    if dest is None:
        return r.read()
    total = int(r.headers.get("Content-Length") or 0)
    done = 0
    with open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if total and done % (10 << 20) < (1 << 20):
                print(f"  ...{done/1048576:.0f}/{total/1048576:.0f} MB", flush=True)
    return done

_GH_SHA = {}
def gh_sha(path):
    if not _GH_SHA:
        d = json.loads(fetch("https://api.github.com/repos/xiaogaostu/xingce-app/git/trees/HEAD?recursive=1", timeout=40))
        _GH_SHA.update({t["path"]: t["sha"] for t in d["tree"]})
    return _GH_SHA.get(path)

def load_module(enc, name):
    """模块 JSON：cdn → fastly → raw → GitHub Blob 兜底（各带重试）"""
    import urllib.parse, base64
    path = os.path.join(TMP, name + ".json")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return json.load(open(path, encoding="utf-8"))
    urls = [
        CDN + enc,
        CDN.replace("cdn.jsdelivr.net", "fastly.jsdelivr.net") + enc,
        "https://raw.githubusercontent.com/xiaogaostu/xingce-app/main/web/public/data/" + enc,
    ]
    data = None
    for u in urls:
        for attempt in (1, 2):
            try:
                data = fetch(u, timeout=60)
                if data[:1] in (b"[", b"{"):
                    break
                data = None
            except Exception as e:
                print(f"  fail {u.split('/')[2]} attempt{attempt}: {e}", flush=True)
            time.sleep(1.5)
        if data:
            break
    if data is None:
        sha = gh_sha("web/public/data/" + urllib.parse.unquote(enc))
        if not sha:
            raise RuntimeError(f"no sha for {name}")
        blob = json.loads(fetch(f"https://api.github.com/repos/xiaogaostu/xingce-app/git/blobs/{sha}", timeout=60))
        data = base64.b64decode(blob["content"])
        print(f"  {name}: served via GitHub Blob", flush=True)
    open(path, "wb").write(data)
    return json.loads(data)

def strip_html(s):
    """返回 (纯文本, [图片src])"""
    if not s:
        return "", []
    srcs = re.findall(r"<img[^>]+src=[\"']([^\"']+)[\"']", s, flags=re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h[1-6]>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = htmllib.unescape(s).replace(" ", " ")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip(), srcs

def main():
    # ---------- 1. 模块 JSON ----------
    mods = {}
    for enc, name in MODULES.items():
        print(f"fetch {name}.json ...", flush=True)
        mods[name] = load_module(enc, name)
        print(f"  {name}: {len(mods[name])} q", flush=True)

    # ---------- 2. APK（三试） ----------
    apk = os.path.join(TMP, "full.apk")
    if not os.path.exists(apk) or os.path.getsize(apk) < 100_000_000:
        for attempt in range(3):
            try:
                print(f"download full.apk (116MB) attempt{attempt + 1} ...", flush=True)
                fetch(APK_URL, timeout=300, dest=apk)
                break
            except Exception as e:
                print(f"  apk fail: {e}", flush=True)
                time.sleep(3)
        if not os.path.exists(apk) or os.path.getsize(apk) < 100_000_000:
            raise RuntimeError("APK download failed after 3 attempts")
    zf = zipfile.ZipFile(apk)
    img_by_name = {}
    for info in zf.infolist():
        if info.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            img_by_name.setdefault(os.path.basename(info.filename), info.filename)
    print(f"apk images indexed: {len(img_by_name)}", flush=True)

    # ---------- 3. 转换 ----------
    from importlib import util as _u
    used_names = {}
    def resolve_img(srcs, tag):
        """srcs → 本地 img/gk/ 路径（按 basename 从 APK 取）"""
        out = []
        for s in srcs:
            base = os.path.basename(s)
            key = base
            if key in used_names and used_names[key] != s:
                key = hashlib.md5(s.encode()).hexdigest()[:6] + "_" + base
            used_names[key] = s
            member = img_by_name.get(base)
            if not member:
                continue
            local = os.path.join(IMG, key)
            if not os.path.exists(local):
                with zf.open(member) as src, open(local, "wb") as dst:
                    dst.write(src.read())
            out.append("img/gk/" + key)
        return out

    # 章节聚合: (模块, qtype) -> [题目]
    groups = {}
    stats = {"img_ok": 0, "img_miss": 0}
    for name, qs in mods.items():
        for q in qs:
            qtype = (q.get("qtype") or "").strip() or "综合"
            mat_txt, mat_imgs = strip_html(q.get("material_content"))
            stem_txt, stem_imgs = strip_html(q.get("stem"))
            expl_txt, expl_imgs = strip_html(q.get("analysis"))
            parts = ([mat_txt] if mat_txt else []) + ([stem_txt] if stem_txt else [])
            imgs = resolve_img(mat_imgs + stem_imgs, "q")
            stats["img_ok"] += len(imgs)
            e_imgs = resolve_img(expl_imgs, "e")
            stats["img_ok"] += len(e_imgs)
            opts_src = q.get("options") or []
            opts = [strip_html(o.get("text", ""))[0] for o in
                    sorted(opts_src, key=lambda o: o.get("label", ""))]
            entry = {"type": "single", "stem": "\n\n".join(parts),
                     "options": opts, "answer": q.get("answer", ""),
                     "explanation": expl_txt}
            if len(imgs) == 1:
                entry["img"] = imgs[0]
            elif imgs:
                entry["img"] = imgs
            if len(e_imgs) == 1:
                entry["expl_img"] = e_imgs[0]
            elif e_imgs:
                entry["expl_img"] = e_imgs
            groups.setdefault((name, qtype), []).append(entry)
    zf.close()

    # ---------- 4. 写盘（幂等）----------
    import glob
    for old in glob.glob(os.path.join(DATA, "考公-*.json")):
        os.remove(old)
    idx_path = os.path.join(DATA, "index.json")
    idx = json.load(open(idx_path, encoding="utf-8"))
    idx["subjects"] = [s for s in idx["subjects"] if s.get("id") not in ("行测", "考公考编")]

    MOD_ORDER = ["政治理论", "常识判断", "言语理解与表达", "数量关系", "判断推理", "资料分析"]
    subject = {"id": "行测", "name": "行测", "sections": []}
    n_q = 0
    for mod in MOD_ORDER:
        pairs = [(qt, g) for (m, qt), g in groups.items() if m == mod]
        if not pairs:
            continue
        pairs.sort(key=lambda p: -len(p[1]))  # 题量大的题型在前
        sec = {"name": mod, "chapters": []}
        n_ch = 0
        for qt, g in pairs:
            n_ch += 1
            cid = f"civil-{len([1 for x in subject['sections'] for c in x['chapters']]) + n_ch:03d}"
            for i, e in enumerate(g, 1):
                e["id"] = f"{cid}#{i}"
            with open(os.path.join(DATA, cid + ".json"), "w", encoding="utf-8") as fp:
                json.dump({"questions": g}, fp, ensure_ascii=False)
            sec["chapters"].append({"id": cid, "name": qt,
                                    "file": f"data/{cid}.json", "count": len(g)})
            n_q += len(g)
        subject["sections"].append(sec)
        print(f"section {mod}: {len(sec['chapters'])} ch / "
              f"{sum(c['count'] for c in sec['chapters'])} q", flush=True)
    idx["subjects"].append(subject)
    json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---------- 5. 题池 ----------
    sys.path.insert(0, os.path.join(BASE, "tools"))
    from reclassify import build_pools
    build_pools(idx)

    img_mb = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG)) / 1048576
    print(f"DONE: {n_q} questions, images used={stats['img_ok']} "
          f"(unique {len(os.listdir(IMG))}, {img_mb:.0f} MB)", flush=True)

if __name__ == "__main__":
    main()
