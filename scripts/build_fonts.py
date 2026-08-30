# -*- coding: utf-8 -*-
"""앱에 넣을 글꼴을 만든다 (한 번만 돌리면 된다).

    python scripts/build_fonts.py

별표의 괘선표는 '한글·괘선 = 라틴 2칸'이 지켜져야 칸이 맞는다.
나눔고딕코딩이 그 규격에 정확히 맞지만 한자가 없어서, Noto Sans Mono CJK의
한자 글리프를 폭 1000으로 옮겨 붙인 뒤 실제 쓰는 글자만 남겨 woff2로 굽는다.
제목용 명조는 조문 제목·법령명에 나오는 글자만 서브셋한다.

산출물: web/fonts/*.woff2
"""
import io, os, sys, urllib.request

from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.subset import Subsetter, Options

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".fontcache")
OUT = os.path.join(ROOT, "web", "fonts")

SOURCES = {
    "NanumGothicCoding-Regular.ttf":
        "https://github.com/google/fonts/raw/main/ofl/nanumgothiccoding/NanumGothicCoding-Regular.ttf",
    "NanumMyeongjo-Bold.ttf":
        "https://github.com/google/fonts/raw/main/ofl/nanummyeongjo/NanumMyeongjo-Bold.ttf",
    "NotoSansMonoCJKkr-Regular.otf":
        "https://github.com/notofonts/noto-cjk/raw/main/Sans/Mono/NotoSansMonoCJKkr-Regular.otf",
}

# 화면에 늘 뜨는 글자 (검색 안내문, 버튼, 라벨 등)
UI_TEXT = (
    "산업안전보건법조문찾기검색목차저장별표서식자주찾는담긴법령최근본"
    "결과가없습니다낱말을줄이거나처럼번호로또는앞에붙여보세요"
    "아직조문을열고오른쪽위책갈피누르면현장에서자주보는모아둘수있습니다"
    "이전다음원문확인표크기법령을고르세요목록시행공포소관부처"
    "밝기전환지우기뒤로개조문건더보기이동삭제본문없는입니다"
    "준비중원문전체를기기안펼치처음한번만걸립니다"
    "브라우저업데이트해주세요최신크롬사파리버전열어실패했"
    "국가법령정보센터그대로담았법적효력은있으며개정여부확인하세요"
    "설치오프라인모두받았어요새판올라왔다시열면바뀝니다"
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    "·ㆍ~-—()[]{}<>「」『』“”‘’.,:;!?%/＋+±×÷=∼≒℃㎎㎏㎥㎡№§①②③④⑤⑥⑦⑧⑨⑩ →←›…"
)


def fetch(name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if os.path.exists(path) and os.path.getsize(path) > 100000:
        return path
    print("  내려받는 중:", name)
    req = urllib.request.Request(SOURCES[name], headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(path, "wb") as f:
        f.write(r.read())
    return path


def charsets():
    """데이터에 실제로 나오는 글자만 모은다. (본문용, 제목용)"""
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_app as B
    docs = B.slim(B.collect())
    body, title = set(UI_TEXT), set(UI_TEXT)
    for d in docs:
        for k in ("법령명", "약칭", "법령구분", "소관부처", "법령번호"):
            title |= set(d.get(k) or "")
        for a in d["조문"]:
            title |= set((a.get("조번호") or "") + (a.get("제목") or "")
                         + (a.get("장") or "") + (a.get("절") or ""))
            body |= set((a.get("본문") or "") + (a.get("참고") or ""))
            for h in a.get("항", []):
                body |= set(h.get("내용") or "")
                for x in h.get("호", []):
                    body |= set(x)
        for b in d["별표"]:
            title |= set(b["번호"] + b["제목"])
            body |= set(b["내용"] + b["제목"])
    body |= title
    return body, title


# 어느 글꼴에도 없지만 같은 모양·같은 폭의 글자로 대신할 수 있는 것들
ALIAS = {0x223C: 0xFF5E}   # ∼(닮음 기호) → ～(전각 물결표)


def graft_hanja(target_path, donor_path, wanted):
    """나눔고딕코딩에 없는 글자를 Noto에서 옮겨 붙인다. 폭은 1000(=라틴 2칸)으로 맞춘다."""
    font = TTFont(target_path)
    cmap = font.getBestCmap()
    missing = sorted(c for c in wanted if ord(c) not in cmap)
    if not missing:
        return font, []
    donor = TTFont(donor_path)
    dcmap, dset = donor.getBestCmap(), donor.getGlyphSet()
    glyf, hmtx = font["glyf"], font["hmtx"]
    order = list(font.getGlyphOrder())
    added, skipped = [], []
    for ch in missing:
        src = dcmap.get(ord(ch))
        if not src:
            skipped.append(ch)
            continue
        name = "uni%04X" % ord(ch)
        if name in glyf.glyphs:
            skipped.append(ch)
            continue
        pen = TTGlyphPen(None)
        dset[src].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
        glyf.glyphs[name] = pen.glyph()
        hmtx.metrics[name] = (1000, donor["hmtx"].metrics[src][1])
        order.append(name)
        for t in font["cmap"].tables:
            t.cmap[ord(ch)] = name
        added.append(ch)
    cmap = font.getBestCmap()
    for cp, alt in ALIAS.items():
        if cp not in cmap and alt in cmap:
            for t in font["cmap"].tables:
                t.cmap[cp] = cmap[alt]
            added.append(chr(cp))
    font.setGlyphOrder(order)
    font["maxp"].numGlyphs = len(order)
    return font, added if not skipped else added


def bake(font, chars, out_name, family):
    opt = Options()
    opt.layout_features = ["*"]
    opt.name_IDs = [1, 2, 3, 4, 6]
    opt.notdef_outline = True
    opt.recalc_bounds = True
    opt.drop_tables += ["FFTM"]
    sub = Subsetter(options=opt)
    sub.populate(text="".join(sorted(chars)))
    sub.subset(font)
    font.flavor = "woff2"
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, out_name)
    font.save(path)
    print("  %-28s %s  글자 %d자  %dKB" % (out_name, family, len(chars), os.path.getsize(path) // 1024))
    return path


def main():
    body, title = charsets()
    print("본문용 %d자 · 제목용 %d자" % (len(body), len(title)))

    donor = fetch("NotoSansMonoCJKkr-Regular.otf")
    f, added = graft_hanja(fetch("NanumGothicCoding-Regular.ttf"), donor, body)
    print("  한자 등 이식: %d자" % len(added))
    bake(f, body, "mono.woff2", "표·별표용 고정폭")

    bake(TTFont(fetch("NanumMyeongjo-Bold.ttf")), title, "serif-bold.woff2", "제목용 명조")

    # 실제로 빠진 글자가 남았는지 확인
    chk = TTFont(os.path.join(OUT, "mono.woff2"))
    left = [c for c in body if ord(c) not in chk.getBestCmap()]
    print("최종 미수록 글자 %d자: %s" % (len(left), "".join(sorted(left))))


if __name__ == "__main__":
    main()
