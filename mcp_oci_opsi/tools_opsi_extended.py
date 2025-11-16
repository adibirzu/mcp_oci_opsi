"""Extended FastMCP tools for OCI Operations Insights - Host, SQL, and Capacity."""

from datetime import datetime
from typing import Any, Optional

from .oci_clients import get_opsi_client, list_all, extract_region_from_ocid, get_ocid_resource_type


def list_host_insights(
    compartment_id: str,
    lifecycle_state: Optional[str] = None,
    host_type: Optional[str] = None,
) -> dict[str, Any]:
    """
    List host insights in a compartment.

    Args:
        compartment_id: Compartment OCID to query.
        lifecycle_state: Filter by lifecycle state (e.g., "ACTIVE").
        host_type: Filter by host type.

    Returns:
        Dictionary containing list of host insights.
    """
    try:
        client = get_opsi_client()

        kwargs = {"compartment_id": compartment_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if host_type:
            kwargs["host_type"] = [host_type]

        host_insights = list_all(
            client.list_host_insights,
            **kwargs,
        )

        items = []
        for host in host_insights:
            items.append({
                "id": host.id,
                "host_name": getattr(host, "host_name", None),
                "host_display_name": getattr(host, "host_display_name", None),
                "host_type": getattr(host, "host_type", None),
                "platform_type": getattr(host, "platform_type", None),
                "processor_count": getattr(host, "processor_count", None),
                "status": host.status,
                "lifecycle_state": host.lifecycle_state,
                "time_created": str(host.time_created),
            })

        return {
            "compartment_id": compartment_id,
            "items": items,
            "count": len(items),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def summarize_sql_statistics(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    database_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Summarize SQL statistics for databases in a compartment.

    Provides aggregated SQL performance metrics including executions, CPU time,
    elapsed time, and other key performance indicators.

    IMPORTANT: Operations Insights is regional. If querying a specific database,
    this function automatically detects the database region and queries the correct
    regional endpoint.

    Args:
        compartment_id: Compartment OCID to query.
        time_interval_start: Start time in ISO format (e.g., "2024-01-01T00:00:00Z").
        time_interval_end: End time in ISO format (e.g., "2024-01-31T23:59:59Z").
        database_id: Optional database insight OCID to filter results.
                    Region will be automatically detected from this OCID.

    Returns:
        Dictionary containing SQL statistics summary.

    Note:
        If you get 404 errors, ensure:
        1. The database has Operations Insights enabled
        2. You have required IAM permissions for SQL statistics
        3. The database is in the expected region
    """
    try:
        # Validate OCID type if database_id provided
        if database_id:
            resource_type = get_ocid_resource_type(database_id)

            # Check if user provided wrong OCID type
            if resource_type and resource_type not in ["opsidatabaseinsight", "databaseinsight"]:
                return {
                    "error": f"Invalid OCID type: '{resource_type}'",
                    "provided_ocid": database_id,
                    "troubleshooting": {
                        "issue": f"You provided a '{resource_type}' OCID, but this function requires a 'database insight' OCID",
                        "explanation": [
                            "Operations Insights uses 'database insight' OCIDs, not database OCIDs",
                            "Database insight OCID format: ocid1.opsidatabaseinsight.oc1.<region>...",
                            f"You provided: ocid1.{resource_type}.oc1.<region>..."
                        ],
                        "solution": {
                            "method_1": "Use get_fleet_summary() or search_databases() to find the database insight OCID",
                            "method_2": "Use list_database_insights() to list all insights in your compartment",
                            "method_3": "In OCI Console: Operations Insights → Database Insights → Copy the Insight OCID (not Database OCID)"
                        },
                        "example": {
                            "wrong_ocid": "ocid1.autonomousdatabase.oc1.phx.xxx (Database OCID)",
                            "correct_ocid": "ocid1.opsidatabaseinsight.oc1.phx.yyy (Database Insight OCID)"
                        }
                    }
                }

        # Detect region from database_id if provided
        region = None
        if database_id:
            # Method 1: Extract from OCID
            region = extract_region_from_ocid(database_id)
            if region:
                print(f"Detected region from OCID: {region}")

            # Method 2: Lookup in cache if OCID extraction fails
            if not region:
                try:
                    from mcp_oci_opsi.cache import DatabaseCache
                    cache = DatabaseCache()
                    if cache.load() and cache.is_valid():
                        region = cache.get_database_region(database_id)
                        if region:
                            print(f"Detected region from cache: {region}")
                except Exception:
                    pass  # Cache lookup failed, continue without region

        # Create region-aware client
        client = get_opsi_client(region=region)

        # Convert time strings to datetime objects
        time_start = datetime.fromisoformat(time_interval_start.replace("Z", "+00:00"))
        time_end = datetime.fromisoformat(time_interval_end.replace("Z", "+00:00"))

        kwargs = {
            "compartment_id": compartment_id,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
        }

        if database_id:
            kwargs["database_id"] = [database_id]

        response = client.summarize_sql_statistics(
            **kwargs,
        )

        items = []
        if hasattr(response.data, "items"):
            for item in response.data.items:
                items.append({
                    "sql_identifier": getattr(item, "sql_identifier", None),
                    "database_id": getattr(item, "database_id", None),
                    "executions_count": getattr(item, "executions_count", None),
                    "cpu_time_in_sec": getattr(item, "cpu_time_in_sec", None),
                    "elapsed_time_in_sec": getattr(item, "elapsed_time_in_sec", None),
                    "buffer_gets": getattr(item, "buffer_gets", None),
                    "disk_reads": getattr(item, "disk_reads", None),
                    "direct_writes": getattr(item, "direct_writes", None),
                    "rows_processed": getattr(item, "rows_processed", None),
                })

        result = {
            "compartment_id": compartment_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "items": items,
            "count": len(items),
        }

        if region:
            result["detected_region"] = region

        return result

    except Exception as e:
        error_msg = str(e)
        error_result = {
            "error": error_msg,
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }

        # Add troubleshooting guidance for common errors
        if "NotAuthorizedOrNotFound" in error_msg or "404" in error_msg:
            error_result["troubleshooting"] = {
                "possible_causes": [
                    "Database does not have Operations Insights enabled",
                    "Missing IAM permissions for SQL statistics",
                    "Database insight ID is incorrect",
                    "Regional mismatch - database may be in different region"
                ],
                "required_permissions": [
                    "Allow group <YourGroup> to read sql-statistics in compartment",
                    "Allow group <YourGroup> to read opsi-data-objects in compartment"
                ],
                "next_steps": [
                    "Verify database has Operations Insights enabled",
                    "Check IAM policies in the database compartment",
                    "Confirm the database_id OCID is correct"
                ]
            }

            if database_id:
                detected_region = extract_region_from_ocid(database_id)
                if detected_region:
                    error_result["detected_database_region"] = detected_region

        return error_result


def get_sql_plan(
    compartment_id: str,
    sql_identifier: str,
    plan_hash: int,
    database_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get SQL execution plan details for a specific SQL identifier.

    Args:
        compartment_id: Compartment OCID.
        sql_identifier: SQL identifier to retrieve plan for.
        plan_hash: Plan hash value.
        database_id: Optional database OCID.

    Returns:
        Dictionary containing SQL plan details.
    """
    try:
        client = get_opsi_client()

        kwargs = {
            "compartment_id": compartment_id,
            "sql_identifier": sql_identifier,
            "plan_hash": plan_hash,
        }

        if database_id:
            kwargs["database_id"] = [database_id]

        response = client.get_sql_plan(
            **kwargs,
        )

        return {
            "compartment_id": compartment_id,
            "sql_identifier": sql_identifier,
            "plan_hash": plan_hash,
            "plan": str(response.data) if hasattr(response, "data") else None,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "sql_identifier": sql_identifier,
        }


def summarize_database_insight_resource_capacity_trend(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    database_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get capacity planning trends for database resource utilization.

    Provides historical trends and forecasts for resource capacity including
    CPU, memory, storage, and I/O metrics.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, STORAGE, MEMORY, IO).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        database_id: Optional database OCID filter.

    Returns:
        Dictionary containing capacity trend analysis.
    """
    try:
        client = get_opsi_client()

        # Convert time strings to datetime
        time_start = datetime.fromisoformat(time_interval_start.replace("Z", "+00:00"))
        time_end = datetime.fromisoformat(time_interval_end.replace("Z", "+00:00"))

        kwargs = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
        }

        if database_id:
            kwargs["database_id"] = [database_id]

        response = client.summarize_database_insight_resource_capacity_trend(
            **kwargs,
        )

        items = []
        if hasattr(response.data, "items"):
            for item in response.data.items:
                items.append({
                    "end_timestamp": str(getattr(item, "end_timestamp", None)),
                    "capacity": getattr(item, "capacity", None),
                    "usage": getattr(item, "usage", None),
                    "utilization_percent": getattr(item, "utilization_percent", None),
                })

        return {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "trend_items": items,
            "count": len(items),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def summarize_database_insight_resource_forecast(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    forecast_days: int = 30,
    database_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get resource utilization forecast for capacity planning.

    Provides ML-based forecasts for future resource utilization to help with
    capacity planning and resource allocation decisions.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, STORAGE, MEMORY, IO).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        forecast_days: Number of days to forecast (default 30).
        database_id: Optional database OCID filter.

    Returns:
        Dictionary containing resource forecast data.
    """
    try:
        client = get_opsi_client()

        # Convert time strings to datetime
        time_start = datetime.fromisoformat(time_interval_start.replace("Z", "+00:00"))
        time_end = datetime.fromisoformat(time_interval_end.replace("Z", "+00:00"))

        kwargs = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
            "forecast_days": forecast_days,
        }

        if database_id:
            kwargs["database_id"] = [database_id]

        response = client.summarize_database_insight_resource_forecast_trend(
            **kwargs,
        )

        forecast_items = []
        if hasattr(response.data, "items"):
            for item in response.data.items:
                forecast_items.append({
                    "end_timestamp": str(getattr(item, "end_timestamp", None)),
                    "usage": getattr(item, "usage", None),
                    "high_value": getattr(item, "high_value", None),
                    "low_value": getattr(item, "low_value", None),
                })

        return {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "forecast_days": forecast_days,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "forecast_items": forecast_items,
            "count": len(forecast_items),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def list_exadata_insights(
    compartment_id: str,
    lifecycle_state: Optional[str] = None,
) -> dict[str, Any]:
    """
    List Exadata insights in a compartment.

    Args:
        compartment_id: Compartment OCID to query.
        lifecycle_state: Filter by lifecycle state (e.g., "ACTIVE").

    Returns:
        Dictionary containing list of Exadata insights.
    """
    try:
        client = get_opsi_client()

        kwargs = {"compartment_id": compartment_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state

        exadata_insights = list_all(
            client.list_exadata_insights,
            **kwargs,
        )

        items = []
        for exadata in exadata_insights:
            items.append({
                "id": exadata.id,
                "exadata_name": getattr(exadata, "exadata_name", None),
                "exadata_display_name": getattr(exadata, "exadata_display_name", None),
                "exadata_type": getattr(exadata, "exadata_type", None),
                "status": exadata.status,
                "lifecycle_state": exadata.lifecycle_state,
                "time_created": str(exadata.time_created),
            })

        return {
            "compartment_id": compartment_id,
            "items": items,
            "count": len(items),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def summarize_host_insight_resource_statistics(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get resource statistics for host insights.

    Provides CPU, memory, and other resource utilization statistics for hosts.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, NETWORK, STORAGE).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing host resource statistics.
    """
    try:
        client = get_opsi_client()

        # Convert time strings to datetime
        time_start = datetime.fromisoformat(time_interval_start.replace("Z", "+00:00"))
        time_end = datetime.fromisoformat(time_interval_end.replace("Z", "+00:00"))

        kwargs = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
        }

        if host_id:
            kwargs["id"] = [host_id]

        response = client.summarize_host_insight_resource_statistics(
            **kwargs,
        )

        items = []
        if hasattr(response.data, "items"):
            for item in response.data.items:
                items.append({
                    "resource_name": getattr(item, "resource_name", None),
                    "usage": getattr(item, "usage", None),
                    "capacity": getattr(item, "capacity", None),
                    "utilization_percent": getattr(item, "utilization_percent", None),
                    "usage_change_percent": getattr(item, "usage_change_percent", None),
                })

        return {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "items": items,
            "count": len(items),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }
