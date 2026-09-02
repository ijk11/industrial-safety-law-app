# -*- coding: utf-8 -*-
"""산업안전보건법 제12장(제167조~제175조)을 조문 밑에 붙일 꼴로 뽑는다.

벌칙(징역·벌금)은 법 제167조~제172조 본문에서, 과태료는 법 제175조가 아니라
시행령 [별표 35] 개별기준에서 캐낸다. 1·2·3차 금액이 거기에만 있기 때문이다.

담는 것은 **조문을 직접 위반한** 경우뿐이다. "~에 따른 명령을 위반한 자",
양벌규정(제173조), 가중처벌(제167조제2항), 이수명령(제174조)은 넣지 않는다.
성격이 다른 것을 한자리에 섞으면 조문마다 같은 경고가 반복돼 본문을 가린다.

  {"제38조": {"항": {1: [항목...], 2: [...]}, "끝": [항목...]}}

항이 지정된 참조는 그 항 밑에, 조 전체에 걸리는 참조는 조문 맨 아래("끝")에 붙는다.
"""
import re

LAW = "산업안전보건법"
DEC = "산업안전보건법 시행령"

# 준용 괄호는 참조를 읽는 데 방해만 된다. 셈에서 빼고 본다.
JUNYONG = re.compile(r"\([^()]*준용[^()]*\)")
# "제38조", "제166조의2" — 조 하나를 가리키는 말
ART = re.compile(r"제(\d+)조(?:의(\d+))?")
SAME = re.compile(r"같은 조")


def _clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


# 줄바꿈으로 끊긴 말을 도로 잇는 일은 build_app.join(말뭉치) 이 맡는다.
# 붙일지 띄울지를 법령 전체의 쓰임을 보고 정하므로 "철거또는해체" 같은 일이 없다.
_JOINER = None


def use_joiner(fn):
    global _JOINER
    _JOINER = fn


def _relaxed(corpus, left, right):
    """build_app 은 앞뒤 넉 자가 안 되면 판정을 포기한다. 여기서는 석 자까지 본다 —
    '알아볼 수' + '없을' 처럼 한 글자로 끊긴 자리가 좁은 칸에서는 흔하다."""
    a = re.search(r"[가-힣]+$", left)
    b = re.match(r"^[가-힣]+", right)
    if not (a and b and corpus):
        return None
    a, b = a.group()[-4:], b.group()[:4]
    for i in range(len(a), 0, -1):
        for j in range(len(b), 0, -1):
            if i + j < 3:
                continue
            x, y = a[-i:], b[:j]
            stuck, spaced = x + y in corpus.text, x + " " + y in corpus.text
            if stuck != spaced:
                return "" if stuck else " "
    return None


def make_joiner(gap_for, corpus):
    """별표 35 의 칸은 여덟 칸밖에 안 돼 낱말 한가운데서 줄이 끊긴다.
    말뭉치가 아는 자리는 말뭉치를 따르고, 모르는 자리는 **붙여** 읽는다 —
    이만큼 좁은 칸에서는 진짜 띄어쓰기보다 끊긴 낱말이 훨씬 흔하다."""
    def fn(frags):
        out = ""
        for f in frags:
            t = f.strip()
            if not t:
                continue
            if not out:
                out = t
                continue
            g = gap_for(out, t, corpus)
            if g is None:
                g = _relaxed(corpus, out, t)
            if g is None:
                g = "" if (re.search(r"[가-힣]$", out) and re.match(r"^[가-힣]", t)) else " "
            out += g + t
        return out
    return fn


def _join(frags):
    """칸 안에서 줄바꿈으로 끊긴 말을 다시 잇는다."""
    if _JOINER:
        return _clean(_JOINER([f for f in frags if f.strip()]))
    out = ""
    for f in frags:
        f = f.strip()
        if not f:
            continue
        if not out:
            out = f
        elif out[-1] in "([{「『·ㆍ-~" or f[0] in ")]}」』,.·ㆍ":
            out += f
        elif re.search(r"[가-힣]$", out) and re.match(r"^[가-힣]", f):
            out += f          # 낱말 한가운데서 끊긴 것 — 그대로 붙인다
        else:
            out += " " + f
    return _clean(out)


