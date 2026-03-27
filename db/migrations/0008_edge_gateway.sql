ALTER TABLE point_mappings ADD COLUMN IF NOT EXISTS signed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE point_mappings ADD COLUMN IF NOT EXISTS register_address INT NOT NULL DEFAULT 0;
ALTER TABLE point_mappings ADD COLUMN IF NOT EXISTS register_count INT NOT NULL DEFAULT 1;

CREATE TABLE IF NOT EXISTS edge_gateways (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    host TEXT NOT NULL,
    port INT NOT NULL DEFAULT 502,
    status TEXT NOT NULL DEFAULT 'offline',
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_edge_gateway_site ON edge_gateways(site_id);
