"""Operations Insights server for database analytics and monitoring.

This server provides tools for Oracle Cloud Infrastructure Operations Insights,
including SQL analytics, capacity planning, and ADDM findings.

Follows MCP Best Practices:
- Tool annotations for hints (readOnlyHint, destructiveHint, etc.)
- Standard pagination with has_more, next_offset, total_count
- Consistent naming: opsi_{action}_{resource}
- Examples in docstrings

Rate Limits: OCI API limits apply (~100 requests/minute)
"""

from typing import Any, Dict, List, Optional, Literal
from datetime import datetime, timedelta

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolAnnotations

from ..oci_clients import get_opsi_client, list_all, extract_region_from_ocid


# Create OPSI sub-server
opsi_server = FastMCP(
    name="opsi-tools",
    instructions="""
    Operations Insights tools provide database analytics and monitoring.
    Use these tools for SQL performance analysis, capacity planning,
    ADDM findings, and fleet-wide insights.

    Rate Limits: OCI API limits apply (~100 requests/minute).
    All tools make API calls to OCI Operations Insights service.
    """,
)


def _get_time_range(days_back: int = 7) -> tuple:
    """Get time range for OPSI queries."""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days_back)
    return start_time, end_time


@opsi_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def list_database_insights(
    compartment_id: str,
    database_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    format: Literal["json", "markdown"] = "json",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List database insights in a compartment.

    Args:
        compartment_id: Compartment OCID
        database_type: Filter by type (e.g., "EXTERNAL-NONCDB", "ATP-D", "ADW-D")
        status: Filter by status (e.g., "ENABLED", "DISABLED")
        limit: Maximum results per page (default 50, max 100)
        offset: Number of results to skip for pagination
        format: Output format - "json" (default) or "markdown"

    Returns:
        List of database insights with pagination metadata

    Examples:
        - list_database_insights(compartment_id="ocid1...") - List all in compartment
        - list_database_insights(compartment_id="ocid1...", status="ENABLED") - Only enabled
        - list_database_insights(compartment_id="ocid1...", database_type="ATP-D") - Only ATP
    """
    if ctx:
        await ctx.info(f"Listing database insights in compartment")

    try:
        opsi_client = get_opsi_client()

        kwargs = {"compartment_id": compartment_id, "limit": min(limit + offset, 1000)}
        if database_type:
            kwargs["database_type"] = [database_type]
        if status:
            kwargs["status"] = [status]

        all_results = list_all(opsi_client.list_database_insights, **kwargs)
        total_count = len(all_results)

        # Apply pagination
        paginated = all_results[offset:offset + limit]

        databases = []
        for db in paginated:
            databases.append({
                "id": db.id,
                "database_id": getattr(db, "database_id", None),
                "database_name": getattr(db, "database_name", None),
                "database_display_name": getattr(db, "database_display_name", None),
                "database_type": getattr(db, "database_type", None),
                "database_version": getattr(db, "database_version", None),
                "status": db.status,
                "lifecycle_state": db.lifecycle_state,
            })

        data = {
            "databases": databases,
            "count": len(databases),
            "compartment_id": compartment_id,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total_count": total_count,
                "has_more": offset + limit < total_count,
                "next_offset": offset + limit if offset + limit < total_count else None,
            },
        }

        if format == "markdown":
            md = f"""## Database Insights

**Compartment:** `{compartment_id[:30]}...`
**Total:** {total_count} | **Showing:** {offset + 1} - {offset + len(databases)}

| Name | Type | Status | Version |
|------|------|--------|---------|
"""
            for db in databases:
                md += f"| {db.get('database_name', 'N/A')} | {db.get('database_type', 'N/A')} | {db.get('status', 'N/A')} | {db.get('database_version', 'N/A')} |\n"

            if data["pagination"]["has_more"]:
                md += f"\n*Use offset={data['pagination']['next_offset']} for next page*"

            return {"markdown": md, "data": data}

        return data

    except Exception as e:
        raise ToolError(f"Failed to list database insights: {e}")


@opsi_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def summarize_sql_insights(
    compartment_id: str,
    database_id: Optional[str] = None,
    days_back: int = 7,
    database_time_pct_greater_than: float = 1.0,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get SQL insights and anomalies for databases.

    Identifies SQL statements with performance anomalies, degradation,
    or unusual behavior patterns.

    Args:
        compartment_id: Compartment OCID
        database_id: Optional specific database insight ID
        days_back: Number of days to analyze (default 7)
        database_time_pct_greater_than: Filter to high-impact SQL (default 1.0%)

    Returns:
        SQL insights with anomalies and trends

    Examples:
        - summarize_sql_insights(compartment_id="ocid1...") - All SQL insights
        - summarize_sql_insights(compartment_id="ocid1...", days_back=30) - Last 30 days
        - summarize_sql_insights(compartment_id="ocid1...", database_id="ocid1...") - Specific DB
    """
    if ctx:
        await ctx.info("Analyzing SQL insights for anomalies...")

    try:
        opsi_client = get_opsi_client()
        start_time, end_time = _get_time_range(days_back)

        kwargs = {
            "compartment_id": compartment_id,
            "time_interval_start": start_time,
            "time_interval_end": end_time,
            "database_time_pct_greater_than": database_time_pct_greater_than,
        }

        if database_id:
            kwargs["database_id"] = [database_id]

        response = opsi_client.summarize_sql_insights(**kwargs)

        insights = []
        if hasattr(response.data, 'inventory'):
            inventory = response.data.inventory
            insights.append({
                "total_sql": getattr(inventory, 'total_sql', 0),
                "sql_analyzed": getattr(inventory, 'sql_analyzed', 0),
                "insights": getattr(inventory, 'insights', []),
            })

        return {
            "insights": insights,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days_back,
            },
            "filter": {
                "database_time_pct_threshold": database_time_pct_greater_than,
            },
        }

    except Exception as e:
        raise ToolError(f"Failed to get SQL insights: {e}")


