import time
import psycopg2

conn = psycopg2.connect(host="localhost", port=5432, dbname="auca_energy",
                        user="postgres", password="YOUR_PASSWORD")
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM energy_readings")
print("Rows before load:", cur.fetchone()[0])

start = time.time()
cur.execute("""
    COPY energy_readings
    (meter_id, event_time, received_time, power_kw, voltage_v,
     current_a, frequency_hz, energy_kwh)
    FROM '/tmp/readings.csv' WITH (FORMAT csv)
""")
conn.commit()
load_secs = round(time.time() - start, 1)

cur.execute("SELECT COUNT(*) FROM energy_readings")
print("Rows committed:", cur.fetchone()[0])
print("Expected emitted_readings: 10696848")
print("Load seconds (first write to final commit):", load_secs)
conn.close()