# ---------------------------------------------------------------- 과태료

def _rows(dec_doc):
    """[별표 35] 개별기준을 행 단위로 자른다. 행은 '가.' '가의2.' 같은 표지로 시작한다."""
    tb = [x for x in dec_doc.get("별표", []) if x.get("번호") == "별표 35"]
    if not tb:
        return []
    lines = [l for l in tb[0]["내용"].split("\n") if l.strip().startswith("│")]
    head = next((i for i, l in enumerate(lines) if "제10조제3항" in l), None)
    if head is None:
        return []
    cells = []
    for l in lines[head:]:
        parts = l.split("│")[1:-1]
        if len(parts) == 6:
            cells.append([p.strip() for p in parts])
    mark = re.compile(r"^[가-힣](?:의\d+)?\.\s")
    rows, cur = [], None
    for c in cells:
        if mark.match(c[0]):
            if cur:
                rows.append(cur)
            cur = [c]
        elif cur:
            cur.append(c)
    if cur:
        rows.append(cur)
    return rows


def _money(v):
    """별표의 금액 칸은 '만원' 단위 숫자다. 글로 풀어 쓴 칸(제119조 등)은 그대로 둔다."""
    v = _clean(v)
    if not v:
        return ""
    return v + "만원" if re.fullmatch(r"[\d,]+", v) else v


def _fine(row):
    """한 행에서 1·2·3차 금액을 캔다. 세부내용이 갈리면 경우마다 따로 캔다.

    세부내용 칸은 두 겹까지 갈린다 — 'N)' 아래 다시 '가) 나)' 가 붙고,
    그때는 금액이 아래쪽 '가) 나)' 에만 붙는다. 어느 쪽이든 표지가 놓인 줄에
    그 경우의 금액이 함께 있으므로, 줄 자리를 맞추면 짝이 어긋나지 않는다.
    """
    # 표지는 뒤에 내용이 따라붙는다. "1개소당)" 처럼 줄이 끊겨 생긴 꼬리를
    # 표지로 잘못 읽지 않도록 가나다 차례의 글자만, 그것도 내용이 딸린 것만 본다.
    L1 = re.compile(r"^\d+\)\s*\S")
    L2 = re.compile(r"^[가나다라마바사아자차카타파하]\)\s*\S")
    marks = []
    for i, ln in enumerate(row):
        t = _clean(ln[2])
        if L1.match(t):
            marks.append((i, 1))
        elif L2.match(t):
            marks.append((i, 2))
    if not marks:
        return None, [_money(_join([ln[c] for ln in row])) for c in (3, 4, 5)]

    nodes = []
    for k, (at, lv) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(row)
        seg = row[at:end]
        nodes.append({
            "lv": lv,
            "때": re.sub(r"^(?:\d+|[가-힣])\)\s*", "", _join([ln[2] for ln in seg])),
            "돈": [_money(_join([ln[c] for ln in seg])) for c in (3, 4, 5)],
        })

    cases, i = [], 0
    while i < len(nodes):
        n = nodes[i]
        kids = []
        j = i + 1
        while n["lv"] == 1 and j < len(nodes) and nodes[j]["lv"] == 2:
            kids.append(nodes[j])
            j += 1
        if kids:
            for k in kids:
                cases.append({"때": n["때"] + " › " + k["때"], "돈": k["돈"]})
        elif any(n["돈"]):
            cases.append({"때": n["때"], "돈": n["돈"]})
        i = j if kids else i + 1
    return (cases, None) if cases else (None, [_money(_join([ln[c] for ln in row])) for c in (3, 4, 5)])


