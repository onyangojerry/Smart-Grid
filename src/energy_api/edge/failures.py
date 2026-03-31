# Author: Jerry Onyango
# Contribution: Defines failure classification exceptions for distinguish auth vs transport vs validation errors.

from __future__ import annotations


class EdgeIngestFailure(Exception):
    """Base exception for edge ingest failures with classification."""

    failure_class: str = "unknown"

    def __init__(self, message: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status


class AuthFailure(EdgeIngestFailure):
    """Auth failure (401/403): Should NOT retry immediately."""

    failure_class = "auth_failure"

    def __init__(self, message: str, http_status: int | None = None) -> None:
        super().__init__(message, http_status)
        self.message = message


class TransientServerError(EdgeIngestFailure):
    """Transient server error (429/500/503): Should retry with exponential backoff."""

    failure_class = "transient_server_error"

    def __init__(self, message: str, http_status: int | None = None, retry_after_seconds: int | None = None) -> None:
        super().__init__(message, http_status)
        self.retry_after_seconds = retry_after_seconds


class TransportFailure(EdgeIngestFailure):
    """Network/transport failure (timeout, DNS, refused, etc): Should retry with exponential backoff."""

    failure_class = "transport_failure"


class ValidationFailure(EdgeIngestFailure):
    """Validation failure (malformed payload, etc): Should NOT retry (permanent error)."""

    failure_class = "validation_failure"


class NetworkUnavailable(TransportFailure):
    """Specific transport failure: API unreachable."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
