# -*- coding: utf-8 -*-
"""data/ 의 법령 JSON을 단일 HTML 앱으로 묶는다 (실행 중 네트워크 호출 없음).

    python scripts/build_app.py

원문 전체를 gzip+base64로 파일 안에 넣고, 앱이 열릴 때 기기 안에서 펼친다.
산출물: dist/산안법-조문찾기.html
"""
import base64, gzip, io, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 법령 위계 → 배지 약호 · 색 단계 · 필터 묶음
LEVELS = [
    ("산업안전보건법", "법", 1, "법률"),
    ("산업안전보건법 시행령", "령", 2, "시행령"),
    ("산업안전보건법 시행규칙", "칙", 3, "시행규칙"),
    ("산업안전보건기준에 관한 규칙", "기준", 4, "기준규칙"),
    ("유해ㆍ위험작업의 취업 제한에 관한 규칙", "취업제한", 4, "취업제한규칙"),
]

# 고시는 fetch_laws.py 의 나열 순서(주제별)를 그대로 따른다
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from fetch_laws import NOTICES, norm  # noqa: E402


def load(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def collect():
    docs = []
    laws_dir = os.path.join(ROOT, "data", "laws")
    files = {norm(os.path.splitext(f)[0]): os.path.join(laws_dir, f) for f in os.listdir(laws_dir)}
    for name, short, level, group in LEVELS:
        f = files.get(norm(name))
        if not f:
            print("  [건너뜀] 없음:", name)
            continue
        d = load(f)
        d["약호"], d["단계"], d["군"] = short, level, group
        docs.append(d)

    nt_dir = os.path.join(ROOT, "data", "notices")
    nfiles = {norm(os.path.splitext(f)[0]): os.path.join(nt_dir, f) for f in os.listdir(nt_dir)}
    for name in NOTICES:
        f = nfiles.get(norm(name))
        if not f:
            print("  [건너뜀] 없음:", name)
            continue
        d = load(f)
        d["약호"], d["단계"], d["군"] = "고시", 5, "고시"
        docs.append(d)
    return docs


def slim(docs):
    """앱이 쓰지 않는 필드를 덜어내고, 별표 표의 줄 끝 공백을 정리한다."""
    keep_doc = {"법령명", "약칭", "법령구분", "법령번호", "소관부처", "공포일", "시행일", "링크",
                "조문", "별표", "약호", "단계", "군"}
    for d in docs:
        for k in list(d):
            if k not in keep_doc:
                del d[k]
        for a in d.get("조문", []):
            for k in list(a):
                if k in ("개정이력", "참조조문"):
                    del a[k]
            if not a.get("본문"):
                a.pop("본문", None)
        for b in d.get("별표", []):
            b["내용"] = "\n".join(l.rstrip() for l in b["내용"].split("\n")).strip("\n")
    return docs


ART_HEAD = """<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;700&family=Nanum+Gothic+Coding&display=swap">
<style>
:root{
  --font-ui:"Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif;
  --font-serif:"Noto Serif KR","Apple SD Gothic Neo",serif;
  --font-mono:"Nanum Gothic Coding",monospace;
}
</style>"""

ART_LOADER = """async function loadLawText() {
  const b64 = document.getElementById("payload").textContent.trim();
  const raw = atob(b64);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  return await gunzip(bytes);
}"""


def main():
    docs = slim(collect())
    payload = json.dumps(docs, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    # mtime=0 — 같은 원문이면 같은 파일이 나오게 한다 (안 그러면 다시 구울 때마다 2.2MB가 통째로 바뀐다)
    gz = gzip.compress(payload, 9, mtime=0)
    b64 = base64.b64encode(gz).decode("ascii")

    with io.open(os.path.join(ROOT, "scripts", "app_template.html"), encoding="utf-8") as f:
        html = f.read()
    for mark, value in (
        ("__HEAD_EXTRA__", ART_HEAD),
        ("__PAYLOAD__", '<script id="payload" type="text/plain">%s</script>' % b64),
        ("__DATA_LOADER__", ART_LOADER),
        ("__TAIL_EXTRA__", ""),
    ):
        assert mark in html, "템플릿에 %s 자리가 없습니다" % mark
        html = html.replace(mark, value)

    out_dir = os.path.join(ROOT, "dist")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "산안법-조문찾기.html")
    with io.open(out, "w", encoding="utf-8") as f:
        f.write(html)

    arts = sum(len(d.get("조문", [])) for d in docs)
    tbls = sum(len(d.get("별표", [])) for d in docs)
    print("법령 %d건 · 조문 %d개 · 별표 %d개" % (len(docs), arts, tbls))
    print("원문 %.2fMB → gzip %.2fMB → HTML %.2fMB" % (
        len(payload) / 1e6, len(gz) / 1e6, os.path.getsize(out) / 1e6))
    print("→", out)


if __name__ == "__main__":
    main()
