# -*- coding: utf-8 -*-
"""文件名英文化（一次性）
- data 章节文件 → {code}-{NNN}.json（408 已 ASCII 保留）；index 同步；q.id 重写
- img 根目录中文图 → {新cid}_{题序}[_a段][_e].png，题内引用同步（跨章共享图复用映射）
- data/pool 中文名 → pool/{code}.json（题内 qid 同步重写）
- 生成 data/idmap.json {旧cid: 新cid}，应用启动时迁移 localStorage 做题进度
- 清理被替换的旧文件
用法: python tools/rename_en.py [--dry]
"""
import json, os, re, sys, shutil, glob

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
IMG = os.path.join(BASE, "img")
DRY = "--dry" in sys.argv

# 科目显示名 → 英文代号（同时用于题池文件名与章节文件前缀）
CODE = {
    "公共科目": "common", "数学1": "math1", "408": "408", "行测": "civil",
    "法律": "law", "申论": "essay",
    "系统架构设计师": "architect", "系统分析师": "analyst",
    "信息系统项目管理师": "pm", "软件设计师": "dev", "信息安全工程师": "sec",
}
NAME_BY_CODE = {v: k for k, v in CODE.items()}
RE_ASCII = re.compile(r"^[A-Za-z0-9_.\-]+$")

def is_legacy_img(p):
    """根目录（非408/gk子目录）的旧中文图路径"""
    return isinstance(p, str) and p.startswith("img/") and \
        not p.startswith("img/408/") and not p.startswith("img/gk/") and \
        not RE_ASCII.match(p[len("img/"):])

def listify(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]

def main():
    idx = json.load(open(os.path.join(DATA, "index.json"), encoding="utf-8"))
    idmap = {}          # 旧 cid -> 新 cid
    n_ch_renamed = n_q_renamed = n_img_renamed = n_pool = 0

    for s in idx["subjects"]:
        name = s.get("name") or s.get("id")
        code = CODE.get(name)
        if not code:
            print(f"! 未知科目 {name} —— 跳过（检查 CODE 表）", flush=True)
            continue
        s["code"] = code
        seq = 0
        img_map = {}          # 旧 img 路径 -> 新 img 路径（全局按科目）
        chapters_flat = [c for sec in s.get("sections", []) for c in sec.get("chapters", [])]
        for ch in chapters_flat:
            old_id = ch["id"]
            if RE_ASCII.match(old_id):
                new_id = old_id          # 已英文（如 408-ds1）保留
            else:
                seq += 1
                new_id = f"{code}-{seq:03d}"
            old_file = os.path.join(BASE, ch["file"])
            new_rel = f"data/{new_id}.json"
            changed = new_id != old_id
            if not os.path.exists(old_file):
                print(f"! 缺文件 {ch['file']} 跳过", flush=True)
                continue
            qs = json.load(open(old_file, encoding="utf-8"))["questions"]
            for qi, q in enumerate(qs, 1):
                q["id"] = f"{new_id}#{qi}"
                n_q_renamed += 1
                for key, sub in (("img", ""), ("expl_img", "_e")):
                    old_list = listify(q.get(key))
                    if not old_list:
                        continue
                    new_list = []
                    total = len(old_list)
                    for j, op in enumerate(old_list, 1):
                        if not is_legacy_img(op):
                            new_list.append(op)     # 408/gk 等已英文的引用不动
                            continue
                        if op in img_map:
                            new_list.append(img_map[op])   # 跨题共享图复用
                            continue
                        ext = os.path.splitext(op)[1] or ".png"
                        if sub == "_e":
                            nn = f"{new_id}_{qi}_e{'' if total == 1 else j}{ext}" if total > 1 else f"{new_id}_{qi}_e{ext}"
                        else:
                            nn = f"{new_id}_{qi}{ext}" if total == 1 else f"{new_id}_{qi}_a{j}{ext}"
                        target = f"img/{nn}"
                        src_abs = os.path.join(BASE, op)
                        dst_abs = os.path.join(BASE, target)
                        if os.path.exists(src_abs):
                            if not DRY:
                                os.replace(src_abs, dst_abs)
                            img_map[op] = target
                            n_img_renamed += 1
                        else:
                            print(f"! 图缺失 {op}", flush=True)
                            img_map[op] = op
                        new_list.append(img_map[op])
                    q[key] = new_list[0] if len(new_list) == 1 else new_list
            if changed:
                idmap[old_id] = new_id
                n_ch_renamed += 1
            new_abs = os.path.join(DATA, f"{new_id}.json")
            if not DRY:
                json.dump({"questions": qs}, open(new_abs, "w", encoding="utf-8"), ensure_ascii=False)
                if changed and os.path.abspath(old_file) != os.path.abspath(new_abs):
                    os.remove(old_file)
            ch["id"] = new_id
            ch["file"] = new_rel

    # ---- 题池：按 code 重命名 + 内部 qid 重写 ----
    pool_dir = os.path.join(DATA, "pool")
    for pf in glob.glob(os.path.join(pool_dir, "*.json")):
        stem = os.path.splitext(os.path.basename(pf))[0]
        if stem in CODE.values():        # 已是代号（幂等重跑）
            code = stem
        elif stem in CODE:               # 旧显示名
            code = CODE[stem]
        else:
            continue
        pool = json.load(open(pf, encoding="utf-8"))
        changed = False
        for q in pool.get("questions", []):
            cid_old = q.get("id", "").split("#")[0]
            if cid_old in idmap:
                q["id"] = f"{idmap[cid_old]}#{q['id'].split('#')[1]}"
                changed = True
        target = os.path.join(pool_dir, f"{code}.json")
        if os.path.abspath(pf) != os.path.abspath(target):
            if not DRY:
                json.dump(pool, open(target, "w", encoding="utf-8"), ensure_ascii=False)
                os.remove(pf)
            n_pool += 1
            print(f"pool: {stem}.json -> {code}.json ({len(pool.get('questions', []))} q)", flush=True)

    if not DRY:
        json.dump(idx, open(os.path.join(DATA, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if idmap:
            json.dump(idmap, open(os.path.join(DATA, "idmap.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"DONE: 章节改名 {n_ch_renamed}，q.id 重写 {n_q_renamed}，图片改名 {n_img_renamed}，题池 {n_pool}，idmap {len(idmap)}", flush=True)
    # 校验：data/img 下非 ASCII 文件名应为 0（408/gk 子目录本就 ASCII）
    bad = 0
    for root, _, files in os.walk(DATA):
        for f in files:
            if not RE_ASCII.match(f):
                bad += 1
    for root, dirs, files in os.walk(IMG):
        for f in files:
            if not RE_ASCII.match(f):
                bad += 1
    print(f"残留非ASCII文件名: {bad}", flush=True)

if __name__ == "__main__":
    main()
