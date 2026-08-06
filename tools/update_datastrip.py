#!/usr/bin/env python3
"""Refresh the homepage datastrip (the proof row) from the coachclaude training DB.

"Last full week" = the most recent Monday-Sunday week whose Sunday has passed.
The script rewrites only the stat cells between the datastrip:auto markers in
index.html. It aborts rather than write a bad week: zero runs, or a DB that has
not synced past the week it is reporting.

Run: python3 tools/update_datastrip.py
Part of the Monday Log session: run after the coachclaude sync, review the git
diff, then push on Charles's go (repo rule: no push without it).
"""
import datetime
import os
import re
import sqlite3

DB = os.path.expanduser("~/Documents/Claude/Projects/coachclaude/data/training.db")
PAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")

START = "<!-- datastrip:auto (tools/update_datastrip.py) -->"
END = "<!-- /datastrip:auto -->"


def last_full_week(today=None):
    today = today or datetime.date.today()
    # Most recent Sunday strictly before today; the Mon-Sun week ending there.
    sunday = today - datetime.timedelta(days=(today.weekday() + 1) % 7 or 7)
    return sunday - datetime.timedelta(days=6), sunday


def fmt_num(x):
    s = "%.1f" % x
    return s[:-2] if s.endswith(".0") else s


def main():
    monday, sunday = last_full_week()
    con = sqlite3.connect(DB)
    max_date = con.execute("SELECT MAX(start_date) FROM activities").fetchone()[0]
    if max_date < sunday.isoformat():
        raise SystemExit(
            "DB last activity %s predates week end %s. Sync coachclaude first (or it was a rest-day Sunday; rerun with a hand check)."
            % (max_date, sunday)
        )
    mi, runs, longrun, moving_s = con.execute(
        """
        SELECT ROUND(SUM(distance_mi),1), COUNT(*), ROUND(MAX(distance_mi),1), SUM(moving_time_s)
        FROM activities
        WHERE type LIKE '%run%' AND start_date BETWEEN ? AND ?
        """,
        (monday.isoformat(), sunday.isoformat()),
    ).fetchone()
    if not runs:
        raise SystemExit("0 runs found for %s..%s; refusing to write." % (monday, sunday))

    # Round total seconds per mile first, then split (the strava-mcp 6:60 lesson).
    pace = round(moving_s / mi)
    pace_str = "%d:%02d" % divmod(pace, 60)

    stats = [(fmt_num(mi), "Miles"), (str(runs), "Runs"), (fmt_num(longrun), "Long run"), (pace_str, "Avg pace")]
    cells = "\n".join(
        '          <div class="stat"><div class="n">%s</div><div class="l">%s</div></div>' % s for s in stats
    )

    with open(PAGE) as f:
        html = f.read()
    if START not in html or END not in html:
        raise SystemExit("datastrip:auto markers not found in index.html")
    new = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        START + "\n" + cells + "\n          " + END,
        html,
        flags=re.S,
    )
    with open(PAGE, "w") as f:
        f.write(new)
    print("Week %s..%s: %s mi, %s runs, %s long, %s avg. Wrote %s" % (monday, sunday, fmt_num(mi), runs, fmt_num(longrun), pace_str, PAGE))


if __name__ == "__main__":
    main()
