"""代码混淆模块：使用 javascript-obfuscator 混淆 JS 代码"""
from pathlib import Path
import re
import subprocess
import tempfile
import os

def extract_inline_scripts(html_content):
    """从 HTML 中提取所有 inline script 内容"""
    scripts = []
    pattern = re.compile(r'<script>(.*?)</script>', re.DOTALL)
    for match in pattern.finditer(html_content):
        js = match.group(1)
        scripts.append(js)
    return scripts

def obfuscate_js(js_code):
    """使用 javascript-obfuscator 混淆 JS 代码（通过 Node.js 调用）"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(js_code)
        js_file = f.name

    obfuscated_file = js_file + '.out'

    try:
        result = subprocess.run(
            ['node', 'tools/obfuscate.js', js_file, obfuscated_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if result.returncode == 0 and os.path.exists(obfuscated_file):
            with open(obfuscated_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"JavaScript obfuscation failed: {result.stderr}")
            return js_code
    finally:
        try:
            os.unlink(js_file)
            if os.path.exists(obfuscated_file):
                os.unlink(obfuscated_file)
        except:
            pass

def obfuscate_html(html_content):
    """混淆 HTML 中的 inline script"""
    scripts = extract_inline_scripts(html_content)
    for i, js in enumerate(scripts):
        obfuscated = obfuscate_js(js)
        html_content = html_content.replace(f'<script>{js}</script>', f'<script>{obfuscated}</script>')
    return html_content

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python obfuscate.py <html_file> <output_file>")
        sys.exit(1)

    html_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    obfuscated = obfuscate_html(content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(obfuscated)

    print(f"HTML obfuscated -> {output_file}")
