# -*- coding: utf-8 -*-
"""index.json 章节重归类：真题/模拟卷单列、知识点各归其位
parse_pdfs.py 跑完后执行"""
import json, re, sys, os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def reclass(subject, name):
    if re.search(r"真题|模拟预测|预测", name):
        return "真题与模拟卷"
    if re.search(r"强化练习|强化训练|典型例题|章节练习|综合", name):
        return "综合强化"
    if subject == "数学1":
        if re.search(r"概率|随机|分布|数字特征|大数|中心极限|数理统计|参数估计|假设检验|抽样|样本|贝叶斯|事件", name):
            return "概率论与数理统计"
        if re.search(r"矩阵|行列式|向量|方程组|特征值|二次型|初等|秩|相似|合同|逆|伴随|转置|余子式|线性", name):
            return "线性代数"
        return "高等数学"
    if re.search(r"辛亥|革命|抗日|长征|五四|新中国|近代|共产党成立|建国|改革开放|社会主义改造|社会主义建设道路|新民主主义", name):
        return "基本知识-中国近现代史"
    if re.search(r"物质|实践与认识|人类社会|资本主义|共产主义|历史观|无产阶级|马克思主义|辩证|唯物|导论|历史发展的动力|社会发展", name):
        return "基本知识-马克思主义理论"
    if re.search(r"毛泽东|邓小平|三个代表|科学发展观|习近平|中国特色社会主义|新时代|总任务|总体布局|战略布局|大国外交|十四五|二十大|两会|中央|一号文件|全会|工作报告|经济工作会议|方针政策|高频考点|应知应会|党的创新|时政|坚持和加强", name):
        return "基本知识-党的创新理论与时政"
    return None

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
                    allq.extend(json.load(open(f, encoding="utf-8"))["questions"])
        pool = random.sample(allq, min(600, len(allq)))
        out = os.path.join(pool_dir, f"{s['name']}.json")
        json.dump({"questions": pool}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"pool {s['name']}: {len(pool)} q, {os.path.getsize(out)//1024} KB")

def main():
    path = os.path.join(BASE, "data", "index.json")
    idx = json.load(open(path, encoding="utf-8"))
    for s in idx["subjects"]:
        newsecs = {}
        for sec in s["sections"]:
            for c in sec["chapters"]:
                tgt = reclass(s["name"], c["name"]) or sec["name"]
                newsecs.setdefault(tgt, []).append(c)
        s["sections"] = [{"name": k, "chapters": v} for k, v in sorted(newsecs.items())]
        for sec in s["sections"]:
            n = sum(c["count"] for c in sec["chapters"])
            print(f"{s['name']} / {sec['name']}: {len(sec['chapters'])} ch / {n} q")
    json.dump(idx, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    build_pools(idx)
    print("reclassify OK")

if __name__ == "__main__":
    main()
