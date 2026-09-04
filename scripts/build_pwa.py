# -*- coding: utf-8 -*-
"""아이폰 홈 화면에 설치해 쓰는 PWA를 굽는다.

    python scripts/build_pwa.py

web/ 폴더를 통째로 GitHub Pages에 올리면 끝. 첫 실행 때 원문·글꼴을 통째로
캐시에 넣으므로, 그 뒤로는 비행기모드에서도 열린다. 실행 중 바깥 통신은 없다.
"""
import hashlib, io, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_app as B  # noqa: E402

APP_NAME = "산안법 조문 찾기"
SHORT_NAME = "산안법"
DESC = ("산업안전보건법·시행령·시행규칙·안전보건기준규칙과 중대재해처벌법, "
        "고용노동부 고시·근로감독관 집무규정 원문을 오프라인에서 찾습니다.")

HEAD_EXTRA = """<meta name="description" content="{desc}">
<meta name="robots" content="noindex, nofollow">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="{short}">
<meta name="theme-color" content="#f7f8f6" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0f1412" media="(prefers-color-scheme: dark)">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/icon-180.png">
<link rel="icon" href="icons/icon-192.png">
{splash}
<style>
@font-face{{font-family:"OSH Mono";src:url("fonts/mono.woff2") format("woff2");
  font-weight:400;font-style:normal;font-display:swap}}
@font-face{{font-family:"OSH Serif";src:url("fonts/serif-bold.woff2") format("woff2");
  font-weight:600 700;font-style:normal;font-display:swap}}
:root{{
  --font-ui:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif;
  --font-serif:"OSH Serif","Apple SD Gothic Neo",serif;
  --font-mono:"OSH Mono",monospace;
}}
</style>""" 

# 서버가 .gz에 Content-Encoding을 붙여 이미 풀어 주는 경우도 있어, 앞 두 바이트로 가려낸다
DATA_LOADER = """async function loadLawText() {
  if (location.protocol === "file:")
    throw new Error("이 폴더는 웹 주소로 열어야 합니다. 브라우저가 file:// 에서는 옆 파일 읽기를 막습니다. " +
      "PC에서 그냥 확인하려면 dist 폴더의 단일 파일(산안법-조문찾기.html)을 여세요.");
  const res = await fetch("data/laws.json.gz");
  if (!res.ok) throw new Error("법령 파일을 받지 못했습니다 (" + res.status + ")");
  const buf = new Uint8Array(await res.arrayBuffer());
  if (buf[0] === 0x1f && buf[1] === 0x8b) return await gunzip(buf);
  return new TextDecoder().decode(buf);
}"""

TAIL_EXTRA = """<style>
.install{position:fixed;left:10px;right:10px;z-index:65;
  bottom:calc(66px + env(safe-area-inset-bottom));
  display:flex;align-items:center;gap:10px;
  background:var(--surface);border:1px solid var(--line-2);border-radius:13px;
  padding:11px 12px;box-shadow:var(--shadow);max-width:740px;margin:0 auto}
.install p{margin:0;flex:1;font-size:12.5px;line-height:1.5;color:var(--ink-2)}
.install b{color:var(--ink)}
.install button{width:32px;height:32px;flex:none;border-radius:9px;color:var(--ink-3);
  display:grid;place-items:center;font-size:17px;line-height:1}
</style>
<script>
/* 아이폰 사파리는 설치 안내를 스스로 띄우지 않는다. 한 번만 알려 준다. */
(() => {
  const standalone = matchMedia("(display-mode: standalone)").matches || navigator.standalone;
  const iOS = /iPhone|iPad|iPod/.test(navigator.userAgent);
  let hidden = false;
  try { hidden = localStorage.getItem("osh:installhint") === "1"; } catch (e) {}
  if (standalone || !iOS || hidden) return;
  addEventListener("load", () => {
    const bar = document.createElement("div");
    bar.className = "install";
    bar.innerHTML = '<p>공유 <b>&#x2191;</b> 버튼을 누르고 <b>홈 화면에 추가</b>를 고르면, ' +
      '앱처럼 전체화면으로 열리고 인터넷 없이도 씁니다.</p>' +
      '<button type="button" aria-label="닫기">&times;</button>';
    bar.querySelector("button").onclick = () => {
      bar.remove();
      try { localStorage.setItem("osh:installhint", "1"); } catch (e) {}
    };
    document.body.appendChild(bar);
  });
})();
</script>
<script>
if ("serviceWorker" in navigator) {
  addEventListener("load", () => {
    /* 새 판을 받아 두었다는 알림은 앱 쪽 watchUpdate() 가 팝업으로 맡는다.
       잠깐 뜨는 토스트로만 알리면 놓쳐, 새 판을 두고도 옛 판을 계속 쓰게 된다. */
    navigator.serviceWorker.register("sw.js").catch(() => {});
  });
}
</script>"""

SW = """/* {name} — 오프라인 캐시. 판이 바뀌면 CACHE 이름이 바뀌고 옛 캐시는 지워진다. */
const CACHE = "osh-{version}";
const ASSETS = {assets};

self.addEventListener("install", e => {{
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
}});

self.addEventListener("activate", e => {{
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
}});

/* 「새 판으로 바꾸기」 를 눌렀을 때. 기다리지 않고 바로 이 판으로 넘어간다. */
self.addEventListener("message", e => {{
  if (e.data && e.data.type === "skipWaiting") self.skipWaiting();
}});

self.addEventListener("fetch", e => {{
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    caches.match(req, {{ ignoreSearch: true }}).then(hit => hit || fetch(req).then(res => {{
      if (res.ok && res.type === "basic") {{
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
      }}
      return res;
    }}).catch(() => caches.match("./index.html")))
  );
}});
"""

