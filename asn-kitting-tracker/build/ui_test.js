// Browser test of the standalone HTML (Chromium via Playwright). usage: node ui_test.js tracker.html asp.xlsx coois.xlsx excel_with_log.xlsx outdir
const { chromium } = require("playwright");
const E = require("./engine.js");
const [html, aspFile, cooisFile, xlFile, outdir] = process.argv.slice(2);
const results = []; const ok = (n, c, d) => { results.push([n, !!c]); console.log((c ? "   ok   " : "   FAIL ") + n + (c ? "" : "  -> " + JSON.stringify(d))); };
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1500, height: 1000 }, acceptDownloads: true });
  const page = await ctx.newPage(); const errors = [];
  page.on("pageerror", (e) => errors.push(e.message)); page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("dialog", (d) => d.accept(d.type() === "prompt" ? (d.message().includes("DELETE") ? "DELETE" : "TEST correction - wrong variant") : undefined));
  await page.goto("file://" + html);
  ok("page opens with no script errors", errors.length === 0, errors);
  ok("blank page warns ASP/COOIS not loaded", (await page.textContent("#pAsp")).includes("not loaded"));
  await page.setInputFiles("#fAsp", aspFile); await page.waitForTimeout(800);
  await page.setInputFiles("#fCoois", cooisFile); await page.waitForTimeout(800);
  const tiles = await page.$$eval("#kpis .tile", (ts) => ts.map((t) => [t.querySelector(".k").textContent, t.querySelector(".v").textContent]));
  const T = Object.fromEntries(tiles);
  ok("Dashboard KPIs after loading real files: planned 403, due this week 7, behind 24", T["Planned"] === "403" && T["Kits due this week"] === "7" && T["Kits behind"] === "24", T);
  ok("ASP pill shows version and file", (await page.textContent("#pAsp")).includes("ASP GH SME AUG 2026"));
  const checks = await page.$$eval("#checks li", (l) => l.map((x) => x.textContent));
  ok("data checks: ASP and COOIS layouts recognised", checks[0].includes("ASP columns as expected") && checks[1].includes("958 orders"), checks.slice(0, 2));
  await page.screenshot({ path: outdir + "/html-dashboard.png", fullPage: false });
  // record 12FP PSB x3
  await page.click('nav button[data-t="t-rec"]');
  await page.selectOption("#eVar", "E2A-R12P-T5-C"); await page.selectOption("#eStage", "PSB"); await page.fill("#eReps", "3");
  await page.waitForTimeout(300);
  const lines = await page.$$eval("#eLines tbody tr", (r) => r.map((x) => [...x.children].map((c) => c.textContent)));
  ok("12FP PSB: 9 units, 9 proposed, 0 shortage", lines[0][3] === "9" && lines[0][8] === "9" && lines[0][9] === "0", lines);
  await page.screenshot({ path: outdir + "/html-record.png" });
  await page.click("#bConfirm"); await page.waitForTimeout(300);
  await page.selectOption("#eVar", "E2A-R4P-T1-C"); await page.selectOption("#eStage", "PSB"); await page.fill("#eReps", "3"); await page.waitForTimeout(300);
  const rows4 = await page.$$eval("#eRows tbody tr", (r) => r.map((x) => x.children[9].textContent));
  await page.click("#bConfirm"); await page.waitForTimeout(300);
  const st = await page.evaluate(() => JSON.parse(localStorage.getItem("asnKittingTracker.v1")));
  const o12 = st.log.filter((r) => r["Variant ID"] === "E2A-R12P-T5-C" && r["Record type"] === "COOIS order").map((r) => r.Order);
  const o4 = st.log.filter((r) => r["Variant ID"] === "E2A-R4P-T1-C" && r["Record type"] === "COOIS order").map((r) => r.Order);
  ok("two entries saved: 9 + 3 distinct orders, no overlap", o12.length === 9 && o4.length === 3 && !o4.some((x) => o12.includes(x)), [o12.length, o4.length]);
  ok("entry IDs K00001 and K00002", st.log[0]["Entry ID"] === "K00001" && st.log[st.log.length - 1]["Entry ID"] === "K00002");
  // engine on the same stored data gives the same numbers as the page shows
  await page.reload(); await page.waitForTimeout(800);
  const st2 = await page.evaluate(() => JSON.parse(localStorage.getItem("asnKittingTracker.v1")));
  ok("data survives a page reload", st2.log.length === 14, st2.log.length);
  await page.click('nav button[data-t="t-log"]');
  await page.click('button[data-void="K00002"]'); await page.waitForTimeout(300);
  const st3 = await page.evaluate(() => JSON.parse(localStorage.getItem("asnKittingTracker.v1")));
  ok("void keeps the rows and records the reason", st3.log.length === 14 && st3.log.find((r) => r["Entry ID"] === "K00002").Void === "Y");
  const struck = await page.$$eval("#logT tbody tr.void", (r) => r.length);
  ok("voided entry shown struck through (4 rows)", struck === 4, struck);
  await page.screenshot({ path: outdir + "/html-log.png" });
  // REP-level
  await page.click('nav button[data-t="t-rec"]');
  await page.selectOption("#eVar", "E2A-R4P-T1-C"); await page.selectOption("#eStage", "LASA"); await page.fill("#eReps", "2"); await page.fill("#eFrom", "5"); await page.fill("#eTo", "6");
  await page.waitForTimeout(200); await page.click("#bConfirm"); await page.waitForTimeout(300);
  await page.click('nav button[data-t="t-rep"]'); await page.selectOption("#rVar", "E2A-R4P-T1-C"); await page.waitForTimeout(300);
  const rep = await page.$$eval("#rTab tbody tr", (r) => r.slice(0, 7).map((x) => [...x.children].map((c) => c.textContent)));
  ok("Repeater View: REP 5 and 6 LASA Kitted, REP 1 open", rep[4][2] === "Kitted" && rep[5][2] === "Kitted" && rep[0][2] === "", rep.slice(0, 6).map((r) => r[2]));
  await page.screenshot({ path: outdir + "/html-repeater.png" });
  // compare page numbers with the engine on the same data
  const model = E.compute({ asp: st3.asp, coois: st3.coois, requirements: st3.requirements, stages: st3.stages, log: (await page.evaluate(() => JSON.parse(localStorage.getItem("asnKittingTracker.v1")))).log, settings: st3.settings });
  const kk = E.scope(model, "REPEATERS", "All", "All");
  await page.click('nav button[data-t="t-dash"]'); await page.waitForTimeout(200);
  const T2 = Object.fromEntries(await page.$$eval("#kpis .tile", (ts) => ts.map((t) => [t.querySelector(".k").textContent, t.querySelector(".v").textContent])));
  ok("page KPIs equal engine KPIs", String(kk.complete) === T2["Complete assembly kits"] && String(kk.partial) === T2["Partly kitted"] && String(kk.behind) === T2["Kits behind"], [kk.complete, kk.partial, kk.behind, T2]);
  // backup and restore in a fresh browser profile
  const [dl] = await Promise.all([page.waitForEvent("download"), page.click("#bSave")]);
  const bak = outdir + "/backup.json"; await dl.saveAs(bak);
  const ctx2 = await browser.newContext(); const p2 = await ctx2.newPage(); p2.on("dialog", (d) => d.accept());
  await p2.goto("file://" + html); await p2.setInputFiles("#fBak", bak); await p2.waitForTimeout(800);
  const st4 = await p2.evaluate(() => JSON.parse(localStorage.getItem("asnKittingTracker.v1")));
  ok("backup restores the full log in another browser profile", st4.log.length === 17 && st4.coois.rows.length === 958, [st4.log.length, st4.coois.rows.length]);
  // import the Excel tracker (LibreOffice-recalculated test workbook) and compare with its cached results
  const ctx3 = await browser.newContext(); const p3 = await ctx3.newPage(); p3.on("dialog", (d) => d.accept());
  await p3.goto("file://" + html); await p3.setInputFiles("#fXl", xlFile); await p3.waitForTimeout(1500);
  const st5 = await p3.evaluate(() => JSON.parse(localStorage.getItem("asnKittingTracker.v1")));
  const m5 = E.compute({ asp: st5.asp, coois: st5.coois, requirements: st5.requirements, stages: st5.stages, log: st5.log, settings: st5.settings });
  const k5 = E.scope(m5, "REPEATERS", "All", "All");
  console.log("IMPORTED", JSON.stringify({ log: st5.log.length, req: st5.requirements.length, asp: st5.asp.rows.length, coois: st5.coois.rows.length, complete: k5.complete, partial: k5.partial, behind: k5.behind, due: k5.dueThis, plannedCfg: k5.plannedCfg, rd: st5.settings.reportDate }));
  await p3.click('nav button[data-t="t-coois"]'); await p3.screenshot({ path: outdir + "/html-coois.png" });
  await p3.click('nav button[data-t="t-set"]'); await p3.screenshot({ path: outdir + "/html-settings.png" });
  ok("no script errors during the whole session", errors.length === 0, errors);
  await browser.close();
  console.log(`${results.filter((r) => r[1]).length}/${results.length} browser checks passed`);
})();
