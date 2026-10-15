CREATE TABLE energy_readings_3h (
    meter_id      BIGINT,
    event_time    TIMESTAMPTZ,
    received_time TIMESTAMPTZ,
    power_kw      DOUBLE PRECISION,
    voltage_v     DOUBLE PRECISION,
    current_a     DOUBLE PRECISION,
    frequency_hz  DOUBLE PRECISION,
    energy_kwh    DOUBLE PRECISION
);
SELECT create_hypertable('energy_readings_3h', 'event_time',
                         chunk_time_interval => INTERVAL '3 hours');

CREATE TABLE energy_readings_week (
    meter_id      BIGINT,
    event_time    TIMESTAMPTZ,
    received_time TIMESTAMPTZ,
    power_kw      DOUBLE PRECISION,
    voltage_v     DOUBLE PRECISION,
    current_a     DOUBLE PRECISION,
    frequency_hz  DOUBLE PRECISION,
    energy_kwh    DOUBLE PRECISION
);
SELECT create_hypertable('energy_readings_week', 'event_time',
                         chunk_time_interval => INTERVAL '7 days');