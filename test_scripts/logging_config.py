"""Centralized logging configuration for MCP servers.

Provides JSON-friendly structured logging with configurable levels.
"""

import logging
import os
import sys
from typing import Optional


def configure_logging(level: Optional[str] = None) -> None:
    """Configure root logger for MCP processes.
    
    IMPORTANT: All logging goes to stderr to avoid interfering with JSON-RPC on stdout.
    """
    log_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()

    # Use stderr for all logging - stdout is reserved for JSON-RPC protocol
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(log_level)
    root.addHandler(handler)

    logging.getLogger("oci").setLevel(os.getenv("OCI_LOG_LEVEL", "WARNING").upper())
