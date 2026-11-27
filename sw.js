// hamster Service Worker：安装资格 + 离线 + 图片缓存提速
const V = "sw-v8";
const CORE = ["./", "index.html", "manifest.json", "icon-hamster.svg",
  "vendor/katex/katex.min.js", "vendor/katex/katex.min.css"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // 页面导航：网络优先 + no-store 绕过 HTTP 启发式缓存（否则更新要等缓存过期才可见），断网回退缓存
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req, { cache: "no-store" }).then(resp => {
        const c = resp.clone();
        caches.open(V).then(ca => ca.put(req, c));
        return resp;
      }).catch(() => caches.match(req).then(r => r || caches.match("index.html")))
    );
    return;
  }

  // 图片（题图/图标）：缓存优先——治加载慢 + 二次秒开
  if (/\.(png|jpg|jpeg|webp|gif|svg)$/.test(url.pathname) || /\.woff2$/.test(url.pathname)) {
    e.respondWith(
      caches.match(req).then(r => r || fetch(req).then(resp => {
        const c = resp.clone();
        caches.open(V).then(ca => ca.put(req, c));
        return resp;
      }))
    );
    return;
  }

  // KaTeX 资源：版本固定，缓存优先
  if (url.pathname.includes("/vendor/katex/")) {
    e.respondWith(
      caches.match(req).then(r => r || fetch(req).then(resp => {
        const c = resp.clone();
        caches.open(V).then(ca => ca.put(req, c));
        return resp;
      }))
    );
    return;
  }

  // html/js/json：网络优先 + no-store（杜绝旧版 index/题库滞留），回退缓存（离线可用）
  e.respondWith(
    fetch(req, { cache: "no-store" }).then(resp => {
      const c = resp.clone();
      caches.open(V).then(ca => ca.put(req, c));
      return resp;
    }).catch(() => caches.match(req))
  );
});
