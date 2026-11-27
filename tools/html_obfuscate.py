"""HTML 脚本混淆工具 - 使用 Python 实现的纯 JavaScript 混淆"""
import re
import os
import sys
from pathlib import Path
import shutil
from obfuscate_py import SimpleObfuscator

def extract_inline_scripts(html_content):
    """从 HTML 中提取所有 inline script 内容"""
    scripts = []
    # 匹配 <script>...</script> 标签
    pattern = re.compile(r'<script[^>]*>(.*?)</script>', re.DOTALL)
    for match in pattern.finditer(html_content):
        js = match.group(1).strip()
        if js:  # 忽略空脚本
            scripts.append(js)
    return scripts

def obfuscate_js(js_code):
    """使用 Python 混淆器混淆 JS 代码"""
    obfuscator = SimpleObfuscator()
    return obfuscator.obfuscate(js_code)

def obfuscate_html(html_content):
    """混淆 HTML 中的 inline script"""
    scripts = extract_inline_scripts(html_content)
    obfuscated_scripts = []

    for i, js in enumerate(scripts):
        print(f"Obfuscating script {i+1}/{len(scripts)}...")
        obfuscated = obfuscate_js(js)
        obfuscated_scripts.append(obfuscated)

        # 替换原始脚本
        html_content = html_content.replace(
            f'<script>{js}</script>',
            f'<script>{obfuscated}</script>',
            1  # 只替换第一个匹配
        )

    return html_content

def obfuscate_file(input_file, output_file):
    """混淆 HTML 文件"""
    print(f"Reading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("Obfuscating inline scripts...")
    obfuscated = obfuscate_html(content)

    print(f"Writing: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(obfuscated)

    print(f"Obfuscation complete: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python html_obfuscate.py <input_html> <output_html>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    obfuscate_file(input_file, output_file)