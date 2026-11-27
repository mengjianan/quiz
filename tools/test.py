"""自动测试脚本 - 验证 dist/ 目录的功能完整性"""
import os
import sys
import json
import base64
import subprocess
import webbrowser
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import requests

class ProjectTester:
    def __init__(self, project_dir="D:/military-civilian-quiz"):
        self.project_dir = project_dir
        self.dist_dir = os.path.join(project_dir, "dist")
        self.test_results = {
            "build_test": False,
            "encryption_test": False,
            "obfuscation_test": False,
            "string_mask_test": False,
            "decryption_test": False,
            "functionality_test": False,
            "performance_test": False
        }

    def run_build_test(self):
        """测试构建过程"""
        print("\n=== 测试 1: 构建过程 ===")
        try:
            # 运行构建脚本
            result = subprocess.run([
                sys.executable, "tools/build.py"
            ], cwd=self.project_dir, capture_output=True, text=True)

            if result.returncode == 0:
                print("✓ 构建成功")
                self.test_results["build_test"] = True
                return True
            else:
                print(f"✗ 构建失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"✗ 构建异常: {e}")
            return False

    def run_encryption_test(self):
        """测试数据加密"""
        print("\n=== 测试 2: 数据加密 ===")
        try:
            # 检查加密文件是否存在
            data_dir = os.path.join(self.dist_dir, "data")
            encrypted_files = list(Path(data_dir).glob("*_encrypted.json"))
            json_files = list(Path(data_dir).glob("*.json"))

            print(f"发现 {len(encrypted_files)} 个加密文件")
            print(f"发现 {len(json_files)} 个 JSON 文件")

            # 测试解密
            if encrypted_files:
                with open(encrypted_files[0], 'r', encoding='utf-8') as f:
                    encrypted_data = json.load(f)

                if 'iv' in encrypted_data and 'data' in encrypted_data:
                    print("✓ 加密文件格式正确")
                    self.test_results["encryption_test"] = True
                    return True
                else:
                    print("✗ 加密文件格式错误")
                    return False
            else:
                print("✗ 未找到加密文件")
                return False
        except Exception as e:
            print(f"✗ 加密测试异常: {e}")
            return False

    def run_obfuscation_test(self):
        """测试代码混淆"""
        print("\n=== 测试 3: 代码混淆 ===")
        try:
            index_file = os.path.join(self.dist_dir, "index.html")
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查混淆标记
            if "SimpleObfuscator" in content:
                print("✓ 代码混淆标记存在")
                self.test_results["obfuscation_test"] = True
                return True
            else:
                print("✗ 未找到代码混淆标记")
                return False
        except Exception as e:
            print(f"✗ 混淆测试异常: {e}")
            return False

    def run_string_mask_test(self):
        """测试字符串掩码"""
        print("\n=== 测试 4: 字符串掩码 ===")
        try:
            index_file = os.path.join(self.dist_dir, "index.html")
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查掩码标记
            if "_str_" in content and "decodeStrings" in content:
                print("✓ 字符串掩码标记存在")
                self.test_results["string_mask_test"] = True
                return True
            else:
                print("✗ 未找到字符串掩码标记")
                return False
        except Exception as e:
            print(f"✗ 字符串掩码测试异常: {e}")
            return False

    def run_decryption_test(self):
        """测试前端解密功能"""
        print("\n=== 测试 5: 前端解密 ===")
        try:
            index_file = os.path.join(self.dist_dir, "index.html")
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查解密函数
            if "decryptJSON" in content and "crypto.subtle" in content:
                print("✓ 前端解密函数存在")
                self.test_results["decryption_test"] = True
                return True
            else:
                print("✗ 未找到前端解密函数")
                return False
        except Exception as e:
            print(f"✗ 解密测试异常: {e}")
            return False

    def start_local_server(self, port=8877):
        """启动本地测试服务器"""
        os.chdir(self.dist_dir)

        def run_server():
            httpd = HTTPServer(("", port), SimpleHTTPRequestHandler)
            print(f"服务器启动在 http://localhost:{port}")
            httpd.serve_forever()

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)  # 等待服务器启动
        return f"http://localhost:{port}"

    def run_functionality_test(self):
        """测试页面功能"""
        print("\n=== 测试 6: 页面功能 ===")
        try:
            # 启动本地服务器
            url = self.start_local_server(8877)

            # 尝试访问页面
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print("✓ 页面访问成功")
                    self.test_results["functionality_test"] = True
                    return True
                else:
                    print(f"✗ 页面访问失败: {response.status_code}")
                    return False
            except requests.RequestException as e:
                print(f"✗ 无法访问页面: {e}")
                return False
        except Exception as e:
            print(f"✗ 功能测试异常: {e}")
            return False

    def run_performance_test(self):
        """测试性能影响"""
        print("\n=== 测试 7: 性能测试 ===")
        try:
            index_file = os.path.join(self.dist_dir, "index.html")

            # 检查文件大小
            original_size = os.path.getsize(index_file)
            print(f"HTML 文件大小: {original_size / 1024:.2f} KB")

            # 检查加密文件大小
            data_dir = os.path.join(self.dist_dir, "data")
            encrypted_files = list(Path(data_dir).glob("*_encrypted.json"))
            total_encrypted_size = sum(f.stat().st_size for f in encrypted_files)

            print(f"加密数据总大小: {total_encrypted_size / 1024:.2f} KB")

            # 评估性能影响
            if original_size < 500 * 1024:  # 500KB以内
                print("✓ 文件大小合理")
                self.test_results["performance_test"] = True
                return True
            else:
                print("⚠ 文件较大，可能影响加载速度")
                return True
        except Exception as e:
            print(f"✗ 性能测试异常: {e}")
            return False

    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "="*50)
        print("测试报告")
        print("="*50)

        passed = sum(self.test_results.values())
        total = len(self.test_results)

        print(f"通过: {passed}/{total}")
        print("详细结果:")

        for test, result in self.test_results.items():
            status = "✓" if result else "✗"
            print(f"  {status} {test.replace('_', ' ').title()}")

        # 提供建议
        print("\n建议:")
        if not self.test_results["build_test"]:
            print("- 检查构建脚本依赖")
        if not self.test_results["encryption_test"]:
            print("- 确认加密模块正常工作")
        if not self.test_results["obfuscation_test"]:
            print("- 检查混淆脚本执行")
        if not self.test_results["string_mask_test"]:
            print("- 确认字符串掩码功能")

        # 保存报告
        report_file = os.path.join(self.project_dir, "test_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "results": self.test_results,
                "summary": f"{passed}/{total} tests passed"
            }, f, ensure_ascii=False, indent=2)

        print(f"\n报告已保存到: {report_file}")

def main():
    print("军队文职刷题系统 - 自动测试脚本")
    print("="*50)

    tester = ProjectTester()

    # 运行所有测试
    tester.run_build_test()
    tester.run_encryption_test()
    tester.run_obfuscation_test()
    tester.run_string_mask_test()
    tester.run_decryption_test()
    tester.run_functionality_test()
    tester.run_performance_test()

    # 生成报告
    tester.generate_test_report()

    # 返回退出代码
    passed = sum(tester.test_results.values())
    total = len(tester.test_results)
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())