self.addEventListener("install", function(e) {
  e.waitUntil(
    caches.open("move-up-metro").then(function(cache) {
      return cache.addAll([
        "/",
        "/static/board.svg",
        "/static/card_decks.json",
        "/static/manifest.json",
        "/static/service-worker.js"
      ]);
    })
  );
});

self.addEventListener("fetch", function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});