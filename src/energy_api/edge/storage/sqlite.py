# Author: Jerry Onyango
# Contribution: Implements WAL-backed SQLite persistence for telemetry buffering, command queueing, and reconciliation logs.
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from energy_api.edge.types import TelemetryRecord


class EdgeSQLiteStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=FULL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_buffer (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  site_id TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  attempt_count INTEGER NOT NULL DEFAULT 0,
                  next_attempt_at TEXT NOT NULL,
                  last_error TEXT,
                  failure_class TEXT DEFAULT 'unclassified'
                )
                """
            )
            # Add failure_class column if it doesn't exist (migration for existing tables)
            try:
                conn.execute("ALTER TABLE telemetry_buffer ADD COLUMN failure_class TEXT DEFAULT 'unclassified'")
            except Exception:
                # Column already exists, ignore error
                pass
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS command_queue (
                  command_id TEXT PRIMARY KEY,
                  site_id TEXT NOT NULL,
                                    idempotency_key TEXT,
                  payload_json TEXT NOT NULL,
                  status TEXT NOT NULL,
                  attempt_count INTEGER NOT NULL DEFAULT 0,
                  updated_at TEXT NOT NULL,
                  last_error TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reconciliation_log (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  command_id TEXT,
                  action TEXT NOT NULL,
                  status TEXT NOT NULL,
                  detail TEXT,
                  created_at TEXT NOT NULL
                )
                """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_telemetry_buffer_next_attempt ON telemetry_buffer(next_attempt_at, id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_command_queue_status ON command_queue(status, updated_at)"
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_command_queue_site_idempotency ON command_queue(site_id, idempotency_key) WHERE idempotency_key IS NOT NULL"
            )

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def enqueue_telemetry(self, site_id: str, records: list[TelemetryRecord]) -> int:
        now = datetime.now(UTC).isoformat()
        rows = [
            (
                site_id,
                json.dumps(self._serialize_record(record), separators=(",", ":")),
                now,
                now,
            )
            for record in records
        ]
        if not rows:
            return 0

        with self.transaction() as conn:
            conn.executemany(
                """
                INSERT INTO telemetry_buffer(site_id, payload_json, created_at, next_attempt_at)
                VALUES (?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def list_pending_telemetry(self, limit: int = 100) -> list[dict[str, Any]]:
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT id, site_id, payload_json, created_at, attempt_count, next_attempt_at, last_error, COALESCE(failure_class, 'unclassified')
                FROM telemetry_buffer
                WHERE next_attempt_at <= ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (now, limit),
            )
            rows = cursor.fetchall()

        output: list[dict[str, Any]] = []
        for row in rows:
            output.append(
                {
                    "id": row[0],
                    "site_id": row[1],
                    "payload": json.loads(row[2]),
                    "created_at": row[3],
                    "attempt_count": row[4],
                    "next_attempt_at": row[5],
                    "last_error": row[6],
                    "failure_class": row[7],
                }
            )
        return output

    def count_buffered_telemetry(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM telemetry_buffer").fetchone()
        return int(row[0]) if row else 0

    def list_buffered_row_ids(self, limit: int = 1000) -> list[int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id FROM telemetry_buffer ORDER BY id ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [int(row[0]) for row in rows]

    def ack_telemetry(self, row_id: int) -> None:
        with self.transaction() as conn:
            conn.execute("DELETE FROM telemetry_buffer WHERE id = ?", (row_id,))

    def mark_telemetry_retry(self, row_id: int, error: str, backoff_seconds: int, failure_class: str | None = None) -> None:
        next_attempt = (datetime.now(UTC)).timestamp() + max(0, backoff_seconds)
        next_attempt_at = datetime.fromtimestamp(next_attempt, tz=UTC).isoformat()
        with self.transaction() as conn:
            conn.execute(
                """
                UPDATE telemetry_buffer
                SET attempt_count = attempt_count + 1,
                    next_attempt_at = ?,
                    last_error = ?,
                    failure_class = COALESCE(?, failure_class)
                WHERE id = ?
                """,
                (next_attempt_at, error[:512], failure_class or "unclassified", row_id),
            )

    def upsert_command(
        self,
        command_id: str,
        site_id: str,
        payload: dict[str, Any],
        status: str = "queued",
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        existing = self.get_command(command_id=command_id)
        if existing:
            return existing
        if idempotency_key:
            existing = self.get_command(site_id=site_id, idempotency_key=idempotency_key)
            if existing:
                return existing

        now = datetime.now(UTC).isoformat()
        with self.transaction() as conn:
            conn.execute(
                """
                INSERT INTO command_queue(command_id, site_id, idempotency_key, payload_json, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(command_id)
                DO UPDATE SET payload_json = excluded.payload_json,
                              status = excluded.status,
                              updated_at = excluded.updated_at
                """,
                (command_id, site_id, idempotency_key, json.dumps(payload, separators=(",", ":")), status, now),
            )
        row = self.get_command(command_id=command_id)
        if not row:
            raise RuntimeError("failed to upsert command")
        return row

    def list_unresolved_commands(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT command_id, site_id, payload_json, status, attempt_count, updated_at, last_error
                FROM command_queue
                WHERE status IN ('queued', 'sent', 'applying')
                ORDER BY updated_at ASC
                """
            )
            rows = cursor.fetchall()

        return [
            {
                "command_id": row[0],
                "site_id": row[1],
                "payload": json.loads(row[2]),
                "status": row[3],
                "attempt_count": row[4],
                "updated_at": row[5],
                "last_error": row[6],
            }
            for row in rows
        ]

    def update_command_status(self, command_id: str, status: str, error: str | None = None) -> None:
        now = datetime.now(UTC).isoformat()
        with self.transaction() as conn:
            conn.execute(
                """
                UPDATE command_queue
                SET status = ?,
                    attempt_count = CASE WHEN ? IN ('failed', 'applying') THEN attempt_count + 1 ELSE attempt_count END,
                    updated_at = ?,
                    last_error = COALESCE(?, last_error)
                WHERE command_id = ?
                """,
                (status, status, now, error[:512] if error else None, command_id),
            )

    def get_command(
        self,
        command_id: str | None = None,
        site_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any] | None:
        where_clauses: list[str] = []
        params: list[Any] = []
        if command_id:
            where_clauses.append("command_id = ?")
            params.append(command_id)
        if site_id:
            where_clauses.append("site_id = ?")
            params.append(site_id)
        if idempotency_key:
            where_clauses.append("idempotency_key = ?")
            params.append(idempotency_key)
        if not where_clauses:
            return None

        query = (
            "SELECT command_id, site_id, idempotency_key, payload_json, status, attempt_count, updated_at, last_error "
            "FROM command_queue WHERE " + " AND ".join(where_clauses) + " ORDER BY updated_at DESC LIMIT 1"
        )
        with self._connect() as conn:
            row = conn.execute(query, tuple(params)).fetchone()
        if not row:
            return None
        return {
            "command_id": row[0],
            "site_id": row[1],
            "idempotency_key": row[2],
            "payload": json.loads(row[3]),
            "status": row[4],
            "attempt_count": row[5],
            "updated_at": row[6],
            "last_error": row[7],
        }

    def has_unresolved_command(self, site_id: str, except_command_id: str | None = None) -> bool:
        query = "SELECT 1 FROM command_queue WHERE site_id = ? AND status IN ('queued', 'sent', 'applying')"
        params: list[Any] = [site_id]
        if except_command_id:
            query += " AND command_id <> ?"
            params.append(except_command_id)
        query += " LIMIT 1"
        with self._connect() as conn:
            row = conn.execute(query, tuple(params)).fetchone()
        return row is not None

    def count_command_backlog(self, site_id: str | None = None) -> int:
        query = "SELECT COUNT(*) FROM command_queue WHERE status IN ('queued', 'sent', 'applying')"
        params: tuple[Any, ...] = ()
        if site_id:
            query += " AND site_id = ?"
            params = (site_id,)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return int(row[0]) if row else 0

    def append_reconciliation_log(self, command_id: str | None, action: str, status: str, detail: str | None = None) -> None:
        now = datetime.now(UTC).isoformat()
        with self.transaction() as conn:
            conn.execute(
                """
                INSERT INTO reconciliation_log(command_id, action, status, detail, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (command_id, action, status, detail, now),
            )

    def get_wal_mode(self) -> str:
        with self._connect() as conn:
            row = conn.execute("PRAGMA journal_mode;").fetchone()
        return str(row[0]).lower() if row else ""

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    @staticmethod
    def _serialize_record(record: TelemetryRecord) -> dict[str, Any]:
        output = asdict(record)
        for key in ("ts", "device_ts", "gateway_received_at", "processed_at"):
            value = output.get(key)
            if isinstance(value, datetime):
                output[key] = value.isoformat()
        return output
