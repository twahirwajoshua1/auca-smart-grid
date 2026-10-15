import psycopg2
import pandas as pd
pd.set_option("display.width", 220)

conn = psycopg2.connect(host="localhost", port=5432, dbname="auca_energy",
                        user="postgres", password="YOUR_PASSWORD")
cur = conn.cursor()
cur.execute("SET timezone TO 'Africa/Kigali'")
cur.execute("SELECT m.region, date_trunc('hour', r.event_time), "
            "SUM(r.energy_kwh), COUNT(*) "
            "FROM energy_readings r JOIN meters m USING (meter_id) "
            "GROUP BY 1,2")
df = pd.DataFrame(cur.fetchall(), columns=["region", "hr", "kwh", "n"])
conn.close()
df["hr"] = pd.to_datetime(df["hr"], utc=True)
df["hr"] = df["hr"].dt.tz_convert("Africa/Kigali").dt.tz_localize(None)

print("===== 8.1 DATASET =====")
regions = sorted(df.region.unique(), key=lambda s: int(s.split()[1]))
hours = pd.date_range("2026-09-01 00:00", "2026-09-28 23:00", freq="h")
idx = pd.MultiIndex.from_product([regions, hours], names=["region", "hr"])
grid = idx.to_frame(index=False)
d = grid.merge(df, on=["region", "hr"], how="left")
print("rows:", len(d), "| absent region-hours:", int(d.kwh.isna().sum()))
print("readings per region-hour min/max:", d.n.min(), d.n.max())

d["day"] = d.hr.dt.normalize()
dm = d.groupby(["region", "day"])["kwh"].mean().rename("prevday_mean")
dm = dm.reset_index()
dm["day"] = dm["day"] + pd.Timedelta(days=1)
d = d.merge(dm, on=["region", "day"], how="left")
d = d.sort_values(["region", "hr"]).reset_index(drop=True)
g = d.groupby("region")["kwh"]
d["lag24"] = g.shift(24)
d["lag168"] = g.shift(168)
d["hour"] = d.hr.dt.hour
d["wkend"] = (d.hr.dt.dayofweek > 4).astype(int)
prev = d.hr - pd.Timedelta(days=1)
d["prev_wkend"] = (prev.dt.dayofweek > 4).astype(int)

d["dnum"] = d.hr.dt.day
d["split"] = "test"
d.loc[d.dnum < 22, "split"] = "val"
d.loc[d.dnum < 15, "split"] = "train"
for nm in ["train", "val", "test"]:
    s = d[d.split == nm]
    print(nm, "rows:", len(s), "| from", s.hr.min(), "to", s.hr.max())

ok = d.lag24.notna() & d.lag168.notna() & d.prevday_mean.notna()
d["ok"] = ok
d["usable"] = ok & (d.split == "train")
trn = d[d.split == "train"]
print("train rows before exclusion:", len(trn))
print("excluded (no 7-day lookback):", int((~trn.ok).sum()))
print("retained:", int(d.usable.sum()))
print("val/test rows missing a lag:", int((~d[d.split != "train"].ok).sum()))

print("FEATURES (name | lag or window in hours | earliest usable target)")
print("lag24 | 24 | 2026-09-02 00:00")
print("lag168 | 168 | 2026-09-08 00:00")
print("prevday_mean | previous calendar day, 24 | 2026-09-02 00:00")
print("hour, wkend, prev_wkend, region | calendar | 2026-09-01 00:00")

origin = d.hr.dt.normalize()
c1 = ((d.hr - pd.Timedelta(hours=24)) < origin).all()
c2 = ((d.hr - pd.Timedelta(hours=168)) < origin).all()
print("every lag source precedes its forecast origin:", bool(c1), bool(c2))
cols = ["region", "hr", "kwh", "lag24", "lag168", "prevday_mean"]
print(d[d.split == "test"][cols].head(5).to_string(index=False))
d.to_pickle("fc_data.pkl")
print("saved fc_data.pkl")
