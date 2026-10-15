import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
pd.set_option("display.width", 220)

d = pd.read_pickle("fc_data.pkl")
regions = sorted(d.region.unique(), key=lambda s: int(s.split()[1]))
tr = d.split == "train"
va = d.split == "val"
te = d.split == "test"
usable = d.usable

def met(e):
    e = np.asarray(e, dtype=float)
    return float(np.mean(np.abs(e))), float(np.sqrt(np.mean(e ** 2)))

print("===== 8.2 BASELINE (previous day, same hour) =====")
T = d[te].copy()
T["base"] = T["lag24"]
bm = met(T.base - T.kwh)
print("test predictions:", len(T))
print("baseline MAE:", round(bm[0], 3), "kWh | RMSE:", round(bm[1], 3), "kWh")
print(T[["region", "hr", "kwh", "base"]].head(5).to_string(index=False))

print("===== 8.3 MODEL (Ridge regression) =====")
num = ["lag24", "lag168", "prevday_mean", "wkend", "prev_wkend"]
hd = pd.get_dummies(d["hour"].astype(str), prefix="h")
rd = pd.get_dummies(d["region"], prefix="r")
X = pd.concat([d[num], hd, rd], axis=1).astype(float).fillna(0)
sc = StandardScaler().fit(X[usable])
Xs = sc.transform(X)
rows = []
models = {}
for cid, a in [("C1", 0.1), ("C2", 10.0), ("C3", 100.0)]:
    mdl = Ridge(alpha=a).fit(Xs[usable.values], d.kwh[usable])
    pv = mdl.predict(Xs[va.values])
    mae, rmse = met(pv - d.kwh[va].values)
    models[cid] = mdl
    rows.append([cid, "Ridge alpha=" + str(a), int(usable.sum()),
                 int(va.sum()), round(mae, 3), round(rmse, 3)])
cols = ["config", "settings", "train_rows", "val_rows",
        "val_MAE_kWh", "val_RMSE_kWh"]
vt = pd.DataFrame(rows, columns=cols)
print(vt.to_string(index=False))
best = vt.sort_values("val_MAE_kWh").iloc[0]["config"]
print("shared predictors:", num, "+ hour dummies + region dummies")
print("selected configuration:", best)
T["model"] = models[best].predict(Xs[te.values])
print("test predictions:", len(T))
print(T[["region", "hr", "kwh", "base", "model"]].head(5).to_string(index=False))

print("===== 8.4 EVALUATION (error = predicted - actual) =====")
mm = met(T.model - T.kwh)
print("OVERALL baseline MAE/RMSE:", round(bm[0], 3), round(bm[1], 3))
print("OVERALL model    MAE/RMSE:", round(mm[0], 3), round(mm[1], 3))
out = []
for r in regions:
    s = T[T.region == r]
    b = met(s.base - s.kwh)
    m = met(s.model - s.kwh)
    out.append([r, round(b[0], 2), round(b[1], 2), round(m[0], 2), round(m[1], 2)])
cols = ["region", "base_MAE", "base_RMSE", "model_MAE", "model_RMSE"]
print(pd.DataFrame(out, columns=cols).to_string(index=False))

pk = []
for r in regions:
    s = T[T.region == r].sort_values("hr")
    x = s.loc[s.kwh.idxmax()]
    pk.append([r, x.hr, round(x.kwh, 2), round(x.base, 2),
               round(abs(x.base - x.kwh), 2), round(x.model, 2),
               round(abs(x.model - x.kwh), 2)])
cols = ["region", "peak_hour", "actual", "base_pred", "base_abs_err",
        "model_pred", "model_abs_err"]
print(pd.DataFrame(pk, columns=cols).to_string(index=False))

s = T[T.region == "Region 1"].sort_values("hr")
plt.figure(figsize=(14, 5))
plt.plot(s.hr, s.kwh, label="actual")
plt.plot(s.hr, s.base, label="baseline (previous day)")
plt.plot(s.hr, s.model, label="model")
plt.title("Region 1 hourly energy, 22-28 Sep 2026")
plt.ylabel("Energy (kWh)")
plt.legend()
plt.tight_layout()
plt.savefig("forecast_plot.png", dpi=150)
T.to_csv("test_predictions.csv", index=False)
print("saved forecast_plot.png and test_predictions.csv")
