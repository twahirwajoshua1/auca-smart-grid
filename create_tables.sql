CREATE TABLE energy_live (
    meter_id      BIGINT,
    event_time    TIMESTAMPTZ,
    received_time TIMESTAMPTZ,
    power_kw      DOUBLE PRECISION,
    voltage_v     DOUBLE PRECISION,
    current_a     DOUBLE PRECISION,
    frequency_hz  DOUBLE PRECISION,
    energy_kwh    DOUBLE PRECISION
);

CREATE TABLE energy_readings (
    meter_id      BIGINT,
    event_time    TIMESTAMPTZ,
    received_time TIMESTAMPTZ,
    power_kw      DOUBLE PRECISION,
    voltage_v     DOUBLE PRECISION,
    current_a     DOUBLE PRECISION,
    frequency_hz  DOUBLE PRECISION,
    energy_kwh    DOUBLE PRECISION
);

SELECT create_hypertable('energy_readings', 'event_time',
                         chunk_time_interval => INTERVAL '1 day');

CREATE TABLE meters (
    meter_id       BIGINT PRIMARY KEY,
    region         TEXT,
    customer_type  TEXT,
    base_power_kw  DOUBLE PRECISION,
    power_factor   DOUBLE PRECISION
);