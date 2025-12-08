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
# Enhanced multi-profile and advanced analytics tools
from . import tools_profile_management
from . import tools_dbmanagement_sql_plans
from . import tools_opsi_sql_insights
# Diagnostic and bulk operation tools
from . import tools_opsi_diagnostics
from . import tools_sqlwatch_bulk
# Skills support for enhanced DBA guidance
from . import tools_skills
# OAuth (OCI IAM / IDCS) integration for FastMCP
from .auth_bridge.oca_auth import (
    fetch_oca_token as oci_oauth_fetch_token,
    get_token_info as oci_oauth_get_info,
    clear_tokens as oci_oauth_clear_tokens,
)

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
# OCI IAM OAuth Tools (IDCS)
# ============================================================================


@app.tool()
def oci_oauth_login(flow: Optional[str] = None) -> dict:
    """
    Start OCI IAM OAuth login (IDCS) and cache access/refresh tokens.

    Args:
        flow: "pc" (browser PKCE) or "headless" (device code). Defaults to env OCA_AUTH_FLOW or "pc".

    Returns:
        Token info (expires, scopes). Token value itself is not returned.
    """
    try:
        # Trigger OAuth (stores tokens in local manager)
        _ = oci_oauth_fetch_token(flow)
        info = oci_oauth_get_info()
        # Do not expose raw tokens
        if "access_token" in info:
            info.pop("access_token")
        if "refresh_token" in info:
            info.pop("refresh_token")
        return {
            "status": "ok",
            "message": "Authenticated with OCI IAM (IDCS). Tokens cached.",
            "token_info": info,
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@app.tool()
def oci_oauth_status() -> dict:
    """
    Return current OAuth token status without exposing raw tokens.

    Returns:
        Token metadata (expiry, scopes, issued_at).
    """
    try:
        info = oci_oauth_get_info()
        if "access_token" in info:
            info.pop("access_token")
        if "refresh_token" in info:
            info.pop("refresh_token")
        return {"status": "ok", "token_info": info}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@app.tool()
def oci_oauth_logout() -> dict:
    """
    Clear cached OAuth tokens (logout).
    """
    try:
        oci_oauth_clear_tokens()
        return {"status": "ok", "message": "Tokens cleared"}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


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


@app.tool()
def get_host_resource_forecast_trend(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    forecast_days: int = 30,
    host_id: Optional[str] = None,
    statistic: Optional[str] = "AVG",
) -> dict:
    """
    Get ML-based resource utilization forecast for host capacity planning.

    This provides the same forecast data you see in OCI Console's Host Capacity Planning view.

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
    return tools_opsi_extended.summarize_host_insight_resource_forecast_trend(
        compartment_id, resource_metric, time_interval_start, time_interval_end,
        forecast_days, host_id, statistic
    )


@app.tool()
def get_host_resource_capacity_trend(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
    utilization_level: Optional[str] = None,
) -> dict:
    """
    Get capacity planning trends for host resource utilization.

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
    return tools_opsi_extended.summarize_host_insight_resource_capacity_trend(
        compartment_id, resource_metric, time_interval_start, time_interval_end,
        host_id, utilization_level
    )


@app.tool()
def get_host_resource_usage(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict:
    """
    Get current resource usage summary for hosts.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, NETWORK, STORAGE).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing resource usage summary.
    """
    return tools_opsi_extended.summarize_host_insight_resource_usage(
        compartment_id, resource_metric, time_interval_start, time_interval_end, host_id
    )


@app.tool()
def get_host_resource_usage_trend(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict:
    """
    Get resource usage trends over time for hosts.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, NETWORK, STORAGE).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing resource usage trend data.
    """
    return tools_opsi_extended.summarize_host_insight_resource_usage_trend(
        compartment_id, resource_metric, time_interval_start, time_interval_end, host_id
    )


@app.tool()
def get_host_resource_utilization_insight(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
    forecast_days: int = 30,
) -> dict:
    """
    Get resource utilization insights with projections and recommendations.

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
    return tools_opsi_extended.summarize_host_insight_resource_utilization_insight(
        compartment_id, resource_metric, time_interval_start, time_interval_end,
        host_id, forecast_days
    )


@app.tool()
def get_host_disk_statistics(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict:
    """
    Get disk I/O statistics for hosts.

    Args:
        compartment_id: Compartment OCID.
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing disk statistics.
    """
    return tools_opsi_extended.summarize_host_insight_disk_statistics(
        compartment_id, time_interval_start, time_interval_end, host_id
    )


@app.tool()
def get_host_io_usage_trend(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict:
    """
    Get I/O usage trends over time for hosts.

    Args:
        compartment_id: Compartment OCID.
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing I/O usage trend data.
    """
    return tools_opsi_extended.summarize_host_insight_io_usage_trend(
        compartment_id, time_interval_start, time_interval_end, host_id
    )


@app.tool()
def get_host_network_usage_trend(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict:
    """
    Get network usage trends over time for hosts.

    Args:
        compartment_id: Compartment OCID.
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing network usage trend data.
    """
    return tools_opsi_extended.summarize_host_insight_network_usage_trend(
        compartment_id, time_interval_start, time_interval_end, host_id
    )


@app.tool()
def get_host_storage_usage_trend(
    compartment_id: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict:
    """
    Get storage usage trends over time for hosts.

    Args:
        compartment_id: Compartment OCID.
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing storage usage trend data.
    """
    return tools_opsi_extended.summarize_host_insight_storage_usage_trend(
        compartment_id, time_interval_start, time_interval_end, host_id
    )


@app.tool()
def get_host_top_processes_usage(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
    limit: int = 10,
) -> dict:
    """
    Get top resource-consuming processes on hosts.

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
    return tools_opsi_extended.summarize_host_insight_top_processes_usage(
        compartment_id, resource_metric, time_interval_start, time_interval_end,
        host_id, limit
    )


@app.tool()
def get_host_top_processes_usage_trend(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict:
    """
    Get trends for top resource-consuming processes over time.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing top processes trend data.
    """
    return tools_opsi_extended.summarize_host_insight_top_processes_usage_trend(
        compartment_id, resource_metric, time_interval_start, time_interval_end, host_id
    )


@app.tool()
def get_host_recommendations(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    host_id: Optional[str] = None,
) -> dict:
    """
    Get AI-driven host configuration recommendations.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, MEMORY, STORAGE).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        host_id: Optional host insight OCID filter.

    Returns:
        Dictionary containing host recommendations.
    """
    return tools_opsi_extended.summarize_host_insight_host_recommendation(
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
# Enhanced Profile Management Tools (Multi-Tenancy Support)
# ============================================================================


@app.tool()
def list_oci_profiles_enhanced() -> dict:
    """
    List all OCI profiles with comprehensive configuration details and validation status.

    Enhanced version with detailed profile information, validation, and multi-tenancy support.

    Returns:
        Dictionary containing profile count, current profile, and detailed profile list.
    """
    return tools_profile_management.list_oci_profiles_enhanced()


@app.tool()
def get_oci_profile_details(profile: str) -> dict:
    """
    Get comprehensive configuration details for a specific OCI profile.

    Args:
        profile: Profile name to query.

    Returns:
        Dictionary with profile configuration, validation status, and tenancy info.
    """
    return tools_profile_management.get_oci_profile_details(profile)


@app.tool()
def validate_oci_profile(profile: str) -> dict:
    """
    Validate that an OCI profile exists and is properly configured.

    Args:
        profile: Profile name to validate.

    Returns:
        Dictionary with validation results and any error messages.
    """
    return tools_profile_management.validate_oci_profile(profile)


@app.tool()
def get_profile_tenancy_details(profile: Optional[str] = None) -> dict:
    """
    Get tenancy information for a specific profile.

    Args:
        profile: Profile name. If None, uses current active profile.

    Returns:
        Dictionary with tenancy OCID, name, region, and user details.
    """
    return tools_profile_management.get_profile_tenancy_details(profile)


@app.tool()
def compare_oci_profiles(profiles: list[str]) -> dict:
    """
    Compare multiple OCI profiles side-by-side.

    Args:
        profiles: List of profile names to compare.

    Returns:
        Dictionary with comparison data for all profiles.
    """
    return tools_profile_management.compare_oci_profiles(profiles)


@app.tool()
def refresh_profile_cache() -> dict:
    """
    Refresh the profile configuration cache.

    Forces reload of all profile configurations from disk.

    Returns:
        Dictionary with success status.
    """
    return tools_profile_management.refresh_profile_cache()


@app.tool()
def get_current_profile_info() -> dict:
    """
    Get information about the currently active OCI profile.

    Returns:
        Dictionary with current profile details and tenancy information.
    """
    return tools_profile_management.get_current_profile_info()


# ============================================================================
# SQL Plan Baseline Management Tools
# ============================================================================


@app.tool()
def list_sql_plan_baselines(
    database_id: str,
    profile: Optional[str] = None,
    plan_name: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    is_accepted: Optional[bool] = None,
) -> dict:
    """
    List SQL Plan Baselines for a managed database.

    Args:
        database_id: Managed Database OCID.
        profile: OCI profile name for multi-tenancy support.
        plan_name: Filter by plan name (optional).
        is_enabled: Filter by enabled status (optional).
        is_accepted: Filter by accepted status (optional).

    Returns:
        Dictionary with list of SQL plan baselines.
    """
    return tools_dbmanagement_sql_plans.list_sql_plan_baselines(
        database_id=database_id,
        profile=profile,
        plan_name=plan_name,
        is_enabled=is_enabled,
        is_accepted=is_accepted,
    )


@app.tool()
def get_sql_plan_baseline(
    database_id: str,
    plan_name: str,
    profile: Optional[str] = None,
) -> dict:
    """
    Get detailed information about a specific SQL Plan Baseline.

    Args:
        database_id: Managed Database OCID.
        plan_name: Name of the SQL plan baseline.
        profile: OCI profile name for multi-tenancy support.

    Returns:
        Dictionary with detailed baseline information.
    """
    return tools_dbmanagement_sql_plans.get_sql_plan_baseline(
        database_id=database_id,
        plan_name=plan_name,
        profile=profile,
    )


@app.tool()
def load_sql_plan_baselines_from_awr(
    database_id: str,
    profile: Optional[str] = None,
    sql_handle: Optional[str] = None,
    sql_text: Optional[str] = None,
    begin_snapshot: Optional[int] = None,
    end_snapshot: Optional[int] = None,
) -> dict:
    """
    Load SQL Plan Baselines from AWR snapshots.

    Args:
        database_id: Managed Database OCID.
        profile: OCI profile name for multi-tenancy support.
        sql_handle: Specific SQL handle to load (optional).
        sql_text: SQL text filter (optional).
        begin_snapshot: Beginning AWR snapshot ID (optional).
        end_snapshot: Ending AWR snapshot ID (optional).

    Returns:
        Dictionary with work request ID for tracking.
    """
    return tools_dbmanagement_sql_plans.load_sql_plan_baselines_from_awr(
        database_id=database_id,
        profile=profile,
        sql_handle=sql_handle,
        sql_text=sql_text,
        begin_snapshot=begin_snapshot,
        end_snapshot=end_snapshot,
    )


@app.tool()
def drop_sql_plan_baselines(
    database_id: str,
    profile: Optional[str] = None,
    plan_name: Optional[str] = None,
    sql_handle: Optional[str] = None,
) -> dict:
    """
    Drop (delete) SQL Plan Baselines from a managed database.

    Args:
        database_id: Managed Database OCID.
        profile: OCI profile name for multi-tenancy support.
        plan_name: Name of specific plan baseline to drop.
        sql_handle: SQL handle (drops all baselines for this SQL).

    Returns:
        Dictionary with operation result.
    """
    return tools_dbmanagement_sql_plans.drop_sql_plan_baselines(
        database_id=database_id,
        profile=profile,
        plan_name=plan_name,
        sql_handle=sql_handle,
    )


@app.tool()
def enable_automatic_spm_evolve_task(
    database_id: str,
    profile: Optional[str] = None,
) -> dict:
    """
    Enable the automatic SQL Plan Management (SPM) evolve advisor task.

    Args:
        database_id: Managed Database OCID.
        profile: OCI profile name for multi-tenancy support.

    Returns:
        Dictionary with operation result.
    """
    return tools_dbmanagement_sql_plans.enable_automatic_spm_evolve_task(
        database_id=database_id,
        profile=profile,
    )


@app.tool()
def configure_automatic_spm_capture(
    database_id: str,
    enabled: bool,
    profile: Optional[str] = None,
    auto_filter_sql_text: Optional[str] = None,
    auto_filter_parsing_schema: Optional[str] = None,
) -> dict:
    """
    Configure automatic SQL Plan Management baseline capture.

    Args:
        database_id: Managed Database OCID.
        enabled: Whether to enable or disable automatic capture.
        profile: OCI profile name for multi-tenancy support.
        auto_filter_sql_text: Filter to capture only matching SQL text.
        auto_filter_parsing_schema: Filter to capture only from specific schemas.

    Returns:
        Dictionary with operation result.
    """
    return tools_dbmanagement_sql_plans.configure_automatic_spm_capture(
        database_id=database_id,
        enabled=enabled,
        profile=profile,
        auto_filter_sql_text=auto_filter_sql_text,
        auto_filter_parsing_schema=auto_filter_parsing_schema,
    )


# ============================================================================
# SQL Insights and Advanced Analytics Tools
# ============================================================================


@app.tool()
def summarize_sql_insights(
    compartment_id: str,
    profile: Optional[str] = None,
    database_id: Optional[list[str]] = None,
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
    database_time_pct_greater_than: Optional[float] = None,
) -> dict:
    """
    Get SQL performance insights with anomaly detection.

    Analyzes SQL statements consuming significant database time and identifies
    performance anomalies, trends, and outliers.

    Args:
        compartment_id: Compartment OCID.
        profile: OCI profile name for multi-tenancy support.
        database_id: List of database insight OCIDs to analyze (optional).
        time_interval_start: Start time in ISO 8601 format (optional).
        time_interval_end: End time in ISO 8601 format (optional).
        database_time_pct_greater_than: Filter to SQL consuming more than this % of DB time.

    Returns:
        Dictionary with SQL insights and performance analysis.
    """
    return tools_opsi_sql_insights.summarize_sql_insights(
        compartment_id=compartment_id,
        profile=profile,
        database_id=database_id,
        time_interval_start=time_interval_start,
        time_interval_end=time_interval_end,
        database_time_pct_greater_than=database_time_pct_greater_than,
    )


@app.tool()
def summarize_sql_plan_insights(
    compartment_id: str,
    sql_identifier: str,
    profile: Optional[str] = None,
    database_id: Optional[list[str]] = None,
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
) -> dict:
    """
    Analyze execution plan performance for a specific SQL statement.

    Args:
        compartment_id: Compartment OCID.
        sql_identifier: SQL identifier to analyze.
        profile: OCI profile name for multi-tenancy support.
        database_id: List of database insight OCIDs (optional).
        time_interval_start: Start time in ISO 8601 format (optional).
        time_interval_end: End time in ISO 8601 format (optional).

    Returns:
        Dictionary with plan insights and performance comparison.
    """
    return tools_opsi_sql_insights.summarize_sql_plan_insights(
        compartment_id=compartment_id,
        sql_identifier=sql_identifier,
        profile=profile,
        database_id=database_id,
        time_interval_start=time_interval_start,
        time_interval_end=time_interval_end,
    )


@app.tool()
def summarize_addm_db_findings(
    compartment_id: str,
    profile: Optional[str] = None,
    database_id: Optional[list[str]] = None,
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
) -> dict:
    """
    Get consolidated ADDM (Automatic Database Diagnostic Monitor) findings.

    Args:
        compartment_id: Compartment OCID.
        profile: OCI profile name for multi-tenancy support.
        database_id: List of database insight OCIDs to analyze (optional).
        time_interval_start: Start time in ISO 8601 format (optional).
        time_interval_end: End time in ISO 8601 format (optional).

    Returns:
        Dictionary with ADDM findings and recommendations.
    """
    return tools_opsi_sql_insights.summarize_addm_db_findings(
        compartment_id=compartment_id,
        profile=profile,
        database_id=database_id,
        time_interval_start=time_interval_start,
        time_interval_end=time_interval_end,
    )


@app.tool()
def get_sql_insight_details(
    compartment_id: str,
    sql_identifier: str,
    database_id: str,
    profile: Optional[str] = None,
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
) -> dict:
    """
    Get detailed insights for a specific SQL statement on a specific database.

    Args:
        compartment_id: Compartment OCID.
        sql_identifier: SQL identifier to analyze.
        database_id: Database insight OCID.
        profile: OCI profile name for multi-tenancy support.
        time_interval_start: Start time in ISO 8601 format (optional).
        time_interval_end: End time in ISO 8601 format (optional).

    Returns:
        Dictionary with detailed SQL performance insights.
    """
    return tools_opsi_sql_insights.get_sql_insight_details(
        compartment_id=compartment_id,
        sql_identifier=sql_identifier,
        database_id=database_id,
        profile=profile,
        time_interval_start=time_interval_start,
        time_interval_end=time_interval_end,
    )


# ============================================================================
# Operations Insights Diagnostic Tools
# ============================================================================


@app.tool()
def diagnose_opsi_permissions(
    compartment_id: str,
    profile: Optional[str] = None,
) -> dict:
    """
    Diagnose Operations Insights IAM permissions and identify missing policies.

    Tests various OPSI operations to determine which permissions are granted
    and which are missing, helping troubleshoot authorization errors.

    Args:
        compartment_id: Compartment OCID to test permissions in.
        profile: OCI profile name for multi-tenancy support.

    Returns:
        Dictionary with permission test results and recommendations.
    """
    return tools_opsi_diagnostics.diagnose_opsi_permissions(
        compartment_id=compartment_id,
        profile=profile,
    )


@app.tool()
def check_sqlwatch_status_bulk(
    compartment_id: str,
    profile: Optional[str] = None,
    lifecycle_state: str = "ACTIVE",
) -> dict:
    """
    Check SQL Watch status across all managed databases in a compartment.

    SQL Watch is required for detailed SQL-level monitoring. This tool
    identifies which databases have SQL Watch enabled/disabled.

    Args:
        compartment_id: Compartment OCID.
        profile: OCI profile name for multi-tenancy support.
        lifecycle_state: Filter by lifecycle state (default: ACTIVE).

    Returns:
        Dictionary with SQL Watch status for each database.
    """
    return tools_opsi_diagnostics.check_sqlwatch_status_bulk(
        compartment_id=compartment_id,
        profile=profile,
        lifecycle_state=lifecycle_state,
    )


@app.tool()
def check_database_insights_configuration(
    compartment_id: str,
    profile: Optional[str] = None,
) -> dict:
    """
    Check Operations Insights configuration for all database insights.

    Identifies databases with incomplete configuration for SQL-level monitoring.

    Args:
        compartment_id: Compartment OCID.
        profile: OCI profile name for multi-tenancy support.

    Returns:
        Dictionary with configuration status for each database insight.
    """
    return tools_opsi_diagnostics.check_database_insights_configuration(
        compartment_id=compartment_id,
        profile=profile,
    )


@app.tool()
def get_comprehensive_diagnostics(
    compartment_id: str,
    profile: Optional[str] = None,
) -> dict:
    """
    Run comprehensive diagnostics for Operations Insights SQL analytics issues.

    Combines all diagnostic checks to provide complete picture of configuration
    and permission issues with actionable recommendations.

    Args:
        compartment_id: Compartment OCID.
        profile: OCI profile name for multi-tenancy support.

    Returns:
        Dictionary with complete diagnostic results and prioritized action plan.
    """
    return tools_opsi_diagnostics.get_comprehensive_diagnostics(
        compartment_id=compartment_id,
        profile=profile,
    )


# ============================================================================
# SQL Watch Bulk Management Tools
# ============================================================================


@app.tool()
def enable_sqlwatch_bulk(
    compartment_id: str,
    profile: Optional[str] = None,
    database_type_filter: Optional[str] = None,
    dry_run: bool = True,
) -> dict:
    """
    Enable SQL Watch on multiple managed databases in bulk.

    SQL Watch is required for detailed SQL-level monitoring in Operations Insights.

    Args:
        compartment_id: Compartment OCID.
        profile: OCI profile name for multi-tenancy support.
        database_type_filter: Filter by database type (optional).
        dry_run: If True, shows what would be done without making changes.

    Returns:
        Dictionary with enablement results for each database.
    """
    return tools_sqlwatch_bulk.enable_sqlwatch_bulk(
        compartment_id=compartment_id,
        profile=profile,
        database_type_filter=database_type_filter,
        dry_run=dry_run,
    )


@app.tool()
def disable_sqlwatch_bulk(
    compartment_id: str,
    profile: Optional[str] = None,
    dry_run: bool = True,
) -> dict:
    """
    Disable SQL Watch on multiple managed databases in bulk.

    Use with caution - this stops detailed SQL-level monitoring.

    Args:
        compartment_id: Compartment OCID.
        profile: OCI profile name for multi-tenancy support.
        dry_run: If True, shows what would be done without making changes.

    Returns:
        Dictionary with disable results for each database.
    """
    return tools_sqlwatch_bulk.disable_sqlwatch_bulk(
        compartment_id=compartment_id,
        profile=profile,
        dry_run=dry_run,
    )


@app.tool()
def check_sqlwatch_work_requests(
    compartment_id: str,
    profile: Optional[str] = None,
    hours_back: int = 1,
) -> dict:
    """
    Check the status of SQL Watch enablement work requests.

    Monitors progress of SQL Watch enable/disable operations.

    Args:
        compartment_id: Compartment OCID.
        profile: OCI profile name for multi-tenancy support.
        hours_back: How many hours back to check work requests (default: 1).

    Returns:
        Dictionary with work request status information.
    """
    return tools_sqlwatch_bulk.check_sqlwatch_work_requests(
        compartment_id=compartment_id,
        profile=profile,
        hours_back=hours_back,
    )


# ============================================================================
# Skills Tools - Enhanced DBA Guidance with Token Optimization
# ============================================================================


@app.tool()
def list_available_skills() -> dict:
    """
    List all available DBA skills for enhanced guidance.

    Skills are specialized instruction sets that help perform specific DBA
    tasks with minimal token usage and maximum accuracy. Each skill provides:
    - Focused guidance for specific task types
    - Recommended tools and workflows
    - Best practices and examples

    Returns:
        Dictionary containing list of available skills with descriptions.

    Example:
        list_available_skills()
        # Returns: {"skills": [{"name": "fleet-overview", ...}, ...]}
    """
    return tools_skills.list_available_skills()


@app.tool()
def get_skill_context(skill_name: str) -> dict:
    """
    Get detailed context for a specific DBA skill.

    Returns full skill instructions including recommended tools,
    example interactions, and best practices.

    Available skills:
    - fleet-overview: Instant database fleet statistics
    - sql-performance: SQL analysis and tuning
    - capacity-planning: Resource forecasting
    - database-diagnostics: ADDM, AWR, troubleshooting
    - awr-analysis: Deep AWR performance analysis
    - host-monitoring: Host resource monitoring
    - storage-management: Tablespace and storage
    - security-audit: Users, roles, privileges
    - sql-watch-management: SQL Watch enablement
    - sql-plan-baselines: SPM management
    - multi-tenancy: Multi-profile operations
    - exadata-monitoring: Exadata systems

    Args:
        skill_name: Name of the skill to retrieve

    Returns:
        Dictionary with skill name, description, allowed tools, and content.

    Example:
        get_skill_context("sql-performance")
    """
    return tools_skills.get_skill_context(skill_name)


@app.tool()
def get_skill_for_query(query: str) -> dict:
    """
    Find the most relevant skill for a user query.

    Analyzes the query to determine which skill would be most helpful,
    then returns that skill's context for optimal response generation.

    This is useful for automatically selecting the right guidance based
    on what the user is asking about.

    Args:
        query: User's natural language question or request

    Returns:
        Dictionary with matched skill name, context, and recommended tools.

    Example:
        get_skill_for_query("How many databases do I have?")
        # Returns: {"matched_skill": "fleet-overview", "context": "...", ...}
    """
    return tools_skills.get_skill_for_query(query)


@app.tool()
def get_quick_reference(category: Optional[str] = None) -> dict:
    """
    Get a quick reference guide for common DBA tasks.

    Provides a condensed reference of which tools to use for different
    tasks, optimized for minimal token usage.

    Args:
        category: Optional filter (fleet, sql, capacity, diagnostics, storage, security)

    Returns:
        Dictionary containing task-to-tool mappings.

    Example:
        get_quick_reference("sql")  # SQL-related tools only
        get_quick_reference()       # All categories
    """
    return tools_skills.get_quick_reference(category)


@app.tool()
def get_token_optimization_tips() -> dict:
    """
    Get tips for minimizing token usage in DBA operations.

    Returns best practices for efficient queries that minimize
    token consumption while maximizing information quality.

    Useful for understanding which tools are most token-efficient
    and how to structure queries for optimal results.

    Returns:
        Dictionary containing optimization tips and tool recommendations.

    Example:
        get_token_optimization_tips()
    """
    return tools_skills.get_token_optimization_tips()


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the MCP server with transport selection based on environment variables."""
    # Transport selection with fallbacks:
    # - stdio (default)
    # - http (streamable HTTP)
    # - sse (Server-Sent Events)
    transport = os.getenv("FASTMCP_TRANSPORT", "stdio").lower()
    use_http = os.getenv("FASTMCP_HTTP", "0") == "1"

    if transport == "sse":
        print("Starting MCP server in SSE mode...")
        try:
            app.run(transport="sse")
            return
        except (ValueError, NotImplementedError):
            print("SSE transport not available, falling back to HTTP")

        # fall through to HTTP

    if use_http or transport == "http":
        print("Starting MCP server in HTTP mode...")
        try:
            app.run(transport="http")
            return
        except (ValueError, NotImplementedError):
            print("HTTP transport not available, falling back to stdio")

    # Default: stdio transport for Claude Desktop/Code
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
