"""Database Management server for monitoring and administration.

This server provides tools for Oracle Cloud Infrastructure Database Management,
including AWR reports, ADDM, tablespace management, and user administration.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError

from ..oci_clients import get_dbm_client, list_all


# Create DBM sub-server
dbm_server = FastMCP(
    name="dbm-tools",
    instructions="""
    Database Management tools provide monitoring and administration capabilities.
    Use these tools for AWR reports, ADDM analysis, tablespace management,
    user/role auditing, and SQL plan baselines.
    """,
)


@dbm_server.tool
async def list_managed_databases(
    compartment_id: str,
    management_option: Optional[str] = None,
    limit: int = 50,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List managed databases in a compartment.

    Args:
        compartment_id: Compartment OCID
        management_option: Filter by management option (BASIC, ADVANCED)
        limit: Maximum results

    Returns:
        List of managed databases with details
    """
    if ctx:
        await ctx.info("Listing managed databases...")

    try:
        dbm_client = get_dbm_client()

        kwargs = {"compartment_id": compartment_id, "limit": limit}
        if management_option:
            kwargs["management_option"] = management_option

        results = list_all(dbm_client.list_managed_databases, **kwargs)

        databases = []
        for db in results[:limit]:
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

        return {
            "databases": databases,
            "count": len(databases),
        }

    except Exception as e:
        raise ToolError(f"Failed to list managed databases: {e}")


@dbm_server.tool
async def get_tablespace_usage(
    managed_database_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get tablespace usage for a managed database.

    Shows space allocation and utilization for all tablespaces.

    Args:
        managed_database_id: Managed database OCID

    Returns:
        Tablespace usage with size, used, and free space
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

        return {
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

    except Exception as e:
        raise ToolError(f"Failed to get tablespace usage: {e}")


@dbm_server.tool
async def list_awr_snapshots(
    managed_database_id: str,
    awr_db_id: str,
    days_back: int = 7,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List AWR snapshots for a database.

    Args:
        managed_database_id: Managed database OCID
        awr_db_id: AWR database ID (DBID)
        days_back: Number of days of snapshots

    Returns:
        List of AWR snapshots with IDs and timestamps
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

        snapshots = []
        if hasattr(response.data, 'items'):
            for snap in response.data.items:
                snapshots.append({
                    "snapshot_id": snap.snapshot_id,
                    "instance_number": getattr(snap, 'instance_number', None),
                    "time_db_startup": str(getattr(snap, 'time_db_startup', None)),
                    "time_begin": str(getattr(snap, 'time_begin', None)),
                    "time_end": str(getattr(snap, 'time_end', None)),
                })

        return {
            "snapshots": snapshots,
            "count": len(snapshots),
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
        }

    except Exception as e:
        raise ToolError(f"Failed to list AWR snapshots: {e}")


@dbm_server.tool
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
        report_format: HTML or TEXT

    Returns:
        AWR report content
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


@dbm_server.tool
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


@dbm_server.tool
async def list_users(
    managed_database_id: str,
    name_filter: Optional[str] = None,
    limit: int = 100,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List database users for security auditing.

    Args:
        managed_database_id: Managed database OCID
        name_filter: Filter by username (partial match)
        limit: Maximum results

    Returns:
        List of users with status and profile info
    """
    if ctx:
        await ctx.info("Listing database users...")

    try:
        dbm_client = get_dbm_client()

        kwargs = {"managed_database_id": managed_database_id, "limit": limit}
        if name_filter:
            kwargs["name"] = name_filter

        response = dbm_client.list_users(**kwargs)

        users = []
        if hasattr(response.data, 'items'):
            for user in response.data.items:
                users.append({
                    "name": user.name,
                    "status": getattr(user, 'status', None),
                    "profile": getattr(user, 'profile', None),
                    "time_created": str(getattr(user, 'time_created', None)),
                    "time_expiring": str(getattr(user, 'time_expiring', None)),
                    "default_tablespace": getattr(user, 'default_tablespace', None),
                    "temp_tablespace": getattr(user, 'temp_tablespace', None),
                })

        return {
            "users": users,
            "count": len(users),
        }

    except Exception as e:
        raise ToolError(f"Failed to list users: {e}")


@dbm_server.tool
async def list_roles(
    managed_database_id: str,
    limit: int = 100,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List database roles for security auditing.

    Args:
        managed_database_id: Managed database OCID
        limit: Maximum results

    Returns:
        List of roles with authentication type
    """
    if ctx:
        await ctx.info("Listing database roles...")

    try:
        dbm_client = get_dbm_client()

        response = dbm_client.list_roles(
            managed_database_id=managed_database_id,
            limit=limit,
        )

        roles = []
        if hasattr(response.data, 'items'):
            for role in response.data.items:
                roles.append({
                    "name": role.name,
                    "authentication_type": getattr(role, 'authentication_type', None),
                })

        return {
            "roles": roles,
            "count": len(roles),
        }

    except Exception as e:
        raise ToolError(f"Failed to list roles: {e}")


@dbm_server.tool
async def list_sql_plan_baselines(
    managed_database_id: str,
    sql_handle: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    limit: int = 50,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List SQL plan baselines for plan stability.

    Args:
        managed_database_id: Managed database OCID
        sql_handle: Filter by SQL handle
        is_enabled: Filter by enabled status
        limit: Maximum results

    Returns:
        List of SQL plan baselines
    """
    if ctx:
        await ctx.info("Listing SQL plan baselines...")

    try:
        dbm_client = get_dbm_client()

        kwargs = {"managed_database_id": managed_database_id, "limit": limit}
        if sql_handle:
            kwargs["sql_handle"] = sql_handle
        if is_enabled is not None:
            kwargs["is_enabled"] = is_enabled

        response = dbm_client.list_sql_plan_baselines(**kwargs)

        baselines = []
        if hasattr(response.data, 'items'):
            for baseline in response.data.items:
                baselines.append({
                    "plan_name": baseline.plan_name,
                    "sql_handle": getattr(baseline, 'sql_handle', None),
                    "sql_text": getattr(baseline, 'sql_text', None)[:100] + "..." if getattr(baseline, 'sql_text', None) else None,
                    "origin": getattr(baseline, 'origin', None),
                    "is_enabled": getattr(baseline, 'is_enabled', None),
                    "is_accepted": getattr(baseline, 'is_accepted', None),
                    "is_fixed": getattr(baseline, 'is_fixed', None),
                    "time_created": str(getattr(baseline, 'time_created', None)),
                })

        return {
            "baselines": baselines,
            "count": len(baselines),
        }

    except Exception as e:
        raise ToolError(f"Failed to list SQL plan baselines: {e}")


@dbm_server.tool
async def get_database_fleet_health_metrics(
    compartment_id: str,
    compare_baseline_time: Optional[str] = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get fleet-wide health metrics for all managed databases.

    Args:
        compartment_id: Compartment OCID
        compare_baseline_time: Baseline time for comparison

    Returns:
        Fleet health metrics summary
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
