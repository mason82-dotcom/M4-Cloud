CREATE TABLE IF NOT EXISTS integration_events (
    id BIGSERIAL PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL,
    topic TEXT,
    payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS integration_events_received_at_idx
    ON integration_events (received_at DESC);

CREATE TABLE IF NOT EXISTS service_heartbeats (
    service TEXT PRIMARY KEY,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
