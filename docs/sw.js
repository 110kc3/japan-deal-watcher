// Service Worker for AgyDeal Japan Auction & Deal Radar PWA
const CACHE_NAME = 'agydeal-v2.3.0';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './style.css',
  './style.css?v=2.3.0',
  './app.js',
  './app.js?v=2.3.0',
  './manifest.json',
  './icons/icon-192.svg',
  './icons/icon-512.svg'
  // Pre-caching skips deals.json to guarantee 100% fresh auction & deal data
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Pre-caching static assets (v2.3.0, skipping deals.json)');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[SW] Clearing old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Immediate skip waiting on message
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Network-first with cache: 'no-store' for live deals, Stale-While-Revalidate for static assets
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // For data/deals.json, NEVER serve stale data: network-first with cache: 'no-store'
  if (url.pathname.endsWith('deals.json')) {
    event.respondWith(
      fetch(new Request(event.request.url, {
        method: event.request.method,
        headers: event.request.headers,
        cache: 'no-store'
      }))
        .then((response) => {
          if (response && response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // For static assets: Stale-While-Revalidate
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse.clone()));
          }
          return networkResponse;
        })
        .catch(() => {
          // Offline fallback
          return cachedResponse;
        });

      return cachedResponse || fetchPromise;
    })
  );
});
