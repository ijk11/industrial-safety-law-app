const w = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  try {
    for (let i = 0; i < 200 && document.getElementById("boot"); i++) await w(100);
    await w(400);
    const o = [];
    o.push("innerWidth=" + innerWidth + " dpr=" + devicePixelRatio);
    o.push("clientWidth=" + document.documentElement.clientWidth + " scrollWidth=" + document.documentElement.scrollWidth);
    const nav = document.querySelector("nav.tabs"), hdr = document.querySelector("header.top"), app = document.querySelector("#app");
    for (const pair of [["#app", app], ["header", hdr], ["nav", nav]]) {
      const r = pair[1].getBoundingClientRect();
      o.push(pair[0] + " x=" + Math.round(r.x) + " w=" + Math.round(r.width));
    }
    const W = document.documentElement.clientWidth, bad = [];
    document.querySelectorAll("body *").forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.right > W + 1 && r.width > 0) {
        let n = el.id ? "#" + el.id : (typeof el.className === "string" && el.className ? "." + el.className.split(" ")[0] : el.tagName);
        bad.push(n + "(right=" + Math.round(r.right) + ")");
      }
    });
    o.push("삐져나옴 " + bad.length + "개: " + bad.slice(0, 10).join(" , "));
    const p = document.createElement("pre"); p.id = "testout";
    p.textContent = o.join(" ;; ");
    document.body.appendChild(p);
  } catch (e) {
    const p = document.createElement("pre"); p.id = "testout";
    p.textContent = "ERROR " + e.message;
    document.body.appendChild(p);
  }
})();
