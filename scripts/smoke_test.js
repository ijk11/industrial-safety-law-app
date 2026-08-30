(async () => {
  const out = [];
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const ok = (name, cond, extra) => out.push((cond ? "PASS " : "FAIL ") + name + (extra ? " :: " + extra : ""));
  const $$ = s => document.querySelector(s);
  const type = async (v) => {
    const q = $$("#q"); q.value = v;
    q.dispatchEvent(new Event("input", { bubbles: true }));
    await wait(500);
  };
  const cards = () => [...document.querySelectorAll("#v-search .card")];
  const txt = el => (el ? el.textContent.replace(/\s+/g, " ").trim() : "");

  for (let i = 0; i < 200 && document.getElementById("boot"); i++) await wait(100);
  ok("부팅 완료", !document.getElementById("boot"));
  ok("법령 29건 적재", typeof DOCS !== "undefined" && DOCS.length === 29, typeof DOCS !== "undefined" ? DOCS.length : "DOCS 없음");
  ok("색인 2532건 내외", typeof RECS !== "undefined" && RECS.length > 2400, typeof RECS !== "undefined" ? RECS.length : "-");

  await type("추락");
  ok("낱말 검색 결과 있음", cards().length > 0, cards().length + "건 표시");
  ok("검색어 강조", !!$$("#v-search mark"));
  ok("첫 결과에 검색어 포함", /추락/.test(txt(cards()[0])), txt(cards()[0]).slice(0, 50));

  await type("38");
  ok("번호 바로가기 → 법 제38조", /제38조/.test(txt(cards()[0])) && /안전조치/.test(txt(cards()[0])), txt(cards()[0]).slice(0, 40));

  await type("령 16");
  ok("법령 지정 바로가기 → 령 제16조", /제16조/.test(txt(cards()[0])) && /안전관리자/.test(txt(cards()[0])), txt(cards()[0]).slice(0, 40));

  await type("도급인 안전조치");
  ok("여러 낱말 AND 검색", cards().length > 0, cards().length + "건");

  // 조문 열기
  await type("38");
  cards()[0].click(); await wait(300);
  ok("리더 열림", !$$("#reader").hidden);
  const body = txt($$("#rbody"));
  ok("항·호 본문 표시", /사업주는 다음 각 호/.test(body), body.slice(0, 60));
  ok("조문 아래 원문 링크", !!$$("#rbody a[href*='law.go.kr']"));

  // 인용 따라가기 — 실제로 다른 조를 인용하는 조문으로 시험한다
  await type("5"); 
  const c5 = cards().find(c => /법제5조|법 제5조/.test(txt(c).replace(/\s/g,"")) ) || cards()[0];
  c5.click(); await wait(300);
  const refs2 = [...document.querySelectorAll("#rbody a.ref")];
  ok("인용 링크 생성", refs2.length > 0, "제5조 " + refs2.length + "개: " + refs2.slice(0,3).map(a=>a.textContent).join(","));
  if (refs2.length) {
    const before = txt($$("#rno"));
    refs2[0].click(); await wait(350);
    ok("인용 눌러 이동", txt($$("#rno")) !== before, before + " → " + txt($$("#rno")));
    history.back(); await wait(450);
    ok("뒤로가기로 복귀", txt($$("#rno")) === before, txt($$("#rno")));
  }

  // 별표
  history.back(); await wait(300);
  await type("별표 3");
  const tbl = cards().find(c => /별표/.test(txt(c)));
  ok("별표 검색", !!tbl, txt(cards()[0]).slice(0, 40));
  if (tbl) {
    tbl.click(); await wait(400);
    const pre = $$("#rbody pre.tbl");
    ok("별표 괘선표 표시", !!pre && /[┌│├─]/.test(pre.textContent), pre ? pre.textContent.slice(0, 30) : "-");
    const rows = pre ? pre.textContent.split("\n").filter(l => /[│┌├]/.test(l)) : [];
    ok("괘선 줄 다수", rows.length > 3, rows.length + "줄");
    history.back(); await wait(300);
  }

  // 필터 칩
  const chip = [...document.querySelectorAll(".chip")].find(c => c.dataset.g === "고시");
  await type("교육"); const beforeN = hits.length;
  chip.click(); await wait(400);
  ok("구분 필터 동작", hits.length > 0 && hits.length < beforeN, "전체 " + beforeN + "건 → 고시 " + hits.length + "건");
  [...document.querySelectorAll(".chip")].find(c => c.dataset.g === "전체").click(); await wait(300);

  // 목차
  document.querySelector('nav.tabs button[data-tab="index"]').click(); await wait(300);
  ok("목차: 법령 목록", document.querySelectorAll("#v-index .row").length >= 29, document.querySelectorAll("#v-index .row").length + "건");
  document.querySelector("#v-index [data-doc]").click(); await wait(400);
  ok("목차: 조문 격자", document.querySelectorAll("#v-index .artgrid button").length > 100,
     document.querySelectorAll("#v-index .artgrid button").length + "개");
  ok("목차: 장 제목", !!document.querySelector("#v-index .chap"));

  // 저장
  document.querySelector('nav.tabs button[data-tab="search"]').click(); await wait(200);
  await type("38"); cards()[0].click(); await wait(300);
  $$("#rstar").click(); await wait(150);
  ok("책갈피 저장", $$("#rstar").classList.contains("on"));
  history.back(); await wait(300);
  document.querySelector('nav.tabs button[data-tab="saved"]').click(); await wait(300);
  ok("저장 탭에 표시", document.querySelectorAll("#v-saved .card").length > 0);

  // 뒤로가기 — 홈 화면에 설치하면 브라우저 버튼이 없어서 쓸어넘기기가 유일한 뒤로가기다.
  // 온 길이 전부 히스토리에 남아야 한 단계씩 되짚고 마지막에 앱을 나간다.
  const curTab = () => {
    const b = document.querySelector('nav.tabs button[aria-selected="true"]');
    return b ? b.dataset.tab : "(없음)";
  };
  document.querySelector('nav.tabs button[data-tab="search"]').click(); await wait(250);
  document.querySelector('nav.tabs button[data-tab="index"]').click(); await wait(350);
  document.querySelector('nav.tabs button[data-tab="saved"]').click(); await wait(350);
  history.back(); await wait(350);
  ok("뒤로가기: 탭 한 단계", curTab() === "index", curTab());
  history.back(); await wait(350);
  ok("뒤로가기: 탭 두 단계", curTab() === "search", curTab());

  document.querySelector('nav.tabs button[data-tab="index"]').click(); await wait(350);
  /* 앞 검사가 법령 하나를 열어 둔 채로 왔을 수 있다. 목록 상태로 맞추고 시작한다 */
  if (document.querySelector("#idxback")) { document.querySelector("#idxback").click(); await wait(450); }
  ok("목차: 빵부스러기로 법령 목록 복귀", !!document.querySelector("#v-index [data-doc]"));
  document.querySelector("#v-index [data-doc]").click(); await wait(450);
  ok("뒤로가기: 목차 안으로 진입", !!document.querySelector("#idxback"));
  history.back(); await wait(450);
  ok("뒤로가기: 목차 법령 목록 복귀",
     !document.querySelector("#idxback") && document.querySelectorAll("#v-index .row").length >= 29,
     document.querySelectorAll("#v-index .row").length + "건");

  document.querySelector('nav.tabs button[data-tab="search"]').click(); await wait(250);
  await type("38"); cards()[0].click(); await wait(400);
  const a0 = txt($$("#rno"));
  $$("#next").click(); await wait(400);
  const a1 = txt($$("#rno"));
  $$("#next").click(); await wait(400);
  ok("이전/다음 조문 이동", a0 !== a1 && txt($$("#rno")) !== a1,
     a0 + " → " + a1 + " → " + txt($$("#rno")));
  history.back(); await wait(450);
  ok("뒤로가기: 다음 조문 한 단계", !$$("#reader").hidden && txt($$("#rno")) === a1, txt($$("#rno")));
  history.back(); await wait(450);
  ok("뒤로가기: 처음 본 조문으로", !$$("#reader").hidden && txt($$("#rno")) === a0, txt($$("#rno")));
  history.back(); await wait(450);
  ok("뒤로가기: 조문 닫힘", $$("#reader").hidden);

  // 법령 판 — 언제 받아온 원문인지 밝히는 칸
  document.querySelector('nav.tabs button[data-tab="saved"]').click(); await wait(400);
  const stamp = txt($$("#stamp"));
  ok("헤더에 업데이트 날짜", /^업데이트 \d{4}-\d{2}-\d{2}$/.test(stamp), stamp);
  const vb = $$(".verbox");
  ok("저장 탭에 법령 판 칸", !!vb && /업데이트/.test(txt(vb)), vb ? txt(vb).slice(0, 60) : "-");
  ok("법령 판에 담긴 법령 수", !!vb && new RegExp(DOCS.length + "건").test(txt(vb)),
     vb ? txt(vb).slice(0, 90) : "-");
  ok("법령 판에 가장 늦은 시행일", !!vb && /가장 늦은 시행일 \d{4}-\d{2}-\d{2}/.test(txt(vb)));
  ok("법령 업데이트 버튼", !!$$(".verbtn"), $$(".verbtn") ? txt($$(".verbtn")) : "-");

  // 조문 상단 시행일
  document.querySelector('nav.tabs button[data-tab="search"]').click(); await wait(250);
  await type("38"); cards()[0].click(); await wait(400);
  const rw = $$("#rbody .rwhen");
  ok("조문 상단에 시행일", !!rw && /^(이 조문 )?시행 \d{4}-\d{2}-\d{2}$/.test(txt(rw)), txt(rw));
  const bodyEl = $$("#rbody");
  ok("아래 중복 시행일 없음", !!bodyEl && !/이 조문의 시행일/.test(txt(bodyEl)));
  history.back(); await wait(400);

  // 괘선 없는 별표는 상자를 벗기고 접혀서 나온다
  const flowRec = RECS.find(r => r.kind === 1 && r.flow);
  ok("접히는 별표 있음", !!flowRec, flowRec ? DOCS[flowRec.d].법령명 + " " + flowRec.no : "-");
  if (flowRec) {
    openRec(flowRec.key, "new"); await wait(450);
    ok("괘선 없는 별표는 문단으로", !!$$("#rbody .tbltext") && !$$("#rbody pre.tbl"));
    ok("괘선 문자가 남지 않음", !/[─-╋]/.test(txt($$("#rbody .tbltext"))));
    history.back(); await wait(400);
  }
  const BOXCH = "│┃─━┌┬┐├┼┤└┴┘┏┳┓┣╋┫┗┻┛┠┨".split("");
  const gridRec = RECS.find(r => r.kind === 1 && r.ps);
  ok("괘선표를 진짜 표로 푼 것 있음", !!gridRec,
     gridRec ? DOCS[gridRec.d].법령명 + " " + gridRec.no : "-");
  if (gridRec) {
    openRec(gridRec.key, "new"); await wait(500);
    const g = $$("#rbody table.grid");
    ok("표 태그로 그려짐", !!g && g.rows.length > 1 && g.rows[0].cells.length > 1,
       g ? g.rows.length + "행 " + g.rows[0].cells.length + "열" : "-");
    ok("표 안에 괘선 문자 없음", !!g && !BOXCH.some(c => txt(g).indexOf(c) >= 0));
    ok("표에 빈 칸만 있지 않음", !!g && txt(g).length > 20, g ? txt(g).slice(0, 50) : "-");
    history.back(); await wait(400);
  }
  const rawRec = RECS.find(r => r.kind === 1 && !r.flow && !r.ps);
  if (rawRec) {
    openRec(rawRec.key, "new"); await wait(450);
    ok("못 푼 표는 원문 그대로", !!$$("#rbody pre.tbl"));
    history.back(); await wait(400);
  }

  // 글꼴
  try {
    await document.fonts.ready;
    ok("고정폭 글꼴 적재", document.fonts.check('12px "OSH Mono"') || document.fonts.check('12px "Nanum Gothic Coding"'));
  } catch (e) { ok("고정폭 글꼴 적재", false, e.message); }

  const el = document.createElement("pre");
  el.id = "testout";
  el.textContent = out.join("\n");
  document.body.appendChild(el);
  document.title = "TEST " + out.filter(l => l.startsWith("FAIL")).length + " FAIL / " + out.length;
})();
