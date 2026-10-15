AUCA Assignment I - Smart Energy Grid Analytics
Group members
- Twahirwa Joshua (101396)
- UBANJE Albert (101402)
- MUTONI Denyse (101207)
This repository holds the ingestion programs, SQL files, analysis and forecast
code, dashboards and recorded timings. smart_meter_simulator.py is the supplied
generator and has not been changed.
REQUIREMENTS
- Docker: timescale/timescaledb:latest-pg17 and emqx/emqx
- Python 3.13
- pip install psycopg2-binary paho-mqtt pandas scikit-learn matplotlib dash plotly
- pip install playwright   (only for dash_render_timing.py; it uses the installed Chrome)
BEFORE YOU RUN ANYTHING
Every script contains YOUR_PASSWORD where the database password goes. Replace it
with your own. The full dataset (about 1.2 GB) is not included; step 5 shows how
to regenerate it.
EXECUTION ORDER
1. Start the containers. TimescaleDB listens on port 5432. EMQX MQTT is mapped
   to port 1884:
   docker run -d --name emqx -p 18083:18083 -p 1884:1883 emqx/emqx:latest
2. Create the database:
   CREATE DATABASE auca_energy;
   then connect to it and run:
   CREATE EXTENSION IF NOT EXISTS timescaledb;
   ALTER DATABASE auca_energy SET timezone TO 'Africa/Kigali';
3. Tables and meters:
   create_tables.sql
   python load_meters.py
4. Pilot (Section 1.3). Empty the table first: TRUNCATE energy_live;
   Window 1: python subscriber.py   (stops itself after 2000 messages)
   Window 2: python publisher.py    (after the subscriber says it is ready)
   Then check: SELECT COUNT(*) FROM energy_live;   (expect 2000)
   All four counts (generated, acknowledged, received, stored) should be 2000.
   The publisher pauses 0.02 s between messages; without it EMQX dropped
   messages in our first two attempts.
5. Full dataset (Section 2.1):
   python generate_csv.py
   docker cp readings.csv iot-stack-db-1:/tmp/readings.csv
   python load_csv.py
   Expect 10,696,848 rows.
6. Cleaning (Section 2.3): run clean_duplicates.sql
   Expect 10,643,735 rows and no duplicate pairs.
7. Chunk comparison (Section 3): run create_hypertables.sql, copy the cleaned
   rows into energy_readings_3h and energy_readings_week with
   INSERT INTO ... SELECT * FROM energy_readings, create an index on
   (meter_id, event_time DESC) on all three tables, run ANALYZE, then:
   python benchmark_chunks.py
8. Compression (Section 4): set your own cutoff (experiment start minus 48 hours)
   in load_compress.py, then:
   create_compressed.sql
   python load_compress.py
   python benchmark_compressed.py
9. Analysis (Section 5):
   analysis_queries.sql (run the queries one at a time in psql)
   python chart_5_1.py
   python anomaly_detect.py
10. Continuous aggregates (Section 6): run create_caggs.sql, refresh each view by
    hand for 1 to 29 September, and only then add the refresh policies.
    The freshness test is at the end of analysis_queries.sql.
11. Dashboards (Section 7):
    python dash_app.py   (pages: localhost:8050/raw and localhost:8050/aggregate)
    python dash_check.py (match check and query timings, in a second window)
    python dash_render_timing.py (end-to-end refresh in Chrome: 1 warm-up and 10 runs
    per page; pause jobs 1000-1004 first with
    SELECT alter_job(j, scheduled => false) FROM generate_series(1000,1004) j;
    and switch them on again afterwards with scheduled => true)
12. Forecast (Section 8):
    python fc1.py
    python fc2.py
RESULT FILES
benchmark_runs.csv, benchmark_summary.csv: chunk comparison timings
benchmark_compressed_runs.csv, benchmark_compressed_summary.csv: compression timings
compress_timings.csv: compression time per chunk
dashboard_timings.csv: dashboard query timings (dash_check.py)
dashboard_render_runs.csv, dashboard_render_summary.csv: browser refresh timings (dash_render_timing.py)
validation_comparison.csv: validation results of the three Ridge configurations
ENVIRONMENT.txt: machine, versions and settings used
anomaly_flags.csv: readings flagged by our anomaly rule
test_predictions.csv: baseline and model forecasts, 22 to 28 September
Environment details and all screenshots are in the PDF report.

