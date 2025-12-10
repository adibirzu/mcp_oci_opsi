"""Main entrypoint for the MCP OCI OPSI server."""

import logging
import os
import threading
from typing import Optional, List, Union

import oci
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .logging_config import configure_logging
from .bootstrap import MCPBootstrap

# Bootstrap the environment on startup
bootstrap = MCPBootstrap()
_bootstrap_success, _bootstrap_message = bootstrap.run_bootstrap(install_deps=True)

# Ensure logging is configured when main.py is invoked directly (not via __main__)
configure_logging()

from .config import get_oci_config, list_available_profiles, get_current_profile
from .config import list_all_profiles_with_details  # optional enhanced config
from .oci_clients import get_opsi_client, list_all
from .tools import (
    opsi as tools_opsi,
    opsi_extended as tools_opsi_extended,
    opsi_sql_insights as tools_opsi_sql_insights,
    opsi_resource_stats as tools_opsi_resource_stats,
    opsi_diagnostics as tools_opsi_diagnostics,
    dbmanagement as tools_dbmanagement,
    dbmanagement_monitoring as tools_dbmanagement_monitoring,
    dbmanagement_sql_plans as tools_dbmanagement_sql_plans,
    dbmanagement_awr_metrics as tools_dbmanagement_awr_metrics,
    dbmanagement_tablespaces as tools_dbmanagement_tablespaces,
    dbmanagement_users as tools_dbmanagement_users,
    sqlwatch as tools_sqlwatch,
    sqlwatch_bulk as tools_sqlwatch_bulk,
    database_registration as tools_database_registration,
    database_discovery as tools_database_discovery,
    oracle_database as tools_oracle_database,
    cache as tools_cache,
    visualization as tools_visualization,
    profile_management as tools_profile_management,
    skills as tools_skills,
    tools_cache_enhanced as tools_cache_enhanced,
    tools_skills_v2 as tools_skills_v2,  # Programmatic skills
)
# Note: OCA OAuth tools removed - this is a public OPSI MCP without OCA dependencies
# OCA authentication is handled by the parent DB OPS agent only

# Initialize FastMCP application
app = FastMCP("oci-opsi")
logger = logging.getLogger(__name__)


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
def whoami(profile: Optional[str] = None) -> dict:
    """
    Get the current OCI user and tenancy information from configuration.

    Args:
        profile: Optional OCI CLI profile name to use for this call.

    Returns:
        Dictionary containing tenancy OCID, user OCID, region, and profile.
    """
    original_profile = os.getenv("OCI_CLI_PROFILE")
    try:
        # Temporarily switch profile if provided
        if profile:
            os.environ["OCI_CLI_PROFILE"] = profile

        config = get_oci_config()
        result = {
            "tenancy_ocid": config.get("tenancy"),
            "user_ocid": config.get("user"),
            "region": config.get("region"),
            "profile": get_current_profile(),
            "fingerprint": config.get("fingerprint"),
        }
        return result
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "profile": profile,
        }
    finally:
        # Restore original profile environment
        if profile:
            if original_profile is not None:
                os.environ["OCI_CLI_PROFILE"] = original_profile
            elif "OCI_CLI_PROFILE" in os.environ:
                del os.environ["OCI_CLI_PROFILE"]


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


# Note: OAuth/IDCS tools removed - OCA authentication is handled by parent agent only


# ============================================================================
# Fast Cache Tools - Instant Responses, No API Calls
# ============================================================================


@app.tool()
def build_database_cache(compartment_ids: str, task_progress: Optional[str] = None) -> dict:
    """
    Build local cache of all databases across compartments and their children.

    This scans the entire compartment hierarchy recursively and stores results
    in ~/.mcp_oci_opsi_cache.json for instant retrieval.

    FIRST-TIME SETUP: Run this once to build the cache, then use fast cache tools.

    Args:
        compartment_ids: Comma-separated list of root compartment OCIDs to scan recursively
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with build status and statistics
    """
    # Convert comma-separated string to list for internal tool
    ids_list = [x.strip() for x in compartment_ids.split(",") if x.strip()]
    return tools_cache.build_database_cache(ids_list, task_progress=task_progress)


@app.tool()
def get_fleet_summary(task_progress: Optional[str] = None) -> dict:
    """
    Get concise fleet summary - INSTANT, NO API CALLS, MINIMAL TOKENS.

    Ultra-fast overview of entire database fleet from local cache.
    Perfect for quick questions about fleet size and distribution.

    Args:
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with fleet statistics (databases, hosts, by compartment, by type)
    """
    return tools_cache.get_fleet_summary(task_progress=task_progress)


