"""修复版 HTML 脚本混淆工具 - 正确处理特殊字符"""
import re
import os
import sys
from pathlib import Path
from obfuscate_py import SimpleObfuscator

def extract_inline_scripts(html_content):
    """从 HTML 中提取所有 inline script 内容"""
    scripts = []
    pattern = re.compile(r'<script[^>]*>(.*?)</script>', re.DOTALL)
    for match in pattern.finditer(html_content):
        js = match.group(1).strip()
        if js and not re.match(r'^\s*<!--', js):
            scripts.append(js)
    return scripts

def obfuscate_js(js_code):
    """使用 Python 混淆器混淆 JS 代码"""
    try:
        obfuscator = SimpleObfuscator()
        return obfuscator.obfuscate(js_code)
    except Exception as e:
        print(f"Obfuscation error: {e}")
        return js_code

def obfuscate_html(html_content):
    """混淆 HTML 中的 inline script"""
    scripts = extract_inline_scripts(html_content)
    print(f"Found {len(scripts)} script(s) to obfuscate")

    for i, js in enumerate(scripts):
        print(f"Obfuscating script {i+1}/{len(scripts)}... (length: {len(js)})")

        # 使用更简单的方式：直接替换第一个匹配的 script 标签
        # 找到 script 标签的开始和结束位置
        script_start = html_content.find('<script>')
        script_end = html_content.find('</script>', script_start)

        if script_start != -1 and script_end != -1:
            # 提取完整的 script 标签
            script_tag_start = html_content.rfind('<', 0, script_start)
            script_tag = html_content[script_tag_start:script_end + 9]  # +9 for </script>

            # 混淆 JavaScript 代码
            obfuscated_js = obfuscate_js(js)

            # 替换完整的 script 标签
            new_script_tag = f'<script>{obfuscated_js}</script>'
            html_content = html_content.replace(script_tag, new_script_tag, 1)

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
        print("Usage: python html_obfuscate_fixed.py <input_html> <output_html>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    obfuscate_file(input_file, output_file)