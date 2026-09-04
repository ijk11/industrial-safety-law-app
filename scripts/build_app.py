# -*- coding: utf-8 -*-
"""data/ 의 법령 JSON을 단일 HTML 앱으로 묶는다 (실행 중 네트워크 호출 없음).

    python scripts/build_app.py

원문 전체를 gzip+base64로 파일 안에 넣고, 앱이 열릴 때 기기 안에서 펼친다.
산출물: dist/산안법-조문찾기.html
"""
import base64, gzip, io, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 법령 위계 → 배지 약호 · 색 단계 · 필터 묶음 · 계열
# 계열은 본문의 "법 제4조" 처럼 짧게 부른 인용을 어느 법으로 풀지 가른다.
# 중대재해처벌법 시행령의 "법" 은 산안법이 아니라 중대재해처벌법이다.
LEVELS = [
    ("산업안전보건법", "법", 1, "법률", "산안"),
    ("산업안전보건법 시행령", "령", 2, "시행령", "산안"),
    ("산업안전보건법 시행규칙", "칙", 3, "시행규칙", "산안"),
    ("산업안전보건기준에 관한 규칙", "기준", 4, "기준규칙", "산안"),
    ("유해ㆍ위험작업의 취업 제한에 관한 규칙", "취업제한", 4, "취업제한규칙", "산안"),
    ("중대재해 처벌 등에 관한 법률", "중대재해", 1, "중대재해", "중대재해"),
    ("중대재해 처벌 등에 관한 법률 시행령", "중대재해령", 2, "중대재해", "중대재해"),
]

# 고시는 fetch_laws.py 의 나열 순서(주제별)를 그대로 따른다
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from fetch_laws import NOTICES, norm  # noqa: E402

# 감독규정과 표준안전작업지침·기술지침은 배지와 묶음을 따로 준다.
# 지침은 단계 6으로 두어 같은 조건의 검색 결과에서 고시보다 뒤에 나온다.
NOTICE_LEVELS = {
    norm("근로감독관 집무규정(산업안전보건)"): ("감독규정", 5, "감독규정"),
    norm("가설공사 표준안전 작업지침"): ("지침", 6, "지침"),
    norm("굴착공사 표준안전 작업지침"): ("지침", 6, "지침"),
    norm("발파 표준안전 작업지침"): ("지침", 6, "지침"),
    norm("철골공사표준안전작업지침"): ("지침", 6, "지침"),
    norm("추락재해방지표준안전작업지침"): ("지침", 6, "지침"),
    norm("콘크리트공사 표준안전 작업지침"): ("지침", 6, "지침"),
    norm("터널공사 표준안전 작업지침-NATM공법"): ("지침", 6, "지침"),
    norm("해체공사표준안전작업지침"): ("지침", 6, "지침"),
    norm("벌목 표준안전 작업지침"): ("지침", 6, "지침"),
    norm("운반하역 표준안전 작업지침"): ("지침", 6, "지침"),
    norm("가스누출감지경보기 설치에 관한 기술상의 지침"): ("지침", 6, "지침"),
    norm("감전재해 예방을 위한 기술상의 지침"): ("지침", 6, "지침"),
    norm("공작기계 안전기준 일반에 관한 기술상의 지침"): ("지침", 6, "지침"),
    norm("저압산업용기계기구의 부속전기설비의 전기재해 예방을 위한 기술상의 지침"): ("지침", 6, "지침"),
    norm("정전기재해 예방을 위한 기술상의 지침"): ("지침", 6, "지침"),
    norm("제1차 금속산업 안전작업지침"): ("지침", 6, "지침"),
    norm("철강업에 있어서 수증기 폭발 및 고열물 접촉위험 방지를 위한 기술상의 지침"): ("지침", 6, "지침"),
}


