CREATE MATERIALIZED VIEW cagg_15min_region
WITH (timescaledb.continuous, timescaledb.materialized_only = true) AS
SELECT time_bucket('15 minutes', r.event_time) AS bucket,
       m.region,
       SUM(r.energy_kwh) AS energy_kwh,
       SUM(r.power_kw)   AS power_kw,
       COUNT(*)          AS readings
FROM energy_readings r JOIN meters m ON r.meter_id = m.meter_id
GROUP BY 1, 2
WITH NO DATA;

CREATE MATERIALIZED VIEW cagg_hour_region
WITH (timescaledb.continuous, timescaledb.materialized_only = true) AS
SELECT time_bucket('1 hour', r.event_time, 'Africa/Kigali') AS bucket,
       m.region,
       SUM(r.energy_kwh) AS energy_kwh,
       SUM(r.power_kw)   AS power_kw,
       COUNT(*)          AS readings
FROM energy_readings r JOIN meters m ON r.meter_id = m.meter_id
GROUP BY 1, 2
WITH NO DATA;

CREATE MATERIALIZED VIEW cagg_day_meter
WITH (timescaledb.continuous, timescaledb.materialized_only = true) AS
SELECT time_bucket('1 day', event_time, 'Africa/Kigali') AS bucket,
       meter_id,
       SUM(energy_kwh) AS energy_kwh,
       SUM(power_kw)   AS power_kw,
       COUNT(*)        AS readings
FROM energy_readings
GROUP BY 1, 2
WITH NO DATA;