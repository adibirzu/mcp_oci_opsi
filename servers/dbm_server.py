"""Database Management server for monitoring and administration.

This server provides tools for Oracle Cloud Infrastructure Database Management,
including AWR reports, ADDM, tablespace management, and user administration.

Follows MCP Best Practices:
- Tool annotations for hints (readOnlyHint, destructiveHint, etc.)
- Standard pagination with has_more, next_offset, total_count
- Consistent naming: dbm_{action}_{resource}
"""

from typing import Any, Dict, List, Optional, Literal
from datetime import datetime, timedelta
import logging

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolAnnotations

from ..oci_clients import get_dbm_client

logger = logging.getLogger(__name__)

MAX_PAGE_LIMIT = 100
RATE_LIMIT_HINT = "OCI DBM ~100 req/min; page with limit<=100 and backoff (2s,4s,8s) on throttling."


# Create DBM sub-server
dbm_server = FastMCP(
    name="dbm-tools",
    instructions="""
    Database Management tools provide monitoring and administration capabilities.
    Use these tools for AWR reports, ADDM analysis, tablespace management,
    user/role auditing, and SQL plan baselines.

    Performance: Operations make OCI API calls, response time depends on database size.
    Rate Limits: Subject to OCI API limits (~100/minute).
    """,
)

def _validate_limit_offset(limit: int, offset: int) -> None:
    if limit < 1 or limit > MAX_PAGE_LIMIT:
        raise ToolError(f"limit must be between 1 and {MAX_PAGE_LIMIT}")
    if offset < 0:
        raise ToolError("offset must be >= 0")


def _validate_ocid(ocid: Optional[str], field: str) -> None:
    if not ocid or not isinstance(ocid, str) or not ocid.startswith("ocid1."):
        raise ToolError(f"{field} must be a valid OCID (starting with ocid1.)")


def _paginate_with_offset(getter, limit: int, offset: int, **kwargs) -> tuple[list, dict]:
    _validate_limit_offset(limit, offset)

    results: list = []
    seen = 0
    page_token = None

    while len(results) < limit:
        remaining_needed = (offset + limit) - seen
        page_limit = max(1, min(MAX_PAGE_LIMIT, remaining_needed))
        response = getter(limit=page_limit, page=page_token, **kwargs)
        items = getattr(response, "data", []) or []

        if not items:
            break

        for item in items:
            if seen < offset:
                seen += 1
                continue
            if len(results) >= limit:
                break
            results.append(item)
            seen += 1

        page_token = getattr(response, "next_page", None) or getattr(response, "opc_next_page", None)
        if not page_token:
            break

    has_more = bool(page_token)
    pagination = {
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
        "next_offset": offset + len(results) if has_more else None,
        "total_count": seen if not has_more else None,
    }
    return results, pagination


def _raise_tool_error(context: str, error: Exception) -> None:
    logger.exception("DBM tool failed: %s", context, exc_info=error)
    raise ToolError(f"Unable to {context} right now. Please retry with a smaller scope or later.")


@dbm_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def health(ctx: Context = None) -> Dict[str, Any]:
    """Lightweight readiness check for DBM server."""
    if ctx:
        await ctx.debug("DBM health check")
    return {
        "status": "ok",
        "rate_limit_hint": RATE_LIMIT_HINT,
        "note": "No OCI calls made; safe for readiness probes.",
    }


