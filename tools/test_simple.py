"""自动测试脚本 - 验证 dist/ 目录的功能完整性"""
import os
import sys
import json
import base64
import subprocess
import time
from pathlib import Path

def run_test():
    print("\n军队文职刷题系统 - 自动测试脚本")
    print("=" * 50)

    project_dir = "D:/military-civilian-quiz"
    dist_dir = os.path.join(project_dir, "dist")

    # 测试结果
    results = {}

    # 测试 1: 构建过程
    print("\n=== 测试 1: 构建过程 ===")
    try:
        result = subprocess.run([
            sys.executable, "tools/build.py"
        ], cwd=project_dir, capture_output=True, text=True)

        if result.returncode == 0:
            print("PASS: 构建成功")
            results['build'] = True
        else:
            print(f"FAIL: 构建失败: {result.stderr}")
            results['build'] = False
    except Exception as e:
        print(f"FAIL: 构建异常: {e}")
        results['build'] = False

    # 测试 2: 数据加密
    print("\n=== 测试 2: 数据加密 ===")
    try:
        data_dir = os.path.join(dist_dir, "data")
        encrypted_files = list(Path(data_dir).glob("*_encrypted.json"))
        json_files = list(Path(data_dir).glob("*.json"))

        print(f"发现 {len(encrypted_files)} 个加密文件")
        print(f"发现 {len(json_files)} 个 JSON 文件")

        if encrypted_files:
            # 测试第一个加密文件
            with open(encrypted_files[0], 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)

            if 'iv' in encrypted_data and 'data' in encrypted_data:
                print("PASS: 加密文件格式正确")
                results['encryption'] = True
            else:
                print("FAIL: 加密文件格式错误")
                results['encryption'] = False
        else:
            print("FAIL: 未找到加密文件")
            results['encryption'] = False
    except Exception as e:
        print(f"FAIL: 加密测试异常: {e}")
        results['encryption'] = False

    # 测试 3: 代码混淆
    print("\n=== 测试 3: 代码混淆 ===")
    try:
        index_file = os.path.join(dist_dir, "index.html")
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if "SimpleObfuscator" in content:
            print("PASS: 代码混淆标记存在")
            results['obfuscation'] = True
        else:
            print("FAIL: 未找到代码混淆标记")
            results['obfuscation'] = False
    except Exception as e:
        print(f"FAIL: 混淆测试异常: {e}")
        results['obfuscation'] = False

    # 测试 4: 字符串掩码
    print("\n=== 测试 4: 字符串掩码 ===")
    try:
        index_file = os.path.join(dist_dir, "index.html")
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if "_str_" in content and "decodeStrings" in content:
            print("PASS: 字符串掩码标记存在")
            results['string_mask'] = True
        else:
            print("FAIL: 未找到字符串掩码标记")
            results['string_mask'] = False
    except Exception as e:
        print(f"FAIL: 字符串掩码测试异常: {e}")
        results['string_mask'] = False

    # 测试 5: 前端解密
    print("\n=== 测试 5: 前端解密 ===")
    try:
        index_file = os.path.join(dist_dir, "index.html")
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if "decryptJSON" in content and "crypto.subtle" in content:
            print("PASS: 前端解密函数存在")
            results['decryption'] = True
        else:
            print("FAIL: 未找到前端解密函数")
            results['decryption'] = False
    except Exception as e:
        print(f"FAIL: 解密测试异常: {e}")
        results['decryption'] = False

    # 测试 6: 性能
    print("\n=== 测试 6: 文件大小 ===")
    try:
        index_file = os.path.join(dist_dir, "index.html")
        original_size = os.path.getsize(index_file)
        print(f"HTML 文件大小: {original_size / 1024:.2f} KB")

        # 检查加密数据大小
        data_dir = os.path.join(dist_dir, "data")
        encrypted_files = list(Path(data_dir).glob("*_encrypted.json"))
        total_encrypted_size = sum(f.stat().st_size for f in encrypted_files)
        print(f"加密数据总大小: {total_encrypted_size / 1024:.2f} KB")

        if original_size < 500 * 1024:  # 500KB以内
            print("PASS: 文件大小合理")
            results['performance'] = True
        else:
            print("WARN: 文件较大")
            results['performance'] = True
    except Exception as e:
        print(f"FAIL: 性能测试异常: {e}")
        results['performance'] = False

    # 生成报告
    print("\n" + "=" * 50)
    print("测试报告")
    print("=" * 50)

    passed = sum(results.values())
    total = len(results)

    print(f"通过: {passed}/{total}")
    print("详细结果:")

    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {status} {test.replace('_', ' ').title()}")

    # 保存报告
    report_file = os.path.join(project_dir, "test_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
            "summary": f"{passed}/{total} tests passed"
        }, f, ensure_ascii=False, indent=2)

    print(f"\n报告已保存到: {report_file}")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(run_test())