"""一键构建：从 src 生成 dist（数据 AES-GCM 加密 + 内联脚本语法自检）。

注意：绝不改写 src/。旧版这里会跑「正则混淆」并把结果写回 src/index.html，
曾产出 `const 5xYTPOSI` 这种非法标识符，导致整站白屏且可读源码被覆盖。
"""
import os
import subprocess
import sys

if __name__ == "__main__":
    sys.exit(subprocess.run([sys.executable, "tools/build.py"]).returncode)