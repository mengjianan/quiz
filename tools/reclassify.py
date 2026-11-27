# -*- coding: utf-8 -*-
"""章节规范化：板块规范排序 + 专题路由 + 同名章节合并 + 真题年份序 + 题池生成
parse_pdfs.py 跑完后执行"""
import json, re, sys, os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 板块规范顺序（考试大纲顺序；未列出的排最后）
SECTION_ORDER = {
    "公共科目": [
        "基本知识-马克思主义理论", "基本知识-党的创新理论与时政", "基本知识-中国近现代史",
        "基本知识-思想道德", "基本知识-法治知识", "基本知识-人文与社会",
        "基本知识-科学技术", "基本知识-国防和军队",
        "岗位能力-言语理解与表达", "岗位能力-数量关系", "岗位能力-判断推理", "岗位能力-资料分析",
        "综合强化", "真题与模拟卷", "其他",
    ],
    "数学1": ["高等数学", "线性代数", "概率论与数理统计", "综合强化", "真题与模拟卷", "其他"],
    "408": ["数据结构", "计算机组成原理", "操作系统", "计算机网络"],
    "行测": ["政治理论", "常识判断", "言语理解与表达", "数量关系", "判断推理", "资料分析"],
    "法律": ["宪法", "法理学", "法制史", "国际法", "民法", "刑法", "行政法",
             "民诉法", "刑诉法", "商经法", "知识产权法", "司法制度与职业道德"],
    "申论": ["概括", "分析", "对策", "应用文", "大作文"],
}
# 板块合并：旧解析产生的近似板块并入规范名
PARTS = {"基本知识-党的创新理论": "基本知识-党的创新理论与时政"}

# 公共科目岗位能力：按源文件编号前缀直接路由（比关键词猜可靠）
TOPIC_PREFIX = {
    "201": ("岗位能力-言语理解与表达", "言语"), "369": ("岗位能力-言语理解与表达", "言语"),
    "202": ("岗位能力-数量关系", "数量"), "370": ("岗位能力-数量关系", "数量"),
    "203": ("岗位能力-判断推理", "判断"), "371": ("岗位能力-判断推理", "判断"),
    "204": ("岗位能力-资料分析", "资料"), "372": ("岗位能力-资料分析", "资料"),
}
# 无辨识度的通用章节名（路由后加专题前缀，如「言语·强化训练」）
GENERIC = {"强化练习", "强化训练", "综合练习", "综合型资料", "应用与综合", "典型例题", "章节练习"}

POLITICS = (r"两会|二十大|一号文件|全会|工作报告|经济工作会议|十四五|方针政策|"
            r"高频考点|应知应会|大国外交|时政|党的创新理论|综合练习")

# 公共科目按源文件编号前缀全量路由（文件编号体系已探明，比关键词可靠）
ORIG_SEC = [
    ("10201", "基本知识-马克思主义理论"), ("700228", "基本知识-马克思主义理论"),
    ("10202", "基本知识-党的创新理论与时政"), ("10203", "基本知识-党的创新理论与时政"),
    ("10204", "基本知识-党的创新理论与时政"), ("700229", "基本知识-党的创新理论与时政"),
    ("700230", "基本知识-党的创新理论与时政"), ("7003", "基本知识-党的创新理论与时政"),
    ("661", "基本知识-党的创新理论与时政"), ("662", "基本知识-党的创新理论与时政"),
    ("7001", "基本知识-党的创新理论与时政"),
    ("700231", "基本知识-中国近现代史"),
    ("10302", "基本知识-思想道德"), ("10304", "基本知识-法治知识"),
    ("10301", "基本知识-人文与社会"), ("10306", "基本知识-科学技术"),
    ("1041", "基本知识-国防和军队"),
    ("201", "岗位能力-言语理解与表达"), ("369", "岗位能力-言语理解与表达"),
    ("202", "岗位能力-数量关系"), ("370", "岗位能力-数量关系"),
    ("203", "岗位能力-判断推理"), ("371", "岗位能力-判断推理"),
    ("204", "岗位能力-资料分析"), ("372", "岗位能力-资料分析"),
]

def orig_section(orig):
    for pre, sec in ORIG_SEC:
        if (orig or "").startswith(pre):
            return sec
    return None

def reclass(subject, name, orig=""):
    if re.search(r"真题|模拟预测|预测", name):
        return "真题与模拟卷"
    if subject != "数学1":
        sec = orig_section(orig)
        if sec:
            return sec
        p = (orig or "")[:3]
        if p in TOPIC_PREFIX:
            return TOPIC_PREFIX[p][0]
        if re.search(POLITICS, name):
            return "基本知识-党的创新理论与时政"
        if re.search(r"强化练习|强化训练|典型例题|章节练习", name):
            return "综合强化"
        if re.search(r"辛亥|革命|抗日|长征|五四|新中国|近代|共产党成立|建国|改革开放|社会主义改造|社会主义建设道路|新民主主义|不同社会力量|早期探索", name):
            return "基本知识-中国近现代史"
        if re.search(r"物质|实践与认识|人类社会|资本主义|共产主义|历史观|无产阶级|马克思主义|辩证|唯物|导论|历史发展的动力|社会发展|社会主义的发展", name):
            return "基本知识-马克思主义理论"
        if re.search(r"人生观|理想信念|中国精神|核心价值观|道德规范", name):
            return "基本知识-思想道德"
        if re.search(r"毛泽东|邓小平|三个代表|科学发展观|习近平|中国特色社会主义|新时代|总任务|总体布局|战略布局|坚持和加强", name):
            return "基本知识-党的创新理论与时政"
        return None
    # 数学1
    if re.search(r"强化练习|典型例题|章节练习", name):
        return "综合强化"
    if re.search(r"概率|随机|分布|数字特征|大数|中心极限|数理统计|参数估计|假设检验|抽样|样本|贝叶斯|事件", name):
        return "概率论与数理统计"
    if re.search(r"矩阵|行列式|向量|方程组|特征值|二次型|初等|秩|相似|合同|逆|伴随|转置|余子式|线性", name):
        return "线性代数"
    return "高等数学"  # 数学1 兜底

