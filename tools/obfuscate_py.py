"""Python JavaScript Obfuscator - 不依赖 Node.js 的纯 Python 实现"""
import re
import random
import base64
import hashlib
from pathlib import Path

class SimpleObfuscator:
    def __init__(self):
        self.variable_map = {}
        self.string_map = {}
        self.function_map = {}

    def _generate_random_name(self, length=8):
        """生成随机名称（首字符必须是字母，否则 const 5xYTPOSI 是非法 JS）"""
        first = random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return first + ''.join(random.choice(chars) for _ in range(length - 1))

    def _obfuscate_variable(self, match):
        """变量名混淆"""
        var_name = match.group(1)
        if var_name not in self.variable_map:
            # 保留一些重要的变量名
            if var_name in ['console', 'window', 'document', 'localStorage', 'JSON', 'Math']:
                return match.group(0)
            self.variable_map[var_name] = self._generate_random_name()
        return self.variable_map[var_name]

    def _obfuscate_string(self, match):
        """字符串混淆"""
        string = match.group(1)
        if string not in self.string_map:
            # Base64 编码
            encoded = base64.b64encode(string.encode()).decode()
            self.string_map[string] = f'atob("{encoded}")'
        return self.string_map[string]

    def _add_control_flow_flattening(self, code):
        """添加控制流扁平化"""
        # 简单的控制流混淆
        if_condition = re.search(r'if\s*\((.*?)\)\s*\{', code)
        if if_condition:
            condition = if_condition.group(1)
            flattened = f'''
            while(Math.random() > 0.5){{
                if({condition}){{
                    // main block
                    break;
                }}
                else{{
                    // else block
                }}
            }}
            '''
            code = re.sub(r'if\s*\(' + re.escape(condition) + r'\)\s*\{', flattened, code)
        return code

    def _add_dead_code(self, code):
        """添加死代码"""
        dead_codes = [
            'if(0){console.log("dead code");}',
            'while(false){}',
            'if(Math.random() > 1){}',
            'try{}catch(e){}'
        ]
        # 随机插入死代码
        for _ in range(random.randint(1, 3)):
            dead_code = random.choice(dead_codes)
            pos = random.randint(0, len(code))
            code = code[:pos] + dead_code + code[pos:]
        return code

    def obfuscate(self, js_code):
        """混淆 JavaScript 代码"""
        # 1. 变量名混淆
        # 匹配变量声明和使用
        var_pattern = r'\b(let|const|var|function)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)'
        code = re.sub(var_pattern, lambda m: f'{m.group(1)} {self._obfuscate_variable(m)}', js_code)

        # 2. 字符串混淆
        string_pattern = r'["\']([^"\'\\]*(\\.[^"\'\\]*)*)["\']'
        code = re.sub(string_pattern, lambda m: self._obfuscate_string(m), code)

        # 3. 控制流扁平化
        code = self._add_control_flow_flattening(code)

        # 4. 死代码注入
        code = self._add_dead_code(code)

        # 5. 添加混淆注释
        header = f"""
// Obfuscated by SimpleObfuscator v1.0
// Var count: {len(self.variable_map)}
// String count: {len(self.string_map)}
(function() {{
    """
        footer = "})();"

        return header + code + footer

def obfuscate_file(input_file, output_file):
    """混淆单个文件"""
    with open(input_file, 'r', encoding='utf-8') as f:
        js_code = f.read()

    obfuscator = SimpleObfuscator()
    obfuscated_code = obfuscator.obfuscate(js_code)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(obfuscated_code)

    print(f"Obfuscated: {input_file} -> {output_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python obfuscate_py.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    obfuscate_file(input_file, output_file)