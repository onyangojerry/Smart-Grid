CREATE TABLE IF NOT EXISTS control_alerts (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    state TEXT NOT NULL CHECK (state IN ('open', 'acknowledged', 'resolved')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    source_key TEXT,
    threshold_value DOUBLE PRECISION,
    actual_value DOUBLE PRECISION,
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMPTZ,
    resolved_by TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_control_alerts_site_state ON control_alerts(site_id, state, severity);
CREATE INDEX IF NOT EXISTS idx_control_alerts_open ON control_alerts(site_id, severity, created_at DESC) WHERE state = 'open';
CREATE INDEX IF NOT EXISTS idx_control_alerts_created ON control_alerts(created_at DESC);

CREATE OR REPLACE FUNCTION update_alerts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER alerts_updated_at
    BEFORE UPDATE ON alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_alerts_updated_at();
