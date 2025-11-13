"""Extended FastMCP tools for OCI Operations Insights - Host, SQL, and Capacity."""

from datetime import datetime
from typing import Any, Optional

from .oci_clients import get_opsi_client, list_all


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

    Args:
        compartment_id: Compartment OCID to query.
        time_interval_start: Start time in ISO format (e.g., "2024-01-01T00:00:00Z").
        time_interval_end: End time in ISO format (e.g., "2024-01-31T23:59:59Z").
        database_id: Optional database OCID to filter results.

    Returns:
        Dictionary containing SQL statistics summary.
    """
    try:
        client = get_opsi_client()

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

        return {
            "compartment_id": compartment_id,
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
