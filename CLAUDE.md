# urunclub.com — production site

Static site for U Run Club, deployed via GitHub Pages (push to main = LIVE at
urunclub.com; never push without Charles's explicit go).

**Read `DESIGN.md` before touching any page.** It is the codified design language:
tokens, type stack, components, chart rules, voice. Every page matches it.

- `index.html` — landing page + Kit signup (form 9751172).
- `archive/index.html` — The Build Archive. GENERATED FILE, do not hand-edit:
  run `python3 tools/build_archive.py` (reads the coachclaude training DB at
  ~/Documents/Claude/Projects/coachclaude/data/training.db). To add a build
  (e.g. Chicago 2026 after race day), add an entry to `BUILDS` in the generator.
- Project planning lives in the Cowork workspace:
  ~/Documents/Claude/Projects/Empire/business-strategy/products/u-run-club/INDEX.md
