/* ASN Kitting Progress Tracker - calculation engine.
   The Excel workbook implements the same rules with worksheet formulas; build/compare.py checks that both agree.
   Dates are Excel serial day numbers so both versions do identical week arithmetic. */
(function (root) {
  "use strict";
  const ASP_FIRST_WEEK_COL = 16;          // column Q (0-based index)
  const ASP_INFO_COLS = { projectId: 2, projectName: 3, product: 4, planningCode: 5, prodId: 6, friendly: 7,
    temp: 8, body: 9, fp: 10, system: 11, planned: 12, progress: 13, dr2mCalc: 14, dr2mDemand: 15 };
  const ASP_HEADERS = ["Project Id", "Project Name", "Product", "Planning code", "Prod Id", "Friendly_name", "Seabed Temp",
    "Body Type", "Nber FP", "System Qty", "Planned Qty", "Prod. progress", "ISO Week of DR2M_CALCULATED", "ISO Week of DR2M_DEMAND_DATE"];
  const COOIS_HEADERS = ["Order", "Order Type", "Material Number", "Material description", "Plant", "Batch",
    "Order quantity (GMEIN)", "Unit of measure (=GMEIN)", "Release date (actual)", "Delivered quantity (GMEIN)",
    "Created on", "Entered by", "Change date", "Last changed by", "System Status"];
  const LOG_COLUMNS = ["Entry ID", "Entry date", "Record type", "Variant ID", "Stage", "Assembly code", "REPs kitted",
    "REP from", "REP to", "Order", "Order qty", "Void", "Void reason", "Note"];
  const PROGRESS = "Kitting Progress", ORDER = "COOIS order";

  const U = (x) => (x === null || x === undefined ? "" : String(x)).trim().toUpperCase();
  const T = (x) => (x === null || x === undefined ? "" : String(x)).trim();
  const num = (x) => { if (x === null || x === undefined || x === "") return 0; const n = Number(x); return isFinite(n) ? n : 0; };
  const isNum = (x) => x !== null && x !== undefined && x !== "" && isFinite(Number(x));
  const EPS = 1e-9;

  // ---------- ISO week helpers (Excel serial dates) ----------
  // Excel serial 1 = 1900-01-01; weekday(serial,2): Monday=1 ... Sunday=7
  const weekday2 = (s) => { const w = ((Math.floor(s) - 1) % 7 + 7) % 7; return w === 0 ? 7 : w; }; // serial 1 (1900-01-01) was a Sunday in Excel's calendar
  function dateSerial(y, m, d) { // proleptic, valid after 1900-03-01 like Excel
    const ms = Date.UTC(y, m - 1, d); return Math.round(ms / 86400000) + 25569;
  }
  function serialToYMD(s) { const d = new Date((s - 25569) * 86400000); return [d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate()]; }
  function isoMonday(y, w) { const j4 = dateSerial(y, 1, 4); return j4 - weekday2(j4) + 1 + 7 * (w - 1); }
  function mondayOf(s) { return Math.floor(s) - weekday2(s) + 1; }
  function isoWeekNum(s) { const m = mondayOf(s); const y = serialToYMD(m + 3)[0]; return Math.floor((m - isoMonday(y, 1)) / 7) + 1; }
  function weekLabel(mon) { const y = serialToYMD(mon + 3)[0]; return String(y).slice(-2) + " W" + isoWeekNum(mon); }
  function parseWeekHeader(h) {
    const m = /^\s*(\d{2})\s+W(\d{1,2})\s*$/i.exec(T(h)); if (!m) return null;
    return isoMonday(2000 + Number(m[1]), Number(m[2]));
  }
  function statusHas(status, token) { return (" " + T(status) + " ").toUpperCase().indexOf(" " + token + " ") >= 0; }

  // ---------- core model ----------
  function compute(data, opts) {
    opts = opts || {};
    const S = data.settings || {};
    const kitLead = isNum(S.kitLead) ? Number(S.kitLead) : 3;
    const rptDate = isNum(S.reportDate) ? Number(S.reportDate) : (opts.todaySerial || todaySerial());
    const thisMon = mondayOf(rptDate);
    const req = (data.requirements || []).filter((r) => T(r.variant) !== "");
    const stages = (data.stages || []).slice().sort((a, b) => num(a.order) - num(b.order));
    const stageOrder = {}; stages.forEach((s) => { stageOrder[U(s.stage)] = num(s.order); });

    // weeks
    const aspHeader = (data.asp && data.asp.header) || [];
    const weeks = [];
    for (let c = ASP_FIRST_WEEK_COL; c < aspHeader.length; c++) {
      const mon = parseWeekHeader(aspHeader[c]);
      weeks.push({ col: c, header: T(aspHeader[c]), aspMon: mon, kitMon: mon === null ? null : mon - 7 * kitLead,
        kitLabel: mon === null ? "" : weekLabel(mon - 7 * kitLead) });
    }

    // ---- log: active flags ----
    const log = (data.log || []).map((r, i) => Object.assign({ _i: i }, r));
    const voidIds = new Set(log.filter((r) => U(r["Void"]) === "Y" && T(r["Entry ID"]) !== "").map((r) => U(r["Entry ID"])));
    log.forEach((r) => { r._active = T(r["Entry ID"]) === "" ? (U(r["Void"]) === "Y" ? 0 : 1) : (voidIds.has(U(r["Entry ID"])) ? 0 : 1);
      r._key = T(r["Order"]); r._type = U(r["Record type"]); });
    const activeOrders = log.filter((r) => r._active && r._type === U(ORDER) && r._key !== "");

    // ---- COOIS review ----
    const cooisRows = ((data.coois && data.coois.rows) || []).filter((r) => T(r[0]) !== "");
    const reqRowsByCode = {};   // number of requirement rows using each code (Excel: COUNTIF on Settings)
    req.forEach((r) => { const c = U(r.code); reqRowsByCode[c] = (reqRowsByCode[c] || 0) + 1; });
    const allocByKey = {};
    activeOrders.forEach((r) => { const k = U(r._key); if (!(k in allocByKey)) allocByKey[k] = r; });
    const cooisByKey = {};
    const coois = cooisRows.map((r) => {
      const status = T(r[14]);
      const o = { order: T(r[0]), material: T(r[2]), description: T(r[3]), qty: num(r[6]), releaseDate: isNum(r[8]) ? Number(r[8]) : "",
        delivered: num(r[9]), status: status,
        PCNF: statusHas(status, "PCNF"), CNF: statusHas(status, "CNF"), DLV: statusHas(status, "DLV"),
        CLSD: statusHas(status, "CLSD"), TECO: statusHas(status, "TECO") };
      o.variantsUsing = reqRowsByCode[U(o.material)] || 0;
      const a = allocByKey[U(o.order)];
      o.allocEntry = a ? T(a["Entry ID"]) : ""; o.allocVariant = a ? T(a["Variant ID"]) : "";
      o.review = o.CLSD ? "CLSD - review" : o.variantsUsing === 0 ? "Code not in Settings" :
        o.allocEntry === "" ? (o.variantsUsing > 1 ? "Shared code - no contract allocation" : "Not allocated") :
          (U(a["Assembly code"]) !== U(o.material) ? "Material changed - review" : "Allocated");
      if (!(U(o.order) in cooisByKey)) cooisByKey[U(o.order)] = o;
      return o;
    });

    // ---- line metrics (one per requirement row) ----
    const progressRows = log.filter((r) => r._active && r._type === U(PROGRESS));
    const lines = req.map((r) => {
      const v = U(r.variant), s = U(r.stage), c = U(r.code), q = num(r.qty);
      let repsWhole = 0, repsLine = 0;
      progressRows.forEach((p) => {
        if (U(p["Variant ID"]) !== v || U(p["Stage"]) !== s) return;
        if (U(p["Assembly code"]) === "") repsWhole += num(p["REPs kitted"]);
        else if (U(p["Assembly code"]) === c) repsLine += num(p["REPs kitted"]);
      });
      const recorded = (repsWhole + repsLine) * q;
      const allocated = activeOrders.filter((o) => U(o["Variant ID"]) === v && U(o["Assembly code"]) === c).reduce((t, o) => t + num(o["Order qty"]), 0);
      const covered = Math.min(recorded, allocated);
      const available = coois.filter((o) => U(o.material) === c && o.allocEntry === "" && !o.CLSD).reduce((t, o) => t + o.qty, 0);
      return { variant: T(r.variant), stage: T(r.stage), stageOrder: stageOrder[s] || 0, code: T(r.code), desc: T(r.desc), qty: q,
        recorded, allocated, covered, shortage: recorded - covered, excess: allocated - covered,
        coveredReps: q > 0 ? Math.floor(covered / q + EPS) : 0, startedReps: q > 0 ? Math.ceil(covered / q - EPS) : 0,
        available, sharedBy: reqRowsByCode[c] || 0 };
    });

    // ---- plan rows ----
    const aspRows = ((data.asp && data.asp.rows) || []);
    const plan = [];
    aspRows.forEach((row, i) => {
      const g = (k) => row[ASP_INFO_COLS[k]];
      if ([g("projectId"), g("projectName"), g("product"), g("friendly"), g("prodId")].every((x) => T(x) === "")) return;
      let wsum = 0, dEnd = 0, dBefore = 0, dNext4 = 0;
      weeks.forEach((w) => { const q = num(row[w.col]); if (!q || w.kitMon === null) { wsum += q; return; }
        wsum += q; if (w.kitMon <= thisMon) dEnd += q; if (w.kitMon < thisMon) dBefore += q;
        if (w.kitMon > thisMon && w.kitMon <= thisMon + 28) dNext4 += q; });
      const friendly = T(g("friendly"));
      const valid = !["", "NA", "N/A"].includes(U(friendly));
      const myLines = valid ? lines.filter((l) => U(l.variant) === U(friendly)) : [];
      const system = num(g("system")), planned = num(g("planned"));
      const p = { aspRow: i + 2, projectId: T(g("projectId")), projectName: T(g("projectName")), product: T(g("product")),
        planningCode: T(g("planningCode")), prodId: T(g("prodId")), variant: friendly, temp: T(g("temp")), body: T(g("body")),
        fp: g("fp") === null || g("fp") === undefined ? "" : g("fp"), system, planned, progress: g("progress"),
        wsum, dEnd, dBefore, dNext4, valid, reqLines: myLines.length, built: system - planned };
      if (myLines.length) {
        p.complete = Math.min(...myLines.map((l) => l.coveredReps));
        p.partial = Math.max(...myLines.map((l) => l.startedReps)) - p.complete;
        p.shortage = myLines.reduce((t, l) => t + l.shortage, 0);
        const top = req.find((r) => U(r.variant) === U(friendly)).top;
        p.topDiffers = U(top) !== U(p.prodId);
      } else { p.complete = ""; p.partial = ""; p.shortage = ""; p.topDiffers = false; }
      const c = p.complete === "" ? 0 : p.complete;
      p.remaining = myLines.length ? Math.max(0, planned - c) : "";
      p.pct = myLines.length && planned > 0 ? c / planned : "not available";
      p.dueThis = myLines.length ? Math.max(0, dEnd - Math.max(c, dBefore)) : "";
      p.behind = myLines.length ? Math.max(0, dBefore - c) : "";
      p.status = !valid ? "No variant ID in ASP" : !myLines.length ? "Assembly setup required" :
        p.topDiffers ? "Top code differs - review" : planned <= 0 ? "No plan quantity" : c >= planned ? "All kitted" :
          p.behind > 0 ? "Kit behind" : p.dueThis > 0 ? "Kit due this week" : "On track";
      plan.push(p);
    });

    // ---- variants with requirements/log but not in the ASP ----
    const aspVariants = new Set(plan.filter((p) => p.valid).map((p) => U(p.variant)));
    const known = [];
    req.forEach((r) => { if (!known.some((k) => U(k) === U(r.variant))) known.push(T(r.variant)); });
    log.forEach((r) => { if (T(r["Variant ID"]) && !known.some((k) => U(k) === U(r["Variant ID"]))) known.push(T(r["Variant ID"])); });
    const notInAsp = known.filter((v) => !aspVariants.has(U(v)));

    // ---- log checks ----
    const keyCount = {}; activeOrders.forEach((o) => { const k = U(o._key); keyCount[k] = (keyCount[k] || 0) + 1; });
    log.forEach((r) => { r._check = logCheck(r); });
    function logCheck(r) {
      if (T(r["Entry ID"]) === "") return "";
      if (!r._active) return "Void";
      const v = U(r["Variant ID"]);
      const vReq = req.filter((x) => U(x.variant) === v);
      if (r._type === U(ORDER)) {
        if (r._key === "") return "Order number missing";
        if (keyCount[U(r._key)] > 1) return "Duplicate allocation - fix";
        const c = cooisByKey[U(r._key)];
        if (!c) return "Not in current COOIS - review";
        if (U(c.material) !== U(r["Assembly code"])) return "Material changed - review";
        if (c.CLSD) return "CLSD - review";
        if (Math.abs(c.qty - num(r["Order qty"])) > EPS) return "Qty changed - review";
        if (!vReq.some((x) => U(x.code) === U(r["Assembly code"]))) return "Assembly not set up for variant";
        return "OK";
      }
      if (r._type === U(PROGRESS)) {
        if (!vReq.length) return "Assembly setup required";
        const sReq = vReq.filter((x) => U(x.stage) === U(r["Stage"]));
        if (!sReq.length) return "Stage not set up for variant";
        if (U(r["Assembly code"]) !== "" && !sReq.some((x) => U(x.code) === U(r["Assembly code"]))) return "Assembly not in this stage";
        if (!(num(r["REPs kitted"]) > 0)) return "REPs kitted missing";
        if (isNum(r["REP from"])) {
          const f = Number(r["REP from"]), t = isNum(r["REP to"]) ? Number(r["REP to"]) : f;
          if (t < f) return "REP range invalid";
          if (U(r["Assembly code"]) === "" && Math.abs(t - f + 1 - num(r["REPs kitted"])) > EPS) return "REP range differs from REPs kitted";
        }
        if (!aspVariants.has(v)) return "Variant not in current ASP - review";
        return "OK";
      }
      return "Record type not recognised";
    }

    return { thisMon, rptDate, kitLead, weeks, coois, lines, plan, notInAsp, log, stages, req,
      thisWeekLabel: weekLabel(thisMon) };
  }

  function todaySerial() { const d = new Date(); return dateSerial(d.getFullYear(), d.getMonth() + 1, d.getDate()); }

  // ---------- scope KPIs (Dashboard) ----------
  function scope(model, product, project, variant) {
    const all = (x) => T(x) === "" || U(x) === "ALL";
    const rows = model.plan.filter((p) => U(p.product) === U(product) && (all(project) || U(p.projectName) === U(project)) && (all(variant) || U(p.variant) === U(variant)));
    const cfg = rows.filter((p) => p.reqLines > 0);
    const sum = (a, k) => a.reduce((t, p) => t + num(p[k]), 0);
    const k = { rows, plannedAll: sum(rows, "planned"), plannedCfg: sum(cfg, "planned"), complete: sum(cfg, "complete"),
      partial: sum(cfg, "partial"), dueThis: sum(cfg, "dueThis"), behind: sum(cfg, "behind"), shortage: sum(cfg, "shortage"),
      unconfigured: rows.filter((p) => p.reqLines === 0 && p.planned > 0).length };
    k.remaining = Math.max(0, k.plannedCfg - k.complete);
    k.pct = cfg.length && k.plannedCfg > 0 ? k.complete / k.plannedCfg : "not available";
    return k;
  }


  // ---------- kit-week strip (Dashboard) ----------
  function weekStrip(model, data, product, project, variant) {
    const k = scope(model, product, project, variant);
    const cfg = k.rows.filter((p) => p.reqLines > 0);
    const out = [];
    for (let i = -4; i <= 8; i++) {
      const M = model.thisMon + 7 * i; let due = 0, cum = 0;
      cfg.forEach((p) => { const row = data.asp.rows[p.aspRow - 2];
        model.weeks.forEach((w) => { if (w.kitMon === null) return; const q = num(row[w.col]); if (!q) return;
          if (w.kitMon === M) due += q; if (w.kitMon <= M) cum += q; }); });
      out.push({ mon: M, label: weekLabel(M), due, cum, complete: k.complete, gap: Math.max(0, cum - k.complete), thisWeek: i === 0 });
    }
    return out;
  }

  // ---------- data checks (Dashboard) ----------
  function dataChecks(model, data, k) {
    const out = [];
    const ah = (data.asp && data.asp.header) || [];
    const aspOk = ASP_HEADERS.every((h, i) => U(ah[i + 2]) === U(h));
    const nWeeks = model.weeks.filter((w) => w.aspMon !== null).length;
    out.push(aspOk ? { ok: true, text: `ASP columns as expected (${model.plan.length} ASP lines, ${nWeeks} week columns)` }
      : { ok: false, text: "ASP headers are not in the expected columns - load the ASP export as exported (headers on row 1)" });
    const ch = (data.coois && data.coois.header) || [];
    const cOk = COOIS_HEADERS.every((h, i) => U(ch[i]) === U(h));
    out.push(cOk ? { ok: true, text: `COOIS columns Order..System Status in the expected order (${model.coois.length} orders)` }
      : { ok: false, text: "COOIS headings differ from the expected layout (Order .. System Status)" });
    const missing = [...new Set(model.req.map((r) => T(r.variant)))].filter((v) => !model.plan.some((p) => p.valid && U(p.variant) === U(v)));
    out.push(!missing.length ? { ok: true, text: "Every set-up variant is in the current ASP" }
      : { ok: false, text: "Set up but not in current ASP (history kept): " + missing.join(", ") });
    const cnt = {}; model.plan.filter((p) => p.valid && p.reqLines > 0).forEach((p) => { cnt[U(p.variant)] = (cnt[U(p.variant)] || 0) + 1; });
    const dups = Object.keys(cnt).filter((v) => cnt[v] > 1);
    out.push(!dups.length ? { ok: true, text: "No set-up variant appears on more than one ASP line" }
      : { ok: false, text: "A set-up variant appears on more than one ASP line - quantities are added together (" + dups.join(", ") + ")" });
    const logReview = model.log.filter((r) => r._check && !["OK", "Void", ""].includes(r._check)).length;
    const cooisReview = model.coois.filter((o) => o.review === "CLSD - review" || o.review === "Material changed - review").length;
    const rv = logReview + cooisReview;
    out.push(rv === 0 ? { ok: true, text: "No Kitting Log or COOIS rows need review" }
      : { ok: false, text: `${rv} rows need review - see Kitting Log checks and COOIS Review` });
    out.push(k.shortage === 0 ? { ok: true, text: "Every recorded unit in scope is covered by a COOIS order" }
      : { ok: false, text: `${k.shortage} recorded units in scope have no allocated COOIS order yet (not counted as complete)` });
    out.push(k.unconfigured === 0 ? { ok: true, text: "Every planned line in scope has assembly requirements" }
      : { ok: false, text: `${k.unconfigured} planned ASP lines in scope have no requirements - Assembly setup required` });
    return out;
  }

  // ---------- repeater view ----------
  function repeaterView(model, data, variant) {
    const v = U(variant);
    const rows = (data.asp.rows || []).filter((r) => U(r[ASP_INFO_COLS.friendly]) === v && v !== "");
    const system = rows.reduce((t, r) => t + num(r[ASP_INFO_COLS.system]), 0);
    const planned = rows.reduce((t, r) => t + num(r[ASP_INFO_COLS.planned]), 0);
    const built = system - planned;
    const wk = model.weeks.map((w) => rows.reduce((t, r) => t + num(r[w.col]), 0));
    const cum = []; wk.reduce((t, q, i) => (cum[i] = t + q), 0);
    const stages = model.stages.map((s) => s.stage).filter((s) => model.req.some((r) => U(r.variant) === v && U(r.stage) === U(s)));
    if (!stages.length) return { variant: T(variant), system, planned, built, wsum: 0, stages, stageInfo: [], reps: [], setupRequired: true };
    const stageInfo = stages.map((s) => {
      const ls = model.lines.filter((l) => U(l.variant) === v && U(l.stage) === U(s));
      return { stage: s, complete: Math.min(...ls.map((l) => l.coveredReps)), started: Math.max(...ls.map((l) => l.startedReps)),
        shortage: ls.reduce((t, l) => t + l.shortage, 0) };
    });
    const entries = model.log.filter((r) => r._active && r._type === U("Kitting Progress") && U(r["Variant ID"]) === v &&
      U(r["Assembly code"]) === "" && isNum(r["REP from"]) && Number(r["REP from"]) > 0);
    const A = []; // A[n-1][s]
    for (let n = 1; n <= system; n++) A.push(stages.map((s) => entries.some((e) => U(e["Stage"]) === U(s) &&
      Number(e["REP from"]) <= n && (isNum(e["REP to"]) ? Number(e["REP to"]) : Number(e["REP from"])) >= n)));
    stageInfo.forEach((si, j) => { si.assigned = A.filter((a) => a[j]).length; si.pool = Math.max(0, si.complete - si.assigned); });
    const rank = stages.map(() => 0);
    const out = [];
    for (let n = 1; n <= system; n++) {
      const cells = stages.map((s, j) => {
        if (n <= built) return "Built";
        if (A[n - 1][j]) return "Kitted";
        rank[j]++;
        const si = stageInfo[j];
        if (rank[j] <= si.pool) return "Kitted*";
        if (rank[j] <= si.pool + (si.started - si.complete)) return "Part";
        return "";
      });
      const r = { rep: n, cells };
      if (n <= built) { Object.assign(r, { aspWeek: "", kitWeek: "", weeksLeft: "", next: "", status: "Built before plan" }); out.push(r); continue; }
      const p = n - built; const idx = cum.findIndex((c) => c >= p);
      const nextIdx = cells.findIndex((c) => c !== "Kitted" && c !== "Kitted*");
      r.next = nextIdx < 0 ? "All kitted" : stages[nextIdx];
      if (idx < 0 || model.weeks[idx].aspMon === null) { Object.assign(r, { aspWeek: "", kitWeek: "", weeksLeft: "", status: nextIdx < 0 ? "All kitted" : "Not in weekly plan" }); out.push(r); continue; }
      const w = model.weeks[idx];
      r.aspWeek = w.header; r.kitWeek = w.kitLabel; r.weeksLeft = Math.round((w.kitMon - model.thisMon) / 7);
      r.status = nextIdx < 0 ? "All kitted" : r.weeksLeft < 0 ? "Kit behind" : r.weeksLeft === 0 ? "Kit due this week" : "On track";
      out.push(r);
    }
    return { variant: T(variant), system, planned, built, wsum: cum.length ? cum[cum.length - 1] : 0, stages, stageInfo, reps: out };
  }

  // ---------- record-kitting proposal ----------
  function propose(model, inp) {
    const v = U(inp.variant), s = U(inp.stage), a = U(inp.assembly), reps = num(inp.reps);
    const msgs = [];
    const vReq = model.req.filter((r) => U(r.variant) === v);
    if (!v) msgs.push("Choose a variant.");
    else if (!vReq.length) msgs.push("Assembly setup required for this variant (Settings).");
    const sel = vReq.filter((r) => U(r.stage) === s && (a === "" || U(r.code) === a));
    if (vReq.length && !sel.length) msgs.push("This stage / assembly code is not set up for this variant.");
    if (reps < 0) msgs.push("REPs kitted cannot be negative.");
    if (isNum(inp.from)) { const f = Number(inp.from), t = isNum(inp.to) ? Number(inp.to) : f;
      if (t < f) msgs.push("REP to is before REP from.");
      else if (a === "" && reps > 0 && Math.abs(t - f + 1 - reps) > EPS) msgs.push("Warning: REP range covers " + (t - f + 1) + " repeaters but REPs kitted is " + reps + "."); }
    const lines = sel.map((r) => {
      const lm = model.lines.find((l) => U(l.variant) === v && U(l.stage) === U(r.stage) && U(l.code) === U(r.code));
      const units = reps * num(r.qty);
      const need = Math.max(0, lm.recorded + units - lm.allocated);
      return { code: T(r.code), desc: T(r.desc), qty: num(r.qty), units, recorded: lm.recorded, allocated: lm.allocated, need, available: lm.available, sharedBy: lm.sharedBy };
    });
    const codes = new Set(lines.map((l) => U(l.code)));
    const cand = model.coois.filter((o) => codes.has(U(o.material)) && o.allocEntry === "" && !o.CLSD)
      .slice().sort((x, y) => cmp(U(x.material), U(y.material)) || (num(x.releaseDate) - num(y.releaseDate)) || cmp(U(x.order), U(y.order)));
    const used = {}; const picks = [];
    cand.forEach((o) => { const l = lines.find((l) => U(l.code) === U(o.material)); const before = used[U(o.material)] || 0;
      if (before < l.need) picks.push(o); used[U(o.material)] = before + o.qty; });
    lines.forEach((l) => { l.proposed = picks.filter((o) => U(o.material) === U(l.code)).reduce((t, o) => t + o.qty, 0); l.shortageAfter = Math.max(0, l.need - l.proposed); });
    const blocking = msgs.some((m) => !m.startsWith("Warning"));
    const id = nextEntryId(model.log);
    const date = isNum(inp.date) ? Number(inp.date) : model.rptDate;
    const rows = [];
    if (!blocking) {
      if (reps > 0) rows.push(rowObj(id, date, "Kitting Progress", T(inp.variant), T(inp.stage), T(inp.assembly), reps, inp.from, inp.to, "", "", T(inp.note)));
      picks.forEach((o) => rows.push(rowObj(id, date, "COOIS order", T(inp.variant), T(inp.stage), o.material, "", "", "", o.order, o.qty, "")));
    }
    return { messages: msgs, blocking, lines, rows, entryId: id };
  }
  function cmp(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
  function rowObj(id, date, type, v, s, a, reps, f, t, order, qty, note) {
    return { "Entry ID": id, "Entry date": date, "Record type": type, "Variant ID": v, "Stage": s, "Assembly code": a,
      "REPs kitted": reps, "REP from": isNum(f) ? Number(f) : "", "REP to": isNum(t) ? Number(t) : "", "Order": order,
      "Order qty": qty, "Void": "", "Void reason": "", "Note": note };
  }
  function nextEntryId(log) {
    let mx = 0; (log || []).forEach((r) => { const m = /^K(\d+)$/i.exec(T(r["Entry ID"])); if (m) mx = Math.max(mx, Number(m[1])); });
    return "K" + String(mx + 1).padStart(5, "0");
  }

  const api = { compute, scope, repeaterView, propose, weekStrip, dataChecks, nextEntryId, weekLabel, isoMonday, mondayOf, parseWeekHeader, dateSerial,
    statusHas, ASP_HEADERS, COOIS_HEADERS, LOG_COLUMNS, ASP_FIRST_WEEK_COL, ASP_INFO_COLS };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.KitEngine = api;
})(this);
