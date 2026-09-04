# -*- coding: utf-8 -*-
"""번호 없는 위임 문구를 국가법령정보센터가 지정한 하위 조문에 연결한다.

python scripts/delegation.py  # data/laws의 판에 맞춰 연결 자료를 다시 받는다
https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsDelegated

XML은 같은 위임정보 안에서도 법령명과 조문정보가 번갈아 나온다. JSON으로
변환하면 이 순서가 사라지므로 XML의 형제 노드를 순서대로 읽는다.
"""
import hashlib
import json
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

from fetch_laws import BASE, OC, ROOT, _get, norm

PATH = Path(ROOT) / "data" / "delegations.json"
WORDS = {"고용노동부령", "대통령령"}


def fingerprint(doc):
    articles = [{k: v for k, v in a.items() if k not in {"위임", "벌"}}
                for a in doc["조문"]]
    raw = json.dumps(articles, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def article_no(number, branch=""):
    return "제%d조" % int(number) + ("의%d" % int(branch) if branch and int(branch) else "")


def parse(xml):
    law = ET.fromstring(xml).find("법령")
    if law is None or law.find("법령정보/법령명") is None:
        raise ValueError("위임 법령 API 응답에 법령정보가 없습니다")
    links = []
    for row in law.findall("위임조문정보"):
        info = row.find("조정보")
        no = article_no(info.findtext("조문번호"), info.findtext("조문가지번호"))
        for block in row.findall("위임정보"):
            name = ""
            for node in block:
                if node.tag == "위임구분":
                    name = ""
                elif node.tag == "위임법령제목":
                    name = node.text or ""
                elif node.tag == "위임법령조문정보":
                    word = node.findtext("링크텍스트")
                    num = node.findtext("위임법령조문번호")
                    if word not in WORDS or not name or not num or not int(num):
                        continue
                    links.append({
                        "조": no, "위치": node.findtext("조항호목") or "",
                        "문구": word, "문맥": node.findtext("라인텍스트") or "",
                        "법령": name,
                        "대상": article_no(num, node.findtext("위임법령조문가지번호")),
                        "제목": node.findtext("위임법령조문제목") or "",
                    })
    return law.findtext("법령정보/법령일련번호"), links


def fragments(a):
    """화면에 따로 그리는 본문·항·호와 법정 위치를 함께 낸다."""
    no = a["조번호"]
    if a.get("본문"):
        yield "본문", no, a["본문"]
    for i, h in enumerate(a.get("항", [])):
        hang = no + ("제%d항" % (i + 1) if h.get("번호") else "")
        if h.get("내용"):
            yield "항%d" % i, hang, h["내용"]
        for j, text in enumerate(h.get("호", [])):
            m = re.match(r"(\d+)(의\d+)?\.", text)
            if m:
                yield "항%d호%d" % (i, j), hang + "제%s호" % m[1] + (m[2] or ""), text


def spans(text, location, link):
    """같은 항에서 문구가 반복되면 API의 주변 문장으로 구별한다."""
    where = link["위치"]
    if where != location and not re.fullmatch(re.escape(location) + r"[가-하]목", where):
        return []
    lo, hi = 0, len(text)
    if where != location:
        mark = re.search(r"(?:^|\n)\s*" + where[-2] + r"\.\s", text)
        if not mark:
            return []
        lo = mark.end()
        nxt = re.search(r"\n\s*[가-하]\.\s", text[lo:])
        if nxt:
            hi = lo + nxt.start()
    # 공백·가운뎃점 표기 차이만 허용한다. 문맥이 사라지면 연결하지 않는다.
    chars = [(c.replace("ㆍ", "·"), i) for i, c in enumerate(text[lo:hi], lo) if not c.isspace()]
    compact = "".join(c for c, _ in chars)
    context = re.sub(r"\s", "", link["문맥"]).replace("ㆍ", "·")
    word = link["문구"]
    if not context or word not in context:
        return []
    out = []
    for m in re.finditer(re.escape(context), compact):
        for hit in re.finditer(re.escape(word), m[0]):
            start = m.start() + hit.start()
            end = start + len(word) - 1
            out.append((chars[start][1], chars[end][1] + 1))
    return out


def attach(docs):
    saved = json.loads(PATH.read_text(encoding="utf-8"))
    byname = {norm(d["법령명"]): (di, d) for di, d in enumerate(docs)}
    count = missing = 0
    for source in saved["법령"]:
        _, doc = byname[norm(source["법령명"])]
        if fingerprint(doc) != source["본문해시"]:
            raise ValueError("%s 원문이 바뀌었습니다. python scripts/delegation.py 로 위임 연결을 갱신하세요" % doc["법령명"])
        articles = {a["조번호"]: a for a in doc["조문"]}
        grouped = {}
        for link in source["연결"]:
            target = byname.get(norm(link["법령"]))
            a = articles.get(link["조"])
            if not target or not a or a.get("삭제"):
                missing += 1
                continue
            di, td = target
            ai = next((i for i, t in enumerate(td["조문"])
                       if t["조번호"] == link["대상"] and not t.get("삭제")
                       and norm(t.get("제목")) == norm(link["제목"])), None)
            if ai is None:
                missing += 1
                continue
            found = False
            for part, loc, text in fragments(a):
                for start, end in spans(text, loc, link):
                    slot = grouped.setdefault((link["조"], part, start, end), set())
                    slot.add((di, ai))
                    found = True
            if not found:
                missing += 1
        for (no, part, start, end), targets in sorted(grouped.items()):
            text = next(t for p, _, t in fragments(articles[no]) if p == part)
            articles[no].setdefault("위임", []).append({
                "부분": part, "시작": len(text[:start].encode("utf-16-le")) // 2,
                "끝": len(text[:end].encode("utf-16-le")) // 2,
                "대상": ["%d:j:%d" % t for t in sorted(targets)],
            })
            count += 1
    print("번호 없는 위임 문구 %d곳 연결 (대상·원문이 맞지 않는 자료 %d건 제외)" % (count, missing))


def main():
    records = []
    for path in sorted((Path(ROOT) / "data" / "laws").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        mst = re.search(r"MST=(\d+)", doc["출처"])[1]
        url = BASE + "lawService.do?" + urllib.parse.urlencode({
            "OC": OC, "target": "lsDelegated", "type": "XML", "MST": mst})
        got, links = parse(_get(url))
        if got != mst:
            raise ValueError("요청한 법령 판과 API 응답이 다릅니다: " + doc["법령명"])
        records.append({"법령명": doc["법령명"], "MST": mst,
                        "본문해시": fingerprint(doc), "연결": links})
        print(doc["법령명"], len(links), "건", flush=True)
    payload = {"출처": "국가법령정보센터 OPEN API (target=lsDelegated)",
               "수집일": time.strftime("%Y-%m-%d"), "법령": records}
    # 모두 받은 뒤 교체한다. 통신 실패로 기존 자료를 일부만 덮지 않는다.
    PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
