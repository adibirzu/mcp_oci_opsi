"""Main entrypoint for the MCP OCI OPSI server."""

import os
from typing import Optional

import oci
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .config import get_oci_config, list_available_profiles, get_current_profile
from .oci_clients import get_opsi_client, list_all
from . import tools_opsi
from . import tools_opsi_extended
from . import tools_sqlwatch
from . import tools_dbmanagement
from . import tools_dbmanagement_monitoring
from . import tools_database_registration
from . import tools_oracle_database
from . import tools_cache
from . import tools_visualization

# Initialize FastMCP application
app = FastMCP("oci-opsi")


# ============================================================================
# Pydantic Input Models
# ============================================================================


class ListDatabaseInsightsInput(BaseModel):
    """Input model for listing database insights."""
    compartment_id: str = Field(..., description="Compartment OCID to query")
    lifecycle_state: Optional[str] = Field(None, description="Filter by lifecycle state")
    page: Optional[str] = Field(None, description="Page token for pagination")
    limit: Optional[int] = Field(None, description="Maximum items per page")


class QueryWarehouseInput(BaseModel):
    """Input model for warehouse queries."""
    compartment_id: str = Field(..., description="Compartment OCID for query scope")
    statement: str = Field(..., description="SQL query statement")


class ListSQLTextsInput(BaseModel):
    """Input model for listing SQL texts."""
    compartment_id: str = Field(..., description="Compartment OCID to query")
    time_start: str = Field(..., description="Start time in ISO format")
    time_end: str = Field(..., description="End time in ISO format")
    database_id: Optional[str] = Field(None, description="Optional database OCID filter")
    sql_identifier: Optional[str] = Field(None, description="Optional SQL identifier")


class DatabaseIdInput(BaseModel):
    """Input model for database ID operations."""
    database_id: str = Field(..., description="Managed Database OCID")


class WorkRequestInput(BaseModel):
    """Input model for work request operations."""
    work_request_id: str = Field(..., description="Work Request OCID")


class CompartmentIdInput(BaseModel):
    """Input model for compartment operations."""
    compartment_id: Optional[str] = Field(None, description="Compartment OCID (optional)")


class SummarizeDatabaseInsightsInput(BaseModel):
    """Input model for database insights summary."""
    compartment_id: str = Field(..., description="Compartment OCID")
    database_insight_id: str = Field(..., description="Database Insight OCID")
    time_interval_start: str = Field(..., description="Start time in ISO format")
    time_interval_end: str = Field(..., description="End time in ISO format")


# ============================================================================
# Utility Tools
# ============================================================================


@app.tool()
def ping() -> dict:
    """
    Simple ping tool to verify the MCP server is responsive.

    Returns:
        Dictionary with status and message.
    """
    return {
        "status": "ok",
        "message": "OCI OPSI MCP server is running",
        "server": "oci-opsi",
    }


