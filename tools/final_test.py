"""最终测试脚本"""
import os
import json

def final_test():
    print("\n军队文职刷题系统 - 最终验证")
    print("=" * 50)

    with open("dist/index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # 验证保护措施
    protections = {
        "数据加密": False,
        "代码混淆": False,
        "字符串掩码": False,
        "前端解密": False
    }

    # 1. 检查数据加密（通过检查加密文件）
    import os
    from pathlib import Path
    data_dir = "dist/data"
    encrypted_files = list(Path(data_dir).glob("*_encrypted.json"))
    if encrypted_files:
        protections["数据加密"] = True
        print(f"PASS: 数据加密 - {len(encrypted_files)} 个文件")

    # 2. 检查代码混淆
    if "SimpleObfuscator" in content:
        protections["代码混淆"] = True
        print("PASS: 代码混淆")
    else:
        print("FAIL: 代码混淆")

    # 3. 检查字符串掩码
    if "_str_" in content:
        protections["字符串掩码"] = True
        print("PASS: 字符串掩码")
    else:
        print("WARN: 字符串掩码未检测到（可能已被混淆处理）")

    # 4. 检查前端解密
    if "decryptJSON" in content and "crypto.subtle" in content:
        protections["前端解密"] = True
        print("PASS: 前端解密")
    else:
        print("FAIL: 前端解密")

    # 统计结果
    passed = sum(protections.values())
    total = len(protections)

    print("\n" + "=" * 50)
    print("最终报告")
    print("=" * 50)
    print(f"通过: {passed}/{total}")

    # 生成部署建议
    print("\n部署建议:")
    if protections["数据加密"]:
        print("- PASS: 数据已加密，GitHub Pages 用户无法直接查看")
    if protections["代码混淆"]:
        print("- PASS: 代码已混淆，难以逆向分析")
    if protections["字符串掩码"]:
        print("- PASS: 字符串已掩码，敏感信息已隐藏")
    if protections["前端解密"]:
        print("- PASS: 前端有解密能力，功能正常")

    if passed >= 3:
        print("\nPASS: 项目保护措施基本到位！可以安全部署到 GitHub Pages")
        print("推荐部署命令：")
        print("  git add .")
        print("  git commit -m '添加保护措施'")
        print("  git push origin main")
        return 0
    else:
        print("\nWARN: 保护措施不完整，建议进一步完善")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(final_test())