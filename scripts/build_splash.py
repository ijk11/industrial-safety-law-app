# -*- coding: utf-8 -*-
"""아이폰 홈 화면에서 열 때 뜨는 실행 화면을 그린다.

    python scripts/build_splash.py

iOS는 PWA에 splash 이미지를 지정하지 않으면 흰 화면을 잠깐 보여 준다.
기기 크기마다 정확히 맞는 그림을 요구하므로, 쓰는 기기 크기별로 밝은 판·어두운 판을 굽는다.
산출물: web/splash/*.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "splash")
FONT = os.path.join(ROOT, ".fontcache", "NanumMyeongjo-Bold.ttf")

# (논리 너비, 논리 높이, 배율) — 지금 쓰이는 아이폰들
DEVICES = [
    (440, 956, 3),   # 16 Pro Max
    (430, 932, 3),   # 15/14 Pro Max
    (402, 874, 3),   # 16 Pro
    (393, 852, 3),   # 15 · 15 Pro · 14 Pro
    (390, 844, 3),   # 14 · 13 · 12
    (375, 812, 3),   # 13 mini · 12 mini · X · XS · 11 Pro
    (414, 896, 3),   # XS Max · 11 Pro Max
    (414, 896, 2),   # XR · 11
    (375, 667, 2),   # SE(2·3세대) · 8
]

THEMES = {
    "light": {"bg": (247, 248, 246), "fg": (14, 107, 69), "sub": (120, 131, 124), "mark": (255, 255, 255)},
    "dark":  {"bg": (15, 20, 18),    "fg": (79, 207, 151), "sub": (126, 139, 132), "mark": (8, 20, 14)},
}


def helmet(d, cx, cy, w, color):
    """아이콘과 같은 안전모를 그린다."""
    brim_y = cy + w * 0.20
    dome_w, dome_h = w * 0.62, w * 0.44
    d.pieslice([cx - dome_w / 2, brim_y - dome_h, cx + dome_w / 2, brim_y + dome_h], 180, 360, fill=color)
    brim_w, brim_h = w * 0.92, w * 0.135
    d.ellipse([cx - brim_w / 2, brim_y - brim_h * 0.55, cx + brim_w / 2, brim_y + brim_h * 0.45], fill=color)


def draw(px, py, theme):
    c = THEMES[theme]
    S = 2
    im = Image.new("RGB", (px * S, py * S), c["bg"])
    d = ImageDraw.Draw(im)
    cx, cy = px * S / 2, py * S / 2
    box = px * S * 0.22

    # 아이콘 타일 (둥근 사각형 + 안전모)
    r = box * 0.24
    d.rounded_rectangle([cx - box / 2, cy - box * 0.9, cx + box / 2, cy + box * 0.1], radius=r, fill=c["fg"])
    helmet(d, cx, cy - box * 0.42, box * 0.60, c["mark"])

    try:
        f1 = ImageFont.truetype(FONT, int(box * 0.20))
        f2 = ImageFont.truetype(FONT, int(box * 0.105))
        d.text((cx, cy + box * 0.42), "산안법 조문 찾기", font=f1, fill=c["fg"], anchor="mm")
        d.text((cx, cy + box * 0.68), "오프라인", font=f2, fill=c["sub"], anchor="mm")
    except OSError:
        pass  # 글꼴이 없으면 그림만

    # 색이 몇 가지 안 되는 그림이라 팔레트로 바꾸면 용량이 크게 준다
    return im.resize((px, py), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE, colors=64)


def main():
    os.makedirs(OUT, exist_ok=True)
    entries = []
    for w, h, scale in DEVICES:
        for theme in THEMES:
            px, py = w * scale, h * scale
            name = "splash-%dx%d@%dx-%s.png" % (w, h, scale, theme)
            draw(px, py, theme).save(os.path.join(OUT, name), "PNG", optimize=True)
            media = ("(device-width: %dpx) and (device-height: %dpx) and "
                     "(-webkit-device-pixel-ratio: %d) and (orientation: portrait)" % (w, h, scale))
            if theme == "dark":
                media += " and (prefers-color-scheme: dark)"
            entries.append((media, "splash/" + name))
    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print("실행 화면 %d장 · %dKB" % (len(entries), total // 1024))
    return entries


if __name__ == "__main__":
    main()