@app.tool()
def search_databases(name: Optional[str] = None, compartment: Optional[str] = None, limit: int = 20, task_progress: Optional[str] = None) -> dict:
    """
    Search databases in cache - INSTANT, NO API CALLS.

    Ultra-fast database search using local cache with partial matching.

    Args:
        name: Database name filter (partial, case-insensitive)
        compartment: Compartment name filter (partial, case-insensitive)
        limit: Maximum results to return (default 20)
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with matching databases
    """
    return tools_cache.search_cached_databases(name=name, compartment=compartment, limit=limit, task_progress=task_progress)


@app.tool()
def get_databases_by_compartment(compartment_name: str, task_progress: Optional[str] = None) -> dict:
    """
    Get all databases in a compartment - INSTANT, NO API CALLS.

    Token-efficient response with essential database info grouped by compartment.

    Args:
        compartment_name: Compartment name (partial match, case-insensitive)
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with databases grouped by compartment
    """
    return tools_cache.get_databases_by_compartment(compartment_name, task_progress=task_progress)


@app.tool()
def get_cached_statistics(task_progress: Optional[str] = None) -> dict:
    """
    Get detailed cache statistics - INSTANT, NO API CALLS.

    Returns comprehensive statistics about cached databases including
    counts by type, compartment, and status.

    Args:
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with detailed statistics and cache metadata
    """
    return tools_cache.get_cached_statistics(task_progress=task_progress)


@app.tool()
def list_cached_compartments(task_progress: Optional[str] = None) -> dict:
    """
    List all compartments in cache - INSTANT, NO API CALLS.

    Args:
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with all cached compartments
    """
    return tools_cache.list_cached_compartments(task_progress=task_progress)


@app.tool()
def refresh_cache_if_needed(max_age_hours: int = 24, task_progress: Optional[str] = None) -> dict:
    """
    Check cache age and determine if refresh is needed.

    Args:
        max_age_hours: Maximum cache age in hours before refresh (default 24)
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with cache validity status and refresh recommendation
    """
    return tools_cache.refresh_cache_if_needed(max_age_hours, task_progress=task_progress)


@app.tool()
def refresh_all_caches(
    profiles: Optional[Union[str, List[str]]] = None,
    compartment_ids: Optional[Union[str, List[str]]] = None,
    max_age_hours: int = 24,
    task_progress: Optional[str] = None,
) -> dict:
    """
    Refresh caches for all (or selected) OCI profiles across all subscribed regions.

    This is the main entry point for populating database discovery data.
    If cache is valid, it is left unchanged. If expired/missing, it will build
    using the tenancy root (or supplied compartments).

    Args:
        profiles: Comma-separated list of OCI profile names to refresh (default: all profiles)
        compartment_ids: Optional comma-separated list of compartment OCIDs to scan (default: tenancy root)
        max_age_hours: Maximum cache age in hours before refresh (default 24)
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with refresh status per profile and region
    """
    # Normalize inputs: accept string (comma-delimited) or list
    profiles_list: Optional[List[str]]
    if isinstance(profiles, list):
        profiles_list = [str(x).strip() for x in profiles if str(x).strip()]
    elif isinstance(profiles, str):
        profiles_list = [x.strip() for x in profiles.split(",") if x.strip()]
    else:
        profiles_list = None

    ids_list: Optional[List[str]]
    if isinstance(compartment_ids, list):
        ids_list = [str(x).strip() for x in compartment_ids if str(x).strip()]
    elif isinstance(compartment_ids, str):
        ids_list = [x.strip() for x in compartment_ids.split(",") if x.strip()]
    else:
        ids_list = None
    
    return tools_cache.refresh_all_caches(
        profiles=profiles_list,
        compartment_ids=ids_list,
        max_age_hours=max_age_hours,
        task_progress=task_progress,
    )


@app.tool()
def get_cached_database(db_id: str, profile: Optional[str] = None, task_progress: Optional[str] = None) -> dict:
    """
    Get database details from cache by OCID - INSTANT, NO API CALLS.

    Args:
        db_id: Database insight OCID
        profile: OCI profile name (optional)
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with database details or not found message
    """
    return tools_cache.get_cached_database(db_id, profile=profile, task_progress=task_progress)


# Enhanced Cache Tools (Regions/Compartments) - Lazy build on demand
@app.tool()
def list_cached_regions(profile: Optional[str] = None, max_age_hours: int = 24) -> dict:
    """
    List subscribed regions from the enhanced cache.
    Builds the enhanced cache on demand if missing/stale.
    """
    return tools_cache_enhanced.list_cached_regions(profile=profile, max_age_hours=max_age_hours)


