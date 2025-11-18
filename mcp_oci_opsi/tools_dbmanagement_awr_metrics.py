"""Database Management AWR metrics APIs for detailed performance analysis."""

from typing import Any, Optional
import oci

from .oci_clients import get_dbm_client, list_all, extract_region_from_ocid


def summarize_awr_db_metrics(
    managed_database_id: str,
    time_greater_than_or_equal_to: str,
    time_less_than_or_equal_to: str,
    name: Optional[list[str]] = None,
    opc_named_credential_id: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Summarize AWR database metrics over a time period.

    Provides aggregated metrics from AWR snapshots including wait events,
    system statistics, and resource usage.

    Args:
        managed_database_id: Managed database OCID
        time_greater_than_or_equal_to: Start time (ISO 8601)
        time_less_than_or_equal_to: End time (ISO 8601)
        name: Filter by specific metric names
        opc_named_credential_id: Named credential OCID for authentication
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with AWR metrics summary and trends
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
                "time_greater_than_or_equal_to": time_greater_than_or_equal_to,
                "time_less_than_or_equal_to": time_less_than_or_equal_to,
            }
            if name:
                kwargs["name"] = name
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id

            response = client.summarize_awr_db_metrics(**kwargs)

            items = []
            for metric in response.data.items if hasattr(response.data, 'items') else [response.data]:
                items.append({
                    "name": metric.name,
                    "timestamp": str(metric.timestamp) if hasattr(metric, "timestamp") else None,
                    "value": getattr(metric, "value", None),
                    "unit": getattr(metric, "unit", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "time_range": {
                    "start": time_greater_than_or_equal_to,
                    "end": time_less_than_or_equal_to,
                },
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


def summarize_awr_db_cpu_usages(
    managed_database_id: str,
    time_greater_than_or_equal_to: str,
    time_less_than_or_equal_to: str,
    opc_named_credential_id: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Summarize AWR database CPU usage over time.

    Provides detailed CPU usage metrics including user time, system time,
    and wait time from AWR snapshots.

    Args:
        managed_database_id: Managed database OCID
        time_greater_than_or_equal_to: Start time (ISO 8601)
        time_less_than_or_equal_to: End time (ISO 8601)
        opc_named_credential_id: Named credential OCID for authentication
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with CPU usage trends and statistics
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
                "time_greater_than_or_equal_to": time_greater_than_or_equal_to,
                "time_less_than_or_equal_to": time_less_than_or_equal_to,
            }
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id

            response = client.summarize_awr_db_cpu_usages(**kwargs)

            items = []
            for cpu_usage in response.data.items if hasattr(response.data, 'items') else [response.data]:
                items.append({
                    "timestamp": str(cpu_usage.timestamp) if hasattr(cpu_usage, "timestamp") else None,
                    "db_time": getattr(cpu_usage, "db_time", None),
                    "db_cpu": getattr(cpu_usage, "db_cpu", None),
                    "background_time": getattr(cpu_usage, "background_time", None),
                    "cpu_count": getattr(cpu_usage, "cpu_count", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "time_range": {
                    "start": time_greater_than_or_equal_to,
                    "end": time_less_than_or_equal_to,
                },
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


def summarize_awr_db_wait_event_buckets(
    managed_database_id: str,
    time_greater_than_or_equal_to: str,
    time_less_than_or_equal_to: str,
    name: Optional[list[str]] = None,
    opc_named_credential_id: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Summarize AWR database wait events in buckets.

    Provides wait event distribution across time buckets for identifying
    performance bottlenecks.

    Args:
        managed_database_id: Managed database OCID
        time_greater_than_or_equal_to: Start time (ISO 8601)
        time_less_than_or_equal_to: End time (ISO 8601)
        name: Filter by specific wait event names
        opc_named_credential_id: Named credential OCID for authentication
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with wait event buckets and statistics
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
                "time_greater_than_or_equal_to": time_greater_than_or_equal_to,
                "time_less_than_or_equal_to": time_less_than_or_equal_to,
            }
            if name:
                kwargs["name"] = name
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id

            response = client.summarize_awr_db_wait_event_buckets(**kwargs)

            items = []
            for bucket in response.data.items if hasattr(response.data, 'items') else [response.data]:
                items.append({
                    "name": bucket.name,
                    "category": getattr(bucket, "category", None),
                    "total_waits": getattr(bucket, "total_waits", None),
                    "total_time_waited": getattr(bucket, "total_time_waited", None),
                    "avg_wait_time": getattr(bucket, "avg_wait_time", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "time_range": {
                    "start": time_greater_than_or_equal_to,
                    "end": time_less_than_or_equal_to,
                },
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


def summarize_awr_db_sysstats(
    managed_database_id: str,
    time_greater_than_or_equal_to: str,
    time_less_than_or_equal_to: str,
    name: Optional[list[str]] = None,
    opc_named_credential_id: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Summarize AWR database system statistics.

    Provides system-level statistics like physical reads, logical reads,
    transactions, etc. from AWR snapshots.

    Args:
        managed_database_id: Managed database OCID
        time_greater_than_or_equal_to: Start time (ISO 8601)
        time_less_than_or_equal_to: End time (ISO 8601)
        name: Filter by specific sysstat names
        opc_named_credential_id: Named credential OCID for authentication
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with system statistics and trends
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
                "time_greater_than_or_equal_to": time_greater_than_or_equal_to,
                "time_less_than_or_equal_to": time_less_than_or_equal_to,
            }
            if name:
                kwargs["name"] = name
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id

            response = client.summarize_awr_db_sysstats(**kwargs)

            items = []
            for sysstat in response.data.items if hasattr(response.data, 'items') else [response.data]:
                items.append({
                    "name": sysstat.name,
                    "category": getattr(sysstat, "category", None),
                    "time_begin": str(sysstat.time_begin) if hasattr(sysstat, "time_begin") else None,
                    "time_end": str(sysstat.time_end) if hasattr(sysstat, "time_end") else None,
                    "avg_value": getattr(sysstat, "avg_value", None),
                    "current_value": getattr(sysstat, "current_value", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "time_range": {
                    "start": time_greater_than_or_equal_to,
                    "end": time_less_than_or_equal_to,
                },
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


def summarize_awr_db_parameter_changes(
    managed_database_id: str,
    time_greater_than_or_equal_to: str,
    time_less_than_or_equal_to: str,
    name: Optional[str] = None,
    opc_named_credential_id: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Summarize AWR database parameter changes over time.

    Tracks changes to database initialization parameters which can
    impact performance and behavior.

    Args:
        managed_database_id: Managed database OCID
        time_greater_than_or_equal_to: Start time (ISO 8601)
        time_less_than_or_equal_to: End time (ISO 8601)
        name: Filter by specific parameter name
        opc_named_credential_id: Named credential OCID for authentication
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with parameter change history
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
                "time_greater_than_or_equal_to": time_greater_than_or_equal_to,
                "time_less_than_or_equal_to": time_less_than_or_equal_to,
            }
            if name:
                kwargs["name"] = name
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id

            response = client.summarize_awr_db_parameter_changes(**kwargs)

            items = []
            for change in response.data.items if hasattr(response.data, 'items') else [response.data]:
                items.append({
                    "name": change.name,
                    "instance_number": getattr(change, "instance_number", None),
                    "begin_value": getattr(change, "begin_value", None),
                    "end_value": getattr(change, "end_value", None),
                    "time_begin": str(change.time_begin) if hasattr(change, "time_begin") else None,
                    "time_end": str(change.time_end) if hasattr(change, "time_end") else None,
                    "is_changed": getattr(change, "is_changed", None),
                    "value_modified": getattr(change, "value_modified", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "time_range": {
                    "start": time_greater_than_or_equal_to,
                    "end": time_less_than_or_equal_to,
                },
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
