# -*- coding: utf-8 -*-
"""PDF -> 题库 JSON + 数学1 题目切图
公共科目：纯文本解析（题号/题干/选项/答案/解析 六要素）
数学1：按题切图（题干+公式区域渲染成 PNG），答案解析存文本
输出: data/index.json + data/<chapterId>.json + img/<qid>.png
用法: python tools/parse_pdfs.py
"""
import os, re, sys, json, glob

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "资料")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
os.makedirs(DATA, exist_ok=True)
os.makedirs(IMG, exist_ok=True)

from pypdf import PdfReader

# ---------- 文本切题 ----------
RE_QNUM = re.compile(r"(?m)^\s*(\d+)\s*[、.．]\s*(单选题|多选题|公共知识|岗位能力|常识判断|言语理解[^ \n]*|数量关系|判断推理|资料分析)?")
RE_ANSWER = re.compile(r"(?m)^正确答案[：:]\s*([A-F](?:[，,、 ]*[A-F])*)")  # 多选答案为 A，B，C 形式
RE_EXPL = re.compile(r"(?m)^解析[：:]?\s*$|^解析[：:]\s*")
RE_OPT = re.compile(r"(?m)^([A-F])\s*[：:.．]\s*")

def clean(t):
    t = t.replace("即刻题库 www.jike.vip", "")
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def unwrap(t):
    """PDF 断行拼回：句中硬换行合并，句末/列表行保留"""
    out = []
    for ln in t.split("\n"):
        if out and out[-1] and not re.search(r"[。！？；：.!?;:）)》”’\]]\s*$", out[-1]) \
           and not re.match(r"^\s*([A-F]\s*[、.．：:]|\d+\s*[、.．]|【|（[一二三四五]|\([一二三四五])", ln):
            out[-1] += ln.strip()
        else:
            out.append(ln)
    return "\n".join(out)

def parse_text_questions(raw):
    """把一章的全文切成题目列表"""
    raw = clean(raw)
    # 按题号锚点分割
    marks = [(m.start(), int(m.group(1))) for m in RE_QNUM.finditer(raw)]
    questions = []
    for i, (pos, num) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(raw)
        block = raw[pos:end]
        am = RE_ANSWER.search(block)
        if not am:
            continue  # 没答案的不当题目
        answer = re.sub(r"[^A-F]", "", am.group(1))
        em = RE_EXPL.search(block)
        expl = ""
        head = block[:am.start()]
        if em and em.start() > am.start():
            expl = unwrap(block[em.end():]).strip()
        # 选项切分：全文扫描 A->B->C... 顺序的选项标记（兼容 PDF 同行多选项）
        opt_re = re.compile(r"(?:^|[\s　])([A-F])\s*[：:.．、]\s*", re.M)
        opt_marks = []
        opos = 0
        for L in "ABCDEF":
            m = opt_re.search(head, opos)
            if not m:
                break
            opt_marks.append((m.group(1), m.start(), m.end()))
            opos = m.end()
        opts = {}
        for i, (L, s, e) in enumerate(opt_marks):
            end = opt_marks[i + 1][1] if i + 1 < len(opt_marks) else len(head)
            opts[L] = unwrap(head[e:end]).strip()
        # 题干 = 第一个选项标记之前（去掉题号行）
        stem_txt = head[:opt_marks[0][1]] if opt_marks else head
        lines = stem_txt.split("\n")
        while lines and (not lines[0].strip() or re.match(r"^\s*\d+\s*[、.．]", lines[0])):
            lines.pop(0)
        stem = unwrap("\n".join(lines)).strip()
        letters = sorted(opts.keys())
        if not letters:
            continue  # 无选项（纯图片题）由图片流程处理
        questions.append({
            "type": "multi" if len(answer) > 1 else "single",
            "stem": stem,
            "options": [opts.get(L, "").strip() for L in letters],
            "answer": answer,
            "explanation": expl,
        })
    return questions

