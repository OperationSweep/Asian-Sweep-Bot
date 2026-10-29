// node engine_run.js scenario.json -> JSON of everything the Excel workbook also shows (used by compare.py)
const E = require("./engine.js"); const fs = require("fs");
const sc = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const data = { asp: sc.asp, coois: sc.coois, requirements: sc.requirements, stages: sc.stages, log: sc.log || [], settings: sc.settings || {} };
const m = E.compute(data);
const d = sc.dash || {};
const k = E.scope(m, d.C5 || "REPEATERS", d.F5 || "All", d.I5 || "All");
const rvVar = sc.rvVariant || "E2A-R12P-T5-C";
const rvw = E.repeaterView(m, data, rvVar);
const en = sc.entry || {};
const pr = E.propose(m, { variant: en.variant, stage: en.stage, assembly: en.assembly, reps: en.reps, from: en.from, to: en.to, date: en.date, note: en.note });
const out = {
  plan: m.plan.map((p) => ({ aspRow: p.aspRow, wsum: p.wsum, dEnd: p.dEnd, dBefore: p.dBefore, dNext4: p.dNext4, valid: p.valid ? 1 : 0, reqLines: p.reqLines,
    built: p.built, complete: p.complete, partial: p.partial, remaining: p.remaining, pct: p.pct, dueThis: p.dueThis, behind: p.behind, shortage: p.shortage,
    topDiffers: p.topDiffers ? 1 : 0, status: p.status })),
  lines: m.lines.map((l) => [l.variant, l.stage, l.code, l.recorded, l.allocated, l.covered, l.shortage, l.coveredReps, l.startedReps, l.available, l.sharedBy]),
  coois: m.coois.map((o) => [o.order, o.review, o.allocEntry, o.PCNF ? "Yes" : "", o.CNF ? "Yes" : "", o.CLSD ? "Yes" : ""]),
  logCheck: m.log.map((r) => [r["Entry ID"] || "", r._active, r._check]),
  kpi: { plannedAll: k.plannedAll, plannedCfg: k.plannedCfg, complete: k.complete, partial: k.partial, dueThis: k.dueThis, behind: k.behind, shortage: k.shortage },
  rv: { summary: rvw.stageInfo.map((s) => [s.stage, s.complete, s.assigned, s.pool, s.started - s.complete, s.shortage]),
        reps: rvw.reps.map((r) => [r.rep, r.aspWeek].concat(r.cells, [r.next, r.kitWeek, r.weeksLeft, r.status])) },
  proposal: { blocking: pr.blocking, lines: pr.lines.map((l) => [l.code, l.units, l.recorded, l.allocated, l.need, l.available, l.proposed, l.shortageAfter]),
    rows: pr.rows.map((r) => E.LOG_COLUMNS.map((c) => r[c])) },
  thisWeek: m.thisWeekLabel,
};
process.stdout.write(JSON.stringify(out));
