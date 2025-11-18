"""Extended FastMCP tools for OCI Operations Insights - Host, SQL, and Capacity."""

from datetime import datetime
from typing import Any, Optional
import oci

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


def _is_em_managed_database(database_insight_id: str, region: Optional[str] = None) -> bool:
    """
    Check if a database insight is EM-Managed External Database type.

    EM-Managed databases have limited API support for SQL Statistics and other APIs.

    Args:
        database_insight_id: Database insight OCID
        region: Optional region override

    Returns:
        True if EM-Managed, False otherwise
    """
    try:
        client = get_opsi_client(region=region)
        response = client.get_database_insight(database_insight_id)
        db_insight = response.data

        # Check if it's EM-Managed
        entity_source = getattr(db_insight, "entity_source", None)
        return entity_source == "EM_MANAGED_EXTERNAL_DATABASE"

    except Exception:
        # If we can't determine, assume it's not EM-Managed
        return False


def _query_sql_statistics_from_warehouse(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    database_id: Optional[str] = None,
    region: Optional[str] = None,
) -> dict[str, Any]:
    """
    Fallback method to get SQL statistics using warehouse queries.

    This is used when the direct API doesn't work (e.g., for EM-Managed databases).
    """
    from .tools_opsi import query_warehouse_standard

    # Build SQL query for warehouse
    # The warehouse has tables like database_sql_statistics with SQL performance data
    where_clauses = [
        f"time_collected >= TIMESTAMP '{time_interval_start.replace('Z', '').replace('T', ' ')}'"
    ]

    if database_id:
        where_clauses.append(f"database_id = '{database_id}'")

    where_clause = " AND ".join(where_clauses)

    # Query for SQL statistics
    sql_query = f"""
        SELECT
            sql_identifier,
            database_id,
            database_name,
            database_display_name,
            SUM(executions_count) as executions_count,
            AVG(executions_per_hour) as executions_per_hour,
            SUM(cpu_time_in_sec) as cpu_time_in_sec,
            SUM(io_time_in_sec) as io_time_in_sec,
            SUM(database_time_in_sec) as database_time_in_sec,
            AVG(database_time_pct) as database_time_pct,
            SUM(inefficient_wait_time_in_sec) as inefficient_wait_time_in_sec,
            AVG(response_time_in_sec) as response_time_in_sec,
            AVG(average_active_sessions) as average_active_sessions,
            MAX(plan_count) as plan_count
        FROM database_sql_statistics
        WHERE {where_clause}
        GROUP BY sql_identifier, database_id, database_name, database_display_name
        ORDER BY cpu_time_in_sec DESC
        FETCH FIRST 100 ROWS ONLY
    """

    try:
        warehouse_result = query_warehouse_standard(
            compartment_id=compartment_id,
            statement=sql_query,
            region=region
        )

        # Transform warehouse results to match API response format
        if "error" in warehouse_result:
            return warehouse_result

        items = []
        if "rows" in warehouse_result:
            columns = warehouse_result.get("columns", [])
            for row in warehouse_result["rows"]:
                # Create a dict from row values
                row_dict = {}
                for i, col in enumerate(columns):
                    if i < len(row):
                        row_dict[col] = row[i]

                items.append(row_dict)

        return {
            "compartment_id": compartment_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "items": items,
            "count": len(items),
            "data_source": "warehouse_query",
            "note": "Data retrieved via warehouse query (EM-Managed database fallback)"
        }

    except Exception as e:
        return {
            "error": f"Warehouse query fallback failed: {str(e)}",
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "troubleshooting": {
                "issue": "Both direct API and warehouse query failed for EM-Managed database",
                "possible_causes": [
                    "Operations Insights warehouse not enabled",
                    "Warehouse data not yet populated",
                    "Missing warehouse access permissions"
                ],
                "required_permissions": [
                    "Allow group <YourGroup> to use operations-insights-warehouse in compartment"
                ],
                "next_steps": [
                    "Enable Operations Insights warehouse in OCI Console",
                    "Wait 24-48 hours for warehouse data to populate",
                    "Check IAM policies for warehouse access"
                ]
            }
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
                # Get database details
                db_id = None
                db_name = None
                db_display_name = None
                if hasattr(item, "database_details") and item.database_details:
                    db_id = getattr(item.database_details, "id", None)
                    db_name = getattr(item.database_details, "database_name", None)
                    db_display_name = getattr(item.database_details, "database_display_name", None)

                # Get statistics - they are nested in item.statistics
                stats = {}
                if hasattr(item, "statistics") and item.statistics:
                    stats = {
                        "executions_count": getattr(item.statistics, "executions_count", None),
                        "executions_per_hour": getattr(item.statistics, "executions_per_hour", None),
                        "cpu_time_in_sec": getattr(item.statistics, "cpu_time_in_sec", None),
                        "io_time_in_sec": getattr(item.statistics, "io_time_in_sec", None),
                        "database_time_in_sec": getattr(item.statistics, "database_time_in_sec", None),
                        "database_time_pct": getattr(item.statistics, "database_time_pct", None),
                        "inefficient_wait_time_in_sec": getattr(item.statistics, "inefficient_wait_time_in_sec", None),
                        "response_time_in_sec": getattr(item.statistics, "response_time_in_sec", None),
                        "average_active_sessions": getattr(item.statistics, "average_active_sessions", None),
                        "plan_count": getattr(item.statistics, "plan_count", None),
                        "variability": getattr(item.statistics, "variability", None),
                    }

                items.append({
                    "sql_identifier": getattr(item, "sql_identifier", None),
                    "database_id": db_id,
                    "database_name": db_name,
                    "database_display_name": db_display_name,
                    "category": getattr(item, "category", None),
                    **stats  # Unpack statistics into the item dict
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

        # Check if it's a 404 error and if the database is EM-Managed
        is_404_error = "NotAuthorizedOrNotFound" in error_msg or "404" in error_msg

        if is_404_error and database_id:
            # Check if this is an EM-Managed database
            is_em_managed = _is_em_managed_database(database_id, region=region)

            if is_em_managed:
                # Try warehouse query fallback for EM-Managed databases
                print(f"Detected EM-Managed database. Attempting warehouse query fallback...")

                warehouse_result = _query_sql_statistics_from_warehouse(
                    compartment_id=compartment_id,
                    time_interval_start=time_interval_start,
                    time_interval_end=time_interval_end,
                    database_id=database_id,
                    region=region
                )

                # Add EM-Managed context to the result
                if "error" not in warehouse_result:
                    warehouse_result["em_managed_database"] = True
                    warehouse_result["note"] = (
                        "This is an EM-Managed External Database. "
                        "SQL Statistics API is not available for this database type. "
                        "Data retrieved via warehouse query instead."
                    )
                else:
                    # Warehouse fallback also failed, add EM-Managed specific guidance
                    warehouse_result["em_managed_database"] = True
                    warehouse_result["additional_info"] = {
                        "database_type": "EM_MANAGED_EXTERNAL_DATABASE",
                        "limitation": "SQL Statistics API is not supported for EM-Managed databases",
                        "alternatives": [
                            "Enable Operations Insights warehouse and wait for data population",
                            "Use Database Management Service Performance Hub APIs",
                            "Enable native OPSI agent on the database (requires reconfiguration)"
                        ]
                    }

                return warehouse_result

        # Standard error handling for non-EM-Managed databases
        error_result = {
            "error": error_msg,
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }

        # Add troubleshooting guidance for common errors
        if is_404_error:
            error_result["troubleshooting"] = {
                "possible_causes": [
                    "Database does not have Operations Insights enabled",
                    "Database is EM-Managed External Database (limited API support)",
                    "Missing IAM permissions for SQL statistics",
                    "Database insight ID is incorrect",
                    "Regional mismatch - database may be in different region"
                ],
                "required_permissions": [
                    "Allow group <YourGroup> to read sql-statistics in compartment",
                    "Allow group <YourGroup> to read opsi-data-objects in compartment"
                ],
                "next_steps": [
                    "Run diagnose_permissions.py to identify the root cause",
                    "Check if database is EM-Managed type (limited API support)",
                    "Verify database has Operations Insights enabled",
                    "Check IAM policies in the database compartment",
                    "Consider enabling warehouse queries for EM-Managed databases"
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


def summarize_host_insight_resource_forecast_trend(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    forecast_days: int = 30,
    host_id: Optional[str] = None,
    statistic: Optional[str] = "AVG",
) -> dict[str, Any]:
    """
    Get ML-based resource utilization forecast for host capacity planning.

    Provides forecasts for future resource utilization to help with capacity
    planning and resource allocation decisions. This matches the OCI Console
    forecast functionality.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, NETWORK, STORAGE, LOGICAL_MEMORY).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        forecast_days: Number of days to forecast (default 30).
        host_id: Optional host insight OCID filter.
        statistic: Statistic type (AVG, MAX, MIN). Default AVG.

    Returns:
        Dictionary containing resource forecast data with trend analysis.
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

        if host_id:
            kwargs["id"] = [host_id]

        if statistic:
            kwargs["statistic"] = statistic

        response = client.summarize_host_insight_resource_forecast_trend(
            **kwargs,
        )

        forecast_items = []
        if hasattr(response.data, "usage_data") and response.data.usage_data:
            for item in response.data.usage_data:
                forecast_items.append({
                    "end_timestamp": str(getattr(item, "end_timestamp", None)),
                    "usage": getattr(item, "usage", None),
                    "high_value": getattr(item, "high_value", None),
                    "low_value": getattr(item, "low_value", None),
                })

        result = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "forecast_days": forecast_days,
            "statistic": statistic,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "forecast_items": forecast_items,
            "count": len(forecast_items),
        }

        # Add summary data if available
        if hasattr(response.data, "time_interval_start"):
            result["response_time_start"] = str(response.data.time_interval_start)
        if hasattr(response.data, "time_interval_end"):
            result["response_time_end"] = str(response.data.time_interval_end)
        if hasattr(response.data, "item_duration_in_ms"):
            result["item_duration_in_ms"] = response.data.item_duration_in_ms
        if hasattr(response.data, "usage_unit"):
            result["usage_unit"] = response.data.usage_unit

        return result

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
        }


def summarize_host_insight_resource_capacity_trend(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
    utilization_level: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get capacity planning trends for host resource utilization.

    Provides historical trends for resource capacity including CPU, memory,
    storage, and network metrics.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, NETWORK, STORAGE).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.
        utilization_level: Filter by utilization level (HIGH_UTILIZATION, LOW_UTILIZATION).

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

        if host_id:
            kwargs["id"] = [host_id]

        if utilization_level:
            kwargs["utilization_level"] = utilization_level

        response = client.summarize_host_insight_resource_capacity_trend(
            **kwargs,
        )

        trend_items = []
        if hasattr(response.data, "usage_data") and response.data.usage_data:
            for item in response.data.usage_data:
                trend_items.append({
                    "end_timestamp": str(getattr(item, "end_timestamp", None)),
                    "capacity": getattr(item, "capacity", None),
                    "usage": getattr(item, "usage", None),
                    "utilization_percent": getattr(item, "utilization_percent", None),
                })

        result = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "trend_items": trend_items,
            "count": len(trend_items),
        }

        if hasattr(response.data, "usage_unit"):
            result["usage_unit"] = response.data.usage_unit
        if hasattr(response.data, "item_duration_in_ms"):
            result["item_duration_in_ms"] = response.data.item_duration_in_ms

        return result

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def summarize_host_insight_resource_usage(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get current resource usage summary for hosts.

    Provides aggregated resource usage data for capacity planning and monitoring.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, NETWORK, STORAGE).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing resource usage summary.
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

        response = client.summarize_host_insight_resource_usage(
            **kwargs,
        )

        items = []
        if hasattr(response.data, "items") and response.data.items:
            for item in response.data.items:
                items.append({
                    "host_id": getattr(item, "id", None),
                    "host_name": getattr(item, "host_name", None),
                    "platform_type": getattr(item, "platform_type", None),
                    "usage": getattr(item, "usage", None),
                    "capacity": getattr(item, "capacity", None),
                    "utilization_percent": getattr(item, "utilization_percent", None),
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


def summarize_host_insight_resource_usage_trend(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get resource usage trends over time for hosts.

    Provides time-series data for resource usage to identify trends and patterns.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, NETWORK, STORAGE).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing resource usage trend data.
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

        response = client.summarize_host_insight_resource_usage_trend(
            **kwargs,
        )

        usage_data = []
        if hasattr(response.data, "usage_data") and response.data.usage_data:
            for item in response.data.usage_data:
                usage_data.append({
                    "end_timestamp": str(getattr(item, "end_timestamp", None)),
                    "usage": getattr(item, "usage", None),
                    "capacity": getattr(item, "capacity", None),
                })

        result = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "usage_data": usage_data,
            "count": len(usage_data),
        }

        if hasattr(response.data, "usage_unit"):
            result["usage_unit"] = response.data.usage_unit
        if hasattr(response.data, "item_duration_in_ms"):
            result["item_duration_in_ms"] = response.data.item_duration_in_ms

        return result

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def summarize_host_insight_resource_utilization_insight(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
    forecast_days: int = 30,
) -> dict[str, Any]:
    """
    Get resource utilization insights with projections and recommendations.

    Provides comprehensive insights including current utilization, projections,
    and capacity recommendations for hosts.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, NETWORK, STORAGE).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.
        forecast_days: Number of days to forecast (default 30).

    Returns:
        Dictionary containing utilization insights and recommendations.
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

        if host_id:
            kwargs["id"] = [host_id]

        response = client.summarize_host_insight_resource_utilization_insight(
            **kwargs,
        )

        items = []
        if hasattr(response.data, "items") and response.data.items:
            for item in response.data.items:
                items.append({
                    "host_id": getattr(item, "id", None),
                    "host_name": getattr(item, "host_name", None),
                    "current_utilization": getattr(item, "current_utilization", None),
                    "projected_utilization": getattr(item, "projected_utilization", None),
                    "days_to_reach_capacity": getattr(item, "days_to_reach_capacity", None),
                })

        return {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "forecast_days": forecast_days,
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

def summarize_host_insight_disk_statistics(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get disk I/O statistics for hosts.

    Provides detailed disk I/O metrics including read/write operations,
    throughput, and latency statistics.

    Args:
        compartment_id: Compartment OCID.
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing disk statistics.
    """
    try:
        client = get_opsi_client()

        # Convert time strings to datetime
        time_start = datetime.fromisoformat(time_interval_start.replace("Z", "+00:00"))
        time_end = datetime.fromisoformat(time_interval_end.replace("Z", "+00:00"))

        kwargs = {
            "compartment_id": compartment_id,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
        }

        if host_id:
            kwargs["id"] = [host_id]

        response = client.summarize_host_insight_disk_statistics(
            **kwargs,
        )

        items = []
        if hasattr(response.data, "items") and response.data.items:
            for item in response.data.items:
                items.append({
                    "disk_name": getattr(item, "disk_name", None),
                    "disk_read_in_mbs": getattr(item, "disk_read_in_mbs", None),
                    "disk_write_in_mbs": getattr(item, "disk_write_in_mbs", None),
                    "disk_iops": getattr(item, "disk_iops", None),
                    "disk_io_time_in_sec": getattr(item, "disk_io_time_in_sec", None),
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


def summarize_host_insight_io_usage_trend(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get I/O usage trends over time for hosts.

    Provides time-series data for I/O operations including reads, writes,
    and IOPS metrics.

    Args:
        compartment_id: Compartment OCID.
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing I/O usage trend data.
    """
    try:
        client = get_opsi_client()

        # Convert time strings to datetime
        time_start = datetime.fromisoformat(time_interval_start.replace("Z", "+00:00"))
        time_end = datetime.fromisoformat(time_interval_end.replace("Z", "+00:00"))

        kwargs = {
            "compartment_id": compartment_id,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
        }

        if host_id:
            kwargs["id"] = [host_id]

        response = client.summarize_host_insight_io_usage_trend(
            **kwargs,
        )

        usage_data = []
        if hasattr(response.data, "usage_data") and response.data.usage_data:
            for item in response.data.usage_data:
                usage_data.append({
                    "end_timestamp": str(getattr(item, "end_timestamp", None)),
                    "disk_read_in_mbs": getattr(item, "disk_read_in_mbs", None),
                    "disk_write_in_mbs": getattr(item, "disk_write_in_mbs", None),
                    "disk_iops": getattr(item, "disk_iops", None),
                })

        return {
            "compartment_id": compartment_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "usage_data": usage_data,
            "count": len(usage_data),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def summarize_host_insight_network_usage_trend(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get network usage trends over time for hosts.

    Provides time-series data for network metrics including throughput,
    packet counts, and errors.

    Args:
        compartment_id: Compartment OCID.
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing network usage trend data.
    """
    try:
        client = get_opsi_client()

        # Convert time strings to datetime
        time_start = datetime.fromisoformat(time_interval_start.replace("Z", "+00:00"))
        time_end = datetime.fromisoformat(time_interval_end.replace("Z", "+00:00"))

        kwargs = {
            "compartment_id": compartment_id,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
        }

        if host_id:
            kwargs["id"] = [host_id]

        response = client.summarize_host_insight_network_usage_trend(
            **kwargs,
        )

        usage_data = []
        if hasattr(response.data, "usage_data") and response.data.usage_data:
            for item in response.data.usage_data:
                usage_data.append({
                    "end_timestamp": str(getattr(item, "end_timestamp", None)),
                    "network_read_in_mbs": getattr(item, "network_read_in_mbs", None),
                    "network_write_in_mbs": getattr(item, "network_write_in_mbs", None),
                })

        return {
            "compartment_id": compartment_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "usage_data": usage_data,
            "count": len(usage_data),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def summarize_host_insight_storage_usage_trend(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get storage usage trends over time for hosts.

    Provides time-series data for storage utilization including filesystem
    usage and capacity metrics.

    Args:
        compartment_id: Compartment OCID.
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing storage usage trend data.
    """
    try:
        client = get_opsi_client()

        # Convert time strings to datetime
        time_start = datetime.fromisoformat(time_interval_start.replace("Z", "+00:00"))
        time_end = datetime.fromisoformat(time_interval_end.replace("Z", "+00:00"))

        kwargs = {
            "compartment_id": compartment_id,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
        }

        if host_id:
            kwargs["id"] = [host_id]

        response = client.summarize_host_insight_storage_usage_trend(
            **kwargs,
        )

        usage_data = []
        if hasattr(response.data, "usage_data") and response.data.usage_data:
            for item in response.data.usage_data:
                usage_data.append({
                    "end_timestamp": str(getattr(item, "end_timestamp", None)),
                    "filesystem_usage": getattr(item, "filesystem_usage", None),
                    "filesystem_capacity": getattr(item, "filesystem_capacity", None),
                    "filesystem_utilization_percent": getattr(item, "filesystem_utilization_percent", None),
                })

        return {
            "compartment_id": compartment_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "usage_data": usage_data,
            "count": len(usage_data),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def summarize_host_insight_top_processes_usage(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Get top resource-consuming processes on hosts.

    Identifies the top processes consuming CPU, memory, or other resources
    to help with performance troubleshooting.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.
        limit: Maximum number of top processes to return (default 10).

    Returns:
        Dictionary containing top processes data.
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
            "limit": limit,
        }

        if host_id:
            kwargs["id"] = [host_id]

        response = client.summarize_host_insight_top_processes_usage(
            **kwargs,
        )

        items = []
        if hasattr(response.data, "items") and response.data.items:
            for item in response.data.items:
                items.append({
                    "process_name": getattr(item, "process_name", None),
                    "process_command": getattr(item, "process_command", None),
                    "process_id": getattr(item, "process_id", None),
                    "cpu_usage": getattr(item, "cpu_usage", None),
                    "memory_usage": getattr(item, "memory_usage", None),
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


def summarize_host_insight_top_processes_usage_trend(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get trends for top resource-consuming processes over time.

    Provides time-series data for top processes to identify patterns and
    resource consumption changes.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing top processes trend data.
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

        response = client.summarize_host_insight_top_processes_usage_trend(
            **kwargs,
        )

        usage_data = []
        if hasattr(response.data, "usage_data") and response.data.usage_data:
            for item in response.data.usage_data:
                usage_data.append({
                    "end_timestamp": str(getattr(item, "end_timestamp", None)),
                    "process_name": getattr(item, "process_name", None),
                    "cpu_usage": getattr(item, "cpu_usage", None),
                    "memory_usage": getattr(item, "memory_usage", None),
                })

        return {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "usage_data": usage_data,
            "count": len(usage_data),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def summarize_host_insight_host_recommendation(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get AI-driven host configuration recommendations.

    Provides intelligent recommendations for host sizing, resource allocation,
    and optimization based on usage patterns and trends.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, STORAGE).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing host recommendations.
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

        response = client.summarize_host_insight_host_recommendation(
            **kwargs,
        )

        items = []
        if hasattr(response.data, "items") and response.data.items:
            for item in response.data.items:
                items.append({
                    "host_id": getattr(item, "id", None),
                    "host_name": getattr(item, "host_name", None),
                    "recommendation_type": getattr(item, "recommendation_type", None),
                    "recommendation_details": getattr(item, "recommendation_details", None),
                    "estimated_savings": getattr(item, "estimated_savings", None),
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
