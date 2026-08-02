#!/usr/bin/env python3
"""Generate archive/index.html (The Build Archive) from the coachclaude training DB.

Data: race-relative weeks. T-k is the 7-day window ending (race_day - 7k), so
T-0 always ends on the finish line, whatever weekday the race falls on (Boston
is a Monday race, NYC a Sunday one). Rerun after adding a build. Design tokens
and component rules: see DESIGN.md at the repo root.

Run: python3 tools/build_archive.py
"""
import sqlite3
import os
import json

DB = os.path.expanduser("~/Documents/Claude/Projects/coachclaude/data/training.db")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archive", "index.html")

BUILDS = [
    {
        "key": "bos",
        "title": "Boston 2026",
        "sub": "22 weeks out &rarr; Marathon Monday &middot; Apr 20 2026",
        "race_date": "2026-04-20",
        "start": "2025-11-12",
        "result": "2:04:35",
        "result_label": "Boston 2026",
        "notes": [
            "T-22 &middot; First jogs back, 10 days after NYC.",
            "T-7 &middot; US Half Marathon Champs mid-build, 1:02:10.",
            "T-4 &middot; Peak: 119.7 miles with a 24-mile long run.",
            "T-0 &middot; Boston runs on a Monday, so T-0 ends on the finish line. 2:04:35.",
        ],
    },
    {
        "key": "nyc",
        "title": "NYC 2025",
        "sub": "14 weeks out &rarr; the debut &middot; Nov 2 2025",
        "race_date": "2025-11-02",
        "start": "2025-07-21",
        "result": "2:09:59",
        "result_label": "The debut",
        "notes": [
            "T-14 &middot; First week back off a full 2-week break. Every build starts smaller than you think.",
            "T-4 &middot; The peak: back-to-back 115.3 weeks, capped with a 24-mile long run.",
            "T-0 &middot; 73.8 for the week, 26.2 of them between Staten Island and Central Park. 2:09:59, first marathon.",
        ],
    },
]

Y_MAX = 130  # shared scale across builds so the charts compare honestly


def weeks_for(build):
    con = sqlite3.connect(DB)
    rows = con.execute(
        """
        SELECT CAST((julianday(?) - julianday(start_date))/7 AS INT) AS t,
               ROUND(SUM(distance_mi),1), COUNT(*), ROUND(MAX(distance_mi),1)
        FROM activities
        WHERE type LIKE '%run%' AND start_date BETWEEN ? AND ?
        GROUP BY t ORDER BY t DESC
        """,
        (build["race_date"], build["start"], build["race_date"]),
    ).fetchall()
    con.close()
    return [{"t": t, "mi": mi, "runs": runs, "lr": lr} for t, mi, runs, lr in rows]


