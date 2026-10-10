<<<<<<< HEAD
// Version bumped to force browsers to discard the stale English-first shell.
const CACHE_NAME = "panjika-v4-day-search";
const SHELL = ["/", "/manifest.json"];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key.startsWith("panjika-") && key !== CACHE_NAME).map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
    return;
  }
  // Network-first for the app shell so frontend fixes show up immediately.
  event.respondWith((async () => {
    try {
      const response = await fetch(event.request, { cache: "no-cache" });
      if (response.ok && (url.pathname === "/" || url.pathname === "/manifest.json")) {
        const cache = await caches.open(CACHE_NAME);
        cache.put(event.request, response.clone());
      }
      return response;
    } catch (error) {
      return (await caches.match(event.request)) || Response.error();
    }
  })());
=======
const CACHE_NAME = "panjika-v1";
const SHELL = ["/", "/manifest.json"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL))
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.url.includes("/api/")) {
    // Network-first for API calls (data should be fresh)
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  } else {
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
  }
>>>>>>> origin/main
});
