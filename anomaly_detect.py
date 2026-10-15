import csv
from datetime import datetime
import psycopg2
import smart_meter_simulator as sim

conn = psycopg2.connect(host="localhost", port=5432, dbname="auca_energy",
                        user="postgres", password="YOUR_PASSWORD")
conn.autocommit = True
cur = conn.cursor()
cur.execute("SET timezone TO 'Africa/Kigali'")

HIGH, LOW = 2.0, 0.25

SQL = """
WITH base AS (
  SELECT meter_id, event_time, power_kw,
         (EXTRACT(hour FROM event_time) * 4 + EXTRACT(minute FROM event_time) / 15)::int AS slot,
         (EXTRACT(isodow FROM event_time) >= 6) AS wkend
  FROM energy_readings),
med AS (
  SELECT meter_id, slot, wkend,
         percentile_cont(0.5) WITHIN GROUP (ORDER BY power_kw) AS m
  FROM base GROUP BY 1, 2, 3)
SELECT b.meter_id, b.event_time, b.power_kw, med.m
FROM base b JOIN med USING (meter_id, slot, wkend)
WHERE b.power_kw > %s * med.m OR b.power_kw < %s * med.m
"""
print("Running detection (this can take a few minutes)...")
cur.execute(SQL, (HIGH, LOW))
flags = cur.fetchall()
print("Total flags:", len(flags))

with open("anomaly_flags.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["meter_id", "event_time", "power_kw", "median_kw"])
    w.writerows(flags)

# evaluation against the labels (labels used only here)
events = sim.anomaly_events()
ivals = {}
for e in events:
    ivals.setdefault(e["meter_id"], []).append(
        (datetime.fromisoformat(e["start_time"]), datetime.fromisoformat(e["end_time"])))

def inside(meter, t):
    return any(s <= t < en for s, en in ivals.get(meter, []))

detected = 0
for e in events:
    s = datetime.fromisoformat(e["start_time"])
    en = datetime.fromisoformat(e["end_time"])
    if any(f[0] == e["meter_id"] and s <= f[1] < en for f in flags):
        detected += 1
print("Detected events:", detected, "of", len(events), "| missed:", len(events) - detected)

false_flags = [f for f in flags if not inside(f[0], f[1])]
in_interval_rows = 0
for e in events:
    cur.execute("SELECT COUNT(*) FROM energy_readings WHERE meter_id=%s "
                "AND event_time >= %s AND event_time < %s",
                (e["meter_id"], e["start_time"], e["end_time"]))
    in_interval_rows += cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM energy_readings")
total_rows = cur.fetchone()[0]
outside = total_rows - in_interval_rows
fm = len({f[0] for f in false_flags})

print("Observed readings inside injected intervals:", in_interval_rows)
print("Observed readings outside injected intervals:", outside)
print("False flags:", len(false_flags),
      "| % of outside readings:", round(100.0 * len(false_flags) / outside, 6))
print("Meters with a false flag:", fm,
      "| % of 4000 meters affected:", round(100.0 * fm / 4000, 4))
print("Sample flags:")
for f in flags[:5]:
    print("  ", f[0], f[1], round(f[2], 3), "median", round(f[3], 3))
conn.close()
