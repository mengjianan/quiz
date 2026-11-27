# -*- coding: utf-8 -*-
"""把 math1_src/*.txt 的简写源转成 build_kp.py 读取的 s_math1.json。

格式：
  @ 分组名
  # 卡片标题（可含 $…$）
  【小节】
  正文行（可含 $…$ 行内公式与 $$…$$ 独立公式）
"""
import io
import json
import os
import sys


def parse_dir(d):
    groups = []
    g = c = None
    for name in sorted(os.listdir(d)):
        if not name.endswith(".txt"):
            continue
        with io.open(os.path.join(d, name), encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\r\n").strip()
                if not line:
                    continue
                if line.startswith("@ "):
                    g = {"name": line[2:].strip(), "cards": []}
                    groups.append(g)
                    c = None
                elif line.startswith("# "):
                    if g is None:
                        sys.exit("卡片出现在任何 @ 分组之前：" + line)
                    c = {"q": line[2:].strip(), "parts": []}
                    g["cards"].append(c)
                elif line.startswith("【"):
                    if c is None:
                        sys.exit("小节出现在任何 # 卡片之前：" + line)
                    c["parts"].append([line])
                else:
                    if c is None or not c["parts"]:
                        sys.exit("正文出现在任何 【小节】 之前：" + line)
                    c["parts"][-1].append(line)
    for g in groups:
        for c in g["cards"]:
            c["a"] = "\n".join("\n".join(p) for p in c["parts"])
            del c["parts"]
    return groups


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "tools/kp_author/math1_src"
    out = sys.argv[2] if len(sys.argv) > 2 else "tools/kp_author/s_math1.json"
    groups = parse_dir(src)
    data = {"name": "数学1", "order": 2, "min_body": 220, "groups": groups}
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("{\n\"name\": \"数学1\",\n\"order\": 2,\n\"min_body\": 220,\n\"groups\": ")
        f.write(json.dumps(groups, ensure_ascii=False, indent=1))
        f.write("\n}\n")
    ls = [len(c["a"]) for g in groups for c in g["cards"]]
    print("groups=%d cards=%d min=%d median=%d" % (
        len(groups), len(ls), min(ls), sorted(ls)[len(ls) // 2]))


if __name__ == "__main__":
    main()