def load(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def collect():
    docs = []
    laws_dir = os.path.join(ROOT, "data", "laws")
    files = {norm(os.path.splitext(f)[0]): os.path.join(laws_dir, f) for f in os.listdir(laws_dir)}
    for name, short, level, group, family in LEVELS:
        f = files.get(norm(name))
        if not f:
            print("  [건너뜀] 없음:", name)
            continue
        d = load(f)
        d["약호"], d["단계"], d["군"], d["계"] = short, level, group, family
        docs.append(d)

    nt_dir = os.path.join(ROOT, "data", "notices")
    nfiles = {norm(os.path.splitext(f)[0]): os.path.join(nt_dir, f) for f in os.listdir(nt_dir)}
    for name in NOTICES:
        f = nfiles.get(norm(name))
        if not f:
            print("  [건너뜀] 없음:", name)
            continue
        d = load(f)
        d["약호"], d["단계"], d["군"] = NOTICE_LEVELS.get(norm(name), ("고시", 5, "고시"))
        d["계"] = "산안"
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



# 괘선표를 진짜 표로 — 466건 중 171건이 글자 손실 없이 풀린다.
# 중첩 표·끊긴 테두리처럼 조금이라도 미심쩍으면 None 을 돌려주고 원문 그대로 둔다.
NL = chr(10)

def dw(ch):
    return 2 if unicodedata.east_asian_width(ch) in "WFA" else 1


def at(line, chars):
    out, x = [], 0
    for ch in line:
        if ch in chars:
            out.append(x)
        x += dw(ch)
    return out


def is_row(l):
    s = l.strip()
    return bool(s) and s[0] in V


def blocks(text):
    out, cur, kind = [], [], None
    for l in text.split(NL):
        k = "tbl" if (is_border(l) or is_row(l)) else "txt"
        if k != kind:
            if cur:
                out.append((kind, cur))
            cur, kind = [], k
        cur.append(l)
    if cur:
        out.append((kind, cur))
    return out


def split_cells(l, edges, tol):
    """한 줄을 세로선 기준으로 자른다 → [(글, 시작칸, 끝칸)].

    원문이 칸을 넘겨 세로선이 밀린 표가 많다. 가까운 경계로 붙여 읽되,
    순서가 뒤집히거나 tol 보다 멀면 손을 뗀다."""
    pos = at(l, V)
    if len(pos) < 2:
        return None
    snap, prev = [], -1
    for p in pos:
        k = min(range(len(edges)), key=lambda j: abs(edges[j] - p))
        if abs(edges[k] - p) > tol or k <= prev:
            return None
        snap.append(k)
        prev = k
    cells, buf, start, seen = [], None, None, 0
    for ch in l:
        if ch in V:
            k = snap[seen]
            seen += 1
            if buf is not None:
                cells.append(("".join(buf), start, k))
            buf, start = [], k
            continue
        if buf is not None:
            buf.append(ch)
    return cells or None


def parse(lines):
    """[[(글, colspan), ...], ...] 로. 못 풀면 None."""
    borders = [l for l in lines if is_border(l)]
    if not borders:
        return None
    edges = sorted({p for l in borders for p in at(l, JOINT)})
    if len(edges) < 3:
        return None
    gap = min(b - a for a, b in zip(edges, edges[1:]))
    tol = max(1, min(8, gap // 2))

    groups, cur = [], []
    for l in lines:
        if is_border(l):
            if cur:
                groups.append(cur)
            cur = []
            continue
        if is_row(l):
            cur.append(l)
        elif l.strip():
            return None
    if cur:
        groups.append(cur)
    if not groups:
        return None

    rows = []
    for g in groups:
        shape, acc = None, None
        for l in g:
            cs = split_cells(l, edges, tol)
            if cs is None or cs[0][1] != 0 or cs[-1][2] != len(edges) - 1:
                return None
            sig = [(a, b) for _, a, b in cs]
            if shape is None:
                shape, acc = sig, [[t] for t, _, _ in cs]
            elif sig != shape:
                rows.append(_row(acc, shape))     # 칸 모양이 바뀌면 새 행
                shape, acc = sig, [[t] for t, _, _ in cs]
            else:
                for i, (t, _, _) in enumerate(cs):
                    acc[i].append(t)
        if acc:
            rows.append(_row(acc, shape))
    if not rows:
        return None
    # 셀 안에 괘선이 남았다면 표 안에 표가 또 그려진 것이다. 손대지 않는다.
    for row in rows:
        for text, _ in row:
            if any(c in BOXSET for c in text):
                return None
    return rows


def _row(acc, shape):
    return [(NL.join(x.rstrip() for x in acc[i]).strip(), shape[i][1] - shape[i][0])
            for i in range(len(acc))]



# ---------------- 접힌 줄 되돌리기 ----------------
# 접힌 자리에 공백이 있었는지는 데이터에 없다. 찍어서 이으면 띄어쓰기가 대량으로 틀리므로
# (표본 대조 결과 근거 없는 추정의 정답률은 61%뿐이었다) 근거가 있는 자리만 잇는다.

# 새 항목이 시작하는 줄. '다)' 처럼 '…제외한다)' 의 꼬리와 헷갈리는 모양은 넣지 않는다.
MARK = re.compile(r"^\s*(?:[○◦●▪□■※]|[0-9]+\s*\.|[가-힣]\s*\.\s|\([0-9]+\)|[-–—]\s|비고)")
# 홀로 쓰이는 낱말 — 앞뒤로 반드시 띄어 쓴다.
NEXT_WORD = re.compile(r"^(?:및|또는|각|기타|해당|다만)(?![가-힣])|^(?:등|중)(?:[의은는을를과와에도만,.)]|으로|$)")
PREV_WORD = re.compile(r"(?:^|\s)(?:및|또는|등|중|각|기타|해당)$")
# 붙여 쓰는 것이 문법으로 정해진 자리
NO_SPACE_BEFORE = ")]}」』〉》,.·ㆍ;:%"
NO_SPACE_AFTER = "([{「『〈《"
TAIL = re.compile(r"[0-9A-Za-z가-힣]+$")
HEAD = re.compile(r"^[0-9A-Za-z가-힣]+")
# 법령 인용은 한 낱말이다 — 제29 + 조, 제 + 29 처럼 끊긴 자리는 붙인다
CITE_L = re.compile(r"(?:제\s*)?\d+$")
CITE_R = re.compile(r"^(?:조|항|호|목|절|장|편|관|류|종)(?![가-힣])|^의\s*\d")


class Corpus:
    """조문 본문 — 강제 줄바꿈이 없는 온전한 문장이라 띄어쓰기의 근거가 된다."""

    def __init__(self, text):
        self.text = text

    def decide(self, left, right):
        """끊긴 자리의 앞뒤 낱말을 떼어 내 조문에서 찾는다.
        문장부호가 섞이면 못 찾으므로 글자만 남긴다."""
        m = TAIL.search(left)
        n2 = HEAD.match(right)
        if not m or not n2:
            return None
        a, b = m.group()[-6:], n2.group()[:6]
        for i in range(len(a), 0, -1):
            for j in range(len(b), 0, -1):
                if i + j < 4:
                    continue
                x, y = a[-i:], b[:j]
                stuck = x + y in self.text
                spaced = x + " " + y in self.text
                if stuck != spaced:
                    return "" if stuck else " "
        return None


def gap_for(left, right, corpus):
    """이 자리에 무엇이 있었는지. 모르면 None (줄바꿈을 그대로 둔다)."""
    if not left or not right:
        return None
    if right[0] in NO_SPACE_BEFORE:
        return ""
    if left[-1] in NO_SPACE_AFTER:
        return ""
    if left[-1] in ",;:":
        return " "
    if CITE_L.search(left) and CITE_R.match(right):
        return ""
    if left.endswith("제") and right[:1].isdigit():
        return ""
    # 괄호가 열리는 자리는 줄을 바꾸는 편이 읽기 좋다 (그대로 둔다)
    if right[0] in NO_SPACE_AFTER:
        return None
    g = corpus.decide(left, right) if corpus else None
    if g is not None:
        return g
    if NEXT_WORD.match(right) or PREV_WORD.search(left):
        return " "
    return None


def join(frags, corpus=None):
    frags = [f.rstrip() for f in frags]
    if len([f for f in frags if f.strip()]) < 2:
        return NL.join(f.strip() for f in frags).strip()
    out = ""
    for f in frags:
        s = f.strip()
        if not s:
            continue
        if not out:
            out = s
            continue
        if MARK.match(f):
            out += NL + s
            continue
        last = out.split(NL)[-1]
        g = gap_for(last, s, corpus)
        out += (g + s) if g is not None else (NL + s)
    return out.strip()


def build_corpus(docs):
    """조문 본문 — 강제 줄바꿈이 없는 온전한 문장이라 띄어쓰기의 근거가 된다."""
    buf = []
    for d in docs:
        for a in d.get("조문", []):
            if a.get("본문"):
                buf.append(a["본문"])
            for h in a.get("항", []) or []:
                if h.get("내용"):
                    buf.append(h["내용"])
                buf.extend(h.get("호", []) or [])
    return Corpus(NL.join(buf))


def split_table(text, corpus=None):
    """별표를 [['t', 글] | ['r', 행목록]] 으로 자른다. 표를 못 풀면 None."""
    out, seen = [], False
    for kind, lines in blocks(text):
        if kind == "txt":
            s = NL.join(lines).strip(NL)
            if s.strip():
                out.append(["t", s])
            continue
        rows = parse(lines)
        if rows is None:
            return None
        seen = True
        rows = [[(join(c.split(NL), corpus), n) for c, n in row] for row in rows]
        out.append(["r", [[c if n == 1 else [c, n] for c, n in row] for row in rows]])
    return out if seen else None


def attach_penalty(docs, corpus):
    """제12장 벌칙·과태료를 산안법 조문에 붙인다. 조문을 읽다가 바로 눈에 들도록."""
    import penalty as P
    P.use_joiner(P.make_joiner(gap_for, corpus))
    pen, dropped = P.build(docs)
    law = next((d for d in docs if d.get("법령명") == P.LAW), None)
    if not law:
        return 0, dropped
    n = 0
    for a in law.get("조문", []):
        v = pen.get(a["조번호"])
        if not v:
            continue
        slot = {}
        if v["항"]:
            slot["항"] = {str(k): [{x: y for x, y in it.items() if x != "일"} for it in lst]
                          for k, lst in sorted(v["항"].items())}
        if v["끝"]:
            slot["끝"] = [{x: y for x, y in it.items() if x != "일"} for it in v["끝"]]
        if slot:
            a["벌"] = slot
            n += 1
    return n, dropped


def slim(docs):
    """앱이 쓰지 않는 필드를 덜어내고, 별표를 읽기 좋은 꼴로 바꾼다."""
    corpus = build_corpus(docs)
    hit, dropped = attach_penalty(docs, corpus)
    print("벌칙·과태료를 붙인 조문 %d개%s" % (
        hit, (" (법에 없는 조 %d건은 건너뜀)" % len(dropped)) if dropped else ""))
    keep_doc = {"법령명", "약칭", "법령구분", "법령번호", "소관부처", "공포일", "시행일", "링크",
                "수집일", "조문", "별표", "약호", "단계", "군", "계"}
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
            if kind == "글":
                b["내용"], b["글"] = join(text.split(NL), corpus), 1
                continue
            pieces = split_table(text, corpus)
            if pieces:
                b["조각"] = pieces
                b.pop("내용", None)
            else:
                b["내용"] = text
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


def bake_gz(raw):
    """같은 원문이면 어디서 구워도 같은 바이트가 나오게 굽는다.

    mtime 을 0으로 두는 것만으로는 모자란다. gzip 머리 10번째 칸은 구운 OS 인데,
    파이썬 3.13 부터 '알 수 없음'(0xFF)을 적고 그 전에는 3(유닉스)을 적는다.
    그 한 바이트 때문에 판(version)이 갈려, 법이 그대로여도 폰이 1.6MB를 다시 받는다.
    """
    gz = gzip.compress(raw, 9, mtime=0)
    return gz[:9] + b"\xff" + gz[10:]


def main():
    docs = slim(collect())
    payload = json.dumps(docs, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    gz = bake_gz(payload)
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