MANIFEST = {
    "name": APP_NAME,
    "short_name": SHORT_NAME,
    "description": DESC,
    "lang": "ko",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#f7f8f6",
    "theme_color": "#0e6b45",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}


def render_page(head_extra, payload, loader, tail):
    """템플릿을 <head>/<body>로 갈라 온전한 HTML 문서로 조립한다."""
    with io.open(os.path.join(ROOT, "scripts", "app_template.html"), encoding="utf-8") as f:
        tpl = f.read()
    cut = tpl.index("</style>") + len("</style>")
    head, body = tpl[:cut], tpl[cut:]
    doc = ("<!doctype html>\n<html lang=\"ko\">\n<head>\n<meta charset=\"utf-8\">\n"
           + head + "\n</head>\n<body>" + body + "\n</body>\n</html>\n")
    for mark, value in (("__HEAD_EXTRA__", head_extra), ("__PAYLOAD__", payload),
                        ("__DATA_LOADER__", loader), ("__TAIL_EXTRA__", tail)):
        assert mark in doc, "템플릿에 %s 자리가 없습니다" % mark
        doc = doc.replace(mark, value)
    return doc


def splash_links():
    """기기 크기마다 맞는 실행 화면을 걸어 준다 (build_splash.py 가 만든 것만)."""
    import build_splash
    tags = []
    for w, h, scale in build_splash.DEVICES:
        for theme in build_splash.THEMES:
            name = "splash-%dx%d@%dx-%s.png" % (w, h, scale, theme)
            if not os.path.exists(os.path.join(WEB, "splash", name)):
                continue
            media = ("(device-width: %dpx) and (device-height: %dpx) and "
                     "(-webkit-device-pixel-ratio: %d) and (orientation: portrait)" % (w, h, scale))
            if theme == "dark":
                media += " and (prefers-color-scheme: dark)"
            tags.append('<link rel="apple-touch-startup-image" media="%s" href="splash/%s">' % (media, name))
    return "\n".join(tags)


def asset_list():
    """web/ 안에 실제로 있는 파일을 훑어 캐시 목록을 만든다. 빠뜨릴 일이 없다.

    os.walk 이 폴더를 돌려주는 차례는 파일시스템에 달렸다 — 내 컴퓨터와 CI 가
    다른 차례로 적으면 sw.js 가 달라져, 같은 원문인데도 판이 갈린 것처럼 보인다.
    이름순으로 못 박는다.
    """
    skip = {"sw.js", "index.html", "robots.txt", ".nojekyll"}
    rest = []
    for base, _, files in os.walk(WEB):
        for fn in files:
            rel = os.path.relpath(os.path.join(base, fn), WEB).replace(os.sep, "/")
            if rel in skip or rel.startswith("__"):
                continue
            rest.append("./" + rel)
    return ["./", "./index.html"] + sorted(rest)


def main():
    docs = B.slim(B.collect())
    raw = json.dumps(docs, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    # 시각도 OS도 박지 않고 굽는다 (build_app.bake_gz 참고). 그것이 박히면 원문이
    # 그대로여도 아래 version(sha256)이 바뀌어, 폰이 1.6MB를 공연히 다시 받는다.
    gz = B.bake_gz(raw)

    os.makedirs(os.path.join(WEB, "data"), exist_ok=True)
    with open(os.path.join(WEB, "data", "laws.json.gz"), "wb") as f:
        f.write(gz)

    head = HEAD_EXTRA.format(desc=DESC, short=SHORT_NAME, splash=splash_links())
    page = render_page(head, "", DATA_LOADER, TAIL_EXTRA)
    version = hashlib.sha256(gz + page.encode("utf-8")).hexdigest()[:12]

    with io.open(os.path.join(WEB, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    with io.open(os.path.join(WEB, "sw.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write(SW.format(name=APP_NAME, version=version,
                          assets=json.dumps(asset_list(), ensure_ascii=False, indent=2)))
    with io.open(os.path.join(WEB, "manifest.webmanifest"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(MANIFEST, f, ensure_ascii=False, indent=2)
    open(os.path.join(WEB, ".nojekyll"), "w").close()
    # 검색엔진에 걸리지 않게 한다 (주소를 아는 사람만 쓰는 앱)
    with io.open(os.path.join(WEB, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("User-agent: *\nDisallow: /\n")

    missing = [p for p in ("fonts/mono.woff2", "fonts/serif-bold.woff2", "icons/icon-180.png")
               if not os.path.exists(os.path.join(WEB, p))]
    if missing:
        print("  [경고] 없는 파일:", missing, "→ build_fonts.py / build_icons.py 를 먼저 돌리세요")

    total = 0
    for base, _, files in os.walk(WEB):
        for fn in files:
            total += os.path.getsize(os.path.join(base, fn))
    print("법령 %d건 · 조문 %d개 · 별표 %d개 · 판 %s"
          % (len(docs), sum(len(d["조문"]) for d in docs), sum(len(d["별표"]) for d in docs), version))
    print("원문 %.2fMB → 내려받기 %.2fMB · 앱 전체 %.2fMB"
          % (len(raw) / 1e6, gz.__len__() / 1e6, total / 1e6))
    print("→", WEB)


if __name__ == "__main__":
    main()
