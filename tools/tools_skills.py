"""Skills tools for MCP OCI OPSI server.

This module provides MCP tools for skill discovery and usage.
Skills help reduce token usage and improve accuracy by providing
focused guidance for specific DBA tasks.

For clients that support skills natively (Anthropic Skills API),
skills are automatically available. For other clients, these tools
provide skill context as prompt enhancement.
"""

from typing import Any, Dict, List, Optional

from ..skills_loader import get_skills_loader, Skill


def list_available_skills() -> Dict[str, Any]:
    """
    List all available DBA skills.

    Skills are specialized instruction sets that help Claude perform
    specific DBA tasks with minimal token usage and maximum accuracy.

    Returns:
        Dictionary containing:
        - skills: List of available skills with name and description
        - count: Total number of skills
        - note: Usage guidance
    """
    loader = get_skills_loader()
    skills = loader.list_skills()

    return {
        "skills": skills,
        "count": len(skills),
        "note": (
            "Skills provide specialized guidance for DBA tasks. "
            "Use get_skill_context() to get detailed instructions for a skill, "
            "or use get_skill_for_query() to find the best skill for your question."
        ),
    }


def get_skill_context(skill_name: str) -> Dict[str, Any]:
    """
    Get detailed context for a specific skill.

    Returns the full skill instructions including recommended tools,
    example interactions, and best practices.

    Args:
        skill_name: Name of the skill (e.g., "fleet-overview", "sql-performance")

    Returns:
        Dictionary containing:
        - name: Skill name
        - description: Skill description
        - allowed_tools: List of recommended tools
        - content: Full skill instructions
        - error: Error message if skill not found
    """
    loader = get_skills_loader()
    skill = loader.get_skill(skill_name)

    if not skill:
        available = [s["name"] for s in loader.list_skills()]
        return {
            "error": f"Skill '{skill_name}' not found",
            "available_skills": available,
        }

    return skill.to_dict()


def get_skill_for_query(query: str) -> Dict[str, Any]:
    """
    Find the most relevant skill for a user query.

    Analyzes the query to determine which skill would be most helpful,
    then returns that skill's context for optimal response generation.

    Args:
        query: User's natural language question or request

    Returns:
        Dictionary containing:
        - matched_skill: Name of the matched skill (or null)
        - context: Skill context for the query
        - recommended_tools: List of tools to use
    """
    loader = get_skills_loader()
    skill = loader.get_skill_for_query(query)

    if not skill:
        return {
            "matched_skill": None,
            "context": "",
            "recommended_tools": [],
            "note": (
                "No specific skill matched this query. "
                "Use list_available_skills() to see all available skills."
            ),
        }

    return {
        "matched_skill": skill.name,
        "description": skill.description,
        "context": skill.to_prompt_context(),
        "recommended_tools": skill.allowed_tools,
    }


