"""字符串掩码工具 - 对敏感常量进行 Base64 编码"""
import re
import base64
import json
from pathlib import Path
import random
import string

class StringMasker:
    def __init__(self):
        self.string_map = {}
        self.reverse_map = {}
        self.mask_prefix = "_str_"
        self.mask_counter = 0

    def _generate_mask(self):
        """生成掩码字符串"""
        self.mask_counter += 1
        return f"{self.mask_prefix}{self.mask_counter}"

    def _encode_string(self, s):
        """编码字符串为 Base64"""
        return base64.b64encode(s.encode()).decode()

    def _decode_string(self, encoded):
        """解码 Base64 字符串"""
        return base64.b64decode(encoded).decode()

    def mask_constant(self, name, value):
        """掩码常量"""
        if value not in self.string_map:
            # 生成唯一掩码
            mask = self._generate_mask()
            encoded = self._encode_string(value)
            self.string_map[value] = {
                'name': name,
                'mask': mask,
                'encoded': encoded
            }
            self.reverse_map[mask] = value
        return self.string_map[value]['mask']

    def unmask_all(self):
        """生成解码函数"""
        decoder = f"""
// String decoder - auto-generated
window.decodeStrings = function() {{
    const encodedStrings = {json.dumps(self.string_map, indent=2)};
    for (const [key, value] of Object.entries(encodedStrings)) {{
        window[value.mask] = atob(value.encoded);
    }}
}};
        """
        return decoder

    def find_constants_in_js(self, js_code):
        """在 JavaScript 代码中查找常量"""
        # 查找 const/let/var 声明
        pattern = r'(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*["\']([^"\']*)["\'];'
        matches = re.findall(pattern, js_code)

        # 查查一些敏感模式
        sensitive_patterns = [
            r'LOGIN_PWD\s*=\s*["\']([^"\']*)["\']',
            r'password\s*=\s*["\']([^"\']*)["\']',
            r'token\s*=\s*["\']([^"\']*)["\']',
            r'api_key\s*=\s*["\']([^"\']*)["\']',
            r'secret\s*=\s*["\']([^"\']*)["\']',
            r'base_url\s*=\s*["\']([^"\']*)["\']'
        ]

        all_matches = []

        # 添加常规变量
        for name, value in matches:
            if len(value) > 3:  # 只处理有意义的字符串
                all_matches.append((name, value))

        # 添加敏感模式匹配
        for pattern in sensitive_patterns:
            pattern_matches = re.findall(pattern, js_code, re.IGNORECASE)
            for match in pattern_matches:
                # 从模式中提取变量名
                var_match = re.search(r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=', pattern)
                if var_match:
                    var_name = var_match.group(1)
                    all_matches.append((var_name, match))

        return list(set(all_matches))  # 去重

    def mask_js_code(self, js_code):
        """掩码 JavaScript 代码中的常量"""
        constants = self.find_constants_in_js(js_code)
        masked_code = js_code

        print(f"Found {len(constants)} constants to mask")

        for name, value in constants:
            mask = self.mask_constant(name, value)
            # 替换常量声明
            masked_code = re.sub(
                rf'(?:const|let|var)\s+{re.escape(name)}\s*=\s*["\']{re.escape(value)}["\'];',
                f'const {name} = "{mask}";',
                masked_code
            )

        # 添加解码函数
        decoder = self.unmask_all()
        masked_code += f"\n\n{decoder}\n\n// Initialize string decoding\nif(typeof window !== \"undefined\") {{ decodeStrings(); }}"

        return masked_code

def mask_html_file(input_file, output_file):
    """掩码 HTML 文件中的敏感字符串"""
    print(f"Reading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 JavaScript 部分
    import re
    script_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    if script_match:
        js_code = script_match.group(1)

        print("Masking constants in JavaScript...")
        masker = StringMasker()
        masked_js = masker.mask_js_code(js_code)

        # 替换回 HTML
        new_script = f'<script>{masked_js}</script>'
        content = content.replace(script_match.group(0), new_script)

        print(f"Masked {len(masker.string_map)} constants")

        # 保存映射文件（可选）
        map_file = output_file.replace('.html', '_string_map.json')
        with open(map_file, 'w', encoding='utf-8') as f:
            json.dump(masker.string_map, f, ensure_ascii=False, indent=2)
        print(f"String map saved to: {map_file}")

    print(f"Writing: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"String masking complete: {output_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python string_mask.py <input_html> <output_html>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    mask_html_file(input_file, output_file)