def norm_name(n):
    """章节名归一化：去掉序号前缀（第一章 / 一、 / (四) 等），用于识别同名重复章节"""
    n = re.sub(r"^第\s*[0-9一二三四五六七八九十]+\s*[章节][\s　、．.]*", "", n)
    n = re.sub(r"^[（(][0-9一二三四五六七八九十]+[)）][\s　、．.]*", "", n)
    n = re.sub(r"^[0-9一二三四五六七八九十]+[、．.][\s　]*", "", n)
    return n.strip()

def merge_section(chapters):
    """同名（归一化后）章节合并：不同教材的同一专题并成一章，重写数据文件"""
    groups = {}
    for c in chapters:
        groups.setdefault(norm_name(c["name"]), []).append(c)
    out = []
    for key, g in groups.items():
        if len(g) == 1:
            out.append(g[0])
            continue
        main = g[0]
        qs = []
        for m in g:
            path = os.path.join(BASE, m["file"])
            if os.path.exists(path):
                qs.extend(json.load(open(path, encoding="utf-8"))["questions"])
            if m is not main:
                try:
                    os.remove(path)
                except OSError:
                    pass
        disp = next((m["name"] for m in g if m["name"] == key), main["name"])
        for i, q in enumerate(qs):
            q["id"] = f"{main['id']}#{i+1}"
        json.dump({"questions": qs}, open(os.path.join(BASE, main["file"]), "w", encoding="utf-8"),
                  ensure_ascii=False)
        out.append({**main, "name": disp, "count": len(qs),
                    "orig": min((m.get("orig") or "") for m in g)})
        print(f"  merge {key}: {len(g)} -> 1 ({len(qs)}q)", flush=True)
    return out

def chapter_sort_key(c, section):
    """真题/模拟卷：真题按年份倒序在前，模拟卷在后"""
    name = c["name"]
    is_zt = 0 if "真题" in name else 1
    yrs = re.findall(r"(\d{4})", name)
    yr = int(yrs[0]) if yrs else 0
    m = re.search(r"模拟预测(\d+)", name)
    seq = int(m.group(1)) if m else 0
    return (is_zt, -yr if is_zt == 0 else yr, seq)

def build_pools(idx):
    """每科生成题池（开始考试/随机练习单文件加载，替代串行拉全库）"""
    import random
    pool_dir = os.path.join(BASE, "data", "pool")
    os.makedirs(pool_dir, exist_ok=True)
    random.seed(20261117)  # 可复现抽样；运行时 shuffle 保证每次组卷不同
    for s in idx["subjects"]:
        allq = []
        for sec in s["sections"]:
            for c in sec["chapters"]:
                f = os.path.join(BASE, c["file"])
                if os.path.exists(f):
                    # 主观题（申论）不入题池：随机/模拟考只组客观题
                    allq.extend(q for q in json.load(open(f, encoding="utf-8"))["questions"]
                                if q.get("type") != "subjective")
        pool = random.sample(allq, min(600, len(allq)))
        out = os.path.join(pool_dir, f"{s.get('code') or s['name']}.json")
        json.dump({"questions": pool}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"pool {s['name']}: {len(pool)} q, {os.path.getsize(out)//1024} KB")

def main():
    path = os.path.join(BASE, "data", "index.json")
    idx = json.load(open(path, encoding="utf-8"))
    for s in idx["subjects"]:
        newsecs = {}
        for sec in s["sections"]:
            for c in sec["chapters"]:
                tgt = reclass(s["name"], c["name"], c.get("orig", "")) or sec["name"]
                tgt = PARTS.get(tgt, tgt)
                c2 = dict(c)
                # 通用名加专题前缀（按源文件前缀路由时）
                p = (c.get("orig") or "")[:3]
                if s["name"] != "数学1" and p in TOPIC_PREFIX and c2["name"] in GENERIC:
                    c2["name"] = f"{TOPIC_PREFIX[p][1]}·{c2['name']}"
                newsecs.setdefault(tgt, []).append(c2)

        # 板块按规范顺序；章内按源文件编号（教材序）排序，合并放最后保证占位正确
        order = SECTION_ORDER.get(s["name"], [])
        sections = []
        for name in order + [k for k in newsecs if k not in order]:
            if name not in newsecs:
                continue
            chaps = newsecs.pop(name)
            if name == "真题与模拟卷":
                chaps = sorted(chaps, key=lambda c: chapter_sort_key(c, name))
            elif name == "基本知识-党的创新理论与时政":
                # 理论章节在前，时政月报归档靠后
                chaps = sorted(chaps, key=lambda c: (
                    1 if re.search(r"\d{4}年\d{1,2}月时政", c["name"]) else 0,
                    c.get("orig") or ""))
            else:
                chaps = sorted(chaps, key=lambda c: c.get("orig") or "")
            sections.append({"name": name, "chapters": merge_section(chaps)})
        s["sections"] = sections
        for sec in s["sections"]:
            n = sum(c["count"] for c in sec["chapters"])
            print(f"{s['name']} / {sec['name']}: {len(sec['chapters'])} ch / {n} q", flush=True)

    json.dump(idx, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    build_pools(idx)
    print("reclassify OK")

if __name__ == "__main__":
    main()
