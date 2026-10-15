import time
from datetime import date, timedelta
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import dq

conn = dq.connect()
app = Dash(__name__)
app.layout = html.Div([
    dcc.Location(id="url"),
    html.H2(id="title"),
    html.Div(["Dates (whole CAT days): ",
              dcc.DatePickerRange(id="dates", start_date="2026-09-22",
                                  end_date="2026-09-28",
                                  min_date_allowed="2026-09-01",
                                  max_date_allowed="2026-09-28"),
              "  Meter: ",
              dcc.Input(id="meter", type="number", value=1000000000)]),
    html.Div(id="timing"),
] + [dcc.Graph(id="g" + str(i)) for i in range(1, 6)])

@app.callback(
    [Output("title", "children"), Output("timing", "children")]
    + [Output("g" + str(i), "figure") for i in range(1, 6)],
    [Input("url", "pathname"), Input("dates", "start_date"),
     Input("dates", "end_date"), Input("meter", "value")])
def refresh(path, sd, ed, meter):
    mode = "agg" if path and "agg" in path else "raw"
    end_excl = date.fromisoformat(ed[:10]) + timedelta(days=1)
    p = {"s": sd[:10] + " 00:00:00+02", "e": str(end_excl) + " 00:00:00+02",
         "m": int(meter or 1000000000)}
    t0 = time.perf_counter()
    f, ms = {}, {}
    for k in dq.PANELS:
        f[k], ms[k] = dq.frame(conn, mode, k, p)
    for k in dq.PANELS:
        f[k] = f[k].astype({c: float for c in f[k].columns
                            if c in ("kwh", "n", "completeness_pct")})
    figs = [
        px.line(f["p1"], x="bucket", y="kwh", color="region",
                title="Hourly energy by region (kWh)"),
        px.bar(f["p2"], x="bucket", y="kwh",
               title="Daily network energy (kWh)"),
        px.bar(f["p3"], x="period_start_day", y="kwh",
               title="Network energy per 7-day period (kWh)"),
        px.bar(f["p4"], x="bucket", y="kwh",
               title="Daily energy, selected meter (kWh)"),
        px.bar(f["p5"], x="region", y="completeness_pct",
               title="Completeness by region (%)"),
    ]
    total = (time.perf_counter() - t0) * 1000
    txt = "Query ms: " + ", ".join(k + "=" + str(round(ms[k], 1))
                                   for k in dq.PANELS)
    txt += " | total incl. figures: " + str(round(total, 1)) + " ms"
    name = "Aggregate" if mode == "agg" else "Raw"
    return [name, txt] + figs

app.run(debug=False, port=8050)
