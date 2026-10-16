(() => {
  const PAGE = 40;
  const GU = ["종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구", "성북구", "강북구",
    "도봉구", "노원구", "은평구", "서대문구", "마포구", "양천구", "강서구", "구로구", "금천구",
    "영등포구", "동작구", "관악구", "서초구", "강남구", "송파구", "강동구"];
  const TYPES = ["국공립", "직장", "민간", "가정", "법인·단체등", "사회복지법인", "협동"];
  const DEFAULT = { kind: ["어린이집"], gu: [], foundation: [], type: [], q: "", fav: false, cl: false, sort: "end", view: "list" };
  const NO_FOUNDATION = "센터 게시판";
  const today = new Date().toLocaleDateString("sv-SE", { timeZone: "Asia/Seoul" });

  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* 저장 안 돼도 화면은 동작 */ } },
  };
  let state = { ...DEFAULT, ...store.get("buddie.filters", {}) };
  let favs = new Set(store.get("buddie.favs", []));
  let all = [];
  let shown = PAGE;

  const $ = (s) => document.querySelector(s);
  const norm = (s) => (s || "").replace(/\s+/g, "").replace(/어린이집$/, "");
  // 직접 입력한 '아모레퍼시픽' 이 '아모레퍼시픽 서울어린이집' 에도 걸리도록 포함 관계로 본다.
  const favOf = (org) => [...favs].filter((f) => norm(org).includes(f));
  const isFav = (j) => favOf(j.org).length > 0;
  const days = (d) => Math.round((Date.parse(d) - Date.parse(today)) / 864e5);
  const md = (d) => d ? d.slice(5).replace("-", ".") : "";
  const safeUrl = (u) => /^https?:\/\//.test(u || "") ? u : "#";

  function chips(el, items, key) {
    el.innerHTML = "";
    for (const [value, label, count] of items) {
      const l = document.createElement("label");
      l.className = "chip";
      const i = document.createElement("input");
      i.type = "checkbox"; i.value = value; i.checked = state[key].includes(value);
      i.addEventListener("change", () => {
        state[key] = i.checked ? [...state[key], value] : state[key].filter((v) => v !== value);
        update();
      });
      const s = document.createElement("span");
      s.textContent = label;
      if (count != null) { const c = document.createElement("i"); c.textContent = count; s.append(c); }
      l.append(i, s);
      el.append(l);
    }
  }

  function buildFilters() {
    const live = all.filter((j) => !j.end || j.end >= today);
    const count = (f) => live.filter(f).length;
    chips($("#f-gu"), GU.map((g) => [g, g, count((j) => j.gu === g)]), "gu");
    chips($("#f-foundation"), [...foundations().map((f) => f.name), NO_FOUNDATION]
      .map((f) => [f, f, count((j) => fnd(j) === f)]), "foundation");
    chips($("#f-type"), TYPES.map((t) => [t, t, count((j) => j.orgType === t)]).filter((x) => x[2]), "type");
    document.querySelectorAll("#f-kind input").forEach((i) => {
      if (!i.disabled) i.checked = state.kind.includes(i.value);
    });
    $("#f-q").value = state.q;
    $("#f-fav").checked = state.fav;
    $("#f-cl").checked = state.cl;
    $("#f-sort").value = state.sort;
  }

  function matches(j) {
    if (j.end && j.end < today) return false;
    if (!state.kind.includes(j.kind)) return false;
    if (state.gu.length && !state.gu.includes(j.gu)) return false;
    if (state.foundation.length && !state.foundation.includes(fnd(j))) return false;
    if (state.type.length && !state.type.includes(j.orgType)) return false;
    if (state.fav && !isFav(j)) return false;
    if (state.cl && !j.coverLetter) return false;
    if (state.q) {
      const q = state.q.replace(/\s+/g, "").toLowerCase();
      if (!(j.org + j.title + (j.addr || "")).replace(/\s+/g, "").toLowerCase().includes(q)) return false;
    }
    return true;
  }

  function sorter(a, b) {
    if (state.sort === "new") {
      return (b.posted || b.start || "").localeCompare(a.posted || a.start || "") || b.id.localeCompare(a.id);
    }
    return (a.end || "9999").localeCompare(b.end || "9999") || (b.posted || "").localeCompare(a.posted || "");
  }

  function card(j) {
    const li = $("#tpl-job").content.firstElementChild.cloneNode(true);
    const d = j.end ? days(j.end) : null;
    const b = li.querySelector(".dday b");
    const s = li.querySelector(".dday span");
    if (d == null) { b.textContent = "채용 시"; s.textContent = "마감"; li.classList.add("is-open"); }
    else if (d === 0) { b.textContent = "오늘"; s.textContent = "마감"; }
    else { b.textContent = `D-${d}`; s.textContent = `${md(j.end)} 마감`; }
    if (d != null && d <= 2) li.classList.add("is-urgent");

    li.querySelector(".meta").textContent = [j.gu, j.orgType, j.job !== "보육교사" ? j.job : null].filter(Boolean).join(" · ");
    const a = li.querySelector("h3 a");
    a.textContent = j.title; a.href = safeUrl(j.url);
    li.querySelector(".org span").textContent = j.org;
    const star = li.querySelector(".star");
    star.setAttribute("aria-pressed", String(isFav(j)));
    star.setAttribute("aria-label", `${j.org} 관심 ${isFav(j) ? "해제" : "등록"}`);
    star.addEventListener("click", () => toggleFav(j.org));
    li.querySelector(".hint").textContent = j.deadlineHint || "";

    li.querySelector(".period").textContent = j.start
      ? `접수 ${md(j.start)} ~ ${j.end ? md(j.end) : "채용 시"}`
      : `게시 ${md(j.posted)} · 마감 ${j.end ? md(j.end) : "채용 시까지"}`;
    const tags = li.querySelector(".tags");
    const add = (t, cls) => { const e = document.createElement("span"); e.className = "tag" + (cls ? " " + cls : ""); e.textContent = t; tags.append(e); };
    if (j.coverLetter) add("자소서", "cl");
    if (j.qual) add(j.qual.length > 18 ? j.qual.slice(0, 18) + "…" : j.qual);
    add(sourceName(j.source));
    li.querySelector(".go").href = safeUrl(j.url);
    return li;
  }

  let sources = [];
  // 재단 사이트 출처 + 센터 게시판 본문에서만 이름이 나온 재단(사이트 없음)
  const foundations = () => {
    const fs = sources.filter((s) => s.foundation).map((s) => ({ name: s.name, url: s.url, ok: s.ok }));
    for (const j of all) if (j.foundation && !fs.some((f) => f.name === j.foundation)) fs.push({ name: j.foundation, url: null, ok: true });
    return fs;
  };
  const fnd = (j) => j.foundation || NO_FOUNDATION;
  const sourceName =(id) => ((sources.find((s) => s.id === id) || {}).name || id).replace(/^서울시/, "").replace(/보육지원재단$/, "");

  function saveFavs() {
    store.set("buddie.favs", [...favs]);
    favChips();
    render();
  }

  function toggleFav(org) {
    const hit = favOf(org);
    hit.length ? hit.forEach((f) => favs.delete(f)) : favs.add(norm(org));
    saveFavs();
  }

  function favChips() {
    $("#fav-list").replaceChildren(...[...favs].map((f) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "fav-chip"; b.textContent = f;
      b.setAttribute("aria-label", `${f} 관심 해제`);
      b.addEventListener("click", () => { favs.delete(f); saveFavs(); });
      return b;
    }));
  }

  function render() {
    const list = all.filter(matches).sort(sorter);
    const grouped = state.view === "foundation";
    document.querySelectorAll(".viewtabs button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === state.view)));
    $("#groups").hidden = !grouped;
    $("#jobs").hidden = grouped;
    if (grouped) renderGroups(list);
    else $("#jobs").replaceChildren(...list.slice(0, shown).map(card));
    $("#result-count").textContent = `공고 ${list.length.toLocaleString()}건`;
    $("#empty").hidden = list.length > 0 || grouped;
    $("#more").hidden = grouped || list.length <= shown;
    $("#more").textContent = `더 보기 (${Math.min(PAGE, list.length - shown)}건)`;

    const favJobs = all.filter((j) => isFav(j) && (!j.end || j.end >= today) && state.kind.includes(j.kind)).sort(sorter);
    $("#fav-section").hidden = favs.size === 0 || state.fav;
    $("#fav-jobs").replaceChildren(...favJobs.map(card));
    $("#fav-names").textContent = favJobs.length ? `${favJobs.length}건` : "지금 열린 공고 없음";

    const n = state.gu.length + state.foundation.length + state.type.length + (state.q ? 1 : 0) + (state.fav ? 1 : 0) + (state.cl ? 1 : 0);
    $("#filter-summary").textContent = n ? `${n}개 조건 적용` : "전체";
  }

  // 재단별 보기. 재단 공고는 많지 않아 페이지를 나누지 않는다. 센터 게시판 공고는 수가 많아 건수만 보여준다.
  function renderGroups(list) {
    const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
    const out = foundations()
      .filter((f) => !state.foundation.length || state.foundation.includes(f.name))
      .map((f) => {
        const mine = list.filter((j) => j.foundation === f.name);
        // 같은 공고가 센터 게시판에도 올라오면 재단 사이트 쪽만 남긴다.
        const site = mine.filter((j) => j.source !== "seoul-ccef");
        const same = (a, b) => a.end === b.end && (norm(a.org).includes(norm(b.org)) || norm(b.org).includes(norm(a.org)));
        const jobs = mine.filter((j) => j.source !== "seoul-ccef" || !site.some((s) => same(s, j)));
        const sec = el("section", "group");
        const head = el("div", "group-head");
        head.append(el("h3", null, f.name), el("span", "count", `서울 공고 ${jobs.length}건`));
        if (f.url) {
          const a = el("a", null, "재단 채용 사이트 ↗");
          a.href = safeUrl(f.url); a.target = "_blank"; a.rel = "noopener noreferrer";
          head.append(a);
        } else head.append(el("span", "count", "· 센터 게시판 본문에서 찾은 공고"));
        sec.append(head);
        if (jobs.length) { const ol = el("ol", "jobs"); ol.append(...jobs.map(card)); sec.append(ol); }
        else sec.append(el("p", "none", f.ok ? "지금 조건에 맞는 서울 공고가 없어요." : "이번 갱신에서 사이트를 읽지 못했어요."));
        return sec;
      });
    const rest = list.filter((j) => !j.foundation).length;
    if (rest && (!state.foundation.length || state.foundation.includes(NO_FOUNDATION))) {
      const sec = el("section", "group rest");
      const b = el("button", null, "전체 목록에서 보기");
      b.type = "button";
      b.addEventListener("click", () => { state.view = "list"; update(); });
      sec.append(`본문에 위탁 재단 이름이 없는 서울시육아종합지원센터 게시판 공고 ${rest.toLocaleString()}건 · `, b);
      out.push(sec);
    }
    $("#groups").replaceChildren(...out);
  }

  function update() {
    shown = PAGE;
    store.set("buddie.filters", state);
    render();
  }

  function stats(data) {
    const live = all.filter((j) => (!j.end || j.end >= today) && j.kind === "어린이집");
    $("#st-total").textContent = live.length.toLocaleString();
    $("#st-work").textContent = live.filter((j) => j.orgType === "직장").length.toLocaleString();
    $("#st-soon").textContent = live.filter((j) => j.end && days(j.end) <= 3).length.toLocaleString();
    const t = data.updatedAt ? new Date(data.updatedAt) : null;
    $("#st-updated").textContent = t
      ? `마지막 갱신 ${t.toLocaleString("ko-KR", { timeZone: "Asia/Seoul", month: "long", day: "numeric", hour: "numeric", minute: "2-digit" })}`
      : "";
  }

  function sourceList() {
    $("#source-list").replaceChildren(...sources.map((s) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = safeUrl(s.url); a.target = "_blank"; a.rel = "noopener noreferrer"; a.textContent = s.name;
      const st = document.createElement("span");
      st.className = "st" + (s.ok ? "" : " bad");
      const when = (iso) => iso ? new Date(iso).toLocaleString("ko-KR", { timeZone: "Asia/Seoul", month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "없음";
      st.textContent = s.ok ? `${s.count}건 · ${when(s.checkedAt)} 확인` : `읽기 실패 · 마지막 성공 ${when(s.lastOkAt)}`;
      li.append(a, st);
      return li;
    }));
  }

  // 이벤트
  let qTimer;
  $("#f-q").addEventListener("input", (e) => { clearTimeout(qTimer); qTimer = setTimeout(() => { state.q = e.target.value.trim(); update(); }, 150); });
  $("#f-fav").addEventListener("change", (e) => { state.fav = e.target.checked; update(); });
  $("#f-cl").addEventListener("change", (e) => { state.cl = e.target.checked; update(); });
  $("#f-sort").addEventListener("change", (e) => { state.sort = e.target.value; update(); });
  document.querySelectorAll("#f-kind input").forEach((i) => i.addEventListener("change", () => {
    state.kind = [...document.querySelectorAll("#f-kind input:checked")].map((x) => x.value);
    update();
  }));
  $("#f-reset").addEventListener("click", () => { state = { ...DEFAULT }; buildFilters(); update(); });
  $("#more").addEventListener("click", () => { shown += PAGE; render(); });
  document.querySelectorAll(".viewtabs button").forEach((b) => b.addEventListener("click", () => { state.view = b.dataset.view; update(); }));
  $("#fav-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const v = norm($("#fav-input").value);
    if (v) { favs.add(v); $("#fav-input").value = ""; saveFavs(); }
  });
  favChips();
  if (matchMedia("(max-width: 560px)").matches) $("#filters").open = false;

  fetch("data/jobs.json", { cache: "no-cache" })
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((data) => {
      all = data.jobs || [];
      sources = data.sources || [];
      buildFilters(); stats(data); sourceList(); render();
    })
    .catch(() => {
      $("#st-updated").textContent = "공고를 불러오지 못했어요. 잠시 뒤 새로고침해 주세요.";
      $("#empty").hidden = false;
      $("#empty").textContent = "공고를 불러오지 못했어요.";
    });
})();
