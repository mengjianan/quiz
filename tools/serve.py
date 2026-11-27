# -*- coding: utf-8 -*-
"""本地静态服务（带缓存头）：html/json/js 永远 no-cache，图片缓存 1 天
用法: cd 项目根 && python tools/serve.py [端口，默认8877]
根治：python -m http.server 不发 Cache-Control，浏览器按文件年龄启发式缓存导致更新不生效"""
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

class H(SimpleHTTPRequestHandler):
    def end_headers(self):
        p = self.path.split("?")[0]
        if p.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico")):
            self.send_header("Cache-Control", "public, max-age=86400")
        else:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *a):
        pass

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8877
print(f"serving on http://127.0.0.1:{port}/", flush=True)
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