def _targets(text):
    """위반행위 칸에서 '법 제○조제○항' 을 캔다. 여럿이면 모두 돌려준다."""
    t = _clean(JUNYONG.sub("", text))
    # 원문 오타 보정 — '법 제145제1항' 처럼 '조' 가 빠진 것이 있다
    t = re.sub(r"법 ?제(\d+)제(\d+)항", r"법 제\1조제\2항", t)
    out, cur = [], None
    for m in re.finditer(r"제(\d+)조(?:의(\d+))?|같은 조|제(\d+)항", t):
        if m.group(3):
            if cur:
                out.append((cur, int(m.group(3))))
        elif m.group(0) == "같은 조":
            pass
        else:
            cur = "제%s조%s" % (m.group(1), "의" + m.group(2) if m.group(2) else "")
            out.append((cur, None))
    # 항이 딸린 조는 '조 전체' 자리를 지운다
    withhang = {a for a, h in out if h}
    return [(a, h) for a, h in out if h or a not in withhang]


# 위반행위 칸은 "가. 법 제10조제3항 후단을 위반하여 …한 경우" 꼴이다. 앞의 표지와
# 법조문 인용을 떼면 "…한 경우" 만 남는다 — 조문 밑에 붙일 때 그 조문 번호는 이미
# 알고 있으니 되풀이할 것이 없고, 무엇을 어겼을 때인지만 남으면 된다.
CUT = re.compile(r"^법\s*제\d+조.*?(?:(?:을|를)\s*위반하여|에\s*따른|에\s*따라)\s*")


def _when(act):
    t = re.sub(r"^[가-힣](?:의\d+)?\.\s*", "", _clean(act))
    t = re.sub(r"법 ?제(\d+)제(\d+)항", r"법 제\1조제\2항", t)   # 원문 오타 보정
    t = CUT.sub("", t, count=1)
    return t


def 과태료(docs):
    dec = next((d for d in docs if d.get("법령명") == DEC), None)
    if not dec:
        return []
    got = []
    for row in _rows(dec):
        act = _join([ln[0] for ln in row])
        base = _join([ln[1] for ln in row])
        cases, flat = _fine(row)
        when = _when(act)
        for art, hang in _targets(act):
            got.append({"t": "과", "조": art, "항": hang,
                        "일": act, "때": when, "근거": base,
                        **({"때들": cases} if cases else {"돈": flat})})
    return got


# ---------------------------------------------------------------- 벌칙

PEN = re.compile(r"(\d+년 이하의 징역 또는 \S+원 이하의 벌금"
                 r"|\d+년 이하의 징역"
                 r"|\S+원 이하의 벌금)에 처한다")


def _punish(text):
    """'5년 이하의 징역 또는 5천만원 이하의 벌금' — 형벌 문구만 떼어 온다."""
    m = PEN.search(text or "")
    return _clean(m.group(1)) if m else ""


def _refs(text):
    """벌칙 조문의 참조를 (조, 항, 호한정) 로 편다.

    '제38조제1항부터 제3항까지', '제80조제1항ㆍ제2항ㆍ제4항', '같은 조 제2항',
    '제64조제1항제1호부터 제5호까지' 같은 꼴을 모두 받는다.
    """
    t = _clean(JUNYONG.sub("", text))
    t = re.split(r"를 위반|을 위반|에 따른|위반한 자|위반하여", t)[0]
    out, cur, lastnum = [], None, None
    tok = re.compile(r"제(\d+)조(?:의(\d+))?|같은 조|제(\d+)항(?:부터 제(\d+)항까지)?"
                     r"|제(\d+)호(?:부터 제(\d+)호까지)?")
    for m in tok.finditer(t):
        if m.group(1):
            cur = "제%s조%s" % (m.group(1), "의" + m.group(2) if m.group(2) else "")
            out.append([cur, None, []])
            lastnum = None
        elif m.group(0) == "같은 조":
            if cur:
                out.append([cur, None, []])
                lastnum = None
        elif m.group(3):
            a, b = int(m.group(3)), int(m.group(4) or m.group(3))
            if out and out[-1][1] is None:
                out[-1][1] = a
                for n in range(a + 1, b + 1):
                    out.append([out[-1][0], n, []])
            elif cur:
                for n in range(a, b + 1):
                    out.append([cur, n, []])
            lastnum = None
        elif m.group(5):
            a, b = int(m.group(5)), int(m.group(6) or m.group(5))
            label = ("제%d호부터 제%d호까지" % (a, b)) if b > a else ("제%d호" % a)
            if out:
                out[-1][2].append(label)
    seen, uniq = set(), []
    for a, h, ho in out:
        k = (a, h)
        if k in seen:
            continue
        seen.add(k)
        uniq.append((a, h, "ㆍ".join(ho)))
    return uniq


