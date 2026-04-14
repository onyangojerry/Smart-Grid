# Author: Jerry Onyango
# Contribution: Configures structured JSON-like application logging for operational observability.
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: int = logging.INFO, log_file_path: Optional[str] = None) -> None:
    handlers = []
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handlers.append(console_handler)
    
    if log_file_path:
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(file_handler)
    
    logging.basicConfig(level=level, format=LOG_FORMAT, handlers=handlers)
