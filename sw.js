// 讓 Chrome 允許 PWA 安裝（不做任何快取）
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(clients.claim()));
self.addEventListener('fetch', () => {});
