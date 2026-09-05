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

  /* 브라우저로 열면 홈 화면에 추가하라고 권한다. 뒤 검사들이 막히지 않게 여기서 물린다.
     한 번 물리면 다시 묻지 않아야 한다 — 열 때마다 뜨면 그것이 더 나쁘다. */
  const sheet = $$("#install");
  ok("홈 화면 추가 권함", !!sheet && !sheet.hidden);
  ok("권하는 까닭 두 가지",
     document.querySelectorAll("#install li").length === 2,
     [...document.querySelectorAll("#install li")].map(e => txt(e)).join(" / "));
  ok("기기에 맞는 방법 안내", /홈 화면에 추가|앱 설치/.test(txt($$("#insthow"))), txt($$("#insthow")).slice(0, 40));
  /* 크롬은 "설치 창을 띄워도 좋다"는 신호를 팝업보다 늦게 줄 때가 있다. 그대로 두면
     크롬인데도 메뉴를 찾아 가라고 이르게 된다 — 신호가 오면 그 자리에서 바꿔 준다. */
  ok("먼저 뜰 때는 설치 단추가 없음", $$("#instgo").hidden);
  {
    const ev = new Event("beforeinstallprompt");
    ev.prompt = () => {};
    ev.userChoice = Promise.resolve({ outcome: "dismissed" });
    dispatchEvent(ev); await wait(250);
    ok("늦게 온 신호로 설치 단추가 생김", !$$("#instgo").hidden);
    ok("안내도 설치 단추 쪽으로 바뀜", /설치를 누르면/.test(txt($$("#insthow"))), txt($$("#insthow")));
    instPrompt = null;
  }
  $$("#instno").click(); await wait(250);
  ok("나중에 누르면 닫힘", $$("#install").hidden);
  /* 물려도 다음에 열면 다시 묻는다 — 저장해 두고 영영 묻지 않으면 안 된다 */
  ok("물려도 남겨 두지 않는다", localStorage.getItem("osh:instOff") === null);
  ok("이미 설치했으면 아예 안 물음", typeof installed === "function" && !installed());
  ok("법령 66건 적재", typeof DOCS !== "undefined" && DOCS.length === 66, typeof DOCS !== "undefined" ? DOCS.length : "DOCS 없음");
  ok("색인 3300건 이상", typeof RECS !== "undefined" && RECS.length >= 3300, typeof RECS !== "undefined" ? RECS.length : "-");
  const guides = DOCS.filter(d => d.군 === "지침");
  ok("지침 17건을 단계 6으로 적재", guides.length === 17 &&
     guides.every(d => d.약호 === "지침" && d.단계 === 6 && d.조문.length > 0), guides.length + "건");
  ok("지침 17건을 목차 끝에 배치", DOCS.slice(-17).every(d => d.군 === "지침"));
  ok("관리·보건 지침은 고시로 유지",
     ["사업장 위험성평가에 관한 지침", "근로자 건강증진활동 지침", "사무실 공기관리 지침",
      "영상표시단말기(VDT) 취급근로자 작업관리지침"].every(name =>
       DOCS.some(d => d.법령명 === name && d.군 === "고시" && d.약호 === "고시" && d.단계 === 5)));
  for (const nm of ["중대재해 처벌 등에 관한 법률", "중대재해 처벌 등에 관한 법률 시행령",
                    "근로감독관 집무규정(산업안전보건)"]) {
    const d = DOCS.find(x => x.법령명 === nm);
    ok("담김: " + nm, !!d && d.조문.length > 10, d ? d.약호 + " · 조문 " + d.조문.length : "없음");
  }

  await type("추락");
  ok("낱말 검색 결과 있음", cards().length > 0, cards().length + "건 표시");
  ok("검색어 강조", !!$$("#v-search mark"));
  ok("첫 결과에 검색어 포함", /추락/.test(txt(cards()[0])), txt(cards()[0]).slice(0, 50));
  {
    const rule = hits.findIndex(r => DOCS[r.d].법령명 === "산업안전보건기준에 관한 규칙" && r.no === "제42조");
    const guide = hits.findIndex(r => DOCS[r.d].군 === "지침");
    ok("추락: 기준규칙 제42조가 지침보다 먼저", rule >= 0 && guide > rule,
       "기준규칙 " + (rule + 1) + "위 · 첫 지침 " + (guide + 1) + "위");
  }
  /* 실제 고시와 지침의 '목적' 조문을 비교해 같은 검색 조건의 우선순위를 확인한다. */
  await type("목적");
  {
    const notice = hits.findIndex(r => DOCS[r.d].법령명 === "건설공사 안전보건대장의 작성 등에 관한 고시" && r.no === "제1조");
    const guide = hits.findIndex(r => DOCS[r.d].법령명 === "가설공사 표준안전 작업지침" && r.no === "제1조");
    ok("같은 검색 조건에서 고시가 지침보다 2점 높고 먼저",
       notice >= 0 && guide > notice && hits[notice]._score - hits[guide]._score === 2,
       "고시 " + (notice + 1) + "위 · 지침 " + (guide + 1) + "위");
  }

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

  // 줄바꿈: 문장 끝·조문 인용·좁은 표 열을 따로 확인한다.
  {
    const notice = RECS.find(r => r.kind === 0 && DOCS[r.d].법령명 === "방호장치 안전인증 고시" && r.no === "제7조");
    ok("고시 문장 끝을 다목으로 잘못 나누지 않음", notice &&
       !/말한\n\s*다\./.test(notice.body) && /말한다\.\n\s*다\./.test(notice.body));
    const rest = RECS.find(r => r.d === 2 && r.no === "별표 21의2");
    ok("휴게시설 별표의 인쇄용 줄바꿈 복원", rest && rest.body.includes("면적으로 정한 경우") &&
       rest.body.includes("갖춰져 있어야") && rest.body.includes("공동휴게시설은 사업장마다") &&
       !/한\n다[.)]/.test(rest.body));
    ok("일반 본문은 단어 단위로 줄바꿈", getComputedStyle(document.body).wordBreak === "keep-all");
    const table = RECS.find(r => r.d === 1 && r.no === "별표 32");
    openRec(table.key); await wait(150);
    const cells = [...document.querySelectorAll("#rbody .grid td,#rbody .grid th")];
    ok("복잡한 표의 열이 두세 글자 폭으로 찌그러지지 않음", cells.length > 10 &&
       cells.every(c => c.getBoundingClientRect().width >= 60));
    ok("변환한 표의 테두리를 본문 글자로 남기지 않음",
       [...document.querySelectorAll("#rbody .tbltext")].every(p => !/[\u2500-\u257f]/.test(p.textContent)));
    ok("넓은 표는 표 안에서만 가로 스크롤", $$("#rbody").scrollWidth <= $$("#rbody").clientWidth + 2);
    history.back(); await wait(250);
    const ref = $$("#rbody a.ref");
    ok("조문 번호 링크는 중간에서 줄을 바꾸지 않음", ref && getComputedStyle(ref).whiteSpace === "nowrap");
  }

  // 번호 없는 위임 — 실제 원문의 위치와 모든 목적지를 전수 확인한다.
  {
    let total = 0, valid = true, preserved = true;
    for (const r of RECS.filter(r => r.kind === 0)) {
      const a = DOCS[r.d].조문[r.i], links = a.위임 || [];
      if (!links.length) continue;
      const parts = { "본문": a.본문 || "" };
      (a.항 || []).forEach((h, i) => {
        parts["항" + i] = h.내용 || "";
        (h.호 || []).forEach((t, j) => { parts["항" + i + "호" + j] = t; });
      });
      for (const x of links) {
        total++;
        const text = parts[x.부분] || "";
        valid = valid && ["고용노동부령", "대통령령"].includes(text.slice(x.시작, x.끝)) &&
          x.대상.length > 0 && x.대상.every(k => BYKEY.has(k) && !BYKEY.get(k).del);
      }
      for (const part of new Set(links.map(x => x.부분))) {
        const box = document.createElement("div"); box.innerHTML = articleText(parts[part], r, part);
        preserved = preserved && box.textContent === parts[part] &&
          box.querySelectorAll(".delegated").length === links.filter(x => x.부분 === part).length &&
          !box.querySelector("a button,button button");
      }
    }
    ok("위임 문구 330곳 이상과 모든 목적지 유효", total >= 330 && valid, total + "곳");
    ok("위임 링크 전체가 원문을 보존하고 중첩되지 않음", preserved);
    const rec = (name, no) => RECS.find(r => r.kind === 0 && DOCS[r.d].법령명 === name && r.no === no);
    const law = no => rec("산업안전보건법", no);
    const destination = b => b && BYKEY.get(b.dataset.key);
    const isRule = (r, no) => r && DOCS[r.d].법령명 === "산업안전보건법 시행규칙" && r.no === no;

    openRec(law("제29조").key); await wait(150);
    const education = [...document.querySelectorAll("#rbody .delegated")];
    ok("교육 의무 세 항은 시행규칙 제26조로 연결", education.length === 3 &&
       education.every(b => isRule(destination(b), "제26조")));
    education[0]?.click(); await wait(200);
    ok("고용노동부령을 누르면 실제 위임 조문 열림", isRule(cur, "제26조"));
    history.back(); await wait(250);
    ok("위임 조문에서 뒤로가면 원래 교육 의무 복귀", cur.key === law("제29조").key);
    history.back(); await wait(250);

    openRec(law("제36조").key); await wait(150);
    const risk = [...document.querySelectorAll("#rbody .delegated")].map(destination);
    ok("위험성평가의 각 항은 서로 다른 시행규칙 조문으로 연결", risk.length === 4 &&
       ["제37조의2", "제37조의3", "제37조의4", "제37조"].every((no, i) => isRule(risk[i], no)));
    history.back(); await wait(250);

    openRec(law("제15조").key); await wait(150);
    const manager = [...document.querySelectorAll("#rbody .delegated")];
    ok("호 안의 부령과 항의 대통령령을 구별", manager.length === 2 &&
       isRule(destination(manager[0]), "제9조") && destination(manager[1])?.no === "제14조" &&
       DOCS[destination(manager[1]).d].법령명 === "산업안전보건법 시행령");
    history.back(); await wait(250);

    const severe = rec("중대재해 처벌 등에 관한 법률", "제8조");
    openRec(severe.key); await wait(150);
    const severeLink = $$("#rbody .delegated");
    ok("중대재해법 위임은 같은 계열 시행령으로 연결", severeLink &&
       DOCS[destination(severeLink)?.d]?.법령명 === "중대재해 처벌 등에 관한 법률 시행령");
    history.back(); await wait(250);

    openRec(law("제38조").key); await wait(150);
    $$("#rbody [data-delegate]")?.click(); await wait(200);
    ok("안전조치 부령은 위임받은 조문 목록을 열음", !!$$("#delegateq") &&
       document.querySelectorAll("#delegatelist .drow").length > 300 &&
       getComputedStyle($$("#rstar")).display === "none" && getComputedStyle($$("#rhl")).display === "none");
    const dq = $$("#delegateq");
    if (dq) { dq.value = "크레인"; dq.dispatchEvent(new Event("input", { bubbles: true })); }
    const choices = [...document.querySelectorAll("#delegatelist .drow")];
    ok("위임 조문 목록 안에서 본문 낱말로 검색", choices.length > 0 && choices.length < 100 &&
       choices.every(b => destination(b).hay.includes("크레인")));
    const chosen = choices[0]?.dataset.key;
    choices[0]?.click(); await wait(200);
    ok("목록에서 선택한 기준규칙 조문으로 이동", !!chosen && cur.key === chosen && !$("#rstar").hidden);
    history.back(); await wait(250);
    ok("뒤로가기로 위임 목록과 검색어 복원", $$("#delegateq")?.value === "크레인");
    if ($$("#delegateq")) {
      $$("#delegateq").value = "없는문구xyz";
      $$("#delegateq").dispatchEvent(new Event("input", { bubbles: true }));
    }
    ok("위임 목록 검색 결과 없음 안내", /찾는 조문이 없습니다/.test(txt($$("#delegatelist"))));
    $$("#rback").click(); await wait(250);
    ok("목록에서 뒤로가면 출발 조문 복귀", cur.key === law("제38조").key &&
       !$$("#delegateq") && !!$$("#rbody [data-delegate]"));
    history.back(); await wait(250);
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
  const guideChip = $$('.chip[data-g="지침"]');
  ok("지침 필터 칩 표시", !!guideChip && txt(guideChip) === "지침");
  await type("추락");
  if (guideChip) guideChip.click();
  await wait(400);
  ok("지침 필터는 지침만 검색", hits.length > 0 && hits.every(r => DOCS[r.d].군 === "지침"), hits.length + "건");
  ok("지침 검색 결과는 원문 종류인 고시 배지", cards().length > 0 &&
     cards().every(c => txt(c.querySelector(".badge")) === "고시"));
  $$('.chip[data-g="전체"]').click(); await wait(300);

  // 목차
  document.querySelector('nav.tabs button[data-tab="index"]').click(); await wait(300);
  ok("목차: 법령 목록 66건", document.querySelectorAll("#v-index .row").length === 66, document.querySelectorAll("#v-index .row").length + "건");
  ok("목차: 단계 6 지침 17건은 고시 배지", document.querySelectorAll("#v-index .badge.l6").length === 17 &&
     [...document.querySelectorAll("#v-index .badge.l6")].every(b => txt(b) === "고시"));
  ok("목차: 행정규칙 배지는 원문의 고시·훈령·예규",
     DOCS.every((d, i) => !["고시", "훈령", "예규"].includes(d.법령구분) ||
       txt($$('#v-index [data-doc="' + i + '"] .badge')) === d.법령구분));
  {
    const employment = DOCS.findIndex(d => d.군 === "취업제한규칙");
    ok("목차: 취업제한규칙은 부령 배지", employment >= 0 &&
       txt($$('#v-index [data-doc="' + employment + '"] .badge')) === "부령");
  }
  {
    const names = [...document.querySelectorAll("#v-index .row .t")].map(e => txt(e));
    const certified = names.indexOf("위험기계·기구 안전인증 고시");
    ok("목차: 위험기계·기구 고시 두 건을 나란히 배치", certified >= 0 &&
       names[certified + 1] === "위험기계·기구 자율안전확인 고시");
    const root = document.documentElement, theme = root.getAttribute("data-theme");
    for (const mode of ["light", "dark"]) {
      root.setAttribute("data-theme", mode);
      const guide = $$("#v-index .badge.l6"), notice = $$("#v-index .badge.l5");
      const color = guide ? getComputedStyle(guide).backgroundColor : "";
      ok("목차: " + mode + " 지침 배지 색상", !!guide && !!notice && !!color &&
         color !== "rgba(0, 0, 0, 0)" && color !== getComputedStyle(notice).backgroundColor, color);
    }
    if (theme === null) root.removeAttribute("data-theme"); else root.setAttribute("data-theme", theme);
  }
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
  /* 저장했는데 화면이 그대로면 "저장이 안 됐다" 로 보인다. 알려 주어야 한다. */
  ok("저장하면 알려 준다", !$$("#toast").hidden && /저장했습니다/.test(txt($$("#toast"))),
     txt($$("#toast")));
  history.back(); await wait(400);
  /* 검색 중에도 저장한 조문으로 갈 길이 있어야 한다 */
  const go = $$("#savego");
  ok("결과 화면에 저장한 조문 줄", !!go && /저장한 조문 1/.test(txt(go)), go ? txt(go) : "(없음)");
  ok("목록은 다시 그리지 않는다", document.querySelectorAll("#v-search .card").length > 10,
     document.querySelectorAll("#v-search .card").length + "장");
  go.click(); await wait(700);
  ok("눌러서 저장한 조문으로", $$("#q").value === "" && !!$$("#savefold"));
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

  /* 목차·기타 탭에서 찾아도 결과는 검색 탭에 있다. 조문에 들어갔다 뒤로 왔을 때
     원래 탭으로 튕기면 찾던 목록이 통째로 사라진다 — 다시 검색어를 쳐야 한다. */
  document.querySelector('nav.tabs button[data-tab="index"]').click(); await wait(300);
  await type("지게차");
  ok("목차 탭에서 검색하면 검색 탭으로", curTab() === "search", curTab());
  const found = cards().length;
  ok("검색 결과가 나옴", found > 0, found + "건");
  cards()[0].click(); await wait(450);
  ok("결과에서 조문이 열림", !$$("#reader").hidden);
  history.back(); await wait(450);
  ok("뒤로가면 검색 탭 그대로", curTab() === "search", curTab());
  ok("뒤로가면 결과도 그대로", cards().length === found, cards().length + "건");
  ok("검색어도 그대로", $$("#q").value === "지게차", $$("#q").value);
  history.back(); await wait(450);
  ok("한 걸음 더 뒤로가면 목차", curTab() === "index", curTab());

  /* 탭 단추는 그 탭의 첫 화면이다. 지난번에 어디까지 들어가 있었는지는 잊는다 */
  document.querySelector("#v-index [data-doc]").click(); await wait(450);
  ok("목차에서 법령 하나로 들어감", !!$$("#idxback"));
  document.querySelector('nav.tabs button[data-tab="search"]').click(); await wait(350);
  ok("검색 탭으로 건너오면 검색어를 비운다", $$("#q").value === "", $$("#q").value);
  document.querySelector('nav.tabs button[data-tab="index"]').click(); await wait(400);
  ok("목차 탭으로 건너오면 법령 목록", !$$("#idxback") && document.querySelectorAll("#v-index .row").length >= 29,
     document.querySelectorAll("#v-index .row").length + "건");
  document.querySelector('nav.tabs button[data-tab="adv"]').click(); await wait(400);
  $$("[data-adv-go]").click(); await wait(450);
  ok("기타 안쪽으로 들어감", !!$$("#advback"));
  document.querySelector('nav.tabs button[data-tab="search"]').click(); await wait(350);
  document.querySelector('nav.tabs button[data-tab="adv"]').click(); await wait(450);
  ok("기타 탭으로 건너오면 첫 화면", !$$("#advback"));

  /* 다만 이미 그 탭에 있으면 그대로 둔다. 보던 결과가 잘못 눌러 날아가면 더 나쁘다 */
  document.querySelector('nav.tabs button[data-tab="search"]').click(); await wait(350);
  await type("추락");
  const keep = cards().length;
  document.querySelector('nav.tabs button[data-tab="search"]').click(); await wait(350);
  ok("같은 탭을 눌러도 검색어가 남음", $$("#q").value === "추락" && cards().length === keep,
     $$("#q").value + " · " + cards().length + "건");
  await type("");

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
  /* 금액만 있으면 남 얘기처럼 읽힌다. 무엇을 했을 때인지가 늘 붙어야 한다 */
  {
    const fines = [];
    for (const key of ["법 15", "법 64", "법 119", "법 17", "법 42"]) {
      await type(key); cards()[0].click(); await wait(450);
      fines.push(...[...document.querySelectorAll("#rbody .pen")]
        .filter(e => /과태료/.test(txt(e))).map(e => e.querySelector(".when")));
      history.back(); await wait(400);
    }
    ok("과태료마다 '~인 경우'가 붙음",
       fines.length > 0 && fines.every(w => w && /경우|때/.test(txt(w))),
       fines.length + "곳 · " + (fines[0] ? txt(fines[0]).slice(0, 40) : "-"));
    ok("법조문 인용을 되풀이하지 않음",
       fines.every(w => !/^법 제\d+조/.test(txt(w))),
       fines.map(w => txt(w).slice(0, 14)).slice(0, 3).join(" / "));
  }

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
  ok("'기타' 글자 자리에 프로그램 소개",
     !$$("#v-adv .sec") && /인터넷 없이 찾습니다/.test(txt($$("#v-adv .advnote"))),
     txt($$("#v-adv .advnote")).slice(0, 34));
  ok("소개에 법적 효력을 밝힘", /법적 효력은 원문에 있습니다/.test(txt($$("#v-adv .advnote"))));
  ok("첫 화면은 벌칙 모아보기를 맨 위에 둔 세 갈래",
     document.querySelectorAll("#v-adv .row").length === 3 &&
     $$("#v-adv .row").dataset.advGo === "pen" && !$$("#v-adv .artgrid") && !$$("#v-adv .band"),
     [...document.querySelectorAll("#v-adv .row .t")].map(e => txt(e)).join(" / "));
  /* 기초 법지식은 걷어냈다. 자취가 남으면 눌러도 빈 화면이 뜬다 */
  ok("기초 법지식은 남아 있지 않음",
     !$$('#v-adv [data-adv-go="basics"]') && typeof basicsPage === "undefined");

  $$('#v-adv [data-adv-go="pen"]').click(); await wait(500);
  const grid = () => [...document.querySelectorAll("#v-adv .artgrid button")];
  ok("벌칙 모아보기로 들어감", /벌칙 모아보기/.test(txt($$("#v-adv .crumb"))) && grid().length > 60, grid().length + "개");
  ok("벌칙 모아보기에서 옮긴 개념 설명 제거", !/행정질서벌|전과가 남|수사·기소/.test(txt($$("#v-adv"))));
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
  /* 연락처가 뒤에 붙을 수 있다. 이름이 밝혀져 있는지만 본다 */
  ok("기타 탭 아래에 만든 사람", /^제작: 김익중/.test(txt($$("#v-adv .by"))), txt($$("#v-adv .by")));

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

  // 얼마나 쓰이는지 세기 — 보내는 것이 숫자 하나뿐인지가 핵심이다
  ok("계수기 설정이 있다", typeof FB === "object" && !!FB.project && !!FB.key, FB.project || "(비었음)");
  /* 만들면서 열어 보는 것과 CI 는 사람이 아니다. 여기에 섞이면 숫자를 믿을 수 없다 */
  ok("만들 때 여는 것은 세지 않는다", isLocal() && localStorage.getItem("osh:day") === null,
     location.hostname + " · " + localStorage.getItem("osh:day"));
  /* 같은 기기가 하루에 여러 번 열어도 한 번만 센다. 그 판정은 기기 안에서 한다 */
  {
    let sent = 0;
    const real = window.fetch;
    window.fetch = (...a) => {
      /* 검사가 진짜 숫자를 올려 버리면 안 된다. 세기만 하고 보내지는 않는다 */
      if (String(a[0]).indexOf("firestore") >= 0) { sent++; return Promise.resolve(new Response("{}")); }
      return real(...a);
    };
    for (const k of ["day", "dev", "ver"]) localStorage.removeItem("osh:" + k);
    await count();
    const first = sent;
    await count(); await count();
    /* 갈아타는 중이면 판 칸은 건너뛴다. 날짜와 기기 둘은 언제나 간다 */
    ok("처음 열면 보낸다", first === 2 || first === 3, first + "번");
    ok("같은 날 다시 열어도 보내지 않는다", sent === first, sent + "번");
    /* 날이 바뀌면 그날 칸만 하나 오른다. 기기 칸은 평생 한 번이라 다시 오르지 않는다 */
    localStorage.removeItem("osh:day");
    await count();
    ok("날이 바뀌어도 기기 칸은 그대로", sent === first + 1, (sent - first) + "번");
    window.fetch = real;
    for (const k of ["day", "dev", "ver"]) localStorage.removeItem("osh:" + k);
    /* 보내지 못한 날은 적어 두지 않는다 — 신호 없는 현장에서 연 날이 통째로 빠진다 */
    window.fetch = () => Promise.reject(new Error("끊김"));
    await count();
    window.fetch = real;
    ok("못 보내면 적어 두지 않는다", localStorage.getItem("osh:day") === null,
       String(localStorage.getItem("osh:day")));
    for (const k of ["day", "dev", "ver"]) localStorage.removeItem("osh:" + k);
  }
  /* 현황판은 내가 숫자를 보는 딴 쪽이다. 앱의 오프라인 캐시에 섞이면
     쓰는 사람이 쓰지도 않을 것을 함께 내려받게 된다. */
  {
    const sw = await (await fetch("sw.js", { cache: "no-store" })).text();
    ok("현황판은 앱 캐시에 넣지 않는다", sw.indexOf("stats.html") < 0);
    const st = await fetch("stats.html", { cache: "no-store" });
    ok("현황판이 함께 올라감", st.ok, String(st.status));
  }
  ok("기기를 가리는 번호를 보내지 않는다",
     !/deviceId|uuid|randomUUID/.test(count.toString() + bump.toString()));

  // 새 판 알림 — 판마다 한 번씩만 물어야 한다
  {
    const $u = () => $$("#update");
    localStorage.removeItem("osh:updSeen");
    const fake = { waiting: { postMessage: () => {} } };
    const ver = await pendingVersion();
    ok("기다리는 판의 이름을 읽음", /^osh-|^new$/.test(ver), ver);
    await showUpdate(fake); await wait(300);
    ok("새 판이면 알린다", !$u().hidden);
    ok("껐다 켜라고 일러 준다", /껐다 켜면/.test(txt($u())), txt($$("#update p")).slice(0, 30));
    ok("바로 바꿀 길도 준다", !!$$("#updgo"));
    $$("#updno").click(); await wait(250);
    ok("물리면 닫힌다", $u().hidden);
    await showUpdate(fake); await wait(300);
    ok("같은 판은 다시 묻지 않는다", $u().hidden);
    store.set("updSeen", "osh-지난판");
    await showUpdate(fake); await wait(300);
    ok("다음 판이 나오면 다시 묻는다", !$u().hidden);
    $$("#updno").click(); await wait(250);
  }

  // 조문 공유 — 링크 없이 글만, 벌칙·과태료는 고르게
  await type("법 42"); cards()[0].click(); await wait(500);
  ok("조문 화면에 공유 단추", !!$$("#rshare"));
  $$("#rshare").click(); await wait(400);
  ok("공유창 열림", !$$("#share").hidden);
  const prev = () => txt($$("#shprev"));
  ok("법령명과 조번호로 시작", /^산업안전보건법 제42조/.test($$("#shprev").textContent), prev().slice(0, 30));
  ok("시행일을 밝힘", /시행 \d{4}-\d{2}-\d{2}/.test(prev()));
  /* 링크는 넣지 않기로 했다 — 주소가 섞이면 카카오톡에서 미리보기가 끼어든다 */
  ok("링크를 넣지 않는다", !/https?:\/\//.test($$("#shprev").textContent), prev().slice(-40));
  ok("벌칙·과태료를 고를 수 있음", !$$("#shpenrow").hidden);
  $$("#shpen").checked = true; $$("#shpen").dispatchEvent(new Event("change")); await wait(300);
  const withPen = $$("#shprev").textContent;
  ok("켜면 과태료가 들어감", /\[과태료\]|\[형벌\]/.test(withPen));
  $$("#shpen").checked = false; $$("#shpen").dispatchEvent(new Event("change")); await wait(300);
  const noPen = $$("#shprev").textContent;
  ok("끄면 빠짐", !/\[과태료\]|\[형벌\]/.test(noPen) && noPen.length < withPen.length,
     withPen.length + "자 → " + noPen.length + "자");
  $$("#shno").click(); await wait(250);
  $$("#rshare").click(); await wait(400);
  ok("고른 것을 기억함", $$("#shpen").checked === false);
  $$("#shno").click(); await wait(250);
  ok("취소하면 닫힘", $$("#share").hidden);
  history.back(); await wait(400);

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
