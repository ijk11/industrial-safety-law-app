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

같은 기기가 하루에 여러 번 열어도 하루 한 번만 센다. 만들면서 여는 것(localhost)과
CI 는 세지 않는다. 사생활 보호 모드처럼 저장이 막힌 기기도 세지 않으므로,
실제 이용자는 여기 숫자보다 조금 더 많다고 보면 된다.
"""
import io, json, os, re, sys, urllib.request

PROJECT = "industrial-safety-law-app"
KEY = "AIzaSyBYl4dZZvZCIFwQ2ybgDh_plwj6VO4IL6M"
URL = ("https://firestore.googleapis.com/v1/projects/%s/databases/(default)"
       "/documents/stats?key=%s&pageSize=300" % (PROJECT, KEY))


def read():
    with urllib.request.urlopen(URL, timeout=30) as r:
        return json.loads(r.read().decode("utf-8")).get("documents", [])


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
            vers[name[4:]] = n

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

    print("\n한 번이라도 연 기기 %d · 그중 홈 화면에 설치를 마친 기기 %d"
          % (one["devices"], one["install"]))
    print("  기기 안 저장에 기대므로, 브라우저 자료를 지우면 새 기기로 센다.")
    print("  사생활 보호 모드는 아예 세지 않으니 실제로는 이보다 조금 더 많다.")

    if vers:
        print("\n판마다 갈아탄 기기 수")
        for k in sorted(vers, key=lambda x: -vers[x]):
            print("  %-22s %4d" % (k, vers[k]))
    print()


if __name__ == "__main__":
    main()
