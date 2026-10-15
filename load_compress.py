import csv
import time
import psycopg2
from datetime import datetime, timedelta, timezone

CAT = timezone(timedelta(hours=2))
CUTOFF = datetime(2026, 10, 11, 20, 20, 26, tzinfo=CAT)
TABLES = ["energy_time_compressed", "energy_meter_compressed"]

conn = psycopg2.connect(host="localhost", port=5432, dbname="auca_energy",
                        user="postgres", password="YOUR_PASSWORD")
conn.autocommit = True
cur = conn.cursor()
cur.execute("SET timezone TO 'Africa/Kigali'")

log = []
done = set()

def compress_complete_chunks(table, loaded_until):
    cur.execute(
        "SELECT chunk_schema || '.' || chunk_name, range_end "
        "FROM timescaledb_information.chunks "
        "WHERE hypertable_name = %s AND NOT is_compressed "
        "ORDER BY range_start", (table,))
    for chunk, range_end in cur.fetchall():
        if range_end <= loaded_until and range_end < CUTOFF and (table, chunk) not in done:
            t0 = time.perf_counter()
            cur.execute("SELECT compress_chunk(%s::regclass)", (chunk,))
            secs = time.perf_counter() - t0
            done.add((table, chunk))
            log.append([table, chunk, "compress", round(secs, 3)])
            print("  compressed", table, chunk, round(secs, 2), "s")

day = datetime(2026, 9, 1, tzinfo=CAT)
end = datetime(2026, 9, 29, tzinfo=CAT)
while day < end:
    nxt = day + timedelta(days=1)
    for t in TABLES:
        t0 = time.perf_counter()
        cur.execute(
            "INSERT INTO " + t + " SELECT * FROM energy_readings "
            "WHERE event_time >= %s AND event_time < %s", (day, nxt))
        log.append([t, str(day.date()), "load", round(time.perf_counter() - t0, 3)])
    print("loaded CAT day", day.date())
    day = nxt
    for t in TABLES:
        compress_complete_chunks(t, day)

# the last chunk extends past 29 Sept 00:00 CAT, so it is complete only now
for t in TABLES:
    compress_complete_chunks(t, datetime(2030, 1, 1, tzinfo=CAT))

with open("compress_timings.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["table", "item", "phase", "seconds"])
    w.writerows(log)

for t in TABLES:
    rows = [r for r in log if r[0] == t and r[2] == "compress"]
    print("Total compression seconds", t, round(sum(r[3] for r in rows), 2),
          "chunks:", len(rows))
conn.close()