@app.tool()
def whoami() -> dict:
    """
    Get the current OCI user and tenancy information from configuration.

    Returns:
        Dictionary containing tenancy OCID, user OCID, region, and profile.
    """
    try:
        config = get_oci_config()
        return {
            "tenancy_ocid": config.get("tenancy"),
            "user_ocid": config.get("user"),
            "region": config.get("region"),
            "profile": get_current_profile(),
            "fingerprint": config.get("fingerprint"),
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


@app.tool()
def list_oci_profiles() -> dict:
    """
    List all available OCI CLI profiles from ~/.oci/config file.

    This helps identify which credentials are available for use.
    To use a specific profile, set the OCI_CLI_PROFILE environment variable.

    Returns:
        Dictionary containing list of available profiles and current active profile.
    """
    try:
        profiles = list_available_profiles()
        current = get_current_profile()
        return {
            "available_profiles": profiles,
            "current_profile": current,
            "profile_count": len(profiles),
            "note": "To switch profiles, set OCI_CLI_PROFILE environment variable and restart the MCP server",
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


@app.tool()
def get_profile_info(profile_name: Optional[str] = None) -> dict:
    """
    Get detailed information about a specific OCI profile.

    Args:
        profile_name: Profile name to query. If not provided, uses current active profile.

    Returns:
        Dictionary containing profile configuration details (excluding sensitive data).
    """
    try:
        # Save current profile
        original_profile = os.getenv("OCI_CLI_PROFILE")

        # Temporarily set the requested profile
        if profile_name:
            os.environ["OCI_CLI_PROFILE"] = profile_name

        try:
            config = get_oci_config()
            result = {
                "profile_name": profile_name or get_current_profile(),
                "tenancy_ocid": config.get("tenancy"),
                "user_ocid": config.get("user"),
                "region": config.get("region"),
                "fingerprint": config.get("fingerprint"),
                "key_file": config.get("key_file"),
            }
        finally:
            # Restore original profile
            if original_profile:
                os.environ["OCI_CLI_PROFILE"] = original_profile
            elif "OCI_CLI_PROFILE" in os.environ:
                del os.environ["OCI_CLI_PROFILE"]

        return result
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "profile_name": profile_name,
        }


# ============================================================================
# Fast Cache Tools - Instant Responses, No API Calls
# ============================================================================


@app.tool()
def build_database_cache(compartment_ids: list[str]) -> dict:
    """
    Build local cache of all databases across compartments and their children.

    This scans the entire compartment hierarchy recursively and stores results
    in ~/.mcp_oci_opsi_cache.json for instant retrieval.

    FIRST-TIME SETUP: Run this once to build the cache, then use fast cache tools.

    Args:
        compartment_ids: List of root compartment OCIDs to scan recursively

    Returns:
        Dictionary with build status and statistics
    """
    return tools_cache.build_database_cache(compartment_ids)


@app.tool()
def get_fleet_summary() -> dict:
    """
    Get concise fleet summary - INSTANT, NO API CALLS, MINIMAL TOKENS.

    Ultra-fast overview of entire database fleet from local cache.
    Perfect for quick questions about fleet size and distribution.

    Returns:
        Dictionary with fleet statistics (databases, hosts, by compartment, by type)
    """
    return tools_cache.get_fleet_summary()


@app.tool()
def search_databases(name: Optional[str] = None, compartment: Optional[str] = None, limit: int = 20) -> dict:
    """
    Search databases in cache - INSTANT, NO API CALLS.

    Ultra-fast database search using local cache with partial matching.

    Args:
        name: Database name filter (partial, case-insensitive)
        compartment: Compartment name filter (partial, case-insensitive)
        limit: Maximum results to return (default 20)

    Returns:
        Dictionary with matching databases
    """
    return tools_cache.search_cached_databases(name=name, compartment=compartment, limit=limit)


@app.tool()
def get_databases_by_compartment(compartment_name: str) -> dict:
    """
    Get all databases in a compartment - INSTANT, NO API CALLS.

    Token-efficient response with essential database info grouped by compartment.

    Args:
        compartment_name: Compartment name (partial match, case-insensitive)

    Returns:
        Dictionary with databases grouped by compartment
    """
    return tools_cache.get_databases_by_compartment(compartment_name)


@app.tool()
def get_cached_statistics() -> dict:
    """
    Get detailed cache statistics - INSTANT, NO API CALLS.

    Returns comprehensive statistics about cached databases including
    counts by type, compartment, and status.

    Returns:
        Dictionary with detailed statistics and cache metadata
    """
    return tools_cache.get_cached_statistics()


@app.tool()
def list_cached_compartments() -> dict:
    """
    List all compartments in cache - INSTANT, NO API CALLS.

    Returns:
        Dictionary with all cached compartments
    """
    return tools_cache.list_cached_compartments()


@app.tool()
def refresh_cache_if_needed(max_age_hours: int = 24) -> dict:
    """
    Check cache age and determine if refresh is needed.

    Args:
        max_age_hours: Maximum cache age in hours before refresh (default 24)

    Returns:
        Dictionary with cache validity status and refresh recommendation
    """
    return tools_cache.refresh_cache_if_needed(max_age_hours)


# ============================================================================
# Operations Insights Tools
# ============================================================================


@app.tool()
def list_database_insights(
    compartment_id: str,
    lifecycle_state: Optional[str] = None,
    page: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """
    List database insights in a compartment with optional filtering.

    Args:
        compartment_id: Compartment OCID to query.
        lifecycle_state: Filter by lifecycle state (e.g., "ACTIVE", "DELETED").
        page: Page token for pagination (from previous response).
        limit: Maximum number of items to return per page.

    Returns:
        Dictionary containing database insights list and pagination info.
    """
    return tools_opsi.list_database_insights(compartment_id, lifecycle_state, page, limit)


@app.tool()
def query_warehouse_standard(
    compartment_id: str,
    statement: str,
) -> dict:
    """
    Execute a standard SQL query against the Operations Insights warehouse.

    This tool allows querying OPSI data warehouse using SQL-like syntax to analyze
    database performance metrics, resource utilization, and SQL statistics.

    Args:
        compartment_id: Compartment OCID for the query scope.
        statement: SQL query statement to execute against the warehouse.

    Returns:
        Dictionary containing query results with columns and rows.
    """
    return tools_opsi.query_warehouse_standard(compartment_id, statement)


@app.tool()
def list_sql_texts(
    compartment_id: str,
    time_start: str,
    time_end: str,
    database_id: Optional[str] = None,
    sql_identifier: Optional[str] = None,
) -> dict:
    """
    List SQL texts from Operations Insights for analysis.

    Retrieves SQL text data for database SQL statements within a time range,
    useful for SQL performance analysis and tuning.

    Args:
        compartment_id: Compartment OCID to query.
        time_start: Start time in ISO format (e.g., "2024-01-01T00:00:00Z").
        time_end: End time in ISO format (e.g., "2024-01-31T23:59:59Z").
        database_id: Optional database OCID to filter results.
        sql_identifier: Optional SQL identifier to retrieve specific SQL text.

    Returns:
        Dictionary containing SQL text data with statistics.
    """
    return tools_opsi.list_sql_texts(compartment_id, time_start, time_end, database_id, sql_identifier)


@app.tool()
def get_operations_insights_summary(compartment_id: str) -> dict:
    """
    Get Operations Insights summary for a compartment.

    Args:
        compartment_id: Compartment OCID to query.

    Returns:
        Dictionary containing Operations Insights summary data.
    """
    try:
        opsi_client = get_opsi_client()

        # List all database insights with pagination
        db_insights = list_all(
            opsi_client.list_database_insights,
            compartment_id=compartment_id,
        )

        result = {
            "compartment_id": compartment_id,
            "database_insights": [],
        }

        for db_insight in db_insights:
            result["database_insights"].append({
                "id": db_insight.id,
                "database_id": db_insight.database_id,
                "database_name": db_insight.database_name,
                "database_type": db_insight.database_type,
                "status": db_insight.status,
                "lifecycle_state": db_insight.lifecycle_state,
                "time_created": str(db_insight.time_created),
            })

        result["database_insights_count"] = len(result["database_insights"])

        return result
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


@app.tool()
def summarize_database_insights(
    compartment_id: str,
    database_insight_id: str,
    time_interval_start: str,
    time_interval_end: str,
) -> dict:
    """
    Summarize database insights metrics for a specific database.

    Args:
        compartment_id: Compartment OCID.
        database_insight_id: Database Insight OCID.
        time_interval_start: Start time in ISO format (e.g., "2024-01-01T00:00:00Z").
        time_interval_end: End time in ISO format (e.g., "2024-01-31T23:59:59Z").

    Returns:
        Dictionary containing database insight metrics summary.
    """
    try:
        opsi_client = get_opsi_client()

        # Get resource statistics
        response = opsi_client.summarize_database_insight_resource_statistics(
            compartment_id=compartment_id,
            resource_metric="CPU",
            database_id=[database_insight_id],
            time_interval_start=time_interval_start,
            time_interval_end=time_interval_end,
        )

        return {
            "database_insight_id": database_insight_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "resource_metric": "CPU",
            "items": [
                {
                    "resource_name": item.resource_name,
                    "usage": item.usage,
                    "capacity": item.capacity,
                    "utilization_percent": item.utilization_percent,
                }
                for item in response.data.items
            ],
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


# ============================================================================
# SQL Watch Tools
# ============================================================================


@app.tool()
def get_sqlwatch_status(database_id: str) -> dict:
    """
    Get SQL Watch status for a managed database.

    Retrieves the Database Management feature status to check if SQL Watch
    is enabled for the specified managed database.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing SQL Watch status and managed database details.
    """
    return tools_sqlwatch.get_status(database_id)


@app.tool()
def enable_sqlwatch(database_id: str) -> dict:
    """
    Enable SQL Watch on a managed database.

    Submits a request to enable the SQL Watch feature for the specified
    managed database. This operation may be asynchronous and return a
    work request OCID for tracking.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing operation status and work request OCID if applicable.
    """
    return tools_sqlwatch.enable_on_db(database_id)


@app.tool()
def disable_sqlwatch(database_id: str) -> dict:
    """
    Disable SQL Watch on a managed database.

    Submits a request to disable the SQL Watch feature for the specified
    managed database. This operation may be asynchronous and return a
    work request OCID for tracking.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing operation status and work request OCID if applicable.
    """
    return tools_sqlwatch.disable_on_db(database_id)


@app.tool()
def get_sqlwatch_work_request(work_request_id: str) -> dict:
    """
    Get the status of a Database Management work request.

    Retrieves the current status of a work request created by SQL Watch
    enable/disable operations.

    Args:
        work_request_id: Work Request OCID.

    Returns:
        Dictionary containing work request status and progress.
    """
    return tools_sqlwatch.get_work_request_status(work_request_id)


# ============================================================================
# Identity/Compartment Tools
# ============================================================================


@app.tool()
def list_compartments(compartment_id: Optional[str] = None) -> dict:
    """
    List all compartments in OCI tenancy.

    Args:
        compartment_id: Optional compartment OCID. If not provided, uses tenancy root.

    Returns:
        Dictionary containing list of compartments with their details.
    """
    try:
        config = get_oci_config()
        identity_client = oci.identity.IdentityClient(config)

        # Use provided compartment_id or tenancy root
        target_compartment = compartment_id or config["tenancy"]

        compartments = identity_client.list_compartments(
            compartment_id=target_compartment,
            compartment_id_in_subtree=True,
        )

        result = []
        for compartment in compartments.data:
            result.append({
                "id": compartment.id,
                "name": compartment.name,
                "description": compartment.description,
                "lifecycle_state": compartment.lifecycle_state,
                "time_created": str(compartment.time_created),
            })

        return {
            "compartments": result,
            "count": len(result),
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


# ============================================================================
# Extended Operations Insights Tools
# ============================================================================


@app.tool()
def list_host_insights(
    compartment_id: str,
    lifecycle_state: Optional[str] = None,
    host_type: Optional[str] = None,
) -> dict:
    """
    List host insights in a compartment.

    Args:
        compartment_id: Compartment OCID to query.
        lifecycle_state: Filter by lifecycle state (e.g., "ACTIVE").
        host_type: Filter by host type.

    Returns:
        Dictionary containing list of host insights.
    """
    return tools_opsi_extended.list_host_insights(compartment_id, lifecycle_state, host_type)


@app.tool()
def summarize_sql_statistics(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    database_id: Optional[str] = None,
) -> dict:
    """
    Summarize SQL statistics for databases in a compartment.

    Provides aggregated SQL performance metrics including executions, CPU time,
    elapsed time, and other key performance indicators.

    Args:
        compartment_id: Compartment OCID to query.
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        database_id: Optional database OCID to filter results.

    Returns:
        Dictionary containing SQL statistics summary.
    """
    return tools_opsi_extended.summarize_sql_statistics(
        compartment_id, time_interval_start, time_interval_end, database_id
    )


@app.tool()
def get_database_capacity_trend(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    database_id: Optional[str] = None,
) -> dict:
    """
    Get capacity planning trends for database resource utilization.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, STORAGE, MEMORY, IO).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        database_id: Optional database OCID filter.

    Returns:
        Dictionary containing capacity trend analysis.
    """
    return tools_opsi_extended.summarize_database_insight_resource_capacity_trend(
        compartment_id, resource_metric, time_interval_start, time_interval_end, database_id
    )


@app.tool()
def get_database_resource_forecast(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    forecast_days: int = 30,
    database_id: Optional[str] = None,
) -> dict:
    """
    Get ML-based resource utilization forecast for capacity planning.

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
    return tools_opsi_extended.summarize_database_insight_resource_forecast(
        compartment_id, resource_metric, time_interval_start, time_interval_end, forecast_days, database_id
    )


@app.tool()
def get_capacity_trend_with_chart(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    database_id: Optional[str] = None,
    database_name: Optional[str] = "Database",
) -> dict:
    """
    Get capacity trend WITH ASCII chart visualization and OCI Console link.

    Enhanced version that returns capacity trend data along with an ASCII line
    chart visualization for easy viewing in text format, plus a direct link
    to the OCI Console for graphical charts.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, STORAGE, MEMORY, IO).
        time_interval_start: Start time in ISO format (e.g., "2024-01-01T00:00:00Z").
        time_interval_end: End time in ISO format (e.g., "2024-01-31T23:59:59Z").
        database_id: Optional database OCID filter.
        database_name: Optional database name for chart title.

    Returns:
        Dictionary with trend data, ASCII chart, statistics, and OCI Console URL.

    Example:
        get_capacity_trend_with_chart(
            "ocid1.compartment...",
            "CPU",
            "2024-01-01T00:00:00Z",
            "2024-01-31T23:59:59Z"
        )
    """
    return tools_visualization.get_capacity_trend_with_visualization(
        compartment_id, resource_metric, time_interval_start, time_interval_end,
        database_id, database_name
    )


@app.tool()
def get_resource_forecast_with_chart(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    forecast_days: int = 30,
    database_id: Optional[str] = None,
    database_name: Optional[str] = "Database",
) -> dict:
    """
    Get ML-based resource forecast WITH ASCII chart and OCI Console link.

    Enhanced forecasting tool that combines historical data and ML predictions
    in a single ASCII chart visualization, similar to OCI Console forecast view.
    Includes capacity planning recommendations.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, STORAGE, MEMORY, IO).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        forecast_days: Number of days to forecast (default 30).
        database_id: Optional database OCID filter.
        database_name: Optional database name for chart title.

    Returns:
        Dictionary with historical + forecast data, combined ASCII chart,
        recommendations, and OCI Console URL.

    Example:
        get_resource_forecast_with_chart(
            "ocid1.compartment...",
            "CPU",
            "2024-01-01T00:00:00Z",
            "2024-01-31T23:59:59Z",
            forecast_days=30
        )
    """
    return tools_visualization.get_resource_forecast_with_visualization(
        compartment_id, resource_metric, time_interval_start, time_interval_end,
        forecast_days, database_id, database_name
    )


@app.tool()
def get_exadata_rack_visualization(
    exadata_insight_id: str,
    compartment_id: str,
) -> dict:
    """
    Get Exadata system rack visualization and topology.

    Provides a text-based visualization of the Exadata rack configuration
    showing compute servers, storage servers, and databases, similar to
    the OCI Console rack view. Includes a link to the graphical console view.

    Args:
        exadata_insight_id: Exadata Insight OCID.
        compartment_id: Compartment OCID.

    Returns:
        Dictionary with rack visualization, system details, database list,
        and OCI Console URL for graphical rack view.

    Example:
        get_exadata_rack_visualization(
            "ocid1.exadatainsight...",
            "ocid1.compartment..."
        )
    """
    return tools_visualization.get_exadata_system_visualization(
        exadata_insight_id, compartment_id
    )


@app.tool()
def list_exadata_insights(
    compartment_id: str,
    lifecycle_state: Optional[str] = None,
) -> dict:
    """
    List Exadata insights in a compartment.

    Args:
        compartment_id: Compartment OCID to query.
        lifecycle_state: Filter by lifecycle state.

    Returns:
        Dictionary containing list of Exadata insights.
    """
    return tools_opsi_extended.list_exadata_insights(compartment_id, lifecycle_state)


@app.tool()
def get_host_resource_statistics(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict:
    """
    Get resource statistics for host insights.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, NETWORK, STORAGE).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing host resource statistics.
    """
    return tools_opsi_extended.summarize_host_insight_resource_statistics(
        compartment_id, resource_metric, time_interval_start, time_interval_end, host_id
    )


# ============================================================================
# Database Management Tools
# ============================================================================


@app.tool()
def list_managed_databases(
    compartment_id: str,
    lifecycle_state: Optional[str] = None,
    name: Optional[str] = None,
) -> dict:
    """
    List all managed databases in a compartment.

    Args:
        compartment_id: Compartment OCID to query.
        lifecycle_state: Filter by lifecycle state.
        name: Filter by database name.

    Returns:
        Dictionary containing list of managed databases.
    """
    return tools_dbmanagement.list_managed_databases(compartment_id, lifecycle_state, name)


@app.tool()
def get_managed_database_details(database_id: str) -> dict:
    """
    Get detailed information about a specific managed database.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing detailed managed database information.
    """
    return tools_dbmanagement.get_managed_database(database_id)


@app.tool()
def get_tablespace_usage(database_id: str) -> dict:
    """
    Get tablespace usage information for a managed database.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing tablespace usage metrics.
    """
    return tools_dbmanagement.get_tablespace_usage(database_id)


@app.tool()
def get_database_parameters(
    database_id: str,
    name: Optional[str] = None,
    is_allowed_values_included: bool = False,
) -> dict:
    """
    Get database parameters for a managed database.

    Args:
        database_id: Managed Database OCID.
        name: Optional parameter name filter.
        is_allowed_values_included: Include allowed values.

    Returns:
        Dictionary containing database parameters.
    """
    return tools_dbmanagement.get_database_parameters(database_id, name, is_allowed_values_included)


@app.tool()
def list_awr_snapshots(
    database_id: str,
    awr_db_id: str,
    time_greater_than_or_equal_to: Optional[str] = None,
    time_less_than_or_equal_to: Optional[str] = None,
) -> dict:
    """
    List AWR snapshots for a managed database.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        time_greater_than_or_equal_to: Start time in ISO format.
        time_less_than_or_equal_to: End time in ISO format.

    Returns:
        Dictionary containing list of AWR snapshots.
    """
    return tools_dbmanagement.list_awr_db_snapshots(
        database_id, awr_db_id, time_greater_than_or_equal_to, time_less_than_or_equal_to
    )


@app.tool()
def get_awr_report(
    database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
    report_format: str = "HTML",
) -> dict:
    """
    Get AWR report for a managed database.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        begin_snapshot_id: Begin snapshot identifier.
        end_snapshot_id: End snapshot identifier.
        report_format: Report format (HTML or TEXT).

    Returns:
        Dictionary containing AWR report data.
    """
    return tools_dbmanagement.get_awr_db_report(
        database_id, awr_db_id, begin_snapshot_id, end_snapshot_id, report_format
    )


@app.tool()
def get_fleet_health_metrics(
    compartment_id: str,
    compare_type: str = "HOUR",
) -> dict:
    """
    Get aggregated fleet health metrics for all managed databases.

    Args:
        compartment_id: Compartment OCID.
        compare_type: Time period for comparison (HOUR, DAY, WEEK).

    Returns:
        Dictionary containing fleet health metrics.
    """
    return tools_dbmanagement.get_database_fleet_health_metrics(compartment_id, compare_type)


# ============================================================================
# Database Management - Monitoring & Diagnostics Tools
# ============================================================================


@app.tool()
def get_database_home_metrics(
    database_id: str,
    start_time: str,
    end_time: str,
) -> dict:
    """
    Get database home metrics for availability monitoring.

    Args:
        database_id: Managed Database OCID.
        start_time: Start time in ISO format.
        end_time: End time in ISO format.

    Returns:
        Dictionary containing database home availability metrics.
    """
    return tools_dbmanagement_monitoring.get_database_home_metrics(database_id, start_time, end_time)


@app.tool()
def list_database_jobs(
    database_id: str,
    job_name: Optional[str] = None,
) -> dict:
    """
    List scheduled database jobs for a managed database.

    Args:
        database_id: Managed Database OCID.
        job_name: Optional job name filter.

    Returns:
        Dictionary containing list of database jobs with schedules and status.
    """
    return tools_dbmanagement_monitoring.list_database_jobs(database_id, job_name)


@app.tool()
def get_addm_report(
    database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
) -> dict:
    """
    Get ADDM (Automatic Database Diagnostic Monitor) report with performance findings.

    ADDM analyzes database performance and provides specific recommendations
    for improving database efficiency.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        begin_snapshot_id: Begin snapshot identifier.
        end_snapshot_id: End snapshot identifier.

    Returns:
        Dictionary containing ADDM findings and recommendations.
    """
    return tools_dbmanagement_monitoring.get_addm_report(
        database_id, awr_db_id, begin_snapshot_id, end_snapshot_id
    )


@app.tool()
def get_ash_analytics(
    database_id: str,
    awr_db_id: str,
    time_start: str,
    time_end: str,
    wait_class: Optional[str] = None,
) -> dict:
    """
    Get ASH (Active Session History) analytics for performance analysis.

    Provides detailed wait event analysis to identify performance bottlenecks.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        time_start: Start time in ISO format.
        time_end: End time in ISO format.
        wait_class: Optional wait class filter (e.g., "User I/O", "CPU").

    Returns:
        Dictionary containing ASH wait event analytics.
    """
    return tools_dbmanagement_monitoring.get_ash_analytics(
        database_id, awr_db_id, time_start, time_end, wait_class
    )


@app.tool()
def get_top_sql_by_metric(
    database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
    metric: str = "CPU",
    top_n: int = 10,
) -> dict:
    """
    Get top SQL statements ranked by specified performance metric.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        begin_snapshot_id: Begin snapshot identifier.
        end_snapshot_id: End snapshot identifier.
        metric: Metric to sort by (CPU, ELAPSED_TIME, BUFFER_GETS, DISK_READS).
        top_n: Number of top SQL statements to return (default 10).

    Returns:
        Dictionary containing top SQL statements by metric.
    """
    return tools_dbmanagement_monitoring.get_top_sql_by_metric(
        database_id, awr_db_id, begin_snapshot_id, end_snapshot_id, metric, top_n
    )


@app.tool()
def get_database_system_statistics(
    database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
) -> dict:
    """
    Get database system statistics from AWR snapshots.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        begin_snapshot_id: Begin snapshot identifier.
        end_snapshot_id: End snapshot identifier.

    Returns:
        Dictionary containing system-level statistics.
    """
    return tools_dbmanagement_monitoring.get_database_system_statistics(
        database_id, awr_db_id, begin_snapshot_id, end_snapshot_id
    )


@app.tool()
def get_database_io_statistics(
    database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
) -> dict:
    """
    Get database I/O statistics from AWR snapshots.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        begin_snapshot_id: Begin snapshot identifier.
        end_snapshot_id: End snapshot identifier.

    Returns:
        Dictionary containing I/O performance metrics.
    """
    return tools_dbmanagement_monitoring.get_database_io_statistics(
        database_id, awr_db_id, begin_snapshot_id, end_snapshot_id
    )


@app.tool()
def list_alert_logs(
    database_id: str,
    log_level: Optional[str] = None,
    time_greater_than_or_equal_to: Optional[str] = None,
    time_less_than_or_equal_to: Optional[str] = None,
) -> dict:
    """
    List alert log entries for a managed database.

    Args:
        database_id: Managed Database OCID.
        log_level: Optional log level filter (CRITICAL, SEVERE, WARNING).
        time_greater_than_or_equal_to: Start time in ISO format.
        time_less_than_or_equal_to: End time in ISO format.

    Returns:
        Dictionary containing alert log entries with timestamps and messages.
    """
    return tools_dbmanagement_monitoring.list_alert_logs(
        database_id, log_level, time_greater_than_or_equal_to, time_less_than_or_equal_to
    )


@app.tool()
def get_database_cpu_usage(
    database_id: str,
    start_time: str,
    end_time: str,
) -> dict:
    """
    Get database CPU usage metrics over time.

    Args:
        database_id: Managed Database OCID.
        start_time: Start time in ISO format.
        end_time: End time in ISO format.

    Returns:
        Dictionary containing CPU usage information.
    """
    return tools_dbmanagement_monitoring.get_database_cpu_usage(database_id, start_time, end_time)


@app.tool()
def get_sql_tuning_recommendations(
    database_id: str,
    sql_id: str,
) -> dict:
    """
    Get SQL tuning recommendations for a specific SQL statement.

    Note: This is a placeholder for future SQL Tuning Advisor integration.
    Use ADDM and AWR reports for detailed recommendations.

    Args:
        database_id: Managed Database OCID.
        sql_id: SQL identifier.

    Returns:
        Dictionary containing SQL tuning recommendations.
    """
    return tools_dbmanagement_monitoring.get_sql_tuning_recommendations(database_id, sql_id)


@app.tool()
def get_database_resource_usage(
    database_id: str,
) -> dict:
    """
    Get current database resource usage summary.

    Provides overview of storage and resource utilization.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing current resource usage metrics.
    """
    return tools_dbmanagement_monitoring.get_database_resource_usage(database_id)


# ============================================================================
# Database Registration & Enablement Tools
# ============================================================================


@app.tool()
def enable_database_insights(
    database_id: str,
    compartment_id: str,
    entity_source: str = "AUTONOMOUS_DATABASE",
) -> dict:
    """
    Register and enable Operations Insights for a database.

    Args:
        database_id: Database OCID to enable insights for.
        compartment_id: Compartment OCID.
        entity_source: Database type (AUTONOMOUS_DATABASE, EM_MANAGED_EXTERNAL_DATABASE).

    Returns:
        Dictionary containing enablement status and database insight OCID.
    """
    return tools_database_registration.enable_database_insight(
        database_id, compartment_id, entity_source
    )


@app.tool()
def disable_database_insights(database_insight_id: str) -> dict:
    """
    Disable Operations Insights for a database.

    Args:
        database_insight_id: Database Insight OCID to disable.

    Returns:
        Dictionary containing disablement status.
    """
    return tools_database_registration.disable_database_insight(database_insight_id)


@app.tool()
def check_database_insight_status(
    database_id: str,
    compartment_id: str,
) -> dict:
    """
    Check if Operations Insights is enabled for a database.

    Args:
        database_id: Database OCID to check.
        compartment_id: Compartment OCID.

    Returns:
        Dictionary containing insight enablement status.
    """
    return tools_database_registration.get_database_insight_status(database_id, compartment_id)


@app.tool()
def get_database_info(database_id: str) -> dict:
    """
    Get comprehensive database information from OCI Database service.

    Retrieves details about Autonomous or regular databases including
    configuration, status, and connection information.

    Args:
        database_id: Database OCID.

    Returns:
        Dictionary containing database details.
    """
    return tools_database_registration.get_database_details_from_ocid(database_id)


# ============================================================================
# Direct Oracle Database Query Tools
# ============================================================================


@app.tool()
def query_oracle_database(
    connection_string: str,
    query: str,
    fetch_size: int = 100,
) -> dict:
    """
    Execute a SQL query directly against an Oracle database.

    SECURITY NOTE: Use wallet-based authentication for Autonomous Databases.

    Args:
        connection_string: Oracle connection string (user/pass@host:port/service).
        query: SQL query to execute.
        fetch_size: Number of rows to fetch (max 1000).

    Returns:
        Dictionary containing query results with columns and rows.
    """
    return tools_oracle_database.execute_query(connection_string, query, None, fetch_size)


@app.tool()
def query_with_wallet(
    wallet_location: str,
    wallet_password: str,
    dsn: str,
    username: str,
    password: str,
    query: str,
    fetch_size: int = 100,
) -> dict:
    """
    Execute a SQL query using Oracle Wallet (for Autonomous Database).

    Args:
        wallet_location: Path to wallet directory.
        wallet_password: Wallet password.
        dsn: Data source name (e.g., "mydb_high").
        username: Database username.
        password: Database password.
        query: SQL query to execute.
        fetch_size: Number of rows to fetch (max 1000).

    Returns:
        Dictionary containing query results.
    """
    return tools_oracle_database.execute_query_with_wallet(
        wallet_location, wallet_password, dsn, username, password, query, None, fetch_size
    )


@app.tool()
def get_oracle_database_metadata(connection_string: str) -> dict:
    """
    Get database metadata including version and instance info.

    Args:
        connection_string: Oracle connection string.

    Returns:
        Dictionary containing database metadata.
    """
    return tools_oracle_database.get_database_metadata(connection_string)


@app.tool()
def list_oracle_tables(
    connection_string: str,
    schema: Optional[str] = None,
) -> dict:
    """
    List tables in an Oracle database.

    Args:
        connection_string: Oracle connection string.
        schema: Optional schema name.

    Returns:
        Dictionary containing list of tables.
    """
    return tools_oracle_database.list_tables(connection_string, schema)


@app.tool()
def describe_oracle_table(
    connection_string: str,
    table_name: str,
    schema: Optional[str] = None,
) -> dict:
    """
    Describe Oracle table structure (columns, data types).

    Args:
        connection_string: Oracle connection string.
        table_name: Table name to describe.
        schema: Optional schema name.

    Returns:
        Dictionary containing table structure details.
    """
    return tools_oracle_database.describe_table(connection_string, table_name, schema)


@app.tool()
def get_oracle_session_info(connection_string: str) -> dict:
    """
    Get current Oracle session information.

    Args:
        connection_string: Oracle connection string.

    Returns:
        Dictionary containing session details.
    """
    return tools_oracle_database.get_session_info(connection_string)


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the MCP server with transport selection based on environment variables."""
    # Check transport mode from environment variables
    transport = os.getenv("FASTMCP_TRANSPORT", "stdio").lower()
    use_http = os.getenv("FASTMCP_HTTP", "0") == "1"

    if use_http or transport == "http":
        # Run HTTP server with streaming support
        # Note: This requires the FastMCP HTTP implementation
        # Check FastMCP docs for exact implementation
        print("Starting MCP server in HTTP mode...")
        try:
            # Try to run with HTTP transport
            app.run(transport="http")
        except (ValueError, NotImplementedError):
            # Fallback if HTTP not supported in this FastMCP version
            print("HTTP transport not available, falling back to stdio")
            app.run(transport="stdio")
    else:
        # Default: stdio transport for Claude Desktop/Code
        app.run(transport="stdio")


if __name__ == "__main__":
    main()
