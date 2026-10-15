BEGIN;

CREATE TEMP TABLE clean_rows AS
SELECT DISTINCT meter_id, event_time, received_time, power_kw,
       voltage_v, current_a, frequency_hz, energy_kwh
FROM energy_readings;

TRUNCATE energy_readings;

INSERT INTO energy_readings
SELECT meter_id, event_time, received_time, power_kw,
       voltage_v, current_a, frequency_hz, energy_kwh
FROM clean_rows;

COMMIT;

SELECT COUNT(*) AS rows_after, SUM(energy_kwh) AS energy_after
FROM energy_readings;