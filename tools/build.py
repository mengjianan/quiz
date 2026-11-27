import os
import json
import base64
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

# ============ AES-GCM 加密/解密模块 ============

SECRET_KEY = "examquiz-build-secret-key-2026"

def generate_key():
    """生成 256-bit AES-GCM 密钥"""
    return hashlib.sha256(SECRET_KEY.encode()).digest()

def encrypt_dict(data_dict):
    """使用 AES-GCM 加密 JSON 数据"""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = generate_key()
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    plaintext = json.dumps(data_dict, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    ciphertext = aesgcm.encrypt(iv, plaintext, None)

    return {
        "iv": base64.b64encode(iv).decode('utf-8'),
        "data": base64.b64encode(ciphertext).decode('utf-8')
    }

def decrypt_dict(encrypted_dict):
    """使用 AES-GCM 解密 JSON 数据"""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = generate_key()
    aesgcm = AESGCM(key)
    iv = base64.b64decode(encrypted_dict["iv"])
    ciphertext = base64.b64decode(encrypted_dict["data"])
    plaintext = aesgcm.decrypt(iv, ciphertext, None)
    return json.loads(plaintext.decode('utf-8'))

def encrypt_all_json(src_dir, dist_dir):
    """加密 src/data/ 下所有 JSON 文件到 dist/data/ 下（添加 _encrypted.json）"""
    src_data = Path(src_dir) / "data"
    dist_data = Path(dist_dir) / "data"

    if not src_data.exists():
        print(f"Error: {src_data} not found")
        return

    dist_data.mkdir(parents=True, exist_ok=True)

    for json_file in src_data.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        encrypted = encrypt_dict(data)
        encrypted_name = json_file.name.replace('.json', '_encrypted.json')
        encrypted_path = dist_data / encrypted_name
        with open(encrypted_path, 'w', encoding='utf-8') as f:
            json.dump(encrypted, f, ensure_ascii=False, separators=(',', ':'))
        print(f"Encrypted: {json_file.name} -> {encrypted_name}")

    # 复制原始文件（用于兼容性，或删除——这里保留原始文件以便开发调试）
    for json_file in src_data.glob("*.json"):
        shutil.copy2(json_file, dist_data / json_file.name)

def build():
    print(">> Starting build process...")

    src_dir = "src"
    dist_dir = "dist"

    if os.path.exists(dist_dir):
        print(f"Cleaning {dist_dir}...")
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)

    if not os.path.exists(src_dir):
        print(f"Error: Source directory '{src_dir}' not found!")
        sys.exit(1)

    print(f"Syncing {src_dir} -> {dist_dir}...")
    try:
        shutil.copytree(src_dir, dist_dir, dirs_exist_ok=True)
        print("Sync complete.")
    except Exception as e:
        print(f"Error during sync: {e}")
        sys.exit(1)

    # Encrypt all JSON files
    print("Encrypting JSON data files...")
    encrypt_all_json(src_dir, dist_dir)

    # 内联脚本语法自检：正则混淆器曾产出 `const 5xYTPOSI` 这类非法标识符，
    # 整个脚本解析失败 → 页面白屏。构建时必须拦住。
    import re, tempfile
    dist_index = os.path.join(dist_dir, "index.html")
    html = open(dist_index, encoding="utf-8").read()
    js = "\n;\n".join(re.findall(r"<script(?![^>]*src=)[^>]*>(.*?)</script>", html, re.S))
    fd, tmp = tempfile.mkstemp(suffix=".js")
    os.close(fd)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(js)
    try:
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    except FileNotFoundError:
        print("WARN: node not found, skipping syntax check")
        r = None
    finally:
        os.remove(tmp)
    if r is not None and r.returncode != 0:
        print("FAIL: dist/index.html inline script syntax error:")
        print(r.stderr[:800])
        sys.exit(1)

    print("Build finished successfully!")

if __name__ == "__main__":
    build()
