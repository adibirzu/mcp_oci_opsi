"""OCI client wrapper - imports from parent module.

This module re-exports OCI client factories from the root-level oci_clients.py
to maintain compatibility with tools that expect clients in the same folder.
"""

from ..oci_clients import (
    get_opsi_client,
    get_dbm_client,
    list_all,
    extract_region_from_ocid,
    get_ocid_resource_type,
)

# Alias for compatibility
get_database_management_client = get_dbm_client

__all__ = [
    "get_opsi_client",
    "get_dbm_client",
    "get_database_management_client",
    "list_all",
    "extract_region_from_ocid",
    "get_ocid_resource_type",
]
