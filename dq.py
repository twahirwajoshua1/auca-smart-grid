import time
import pandas as pd
import psycopg2

PANELS = ["p1", "p2", "p3", "p4", "p5"]
D = "EXTRACT(EPOCH FROM (%(e)s::timestamptz - %(s)s::timestamptz)) / 86400"
MC = "(SELECT region, COUNT(*) AS c FROM meters GROUP BY region) mc"
WR = "WHERE r.event_time >= %(s)s AND r.event_time < %(e)s"
WA = "WHERE a.bucket >= %(s)s AND a.bucket < %(e)s"

RAW = {
 "p1": "SELECT date_trunc('hour', r.event_time) AS bucket, m.region, "
       "SUM(r.energy_kwh) AS kwh, COUNT(*) AS n "
       "FROM energy_readings r JOIN meters m USING (meter_id) "
       + WR + " GROUP BY 1, 2 ORDER BY 1, 2",
 "p2": "SELECT date_trunc('day', r.event_time) AS bucket, "
       "SUM(r.energy_kwh) AS kwh, COUNT(*) AS n "
       "FROM energy_readings r " + WR + " GROUP BY 1 ORDER BY 1",
 "p3": "SELECT 1 + 7 * ((EXTRACT(day FROM r.event_time)::int - 1) / 7) "
       "AS period_start_day, SUM(r.energy_kwh) AS kwh, COUNT(*) AS n "
       "FROM energy_readings r " + WR + " GROUP BY 1 ORDER BY 1",
 "p4": "SELECT date_trunc('day', r.event_time) AS bucket, "
       "SUM(r.energy_kwh) AS kwh, COUNT(*) AS n "
       "FROM energy_readings r " + WR + " AND r.meter_id = %(m)s "
       "GROUP BY 1 ORDER BY 1",
 "p5": "SELECT m.region, COUNT(*) AS n, "
       "100.0 * COUNT(*) / (mc.c * " + D + " * 96) AS completeness_pct "
       "FROM energy_readings r JOIN meters m USING (meter_id) "
       "JOIN " + MC + " ON mc.region = m.region " + WR +
       " GROUP BY m.region, mc.c ORDER BY m.region",
}

AGG = {
 "p1": "SELECT a.bucket, a.region, SUM(a.energy_kwh) AS kwh, "
       "SUM(a.readings) AS n FROM cagg_hour_region a " + WA +
       " GROUP BY 1, 2 ORDER BY 1, 2",
 "p2": "SELECT date_trunc('day', a.bucket) AS bucket, "
       "SUM(a.energy_kwh) AS kwh, SUM(a.readings) AS n "
       "FROM cagg_15min_region a " + WA + " GROUP BY 1 ORDER BY 1",
 "p3": "SELECT 1 + 7 * ((EXTRACT(day FROM a.bucket)::int - 1) / 7) "
       "AS period_start_day, SUM(a.energy_kwh) AS kwh, "
       "SUM(a.readings) AS n FROM cagg_15min_region a " + WA +
       " GROUP BY 1 ORDER BY 1",
 "p4": "SELECT a.bucket, a.energy_kwh AS kwh, a.readings AS n "
       "FROM cagg_day_meter a " + WA + " AND a.meter_id = %(m)s ORDER BY 1",
 "p5": "SELECT a.region, SUM(a.readings) AS n, "
       "100.0 * SUM(a.readings) / (mc.c * " + D + " * 96) "
       "AS completeness_pct FROM cagg_15min_region a "
       "JOIN " + MC + " ON mc.region = a.region " + WA +
       " GROUP BY a.region, mc.c ORDER BY a.region",
}
MODES = {"raw": RAW, "agg": AGG}

def connect():
    c = psycopg2.connect(host="localhost", port=5432, dbname="auca_energy",
                         user="postgres", password="YOUR_PASSWORD")
    c.autocommit = True
    c.cursor().execute("SET timezone TO 'Africa/Kigali'")
    return c

def frame(conn, mode, panel, p):
    cur = conn.cursor()
    t0 = time.perf_counter()
    cur.execute(MODES[mode][panel], p)
    rows = cur.fetchall()
    ms = (time.perf_counter() - t0) * 1000
    cols = [c[0] for c in cur.description]
    return pd.DataFrame(rows, columns=cols), ms
