// 刷题练习 Service Worker：安装资格 + 离线 + 图片缓存提速
const V = "sw-v1";
const CORE = ["./", "index.html", "manifest.json", "icon-192.png", "icon-512.png", "icon-mask-512.png"];

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

  // 页面导航：网络优先（保证更新触达），断网回退缓存
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req).then(resp => {
        const c = resp.clone();
        caches.open(V).then(ca => ca.put(req, c));
        return resp;
      }).catch(() => caches.match(req).then(r => r || caches.match("index.html")))
    );
    return;
  }

  // 图片（题图/图标）：缓存优先——治加载慢 + 二次秒开
  if (/\.(png|jpg|jpeg|webp|gif|svg)$/.test(url.pathname)) {
    e.respondWith(
      caches.match(req).then(r => r || fetch(req).then(resp => {
        const c = resp.clone();
        caches.open(V).then(ca => ca.put(req, c));
        return resp;
      }))
    );
    return;
  }

  // html/js/json：网络优先，回退缓存（离线可用）
  e.respondWith(
    fetch(req).then(resp => {
      const c = resp.clone();
      caches.open(V).then(ca => ca.put(req, c));
      return resp;
    }).catch(() => caches.match(req))
  );
});
