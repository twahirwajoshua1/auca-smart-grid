CREATE TABLE energy_time_compressed (
    meter_id BIGINT, event_time TIMESTAMPTZ, received_time TIMESTAMPTZ,
    power_kw DOUBLE PRECISION, voltage_v DOUBLE PRECISION,
    current_a DOUBLE PRECISION, frequency_hz DOUBLE PRECISION,
    energy_kwh DOUBLE PRECISION
);
SELECT create_hypertable('energy_time_compressed', 'event_time',
                         chunk_time_interval => INTERVAL '1 day');
CREATE INDEX energy_time_compressed_meter_time_idx
    ON energy_time_compressed (meter_id, event_time DESC);

CREATE TABLE energy_meter_compressed (
    meter_id BIGINT, event_time TIMESTAMPTZ, received_time TIMESTAMPTZ,
    power_kw DOUBLE PRECISION, voltage_v DOUBLE PRECISION,
    current_a DOUBLE PRECISION, frequency_hz DOUBLE PRECISION,
    energy_kwh DOUBLE PRECISION
);
SELECT create_hypertable('energy_meter_compressed', 'event_time',
                         chunk_time_interval => INTERVAL '1 day');
CREATE INDEX energy_meter_compressed_meter_time_idx
    ON energy_meter_compressed (meter_id, event_time DESC);

ALTER TABLE energy_time_compressed SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'event_time DESC');

ALTER TABLE energy_meter_compressed SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'meter_id',
    timescaledb.compress_orderby = 'event_time DESC');