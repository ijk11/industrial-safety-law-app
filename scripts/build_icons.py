# -*- coding: utf-8 -*-
"""홈 화면 아이콘을 그린다 (한 번만 돌리면 된다).

    python scripts/build_icons.py

안전모 실루엣. 아이폰은 아이콘을 스스로 둥글게 깎으므로 배경을 꽉 채워 그린다.
산출물: web/icons/*.png
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "icons")

GREEN = (14, 107, 69)
WHITE = (255, 255, 255)


def helmet(size, pad):
    """안전모: 돔 + 챙 + 세로 능선. pad는 0~1 (아이콘 안쪽 여백 비율)."""
    S = 4  # 안티에일리어싱용 확대 배율
    im = Image.new("RGB", (size * S, size * S), GREEN)
    d = ImageDraw.Draw(im)
    c = size * S
    m = c * pad                      # 여백
    w = c - 2 * m                    # 그림 영역

    cx = c / 2
    brim_y = m + w * 0.70            # 챙의 중심선
    dome_w = w * 0.62
    dome_h = w * 0.44

    # 돔 — 반원의 평평한 아래쪽이 챙에 정확히 닿도록 상자를 챙 기준 대칭으로 잡는다
    d.pieslice([cx - dome_w / 2, brim_y - dome_h, cx + dome_w / 2, brim_y + dome_h],
               180, 360, fill=WHITE)
    # 챙 — 돔 밑동을 살짝 덮는 납작한 타원
    brim_w, brim_h = w * 0.92, w * 0.135
    d.ellipse([cx - brim_w / 2, brim_y - brim_h * 0.55, cx + brim_w / 2, brim_y + brim_h * 0.45],
              fill=WHITE)
    # 능선 두 줄 — 초록을 파내어 안전모의 골을 만든다 (챙 위에서 끝난다)
    rib_w = w * 0.05
    for off in (-dome_w * 0.26, dome_w * 0.26):
        d.rounded_rectangle(
            [cx + off - rib_w / 2, brim_y - dome_h * 0.90,
             cx + off + rib_w / 2, brim_y - brim_h * 0.60],
            radius=rib_w / 2, fill=GREEN)

    return im.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    plan = [
        ("icon-180.png", 180, 0.14),   # 아이폰 홈 화면
        ("icon-192.png", 192, 0.14),
        ("icon-512.png", 512, 0.14),
        ("icon-maskable-512.png", 512, 0.24),  # 안드로이드가 더 깎아내도 남도록 여백을 더 준다
    ]
    for name, size, pad in plan:
        p = os.path.join(OUT, name)
        helmet(size, pad).save(p, "PNG", optimize=True)
        print("  %-24s %3dpx  %dKB" % (name, size, os.path.getsize(p) // 1024))


if __name__ == "__main__":
    main()
