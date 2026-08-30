# -*- coding: utf-8 -*-
"""실제 브라우저로 web/ 을 열어 동작을 확인한다.

    python scripts/verify.py            # 검사만
    python scripts/verify.py --shots    # 아이폰 크기(390x844) 화면도 찍는다

크롬을 화면 없이 띄워 검색·조문 열기·인용 이동·별표·목차·책갈피까지 눌러 본다.
법령을 다시 받은 뒤에는 이걸 돌려 깨진 데가 없는지 보면 된다.
"""
import functools, http.server, io, os, re, shutil, socketserver, subprocess, sys, tempfile, threading, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
PORT = 8791

CHROMES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser",
]

FRAME = ('<!doctype html><meta charset="utf-8"><title>frame</title>'
         '<style>html,body{margin:0;background:#888}'
         'iframe{width:390px;height:844px;border:0;display:block}</style>'
         '<iframe src="%s"></iframe>')

SHOTS = {
    "검색": '''const q=document.querySelector("#q");q.value="추락 방지";
        q.dispatchEvent(new Event("input",{bubbles:true}));await w(800);''',
    "조문": '''const r=RECS.find(x=>DOCS[x.d].법령명==="산업안전보건법"&&x.no==="제5조");
        openRec(r.key,"new");await w(700);''',
    "별표": '''document.documentElement.setAttribute("data-theme","dark");
        const r=RECS.find(x=>DOCS[x.d].법령명==="산업안전보건법 시행령"&&x.kind===1&&x.no==="별표 3");
        openRec(r.key,"new");await w(700);''',
    "별표글": '''const r=RECS.find(x=>x.kind===1&&x.flow);
        openRec(r.key,"new");await w(700);''',
    "목차": '''idxDoc=DOCS.findIndex(d=>d.법령명==="산업안전보건기준에 관한 규칙");
        setTab("index");await w(700);''',
}


def find_chrome():
    for c in CHROMES:
        if os.path.exists(c) or shutil.which(c):
            return c
    raise SystemExit("크롬이나 엣지를 찾지 못했습니다.")


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass


def serve():
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), functools.partial(Handler, directory=WEB))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def make_page(name, script):
    with io.open(os.path.join(WEB, "index.html"), encoding="utf-8") as f:
        page = f.read()
    path = os.path.join(WEB, "__%s.html" % name)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(page.replace("</body>", "<script>\n%s\n</script>\n</body>" % script))
    return path


def run_chrome(chrome, url, args, profile):
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                    "--user-data-dir=" + profile, "--virtual-time-budget=70000"] + args + [url],
                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=240)


def main():
    if not os.path.exists(os.path.join(WEB, "index.html")):
        raise SystemExit("web/index.html 이 없습니다. python scripts/build_pwa.py 를 먼저 돌리세요.")
    chrome = find_chrome()
    httpd = serve()
    tmp = tempfile.mkdtemp(prefix="oshverify")
    made = []
    try:
        with io.open(os.path.join(ROOT, "scripts", "smoke_test.js"), encoding="utf-8") as f:
            made.append(make_page("verify", f.read()))
        dom = os.path.join(tmp, "dom.html")
        with open(dom, "wb") as out:
            p = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                                "--user-data-dir=" + os.path.join(tmp, "p0"),
                                "--virtual-time-budget=70000", "--dump-dom",
                                "http://127.0.0.1:%d/__verify.html" % PORT],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=300)
            out.write(p.stdout)
        with io.open(dom, encoding="utf-8", errors="replace") as f:
            body = f.read()
        m = re.search(r'<pre id="testout">(.*?)</pre>', body, re.S)
        if not m:
            raise SystemExit("시험이 끝나지 않았습니다. web/ 을 브라우저로 직접 열어 확인해 보세요.")
        lines = html.unescape(m.group(1)).splitlines()
        for l in lines:
            print(("  " if l.startswith("PASS") else "! ") + l)
        fails = [l for l in lines if l.startswith("FAIL")]
        print("\n%d개 항목 중 실패 %d개" % (len(lines), len(fails)))

        if "--shots" in sys.argv:
            wrap = "const w=ms=>new Promise(r=>setTimeout(r,ms));(async()=>{" \
                   "for(let i=0;i<200&&document.getElementById('boot');i++)await w(100);%s})();"
            print("\n화면 저장:")
            for i, (label, js) in enumerate(SHOTS.items()):
                made.append(make_page("shot%d" % i, wrap % js))
                fp = os.path.join(WEB, "__frame%d.html" % i)
                with io.open(fp, "w", encoding="utf-8") as f:
                    f.write(FRAME % ("__shot%d.html" % i))
                made.append(fp)
                png = os.path.join(ROOT, "shots", "%s.png" % label)
                os.makedirs(os.path.dirname(png), exist_ok=True)
                run_chrome(chrome, "http://127.0.0.1:%d/__frame%d.html" % (PORT, i),
                           ["--window-size=390,844", "--screenshot=" + png],
                           os.path.join(tmp, "p%d" % (i + 1)))
                print("  shots/%s.png" % label)
        return 1 if fails else 0
    finally:
        for f in made:
            try:
                os.remove(f)
            except OSError:
                pass
        httpd.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
