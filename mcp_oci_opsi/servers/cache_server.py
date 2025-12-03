"""Cache-based server for instant database fleet operations.

This server provides tools that operate entirely from local cache,
requiring zero API calls for maximum performance and minimal token usage.

All tools in this server respond in <100ms with minimal data.
"""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP, Context

from ..cache import get_cache, DatabaseCache


# Create cache sub-server
cache_server = FastMCP(
    name="cache-tools",
    instructions="""
    Cache tools provide instant access to database fleet information.
    These tools use local cache and require zero API calls.
    Always try cache tools first before using API-based tools.
    """,
)


@cache_server.tool
async def get_fleet_summary(ctx: Context) -> Dict[str, Any]:
    """
    Get instant fleet overview from cache (zero API calls).

    Returns database and host counts, breakdown by compartment and type.
    This is the fastest way to understand your fleet composition.

    Returns:
        Fleet summary with counts and breakdowns
    """
    await ctx.debug("Getting fleet summary from cache")
    cache = get_cache()
    cache.load()

    stats = cache.get_statistics()

    return {
        "databases": stats["statistics"]["total_databases"],
        "hosts": stats["statistics"]["total_hosts"],
        "by_compartment": stats["statistics"]["databases_by_compartment"],
        "by_type": stats["statistics"]["databases_by_type"],
        "by_status": stats["statistics"]["databases_by_status"],
        "cache_updated": stats["metadata"]["last_updated"],
        "profile": stats["metadata"]["profile"],
        "region": stats["metadata"]["region"],
    }


@cache_server.tool
async def search_databases(
    name: Optional[str] = None,
    compartment: Optional[str] = None,
    limit: int = 20,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Search databases in cache by name or compartment (instant).

    Args:
        name: Partial database name to search (case-insensitive)
        compartment: Partial compartment name to filter
        limit: Maximum results to return (default 20)

    Returns:
        List of matching databases with their details
    """
    if ctx:
        await ctx.debug(f"Searching databases: name={name}, compartment={compartment}")

    cache = get_cache()
    cache.load()

    results = cache.search_databases(name=name, compartment=compartment)

    # Apply limit
    limited_results = results[:limit]

    return {
        "databases": limited_results,
        "count": len(limited_results),
        "total_matches": len(results),
        "truncated": len(results) > limit,
    }


@cache_server.tool
async def get_databases_by_compartment(
    compartment_name: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get all databases in a specific compartment (instant).

    Args:
        compartment_name: Compartment name to filter (case-insensitive partial match)

    Returns:
        List of databases in the compartment
    """
    if ctx:
        await ctx.debug(f"Getting databases in compartment: {compartment_name}")

    cache = get_cache()
    cache.load()

    results = cache.search_databases(compartment=compartment_name)

    return {
        "compartment_filter": compartment_name,
        "databases": results,
        "count": len(results),
    }


@cache_server.tool
async def get_cached_statistics(ctx: Context = None) -> Dict[str, Any]:
    """
    Get detailed cache statistics.

    Returns comprehensive breakdown of the cached fleet data including
    counts by type, compartment, and status.

    Returns:
        Detailed statistics from cache
    """
    if ctx:
        await ctx.debug("Getting detailed cache statistics")

    cache = get_cache()
    cache.load()

    return cache.get_statistics()


@cache_server.tool
async def list_cached_compartments(ctx: Context = None) -> Dict[str, Any]:
    """
    List all compartments in cache.

    Returns:
        List of compartments with their IDs and names
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


@cache_server.tool
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


@cache_server.tool
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


@cache_server.tool
async def build_database_cache(
    compartment_ids: List[str],
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Build or rebuild the local database cache.

    Scans all specified compartments (and their children) to build
    a local cache of database and host information.

    Args:
        compartment_ids: List of root compartment OCIDs to scan

    Returns:
        Cache build results with statistics
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
