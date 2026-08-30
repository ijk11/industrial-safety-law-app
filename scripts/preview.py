# -*- coding: utf-8 -*-
"""PC에서 web/ 을 실제 주소처럼 열어 본다.

    python scripts/preview.py

브라우저는 file:// 에서 옆 파일 읽기를 막으므로, web/ 을 그냥 더블클릭하면 열리지 않는다.
이 스크립트가 작은 서버를 띄워 http://127.0.0.1:8770/ 으로 열어 준다. Ctrl+C 로 끝낸다.
"""
import functools, http.server, os, socketserver, threading, webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
PORT = 8770


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")   # 고치는 중에는 캐시가 방해된다
        super().end_headers()

    def log_message(self, *a):
        pass


def main():
    if not os.path.exists(os.path.join(WEB, "index.html")):
        raise SystemExit("web/index.html 이 없습니다. 먼저 python scripts/build_pwa.py 를 돌리세요.")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), functools.partial(Handler, directory=WEB)) as httpd:
        url = "http://127.0.0.1:%d/" % PORT
        print("열었습니다 →", url, "  (Ctrl+C 로 종료)")
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n종료")


if __name__ == "__main__":
    main()