# ---------- 图片切题（数学1 / 图表题）----------
RE_ANCHOR = re.compile(r"^\s*(\d+)\s*[、.．]\s*\S")

def parse_image_questions(pdf_path, prefix):
    """按题号/答案锚点切出题干区域渲染成 PNG（公式/图表在图里）
    跨页题输出多段图（img 为数组）；另附解析区域切图（expl_img）"""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    # 全文档收集锚点 (page, y, text)
    lines = []  # (pno, y0, y1, s)
    for pno in range(len(doc)):
        for block in doc[pno].get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for ln in block.get("lines", []):
                s = "".join(sp["text"] for sp in ln["spans"]).strip()
                if s:
                    lines.append((pno, ln["bbox"][1], ln["bbox"][3], s))
    lines.sort(key=lambda x: (x[0], x[1]))
    q_starts = [(pno, y0, int(m.group(1))) for pno, y0, y1, s in lines
                for m in [RE_ANCHOR.match(s)] if m and len(s) < 24]
    ans_lines = [(pno, y0, re.sub(r"[^A-F]", "", re.search(r"正确答案[：:]\s*([A-F](?:[，,、 ]*[A-F])*)", s).group(1)))
                 for pno, y0, y1, s in lines if re.search(r"正确答案[：:]\s*[A-F]", s)]

    def clip_to_imgs(y_from, y_to, qid, suffix=""):
        """从 (p0,y_from) 切到 (p1,y_to)，跨页则多段"""
        p0, yf = y_from
        p1, yt = y_to
        outs = []
        for p in range(p0, p1 + 1):
            page = doc[p]
            y_a = max(0, yf - 2) if p == p0 else 0
            y_b = min(page.rect.height, yt + 2) if p == p1 else page.rect.height
            if y_b - y_a < 4:
                continue
            clip = pymupdf.Rect(0, y_a, page.rect.width, y_b)
            rel = f"img/{qid}{suffix}_{p}.png"
            out_abs = os.path.join(ROOT, rel)
            if not os.path.exists(out_abs):  # 已切过则跳过（重跑提速）
                # ponytail: 灰度1.5x省70%体积(Pages 1GB上限)；彩色图表题灰度失真时按章重渲染RGB
                pix = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), clip=clip, colorspace=pymupdf.csGRAY)
                pix.save(out_abs)
            outs.append(rel)
        return outs

    questions = []
    seq = 0
    for (p0, y0, num) in q_starts:
        a = next(((p, y, ans) for p, y, ans in ans_lines if (p, y) > (p0, y0)), None)
        if not a:
            continue
        seq += 1
        qid = f"{prefix}_{seq}"
        imgs = clip_to_imgs((p0, y0), (a[0], a[1]), qid)
        if not imgs:
            continue
        # 解析区域：答案行 -> 下一题号行（全局）
        nxt = next(((p, y) for p, y, n in q_starts if (p, y) > (a[0], a[1])), (len(doc) - 1, doc[-1].rect.height))
        expl = " ".join(s for p, y0_, y1_, s in lines
                        if (p, y0_) > (a[0], a[1]) and (p, y0_) < nxt).strip()
        expl = re.sub(r"^正确答案[：:]\s*[A-F]+\s*|^解析[：:]?\s*", "", expl)
        expl_imgs = clip_to_imgs((a[0], a[1]), nxt, qid, "_e") if (nxt[0], nxt[1]) != (a[0], a[1]) else []
        ans = a[2]
        n_opt = max(4, max(ord(c) - 64 for c in ans))
        questions.append({
            "type": "multi" if len(ans) > 1 else "single",
            "stem": "",
            "img": imgs[0] if len(imgs) == 1 else imgs,
            "expl_img": expl_imgs[0] if len(expl_imgs) == 1 else (expl_imgs or None),
            "options": [""] * n_opt,
            "answer": ans,
            "explanation": expl,
        })
    doc.close()
    return questions

