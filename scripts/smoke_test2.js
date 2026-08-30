(async () => {
  const out = [];
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && document.getElementById("boot"); i++) await wait(100);

  // 실제로 다른 조를 인용하는 조문을 골라 linkify 를 직접 시험한다
  const samples = [];
  for (const r of RECS) {
    if (r.kind !== 0) continue;
    if (/제\d+조/.test(r.body)) samples.push(r);
    if (samples.length >= 8) break;
  }
  out.push("인용 문구가 있는 조문 표본 " + samples.length + "개");
  for (const r of samples.slice(0, 6)) {
    const src = (DOCS[r.d].조문[r.i].본문 || "") ||
      ((DOCS[r.d].조문[r.i].항 || []).map(h => h.내용).join(" "));
    const html = linkify(esc(src), r.d);
    const n = (html.match(/class="ref"/g) || []).length;
    const hit = (src.match(/(?:「[^」]+」\s*)?(?:법|영|령|규칙)?\s*제\d+조(?:의\d+)?/g) || []).slice(0, 3);
    out.push((n > 0 ? "PASS " : "FAIL ") + DOCS[r.d].약호 + " " + r.no +
      " → 링크 " + n + "개 / 원문 인용 " + JSON.stringify(hit));
  }

  // 리더에서 실제 렌더된 앵커 확인
  const target = samples[0];
  openRec(target.key, "new"); await wait(300);
  const anchors = [...document.querySelectorAll("#rbody a.ref")];
  out.push((anchors.length ? "PASS " : "FAIL ") + "리더 화면 인용 앵커 " + anchors.length + "개 :: " +
    anchors.slice(0, 3).map(a => a.textContent).join(", "));
  if (anchors.length) {
    const before = document.querySelector("#rno").textContent;
    anchors[0].click(); await wait(300);
    const after = document.querySelector("#rno").textContent;
    out.push((after !== before ? "PASS " : "FAIL ") + "인용 눌러 이동 :: " + before.trim() + " → " + after.trim());
    history.back(); await wait(400);
    out.push((document.querySelector("#rno").textContent === before ? "PASS " : "FAIL ") + "뒤로 복귀");
  }

  // 별표 인용
  const r16 = RECS.find(r => DOCS[r.d].법령명 === "산업안전보건법 시행령" && r.no === "제16조");
  openRec(r16.key, "new"); await wait(300);
  const tblRefs = [...document.querySelectorAll("#rbody a.ref")].filter(a => /별표/.test(a.textContent));
  out.push((tblRefs.length ? "PASS " : "FAIL ") + "별표 인용 링크 " + tblRefs.length + "개");
  history.back(); await wait(300);

  // 필터가 실제 건수를 줄이는지 (표시 개수가 아니라 전체 건수로)
  const q = document.querySelector("#q");
  const setQ = async v => { q.value = v; q.dispatchEvent(new Event("input", {bubbles:true})); await wait(500); };
  await setQ("교육");
  const all = hits.length;
  [...document.querySelectorAll(".chip")].find(c => c.dataset.g === "고시").click(); await wait(400);
  const only = hits.length;
  out.push((only > 0 && only < all ? "PASS " : "FAIL ") + "구분 필터 :: 전체 " + all + "건 → 고시 " + only + "건");

  const el = document.createElement("pre"); el.id = "testout";
  el.textContent = out.join("\n"); document.body.appendChild(el);
})();
