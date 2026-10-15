"""Section 7.4 end-to-end timing in one browser.

For each mode (Raw, Aggregate): one warm-up refresh, then ten measured refreshes.
A refresh = the page is requested again (same filters: 22-28 September, meter
1000000000) and the clock stops when the app has returned all five panels AND the
browser has drawn all five chart titles. The per-panel query durations are the ones
the dashboard itself prints (dq.frame, time.perf_counter around execute+fetchall).

Before running:  python dash_app.py   (leave it running in another window)
                 pause jobs 1000-1004 (see README step 11) and close other programs.
Run:             python dash_render_timing.py
Needs:           pip install playwright   (uses the installed Chrome, no download)
Writes:          dashboard_render_runs.csv and dashboard_render_summary.csv
"""
import csv
import os
import re
import statistics
import time
from datetime import datetime, timedelta, timezone

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8050"
PAGES = {"raw": BASE + "/raw", "agg": BASE + "/aggregate"}
RUNS = 10
CAT = timezone(timedelta(hours=2))
PANELS = ["p1", "p2", "p3", "p4", "p5"]

DONE_JS = ("() => document.querySelectorAll('.js-plotly-plot .gtitle').length >= 5"
           " && /Query ms/.test((document.getElementById('timing') || {}).innerText || '')")


def launch(p):
    exe = os.environ.get("BROWSER_EXE")          # optional: path to a browser program
    if exe:
        return p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
    for channel in ("chrome", "msedge"):
        try:
            return p.chromium.launch(channel=channel)
        except Exception:
            pass
    raise SystemExit("Neither Chrome nor Edge could be started by Playwright.")


def refresh(page, url):
    start = datetime.now(CAT)
    t0 = time.perf_counter()
    page.goto(url, wait_until="commit")           # request the page / refresh again
    page.wait_for_function(DONE_JS, timeout=180000)
    ms = (time.perf_counter() - t0) * 1000
    end = datetime.now(CAT)
    page.wait_for_load_state("networkidle")       # not timed: lets any second update finish
    txt = page.inner_text("#timing")
    q = {k: float(v) for k, v in re.findall(r"(p\d)=([0-9.]+)", txt)}
    return start, end, ms, q


def main():
    rows = []
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        for mode, url in PAGES.items():
            refresh(page, url)                    # one warm-up refresh (not recorded)
            for i in range(1, RUNS + 1):
                s, e, ms, q = refresh(page, url)
                row = {"mode": mode, "run": i, "start_cat": s.isoformat(timespec="milliseconds"),
                       "end_cat": e.isoformat(timespec="milliseconds"),
                       "render_ms": round(ms, 1), "machine": os.environ.get("COMPUTERNAME", "Josh")}
                for k in PANELS:
                    row[k + "_query_ms"] = q[k]
                row["queries_sum_ms"] = round(sum(q[k] for k in PANELS), 1)
                rows.append(row)
                print(mode, i, "render", row["render_ms"], "ms | queries", row["queries_sum_ms"], "ms")
        browser.close()

    with open("dashboard_render_runs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    out = []
    for mode in PAGES:
        sel = [r for r in rows if r["mode"] == mode]
        for key in [k + "_query_ms" for k in PANELS] + ["queries_sum_ms", "render_ms"]:
            v = [r[key] for r in sel]
            out.append([mode, key, round(statistics.median(v), 1), round(min(v), 1), round(max(v), 1)])
    with open("dashboard_render_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mode", "measure", "median_ms", "min_ms", "max_ms"])
        w.writerows(out)
    print("\nmode  measure           median     min      max")
    for r in out:
        print(f"{r[0]:5} {r[1]:17} {r[2]:8} {r[3]:8} {r[4]:8}")
    print("saved dashboard_render_runs.csv and dashboard_render_summary.csv")


if __name__ == "__main__":
    main()