@opsi_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def summarize_sql_plan_insights(
    compartment_id: str,
    sql_identifier: str,
    days_back: int = 7,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Analyze SQL execution plan insights for a specific SQL statement.

    Shows plan changes, performance comparison across plans, and
    plan stability information.

    Args:
        compartment_id: Compartment OCID
        sql_identifier: SQL ID to analyze
        days_back: Number of days to analyze

    Returns:
        Plan insights including changes and performance comparison

    Examples:
        - summarize_sql_plan_insights(compartment_id="ocid1...", sql_identifier="abc123")
        - summarize_sql_plan_insights(..., days_back=30) - Analyze last 30 days
    """
    if ctx:
        await ctx.info(f"Analyzing SQL plan insights for {sql_identifier}")

    try:
        opsi_client = get_opsi_client()
        start_time, end_time = _get_time_range(days_back)

        response = opsi_client.summarize_sql_plan_insights(
            compartment_id=compartment_id,
            sql_identifier=sql_identifier,
            time_interval_start=start_time,
            time_interval_end=end_time,
        )

        return {
            "sql_identifier": sql_identifier,
            "insights": response.data if hasattr(response, 'data') else None,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
        }

    except Exception as e:
        raise ToolError(f"Failed to get SQL plan insights: {e}")


@opsi_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def summarize_addm_db_findings(
    compartment_id: str,
    database_id: Optional[str] = None,
    days_back: int = 7,
    limit: int = 50,
    offset: int = 0,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get ADDM (Automatic Database Diagnostic Monitor) findings.

    Provides fleet-wide ADDM recommendations for performance issues,
    resource bottlenecks, and configuration problems.

    Args:
        compartment_id: Compartment OCID
        database_id: Optional specific database
        days_back: Number of days to analyze
        limit: Maximum findings to return
        offset: Number of findings to skip

    Returns:
        ADDM findings with recommendations, impact, and pagination

    Examples:
        - summarize_addm_db_findings(compartment_id="ocid1...") - All findings
        - summarize_addm_db_findings(compartment_id="ocid1...", database_id="ocid1...") - Specific DB
        - summarize_addm_db_findings(compartment_id="ocid1...", days_back=30) - Last 30 days
    """
    if ctx:
        await ctx.info("Getting ADDM findings...")

    try:
        opsi_client = get_opsi_client()
        start_time, end_time = _get_time_range(days_back)

        kwargs = {
            "compartment_id": compartment_id,
            "time_interval_start": start_time,
            "time_interval_end": end_time,
        }

        if database_id:
            kwargs["database_id"] = [database_id]

        response = opsi_client.summarize_addm_db_findings(**kwargs)

        all_findings = []
        if hasattr(response.data, 'items'):
            for item in response.data.items:
                all_findings.append({
                    "finding_id": getattr(item, 'id', None),
                    "category": getattr(item, 'category_name', None),
                    "finding": getattr(item, 'finding_name', None),
                    "impact": getattr(item, 'impact_percent', None),
                    "recommendation": getattr(item, 'recommendation', None),
                })

        total_count = len(all_findings)
        paginated = all_findings[offset:offset + limit]

        return {
            "findings": paginated,
            "count": len(paginated),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total_count": total_count,
                "has_more": offset + limit < total_count,
                "next_offset": offset + limit if offset + limit < total_count else None,
            },
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
        }

    except Exception as e:
        raise ToolError(f"Failed to get ADDM findings: {e}")


