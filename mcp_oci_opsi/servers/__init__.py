"""Server composition module for MCP OCI OPSI.

This module provides domain-specific sub-servers that can be composed
into the main MCP server for modular architecture.

Sub-servers:
- cache_server: Fast cache-based tools (zero API calls)
- opsi_server: Operations Insights tools
- dbm_server: Database Management tools
- admin_server: Profile and configuration management
"""

from .cache_server import cache_server
from .opsi_server import opsi_server
from .dbm_server import dbm_server
from .admin_server import admin_server

__all__ = [
    "cache_server",
    "opsi_server",
    "dbm_server",
    "admin_server",
]
