import csv
import time
import statistics
import socket
from datetime import datetime, timezone, timedelta
import psycopg2

CAT = timezone(timedelta(hours=2))
MACHINE = socket.gethostname()
TABLES = ["energy_readings", "energy_readings_3h", "energy_readings_week"]

QUERIES = {
 "Q1": """SELECT date_trunc('hour', event_time) AS hr, AVG(power_kw)
          FROM {t}
          WHERE event_time >= '2026-09-21 00:00:00+02'
            AND event_time <  '2026-09-22 00:00:00+02'
          GROUP BY 1 ORDER BY 1""",
 "Q2": """SELECT event_time, SUM(power_kw) AS total_kw
          FROM {t}
          WHERE event_time >= '2026-09-22 00:00:00+02'
            AND event_time <  '2026-09-29 00:00:00+02'
          GROUP BY event_time
          ORDER BY total_kw DESC, event_time ASC
          LIMIT 10""",
 "Q3": """SELECT meter_id, SUM(energy_kwh) FROM {t}
          GROUP BY meter_id ORDER BY meter_id""",
 "Q4": """SELECT SUM(energy_kwh), AVG(power_kw), MAX(power_kw)
          FROM {t}
          WHERE meter_id = 1000000000
            AND event_time >= '2026-09-22 00:00:00+02'
            AND event_time <  '2026-09-29 00:00:00+02'""",
 "Q5": """SELECT COUNT(*), SUM(energy_kwh), AVG(power_kw),
                 MIN(power_kw), MAX(power_kw) FROM {t}""",
}

def connect():
    c = psycopg2.connect(host="localhost", port=5432, dbname="auca_energy",
                         user="postgres", password="YOUR_PASSWORD")
    c.autocommit = True
    cur = c.cursor()
    cur.execute("SET timezone TO 'Africa/Kigali'")
    return c, cur

def run(cur, sql):
    t0 = time.perf_counter()
    cur.execute(sql)
    rows = cur.fetchall()
    ms = (time.perf_counter() - t0) * 1000
    return ms, rows

def close(a, b):
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        return abs(float(a) - float(b)) <= 0.001
    return a == b

conn, cur = connect()
session_start = time.perf_counter()
log = []
results = {}
summary = []

for q, tmpl in QUERIES.items():
    for t in TABLES:
        sql = tmpl.format(t=t)
        _, rows = run(cur, sql)                      # warm-up
        results[(q, t)] = rows
        durs = []
        for i in range(1, 6):
            s = datetime.now(CAT)
            ms, _ = run(cur, sql)
            e = datetime.now(CAT)
            durs.append(ms)
            log.append([q, t, i, s.isoformat(timespec="milliseconds"),
                        e.isoformat(timespec="milliseconds"),
                        round(ms, 2), MACHINE])
        summary.append([q, t, round(statistics.median(durs), 2),
                        round(min(durs), 2), round(max(durs), 2)])
        print(q, t, "median ms:", round(statistics.median(durs), 2))
    base = results[(q, TABLES[0])]
    ok = all(close(base, results[(q, t)]) for t in TABLES[1:])
    print(q, "results match across tables:", ok)

total = round(time.perf_counter() - session_start, 1)
print("Session seconds (first warm-up to last result):", total)

with open("benchmark_runs.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["query", "table", "run", "start_CAT", "end_CAT", "ms", "machine"])
    w.writerows(log)
with open("benchmark_summary.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["query", "table", "median_ms", "min_ms", "max_ms"])
    w.writerows(summary)
conn.close()