# ---------- 章节目录（按文件名归类）----------
SUBJ_RULES = [
    ("数学1", "数学1", [  # 前缀匹配本地资料目录
        ("函数|极限|连续|导数|微分|积分|级数|微分方程|空间解析|向量代数|多元", "高等数学"),
        ("行列式|矩阵|向量|线性方程|特征值|二次型|线性代数", "线性代数"),
        ("概率|随机|分布|数字特征|大数定律|中心极限|数理统计|参数估计|假设检验|抽样", "概率论与数理统计"),
    ]),
    ("公共科目", "公共科目", [  # 前缀匹配本地资料目录
        ("马克思主义|马原|哲学|认识|唯物|历史观|社会发展", "基本知识-马克思主义理论"),
        ("毛泽东|邓小平|三个代表|科学发展观|习近平|中特|社会主义", "基本知识-党的创新理论"),
        ("思想道德|人生观|理想信念|中国精神|核心价值观|道德", "基本知识-思想道德"),
        ("法治|宪法|法理|法律", "基本知识-法治知识"),
        ("人文|历史|文化|艺术", "基本知识-人文与社会"),
        ("科技|科学|技术", "基本知识-科学技术"),
        ("国防|军队|国情|国力|军事", "基本知识-国防和军队"),
        ("时政|两会|二十大|全会|政府工作报告|经济工作会议|十四五|应知应会|方针政策|高频考点|党的创新理论|综合练习|大国外交|战略布局|总体布局|总任务", "基本知识-政治理论与时政"),
        ("选词填空|逻辑填空|阅读理解|片段阅读|文章阅读|篇章阅读|语句表达", "岗位能力-言语理解与表达"),
        ("数学运算|数字推理|图形与几何|组合与概率|应用与综合", "岗位能力-数量关系"),
        ("图形推理|定义判断|类比推理|逻辑判断", "岗位能力-判断推理"),
        ("文字资料|表格资料|图形资料|混合资料|资料分析|文字型|表格型|图形型|综合型", "岗位能力-资料分析"),
    ]),
]

def classify(path):
    name = os.path.basename(path)
    dirname = path.replace("\\", "/")
    for root_dir, subject, rules in SUBJ_RULES:
        if root_dir in dirname:
            for pat, section in rules:
                if re.search(pat, name, re.I):
                    return subject, section
            return subject, "其他"
    return None, None

def make_cid(cid0, seen, counts):
    """同名章节消歧：首个沿用原 cid（进度兼容），其余加 -d序号。
    一文件一章节——旧版按同名合并会把不同专题的强化练习混成一章。"""
    if counts.get(cid0, 0) <= 1:
        return cid0
    k = seen.get(cid0, 0)
    seen[cid0] = k + 1
    return cid0 if k == 0 else f"{cid0}-d{k}"