def get_quick_reference(category: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a quick reference guide for common DBA tasks.

    Provides a condensed reference of which tools to use for different
    tasks, optimized for minimal token usage.

    Args:
        category: Optional category filter (fleet, sql, capacity, diagnostics, storage, security)

    Returns:
        Dictionary containing task-to-tool mappings
    """
    quick_ref = {
        "fleet": {
            "category": "Fleet & Inventory",
            "tasks": {
                "count_databases": "get_fleet_summary() - instant, no API",
                "find_database": "search_databases(name='...') - instant",
                "by_compartment": "get_databases_by_compartment('...') - instant",
                "list_all": "list_database_insights(compartment_id) - API call",
                "list_hosts": "list_host_insights(compartment_id) - API call",
            }
        },
        "sql": {
            "category": "SQL Performance",
            "tasks": {
                "top_sql": "get_top_sql_by_metric(metric='CPU') - requires AWR",
                "sql_anomalies": "summarize_sql_insights() - OPSI",
                "plan_analysis": "summarize_sql_plan_insights(sql_identifier)",
                "sql_text": "list_sql_texts(time_start, time_end)",
                "addm_sql": "summarize_addm_db_findings() - OPSI",
            }
        },
        "capacity": {
            "category": "Capacity Planning",
            "tasks": {
                "cpu_forecast": "get_resource_forecast_with_chart(metric='CPU')",
                "storage_forecast": "get_resource_forecast_with_chart(metric='STORAGE')",
                "trend_analysis": "get_capacity_trend_with_chart(metric='...')",
                "host_forecast": "get_host_resource_forecast_trend()",
                "recommendations": "get_host_recommendations()",
            }
        },
        "diagnostics": {
            "category": "Diagnostics & Troubleshooting",
            "tasks": {
                "addm_findings": "summarize_addm_db_findings() or get_addm_report()",
                "wait_events": "get_ash_analytics(wait_class='...')",
                "awr_report": "get_awr_report(begin_snapshot, end_snapshot)",
                "alert_logs": "list_alert_logs(log_level='CRITICAL')",
                "permissions": "diagnose_opsi_permissions(compartment_id)",
                "full_diag": "get_comprehensive_diagnostics()",
            }
        },
        "storage": {
            "category": "Storage Management",
            "tasks": {
                "tablespace_usage": "get_tablespace_usage(database_id)",
                "all_tablespaces": "list_tablespaces(database_id)",
                "table_stats": "list_table_statistics()",
                "resource_usage": "get_database_resource_usage()",
            }
        },
        "security": {
            "category": "Security Audit",
            "tasks": {
                "list_users": "list_users(database_id)",
                "user_details": "get_user(user_name='...')",
                "list_roles": "list_roles(database_id)",
                "privileges": "list_system_privileges(database_id)",
                "proxy_users": "list_proxy_users(database_id)",
            }
        },
    }

    if category and category in quick_ref:
        return {
            "reference": quick_ref[category],
            "note": "Use the skill-specific context for detailed guidance",
        }

    return {
        "reference": quick_ref,
        "categories": list(quick_ref.keys()),
        "note": "Pass category parameter for filtered results",
    }


def get_token_optimization_tips() -> Dict[str, Any]:
    """
    Get tips for minimizing token usage in DBA operations.

    Returns best practices for efficient queries that minimize
    token consumption while maximizing information quality.

    Returns:
        Dictionary containing optimization tips and tool recommendations
    """
    return {
        "tips": [
            {
                "title": "Use Cache Tools First",
                "description": (
                    "Tools like get_fleet_summary(), search_databases(), and "
                    "get_databases_by_compartment() use local cache - zero API calls, "
                    "instant response, minimal tokens."
                ),
                "tools": [
                    "get_fleet_summary",
                    "search_databases",
                    "get_databases_by_compartment",
                    "get_cached_statistics",
                    "list_cached_compartments",
                ],
            },
            {
                "title": "Limit Result Sets",
                "description": (
                    "Always use limit parameters and time ranges to reduce data volume."
                ),
                "examples": [
                    "search_databases(limit=10)",
                    "get_top_sql_by_metric(top_n=5)",
                    "list_alert_logs(log_level='CRITICAL')",
                ],
            },
            {
                "title": "Use Summary Tools Over Detail Tools",
                "description": (
                    "Start with summary/overview tools, drill down only if needed."
                ),
                "examples": [
                    "get_fleet_summary() before list_database_insights()",
                    "summarize_addm_db_findings() before get_addm_report()",
                    "get_tablespace_usage() before get_tablespace()",
                ],
            },
            {
                "title": "Skip Charts Unless Needed",
                "description": (
                    "Use non-chart versions for data-only queries. "
                    "Charts add ~30% more tokens."
                ),
                "tools": [
                    "get_database_resource_forecast (no chart)",
                    "get_database_capacity_trend (no chart)",
                ],
            },
            {
                "title": "Use Skills for Guidance",
                "description": (
                    "Skills provide focused guidance that helps avoid unnecessary tool calls."
                ),
                "tools": [
                    "get_skill_for_query",
                    "list_available_skills",
                ],
            },
        ],
        "token_efficient_tools": [
            "get_fleet_summary",
            "search_databases",
            "get_databases_by_compartment",
            "get_cached_statistics",
            "ping",
            "whoami",
        ],
    }
