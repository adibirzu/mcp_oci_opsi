"""Enhanced OCI client wrapper - imports from parent module.

This module re-exports enhanced OCI client factories from the root-level oci_clients_enhanced.py
to maintain compatibility with tools that expect clients in the same folder.
"""

from ..oci_clients_enhanced import (
    get_opsi_client,
    get_dbm_client,
    get_identity_client,
    get_database_client,
    clear_client_cache,
)

# These functions are in oci_clients.py, not oci_clients_enhanced.py
from ..oci_clients import (
    extract_region_from_ocid,
    get_ocid_resource_type,
    list_all,
)

__all__ = [
    "get_opsi_client",
    "get_dbm_client",
    "get_identity_client",
    "get_database_client",
    "clear_client_cache",
    "extract_region_from_ocid",
    "get_ocid_resource_type",
    "list_all",
]
