"""
MCP Tools for OPSI Skills v2 - Programmatic Skills Interface

This module provides MCP tools that expose the programmatic skills:
- DatabaseDiscoverySkill
- PerformanceAnalysisSkill  
- CostOptimizationSkill

These tools use the adapter pattern to bridge skills with the existing
OPSI infrastructure.
"""

from typing import Any, Dict, List, Optional
import logging
import os

logger = logging.getLogger(__name__)

# Lazy initialization of skills (initialized on first use)
_discovery_skill = None
_performance_skill = None
_cost_skill = None


def _get_discovery_skill():
    """Get or initialize the DatabaseDiscoverySkill."""
    global _discovery_skill
    if _discovery_skill is None:
        from ..skills import DatabaseDiscoverySkill, CacheManager
        profile = os.getenv("OCI_CLI_PROFILE", "DEFAULT")
        cache_manager = CacheManager(profile=profile)
        _discovery_skill = DatabaseDiscoverySkill(cache_manager)
        logger.info(f"Initialized DatabaseDiscoverySkill for profile: {profile}")
    return _discovery_skill


def _get_performance_skill():
    """Get or initialize the PerformanceAnalysisSkill."""
    global _performance_skill
    if _performance_skill is None:
        from ..skills import PerformanceAnalysisSkill, CacheManager, OPSIClient
        profile = os.getenv("OCI_CLI_PROFILE", "DEFAULT")
        cache_manager = CacheManager(profile=profile)
        opsi_client = OPSIClient(profile=profile)
        _performance_skill = PerformanceAnalysisSkill(opsi_client, cache_manager)
        logger.info(f"Initialized PerformanceAnalysisSkill for profile: {profile}")
    return _performance_skill


def _get_cost_skill():
    """Get or initialize the CostOptimizationSkill."""
    global _cost_skill
    if _cost_skill is None:
        from ..skills import CostOptimizationSkill, OPSIClient
        profile = os.getenv("OCI_CLI_PROFILE", "DEFAULT")
        opsi_client = OPSIClient(profile=profile)
        _cost_skill = CostOptimizationSkill(opsi_client)
        logger.info(f"Initialized CostOptimizationSkill for profile: {profile}")
    return _cost_skill


# ==============================================================================
# Database Discovery Tools (Tier 1 - Cache-based, < 100ms)
# ==============================================================================