def build_section(build, weeks):
    peak = max(w["mi"] for w in weeks)
    biggest_lr = max(w["lr"] for w in weeks[:-1])  # exclude T-0 (the race itself)
    bars, ticks, trs = [], [], []
    peak_labeled = False
    for w in weeks:
        h = round(w["mi"] / Y_MAX * 100, 1)
        cls = "bar race" if w["t"] == 0 else ("bar peak" if w["mi"] == peak else "bar")
        label = ""
        if w["mi"] == peak and not peak_labeled:
            label = '<span class="bar-val">%s</span>' % w["mi"]
            peak_labeled = True
        if w["t"] == 0:
            label = '<span class="bar-val race-val">26.2</span>'
        bars.append(
            '<div class="%s" style="height:%s%%" data-t="%d" data-mi="%s" data-runs="%d" data-lr="%s" tabindex="0" role="img" aria-label="T-%d: %s miles, %d runs, longest %s">%s</div>'
            % (cls, h, w["t"], w["mi"], w["runs"], w["lr"], w["t"], w["mi"], w["runs"], w["lr"], label)
        )
        ticks.append('<span>%s</span>' % ("T-%d" % w["t"] if (w["t"] % 4 == 0) else ""))
        trs.append(
            '<tr data-mi="%s" data-lr="%s"><td class="tw">T-%d</td><td>%s</td><td>%s</td><td>%d</td><td class="yours">&mdash;</td></tr>'
            % (w["mi"], w["lr"], w["t"], w["mi"], w["lr"], w["runs"])
        )
    notes = "\n      ".join('<li>%s</li>' % n for n in build["notes"])
    return """
<section class="wrap build" id="%(key)s">
  <h2 class="sec-head disp">%(title)s</h2>
  <p class="sec-sub label">%(sub)s</p>
  <div class="datastrip">
    <div class="stat"><div class="n">%(nweeks)d</div><div class="l">Weeks</div></div>
    <div class="stat"><div class="n">%(peak)s</div><div class="l">Peak week</div></div>
    <div class="stat"><div class="n">%(lr)s</div><div class="l">Biggest long run</div></div>
    <div class="stat"><div class="n">%(result)s</div><div class="l">%(result_label)s</div></div>
  </div>
  <div class="chartwrap" aria-hidden="false">
    <div class="grid"><i style="bottom:%(g40)s%%"><em>40</em></i><i style="bottom:%(g80)s%%"><em>80</em></i><i style="bottom:%(g120)s%%"><em>120</em></i></div>
    <div class="chart" data-build="%(key)s">%(bars)s</div>
    <div class="ticks label">%(ticks)s</div>
  </div>
  <ul class="notes label">
      %(notes)s
  </ul>
  <details class="tablebox" open>
    <summary class="label">Week-by-week table</summary>
    <table class="tminus data">
      <thead><tr><th>Week</th><th>Miles</th><th>Long run</th><th>Runs</th><th class="yours-h">Yours</th></tr></thead>
      <tbody>%(trs)s</tbody>
    </table>
  </details>
</section>""" % {
        "key": build["key"], "title": build["title"], "sub": build["sub"],
        "nweeks": len(weeks), "peak": peak, "lr": biggest_lr,
        "result": build["result"], "result_label": build["result_label"],
        "g40": round(40 / Y_MAX * 100, 1), "g80": round(80 / Y_MAX * 100, 1), "g120": round(120 / Y_MAX * 100, 1),
        "bars": "".join(bars), "ticks": "".join(ticks), "trs": "".join(trs),
        "notes": notes,
    }


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="The Build Archive: both of Charles Hicks's marathon builds, week by week, counted in weeks-to-race. A 2:09:59 debut in New York and a 2:04:35 in Boston. Find your T-week, apply your percentage, run yours.">
<meta property="og:title" content="The Build Archive &mdash; U Run Club">
<meta property="og:description" content="2 real marathon builds, week by week, in weeks-to-race. Find your T-week. Run yours.">
<meta property="og:image" content="https://urunclub.com/og.png">
<meta property="og:url" content="https://urunclub.com/archive/">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2216%22 fill=%22%231233E8%22/><text x=%2250%22 y=%2274%22 font-size=%2270%22 font-family=%22Arial Narrow,sans-serif%22 font-weight=%22bold%22 text-anchor=%22middle%22 fill=%22white%22>U</text></svg>">
<title>The Build Archive &mdash; U Run Club</title>
<style>
  :root {
    --paper:#FFFFFF;
    --tint:#F3F5F9;
    --ink:#0A1120;
    --muted:#525E74;
    --faint:#8B94A8;
    --line:rgba(10,17,32,0.12);
    --blue:#1233E8;
    --blue-deep:#0C24AC;
    --shadow:0 1px 2px rgba(10,17,32,0.05), 0 8px 24px rgba(10,17,32,0.06);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  html { -webkit-font-smoothing:antialiased; }
  body { background:var(--paper); color:var(--ink); font-family:'Helvetica Neue', -apple-system, Arial, sans-serif; font-size:16.5px; line-height:1.65; }
  .wrap { max-width:680px; margin:0 auto; padding:0 24px; }
  .u { color:var(--blue); }
  .disp { font-family:'Avenir Next Condensed','DIN Condensed','Arial Narrow',sans-serif; font-weight:800; text-transform:uppercase; }
  .data { font-family:'DIN Alternate', Menlo, sans-serif; }
  .label { font-family:'DIN Alternate', Menlo, sans-serif; font-size:11px; letter-spacing:0.18em; text-transform:uppercase; color:var(--faint); }
  a { color:inherit; }

  .topbar { display:flex; justify-content:space-between; align-items:center; padding:18px 0; }
  .topbar .mark { font-family:'Avenir Next Condensed',sans-serif; font-weight:800; text-transform:uppercase; font-size:20px; letter-spacing:0.05em; text-decoration:none; }
  .pill { font-family:'DIN Alternate', Menlo, sans-serif; font-size:11px; letter-spacing:0.14em; text-transform:uppercase; color:var(--blue); border:1px solid var(--blue); border-radius:999px; padding:6px 14px 5px; }
  .topline { border-bottom:1px solid var(--line); }

  .hero { padding:64px 0 40px; }
  .eyebrow { display:flex; align-items:center; gap:10px; font-family:'DIN Alternate', Menlo, sans-serif; font-size:12px; font-weight:700; letter-spacing:0.22em; text-transform:uppercase; color:var(--blue); margin-bottom:26px; }
  .eyebrow::before { content:"+"; color:var(--faint); font-weight:400; }
  .wordmark { line-height:0.86; letter-spacing:0.005em; }
  .wordmark > span { display:block; font-size:clamp(52px, 14vw, 96px); }
  .ghost { color:transparent; -webkit-text-stroke:3px var(--blue); }
  .device-note { font-family:'DIN Alternate', Menlo, sans-serif; font-size:12px; letter-spacing:0.1em; color:var(--faint); margin-top:16px; text-transform:uppercase; }
  .hero-pitch { margin-top:30px; font-size:19px; color:var(--muted); max-width:31em; }
  .hero-pitch strong { color:var(--ink); font-weight:600; }

  .rows { display:flex; flex-direction:column; }
  .row { display:flex; gap:20px; padding:22px 0; border-top:1px solid var(--line); }
  .row:last-child { border-bottom:1px solid var(--line); }
  .when { flex:0 0 84px; font-family:'DIN Alternate', Menlo, sans-serif; font-weight:700; font-size:12px; letter-spacing:0.08em; color:var(--blue); text-transform:uppercase; padding-top:5px; }
  .when b { display:inline-block; background:rgba(18,51,232,0.08); border-radius:6px; padding:4px 9px 3px; font-weight:700; }
  .row h3 { font-weight:700; font-size:17px; margin-bottom:4px; letter-spacing:-0.01em; }
  .row p { color:var(--muted); font-size:15.5px; max-width:32em; }

  /* tier control */
  .tierbar { background:var(--tint); margin-top:48px; padding:28px 0 30px; position:sticky; top:0; z-index:5; border-bottom:1px solid var(--line); }
  .tierbar .wrap { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
  .tierbar .label { flex:0 0 auto; }
  .tiersel { display:flex; gap:8px; flex-wrap:wrap; }
  .tbtn { font-family:'DIN Alternate', Menlo, sans-serif; font-weight:700; font-size:13px; letter-spacing:0.1em; cursor:pointer; background:var(--paper); color:var(--ink); border:1px solid var(--line); border-radius:8px; padding:9px 14px 7px; box-shadow:var(--shadow); }
  .tbtn[aria-pressed="true"] { background:var(--blue); border-color:var(--blue); color:#fff; box-shadow:0 2px 0 var(--blue-deep); }

  section.build { padding:56px 0 8px; }
  .sec-head { font-size:46px; line-height:1; margin-bottom:8px; }
  .sec-sub { margin-bottom:26px; }

  .datastrip { margin-top:6px; display:flex; background:var(--paper); border:1px solid var(--line); border-radius:10px; overflow:hidden; box-shadow:var(--shadow); }
  .stat { flex:1; padding:16px 8px 13px; text-align:center; border-left:1px solid var(--line); }
  .stat:first-child { border-left:none; }
  .stat .n { font-family:'DIN Alternate', Menlo, sans-serif; font-weight:700; font-size:24px; font-variant-numeric:tabular-nums; line-height:1.05; color:var(--ink); }
  .stat .l { font-family:'DIN Alternate', Menlo, sans-serif; font-size:10px; letter-spacing:0.14em; color:var(--faint); text-transform:uppercase; margin-top:4px; }

  /* chart */
  .chartwrap { position:relative; margin-top:34px; padding-top:14px; }
  .grid { position:absolute; left:0; right:0; top:14px; bottom:22px; pointer-events:none; }
  .grid i { position:absolute; left:0; right:0; border-top:1px solid rgba(10,17,32,0.07); }
  .grid i em { position:absolute; left:0; top:-16px; font-style:normal; font-family:'DIN Alternate', Menlo, sans-serif; font-size:10px; letter-spacing:0.08em; color:var(--faint); }
  .chart { display:flex; align-items:flex-end; gap:2px; height:200px; border-bottom:1px solid var(--line); }
  .bar { flex:1; min-width:5px; background:var(--blue); border-radius:4px 4px 0 0; position:relative; cursor:pointer; transition:height 0.45s cubic-bezier(0.22,1,0.36,1); }
  @media (prefers-reduced-motion: reduce) { .bar { transition:none; } }
  .bar:hover, .bar:focus-visible { background:var(--blue-deep); outline:none; }
  .bar.race { background:var(--ink); }
  .bar-val { position:absolute; top:-20px; left:50%; transform:translateX(-50%); font-family:'DIN Alternate', Menlo, sans-serif; font-weight:700; font-size:11px; color:var(--muted); white-space:nowrap; }
  .ticks { display:flex; gap:2px; margin-top:6px; }
  .ticks span { flex:1; min-width:5px; text-align:center; font-size:9px; letter-spacing:0.04em; }
  .tooltip { position:fixed; z-index:20; pointer-events:none; background:var(--ink); color:#fff; border-radius:8px; padding:10px 13px 9px; font-family:'DIN Alternate', Menlo, sans-serif; font-size:12px; letter-spacing:0.04em; line-height:1.5; box-shadow:var(--shadow); display:none; }
  .tooltip b { color:#fff; font-size:14px; }
  .tooltip .tt-yours { color:#9DB0FF; }

  .notes { margin:18px 0 0; list-style:none; }
  .notes li { padding:7px 0 6px; border-top:1px dashed var(--line); letter-spacing:0.08em; line-height:1.7; }

  /* table */
  .tablebox { margin-top:28px; }
  .tablebox summary { cursor:pointer; padding-bottom:10px; }
  .tminus { width:100%; border-collapse:collapse; font-size:13.5px; }
  .tminus th { text-align:right; font-family:'DIN Alternate', Menlo, sans-serif; font-size:10px; letter-spacing:0.14em; text-transform:uppercase; color:var(--faint); font-weight:700; padding:8px 10px; border-bottom:1px solid var(--line); }
  .tminus th:first-child { text-align:left; }
  .tminus td { text-align:right; padding:7px 10px 6px; border-bottom:1px solid rgba(10,17,32,0.06); font-variant-numeric:tabular-nums; }
  .tminus td.tw { text-align:left; font-weight:700; color:var(--blue); }
  .tminus td.yours { color:var(--faint); }
  body.tiered .tminus td.yours { color:var(--blue); font-weight:700; }

  .joiner { background:var(--tint); margin-top:64px; padding:56px 0 64px; }
  .capture { margin-top:26px; display:flex; flex-direction:column; gap:12px; }
  .capture input { width:100%; padding:16px 18px; background:var(--paper); border:1px solid var(--line); border-radius:8px; color:var(--ink); font-family:inherit; font-size:16px; box-shadow:inset 0 1px 2px rgba(10,17,32,0.04); }
  .capture input::placeholder { color:var(--faint); }
  .capture input:focus { outline:2px solid var(--blue); outline-offset:1px; }
  .btn { display:block; width:100%; padding:16px 20px 15px; background:var(--blue); color:#fff; font-family:'Avenir Next Condensed',sans-serif; font-weight:800; text-transform:uppercase; font-size:20px; letter-spacing:0.09em; text-align:center; border:none; border-radius:8px; text-decoration:none; box-shadow:0 2px 0 var(--blue-deep), 0 10px 24px rgba(18,51,232,0.25); cursor:pointer; }
  .capture .ok { font-size:16px; color:var(--ink); font-weight:600; padding:16px 18px; background:rgba(18,51,232,0.06); border:1px solid var(--blue); border-radius:8px; }
  .capture .ok b { color:var(--blue); }
  .joiner p.jsub { color:var(--muted); max-width:32em; }

  .fine { padding:44px 0 20px; }
  .fine p { font-size:13px; color:var(--faint); max-width:40em; margin-bottom:10px; }
  footer { margin-top:20px; border-top:1px solid var(--line); padding:26px 0 46px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }
  footer .fm { font-family:'Avenir Next Condensed',sans-serif; font-weight:800; text-transform:uppercase; font-size:18px; letter-spacing:0.05em; }
  footer .fl { font-family:'DIN Alternate', Menlo, sans-serif; font-size:12px; letter-spacing:0.08em; color:var(--faint); }
  footer .fl span { margin-left:16px; }

  @media (min-width:900px) {
    .wrap { max-width:1040px; }
    .hero { padding:88px 0 56px; }
    .sec-head { font-size:58px; }
    .capture { flex-direction:row; max-width:620px; }
    .capture input { flex:1; }
    .btn { width:auto; padding:16px 36px 15px; white-space:nowrap; }
    .chart { height:260px; }
    .row { gap:40px; }
    .when { flex:0 0 104px; }
  }
</style>
</head>
<body>

<div class="topline">
  <div class="wrap topbar">
    <a class="mark" href="/">U R<span class="u">U</span>N CLUB</a>
    <div class="pill">Welcome to the club</div>
  </div>
</div>

<header class="wrap hero">
  <div class="eyebrow">Free forever &middot; Straight off the watch</div>
  <h1 class="wordmark disp">
    <span>THE B<span class="ghost">U</span>ILD</span>
    <span>ARCHIVE</span>
  </h1>
  <p class="device-note">You can't spell build without U.</p>
  <p class="hero-pitch">My last 2 marathon builds, week by week, from first jog back to the finish line: a <strong>2:09:59 debut in New York</strong> and a <strong>2:04:35 in Boston</strong> 5 months later. Counted in weeks-to-race, not calendar dates, so they line up with your build whenever your race is.</p>
  <div class="rows" style="margin-top:34px;">
    <div class="row">
      <div class="when"><b>Step 1</b></div>
      <div><h3>Count back from your race.</h3><p>Your race date minus today, in weeks. That number is your T-week. 9 weeks out means T-9.</p></div>
    </div>
    <div class="row">
      <div class="when"><b>Step 2</b></div>
      <div><h3>Look up my T-week.</h3><p>Same week, either build. Miles, runs, long run. That's what the week looked like from inside.</p></div>
    </div>
    <div class="row">
      <div class="when"><b>Step 3</b></div>
      <div><h3>Apply your number.</h3><p>Pick your tier below and every week recalculates to your percentage. Proven training that works, at a volume that works for you.</p></div>
    </div>
  </div>
</header>

<div class="tierbar">
  <div class="wrap">
    <span class="label">Your number</span>
    <div class="tiersel" role="group" aria-label="Scale weeks to your tier">
      <button class="tbtn" data-pct="100" aria-pressed="true">RAW</button>
      <button class="tbtn" data-pct="20" aria-pressed="false">THE 20</button>
      <button class="tbtn" data-pct="30" aria-pressed="false">THE 30</button>
      <button class="tbtn" data-pct="40" aria-pressed="false">THE 40</button>
      <button class="tbtn" data-pct="60" aria-pressed="false">THE 60</button>
    </div>
  </div>
</div>

@@SECTIONS@@

<div class="joiner">
  <section class="wrap" style="padding:0;">
    <h2 class="sec-head disp">R<span class="ghost">u</span>n the next one with <span class="u">u</span>s</h2>
    <p class="jsub">The next build in this archive is happening right now: Chicago, Oct 11. The Log drops every Monday. Members run their percentage.</p>
    <form class="capture" action="https://app.kit.com/forms/9751172/subscriptions" method="post" data-urc-form>
      <input type="email" name="email_address" required placeholder="your@email.com" aria-label="Email address">
      <button class="btn" type="submit">Join the club</button>
    </form>
  </section>
</div>

<div class="wrap fine">
  <p>Weeks are counted back from race day: T-0 is the 7 days ending on the finish line. Both charts share 1 scale so the builds compare honestly. Your tier scales the weekly miles and the long run. Run counts don't scale; that column just shows how I split each week up.</p>
  <p>Pick the tier at or below your current weekly volume. Not medical advice, not a plan. It's a record of what 2 builds actually looked like. The down weeks are real and they're part of why the peaks worked.</p>
</div>

<div class="wrap">
  <footer>
    <div class="fm">U R<span class="u">U</span>N CLUB</div>
    <div class="fl">@_charleshicks<span>#RnningNeedsU</span><span>urunclub.com</span></div>
  </footer>
</div>

<div class="tooltip" id="tt" role="status"></div>

<script>
var pct = 100;
var tt = document.getElementById('tt');

function fmt(n) { return (Math.round(n * 10) / 10).toFixed(1); }

var Y_MAX = 130;

function applyTier() {
  document.body.classList.toggle('tiered', pct !== 100);
  document.querySelectorAll('.tminus tbody tr').forEach(function (tr) {
    var mi = parseFloat(tr.dataset.mi);
    tr.querySelector('.yours').textContent = pct === 100 ? '\\u2014' : fmt(mi * pct / 100);
  });
  document.querySelectorAll('.bar').forEach(function (bar) {
    var mi = parseFloat(bar.dataset.mi) * pct / 100;
    bar.style.height = (mi / Y_MAX * 100) + '%';
    var val = bar.querySelector('.bar-val');
    if (val) {
      if (bar.classList.contains('race')) {
        val.textContent = pct === 100 ? '26.2' : fmt(mi);
      } else {
        val.textContent = fmt(mi);
      }
    }
  });
}

document.querySelectorAll('.tbtn').forEach(function (b) {
  b.addEventListener('click', function () {
    pct = parseInt(b.dataset.pct, 10);
    document.querySelectorAll('.tbtn').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
    applyTier();
  });
});

function showTT(bar, x, y) {
  var mi = parseFloat(bar.dataset.mi), lr = parseFloat(bar.dataset.lr);
  var html = '<b>T-' + bar.dataset.t + '</b> &middot; ' + fmt(mi) + ' mi &middot; ' + bar.dataset.runs + ' runs &middot; LR ' + fmt(lr);
  if (pct !== 100) html += '<br><span class="tt-yours">THE ' + pct + ': ' + fmt(mi * pct / 100) + ' mi &middot; LR ' + fmt(lr * pct / 100) + '</span>';
  tt.innerHTML = html;
  tt.style.display = 'block';
  var w = tt.offsetWidth;
  tt.style.left = Math.min(Math.max(8, x - w / 2), window.innerWidth - w - 8) + 'px';
  tt.style.top = (y - tt.offsetHeight - 14) + 'px';
}
function hideTT() { tt.style.display = 'none'; }

document.querySelectorAll('.bar').forEach(function (bar) {
  bar.addEventListener('mouseenter', function () { var r = bar.getBoundingClientRect(); showTT(bar, r.left + r.width / 2, r.top); });
  bar.addEventListener('mouseleave', hideTT);
  bar.addEventListener('focus', function () { var r = bar.getBoundingClientRect(); showTT(bar, r.left + r.width / 2, r.top); });
  bar.addEventListener('blur', hideTT);
  bar.addEventListener('touchstart', function (e) { var r = bar.getBoundingClientRect(); showTT(bar, r.left + r.width / 2, r.top); e.stopPropagation(); }, { passive: true });
});
document.addEventListener('touchstart', hideTT, { passive: true });
window.addEventListener('scroll', hideTT, { passive: true });

document.querySelectorAll('[data-urc-form]').forEach(function (f) {
  f.addEventListener('submit', function (e) {
    e.preventDefault();
    var btn = f.querySelector('button');
    btn.disabled = true; btn.textContent = 'Joining\\u2026';
    fetch(f.action, { method: 'POST', body: new FormData(f), headers: { 'Accept': 'application/json' } })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function () {
        f.innerHTML = '<div class="ok">You\\u2019re in. <b>The Number drops Monday.</b> Check your inbox to confirm, and hit reply with your ambition. #RnningNeedsU</div>';
      })
      .catch(function () {
        btn.disabled = false; btn.textContent = 'Join the club';
        f.submit();
      });
  });
});
</script>
</body>
</html>
"""


def main():
    sections = "".join(build_section(b, weeks_for(b)) for b in BUILDS)
    html = PAGE.replace("@@SECTIONS@@", sections)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(html)
    print("wrote %s (%d bytes)" % (OUT, len(html)))


if __name__ == "__main__":
    main()
