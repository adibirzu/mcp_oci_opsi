"""Cache-based server for instant database fleet operations.

This server provides tools that operate entirely from local cache,
requiring zero API calls for maximum performance and minimal token usage.

All tools in this server respond in <100ms with minimal data.

Follows MCP Best Practices:
- Tool annotations for hints (readOnlyHint, destructiveHint, etc.)
- Standard pagination with has_more, next_offset, total_count
- Consistent naming: cache_{action}_{resource}
"""

from typing import Any, Dict, List, Optional, Literal

from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolAnnotations

from ..cache import get_cache, DatabaseCache


# Create cache sub-server
cache_server = FastMCP(
    name="cache-tools",
    instructions="""
    Cache tools provide instant access to database fleet information.
    These tools use local cache and require zero API calls.
    Always try cache tools first before using API-based tools.

    Performance: All operations complete in <100ms.
    Rate Limits: Unlimited (no API calls).
    """,
)


@cache_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def get_fleet_summary(
    format: Literal["json", "markdown"] = "json",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get instant fleet overview from cache (zero API calls).

    Returns database and host counts, breakdown by compartment and type.
    This is the fastest way to understand your fleet composition.

    Args:
        format: Output format - "json" (default) or "markdown" for human-readable

    Returns:
        Fleet summary with counts and breakdowns

    Examples:
        - get_fleet_summary() - Get JSON summary
        - get_fleet_summary(format="markdown") - Get human-readable summary
        - Use this first to understand fleet size before querying specific databases
    """
    if ctx:
        await ctx.debug("Getting fleet summary from cache")
    cache = get_cache()
    cache.load()

    stats = cache.get_statistics()

    data = {
        "databases": stats["statistics"]["total_databases"],
        "hosts": stats["statistics"]["total_hosts"],
        "by_compartment": stats["statistics"]["databases_by_compartment"],
        "by_type": stats["statistics"]["databases_by_type"],
        "by_status": stats["statistics"]["databases_by_status"],
        "cache_updated": stats["metadata"]["last_updated"],
        "profile": stats["metadata"]["profile"],
        "region": stats["metadata"]["region"],
    }

    if format == "markdown":
        md = f"""## Fleet Summary

**Total Databases:** {data['databases']}
**Total Hosts:** {data['hosts']}
**Profile:** {data['profile']}
**Region:** {data['region']}
**Cache Updated:** {data['cache_updated']}

### By Type
| Type | Count |
|------|-------|
"""
        for db_type, count in data['by_type'].items():
            md += f"| {db_type} | {count} |\n"

        md += "\n### By Compartment\n| Compartment | Count |\n|-------------|-------|\n"
        for comp, count in data['by_compartment'].items():
            md += f"| {comp} | {count} |\n"

        return {"markdown": md, "data": data}

    return data


@cache_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def search_databases(
    name: Optional[str] = None,
    compartment: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    format: Literal["json", "markdown"] = "json",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Search databases in cache by name or compartment (instant).

    Args:
        name: Partial database name to search (case-insensitive)
        compartment: Partial compartment name to filter
        limit: Maximum results to return (default 20, max 100)
        offset: Number of results to skip for pagination (default 0)
        format: Output format - "json" (default) or "markdown"

    Returns:
        List of matching databases with pagination metadata

    Examples:
        - search_databases(name="PROD") - Find databases with PROD in name
        - search_databases(compartment="Production", limit=10) - First 10 in Production
        - search_databases(name="DB", offset=20, limit=20) - Page 2 of results
    """
    if ctx:
        await ctx.debug(f"Searching databases: name={name}, compartment={compartment}")

    cache = get_cache()
    cache.load()

    # Get all matches
    all_results = cache.search_databases(name=name, compartment=compartment)
    total_count = len(all_results)

    # Apply pagination
    limit = min(limit, 100)  # Cap at 100
    paginated_results = all_results[offset:offset + limit]

    data = {
        "databases": paginated_results,
        "count": len(paginated_results),
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total_count": total_count,
            "has_more": offset + limit < total_count,
            "next_offset": offset + limit if offset + limit < total_count else None,
        },
        "filters": {
            "name": name,
            "compartment": compartment,
        },
    }

    if format == "markdown":
        md = f"""## Database Search Results

**Total Matches:** {total_count}
**Showing:** {offset + 1} - {offset + len(paginated_results)}

| Name | Type | Compartment | Status |
|------|------|-------------|--------|
"""
        for db in paginated_results:
            md += f"| {db.get('name', 'N/A')} | {db.get('type', 'N/A')} | {db.get('compartment_name', 'N/A')} | {db.get('status', 'N/A')} |\n"

        if data["pagination"]["has_more"]:
            md += f"\n*Use offset={data['pagination']['next_offset']} to see more results*"

        return {"markdown": md, "data": data}

    return data


