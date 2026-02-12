/* Offline cache for Sentence Cards (scope: /english-cards/) */

const CACHE_NAME = "sentence-cards-pwa-v1";

const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./app.css",
  "./app.js",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      await cache.addAll(PRECACHE_URLS);
      await self.skipWaiting();
    })()
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)));
      await self.clients.claim();
    })()
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  event.respondWith(
    (async () => {
      const url = new URL(req.url);
      const sameOrigin = url.origin === self.location.origin;
      const isNav = req.mode === "navigate";

      // Navigation fallback to cached app shell.
      if (sameOrigin && isNav) {
        const cached = await caches.match("./index.html");
        if (cached) return cached;
      }

      // Cache-first for same-origin assets.
      if (sameOrigin) {
        const cached = await caches.match(req);
        if (cached) return cached;
        try {
          const res = await fetch(req);
          const cache = await caches.open(CACHE_NAME);
          cache.put(req, res.clone()).catch(() => {});
          return res;
        } catch {
          // Fall back to app shell if possible.
          const shell = await caches.match("./index.html");
          if (shell) return shell;
          throw new Error("offline");
        }
      }

      // Network-first for cross-origin (e.g., translation API).
      return fetch(req);
    })()
  );
});