def skill_discover_databases(
    compartment_id: Optional[str] = None,
    region: Optional[str] = None,
    db_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Discover databases using the DatabaseDiscoverySkill.
    
    This tool uses cached data for fast response (< 100ms).
    Falls back to API only when cache is stale.
    
    Args:
        compartment_id: Filter by compartment OCID (optional)
        region: Filter by region (e.g., 'us-ashburn-1') (optional)
        db_type: Filter by type ('adb', 'base', 'exadata', etc.) (optional)
        limit: Maximum number of results to return (default: 50)
    
    Returns:
        Dict containing:
        - databases: List of database info
        - total: Total count
        - filters_applied: Which filters were used
    """
    try:
        skill = _get_discovery_skill()
        databases = skill.discover_databases(
            compartment_id=compartment_id,
            region=region,
            db_type=db_type
        )
        
        # Convert to serializable format
        results = [
            {
                "ocid": db.ocid,
                "name": db.name,
                "db_type": db.db_type,
                "lifecycle_state": db.lifecycle_state,
                "compartment_id": db.compartment_id,
                "region": db.region,
                "cpu_count": db.cpu_count,
                "storage_gb": db.storage_gb
            }
            for db in databases[:limit]
        ]
        
        return {
            "databases": results,
            "total": len(databases),
            "returned": len(results),
            "filters_applied": {
                "compartment_id": compartment_id,
                "region": region,
                "db_type": db_type
            },
            "skill": "DatabaseDiscoverySkill",
            "tier": 1
        }
        
    except Exception as e:
        logger.error(f"skill_discover_databases failed: {e}")
        return {"error": str(e)}


def skill_get_fleet_summary() -> Dict[str, Any]:
    """
    Get a high-level summary of the database fleet.
    
    This tool provides instant statistics using cached data.
    Zero API calls, instant response.
    
    Returns:
        Dict containing:
        - total: Total database count
        - by_type: Count by database type
        - by_state: Count by lifecycle state
        - by_region: Count by region
        - total_cpu: Sum of CPU counts
        - total_storage_gb: Sum of storage
    """
    try:
        skill = _get_discovery_skill()
        summary = skill.get_fleet_summary()
        
        return {
            **summary,
            "skill": "DatabaseDiscoverySkill",
            "tier": 1
        }
        
    except Exception as e:
        logger.error(f"skill_get_fleet_summary failed: {e}")
        return {"error": str(e)}


def skill_search_databases(query: str, limit: int = 20) -> Dict[str, Any]:
    """
    Search databases by name or OCID.
    
    Performs partial, case-insensitive matching using cached data.
    
    Args:
        query: Search string to match against database name or OCID
        limit: Maximum number of results (default: 20)
    
    Returns:
        Dict containing matching databases
    """
    try:
        skill = _get_discovery_skill()
        databases = skill.search_databases(query)
        
        results = [
            {
                "ocid": db.ocid,
                "name": db.name,
                "db_type": db.db_type,
                "lifecycle_state": db.lifecycle_state,
                "region": db.region
            }
            for db in databases[:limit]
        ]
        
        return {
            "query": query,
            "results": results,
            "total": len(databases),
            "returned": len(results),
            "skill": "DatabaseDiscoverySkill",
            "tier": 1
        }
        
    except Exception as e:
        logger.error(f"skill_search_databases failed: {e}")
        return {"error": str(e)}


def skill_get_database_by_name(name: str) -> Dict[str, Any]:
    """
    Get database details by exact name match.
    
    Args:
        name: Database name (case-insensitive)
    
    Returns:
        Dict with database details or error if not found
    """
    try:
        skill = _get_discovery_skill()
        db = skill.get_database_by_name(name)
        
        if db:
            return {
                "found": True,
                "database": {
                    "ocid": db.ocid,
                    "name": db.name,
                    "db_type": db.db_type,
                    "lifecycle_state": db.lifecycle_state,
                    "compartment_id": db.compartment_id,
                    "region": db.region,
                    "cpu_count": db.cpu_count,
                    "storage_gb": db.storage_gb
                },
                "skill": "DatabaseDiscoverySkill",
                "tier": 1
            }
        else:
            return {
                "found": False,
                "error": f"Database not found: {name}",
                "suggestion": "Use skill_search_databases to search by partial name"
            }
        
    except Exception as e:
        logger.error(f"skill_get_database_by_name failed: {e}")
        return {"error": str(e)}


# ==============================================================================
# Performance Analysis Tools (Tier 2/3 - API/Cache, 1-30s)
# ==============================================================================

def skill_analyze_cpu_usage(
    database_id: str,
    hours_back: int = 24
) -> Dict[str, Any]:
    """
    Analyze CPU usage for a database.
    
    Provides current, average, peak usage and trend analysis.
    Includes AI-generated recommendations.
    
    Args:
        database_id: Database OCID
        hours_back: Number of hours to analyze (default: 24)
    
    Returns:
        Dict containing:
        - current_usage: Current CPU percentage
        - average_usage: Average over time period
        - peak_usage: Maximum CPU percentage
        - trend: 'increasing', 'decreasing', or 'stable'
        - recommendations: List of optimization suggestions
    """
    try:
        skill = _get_performance_skill()
        analysis = skill.analyze_cpu_usage(database_id, hours_back)
        
        return {
            "database_id": database_id,
            "hours_analyzed": hours_back,
            "current_usage": analysis.current_usage,
            "average_usage": analysis.average_usage,
            "peak_usage": analysis.peak_usage,
            "trend": analysis.trend,
            "data_points": len(analysis.metrics),
            "recommendations": analysis.recommendations,
            "skill": "PerformanceAnalysisSkill",
            "tier": 2
        }
        
    except Exception as e:
        logger.error(f"skill_analyze_cpu_usage failed: {e}")
        return {"error": str(e)}


def skill_analyze_memory_usage(
    database_id: str,
    hours_back: int = 24
) -> Dict[str, Any]:
    """
    Analyze memory usage for a database.
    
    Args:
        database_id: Database OCID
        hours_back: Number of hours to analyze (default: 24)
    
    Returns:
        Dict containing memory analysis with trend and recommendations
    """
    try:
        skill = _get_performance_skill()
        analysis = skill.analyze_memory_usage(database_id, hours_back)
        
        return {
            "database_id": database_id,
            "hours_analyzed": hours_back,
            "current_usage": analysis.current_usage,
            "average_usage": analysis.average_usage,
            "peak_usage": analysis.peak_usage,
            "trend": analysis.trend,
            "data_points": len(analysis.metrics),
            "recommendations": analysis.recommendations,
            "skill": "PerformanceAnalysisSkill",
            "tier": 2
        }
        
    except Exception as e:
        logger.error(f"skill_analyze_memory_usage failed: {e}")
        return {"error": str(e)}


def skill_analyze_io_performance(
    database_id: str,
    hours_back: int = 24
) -> Dict[str, Any]:
    """
    Analyze I/O performance for a database.
    
    Args:
        database_id: Database OCID
        hours_back: Number of hours to analyze (default: 24)
    
    Returns:
        Dict containing I/O analysis (throughput in MB/s)
    """
    try:
        skill = _get_performance_skill()
        analysis = skill.analyze_io_performance(database_id, hours_back)
        
        return {
            "database_id": database_id,
            "hours_analyzed": hours_back,
            "current_throughput_mbps": analysis.current_usage,
            "average_throughput_mbps": analysis.average_usage,
            "peak_throughput_mbps": analysis.peak_usage,
            "trend": analysis.trend,
            "data_points": len(analysis.metrics),
            "recommendations": analysis.recommendations,
            "skill": "PerformanceAnalysisSkill",
            "tier": 2
        }
        
    except Exception as e:
        logger.error(f"skill_analyze_io_performance failed: {e}")
        return {"error": str(e)}


def skill_get_performance_summary(
    database_id: str,
    hours_back: int = 24
) -> Dict[str, Any]:
    """
    Get comprehensive performance summary for a database.
    
    Includes CPU, memory, and I/O analysis in a single call.
    
    Args:
        database_id: Database OCID
        hours_back: Number of hours to analyze (default: 24)
    
    Returns:
        Dict containing complete performance summary with all metrics
    """
    try:
        skill = _get_performance_skill()
        summary = skill.get_performance_summary(database_id, hours_back)
        
        return {
            **summary,
            "skill": "PerformanceAnalysisSkill",
            "tier": 2
        }
        
    except Exception as e:
        logger.error(f"skill_get_performance_summary failed: {e}")
        return {"error": str(e)}


# ==============================================================================
# Cost Optimization Tools (Tier 2 - API-based, 1-5s)
# ==============================================================================

def skill_find_cost_opportunities(
    compartment_id: Optional[str] = None,
    min_savings_usd: float = 50.0,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Find cost-saving opportunities in the database fleet.
    
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
        Dict containing list of opportunities with estimated savings
    """
    try:
        skill = _get_cost_skill()
        opportunities = skill.find_opportunities(
            compartment_id=compartment_id,
            min_savings_usd=min_savings_usd
        )
        
        results = [
            {
                "database_id": opp.database_id,
                "database_name": opp.database_name,
                "opportunity_type": opp.opportunity_type,
                "estimated_monthly_savings": opp.estimated_monthly_savings,
                "confidence": opp.confidence,
                "recommendation": opp.recommendation,
                "action_required": opp.action_required,
                "current_monthly_cost": opp.current_monthly_cost,
                "potential_monthly_cost": opp.potential_monthly_cost
            }
            for opp in opportunities[:limit]
        ]
        
        total_savings = sum(opp.estimated_monthly_savings for opp in opportunities)
        
        return {
            "opportunities": results,
            "total_opportunities": len(opportunities),
            "returned": len(results),
            "total_monthly_savings": total_savings,
            "filters": {
                "compartment_id": compartment_id,
                "min_savings_usd": min_savings_usd
            },
            "skill": "CostOptimizationSkill",
            "tier": 2
        }
        
    except Exception as e:
        logger.error(f"skill_find_cost_opportunities failed: {e}")
        return {"error": str(e)}


def skill_get_savings_summary(
    compartment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a summary of all cost-saving opportunities.
    
    Provides totals grouped by opportunity type and confidence level.
    
    Args:
        compartment_id: Filter by compartment (optional)
    
    Returns:
        Dict containing:
        - total_opportunities: Count of all opportunities
        - total_monthly_savings: Total potential savings
        - by_type: Opportunities grouped by type
        - by_confidence: Opportunities grouped by confidence level
        - top_opportunities: Top 10 highest-value opportunities
    """
    try:
        skill = _get_cost_skill()
        summary = skill.get_savings_summary(compartment_id)
        
        return {
            **summary,
            "skill": "CostOptimizationSkill",
            "tier": 2
        }
        
    except Exception as e:
        logger.error(f"skill_get_savings_summary failed: {e}")
        return {"error": str(e)}


# ==============================================================================
# Skill Management Tools
# ==============================================================================

def list_programmatic_skills() -> Dict[str, Any]:
    """
    List all available programmatic skills.
    
    Returns metadata about each skill including tier, category,
    and available methods.
    
    Returns:
        Dict containing list of skills with their metadata
    """
    skills = [
        {
            "name": "DatabaseDiscoverySkill",
            "description": "Fast database fleet discovery using cached data",
            "tier": 1,
            "category": "discovery",
            "response_time": "< 100ms",
            "tools": [
                "skill_discover_databases",
                "skill_get_fleet_summary",
                "skill_search_databases",
                "skill_get_database_by_name"
            ]
        },
        {
            "name": "PerformanceAnalysisSkill",
            "description": "Database performance analysis using OPSI metrics",
            "tier": 2,
            "category": "analysis",
            "response_time": "1-30s",
            "tools": [
                "skill_analyze_cpu_usage",
                "skill_analyze_memory_usage",
                "skill_analyze_io_performance",
                "skill_get_performance_summary"
            ]
        },
        {
            "name": "CostOptimizationSkill",
            "description": "Identify database cost-saving opportunities",
            "tier": 2,
            "category": "optimization",
            "response_time": "1-5s",
            "tools": [
                "skill_find_cost_opportunities",
                "skill_get_savings_summary"
            ]
        }
    ]
    
    return {
        "skills": skills,
        "total": len(skills),
        "note": (
            "Tier 1 skills use cache for instant response. "
            "Tier 2/3 skills may make API calls. "
            "Use Tier 1 skills first to minimize latency and token usage."
        )
    }


def get_skill_recommendations(query: str) -> Dict[str, Any]:
    """
    Get skill recommendations for a natural language query.
    
    Analyzes the query to suggest which skills/tools to use.
    
    Args:
        query: Natural language description of what you want to do
    
    Returns:
        Dict containing recommended skills and tools
    """
    query_lower = query.lower()
    
    recommendations = []
    
    # Discovery patterns
    if any(word in query_lower for word in ['list', 'find', 'discover', 'search', 'count', 'how many', 'fleet', 'summary']):
        recommendations.append({
            "skill": "DatabaseDiscoverySkill",
            "reason": "Query involves database discovery/enumeration",
            "suggested_tools": ["skill_get_fleet_summary", "skill_discover_databases", "skill_search_databases"],
            "tier": 1
        })
    
    # Performance patterns
    if any(word in query_lower for word in ['performance', 'cpu', 'memory', 'io', 'slow', 'usage', 'trend', 'analyze']):
        recommendations.append({
            "skill": "PerformanceAnalysisSkill",
            "reason": "Query involves performance analysis",
            "suggested_tools": ["skill_get_performance_summary", "skill_analyze_cpu_usage"],
            "tier": 2
        })
    
    # Cost patterns
    if any(word in query_lower for word in ['cost', 'savings', 'optimize', 'expensive', 'rightsize', 'budget', 'money']):
        recommendations.append({
            "skill": "CostOptimizationSkill",
            "reason": "Query involves cost optimization",
            "suggested_tools": ["skill_get_savings_summary", "skill_find_cost_opportunities"],
            "tier": 2
        })
    
    if not recommendations:
        recommendations.append({
            "skill": "DatabaseDiscoverySkill",
            "reason": "Default - start with fleet discovery",
            "suggested_tools": ["skill_get_fleet_summary"],
            "tier": 1
        })
    
    return {
        "query": query,
        "recommendations": recommendations,
        "note": "Start with Tier 1 skills for fastest response"
    }


# Tool registry for MCP server
SKILL_TOOLS = {
    # Discovery tools (Tier 1)
    "skill_discover_databases": skill_discover_databases,
    "skill_get_fleet_summary": skill_get_fleet_summary,
    "skill_search_databases": skill_search_databases,
    "skill_get_database_by_name": skill_get_database_by_name,
    
    # Performance tools (Tier 2)
    "skill_analyze_cpu_usage": skill_analyze_cpu_usage,
    "skill_analyze_memory_usage": skill_analyze_memory_usage,
    "skill_analyze_io_performance": skill_analyze_io_performance,
    "skill_get_performance_summary": skill_get_performance_summary,
    
    # Cost tools (Tier 2)
    "skill_find_cost_opportunities": skill_find_cost_opportunities,
    "skill_get_savings_summary": skill_get_savings_summary,
    
    # Skill management
    "list_programmatic_skills": list_programmatic_skills,
    "get_skill_recommendations": get_skill_recommendations,
}
