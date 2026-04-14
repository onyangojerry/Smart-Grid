# Author: Jerry Onyango
# Contribution: Implements ordered at-least-once telemetry replay with persisted retry/backoff handling and failure classification.
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .failures import AuthFailure, EdgeIngestFailure, TransientServerError, TransportFailure, ValidationFailure
from .storage.sqlite import EdgeSQLiteStore


UploadFn = Callable[[str, dict], None]

'''
The ReplayService class provides a mechanism for buffering telemetry 
data locally on the edge device and reliably uploading it to the 
control loop. The buffer_telemetry method allows adding new telemetry 
records to the local store, while the replay_once method attempts to 
upload pending records in order, with retry and backoff logic for 
handling failures. The rebuild_queue_snapshot method can be used to 
inspect the current state of the pending telemetry queue, which is 
useful for monitoring and debugging. The backoff strategy uses 
exponential backoff with configurable base and maximum limits 
to avoid overwhelming the network or control loop during transient issues.

The failure_class field enables classification of failures (auth, transport, validation)
to support intelligent retry strategy: auth failures do not retry; transient failures
use exponential backoff; validation failures do not retry.
'''
@dataclass
class ReplayService:
    store: EdgeSQLiteStore
    upload_fn: UploadFn
    base_backoff_seconds: int = 2
    max_backoff_seconds: int = 60

    def buffer_telemetry(self, site_id: str, records: list[object]) -> int:
        return self.store.enqueue_telemetry(site_id=site_id, records=records)

    def replay_once(self, limit: int = 100) -> dict[str, int]:
        pending = self.store.list_pending_telemetry(limit=limit)
        sent = 0
        failed = 0
        failed_by_class: dict[str, int] = {}

        for row in pending:
            try:
                self.upload_fn(row["site_id"], row["payload"])
                self.store.ack_telemetry(row["id"])
                sent += 1
            except EdgeIngestFailure as exc:
                # Classified failure: apply retry strategy based on failure class
                failure_class = exc.failure_class
                backoff = self._backoff_for_failure_class(failure_class, row["attempt_count"] + 1)
                
                failed_by_class[failure_class] = failed_by_class.get(failure_class, 0) + 1
                self.store.mark_telemetry_retry(
                    row["id"],
                    error=str(exc)[:512],
                    backoff_seconds=backoff,
                    failure_class=failure_class,
                )
                failed += 1
            except Exception as exc:
                # Unclassified exception (fallback): treat as transport failure for backoff
                failure_class = "unclassified_exception"
                backoff = self._backoff_for_failure_class("transport_failure", row["attempt_count"] + 1)
                
                failed_by_class[failure_class] = failed_by_class.get(failure_class, 0) + 1
                self.store.mark_telemetry_retry(
                    row["id"],
                    error=str(exc)[:512],
                    backoff_seconds=backoff,
                    failure_class=failure_class,
                )
                failed += 1

        return {
            "attempted": len(pending),
            "sent": sent,
            "failed": failed,
            "remaining": len(self.store.list_pending_telemetry(limit=100000)),
            "failed_by_class": failed_by_class,
        }

    def rebuild_queue_snapshot(self, limit: int = 100000) -> list[dict]:
        return self.store.list_pending_telemetry(limit=limit)

    @staticmethod
    def _backoff_for_failure_class(failure_class: str, attempt: int) -> int:
        """
        Calculate backoff seconds based on failure class and attempt count.
        - auth_failure: Do not retry (0 seconds signals no backoff, handled by caller)
        - validation_failure: Do not retry (0 seconds)
        - transient_server_error: Exponential backoff (2^n)
        - transport_failure: Exponential backoff (2^n)
        """
        if failure_class in {"auth_failure", "validation_failure"}:
            # Do not retry: return max backoff to prevent immediate retry loops
            # (caller should interpret >60s as "do not retry" or marked as permanent)
            return 999999  # Signal: do not retry

        # Transient failures: exponential backoff
        value = 2 * (2 ** max(0, attempt - 1))  # base=2, formula: 2^n
        return min(60, value)  # Max backoff 60 seconds

    def _backoff_seconds(self, attempt: int) -> int:
        """Deprecated: Use _backoff_for_failure_class instead. Kept for compatibility."""
        value = self.base_backoff_seconds * (2 ** max(0, attempt - 1))
        return min(self.max_backoff_seconds, value)
