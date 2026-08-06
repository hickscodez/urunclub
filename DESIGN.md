# U Run Club — design language

The club's visual identity. Deliberately decoupled from the caroclaude carousel brand
(dark/track-red/Bebas); the club is white paper and cobalt. Locked 2026-07-31 ("v2 light").
Every page on urunclub.com follows this file. If a page needs something this file doesn't
cover, extend the system here first, then build.

## Tokens (copy the `:root` block verbatim)

```css
--paper:#FFFFFF;      /* page background, cards */
--tint:#F3F5F9;       /* alternate section background, sticky bars */
--ink:#0A1120;        /* primary text, the race-day bar */
--muted:#525E74;      /* body copy on white */
--faint:#8B94A8;      /* labels, fine print */
--line:rgba(10,17,32,0.12);   /* all borders and rules */
--blue:#1233E8;       /* THE cobalt. Accent, data marks, CTAs */
--blue-deep:#0C24AC;  /* hover states, button under-shadow */
--shadow:0 1px 2px rgba(10,17,32,0.05), 0 8px 24px rgba(10,17,32,0.06);
```

Cobalt #1233E8 is the only chart/data color (validated: passes lightness band, chroma,
and 3:1 contrast on white). Light theme only; the brand is paper, no dark mode.

## Type stack (all system fonts, no webfonts)

| Role | Class | Stack | Rules |
|---|---|---|---|
| Display | `.disp` | Avenir Next Condensed 800 → DIN Condensed → Arial Narrow | Always uppercase. Hero `clamp()`-sized, section heads 46/58px |
| Body | (default) | Helvetica Neue → -apple-system → Arial | 16.5px / 1.65 |
| Data | `.data` | DIN Alternate → Menlo | Numbers, tables. Always `font-variant-numeric:tabular-nums` for columns |
| Label | `.label` | DIN Alternate, 11px, tracking 0.18em | Uppercase, `--faint`. Eyebrows, captions, table heads |

## The U

- Ghost U: `color:transparent; -webkit-text-stroke:3px var(--blue)` (2px at pull-quote size).
  1 ghost U per headline, max. It belongs to the slogan; don't scatter it.
- Solid cobalt U: `.u` for the second emphasis in the same lockup (see wordmark: ghost U in
  RUNNING, solid U in "NEEDS U").
- Wordmark: "U R<span class=u>U</span>N CLUB" in topbar and footer, always.

## Layout

- `.wrap`: max-width 680px mobile-first, 1040px at ≥900px, 24px side padding.
- Sections: 56-64px top padding. Alternate `--paper` and `--tint` full-bleed bands.
- 1 breakpoint: 900px. Nothing else.

## Components (steal from index.html / archive/index.html, don't reinvent)

- **topbar** — wordmark left, `.pill` status right, `.topline` bottom rule.
- **eyebrow** — cobalt label with `+` prefix, above every hero.
- **device-note** — 1 dry line under the wordmark, DIN 12px. Earn it.
- **datastrip** — 4 stats in a bordered card: big DIN number + tiny label. The proof row.
- **ticker** — cobalt marquee strip. Crawls left at ~44px/s (90s seamless loop, 2
  identical spans, translateX -50%); spans must be wider than any viewport (9 phrase
  pairs ≈ 3,940px) or the loop drags a blank gap. Freezes under `prefers-reduced-motion`.
  Motion rule sitewide: animation must earn its place (this + the archive tier rescale).
- **rows** — hairline-separated list with a cobalt `when` chip column. Steps, schedules.
- **bib** — race-bib card (2 punch holes) for tier numbers.
- **tbtn** — tier toggle buttons; `aria-pressed`, cobalt when active.
- **capture** — Kit form 9751172 + `.btn` (condensed 800 uppercase, cobalt, hard under-shadow).
  Include the fetch-submit JS with no-JS form fallback.
- **pull** — condensed uppercase pull-quote with 4px cobalt left rule.
- **fine + footer** — 13px faint disclaimers; footer wordmark + handles.

## Charts (Build Archive pattern; the dataviz rules that apply here)

- Bars: cobalt, `flex:1`, 2px gaps, 4px top radius, anchored to a 1px baseline.
  Race week is `--ink`, never a second hue.
- 1 shared y-scale across comparable charts (both builds scale to 130).
- Grid: 3 faint lines max, DIN labels on the LEFT (bars are short there).
- Labels: selective. Peak week + race week only; never a number on every bar.
- Hover/focus tooltip (fixed, ink background) carries the detail; the full table below
  carries the lookup. Chart + table always ship together; the table is the accessible view.
- Tick labels every 4th week (T-20, T-16...), 9px DIN.

## Voice (applies to page copy too)

Numerals over words. No em dashes (commas, periods, reflow). No explainer tag phrases.
Specific units, race-week jargon, dry humor. Data claims come straight off the watch or
the training DB, never rounded for effect. Brand-neutral fueling; Nike worn in all club
imagery; no contract terms anywhere (see nike-clearance-notes.md in the Cowork project,
private).

## Build notes

- Pages are static, self-contained HTML, 1 file per page, inline CSS. No frameworks,
  no webfonts, no external requests except the Kit form POST.
- The archive page is GENERATED: `python3 tools/build_archive.py` reads the coachclaude
  training DB and rewrites `archive/index.html`. Edit the generator, not the output.
- Deploy = push to main (GitHub Pages, urunclub.com). Nothing goes live without
  Charles's voice-check on new copy.

## CSS gotcha (learned 2026-08-03, commit 81cd600)

`.wrap` sets `padding:0 24px` and, as a class selector, beats element selectors and ties
with other classes (last-declared wins). Any rule that adds padding to an element that ALSO
carries `.wrap` must (a) use equal-or-higher specificity declared later, and (b) restate the
24px horizontal padding. Symptom when violated: sections flush against neighbors, content
touching screen edges on mobile.
