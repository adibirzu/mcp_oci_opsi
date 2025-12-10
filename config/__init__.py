"""
Unified config namespace for mcp_oci_opsi.

This package re-exports configuration helpers and OCI client factories under a stable,
organized namespace without moving legacy modules. Consumers should import from this
package rather than top-level modules to decouple from file layout.

Example:
    from mcp_oci_opsi.config import get_oci_config, list_available_profiles
    from mcp_oci_opsi.config import get_opsi_client, list_all
"""

# Base configuration - now at root level
from ..config_base import (
    list_available_profiles,
    get_current_profile,
    get_signer_and_region,
)

# Use new AuthConfig for get_oci_config
from ..config_auth import get_oci_config

# Enhanced configuration - now at root level
try:
    from ..config_enhanced import (
        list_all_profiles_with_details,
    )
except ImportError:
    # Optional; keep import surface stable if module missing at runtime
    def list_all_profiles_with_details():
        return []

# OCI clients are not re-exported here to avoid import cycles.
# Import directly from mcp_oci_opsi.oci_clients where needed.

__all__ = [
    "get_oci_config",
    "list_available_profiles",
    "get_current_profile",
    "get_signer_and_region",
    "list_all_profiles_with_details",
]
