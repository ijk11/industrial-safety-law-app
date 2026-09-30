# -*- coding: utf-8 -*-
"""얼마나 쓰이는지 본다.

    python scripts/usage.py          # 최근 14일
    python scripts/usage.py 30       # 최근 30일

앱은 Firestore 문서 하나의 숫자를 올릴 뿐이고, 그 숫자는 인증 없이 읽힌다.
누가·어디서·무엇을 봤는지는 아예 보내지 않으므로 여기서도 알 수 없다.

    stats/devices            한 번이라도 연 기기 수 (기기마다 평생 한 번)
    stats/install            홈 화면 앱으로 처음 열린 수 (설치를 마친 수)
    stats/daily-2026-09-04   그날 앱을 연 기기 수
    stats/ver-osh-abc123     그 판으로 갈아탄 기기 수

홈 화면에 추가해 앱으로 연 것만 센다 — 브라우저 탭은 저장이 이레 뒤 지워져 같은 기기가
되풀이해 잡히므로 아예 세지 않는다. 그래서 devices 와 install 은 이제 같은 것을 센다.

같은 기기가 하루에 여러 번 열어도 하루 한 번만 센다. 만들면서 여는 것(localhost)과
CI 는 세지 않는다. 사생활 보호 모드처럼 저장이 막힌 기기도 세지 않으므로,
실제 이용자는 여기 숫자보다 조금 더 많다고 보면 된다.
"""
import datetime, io, json, os, re, sys, urllib.request

PROJECT = "industrial-safety-law-app"
KEY = "AIzaSyBYl4dZZvZCIFwQ2ybgDh_plwj6VO4IL6M"
URL = ("https://firestore.googleapis.com/v1/projects/%s/databases/(default)"
       "/documents/stats?key=%s&pageSize=300" % (PROJECT, KEY))


def read():
    with urllib.request.urlopen(URL, timeout=30) as r:
        return json.loads(r.read().decode("utf-8")).get("documents", [])


def kst(ts):
    """Firestore 가 적어 둔 「만든 때」(UTC)를 한국 날짜로 끊는다.
    날짜별 집계도 한국 시각으로 끊으므로 여기서도 같게 맞춘다."""
    try:
        t = datetime.datetime.strptime((ts or "")[:16], "%Y-%m-%dT%H:%M")
    except ValueError:
        return ""
    return (t + datetime.timedelta(hours=9)).strftime("%Y-%m-%d")


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 14
    try:
        docs = read()
    except Exception as e:
        raise SystemExit("읽지 못했습니다: %s" % e)

    daily, vers, one = {}, {}, {"devices": 0, "install": 0}
    for d in docs:
        name = d["name"].rsplit("/", 1)[-1]
        n = int(d.get("fields", {}).get("n", {}).get("integerValue", 0))
        if name in one:
            one[name] = n
        elif re.match(r"^daily-\d{4}-\d{2}-\d{2}$", name):
            daily[name[6:]] = n
        elif name.startswith("ver-"):
            vers[name[4:]] = (n, kst(d.get("createTime", "")))

    if not daily:
        raise SystemExit("아직 집계된 날이 없습니다.")

    order = sorted(daily, reverse=True)[:days]
    wide = max(daily[k] for k in order) or 1
    print("\n날짜별로 앱을 연 기기 수\n")
    for k in order:
        n = daily[k]
        print("  %s  %4d  %s" % (k, n, "█" * max(1, round(n * 28 / wide))))

    got = sum(daily[k] for k in order)
    print("\n  최근 %d일 합계 %d · 하루 평균 %.1f" % (len(order), got, got / len(order)))

    print("\n한 번이라도 연 기기 %d · 홈 화면에 설치를 마친 기기 %d"
          % (one["devices"], one["install"]))
    print("  홈 화면 앱으로 연 것만 센다 — 브라우저 탭으로 열어 본 사람은 빠진다.")
    print("  그래서 두 숫자는 이제 같은 것을 센다 (바꾸기 전에 쌓인 몫만큼 벌어져 있다).")
    print("  앱을 지우고 다시 추가하면 새 기기로 센다.")
    print("  사생활 보호 모드는 아예 세지 않으니 실제로는 이보다 조금 더 많다.")

    if vers:
        print("\n판마다 갈아탄 기기 수")
        # 날짜 내림차순 — 판 이름(해시)에는 차례가 없어 날짜가 유일한 순서다
        for k in sorted(vers, key=lambda x: (vers[x][1], x), reverse=True):
            cnt, at = vers[k]
            print("  %-10s  %-14s %4d" % (at or "-", k, cnt))
        print("  날짜는 그 판이 처음 잡힌 때다 — 올린 때가 아니라 첫 기기가 갈아탄 때다.")
    print()


if __name__ == "__main__":
    main()