@dbm_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def list_managed_databases(
    compartment_id: str,
    management_option: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    format: Literal["json", "markdown"] = "json",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List managed databases in a compartment.

    Args:
        compartment_id: Compartment OCID
        management_option: Filter by management option (BASIC, ADVANCED)
        limit: Maximum results per page (default 50)
        offset: Number of results to skip for pagination
        format: Output format - "json" (default) or "markdown"

    Returns:
        List of managed databases with pagination metadata

    Examples:
        - list_managed_databases(compartment_id="ocid1...") - List all
        - list_managed_databases(compartment_id="ocid1...", management_option="ADVANCED") - Filter by management option
        - list_managed_databases(compartment_id="ocid1...", offset=50, limit=50) - Page 2
    """
    if ctx:
        await ctx.info("Listing managed databases...")

    try:
        _validate_ocid(compartment_id, "compartment_id")
        _validate_limit_offset(limit, offset)
        dbm_client = get_dbm_client()

        kwargs = {"compartment_id": compartment_id}
        if management_option:
            kwargs["management_option"] = management_option

        paginated_results, pagination = _paginate_with_offset(
            dbm_client.list_managed_databases,
            limit=limit,
            offset=offset,
            **kwargs,
        )

        databases = []
        for db in paginated_results:
            databases.append({
                "id": db.id,
                "name": db.name,
                "database_type": getattr(db, "database_type", None),
                "database_sub_type": getattr(db, "database_sub_type", None),
                "deployment_type": getattr(db, "deployment_type", None),
                "management_option": getattr(db, "management_option", None),
                "workload_type": getattr(db, "workload_type", None),
                "time_created": str(getattr(db, "time_created", None)),
            })

        data = {
            "databases": databases,
            "count": len(databases),
            "pagination": pagination,
            "rate_limit_hint": RATE_LIMIT_HINT,
        }

        if format == "markdown":
            total_display = pagination["total_count"] if pagination["total_count"] is not None else "unknown"
            md = f"""## Managed Databases

**Total:** {total_display}
**Showing:** {offset + 1} - {offset + len(databases)}

| Name | Type | Management | Workload |
|------|------|------------|----------|
"""
            for db in databases:
                md += f"| {db['name']} | {db['database_type'] or 'N/A'} | {db['management_option'] or 'N/A'} | {db['workload_type'] or 'N/A'} |\n"

            if data["pagination"]["has_more"]:
                md += f"\n*Use offset={data['pagination']['next_offset']} to see more (limit {MAX_PAGE_LIMIT})*"

            return {"markdown": md, "data": data}

        return data

    except ToolError:
        raise
    except Exception as e:
        _raise_tool_error("list managed databases", e)


@dbm_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def get_tablespace_usage(
    managed_database_id: str,
    format: Literal["json", "markdown"] = "json",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get tablespace usage for a managed database.

    Shows space allocation and utilization for all tablespaces.

    Args:
        managed_database_id: Managed database OCID
        format: Output format - "json" (default) or "markdown"

    Returns:
        Tablespace usage with size, used, and free space

    Examples:
        - get_tablespace_usage(managed_database_id="ocid1...") - Get JSON
        - get_tablespace_usage(managed_database_id="ocid1...", format="markdown") - Human-readable
        - Use to identify tablespaces approaching capacity (warnings list)
    """
    if ctx:
        await ctx.info("Getting tablespace usage...")

    try:
        dbm_client = get_dbm_client()

        response = dbm_client.list_tablespaces(
            managed_database_id=managed_database_id
        )

        tablespaces = []
        if hasattr(response.data, 'items'):
            for ts in response.data.items:
                # Calculate usage percentage
                size = getattr(ts, 'allocated_size_kb', 0) or 0
                used = getattr(ts, 'used_size_kb', 0) or 0
                usage_pct = (used / size * 100) if size > 0 else 0

                tablespaces.append({
                    "name": ts.name,
                    "type": getattr(ts, 'type', None),
                    "status": getattr(ts, 'status', None),
                    "allocated_size_kb": size,
                    "used_size_kb": used,
                    "free_size_kb": size - used,
                    "usage_percent": round(usage_pct, 2),
                    "is_auto_extensible": getattr(ts, 'is_auto_extensible', None),
                })

        # Sort by usage percentage descending
        tablespaces.sort(key=lambda x: x['usage_percent'], reverse=True)

        # Calculate summary
        total_allocated = sum(t['allocated_size_kb'] for t in tablespaces)
        total_used = sum(t['used_size_kb'] for t in tablespaces)

        data = {
            "tablespaces": tablespaces,
            "count": len(tablespaces),
            "summary": {
                "total_allocated_gb": round(total_allocated / 1024 / 1024, 2),
                "total_used_gb": round(total_used / 1024 / 1024, 2),
                "total_free_gb": round((total_allocated - total_used) / 1024 / 1024, 2),
                "overall_usage_percent": round(total_used / total_allocated * 100, 2) if total_allocated > 0 else 0,
            },
            "warnings": [t['name'] for t in tablespaces if t['usage_percent'] > 80],
        }

        if format == "markdown":
            summary = data["summary"]
            md = f"""## Tablespace Usage

**Total Allocated:** {summary['total_allocated_gb']} GB
**Total Used:** {summary['total_used_gb']} GB
**Total Free:** {summary['total_free_gb']} GB
**Overall Usage:** {summary['overall_usage_percent']}%

| Tablespace | Status | Allocated (KB) | Used (KB) | Usage % |
|------------|--------|----------------|-----------|---------|
"""
            for ts in tablespaces[:20]:  # Limit for readability
                status_icon = "⚠️ " if ts['usage_percent'] > 80 else ""
                md += f"| {status_icon}{ts['name']} | {ts['status'] or 'N/A'} | {ts['allocated_size_kb']:,} | {ts['used_size_kb']:,} | {ts['usage_percent']}% |\n"

            if data["warnings"]:
                md += f"\n**Warnings (>80% used):** {', '.join(data['warnings'])}"

            return {"markdown": md, "data": data}

        return data

    except Exception as e:
        raise ToolError(f"Failed to get tablespace usage: {e}")


@dbm_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def list_awr_snapshots(
    managed_database_id: str,
    awr_db_id: str,
    days_back: int = 7,
    limit: int = 50,
    offset: int = 0,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List AWR snapshots for a database.

    Args:
        managed_database_id: Managed database OCID
        awr_db_id: AWR database ID (DBID)
        days_back: Number of days of snapshots (default 7)
        limit: Maximum results per page (default 50)
        offset: Number of results to skip for pagination

    Returns:
        List of AWR snapshots with IDs and timestamps

    Examples:
        - list_awr_snapshots(managed_database_id="ocid1...", awr_db_id="123456") - Last 7 days
        - list_awr_snapshots(..., days_back=30) - Last 30 days
        - Use snapshot IDs for get_awr_report() or get_addm_report()
    """
    if ctx:
        await ctx.info("Listing AWR snapshots...")

    try:
        dbm_client = get_dbm_client()

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)

        response = dbm_client.list_awr_db_snapshots(
            managed_database_id=managed_database_id,
            awr_db_id=awr_db_id,
            time_greater_than_or_equal_to=start_time,
            time_less_than_or_equal_to=end_time,
        )

        all_snapshots = []
        if hasattr(response.data, 'items'):
            for snap in response.data.items:
                all_snapshots.append({
                    "snapshot_id": snap.snapshot_id,
                    "instance_number": getattr(snap, 'instance_number', None),
                    "time_db_startup": str(getattr(snap, 'time_db_startup', None)),
                    "time_begin": str(getattr(snap, 'time_begin', None)),
                    "time_end": str(getattr(snap, 'time_end', None)),
                })

        total_count = len(all_snapshots)
        paginated = all_snapshots[offset:offset + limit]

        return {
            "snapshots": paginated,
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
        raise ToolError(f"Failed to list AWR snapshots: {e}")


@dbm_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def get_awr_report(
    managed_database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
    report_format: str = "HTML",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Generate AWR report for a snapshot range.

    Args:
        managed_database_id: Managed database OCID
        awr_db_id: AWR database ID
        begin_snapshot_id: Starting snapshot ID
        end_snapshot_id: Ending snapshot ID
        report_format: HTML or TEXT (default HTML)

    Returns:
        AWR report content

    Examples:
        - get_awr_report(..., begin_snapshot_id=100, end_snapshot_id=110) - HTML report
        - get_awr_report(..., report_format="TEXT") - Text format report
        - First use list_awr_snapshots() to find valid snapshot IDs
    """
    if ctx:
        await ctx.info(f"Generating AWR report ({begin_snapshot_id} to {end_snapshot_id})...")
        await ctx.report_progress(progress=10, total=100)

    try:
        dbm_client = get_dbm_client()

        response = dbm_client.get_awr_db_report(
            managed_database_id=managed_database_id,
            awr_db_id=awr_db_id,
            begin_snapshot_id=begin_snapshot_id,
            end_snapshot_id=end_snapshot_id,
            report_format=report_format,
        )

        if ctx:
            await ctx.report_progress(progress=100, total=100)

        return {
            "report": response.data.content if hasattr(response.data, 'content') else str(response.data),
            "format": report_format,
            "snapshot_range": {
                "begin": begin_snapshot_id,
                "end": end_snapshot_id,
            },
        }

    except Exception as e:
        raise ToolError(f"Failed to generate AWR report: {e}")


@dbm_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=False,  # Creates a task
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def get_addm_report(
    managed_database_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Generate ADDM report for a snapshot range.

    ADDM (Automatic Database Diagnostic Monitor) provides
    performance recommendations based on AWR data.

    Args:
        managed_database_id: Managed database OCID
        begin_snapshot_id: Starting snapshot ID
        end_snapshot_id: Ending snapshot ID

    Returns:
        ADDM findings and recommendations

    Examples:
        - get_addm_report(managed_database_id="ocid1...", begin_snapshot_id=100, end_snapshot_id=110)
        - Use after identifying performance issues in AWR reports
        - First use list_awr_snapshots() to find valid snapshot IDs
    """
    if ctx:
        await ctx.info("Generating ADDM report...")
        await ctx.report_progress(progress=20, total=100)

    try:
        dbm_client = get_dbm_client()

        response = dbm_client.run_addm_task(
            managed_database_id=managed_database_id,
            run_addm_task_details={
                "begin_snapshot_id": begin_snapshot_id,
                "end_snapshot_id": end_snapshot_id,
            },
        )

        if ctx:
            await ctx.report_progress(progress=100, total=100)

        return {
            "addm_task": response.data if hasattr(response, 'data') else None,
            "snapshot_range": {
                "begin": begin_snapshot_id,
                "end": end_snapshot_id,
            },
        }

    except Exception as e:
        raise ToolError(f"Failed to generate ADDM report: {e}")


@dbm_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def list_users(
    managed_database_id: str,
    name_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    format: Literal["json", "markdown"] = "json",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List database users for security auditing.

    Args:
        managed_database_id: Managed database OCID
        name_filter: Filter by username (partial match)
        limit: Maximum results per page (default 100)
        offset: Number of results to skip for pagination
        format: Output format - "json" (default) or "markdown"

    Returns:
        List of users with status and profile info

    Examples:
        - list_users(managed_database_id="ocid1...") - All users
        - list_users(managed_database_id="ocid1...", name_filter="APP") - Filter by name
        - list_users(..., format="markdown") - Human-readable table
    """
    if ctx:
        await ctx.info("Listing database users...")

    try:
        dbm_client = get_dbm_client()

        kwargs = {"managed_database_id": managed_database_id, "limit": 1000}
        if name_filter:
            kwargs["name"] = name_filter

        response = dbm_client.list_users(**kwargs)

        all_users = []
        if hasattr(response.data, 'items'):
            for user in response.data.items:
                all_users.append({
                    "name": user.name,
                    "status": getattr(user, 'status', None),
                    "profile": getattr(user, 'profile', None),
                    "time_created": str(getattr(user, 'time_created', None)),
                    "time_expiring": str(getattr(user, 'time_expiring', None)),
                    "default_tablespace": getattr(user, 'default_tablespace', None),
                    "temp_tablespace": getattr(user, 'temp_tablespace', None),
                })

        total_count = len(all_users)
        paginated = all_users[offset:offset + limit]

        data = {
            "users": paginated,
            "count": len(paginated),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total_count": total_count,
                "has_more": offset + limit < total_count,
                "next_offset": offset + limit if offset + limit < total_count else None,
            },
        }

        if format == "markdown":
            md = f"""## Database Users

**Total:** {total_count}
**Showing:** {offset + 1} - {offset + len(paginated)}

| Name | Status | Profile | Default Tablespace |
|------|--------|---------|-------------------|
"""
            for user in paginated:
                md += f"| {user['name']} | {user['status'] or 'N/A'} | {user['profile'] or 'N/A'} | {user['default_tablespace'] or 'N/A'} |\n"

            if data["pagination"]["has_more"]:
                md += f"\n*Use offset={data['pagination']['next_offset']} to see more*"

            return {"markdown": md, "data": data}

        return data

    except Exception as e:
        raise ToolError(f"Failed to list users: {e}")


@dbm_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def list_roles(
    managed_database_id: str,
    limit: int = 100,
    offset: int = 0,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List database roles for security auditing.

    Args:
        managed_database_id: Managed database OCID
        limit: Maximum results per page (default 100)
        offset: Number of results to skip for pagination

    Returns:
        List of roles with authentication type

    Examples:
        - list_roles(managed_database_id="ocid1...") - All roles
        - list_roles(managed_database_id="ocid1...", limit=20) - First 20 roles
        - Use for security auditing and privilege analysis
    """
    if ctx:
        await ctx.info("Listing database roles...")

    try:
        dbm_client = get_dbm_client()

        response = dbm_client.list_roles(
            managed_database_id=managed_database_id,
            limit=1000,
        )

        all_roles = []
        if hasattr(response.data, 'items'):
            for role in response.data.items:
                all_roles.append({
                    "name": role.name,
                    "authentication_type": getattr(role, 'authentication_type', None),
                })

        total_count = len(all_roles)
        paginated = all_roles[offset:offset + limit]

        return {
            "roles": paginated,
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
        raise ToolError(f"Failed to list roles: {e}")


@dbm_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def list_sql_plan_baselines(
    managed_database_id: str,
    sql_handle: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List SQL plan baselines for plan stability.

    Args:
        managed_database_id: Managed database OCID
        sql_handle: Filter by SQL handle
        is_enabled: Filter by enabled status
        limit: Maximum results per page (default 50)
        offset: Number of results to skip for pagination

    Returns:
        List of SQL plan baselines with pagination

    Examples:
        - list_sql_plan_baselines(managed_database_id="ocid1...") - All baselines
        - list_sql_plan_baselines(..., is_enabled=True) - Only enabled plans
        - list_sql_plan_baselines(..., sql_handle="SQL_123") - Specific SQL
    """
    if ctx:
        await ctx.info("Listing SQL plan baselines...")

    try:
        dbm_client = get_dbm_client()

        kwargs = {"managed_database_id": managed_database_id, "limit": 1000}
        if sql_handle:
            kwargs["sql_handle"] = sql_handle
        if is_enabled is not None:
            kwargs["is_enabled"] = is_enabled

        response = dbm_client.list_sql_plan_baselines(**kwargs)

        all_baselines = []
        if hasattr(response.data, 'items'):
            for baseline in response.data.items:
                all_baselines.append({
                    "plan_name": baseline.plan_name,
                    "sql_handle": getattr(baseline, 'sql_handle', None),
                    "sql_text": getattr(baseline, 'sql_text', None)[:100] + "..." if getattr(baseline, 'sql_text', None) else None,
                    "origin": getattr(baseline, 'origin', None),
                    "is_enabled": getattr(baseline, 'is_enabled', None),
                    "is_accepted": getattr(baseline, 'is_accepted', None),
                    "is_fixed": getattr(baseline, 'is_fixed', None),
                    "time_created": str(getattr(baseline, 'time_created', None)),
                })

        total_count = len(all_baselines)
        paginated = all_baselines[offset:offset + limit]

        return {
            "baselines": paginated,
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
        raise ToolError(f"Failed to list SQL plan baselines: {e}")


@dbm_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def get_database_fleet_health_metrics(
    compartment_id: str,
    compare_baseline_time: Optional[str] = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get fleet-wide health metrics for all managed databases.

    Args:
        compartment_id: Compartment OCID
        compare_baseline_time: Baseline time for comparison (ISO format)

    Returns:
        Fleet health metrics summary

    Examples:
        - get_database_fleet_health_metrics(compartment_id="ocid1...") - Current metrics
        - get_database_fleet_health_metrics(..., compare_baseline_time="2025-01-01T00:00:00Z")
        - Use to get overall health status of all managed databases
    """
    if ctx:
        await ctx.info("Getting fleet health metrics...")

    try:
        dbm_client = get_dbm_client()

        kwargs = {"compartment_id": compartment_id}
        if compare_baseline_time:
            kwargs["compare_baseline_time"] = compare_baseline_time

        response = dbm_client.get_database_fleet_health_metrics(**kwargs)

        return {
            "fleet_metrics": response.data if hasattr(response, 'data') else None,
        }

    except Exception as e:
        raise ToolError(f"Failed to get fleet health metrics: {e}")


# Resources for DBM data
@dbm_server.resource("resource://database/{database_id}/tablespaces")
async def tablespaces_resource(database_id: str) -> Dict[str, Any]:
    """Tablespace usage as a resource."""
    try:
        dbm_client = get_dbm_client()
        response = dbm_client.list_tablespaces(managed_database_id=database_id)
        tablespaces = []
        if hasattr(response.data, 'items'):
            for ts in response.data.items:
                tablespaces.append({
                    "name": ts.name,
                    "status": getattr(ts, 'status', None),
                    "allocated_size_kb": getattr(ts, 'allocated_size_kb', 0),
                    "used_size_kb": getattr(ts, 'used_size_kb', 0),
                })
        return {"tablespaces": tablespaces}
    except Exception:
        return {"error": "Failed to get tablespaces"}


@dbm_server.resource("resource://database/{database_id}/users")
async def users_resource(database_id: str) -> Dict[str, Any]:
    """Database users as a resource."""
    try:
        dbm_client = get_dbm_client()
        response = dbm_client.list_users(managed_database_id=database_id)
        users = []
        if hasattr(response.data, 'items'):
            for user in response.data.items:
                users.append({
                    "name": user.name,
                    "status": getattr(user, 'status', None),
                })
        return {"users": users}
    except Exception:
        return {"error": "Failed to get users"}
