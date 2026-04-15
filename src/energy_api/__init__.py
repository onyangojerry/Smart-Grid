# Author: Jerry Onyango
# Contribution: Exposes the FastAPI app object for package-level imports.
try:
    from .main import app
except ImportError:
    app = None  # type: ignore

__all__ = ["app"]
