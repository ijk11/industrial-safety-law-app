# -*- coding: utf-8 -*-
"""국가법령정보센터 OPEN API에서 산업안전보건법 체계 원문을 수집한다.

    python scripts/fetch_laws.py             # 전체 수집
    python scripts/fetch_laws.py --only 규칙  # 이름에 '규칙'이 들어간 것만

산출물: data/laws/*.json, data/notices/*.json, data/delegations.json
공용 샘플 계정(OC=test)을 쓰므로, 본인 OC를 발급받았으면 환경변수 LAW_API_OC로 지정한다.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

OC = os.environ.get("LAW_API_OC", "test")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.law.go.kr/DRF/"

# 4대 법령 + 위임 규칙 + 중대재해처벌법 계열 (target=law)
LAWS = [
    "산업안전보건법",
    "산업안전보건법 시행령",
    "산업안전보건법 시행규칙",
    "산업안전보건기준에 관한 규칙",
    "유해·위험작업의 취업 제한에 관한 규칙",
    # 중대재해처벌법은 하위법령이 시행령 하나뿐이다 (시행규칙 없음)
    "중대재해 처벌 등에 관한 법률",
    "중대재해 처벌 등에 관한 법률 시행령",
]

# 실무 빈출 고시·훈령·지침 (target=admrul)
NOTICES = [
    # 화학물질·교육·안전보건관리
    "화학물질의 분류·표시 및 물질안전보건자료에 관한 기준",
    "화학물질 및 물리적 인자의 노출기준",
    "화학물질의 유해성·위험성 평가에 관한 규정",
    "신규화학물질의 유해성·위험성 조사 등에 관한 고시",
    "사업장 위험성평가에 관한 지침",
    "안전보건교육규정",
    "명예산업안전감독관 운영규정",
    "안전·보건관리전문기관 및 건설재해예방전문지도기관 관리규정",
    "안전·보건에 관한 업무 수행시간의 기준 고시",
    "외국어로 작성하는 안전보건표지에 관한 규정",
    # 기계·기구·보호구
    "안전검사 고시",
    "안전검사 절차에 관한 고시",
    "안전인증·자율안전확인신고의 절차에 관한 고시",
    "방호장치 안전인증 고시",
    "방호장치 자율안전기준 고시",
    "보호구 안전인증 고시",
    "보호구 자율안전확인 고시",
    "위험기계·기구 방호조치 기준",
    "위험기계·기구 안전인증 고시",
    "위험기계·기구 자율안전확인 고시",
    "안전인증대상기계등이 아닌 유해·위험기계등의 안전인증 규정",
    "공정안전보고서의 제출·심사·확인 및 이행상태평가 등에 관한 규정",
    "제조업 등 유해·위험방지계획서 제출·심사·확인에 관한 고시",
    # 건설공사
    "건설업 산업안전보건관리비 계상 및 사용기준",
    "건설공사 안전보건대장의 작성 등에 관한 고시",
    "건설업 유해·위험방지계획서 중 지도사가 평가·확인 할 수 있는 대상 건설공사의 범위 및 지도사의 요건",
    "유해·위험방지계획서 자체심사 및 확인업체 지정대상 건설업체 고시",
    "건설업체의 산업재해예방활동 실적 평가기준",
    # 작업환경·건강관리
    "작업환경측정 및 정도관리 등에 관한 고시",
    "근로자 건강진단 실시기준",
    "근로자 건강진단 관리규정",
    "특수건강진단기관의 정도관리에 관한 고시",
    "근로자 건강증진활동 지침",
    "산업보건의 관리규정",
    "사무실 공기관리 지침",
    "영상표시단말기(VDT) 취급근로자 작업관리지침",
    "근골격계부담작업의 범위 및 유해요인조사 방법에 관한 고시",
    "석면조사 및 안전성 평가 등에 관한 고시",
    "석면해체·제거업자 종사인력의 교육에 관한 규정",
    # 재해조사·감독
    "산업재해통계업무처리규정",
    "재해원인조사 및 재해조사보고서 운영에 관한 규정",
    # 고시가 아닌 훈령. 감독·처벌의 실제 잣대라 따로 둔다.
    "근로감독관 집무규정(산업안전보건)",
    # 표준안전작업지침·기술지침은 끝에 모으고, 앱에서 단계 6으로 구분한다.
    "가설공사 표준안전 작업지침",
    "굴착공사 표준안전 작업지침",
    "발파 표준안전 작업지침",
    "철골공사표준안전작업지침",
    "추락재해방지표준안전작업지침",
    "콘크리트공사 표준안전 작업지침",
    "터널공사 표준안전 작업지침-NATM공법",
    "해체공사표준안전작업지침",
    "벌목 표준안전 작업지침",
    "운반하역 표준안전 작업지침",
    "가스누출감지경보기 설치에 관한 기술상의 지침",
    "감전재해 예방을 위한 기술상의 지침",
    "공작기계 안전기준 일반에 관한 기술상의 지침",
    "저압산업용기계기구의 부속전기설비의 전기재해 예방을 위한 기술상의 지침",
    "정전기재해 예방을 위한 기술상의 지침",
    "제1차 금속산업 안전작업지침",
    "철강업에 있어서 수증기 폭발 및 고열물 접촉위험 방지를 위한 기술상의 지침",
]

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"


def _get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            if i == tries - 1:
                raise
            print("  재시도(%d) %s" % (i + 1, e))
            time.sleep(2 + i * 2)


def api(kind, target, **kw):
    p = {"OC": OC, "target": target, "type": "JSON"}
    p.update(kw)
    return json.loads(_get(BASE + kind + ".do?" + urllib.parse.urlencode(p)))


def norm(s):
    return re.sub(r"[\s·ㆍ]", "", s or "")


def search(target, name):
    body = api("lawSearch", target, query=name, display="100")
    body = body[list(body)[0]]
    items = body.get("law") or body.get("admrul") or []
    if isinstance(items, dict):
        items = [items]
    key = "법령명한글" if target == "law" else "행정규칙명"
    exact = [x for x in items if norm(x.get(key)) == norm(name)]
    if not exact:
        raise SystemExit("[!] 검색 실패: %s (후보 %s)" % (name, [x.get(key) for x in items][:5]))
    exact.sort(key=lambda x: x.get("시행일자", ""), reverse=True)
    return exact[0]


def clean(s):
    """API가 문자열 대신 중첩 리스트를 돌려주는 필드가 있어 재귀적으로 펼친다."""
    if isinstance(s, (list, tuple)):
        return "\n".join(x for x in (clean(v) for v in s) if x)
    return re.sub(r"[ \t]+", " ", str(s if s is not None else "")).strip()


def fmt_date(s):
    s = str(s or "")
    return "%s-%s-%s" % (s[:4], s[4:6], s[6:8]) if len(s) == 8 else s


def split_ho(ho):
    """호 항목이 목을 가진 dict일 수도, 문자열일 수도 있다."""
    out = []
    for h in ho if isinstance(ho, list) else [ho]:
        if isinstance(h, dict):
            txt = clean(h.get("호내용"))
            mok = h.get("목")
            if mok:
                for m in mok if isinstance(mok, list) else [mok]:
                    mc = m.get("목내용") if isinstance(m, dict) else m
                    if isinstance(mc, list):
                        mc = "\n".join(clean(x) for x in mc)
                    txt += "\n" + clean(mc)
            out.append(txt)
        else:
            out.append(clean(h))
    return [x for x in out if x]


def parse_byeolpyo(node):
    if not node:
        return []
    units = node.get("별표단위", node) if isinstance(node, dict) else node
    if isinstance(units, dict):
        units = [units]
    out = []
    for b in units:
        cont = b.get("별표내용") or []
        lines = []
        for row in cont if isinstance(cont, list) else [cont]:
            if isinstance(row, list):
                lines += [str(x).rstrip() for x in row]
            else:
                lines.append(str(row).rstrip())
        no = (b.get("별표번호") or "").lstrip("0") or "?"
        branch = (b.get("별표가지번호") or "").lstrip("0")
        label = "%s %s" % (b.get("별표구분") or "별표", no + ("의" + branch if branch else ""))
        body = "\n".join(lines).strip()
        if not body:
            continue
        out.append({"번호": label, "제목": clean(b.get("별표제목")), "내용": body})
    return out


def parse_law(mst):
    d = api("lawService", "law", MST=mst)["법령"]
    info = d["기본정보"]
    dept = info.get("소관부처")
    if isinstance(dept, dict):
        dept = dept.get("content") or dept.get("소관부처명")
    kind = info.get("법종구분")
    if isinstance(kind, dict):
        kind = kind.get("content")
    units = d.get("조문", {}).get("조문단위", [])
    if isinstance(units, dict):
        units = [units]
    jomun, cur_ch, cur_sec = [], "", ""
    for u in units:
        body = clean(u.get("조문내용"))
        if u.get("조문여부") != "조문":
            if re.match(r"^제\d+장", body):
                cur_ch, cur_sec = body, ""
            elif re.match(r"^제\d+(절|관)", body):
                cur_sec = body
            continue
        no = "제%s조" % u.get("조문번호")
        branch = (u.get("조문가지번호") or "").strip().lstrip("0")
        if branch:
            no += "의%s" % branch
        art = {"조번호": no, "제목": clean(u.get("조문제목")), "장": cur_ch}
        if cur_sec:
            art["절"] = cur_sec
        if u.get("조문참고자료"):
            # 이동·삭제된 조문은 본문 없이 "[종전 제336조는 제333조로 이동]" 같은 안내만 남는다
            art["참고"] = clean(u["조문참고자료"])
        text = re.sub(r"^제\d+조(의\d+)?\s*(\([^)]*\))?\s*", "", body)
        if re.match(r"^삭제", text):
            art["삭제"] = True
            art["본문"] = text
            jomun.append(art)
            continue
        art["본문"] = text
        hangs = u.get("항")
        if hangs:
            hs = []
            for h in hangs if isinstance(hangs, list) else [hangs]:
                num = clean(h.get("항번호"))
                cont = clean(h.get("항내용"))
                if num and cont.startswith(num):
                    cont = cont[len(num):].strip()
                item = {"번호": num, "내용": cont}
                ho = split_ho(h.get("호")) if h.get("호") else []
                if ho:
                    item["호"] = ho
                hs.append(item)
            if hs:
                art["항"] = hs
        if u.get("조문시행일자"):
            art["조문시행일"] = fmt_date(u["조문시행일자"])
        jomun.append(art)
    name = info.get("법령명_한글")
    return {
        "법령명": name,
        "약칭": info.get("법령명약칭") or "",
        "법령구분": kind,
        "법령번호": "제%s호" % (info.get("공포번호") or "").lstrip("0"),
        "소관부처": dept,
        "공포일": fmt_date(info.get("공포일자")),
        "시행일": fmt_date(info.get("시행일자")),
        "출처": "국가법령정보센터 OPEN API (target=law, MST=%s), 수집일 %s" % (mst, time.strftime("%Y-%m-%d")),
        "링크": "https://www.law.go.kr/법령/" + urllib.parse.quote(name or ""),
        "조문": jomun,
        "별표": parse_byeolpyo(d.get("별표")),
    }


HEAD_RE = re.compile(r"^제(\d+)조(?:의(\d+))?\s*(?:\(([^)]*)\))?\s*")


MOK = "가나다라마바사아자차카타파하"
DATE_TAIL = re.compile(r"\d\.\s?$")   # "2020. 5. " 처럼 날짜 한가운데인지


def _find_marker(text, start, token):
    """token('3.', '나.', '②')이 실제 마커로 쓰인 위치. 없으면 -1."""
    i = start
    while True:
        i = text.find(token, i)
        if i < 0:
            return -1
        prev = text[i - 1] if i else ""
        nxt = text[i + len(token):i + len(token) + 1]
        bad = prev.isdigit() or (token[-1] == "." and nxt.isdigit() and not text[i:].startswith(token + " "))
        # 문장 끝의 '한다/된다/있다/없다'를 세 번째 목 '다.'로 자르지 않는다.
        # '전원다. …'처럼 앞 목이 명사로 끝나고 바로 다음 목이 붙는 원문도
        # 있으므로 한글 뒤라는 이유만으로 모든 목 기호를 제외하면 안 된다.
        if token == "다." and prev and prev in "한된있없":
            bad = True
        if not bad and not DATE_TAIL.search(text[max(0, i - 7):i]):
            return i
        i += 1


def _split_seq(text, tokens, least=2):
    """1. 2. 3. … 처럼 순번이 이어지는 마커만 잘라낸다. → (머리말, [조각…])"""
    cuts, pos = [], 0
    for t in tokens:
        i = _find_marker(text, pos, t)
        if i < 0:
            break
        cuts.append(i)
        pos = i + len(t)
    if len(cuts) < least:
        return text.strip(), []
    parts = [text[cuts[n]:(cuts[n + 1] if n + 1 < len(cuts) else len(text))].strip()
             for n in range(len(cuts))]
    return text[:cuts[0]].strip(), parts


def soften(t):
    """고시 본문은 항·호·목이 한 줄에 붙어 오므로 계층대로 줄을 나눈다.

    '하여야 한다.'의 '다.'를 목 기호로 잘못 읽지 않도록, 목은 그 호가
    '각 목'을 예고했을 때만 나눈다. 호·목 모두 순번이 이어질 때만 인정한다.
    """
    t = clean(t)
    if not t:
        return ""
    lines = []
    head, hangs = _split_seq(t, list(CIRCLED), least=1)
    for chunk in ([head] if head else []) + hangs:
        h2, hos = _split_seq(chunk, ["%d." % n for n in range(1, 41)])
        if h2:
            lines.append(h2)
        for ho in hos:
            if "각 목" in ho or "각목" in ho:
                h3, moks = _split_seq(ho, ["%s." % c for c in MOK])
                lines.append(h3)
                lines += ["  " + m for m in moks]
            else:
                lines.append(ho)
    return "\n".join(x for x in lines if x)


def parse_admrul(rid):
    d = api("lawService", "admrul", ID=rid)
    d = d[list(d)[0]]
    info = d.get("행정규칙기본정보", {})
    lines = d.get("조문내용") or []
    if isinstance(lines, str):
        lines = [lines]
    jomun, cur_ch, cur_sec = [], "", ""
    for raw in lines:
        s = clean(raw)
        if not s:
            continue
        if len(s) < 40 and re.match(r"^제\d+장", s):
            cur_ch, cur_sec = s, ""
            continue
        if len(s) < 40 and re.match(r"^제\d+(절|관)", s):
            cur_sec = s
            continue
        m = HEAD_RE.match(s)
        if m:
            no = "제%s조" % m.group(1) + ("의%s" % m.group(2) if m.group(2) else "")
            art = {"조번호": no, "제목": m.group(3) or "", "장": cur_ch, "본문": soften(s[m.end():])}
            if cur_sec:
                art["절"] = cur_sec
            jomun.append(art)
        elif jomun:
            jomun[-1]["본문"] = (jomun[-1]["본문"] + "\n" + soften(s)).strip()
        else:
            jomun.append({"조번호": "", "제목": "", "장": cur_ch, "본문": soften(s)})
    name = info.get("행정규칙명")
    return {
        "법령명": name,
        "약칭": "",
        "법령구분": info.get("행정규칙종류") or "고시",
        "법령번호": "제%s호" % (info.get("발령번호") or ""),
        "소관부처": info.get("소관부처명"),
        "공포일": fmt_date(info.get("발령일자")),
        "시행일": fmt_date(info.get("시행일자")),
        "출처": "국가법령정보센터 OPEN API (target=admrul, ID=%s), 수집일 %s" % (rid, time.strftime("%Y-%m-%d")),
        "링크": "https://www.law.go.kr/행정규칙/" + urllib.parse.quote(name or ""),
        "조문": jomun,
        "별표": parse_byeolpyo(d.get("별표")),
    }


def save(doc, subdir):
    path = os.path.join(ROOT, "data", subdir, doc["법령명"].replace("/", "_") + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print("  %-46s 조문 %3d · 별표 %2d · %4dKB"
          % (doc["법령명"], len(doc["조문"]), len(doc["별표"]), os.path.getsize(path) // 1024))


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    laws_changed = False
    for name in LAWS:
        if only and only not in name:
            continue
        print("[법령]", name)
        save(parse_law(search("law", name)["법령일련번호"]), "laws")
        laws_changed = True
    for name in NOTICES:
        if only and only not in name:
            continue
        print("[고시]", name)
        save(parse_admrul(search("admrul", name)["행정규칙일련번호"]), "notices")
    if laws_changed:
        from delegation import main as fetch_delegations
        fetch_delegations()


if __name__ == "__main__":
    main()
