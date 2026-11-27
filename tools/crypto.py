"""数据加密模块：AES-GCM 加密/解密"""
import os
import json
import base64
import hashlib
from pathlib import Path

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

def encrypt_file(file_path, output_path=None):
    """加密单个 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    encrypted = encrypt_dict(data)
    out_path = output_path or str(Path(file_path).with_name(Path(file_path).name.replace('.json', '_encrypted.json')))

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(encrypted, f, ensure_ascii=False, separators=(',', ':'))

    return out_path

def decrypt_file(file_path):
    """解密单个 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        encrypted = json.load(f)

    return decrypt_dict(encrypted)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python crypto.py <encrypt|decrypt> <file_path>")
        sys.exit(1)

    action = sys.argv[1]
    file_path = sys.argv[2]

    if action == "encrypt":
        out = encrypt_file(file_path)
        print(f"Encrypted -> {out}")
    elif action == "decrypt":
        data = decrypt_file(file_path)
        print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
