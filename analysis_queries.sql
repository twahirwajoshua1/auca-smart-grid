-- 2.2 data quality (before cleaning)
SELECT COUNT(*) AS emitted, COUNT(DISTINCT (meter_id, event_time)) AS uniq
FROM energy_readings;

SELECT COUNT(*) FROM (SELECT DISTINCT meter_id, event_time FROM energy_readings
  WHERE received_time > event_time + INTERVAL '15 minutes') t;

SELECT meter_id, 2688 - COUNT(DISTINCT event_time) AS missing
FROM energy_readings GROUP BY meter_id ORDER BY missing DESC, meter_id LIMIT 5;

-- 2.3 conflict check
SELECT COUNT(*) FROM (SELECT meter_id, event_time FROM energy_readings
  GROUP BY 1, 2 HAVING COUNT(*) > 1 AND (COUNT(DISTINCT received_time) > 1
  OR COUNT(DISTINCT power_kw) > 1 OR COUNT(DISTINCT voltage_v) > 1
  OR COUNT(DISTINCT current_a) > 1 OR COUNT(DISTINCT frequency_hz) > 1
  OR COUNT(DISTINCT energy_kwh) > 1)) t;

-- 5.1 demand patterns
SELECT date_trunc('day', event_time), SUM(energy_kwh)
FROM energy_readings GROUP BY 1 ORDER BY 1;

SELECT 1 + 7 * ((EXTRACT(day FROM event_time)::int - 1) / 7), SUM(energy_kwh)
FROM energy_readings GROUP BY 1 ORDER BY 1;

SELECT event_time, SUM(power_kw) AS kw FROM energy_readings
GROUP BY 1 ORDER BY kw DESC, event_time LIMIT 3;

-- 5.2 regions and customer types
SELECT m.region, COUNT(DISTINCT m.meter_id), SUM(r.energy_kwh),
  SUM(r.energy_kwh) / COUNT(DISTINCT m.meter_id)
FROM energy_readings r JOIN meters m USING (meter_id) GROUP BY 1 ORDER BY 1;

SELECT m.customer_type, COUNT(DISTINCT m.meter_id), SUM(r.energy_kwh),
  SUM(r.energy_kwh) / COUNT(DISTINCT m.meter_id)
FROM energy_readings r JOIN meters m USING (meter_id) GROUP BY 1 ORDER BY 1;

SELECT region, customer_type, COUNT(*) FROM meters GROUP BY 1, 2 ORDER BY 1, 2;

-- 5.3 reporting quality
SELECT m.region, COUNT(*), COUNT(DISTINCT m.meter_id) * 2688,
  ROUND((100.0 * COUNT(*) / (COUNT(DISTINCT m.meter_id) * 2688))::numeric, 4)
FROM energy_readings r JOIN meters m USING (meter_id) GROUP BY 1 ORDER BY 1;

SELECT SUM(energy_kwh) FILTER (WHERE received_time <= '2026-09-22 00:00:00+02'),
  SUM(energy_kwh)
FROM energy_readings
WHERE event_time >= '2026-09-21 00:00:00+02'
  AND event_time < '2026-09-22 00:00:00+02';

-- 6.2 freshness test
CREATE TABLE fresh_test (event_time TIMESTAMPTZ NOT NULL, energy_kwh DOUBLE PRECISION);
SELECT create_hypertable('fresh_test', 'event_time');
CREATE MATERIALIZED VIEW fresh_test_hourly
WITH (timescaledb.continuous, timescaledb.materialized_only = true) AS
SELECT time_bucket('1 hour', event_time) AS bucket,
       SUM(energy_kwh) AS energy_kwh, COUNT(*) AS readings
FROM fresh_test GROUP BY 1
WITH NO DATA;