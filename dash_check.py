import csv
import statistics
import dq

P = {"s": "2026-09-22 00:00:00+02", "e": "2026-09-29 00:00:00+02",
     "m": 1000000000}
KEYS = {"p1": 2, "p2": 1, "p3": 1, "p4": 1, "p5": 1}
TOL = {"p1": [0.001, 0], "p2": [0.001, 0], "p3": [0.001, 0],
       "p4": [0.001, 0], "p5": [0, 0.000001]}
conn = dq.connect()

print("===== 7.3 MATCH (22 Sep 00:00 to 29 Sep 00:00, meter 1000000000) =====")
for p in dq.PANELS:
    a, _ = dq.frame(conn, "raw", p, P)
    b, _ = dq.frame(conn, "agg", p, P)
    if len(a) != len(b):
        print(p, "ROW COUNT DIFFERS", len(a), len(b))
        continue
    k = KEYS[p]
    same = (a.iloc[:, :k].astype(str).values.tolist()
            == b.iloc[:, :k].astype(str).values.tolist())
    diffs = []
    for i in range(2):
        x = a.iloc[:, k + i].astype(float)
        y = b.iloc[:, k + i].astype(float)
        diffs.append(float((x - y).abs().max()))
    ok = same and all(d <= t for d, t in zip(diffs, TOL[p]))
    print(p, "rows compared:", len(a), "| keys identical:", same,
          "| max abs diffs:", diffs, "| PASS:", ok)

print("===== 7.4 TIMING (query ms per panel; 1 warm-up + 10 runs) =====")
out = []
for mode in ("raw", "agg"):
    runs = []
    for i in range(11):
        row = {}
        for p in dq.PANELS:
            _, ms = dq.frame(conn, mode, p, P)
            row[p] = ms
        row["total"] = sum(row.values())
        if i > 0:
            runs.append(row)
    for key in dq.PANELS + ["total"]:
        v = [r[key] for r in runs]
        line = [mode, key, round(statistics.median(v), 2),
                round(min(v), 2), round(max(v), 2)]
        out.append(line)
        print(*line)
with open("dashboard_timings.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["mode", "panel", "median_ms", "min_ms", "max_ms"])
    w.writerows(out)
print("saved dashboard_timings.csv")
