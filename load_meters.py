import psycopg2
import smart_meter_simulator as sim

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="auca_energy",
    user="postgres",
    password="YOUR_PASSWORD",
)
cur = conn.cursor()

for m in sim.meter_metadata():
    cur.execute(
        """
        INSERT INTO meters (meter_id, region, customer_type,
                            base_power_kw, power_factor)
        VALUES (%(meter_id)s, %(region)s, %(customer_type)s,
                %(base_power_kw)s, %(power_factor)s)
        """,
        m,
    )

conn.commit()

cur.execute("SELECT COUNT(*) FROM meters")
print("Rows in meters:", cur.fetchone()[0])

cur.close()
conn.close()
