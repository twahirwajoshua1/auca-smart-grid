import psycopg2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

conn = psycopg2.connect(host="localhost", port=5432, dbname="auca_energy",
                        user="postgres", password="YOUR_PASSWORD")
cur = conn.cursor()
cur.execute("SET timezone TO 'Africa/Kigali'")

cur.execute("SELECT date_trunc('day', event_time)::date, SUM(energy_kwh) FROM energy_readings GROUP BY 1 ORDER BY 1")
days = cur.fetchall()
cur.execute("SELECT 1 + 7 * ((EXTRACT(day FROM event_time)::int - 1) / 7), SUM(energy_kwh) FROM energy_readings GROUP BY 1 ORDER BY 1")
weeks = cur.fetchall()

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
ax[0].bar([d[0].strftime("%d") for d in days], [float(d[1]) for d in days])
ax[0].set_title("Total network energy per CAT day, Sept 2026")
ax[0].set_xlabel("Day of September")
ax[0].set_ylabel("Energy (kWh)")

names = ["1-7 Sep", "8-14 Sep", "15-21 Sep", "22-28 Sep"]
ax[1].bar(names, [float(w[1]) for w in weeks])
ax[1].set_title("Total network energy per 7-day period")
ax[1].set_ylabel("Energy (kWh)")

plt.tight_layout()
plt.savefig("chart_5_1.png", dpi=150)
print("saved chart_5_1.png")
conn.close()
