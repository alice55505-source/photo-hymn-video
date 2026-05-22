const CACHE = 'phv-v17';
const ASSETS = ['./manifest.json', './icon.svg', './mp4-muxer.js'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // 外部請求（GitHub API、CDN 等）直接走網路
  if (url.origin !== self.location.origin) return;

  // HTML：強制跳過 HTTP 快取，永遠向 server 驗證最新版
  const isHTML = e.request.destination === 'document' ||
                 url.pathname === '/' || url.pathname.endsWith('.html');
  if (isHTML) {
    e.respondWith(fetch(e.request, { cache: 'no-cache' }).catch(() => Response.error()));
    return;
  }

  // 靜態資源：Cache-First
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(res => {
      caches.open(CACHE).then(c => c.put(e.request, res.clone()));
      return res;
    }))
  );
});