@cache_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def get_databases_by_compartment(
    compartment_name: str,
    limit: int = 50,
    offset: int = 0,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get all databases in a specific compartment (instant).

    Args:
        compartment_name: Compartment name to filter (case-insensitive partial match)
        limit: Maximum results to return (default 50)
        offset: Number of results to skip for pagination

    Returns:
        List of databases in the compartment with pagination

    Examples:
        - get_databases_by_compartment("Production") - All databases in Production
        - get_databases_by_compartment("Dev", limit=10) - First 10 in Dev compartments
    """
    if ctx:
        await ctx.debug(f"Getting databases in compartment: {compartment_name}")

    cache = get_cache()
    cache.load()

    all_results = cache.search_databases(compartment=compartment_name)
    total_count = len(all_results)
    paginated = all_results[offset:offset + limit]

    return {
        "compartment_filter": compartment_name,
        "databases": paginated,
        "count": len(paginated),
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total_count": total_count,
            "has_more": offset + limit < total_count,
            "next_offset": offset + limit if offset + limit < total_count else None,
        },
    }


@cache_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def get_cached_statistics(ctx: Context = None) -> Dict[str, Any]:
    """
    Get detailed cache statistics.

    Returns comprehensive breakdown of the cached fleet data including
    counts by type, compartment, and status.

    Returns:
        Detailed statistics from cache

    Examples:
        - get_cached_statistics() - Full cache breakdown
        - Use to check cache age and decide if refresh is needed
    """
    if ctx:
        await ctx.debug("Getting detailed cache statistics")

    cache = get_cache()
    cache.load()

    return cache.get_statistics()


@cache_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def list_cached_compartments(ctx: Context = None) -> Dict[str, Any]:
    """
    List all compartments in cache.

    Returns:
        List of compartments with their IDs and names

    Examples:
        - list_cached_compartments() - Get all compartment names and OCIDs
        - Use to find compartment IDs for other operations
    """
    if ctx:
        await ctx.debug("Listing cached compartments")

    cache = get_cache()
    cache.load()

    compartments = cache.get_compartments()

    return {
        "compartments": list(compartments.values()),
        "count": len(compartments),
    }


@cache_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def get_database_info(
    database_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get cached information for a specific database.

    Args:
        database_id: Database insight OCID

    Returns:
        Database details from cache or error if not found

    Examples:
        - get_database_info("ocid1.opsidatabaseinsight...") - Get specific database
        - If not found, use search_databases() to find the correct ID
    """
    if ctx:
        await ctx.debug(f"Getting database info: {database_id}")

    cache = get_cache()
    cache.load()

    db = cache.get_database(database_id)

    if db:
        return {"database": db, "found": True}
    else:
        return {
            "found": False,
            "error": f"Database {database_id} not found in cache",
            "suggestion": "Try search_databases() or rebuild cache with build_database_cache()",
        }


@cache_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def check_cache_validity(
    max_age_hours: int = 24,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Check if cache is valid and current.

    Args:
        max_age_hours: Maximum cache age in hours (default 24)

    Returns:
        Cache validity status and recommendations

    Examples:
        - check_cache_validity() - Check if cache is less than 24 hours old
        - check_cache_validity(max_age_hours=1) - Stricter freshness check
    """
    if ctx:
        await ctx.debug(f"Checking cache validity (max age: {max_age_hours}h)")

    cache = get_cache()
    cache.load()

    is_valid = cache.is_cache_valid(max_age_hours)
    stats = cache.get_statistics()

    return {
        "is_valid": is_valid,
        "last_updated": stats["metadata"]["last_updated"],
        "profile": stats["metadata"]["profile"],
        "region": stats["metadata"]["region"],
        "max_age_hours": max_age_hours,
        "recommendation": None if is_valid else "Cache is stale. Run build_database_cache() to refresh.",
    }


@cache_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,  # Not destructive - creates/updates cache
        idempotent_hint=True,
        open_world_hint=True,  # Makes API calls to OCI
    )
)
async def build_database_cache(
    compartment_ids: List[str],
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Build or rebuild the local database cache.

    Scans all specified compartments (and their children) to build
    a local cache of database and host information.

    NOTE: This tool makes OCI API calls to scan compartments.
    All other cache tools are instant and use zero API calls.

    Args:
        compartment_ids: List of root compartment OCIDs to scan

    Returns:
        Cache build results with statistics

    Examples:
        - build_database_cache(["ocid1.compartment..."]) - Scan one compartment tree
        - build_database_cache([tenancy_ocid]) - Scan entire tenancy
    """
    if ctx:
        await ctx.info(f"Building cache for {len(compartment_ids)} compartments...")

    cache = get_cache()

    # Report progress
    total_compartments = len(compartment_ids)
    for i, comp_id in enumerate(compartment_ids):
        if ctx:
            await ctx.report_progress(progress=i, total=total_compartments)
            await ctx.debug(f"Scanning compartment {i+1}/{total_compartments}")

    result = cache.build_cache(compartment_ids)

    if ctx:
        await ctx.report_progress(progress=total_compartments, total=total_compartments)
        await ctx.info(f"Cache built: {result['statistics']['total_databases']} databases, {result['statistics']['total_hosts']} hosts")

    return result


# Resource definitions for cache data
@cache_server.resource("resource://fleet/summary")
async def fleet_summary_resource() -> Dict[str, Any]:
    """Fleet summary as a resource (read-only data)."""
    cache = get_cache()
    cache.load()
    stats = cache.get_statistics()

    return {
        "databases": stats["statistics"]["total_databases"],
        "hosts": stats["statistics"]["total_hosts"],
        "by_compartment": stats["statistics"]["databases_by_compartment"],
        "by_type": stats["statistics"]["databases_by_type"],
        "cache_updated": stats["metadata"]["last_updated"],
    }


@cache_server.resource("resource://fleet/statistics")
async def fleet_statistics_resource() -> Dict[str, Any]:
    """Detailed fleet statistics as a resource."""
    cache = get_cache()
    cache.load()
    return cache.get_statistics()


@cache_server.resource("resource://fleet/compartments")
async def compartments_resource() -> Dict[str, Any]:
    """List of compartments as a resource."""
    cache = get_cache()
    cache.load()
    return {"compartments": list(cache.get_compartments().values())}


@cache_server.resource("resource://database/{database_id}")
async def database_resource(database_id: str) -> Dict[str, Any]:
    """Individual database info as a resource."""
    cache = get_cache()
    cache.load()
    db = cache.get_database(database_id)
    return {"database": db} if db else {"error": "Database not found"}