@opsi_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def get_database_resource_forecast(
    compartment_id: str,
    resource_metric: str = "CPU",
    forecast_days: int = 30,
    database_insight_id: Optional[str] = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get ML-based resource forecast for databases.

    Predicts future resource utilization based on historical patterns.

    Args:
        compartment_id: Compartment OCID
        resource_metric: Metric to forecast (CPU, STORAGE, MEMORY, IO)
        forecast_days: Days to forecast ahead (default 30)
        database_insight_id: Optional specific database

    Returns:
        Resource forecast with predictions and trends

    Examples:
        - get_database_resource_forecast(compartment_id="ocid1...") - CPU forecast
        - get_database_resource_forecast(..., resource_metric="STORAGE") - Storage forecast
        - get_database_resource_forecast(..., forecast_days=90) - 90-day forecast
    """
    if ctx:
        await ctx.info(f"Generating {resource_metric} forecast for {forecast_days} days...")

    try:
        opsi_client = get_opsi_client()
        start_time, end_time = _get_time_range(30)  # Need history for forecast

        kwargs = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": start_time,
            "time_interval_end": end_time,
            "forecast_days": forecast_days,
        }

        if database_insight_id:
            kwargs["database_insight_id"] = database_insight_id

        if ctx:
            await ctx.report_progress(progress=30, total=100)

        response = opsi_client.summarize_database_insight_resource_forecast_trend(**kwargs)

        if ctx:
            await ctx.report_progress(progress=100, total=100)

        return {
            "resource_metric": resource_metric,
            "forecast_days": forecast_days,
            "forecast": response.data if hasattr(response, 'data') else None,
            "historical_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
        }

    except Exception as e:
        raise ToolError(f"Failed to get resource forecast: {e}")


@opsi_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def get_database_capacity_trend(
    compartment_id: str,
    resource_metric: str = "CPU",
    days_back: int = 30,
    database_insight_id: Optional[str] = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get historical capacity trend for databases.

    Shows resource utilization patterns over time.

    Args:
        compartment_id: Compartment OCID
        resource_metric: Metric to analyze (CPU, STORAGE, MEMORY, IO)
        days_back: Days of history to retrieve
        database_insight_id: Optional specific database

    Returns:
        Capacity trend data with historical utilization

    Examples:
        - get_database_capacity_trend(compartment_id="ocid1...") - CPU trend
        - get_database_capacity_trend(..., resource_metric="MEMORY") - Memory trend
        - get_database_capacity_trend(..., days_back=90) - 90-day history
    """
    if ctx:
        await ctx.info(f"Getting {resource_metric} capacity trend...")

    try:
        opsi_client = get_opsi_client()
        start_time, end_time = _get_time_range(days_back)

        kwargs = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": start_time,
            "time_interval_end": end_time,
        }

        if database_insight_id:
            kwargs["database_insight_id"] = database_insight_id

        response = opsi_client.summarize_database_insight_resource_capacity_trend(**kwargs)

        return {
            "resource_metric": resource_metric,
            "trend": response.data if hasattr(response, 'data') else None,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days_back,
            },
        }

    except Exception as e:
        raise ToolError(f"Failed to get capacity trend: {e}")