@app.tool()
def get_compartment_tree(profile: Optional[str] = None, root_id: Optional[str] = None, max_age_hours: int = 24) -> dict:
    """
    Get compartment tree from the enhanced cache.
    Builds the enhanced cache on demand if missing/stale.
    """
    return tools_cache_enhanced.get_compartment_tree(profile=profile, root_id=root_id, max_age_hours=max_age_hours)


@app.tool()
def list_enhanced_compartments(profile: Optional[str] = None, max_age_hours: int = 24) -> dict:
    """
    Get a flat list of compartments (id, name, parent_id, level, lifecycle_state) from the enhanced cache.
    Builds the enhanced cache on demand if missing/stale.
    """
    return tools_cache_enhanced.list_enhanced_compartments(profile=profile, max_age_hours=max_age_hours)


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

        items = []
        if response and hasattr(response, 'data') and response.data:
            items = [
                {
                    "resource_name": item.resource_name,
                    "usage": item.usage,
                    "capacity": item.capacity,
                    "utilization_percent": item.utilization_percent,
                }
                for item in response.data.items
            ]

        return {
            "database_insight_id": database_insight_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "resource_metric": "CPU",
            "items": items,
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
        if compartments and hasattr(compartments, 'data') and compartments.data:
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
# Programmatic Skills Tools (v2)
# ============================================================================

@app.tool()
def skill_discover_databases(
    compartment_id: Optional[str] = None,
    region: Optional[str] = None,
    db_type: Optional[str] = None,
    limit: int = 50
) -> dict:
    """
    Discover databases using the DatabaseDiscoverySkill (Tier 1 - Cache-based).
    
    FAST: Uses cached data for instant response (< 100ms).
    Falls back to API only when cache is stale.
    
    Args:
        compartment_id: Filter by compartment OCID (optional)
        region: Filter by region (e.g., 'us-ashburn-1') (optional)
        db_type: Filter by type ('adb', 'base', 'exadata', etc.) (optional)
        limit: Maximum number of results to return (default: 50)
    
    Returns:
        Dictionary with databases, total count, and filters applied
    """
    return tools_skills_v2.skill_discover_databases(
        compartment_id=compartment_id,
        region=region,
        db_type=db_type,
        limit=limit
    )


@app.tool()
def skill_get_fleet_summary() -> dict:
    """
    Get high-level fleet summary using DatabaseDiscoverySkill (Tier 1).
    
    INSTANT: Zero API calls, uses cached data.
    
    Returns:
        Dictionary with total count, by_type, by_state, by_region, total_cpu, total_storage
    """
    return tools_skills_v2.skill_get_fleet_summary()


@app.tool()
def skill_search_databases(query: str, limit: int = 20) -> dict:
    """
    Search databases by name or OCID using DatabaseDiscoverySkill (Tier 1).
    
    FAST: Uses cached data, partial case-insensitive matching.
    
    Args:
        query: Search string to match against database name or OCID
        limit: Maximum number of results (default: 20)
    
    Returns:
        Dictionary with matching databases
    """
    return tools_skills_v2.skill_search_databases(query=query, limit=limit)


@app.tool()
def skill_get_database_by_name(name: str) -> dict:
    """
    Get database details by exact name match (Tier 1).
    
    Args:
        name: Database name (case-insensitive)
    
    Returns:
        Dictionary with database details or error if not found
    """
    return tools_skills_v2.skill_get_database_by_name(name=name)


@app.tool()
def skill_analyze_cpu_usage(database_id: str, hours_back: int = 24) -> dict:
    """
    Analyze CPU usage for a database using PerformanceAnalysisSkill (Tier 2).
    
    Provides current, average, peak usage, trend analysis, and recommendations.
    
    Args:
        database_id: Database OCID
        hours_back: Number of hours to analyze (default: 24)
    
    Returns:
        Dictionary with CPU analysis including current_usage, average_usage, peak_usage, trend, recommendations
    """
    return tools_skills_v2.skill_analyze_cpu_usage(
        database_id=database_id,
        hours_back=hours_back
    )


@app.tool()
def skill_analyze_memory_usage(database_id: str, hours_back: int = 24) -> dict:
    """
    Analyze memory usage for a database using PerformanceAnalysisSkill (Tier 2).
    
    Args:
        database_id: Database OCID
        hours_back: Number of hours to analyze (default: 24)
    
    Returns:
        Dictionary with memory analysis including trend and recommendations
    """
    return tools_skills_v2.skill_analyze_memory_usage(
        database_id=database_id,
        hours_back=hours_back
    )


@app.tool()
def skill_analyze_io_performance(database_id: str, hours_back: int = 24) -> dict:
    """
    Analyze I/O performance for a database using PerformanceAnalysisSkill (Tier 2).
    
    Args:
        database_id: Database OCID
        hours_back: Number of hours to analyze (default: 24)
    
    Returns:
        Dictionary with I/O analysis (throughput in MB/s)
    """
    return tools_skills_v2.skill_analyze_io_performance(
        database_id=database_id,
        hours_back=hours_back
    )


@app.tool()
def skill_get_performance_summary(database_id: str, hours_back: int = 24) -> dict:
    """
    Get comprehensive performance summary using PerformanceAnalysisSkill (Tier 2).
    
    Includes CPU, memory, and I/O analysis in a single call.
    
    Args:
        database_id: Database OCID
        hours_back: Number of hours to analyze (default: 24)
    
    Returns:
        Dictionary with complete performance summary
    """
    return tools_skills_v2.skill_get_performance_summary(
        database_id=database_id,
        hours_back=hours_back
    )


@app.tool()
def skill_find_cost_opportunities(
    compartment_id: Optional[str] = None,
    min_savings_usd: float = 50.0,
    limit: int = 20
) -> dict:
    """
    Find cost-saving opportunities using CostOptimizationSkill (Tier 2).
    
    Analyzes utilization patterns to identify:
    - Rightsizing opportunities (over-provisioned databases)
    - Scheduling opportunities (dev/test databases)
    - Storage optimization
    - Unused resources
    
    Args:
        compartment_id: Filter by compartment (optional)
        min_savings_usd: Minimum monthly savings to report (default: $50)
        limit: Maximum opportunities to return (default: 20)
    
    Returns:
        Dictionary with opportunities and estimated savings
    """
    return tools_skills_v2.skill_find_cost_opportunities(
        compartment_id=compartment_id,
        min_savings_usd=min_savings_usd,
        limit=limit
    )


@app.tool()
def skill_get_savings_summary(compartment_id: Optional[str] = None) -> dict:
    """
    Get summary of all cost-saving opportunities using CostOptimizationSkill (Tier 2).
    
    Provides totals grouped by opportunity type and confidence level.
    
    Args:
        compartment_id: Filter by compartment (optional)
    
    Returns:
        Dictionary with total_opportunities, total_monthly_savings, by_type, by_confidence
    """
    return tools_skills_v2.skill_get_savings_summary(compartment_id=compartment_id)


@app.tool()
def list_programmatic_skills() -> dict:
    """
    List all available programmatic skills with metadata.
    
    Returns information about each skill including tier, category,
    response time, and available tools.
    
    Returns:
        Dictionary with list of skills and their metadata
    """
    return tools_skills_v2.list_programmatic_skills()


@app.tool()
def get_skill_recommendations(query: str) -> dict:
    """
    Get skill recommendations for a natural language query.
    
    Analyzes the query to suggest which skills/tools to use.
    
    Args:
        query: Natural language description of what you want to do
    
    Returns:
        Dictionary with recommended skills and tools
    """
    return tools_skills_v2.get_skill_recommendations(query=query)


# ============================================================================
# Health / Status
# ============================================================================

@app.tool()
def health(detail: bool = False) -> dict:
    """Health/status check for the OCI OPSI MCP server (no side effects)."""
    try:
        info = {
            "status": "ok",
            "server": "oci-opsi",
            "transport": os.getenv("MCP_TRANSPORT", os.getenv("FASTMCP_TRANSPORT", "stdio")).lower(),
            "profile": os.getenv("OCI_CLI_PROFILE", "DEFAULT"),
        }
        if detail:
            import platform
            info["python_version"] = platform.python_version()
            info["timestamp"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
        return {"content": [{"type": "text", "text": __import__("json").dumps(info, indent=2)}]}
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": str(e)}]}


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the MCP server with transport selection based on environment variables."""
    transport = os.getenv("MCP_TRANSPORT", os.getenv("FASTMCP_TRANSPORT", "stdio")).lower()
    http_host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
    http_port = int(os.getenv("MCP_HTTP_PORT", "8000"))

    logger.info(
        "Starting MCP oci-opsi server",
        extra={
            "transport": transport,
            "profile": os.getenv("OCI_CLI_PROFILE"),
            "version": "v2",
            "http_host": http_host,
            "http_port": http_port,
        },
    )

    if transport == "http":
        logger.info("Starting MCP server in HTTP mode")
        try:
            app.run(transport="http", host=http_host, port=http_port)
            return
        except (ValueError, NotImplementedError):
            logger.warning("HTTP transport not available, falling back to stdio")

    # Default: stdio transport for local usage
    try:
        app.run(transport="stdio")
    except Exception as exc:
        logger.exception("Failed to start MCP server (stdio)", exc_info=exc)
        raise


if __name__ == "__main__":
    main()
