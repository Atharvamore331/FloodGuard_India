/* ============================================================
   FloodGuard India – Service Worker (PWA)
   ============================================================ */

const CACHE_NAME = 'floodguard-v1';

// Static assets to cache on install
const STATIC_ASSETS = [
  '/index.html',
  '/register.html',
  '/dashboard.html',
  '/styles/main.css',
  '/styles/auth.css',
  '/styles/dashboard.css',
  '/js/data.js',
  '/js/auth.js',
  '/js/gps.js',
  '/js/dashboard.js',
  '/js/map.js',
  '/js/weather.js',
  '/js/safety.js',
  '/js/alerts.js',
  '/js/lang.js',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png'
];

// ── Install: cache static files ──
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS.map(url => {
        return new Request(url, { cache: 'reload' });
      })).catch(err => {
        // Don't fail install if some assets are missing
        console.warn('[SW] Cache install partial:', err);
      });
    })
  );
  self.skipWaiting();
});

// ── Activate: clean up old caches ──
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch Strategy ──
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Network-first for API calls (Flask backend)
  if (url.pathname.startsWith('/api/') || url.port === '5000' || url.port === '8000') {
    event.respondWith(
      fetch(request)
        .catch(() => new Response(JSON.stringify({ error: 'offline' }), {
          headers: { 'Content-Type': 'application/json' }
        }))
    );
    return;
  }

  // Network-first for external CDN resources (Leaflet, Chart.js, Fonts)
  if (!url.origin.includes(location.origin)) {
    event.respondWith(
      fetch(request).catch(() => caches.match(request))
    );
    return;
  }

  // Cache-first for static assets
  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;
      return fetch(request).then(response => {
        // Cache successful GET responses
        if (response && response.status === 200 && request.method === 'GET') {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, responseClone));
        }
        return response;
      }).catch(() => {
        // Offline fallback: serve index.html for navigation requests
        if (request.mode === 'navigate') {
          return caches.match('/index.html');
        }
      });
    })
  );
});

// ── Push Notifications ──
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || '🌊 FloodGuard Alert';
  const options = {
    body: data.body || 'Flood risk update for your area.',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    tag: 'floodguard-alert',
    renotify: true,
    data: { url: data.url || '/dashboard.html' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

// ── Notification Click ──
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data && event.notification.data.url
    ? event.notification.data.url
    : '/dashboard.html';
  event.waitUntil(clients.openWindow(url));
});