@opsi_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def list_host_insights(
    compartment_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    format: Literal["json", "markdown"] = "json",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List host insights in a compartment.

    Args:
        compartment_id: Compartment OCID
        status: Filter by status (ENABLED, DISABLED)
        limit: Maximum results per page (default 50)
        offset: Number of results to skip for pagination
        format: Output format - "json" (default) or "markdown"

    Returns:
        List of host insights with pagination metadata

    Examples:
        - list_host_insights(compartment_id="ocid1...") - All hosts
        - list_host_insights(compartment_id="ocid1...", status="ENABLED") - Only enabled
        - list_host_insights(compartment_id="ocid1...", limit=10, offset=10) - Page 2
    """
    if ctx:
        await ctx.info("Listing host insights...")

    try:
        opsi_client = get_opsi_client()

        kwargs = {"compartment_id": compartment_id, "limit": min(limit + offset, 1000)}
        if status:
            kwargs["status"] = [status]

        all_results = list_all(opsi_client.list_host_insights, **kwargs)
        total_count = len(all_results)
        paginated = all_results[offset:offset + limit]

        hosts = []
        for host in paginated:
            hosts.append({
                "id": host.id,
                "host_name": getattr(host, "host_name", None),
                "host_display_name": getattr(host, "host_display_name", None),
                "host_type": getattr(host, "host_type", None),
                "platform_type": getattr(host, "platform_type", None),
                "status": host.status,
                "lifecycle_state": host.lifecycle_state,
            })

        data = {
            "hosts": hosts,
            "count": len(hosts),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total_count": total_count,
                "has_more": offset + limit < total_count,
                "next_offset": offset + limit if offset + limit < total_count else None,
            },
        }

        if format == "markdown":
            md = f"""## Host Insights

**Total:** {total_count} | **Showing:** {offset + 1} - {offset + len(hosts)}

| Host Name | Type | Platform | Status |
|-----------|------|----------|--------|
"""
            for host in hosts:
                md += f"| {host.get('host_name', 'N/A')} | {host.get('host_type', 'N/A')} | {host.get('platform_type', 'N/A')} | {host.get('status', 'N/A')} |\n"

            if data["pagination"]["has_more"]:
                md += f"\n*Use offset={data['pagination']['next_offset']} for next page*"

            return {"markdown": md, "data": data}

        return data

    except Exception as e:
        raise ToolError(f"Failed to list host insights: {e}")


@opsi_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def get_host_resource_statistics(
    compartment_id: str,
    resource_metric: str = "CPU",
    limit: int = 50,
    offset: int = 0,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get resource statistics for all hosts.

    Args:
        compartment_id: Compartment OCID
        resource_metric: Metric (CPU, MEMORY, STORAGE, NETWORK)
        limit: Maximum results per page
        offset: Number of results to skip

    Returns:
        Host resource statistics with utilization and pagination

    Examples:
        - get_host_resource_statistics(compartment_id="ocid1...") - CPU stats
        - get_host_resource_statistics(..., resource_metric="MEMORY") - Memory stats
        - get_host_resource_statistics(..., limit=10) - Top 10 hosts
    """
    if ctx:
        await ctx.info(f"Getting host {resource_metric} statistics...")

    try:
        opsi_client = get_opsi_client()
        start_time, end_time = _get_time_range(7)

        response = opsi_client.summarize_host_insight_resource_statistics(
            compartment_id=compartment_id,
            resource_metric=resource_metric,
            time_interval_start=start_time,
            time_interval_end=end_time,
        )

        all_items = []
        if hasattr(response.data, 'items'):
            for item in response.data.items:
                all_items.append({
                    "host_name": getattr(item, 'host_name', None),
                    "usage": getattr(item, 'usage', None),
                    "capacity": getattr(item, 'capacity', None),
                    "utilization_percent": getattr(item, 'utilization_percent', None),
                })

        total_count = len(all_items)
        paginated = all_items[offset:offset + limit]

        return {
            "resource_metric": resource_metric,
            "hosts": paginated,
            "count": len(paginated),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total_count": total_count,
                "has_more": offset + limit < total_count,
                "next_offset": offset + limit if offset + limit < total_count else None,
            },
        }

    except Exception as e:
        raise ToolError(f"Failed to get host statistics: {e}")


# Resource for OPSI summary
@opsi_server.resource("resource://opsi/summary/{compartment_id}")
async def opsi_summary_resource(compartment_id: str) -> Dict[str, Any]:
    """Operations Insights summary for a compartment."""
    try:
        opsi_client = get_opsi_client()
        response = opsi_client.get_operations_insights_warehouse_resource_usage_summary(
            compartment_id=compartment_id
        )
        return {"summary": response.data if hasattr(response, 'data') else None}
    except Exception:
        return {"error": "Failed to get OPSI summary"}
