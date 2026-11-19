# -*- coding: utf-8 -*-
"""导入 elizen95/bailu-shenlun 申论真题（202 题题料答齐全）为新科目「申论」
数据源：_tmp_shenlun/library.sqlite3（questions join exam_meta，仅 stage=真题）
- 章节 = 题型（概括/分析/对策/应用文/大作文），章内按年份
- type="subjective" 主观题模式（阅读→看参考答案→自评）
用法: python tools/import_shenlun.py
"""
import sqlite3, json, os, sys, glob

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
DB = os.path.join(BASE, "_tmp_shenlun", "library.sqlite3")

TYPE_ORDER = ["概括", "分析", "对策", "应用文", "大作文"]

def main():
    assert os.path.exists(DB), "library.sqlite3 未就绪"
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    rows = db.execute("""
        SELECT q.id, q.type, q.student, q.teacher,
               m.year, m.region, m.variant, m.paper
        FROM questions q JOIN exam_meta m ON m.question_id = q.id
        WHERE q.stage = '真题' AND trim(coalesce(q.teacher,'')) <> ''
        ORDER BY m.year, m.region, m.variant, q.id
    """).fetchall()
    print(f"source: {len(rows)} 真题（题料答齐全）", flush=True)
    assert len(rows) == 202, f"expect 202, got {len(rows)}"

    # 幂等清理
    for old in glob.glob(os.path.join(DATA, "申论-*.json")):
        os.remove(old)
    ipath = os.path.join(DATA, "index.json")
    full = json.load(open(ipath, encoding="utf-8"))
    full["subjects"] = [s for s in full["subjects"] if s.get("id") != "申论"]

    # 按 题型→年份 分组
    groups = {}
    for r in rows:
        groups.setdefault((r["type"], r["year"] or 0), []).append(r)

    subject = {"id": "申论", "name": "申论", "sections": []}
    n_total = 0
    for t in TYPE_ORDER:
        years = sorted({y for (tt, y) in groups if tt == t}, reverse=True)
        if not years:
            continue
        sec = {"name": t, "chapters": []}
        for y in years:
            g = groups[(t, y)]
            cid = f"申论-{t}-{y}"
            out = []
            for i, r in enumerate(g, 1):
                meta = " · ".join(x for x in [str(r["year"] or ""), r["region"] or "", r["variant"] or ""] if x)
                out.append({
                    "id": f"{cid}#{i}",
                    "type": "subjective",
                    "stem": f"【{meta}】\n\n" + (r["student"] or "").strip(),
                    "options": [],
                    "answer": "",
                    "explanation": (r["teacher"] or "").strip(),
                })
            with open(os.path.join(DATA, cid + ".json"), "w", encoding="utf-8") as fp:
                json.dump({"questions": out}, fp, ensure_ascii=False)
            sec["chapters"].append({"id": cid, "name": str(y),
                                    "file": f"data/{cid}.json", "count": len(out)})
            n_total += len(out)
        subject["sections"].append(sec)
        print(f"  {t}: {len(sec['chapters'])} 年 / "
              f"{sum(c['count'] for c in sec['chapters'])} 题", flush=True)
    full["subjects"].append(subject)
    json.dump(full, open(ipath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    sys.path.insert(0, os.path.join(BASE, "tools"))
    from reclassify import build_pools
    build_pools(full)  # 主观题被过滤 → 申论题池为空（随机/模拟考走章节练习）
    print(f"DONE: {n_total} questions", flush=True)

if __name__ == "__main__":
    main()
