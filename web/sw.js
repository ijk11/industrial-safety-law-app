/* 산안법 조문 찾기 — 오프라인 캐시. 판이 바뀌면 CACHE 이름이 바뀌고 옛 캐시는 지워진다. */
const CACHE = "osh-ba8e989da604";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon-180.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./data/laws.json.gz",
  "./fonts/mono.woff2",
  "./fonts/serif-bold.woff2",
  "./splash/splash-375x667@2x-dark.png",
  "./splash/splash-375x667@2x-light.png",
  "./splash/splash-375x812@3x-dark.png",
  "./splash/splash-375x812@3x-light.png",
  "./splash/splash-390x844@3x-dark.png",
  "./splash/splash-390x844@3x-light.png",
  "./splash/splash-393x852@3x-dark.png",
  "./splash/splash-393x852@3x-light.png",
  "./splash/splash-402x874@3x-dark.png",
  "./splash/splash-402x874@3x-light.png",
  "./splash/splash-414x896@2x-dark.png",
  "./splash/splash-414x896@2x-light.png",
  "./splash/splash-414x896@3x-dark.png",
  "./splash/splash-414x896@3x-light.png",
  "./splash/splash-430x932@3x-dark.png",
  "./splash/splash-430x932@3x-light.png",
  "./splash/splash-440x956@3x-dark.png",
  "./splash/splash-440x956@3x-light.png"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* 「새 판으로 바꾸기」 를 눌렀을 때. 기다리지 않고 바로 이 판으로 넘어간다. */
self.addEventListener("message", e => {
  if (e.data && e.data.type === "skipWaiting") self.skipWaiting();
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(hit => hit || fetch(req).then(res => {
      if (res.ok && res.type === "basic") {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
      }
      return res;
    }).catch(() => caches.match("./index.html")))
  );
});
