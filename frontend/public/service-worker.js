// Service Worker for ViralPilot
// Provides offline support, caching, and PWA capabilities

const CACHE_VERSION = 'v1';
const CACHE_NAME = `viralpilot-${CACHE_VERSION}`;

// Assets to cache immediately on install
const STATIC_CACHE = [
  '/',
  '/dashboard',
  '/dashboard/videos',
  '/offline',
];

// Cache strategies
const CACHE_FIRST = ['/_next/static/', '/static/', '/images/'];
const NETWORK_FIRST = ['/api/', '/dashboard/'];
const STALE_WHILE_REVALIDATE = ['/'];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_CACHE);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME)
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== self.location.origin) {
    return;
  }

  // Determine caching strategy
  if (shouldCacheFirst(url.pathname)) {
    event.respondWith(cacheFirst(request));
  } else if (shouldNetworkFirst(url.pathname)) {
    event.respondWith(networkFirst(request));
  } else {
    event.respondWith(staleWhileRevalidate(request));
  }
});

// Cache-first strategy (for static assets)
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.error('[SW] Cache-first fetch failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

// Network-first strategy (for API calls)
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return new Response(JSON.stringify({ error: 'Offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

// Stale-while-revalidate strategy (for pages)
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  });

  return cached || fetchPromise;
}

// Helper functions
function shouldCacheFirst(pathname) {
  return CACHE_FIRST.some((pattern) => pathname.includes(pattern));
}

function shouldNetworkFirst(pathname) {
  return NETWORK_FIRST.some((pattern) => pathname.includes(pattern));
}

// Background sync for failed requests
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-videos') {
    event.waitUntil(syncVideos());
  }
});

async function syncVideos() {
  console.log('[SW] Syncing videos in background');
  // Implement background sync logic here
}

// Push notifications
self.addEventListener('push', (event) => {
  const data = event.data?.json() || {};
  const title = data.title || 'ViralPilot';
  const options = {
    body: data.body || 'New notification',
    icon: '/icon-192.png',
    badge: '/badge-72.png',
    data: data.url,
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.notification.data) {
    event.waitUntil(clients.openWindow(event.notification.data));
  }
});
