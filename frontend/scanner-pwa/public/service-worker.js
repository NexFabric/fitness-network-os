/* Minimal shell cache for installability — no API caching. */
const CACHE = 'scanner-shell-v1'
const SHELL = ['/', '/index.html', '/manifest.json']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
    ).then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return
  // Network-first for navigations; cache fallback for shell only
  event.respondWith(
    fetch(request)
      .then((response) => {
        const copy = response.clone()
        if (response.ok && request.url.startsWith(self.location.origin)) {
          caches.open(CACHE).then((cache) => cache.put(request, copy))
        }
        return response
      })
      .catch(() => caches.match(request).then((r) => r || caches.match('/index.html'))),
  )
})
