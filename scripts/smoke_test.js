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

  for (let i = 0; i < 600 && document.getElementById("boot"); i++) await wait(100);
  ok("부팅 완료", !document.getElementById("boot"));
  ok("법령 32건 적재", typeof DOCS !== "undefined" && DOCS.length === 32, typeof DOCS !== "undefined" ? DOCS.length : "DOCS 없음");
  ok("색인 2641건 내외", typeof RECS !== "undefined" && RECS.length > 2500, typeof RECS !== "undefined" ? RECS.length : "-");
  for (const nm of ["중대재해 처벌 등에 관한 법률", "중대재해 처벌 등에 관한 법률 시행령",
                    "근로감독관 집무규정(산업안전보건)"]) {
    const d = DOCS.find(x => x.법령명 === nm);
    ok("담김: " + nm, !!d && d.조문.length > 10, d ? d.약호 + " · 조문 " + d.조문.length : "없음");
  }

  await type("추락");
  ok("낱말 검색 결과 있음", cards().length > 0, cards().length + "건 표시");
  ok("검색어 강조", !!$$("#v-search mark"));
  ok("첫 결과에 검색어 포함", /추락/.test(txt(cards()[0])), txt(cards()[0]).slice(0, 50));

  await type("38");
  ok("번호 바로가기 → 법 제38조", /제38조/.test(txt(cards()[0])) && /안전조치/.test(txt(cards()[0])), txt(cards()[0]).slice(0, 40));

  await type("령 16");
  ok("법령 지정 바로가기 → 령 제16조", /제16조/.test(txt(cards()[0])) && /안전관리자/.test(txt(cards()[0])), txt(cards()[0]).slice(0, 40));

  await type("중대재해 4");
  ok("중대재해처벌법 바로가기 → 제4조", /제4조/.test(txt(cards()[0])) && /확보의무/.test(txt(cards()[0])), txt(cards()[0]).slice(0, 40));

  await type("감독규정 16");
  ok("집무규정 바로가기 → 제16조", /제16조/.test(txt(cards()[0])), txt(cards()[0]).slice(0, 40));

  await type("중대재해처벌법");
  ok("법령 이름만 치면 그 법령을 펼침",
     hits.length > 10 && hits.every(r => DOCS[r.d].법령명 === "중대재해 처벌 등에 관한 법률"),
     hits.length + "건 · 첫 결과 " + txt(cards()[0]).slice(0, 24));

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

  // 인용을 어느 법으로 푸는가 — 짧게 부른 이름은 읽고 있는 법령의 계열 안에서 풀어야 한다
  {
    const ci = DOCS.findIndex(d => d.법령명 === "중대재해 처벌 등에 관한 법률 시행령");
    const one = linkify(esc("법 제4조제1항"), ci);
    const key = (one.match(/data-key="([^"]+)"/) || [])[1];
    const to = key ? BYKEY.get(key) : null;
    ok("중대재해령의 '법'은 중대재해처벌법", !!to && DOCS[to.d].법령명 === "중대재해 처벌 등에 관한 법률",
       to ? DOCS[to.d].약호 + " " + to.no : "링크 없음");

    const far = linkify(esc("「화학물질관리법」 제9조제1항의 정보(같은 법 제52조제1항)"), 0);
    ok("담지 않은 법의 '같은 법'은 링크 없음", !/class="ref"/.test(far), far.slice(0, 70));

    const near = linkify(esc("「산업안전보건법」 제24조 및 같은 법 제64조"), 0);
    ok("'같은 법'은 앞서 부른 법으로", (near.match(/class="ref"/g) || []).length === 2, near.slice(0, 110));

    /* 별표도 앞에 붙은 이름을 봐야 한다 — 시행규칙 안의 "영 별표 7" 은 시행령의 별표다 */
    const ri = DOCS.findIndex(d => d.법령명 === "산업안전보건법 시행규칙");
    const tb = linkify(esc("영 별표 7에 따른 인력"), ri);
    const tk = (tb.match(/data-key="([^"]+)"/) || [])[1];
    const trg = tk ? BYKEY.get(tk) : null;
    ok("별표 인용도 법령을 가려서", !!trg && DOCS[trg.d].법령명 === "산업안전보건법 시행령" && trg.no === "별표 7",
       trg ? DOCS[trg.d].약호 + " " + trg.no : "링크 없음");

    const own = linkify(esc("별표 5의 교육내용"), ri);
    const ok2 = BYKEY.get((own.match(/data-key="([^"]+)"/) || [])[1]);
    ok("이름 없는 별표는 읽고 있는 법령", !!ok2 && ok2.d === ri && ok2.no === "별표 5",
       ok2 ? DOCS[ok2.d].약호 + " " + ok2.no : "링크 없음");
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
  ok("목차: 시행일과 공포일",
     [...document.querySelectorAll("#v-index .row .s")].every(e => /시행 \d{4}-\d{2}-\d{2} · 공포 \d{4}-\d{2}-\d{2}/.test(txt(e))),
     txt(document.querySelector("#v-index .row .s")));
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
  await type(""); await wait(400);
  const head = $$("#savefold");
  ok("검색 첫 화면에 저장한 조문", !!head && /저장한 조문 1/.test(txt(head)), head ? txt(head) : "머리 없음");
  ok("저장 카드가 보임", document.querySelectorAll("#v-search .list .card").length > 0);
  ok("자주 찾는 조문은 없앰", !$$("#v-search .quick"));
  /* 저장이 쌓이면 화면을 다 먹으므로 접을 수 있어야 한다 */
  const before = document.querySelectorAll("#v-search .list .card").length;
  head.click(); await wait(350);
  ok("저장한 조문 접기", document.querySelectorAll("#v-search .list .card").length < before,
     before + "장 → " + document.querySelectorAll("#v-search .list .card").length + "장");
  await type("38"); await type(""); await wait(400);
  ok("접은 것을 기억함", document.querySelectorAll("#v-search .list .card").length < before);
  $$("#savefold").click(); await wait(350);
  ok("다시 펴기", document.querySelectorAll("#v-search .list .card").length === before);

  // 뒤로가기 — 홈 화면에 설치하면 브라우저 버튼이 없어서 쓸어넘기기가 유일한 뒤로가기다.
  // 온 길이 전부 히스토리에 남아야 한 단계씩 되짚고 마지막에 앱을 나간다.
  const curTab = () => {
    const b = document.querySelector('nav.tabs button[aria-selected="true"]');
    return b ? b.dataset.tab : "(없음)";
  };
  document.querySelector('nav.tabs button[data-tab="search"]').click(); await wait(250);
  document.querySelector('nav.tabs button[data-tab="index"]').click(); await wait(350);
  document.querySelector('nav.tabs button[data-tab="adv"]').click(); await wait(350);
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
  const stamp = txt($$("#stamp"));
  ok("헤더에 업데이트 날짜", /^업데이트 \d{4}-\d{2}-\d{2}$/.test(stamp), stamp);
  ok("탭은 검색·목차·기타 셋", document.querySelectorAll("nav.tabs button").length === 3,
     [...document.querySelectorAll("nav.tabs button")].map(b => txt(b)).join("/"));

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

  // 형광펜 — 찾던 낱말은 조문을 열어도 남아 있어야 한다
  await type("추락 방지");
  cards()[0].click(); await wait(400);
  const marks = document.querySelectorAll("#rbody mark");
  ok("조문에 형광펜 남음", marks.length > 0, marks.length + "곳");
  ok("형광펜이 찾던 낱말", [...marks].every(m => /추락|방지/.test(m.textContent)));
  ok("인용 링크 안 깨짐", document.querySelectorAll("#rbody a.ref").length >= 0 && !!$$("#rbody .art"));
  ok("형광펜 단추 보임", !$$("#rhl").hidden);
  $$("#next").click(); await wait(450);
  ok("조문을 옮겨도 형광펜 남음", document.querySelectorAll("#rbody mark").length > 0);
  $$("#rhl").click(); await wait(250);
  ok("단추를 누르면 형광펜 걷힘", document.querySelectorAll("#rbody mark").length === 0);
  ok("걷은 뒤 단추도 사라짐", $$("#rhl").hidden);
  $$("#next").click(); await wait(450);
  ok("걷은 뒤엔 다시 칠하지 않음", document.querySelectorAll("#rbody mark").length === 0);
  history.back(); await wait(400); history.back(); await wait(400); history.back(); await wait(450);
  await type("38"); cards()[0].click(); await wait(400);
  ok("번호로 찾아간 조문엔 형광펜 없음", document.querySelectorAll("#rbody mark").length === 0);
  history.back(); await wait(400);

  // 제12장 벌칙·과태료 — 조문 밑에 붙는다
  await type("법 38"); cards()[0].click(); await wait(450);
  const pens = [...document.querySelectorAll("#rbody .pen")];
  ok("제38조에 형벌 붙음", pens.length >= 2, pens.length + "개");
  ok("사망 시 가중형도 함께", pens.some(e => /7년 이하의 징역/.test(txt(e))));
  ok("형벌이 항 밑에 붙음",
     !!document.querySelector("#rbody .hang + .pen"), "제1항 다음 자리");
  history.back(); await wait(400);

  await type("법 15"); cards()[0].click(); await wait(450);
  const fine = $$("#rbody .pen");
  ok("제15조에 과태료 붙음", !!fine && /과태료/.test(txt(fine)));
  const more = $$("#rbody [data-pen]");
  ok("경우별 과태료는 접혀 있음", !!more && $$("#" + more.dataset.pen).hidden);
  more.click(); await wait(250);
  const li = document.querySelectorAll("#rbody .pen li");
  ok("눌러서 펼침", li.length === 2, li.length + "가지");
  ok("차수별 금액", /1차.*500만원.*2차.*500만원.*3차.*500만원/.test(txt(li[0])), txt(li[0]).slice(0, 60));
  ok("경우마다 금액이 다름", /1차.*300만원.*2차.*400만원/.test(txt(li[1])), txt(li[1]).slice(0, 60));
  history.back(); await wait(400);

  await type("법 119"); cards()[0].click(); await wait(450);
  ok("제119조 과태료 — 공사금액 기준 1차",
     /공사금액의 100분의 5/.test(txt($$("#rbody .pen"))) && /200만원/.test(txt($$("#rbody .pen"))),
     txt($$("#rbody .pen")).slice(0, 70));
  history.back(); await wait(400);

  await type("법 63"); cards()[0].click(); await wait(450);
  ok("항이 없는 조는 맨 아래에", !!document.querySelector("#rbody .art > .pen"));
  history.back(); await wait(400);

  // 기타 탭 — 갈래를 고른 뒤에 들어간다
  document.querySelector('nav.tabs button[data-tab="adv"]').click(); await wait(500);
  ok("기타 탭 열림", !$$("#v-adv").hidden && document.querySelectorAll("nav.tabs button").length === 3);
  ok("첫 화면은 갈래 셋만",
     document.querySelectorAll("#v-adv .row").length === 3 && !$$("#v-adv .artgrid") && !$$("#v-adv .band"),
     [...document.querySelectorAll("#v-adv .row .t")].map(e => txt(e)).join(" / "));

  $$('#v-adv [data-adv-go="pen"]').click(); await wait(500);
  const grid = () => [...document.querySelectorAll("#v-adv .artgrid button")];
  ok("벌칙 모아보기로 들어감", /벌칙 모아보기/.test(txt($$("#v-adv .crumb"))) && grid().length > 60, grid().length + "개");
  const chaps = () => [...document.querySelectorAll("#v-adv .chap")];
  ok("장별로 묶임", chaps().length >= 8 && /^제1장/.test(txt(chaps()[0])), chaps().length + "개 장 · " + txt(chaps()[0]));
  ok("장마다 조문 수",
     chaps().every(c => /\d+$/.test(txt(c))) &&
     [...document.querySelectorAll("#v-adv .artgrid")].reduce((n, g) => n + g.querySelectorAll("button").length, 0) === grid().length);
  const fineN = grid().length;
  $$('#v-adv [data-adv="pun"]').click(); await wait(400);
  ok("형벌로 전환", grid().length > 20 && grid().length !== fineN, grid().length + "개");
  ok("전환 단추가 켜짐", txt($$("#v-adv .seg button.on")).indexOf("형벌") >= 0);
  $$('#v-adv [data-adv="fine"]').click(); await wait(400);
  ok("과태료로 되돌아옴", grid().length === fineN);
  grid()[0].click(); await wait(500);
  ok("모아보기에서 조문 열림", !$$("#reader").hidden && !!$$("#rbody .pen"), txt($$("#rno")).slice(0, 24));
  history.back(); await wait(450);
  ok("뒤로가기: 모아보기로 복귀", !!$$("#v-adv .artgrid"));
  history.back(); await wait(500);
  ok("뒤로가기: 기타 첫 화면으로", document.querySelectorAll("#v-adv .row").length === 3 && !$$("#v-adv .crumb"));

  /* 상시근로자 기준표는 정리한 것이라, 근거가 실제 조문에 닿는지가 생명이다.
     법이 개정돼 조문 번호가 바뀌면 여기서 먼저 걸린다. */
  $$('#v-adv [data-adv-go="scale"]').click(); await wait(500);
  ok("규모별 의무로 들어감", /규모별 의무/.test(txt($$("#v-adv .crumb"))));
  /* 접혀 있는 칸도 DOM 에는 이미 있다. 눈에 보이는 것만 센다 */
  const seen = () => [...document.querySelectorAll("#v-adv .scale>li")].filter(e => e.offsetParent !== null);
  const bands = seen();
  ok("눈금이 이어진 줄 위에", !!$$("#v-adv .scale") && bands.length === 7, bands.length + "눈금");
  ok("눈금이 작은 수부터", txt(bands[0].querySelector(".tick")).indexOf("5명") >= 0, txt(bands[0].querySelector(".tick")));
  ok("규모가 커지는 차례",
     bands.map(e => parseInt(txt(e.querySelector(".tick")).replace(/,/g, ""), 10))
       .every((n, i, a) => i === 0 || n > a[i - 1]),
     bands.map(e => txt(e.querySelector(".tick"))).join(" → "));
  /* 펼침 안쪽 목록까지 세지 않도록 직계 자식만 본다 */
  ok("의무마다 근거가 붙음",
     [...document.querySelectorAll("#v-adv .duty > li")].every(li => li.querySelector(".reflink")));
  const dead = [...document.querySelectorAll("#v-adv .reflink.off")];
  ok("근거가 모두 실제 조문에 닿음", dead.length === 0,
     dead.length ? "끊김: " + dead.map(e => txt(e)).join(", ") : document.querySelectorAll("#v-adv .reflink").length + "개 모두 연결");
  ok("건설공사 금액 기준은 접혀 있음", !!$$("#v-adv .fold") && $$("#" + $$("#v-adv .fold").dataset.sc).hidden);
  $$("#v-adv .fold").click(); await wait(350);
  ok("건설공사 기준을 눌러서 펼침", seen().length > bands.length,
     bands.length + "눈금 → " + seen().length + "눈금");
  /* 5명 미만은 무엇이 빠지는지가 핵심이다. 접혀 있다가 눌러야 펼쳐진다 */
  const gone = $$("#v-adv .gone");
  ok("5명 미만 상세는 접혀 있음", !!gone && gone.hidden);
  $$("#v-adv .duty .open").click(); await wait(350);
  ok("눌러서 무엇이 빠지는지 펼침", !$$("#v-adv .gone").hidden);
  const gl = [...document.querySelectorAll("#v-adv .gone li")];
  ok("빠지는 것을 조문 단위로", gl.length >= 6, gl.length + "가지");
  ok("무엇이 왜 빠지는지 함께",
     gl.every(li => li.querySelector(".g1") && li.querySelector(".g2")),
     txt(gl[0].querySelector(".g1")));
  const link = $$("#v-adv .reflink[data-key]");
  const want = txt(link);
  link.click(); await wait(550);
  ok("근거를 눌러 조문으로", !$$("#reader").hidden, want + " → " + txt($$("#rwho")) + " " + txt($$("#rno")).slice(0, 16));
  history.back(); await wait(450);
  $$("#advback").click(); await wait(500);
  ok("빵부스러기로 기타 첫 화면", document.querySelectorAll("#v-adv .row").length === 3);
  ok("기타 탭 아래에 만든 사람", txt($$("#v-adv .by")) === "제작: 김익중", txt($$("#v-adv .by")));

  // 법령 판 · 업데이트
  $$('#v-adv [data-adv-go="ver"]').click(); await wait(600);
  const vb = $$("#v-adv .verbox");
  ok("법령 판 칸", !!vb && /업데이트/.test(txt(vb)), vb ? txt(vb).slice(0, 50) : "-");
  ok("담긴 법령 수", !!vb && new RegExp(DOCS.length + "건").test(txt(vb)));
  ok("가장 늦은 시행일", !!vb && /가장 늦은 시행일 \d{4}-\d{2}-\d{2}/.test(txt(vb)));
  ok("법령 업데이트 버튼", !!$$("#v-adv .verbtn"), $$("#v-adv .verbtn") ? txt($$("#v-adv .verbtn")) : "-");
  ok("법령 목록은 넣지 않는다", document.querySelectorAll("#v-adv .list .row").length === 0);
  const chg = [...document.querySelectorAll("#v-adv .chg")];
  ok("업데이트 내역", chg.length >= 3, chg.map(e => txt(e.querySelector(".d"))).join(" / "));
  ok("날짜가 최신부터", txt(chg[0].querySelector(".d")) > txt(chg[chg.length - 1].querySelector(".d")));
  /* 개조식 — 한 줄로 끊어 적는다. 문장이 길어지면 훑어보는 뜻이 없어진다 */
  const items = [...document.querySelectorAll("#v-adv .chg li")];
  ok("개조식으로 짧게", items.every(li => txt(li).length <= 40 && !/입니다|습니다/.test(txt(li))),
     items.map(li => txt(li).length).join(","));
  $$("#advback").click(); await wait(500);
  document.querySelector('nav.tabs button[data-tab="search"]').click(); await wait(300);

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
