# Author: Jerry Onyango
# Contribution: Implements PostgreSQL persistence and schema bootstrap for control-loop entities, telemetry, commands, runs, and savings snapshots.

# /Users/loan/Desktop/energyallocation/src/energy_api/control/repository.py
from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def _db_url() -> str:
    return os.getenv(
        "EA_DATABASE_URL",
        "postgresql://energyallocation:energyallocation@localhost:5432/energyallocation",
    )


class ControlRepository:
    def __init__(self, db_url: str | None = None) -> None:
        self._db_url = db_url or _db_url()
        self._ensure_control_schema()

    def _connect(self):
        return psycopg.connect(self._db_url, row_factory=dict_row, autocommit=True)

    def _table_exists(self, table_name: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    ) AS exists_flag
                    """,
                    (table_name,),
                )
                return cur.fetchone()["exists_flag"]

    def _column_exists(self, table_name: str, column_name: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = %s 
                        AND column_name = %s
                    ) AS exists_flag
                    """,
                    (table_name, column_name),
                )
                return cur.fetchone()["exists_flag"]

    def _ensure_control_schema(self) -> None:
        required_tables = (
            "sites",
            "assets",
            "devices",
            "telemetry_streams",
            "telemetry_points",
            "point_mappings",
            "tariffs",
            "control_policies",
            "optimization_runs",
            "commands",
            "savings_snapshots",
            "simulations",
            "control_alerts",
            "edge_gateways",
        )
        missing_tables = [table_name for table_name in required_tables if not self._table_exists(table_name)]
        if missing_tables:
            raise RuntimeError(f"missing required control schema tables: {', '.join(missing_tables)}")

    @staticmethod
    def _id(prefix: str) -> str:
        # use a more robust ID generation strategy (e.g., UUIDs, ULIDs) to ensure uniqueness and avoid collisions. Here, we use a simple random hex string for demonstration purposes.
        return f"{prefix}_{os.urandom(4).hex()}"

    def upsert_site_defaults(self, site_id: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sites(id, name)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (site_id, f"Site {site_id}"),
                )
                cur.execute(
                    """
                    INSERT INTO control_policies(id, site_id)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (f"pol_{site_id}", site_id),
                )
                cur.execute(
                    """
                    INSERT INTO devices(id, site_id, device_type)
                    VALUES (%s, %s, 'battery_inverter')
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (f"dev_{site_id}", site_id),
                )

                canonical_keys = [
                    "site_load_kw",
                    "pv_generation_kw",
                    "pv_kw",
                    "load_kw",
                    "battery_soc",
                    "battery_power_kw",
                    "grid_import_kw",
                    "grid_export_kw",
                    "battery_voltage_v",
                    "battery_current_a",
                    "battery_temp_c",
                    "inverter_mode",
                    "alarm_code",
                    "device_online",
                    "device_fault",
                    "price_import",
                    "price_export",
                ]
                for key in canonical_keys:
                    cur.execute(
                        """
                        INSERT INTO telemetry_streams(id, site_id, device_id, canonical_key, is_critical)
                        VALUES (%s, %s, %s, %s, true)
                        ON CONFLICT (site_id, canonical_key) DO NOTHING
                        """,
                        (f"str_{site_id}_{key}", site_id, f"dev_{site_id}", key),
                    )

    def get_active_policy(self, site_id: str) -> dict[str, Any]:
        self.upsert_site_defaults(site_id)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM control_policies
                    WHERE site_id = %s AND active = true
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (site_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("active control policy not found")
                return row

    def list_sites(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM sites ORDER BY created_at DESC")
                return cur.fetchall()

    def get_site(self, site_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM sites WHERE id = %s", (site_id,))
                return cur.fetchone()

    def update_site(self, site_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        if not updates:
            return self.get_site(site_id)
        
        allowed_keys = {"name", "timezone", "reserve_soc_min", "polling_interval_seconds"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_keys}
        if not filtered_updates:
            return self.get_site(site_id)

        set_clause = ", ".join([f"{k} = %s" for k in filtered_updates.keys()])
        values = list(filtered_updates.values())
        values.append(site_id)

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE sites SET {set_clause}, updated_at = now() WHERE id = %s RETURNING *",
                    values
                )
                return cur.fetchone()

    def list_devices(self, site_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM devices WHERE site_id = %s ORDER BY created_at ASC", (site_id,))
                return cur.fetchall()

    def get_device(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM devices WHERE site_id = %s AND id = %s", (site_id, device_id))
                return cur.fetchone()

    def create_site(self, site_id: str, name: str, timezone: str, reserve_soc_min: float, polling_interval_seconds: int) -> dict[str, Any]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sites(id, name, timezone, reserve_soc_min, polling_interval_seconds)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id)
                    DO UPDATE SET
                      name = EXCLUDED.name,
                      timezone = EXCLUDED.timezone,
                      reserve_soc_min = EXCLUDED.reserve_soc_min,
                      polling_interval_seconds = EXCLUDED.polling_interval_seconds,
                      updated_at = now()
                    RETURNING *
                    """,
                    (site_id, name, timezone, reserve_soc_min, polling_interval_seconds),
                )
                created = cur.fetchone()

                cur.execute(
                    """
                    INSERT INTO control_policies(
                      id, site_id, reserve_soc_min
                    ) VALUES (%s, %s, %s)
                    ON CONFLICT (id)
                    DO UPDATE SET reserve_soc_min = EXCLUDED.reserve_soc_min, updated_at = now()
                    """,
                    (f"pol_{site_id}", site_id, reserve_soc_min),
                )
                return created

    def create_device(self, site_id: str, device_type: str, protocol: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        device_id = self._id("dev")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO devices(id, site_id, device_type, protocol, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (device_id, site_id, device_type, protocol, Jsonb(metadata or {})),
                )
                return cur.fetchone()

    def create_asset(self, site_id: str, asset_type: str, name: str) -> dict[str, Any]:
        asset_id = self._id("ast")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO assets(id, site_id, asset_type, name)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                    """,
                    (asset_id, site_id, asset_type, name),
                )
                return cur.fetchone()

    def list_assets(self, site_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM assets WHERE site_id = %s ORDER BY created_at ASC", (site_id,))
                return cur.fetchall()

    def get_asset(self, asset_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM assets WHERE id = %s", (asset_id,))
                return cur.fetchone()

    def delete_asset(self, asset_id: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM assets WHERE id = %s RETURNING id", (asset_id,))
                return cur.fetchone() is not None

    def create_asset_device(self, asset_id: str, device_type: str, protocol: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT site_id FROM assets WHERE id = %s", (asset_id,))
                row = cur.fetchone()
                if not row:
                    raise ValueError("Asset not found")
                site_id = row["site_id"]
                
                device_id = self._id("dev")
                cur.execute(
                    """
                    INSERT INTO devices(id, site_id, asset_id, device_type, protocol, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (device_id, site_id, asset_id, device_type, protocol, Jsonb(metadata or {})),
                )
                return cur.fetchone()

    def create_device_mapping(self, device_id: str, source_key: str, canonical_key: str, scale_factor: float = 1.0) -> dict[str, Any]:
        mapping_id = self._id("map")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO point_mappings(id, device_id, source_key, canonical_key, scale_factor)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (mapping_id, device_id, source_key, canonical_key, scale_factor),
                )
                return cur.fetchone()

    def get_polling_interval(self, site_id: str) -> int:
        self.upsert_site_defaults(site_id)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT polling_interval_seconds FROM sites WHERE id = %s", (site_id,))
                row = cur.fetchone()
                return int(row["polling_interval_seconds"]) if row else 300

    def get_primary_device_id(self, site_id: str) -> str:
        self.upsert_site_defaults(site_id)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id
                    FROM devices
                    WHERE site_id = %s
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (site_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("device not found")
                return str(row["id"])

    def resolve_stream_ids(self, site_id: str, canonical_keys: list[str]) -> dict[str, dict[str, Any]]:
        if not canonical_keys:
            return {}
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, canonical_key, unit, is_critical, device_id
                    FROM telemetry_streams
                    WHERE site_id = %s AND canonical_key = ANY(%s)
                    """,
                    (site_id, canonical_keys),
                )
                rows = cur.fetchall()
        return {row["canonical_key"]: row for row in rows}

    def insert_telemetry_points(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        inserted = 0
        with self._connect() as conn:
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute(
                        """
                        INSERT INTO telemetry_points(stream_id, ts, value, unit, quality)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (stream_id, ts) DO NOTHING
                        RETURNING id
                        """,
                        (
                            row["stream_id"],
                            row["ts"],
                            row["value"],
                            row.get("unit"),
                            row["quality"],
                        ),
                    )
                    if cur.fetchone() is not None:
                        inserted += 1
        return inserted

    def get_latest_state_rows(self, site_id: str) -> dict[str, dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.canonical_key, s.is_critical, p.ts, p.value, p.quality
                    FROM telemetry_streams s
                    LEFT JOIN LATERAL (
                        SELECT ts, value, quality
                        FROM telemetry_points p
                        WHERE p.stream_id = s.id
                        ORDER BY ts DESC
                        LIMIT 1
                    ) p ON true
                    WHERE s.site_id = %s
                    """,
                    (site_id,),
                )
                rows = cur.fetchall()
        return {row["canonical_key"]: row for row in rows}

    def get_telemetry_history(self, site_id: str, key: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT p.ts, p.value, p.unit, p.quality, s.canonical_key
                    FROM telemetry_points p
                    JOIN telemetry_streams s ON p.stream_id = s.id
                    WHERE s.site_id = %s AND s.canonical_key = %s
                      AND p.ts BETWEEN %s AND %s
                    ORDER BY p.ts ASC
                    """,
                    (site_id, key, start, end),
                )
                return cur.fetchall()

    # To prevent command spamming, we check if there's a recently sent command for the same device that hasn't 
    # been acknowledged yet. If such a command exists and was requested within the block_seconds window, we can 
    # choose to block the new command or handle it according to your application's needs (e.g., queue it, replace the old command, etc.).
    def get_last_sent_unacked_command(self, device_id: str, block_seconds: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM commands
                    WHERE device_id = %s
                      AND status IN ('queued', 'sent')
                      AND acked_at IS NULL
                      AND requested_at >= %s
                    ORDER BY requested_at DESC
                    LIMIT 1
                    """,
                    (device_id, datetime.now(UTC) - timedelta(seconds=block_seconds)),
                )
                return cur.fetchone()

    def create_command(
        self,
        site_id: str,
        device_id: str,
        command_type: str,
        target_power_kw: float | None,
        target_soc: float | None,
        reason: str,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        command_id = self._id("cmd")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO commands(
                      id, site_id, device_id, command_type, target_power_kw,
                      target_soc, reason, status, idempotency_key
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'queued', %s)
                    RETURNING *
                    """,
                    (
                        command_id,
                        site_id,
                        device_id,
                        command_type,
                        target_power_kw,
                        target_soc,
                        reason,
                        idempotency_key,
                    ),
                )
                return cur.fetchone()

    def update_command_status(self, command_id: str, status: str, failure_reason: str | None = None) -> dict[str, Any]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                sent_at = datetime.now(UTC) if status == "sent" else None
                acked_at = datetime.now(UTC) if status == "acked" else None
                cur.execute(
                    """
                    UPDATE commands
                    SET status = %s,
                        failure_reason = COALESCE(%s, failure_reason),
                        sent_at = COALESCE(%s, sent_at),
                        acked_at = COALESCE(%s, acked_at)
                    WHERE id = %s
                    RETURNING *
                    """,
                    (status, failure_reason, sent_at, acked_at, command_id),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("command not found")
                return row

    def get_command(self, command_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM commands WHERE id = %s", (command_id,))
                return cur.fetchone()

    def create_optimization_run(
        self,
        site_id: str,
        mode: str,
        horizon_minutes: int,
        step_minutes: int,
        action_type: str,
        target_power_kw: float,
        score_json: dict[str, Any],
        explanation: dict[str, Any],
        state_json: dict[str, Any],
        command_id: str | None,
    ) -> str:
        run_id = self._id("opt")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO optimization_runs(
                      id, site_id, mode, horizon_minutes, step_minutes, action_type,
                      target_power_kw, score_json, explanation, state_json, command_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        site_id,
                        mode,
                        horizon_minutes,
                        step_minutes,
                        action_type,
                        target_power_kw,
                        Jsonb(score_json),
                        Jsonb(explanation),
                        Jsonb(state_json),
                        command_id,
                    ),
                )
        return run_id

    def list_optimization_runs(self, site_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM optimization_runs
                    WHERE site_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (site_id, limit),
                )
                return cur.fetchall()

    def get_optimization_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM optimization_runs WHERE id = %s", (run_id,))
                return cur.fetchone()

    def list_commands(self, site_id: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM commands
                    WHERE site_id = %s
                      AND requested_at BETWEEN %s AND %s
                    ORDER BY requested_at ASC
                    """,
                    (site_id, start, end),
                )
                return cur.fetchall()

    def list_commands_by_site(self, site_id: str, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM commands WHERE site_id = %s"
                params = [site_id]
                if status:
                    query += " AND status = %s"
                    params.append(status)
                query += " ORDER BY requested_at DESC LIMIT %s"
                params.append(limit)
                cur.execute(query, params)
                return cur.fetchall()

    def average_import_price(self, site_id: str) -> float:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT import_price_eur_kwh
                    FROM tariffs
                    WHERE site_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (site_id,),
                )
                row = cur.fetchone()
                return float(row["import_price_eur_kwh"]) if row else 0.20

    def upsert_savings_snapshot(
        self,
        site_id: str,
        start: datetime,
        end: datetime,
        baseline_cost: float,
        optimized_cost: float,
        savings_percent: float,
        battery_cycles: float,
        self_consumption_percent: float,
        peak_demand_reduction: float,
    ) -> str:
        snapshot_id = self._id("sav")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO savings_snapshots(
                      id, site_id, window_start, window_end,
                      baseline_cost, optimized_cost, savings_percent,
                      battery_cycles, self_consumption_percent, peak_demand_reduction
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        snapshot_id,
                        site_id,
                        start,
                        end,
                        baseline_cost,
                        optimized_cost,
                        savings_percent,
                        battery_cycles,
                        self_consumption_percent,
                        peak_demand_reduction,
                    ),
                )
        return snapshot_id

    def create_simulation(
        self,
        site_id: str,
        baseline_cost: float,
        optimized_cost: float,
        savings_percent: float,
        battery_cycles: float,
        self_consumption_percent: float,
        peak_demand_reduction: float,
        action_history: list[dict[str, Any]],
    ) -> str:
        sim_id = self._id("sim")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO simulations(
                      id, site_id, baseline_cost, optimized_cost, savings_percent,
                      battery_cycles, self_consumption_percent, peak_demand_reduction, action_history
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        sim_id,
                        site_id,
                        baseline_cost,
                        optimized_cost,
                        savings_percent,
                        battery_cycles,
                        self_consumption_percent,
                        peak_demand_reduction,
                        Jsonb(action_history),
                    ),
                )
        return sim_id

    def get_simulation(self, sim_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM simulations WHERE id = %s", (sim_id,))
                return cur.fetchone()

    def create_alert(
        self,
        site_id: str,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        source_key: str | None = None,
        threshold_value: float | None = None,
        actual_value: float | None = None,
    ) -> dict[str, Any]:
        alert_id = self._id("alrt")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO control_alerts(
                        id, site_id, alert_type, severity, state, title, message,
                        source_key, threshold_value, actual_value
                    ) VALUES (%s, %s, %s, %s, 'open', %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        alert_id,
                        site_id,
                        alert_type,
                        severity,
                        title,
                        message,
                        source_key,
                        threshold_value,
                        actual_value,
                    ),
                )
                return cur.fetchone()

    def list_alerts(self, site_id: str, state: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM control_alerts WHERE site_id = %s"
                params: list[Any] = [site_id]
                if state:
                    query += " AND state = %s"
                    params.append(state)
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                cur.execute(query, params)
                return cur.fetchall()

    def get_alert(self, alert_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM control_alerts WHERE id = %s", (alert_id,))
                return cur.fetchone()

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE control_alerts
                    SET state = 'acknowledged', acknowledged_by = %s, acknowledged_at = now()
                    WHERE id = %s AND state = 'open'
                    RETURNING *
                    """,
                    (acknowledged_by, alert_id),
                )
                return cur.fetchone()

    def resolve_alert(self, alert_id: str, resolved_by: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE control_alerts
                    SET state = 'resolved', resolved_by = %s, resolved_at = now()
                    WHERE id = %s AND state IN ('open', 'acknowledged')
                    RETURNING *
                    """,
                    (resolved_by, alert_id),
                )
                return cur.fetchone()

    def count_open_alerts(self, site_id: str) -> dict[str, int]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT severity, COUNT(*) as count
                    FROM control_alerts
                    WHERE site_id = %s AND state = 'open'
                    GROUP BY severity
                    """,
                    (site_id,),
                )
                rows = cur.fetchall()
        result = {"info": 0, "warning": 0, "critical": 0}
        for row in rows:
            result[row["severity"]] = int(row["count"])
        return result

    def create_edge_gateway(self, site_id: str, name: str, host: str, port: int) -> dict[str, Any]:
        gateway_id = self._id("gw")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO edge_gateways(id, site_id, name, host, port, status)
                    VALUES (%s, %s, %s, %s, %s, 'offline')
                    RETURNING *
                    """,
                    (gateway_id, site_id, name, host, port),
                )
                return cur.fetchone()

    def list_edge_gateways(self, site_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM edge_gateways WHERE site_id = %s ORDER BY created_at DESC",
                    (site_id,),
                )
                return cur.fetchall()

    def get_edge_gateway(self, gateway_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM edge_gateways WHERE id = %s", (gateway_id,))
                return cur.fetchone()

    def update_edge_gateway_heartbeat(self, gateway_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE edge_gateways
                    SET status = 'online', last_seen_at = now(), updated_at = now()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (gateway_id,),
                )
                return cur.fetchone()

    def update_edge_gateway_status(self, gateway_id: str, status: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE edge_gateways
                    SET status = %s, updated_at = now()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (status, gateway_id),
                )
                return cur.fetchone()

    def create_device_mapping(
        self,
        device_id: str,
        source_key: str,
        canonical_key: str,
        scale_factor: float = 1.0,
        byte_order: str = "big",
        word_order: str = "big",
        value_type: str = "float32",
        signed: bool = False,
        register_address: int = 0,
        register_count: int = 1,
        unit: str | None = None,
    ) -> dict[str, Any]:
        mapping_id = self._id("map")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO point_mappings(
                        id, device_id, source_key, canonical_key, scale_factor,
                        byte_order, word_order, value_type, signed,
                        register_address, register_count
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        mapping_id,
                        device_id,
                        source_key,
                        canonical_key,
                        scale_factor,
                        byte_order,
                        word_order,
                        value_type,
                        signed,
                        register_address,
                        register_count,
                    ),
                )
                row = cur.fetchone()
                if unit and row:
                    row = dict(row)
                    row["unit"] = unit
                return row

    def list_point_mappings(self, device_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM point_mappings WHERE device_id = %s ORDER BY source_key",
                    (device_id,),
                )
                return cur.fetchall()

    def delete_point_mapping(self, mapping_id: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM point_mappings WHERE id = %s RETURNING id", (mapping_id,))
                return cur.fetchone() is not None
