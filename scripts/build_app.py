# -*- coding: utf-8 -*-
"""data/ 의 법령 JSON을 단일 HTML 앱으로 묶는다 (실행 중 네트워크 호출 없음).

    python scripts/build_app.py

원문 전체를 gzip+base64로 파일 안에 넣고, 앱이 열릴 때 기기 안에서 펼친다.
산출물: dist/산안법-조문찾기.html
"""
import base64, gzip, io, json, os, re, sys, unicodedata

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


# ---------------- 별표 괘선 ----------------
# 별표 551건 중 91건은 표가 아니라 글을 상자에 넣어 둔 것이거나 아예 괘선이 없다.
# 그런 것은 괘선 장식만 걷어내 비례 글꼴로 흘려 보낸다 (폰에서 가로로 잘리지 않는다).
# 진짜 표 460건은 칸이 맞아야 하므로 손대지 않는다.
V = "│┃"
H = "─━"
JOINT = "┌┬┐├┼┤└┴┘┏┳┓┣╋┫┗┻┛┠┨┯┷┰┸╂┿"
BOX = V + H + JOINT
BOXSET = set(BOX)
RE_BOX = re.compile("[" + re.escape(BOX) + "]")


def is_border(l):
    """괘선만으로 이뤄진 줄. 모서리 없이 ─ 로 시작하는 줄도 포함한다."""
    s = l.strip()
    return bool(s) and set(s) <= BOXSET | {" "} and any(c in H for c in s)


def col_count(text):
    n = 0
    for l in text.split("\n"):
        if is_border(l):
            n = max(n, sum(1 for c in l if c in JOINT) - 1)
        s = l.strip()
        if s and s[0] in V:
            n = max(n, sum(1 for c in s if c in V) - 1)
    return n


def space_aligned(text):
    """괘선 없이 공백으로 칸을 맞춘 것. 비례 글꼴로 흘리면 정렬이 깨진다."""
    ls = [l for l in text.split("\n") if l.strip()]
    if len(ls) < 4:
        return False
    return sum(1 for l in ls if re.search(r"\S {2,}\S", l)) / len(ls) >= 0.3


def strip_box(text):
    out = []
    for l in text.split("\n"):
        if is_border(l):
            continue
        s = l.rstrip()
        while s and s[0] in V:
            s = s[1:]
        while s and s[-1] in V:
            s = s[:-1]
        out.append(s.rstrip())
    return out


def convert(text):
    """('글'|'표', 내용). '글' 은 비례 글꼴로 흘려도 되는 것.

    줄바꿈은 손대지 않는다. 원문이 칸 너비에 맞춰 접어 둔 자리에 공백이 있었는지가
    데이터에 남아 있지 않아(줄 끝 공백이 전부 잘려 있다), 도로 이으면 '해당 지정기관'
    이 '해당지정기관' 이 된다. 법령 원문을 바꾸는 셈이라 하지 않는다.
    """
    if col_count(text) > 1:
        return "표", text
    if not RE_BOX.search(text):
        return ("표", text) if space_aligned(text) else ("글", text)
    body = "\n".join(strip_box(text)).strip("\n")
    # 안전망 — 벗겼는데도 괘선이 남았다면 표를 잘못 본 것이다. 원문 그대로 둔다.
    if RE_BOX.search(body):
        return "표", text
    return "글", body


def slim(docs):
    """앱이 쓰지 않는 필드를 덜어내고, 별표 표의 줄 끝 공백을 정리한다."""
    keep_doc = {"법령명", "약칭", "법령구분", "법령번호", "소관부처", "공포일", "시행일", "링크",
                "수집일", "조문", "별표", "약호", "단계", "군"}
    for d in docs:
        # 언제 받아온 원문인지는 앱이 화면에 보여 줘야 한다. 출처 문자열에서 날짜만 빼 둔다.
        m = re.search(r"수집일\s*(\d{4}-\d{2}-\d{2})", d.get("출처") or "")
        if m:
            d["수집일"] = m.group(1)
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
            kind, text = convert(b["내용"])
            b["내용"] = text
            if kind == "글":
                b["글"] = 1
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