def 벌칙(docs):
    law = next((d for d in docs if d.get("법령명") == LAW), None)
    if not law:
        return []
    got = []
    for a in law.get("조문", []):
        if a["조번호"] not in ("제167조", "제168조", "제169조", "제170조", "제171조", "제172조"):
            continue
        head = _clean(a.get("본문", ""))
        base_pen = _punish(head)
        units = []
        if a.get("본문") and not a.get("항"):
            units.append((head, base_pen, a["조번호"]))
        for hg in a.get("항", []):
            if a["조번호"] == "제167조" and hg["번호"] != "①":
                continue          # 제2항은 가중처벌 — 담지 않는다
            hp = _punish(hg["내용"]) or base_pen
            if hg.get("호"):
                for x in hg["호"]:
                    units.append((_clean(x), _punish(x) or hp, a["조번호"]))
            else:
                units.append((_clean(hg["내용"]), hp, a["조번호"]))
        for x in a.get("호", []) or []:
            units.append((_clean(x), _punish(x) or base_pen, a["조번호"]))

        for text, pen, src in units:
            if "에 따른 명령을 위반" in text or "명령을 위반한 자" in text:
                continue          # 조문이 아니라 그에 딸린 명령을 어긴 것 — 성격이 다르다
            if "위탁받은 자로서" in text:
                continue          # 위탁기관의 부정수행 — 그 조문 위반이 아니다
            if "위반" not in text or not pen:
                continue
            note = ""
            m = re.search(r"위반하여\s*(.+?)\s*(?:자|사람)(?:는|$)", text)
            if m and len(m.group(1)) <= 40:
                note = _clean(m.group(1))
            for art, hang, ho in _refs(text):
                got.append({"t": "벌", "조": art, "항": hang, "형": pen,
                            "한정": ho, "때": note, "근거": src, "일": text})
    return got


# ---------------------------------------------------------------- 묶기

def build(docs):
    """조문 열쇠별로 묶는다. 항이 있으면 그 항 밑, 없으면 조문 맨 아래."""
    law = next((d for d in docs if d.get("법령명") == LAW), None)
    if not law:
        return {}
    hang_count = {a["조번호"]: len(a.get("항", [])) for a in law.get("조문", [])}
    known = set(hang_count)

    out, dropped = {}, []
    for it in 벌칙(docs) + 과태료(docs):
        art = it.pop("조")
        hang = it.pop("항")
        if art not in known:
            dropped.append((art, hang, it.get("근거")))
            continue
        slot = out.setdefault(art, {"항": {}, "끝": []})
        bag = slot["항"].setdefault(hang, []) if (hang and hang <= hang_count[art]) else slot["끝"]
        sig = repr(sorted((k, repr(v)) for k, v in it.items() if k != "일"))
        if sig not in {repr(sorted((k, repr(v)) for k, v in x.items() if k != "일")) for x in bag}:
            bag.append(it)
    return out, dropped
