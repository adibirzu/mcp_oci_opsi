"""Database Management tablespace management and AWR metrics APIs."""

from typing import Any, Optional
import oci

from .oci_clients import get_dbm_client, list_all, extract_region_from_ocid


def list_tablespaces(
    managed_database_id: str,
    opc_named_credential_id: Optional[str] = None,
    name: Optional[str] = None,
    tablespace_type: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    List tablespaces in a managed database.

    Args:
        managed_database_id: Managed database OCID
        opc_named_credential_id: Named credential OCID for authentication
        name: Filter by tablespace name
        tablespace_type: Filter by type (PERMANENT, TEMPORARY, UNDO)
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with list of tablespaces and their details
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            region = extract_region_from_ocid(managed_database_id)
            client = get_dbm_client(region=region)

            kwargs = {"managed_database_id": managed_database_id}
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id
            if name:
                kwargs["name"] = name
            if tablespace_type:
                kwargs["tablespace_type"] = tablespace_type

            # Note: list_tablespaces returns Tablespace objects
            # We need to use summarize_managed_database_availability for tablespace info
            # or get it through AWR/ASH data

            # Alternative: Use the existing get_tablespace_usage function
            # For now, let's implement a basic version
            response = client.list_tablespaces(**kwargs)
            tablespaces = response.data.items if hasattr(response.data, 'items') else [response.data]

            items = []
            for ts in tablespaces:
                items.append({
                    "name": ts.name,
                    "type": getattr(ts, "type", None),
                    "status": getattr(ts, "status", None),
                    "block_size_bytes": getattr(ts, "block_size_bytes", None),
                    "logging": getattr(ts, "logging", None),
                    "is_force_logging": getattr(ts, "is_force_logging", None),
                    "extent_management": getattr(ts, "extent_management", None),
                    "allocation_type": getattr(ts, "allocation_type", None),
                    "is_plugged_in": getattr(ts, "is_plugged_in", None),
                    "segment_space_management": getattr(ts, "segment_space_management", None),
                    "default_table_compression": getattr(ts, "default_table_compression", None),
                    "retention": getattr(ts, "retention", None),
                    "is_bigfile": getattr(ts, "is_bigfile", None),
                    "predicate_evaluation": getattr(ts, "predicate_evaluation", None),
                    "is_encrypted": getattr(ts, "is_encrypted", None),
                    "compress_for": getattr(ts, "compress_for", None),
                    "default_in_memory": getattr(ts, "default_in_memory", None),
                    "default_in_memory_priority": getattr(ts, "default_in_memory_priority", None),
                    "default_in_memory_distribute": getattr(ts, "default_in_memory_distribute", None),
                    "default_in_memory_compression": getattr(ts, "default_in_memory_compression", None),
                    "default_in_memory_duplicate": getattr(ts, "default_in_memory_duplicate", None),
                    "shared": getattr(ts, "shared", None),
                    "default_index_compression": getattr(ts, "default_index_compression", None),
                    "index_compress_for": getattr(ts, "index_compress_for", None),
                    "default_cell_memory": getattr(ts, "default_cell_memory", None),
                    "default_in_memory_service": getattr(ts, "default_in_memory_service", None),
                    "default_in_memory_service_name": getattr(ts, "default_in_memory_service_name", None),
                    "lost_write_protect": getattr(ts, "lost_write_protect", None),
                    "is_chunk_tablespace": getattr(ts, "is_chunk_tablespace", None),
                    "temp_group": getattr(ts, "temp_group", None),
                    "max_size_kb": getattr(ts, "max_size_kb", None),
                    "allocated_size_kb": getattr(ts, "allocated_size_kb", None),
                    "user_size_kb": getattr(ts, "user_size_kb", None),
                    "free_space_kb": getattr(ts, "free_space_kb", None),
                    "used_space_kb": getattr(ts, "used_space_kb", None),
                    "used_percent_available": getattr(ts, "used_percent_available", None),
                    "used_percent_allocated": getattr(ts, "used_percent_allocated", None),
                    "is_default": getattr(ts, "is_default", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "items": items,
                "count": len(items),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "managed_database_id": managed_database_id,
        }


def get_tablespace(
    managed_database_id: str,
    tablespace_name: str,
    opc_named_credential_id: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get detailed information about a specific tablespace.

    Args:
        managed_database_id: Managed database OCID
        tablespace_name: Tablespace name
        opc_named_credential_id: Named credential OCID for authentication
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with detailed tablespace information
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            region = extract_region_from_ocid(managed_database_id)
            client = get_dbm_client(region=region)

            kwargs = {
                "managed_database_id": managed_database_id,
                "tablespace_name": tablespace_name,
            }
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id

            response = client.get_tablespace(**kwargs)
            ts = response.data

            return {
                "managed_database_id": managed_database_id,
                "tablespace": {
                    "name": ts.name,
                    "type": getattr(ts, "type", None),
                    "status": getattr(ts, "status", None),
                    "block_size_bytes": getattr(ts, "block_size_bytes", None),
                    "max_size_kb": getattr(ts, "max_size_kb", None),
                    "allocated_size_kb": getattr(ts, "allocated_size_kb", None),
                    "user_size_kb": getattr(ts, "user_size_kb", None),
                    "free_space_kb": getattr(ts, "free_space_kb", None),
                    "used_space_kb": getattr(ts, "used_space_kb", None),
                    "used_percent_available": getattr(ts, "used_percent_available", None),
                    "used_percent_allocated": getattr(ts, "used_percent_allocated", None),
                    "is_default": getattr(ts, "is_default", None),
                    "is_bigfile": getattr(ts, "is_bigfile", None),
                    "is_encrypted": getattr(ts, "is_encrypted", None),
                    "datafiles": [
                        {
                            "name": df.name,
                            "status": getattr(df, "status", None),
                            "online_status": getattr(df, "online_status", None),
                            "is_auto_extensible": getattr(df, "is_auto_extensible", None),
                            "lost_write_protect": getattr(df, "lost_write_protect", None),
                            "shared": getattr(df, "shared", None),
                            "instance_id": getattr(df, "instance_id", None),
                            "max_size_kb": getattr(df, "max_size_kb", None),
                            "allocated_size_kb": getattr(df, "allocated_size_kb", None),
                            "user_size_kb": getattr(df, "user_size_kb", None),
                            "increment_by": getattr(df, "increment_by", None),
                            "free_space_kb": getattr(df, "free_space_kb", None),
                            "used_space_kb": getattr(df, "used_space_kb", None),
                            "used_percent_available": getattr(df, "used_percent_available", None),
                            "used_percent_allocated": getattr(df, "used_percent_allocated", None),
                        }
                        for df in getattr(ts, "datafiles", [])
                    ],
                },
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "managed_database_id": managed_database_id,
            "tablespace_name": tablespace_name,
        }


def list_table_statistics(
    managed_database_id: str,
    opc_named_credential_id: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    List table statistics for optimizer performance.

    Table statistics are critical for the Oracle optimizer to create
    efficient execution plans.

    Args:
        managed_database_id: Managed database OCID
        opc_named_credential_id: Named credential OCID for authentication
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with table statistics information
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            region = extract_region_from_ocid(managed_database_id)
            client = get_dbm_client(region=region)

            kwargs = {"managed_database_id": managed_database_id}
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id

            table_stats = list_all(client.list_table_statistics, **kwargs)

            items = []
            for stat in table_stats:
                items.append({
                    "owner": stat.owner,
                    "table_name": stat.table_name,
                    "num_rows": getattr(stat, "num_rows", None),
                    "blocks": getattr(stat, "blocks", None),
                    "avg_row_len": getattr(stat, "avg_row_len", None),
                    "last_analyzed": str(stat.last_analyzed) if hasattr(stat, "last_analyzed") else None,
                    "partitioned": getattr(stat, "partitioned", None),
                    "stale_stats": getattr(stat, "stale_stats", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "items": items,
                "count": len(items),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "managed_database_id": managed_database_id,
        }