def main():
    files = sorted(glob.glob(os.path.join(SRC, "**", "*.pdf"), recursive=True))
    files = [f for f in files if "题目+解析" in f.replace("\\", "/")]
    print(f"found {len(files)} pdfs", flush=True)

    # pass1：文件元信息 + 同名计数
    meta = []
    for f in files:
        subject, section = classify(f)
        if not subject:
            continue
        name = os.path.basename(f)
        chap = re.sub(r"^\d+-", "", name)           # 去编号前缀
        chap = re.sub(r"-\d+\.pdf$", "", chap)       # 去尾部 id
        chap = re.sub(r"\.pdf$", "", chap)
        chap = chap.replace("（解析）", "").replace(" 答案解析", "")
        cid0 = re.sub(r"\W+", "-", f"{subject[:2]}-{chap}")[:24].strip("-")
        meta.append((f, subject, section, chap, cid0, name))
    counts = {}
    for m in meta:
        counts[m[4]] = counts.get(m[4], 0) + 1

    # 清空旧数据（全部重建，避免孤儿文件）
    for old in glob.glob(os.path.join(DATA, "*.json")):
        os.remove(old)

    seen_cid, seen_img = {}, {}
    entries = []  # 源文件顺序（章节排序的基础）
    for f, subject, section, chap, cid0, orig in meta:
        try:
            reader = PdfReader(f)
            raw = "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as e:
            print(f"SKIP {orig}: {e}", flush=True)
            continue
        qs = parse_text_questions(raw)
        cid = make_cid(cid0, seen_cid, counts)
        # 图片前缀同规则消歧：同名文件首个沿用旧前缀（已有切图缓存命中），其余重渲染
        ibase = re.sub(r"\W", "", chap)[:12]
        k = seen_img.get(ibase, 0)
        seen_img[ibase] = k + 1
        prefix = ibase if k == 0 else f"{ibase}d{k}"
        if subject == "数学1":
            # 公式在图片里，整章切图
            try:
                img_qs = parse_image_questions(f, prefix)
                if img_qs:
                    qs = img_qs
            except Exception as e:
                print(f"IMG-FAIL {orig}: {e}", flush=True)
        elif qs and any(not q["stem"] for q in qs):
            # 公共科目图表题：题干为空的按序号对齐补图片
            try:
                img_qs = parse_image_questions(f, prefix)
                if len(img_qs) == len(qs):
                    for q, iq in zip(qs, img_qs):
                        if not q["stem"]:
                            q["img"] = iq["img"]
                            q["expl_img"] = iq.get("expl_img")
                            q["options"] = iq["options"] or q["options"]
            except Exception as e:
                print(f"IMG-MIX-FAIL {orig}: {e}", flush=True)
        if not qs:
            print(f"EMPTY {orig}", flush=True)
            continue
        for i, q in enumerate(qs):
            q["id"] = f"{cid}#{i+1}"
        with open(os.path.join(DATA, cid + ".json"), "w", encoding="utf-8") as fp:
            json.dump({"questions": qs}, fp, ensure_ascii=False)
        print(f"OK {subject}/{section}/{chap}: {len(qs)}q", flush=True)
        entries.append({"subject": subject, "section": section, "chap": chap,
                        "orig": orig, "cid": cid, "count": len(qs)})

    # index 按源文件顺序（节/章排序交给 reclassify 的规范化规则）
    subjects_out = {}
    n_total = 0
    for e in entries:
        n_total += e["count"]
        s = subjects_out.setdefault(e["subject"], {"id": e["subject"], "name": e["subject"], "sections": {}})
        sec = s["sections"].setdefault(e["section"], {"name": e["section"], "chapters": []})
        sec["chapters"].append({"id": e["cid"], "name": e["chap"],
                                "file": f"data/{e['cid']}.json", "count": e["count"],
                                "orig": e["orig"]})

    # 清理未被任何题引用的孤儿图片（同名前缀消歧后的遗留）
    referenced = set()
    for e in entries:
        with open(os.path.join(DATA, e["cid"] + ".json"), encoding="utf-8") as fp:
            for q in json.load(fp)["questions"]:
                for key in ("img", "expl_img"):
                    v = q.get(key)
                    if isinstance(v, list):
                        referenced.update(v)
                    elif v:
                        referenced.add(v)
    img_dir = os.path.join(ROOT, "img")
    removed = 0
    if os.path.isdir(img_dir):
        for fn in os.listdir(img_dir):
            if "img/" + fn not in referenced:
                os.remove(os.path.join(img_dir, fn))
                removed += 1
    print(f"orphan imgs removed: {removed}", flush=True)

    index_out = {"subjects": []}
    for s in subjects_out.values():
        s["sections"] = list(s["sections"].values())
        index_out["subjects"].append(s)
    with open(os.path.join(DATA, "index.json"), "w", encoding="utf-8") as fp:
        json.dump(index_out, fp, ensure_ascii=False, indent=1)
    print(f"DONE: {n_total} questions, {sum(len(s['sections']) for s in index_out['subjects'])} sections", flush=True)

if __name__ == "__main__":
    main()
