// 最小 Service Worker：讓 Chrome 允許 PWA 安裝
// 不做任何快取，所有請求直接走網路
self.addEventListener('fetch', event => {});
