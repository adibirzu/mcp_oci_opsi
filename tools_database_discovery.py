"""Enhanced database discovery and management type classification tools."""

from typing import Any, Optional
import oci

from .oci_clients import get_opsi_client, list_all
from .cache import DatabaseCache


def list_database_insights_by_management_type(
    compartment_id: str,
    lifecycle_state: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    List database insights grouped by their management type (agent source).

    This tool categorizes databases by how they're monitored:
    - **MACS_MANAGED_EXTERNAL_DATABASE**: Management Agent Cloud Service
    - **AUTONOMOUS**: OCI-managed autonomous databases
    - **EM_MANAGED_EXTERNAL_DATABASE**: Enterprise Manager managed
    - **MDS_MYSQL_DATABASE_SYSTEM**: MySQL Database Service
    - **PE_COMANAGED_DATABASE**: PE (Pluggable Database) co-managed
    - **COMPARTMENT_ID_IN_SUBTREE**: Database with subtree access

    Each type has different API capabilities - this tool helps identify which
    databases support which Operations Insights features.

    Args:
        compartment_id: Compartment OCID to query
        lifecycle_state: Filter by lifecycle state (optional, e.g., "ACTIVE")
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with databases grouped by management type, including:
        - databases_by_type: Databases organized by entity_source
        - api_compatibility: Which APIs work for each type
        - summary: Count by type and total
    """
    try:
        # Get client with optional profile
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile
            try:
                client = get_opsi_client()
            finally:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)
        else:
            client = get_opsi_client()

        # Fetch all database insights
        kwargs = {"compartment_id": compartment_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state

        db_insights = list_all(
            client.list_database_insights,
            **kwargs,
        )

        # Group by management type
        databases_by_type = {}

        for db in db_insights:
            entity_source = getattr(db, "entity_source", "UNKNOWN")

            if entity_source not in databases_by_type:
                databases_by_type[entity_source] = []

            db_info = {
                "id": db.id,
                "database_id": getattr(db, "database_id", None),
                "database_name": getattr(db, "database_name", None),
                "database_display_name": getattr(db, "database_display_name", None),
                "database_type": db.database_type,
                "database_version": getattr(db, "database_version", None),
                "entity_source": entity_source,
                "status": db.status,
                "lifecycle_state": db.lifecycle_state,
                "compartment_id": db.compartment_id,
                "processor_count": getattr(db, "processor_count", None),
                "time_created": str(db.time_created),
            }

            databases_by_type[entity_source].append(db_info)

        # Define API compatibility for each management type
        # Priority: 1 = Highest (agent-based, full API support), 3 = Lowest
        api_compatibility = {
            "MACS_MANAGED_EXTERNAL_DATABASE": {
                "display_name": "Management Agent (MACS)",
                "description": "Databases monitored via OCI Management Agent",
                "priority": 1,
                "agent_type": "Management Agent Cloud Service (MACS)",
                "agent_based": True,
                "supported_apis": {
                    "list_database_insights": "✅ Full Support",
                    "get_database_insight": "✅ Full Support",
                    "summarize_sql_statistics": "✅ Full Support",
                    "summarize_database_insight_resource_statistics": "✅ Full Support",
                    "summarize_database_insight_resource_capacity_trend": "✅ Full Support",
                    "summarize_database_insight_resource_forecast_trend": "✅ Full Support",
                    "summarize_database_insight_resource_usage": "✅ Full Support",
                    "summarize_database_insight_resource_utilization_insight": "✅ Full Support",
                    "get_sql_plan": "✅ Full Support",
                    "warehouse_queries": "✅ Full Support",
                },
                "limitations": None,
                "recommended": True,
            },
            "AUTONOMOUS": {
                "display_name": "Autonomous Database (OCI Native)",
                "description": "OCI Autonomous Database with native integration",
                "priority": 1,
                "agent_type": "Cloud Agent (Built-in)",
                "agent_based": True,
                "supported_apis": {
                    "list_database_insights": "✅ Full Support",
                    "get_database_insight": "✅ Full Support",
                    "summarize_sql_statistics": "✅ Full Support",
                    "summarize_database_insight_resource_statistics": "✅ Full Support",
                    "summarize_database_insight_resource_capacity_trend": "✅ Full Support",
                    "summarize_database_insight_resource_forecast_trend": "✅ Full Support",
                    "summarize_database_insight_resource_usage": "✅ Full Support",
                    "warehouse_queries": "✅ Full Support",
                },
                "limitations": None,
                "recommended": True,
            },
            "EM_MANAGED_EXTERNAL_DATABASE": {
                "display_name": "Enterprise Manager Managed",
                "description": "Databases monitored through Oracle Enterprise Manager",
                "priority": 3,
                "agent_type": "Enterprise Manager Agent",
                "agent_based": False,
                "supported_apis": {
                    "list_database_insights": "✅ Full Support",
                    "get_database_insight": "✅ Full Support",
                    "summarize_sql_statistics": "❌ Not Supported (use warehouse)",
                    "summarize_database_insight_resource_statistics": "✅ Partial Support",
                    "summarize_database_insight_resource_capacity_trend": "✅ Partial Support",
                    "summarize_database_insight_resource_forecast_trend": "❌ Limited Support",
                    "warehouse_queries": "✅ Full Support (if enabled)",
                },
                "limitations": [
                    "SQL Statistics API returns 404 (use warehouse queries)",
                    "Some capacity planning APIs may have limited data",
                    "Resource statistics may be delayed",
                ],
                "recommended": False,
                "alternatives": [
                    "Enable Operations Insights warehouse for SQL statistics",
                    "Use Database Management Service Performance Hub APIs",
                    "Migrate to Management Agent (MACS) for full API support",
                ],
            },
            "PE_COMANAGED_DATABASE": {
                "display_name": "PE Co-managed Database",
                "description": "Pluggable databases with co-managed monitoring",
                "priority": 2,
                "agent_type": "Cloud Agent (Co-managed)",
                "agent_based": True,
                "supported_apis": {
                    "list_database_insights": "✅ Full Support",
                    "get_database_insight": "✅ Full Support",
                    "summarize_sql_statistics": "✅ Full Support",
                    "summarize_database_insight_resource_statistics": "✅ Full Support",
                    "warehouse_queries": "✅ Full Support",
                },
                "limitations": None,
                "recommended": True,
            },
            "MDS_MYSQL_DATABASE_SYSTEM": {
                "display_name": "MySQL Database Service",
                "description": "OCI MySQL Database Service",
                "priority": 2,
                "agent_type": "Cloud Agent (Built-in)",
                "agent_based": True,
                "supported_apis": {
                    "list_database_insights": "✅ Full Support",
                    "get_database_insight": "✅ Full Support",
                    "summarize_database_insight_resource_statistics": "✅ Full Support",
                    "summarize_database_insight_resource_capacity_trend": "✅ Full Support",
                },
                "limitations": ["SQL-specific APIs not applicable for MySQL"],
                "recommended": True,
            },
            "AUTONOMOUS_DATABASE": {
                "display_name": "Autonomous Database",
                "description": "OCI Autonomous Database (alternative entity_source value)",
                "priority": 1,
                "agent_type": "Cloud Agent (Built-in)",
                "agent_based": True,
                "supported_apis": {
                    "list_database_insights": "✅ Full Support",
                    "get_database_insight": "✅ Full Support",
                    "summarize_sql_statistics": "✅ Full Support",
                    "summarize_database_insight_resource_statistics": "✅ Full Support",
                    "summarize_database_insight_resource_capacity_trend": "✅ Full Support",
                    "summarize_database_insight_resource_forecast_trend": "✅ Full Support",
                    "warehouse_queries": "✅ Full Support",
                },
                "limitations": None,
                "recommended": True,
            },
            "EXTERNAL_MYSQL_DATABASE_SYSTEM": {
                "display_name": "External MySQL Database",
                "description": "External MySQL database system",
                "priority": 3,
                "agent_type": "External Database Agent",
                "agent_based": False,
                "supported_apis": {
                    "list_database_insights": "✅ Full Support",
                    "get_database_insight": "✅ Full Support",
                    "summarize_database_insight_resource_statistics": "✅ Partial Support",
                },
                "limitations": ["Limited API support compared to agent-based monitoring"],
                "recommended": False,
            },
        }

        # Sort databases by priority within each type
        for entity_type in databases_by_type:
            # Sort by database name for consistency
            databases_by_type[entity_type].sort(key=lambda x: x.get("database_name", ""))

        # Calculate summary with agent-based statistics
        total_dbs = sum(len(dbs) for dbs in databases_by_type.values())
        agent_based_dbs = sum(
            len(dbs) for entity_type, dbs in databases_by_type.items()
            if api_compatibility.get(entity_type, {}).get("agent_based", False)
        )

        # Create prioritized type list
        types_by_priority = sorted(
            databases_by_type.keys(),
            key=lambda t: api_compatibility.get(t, {}).get("priority", 99)
        )

        summary = {
            "total_databases": total_dbs,
            "agent_based_databases": agent_based_dbs,
            "agent_based_percentage": round((agent_based_dbs / total_dbs * 100) if total_dbs > 0 else 0, 1),
            "by_management_type": {
                entity_type: {
                    "count": len(databases_by_type[entity_type]),
                    "display_name": api_compatibility.get(entity_type, {}).get(
                        "display_name", entity_type
                    ),
                    "priority": api_compatibility.get(entity_type, {}).get("priority", 99),
                    "agent_type": api_compatibility.get(entity_type, {}).get("agent_type", "Unknown"),
                    "agent_based": api_compatibility.get(entity_type, {}).get("agent_based", False),
                    "recommended": api_compatibility.get(entity_type, {}).get("recommended", None),
                }
                for entity_type in types_by_priority
            },
            "management_types_found": types_by_priority,
            "recommendation": (
                "✅ Excellent! Most databases use agent-based monitoring with full API support."
                if agent_based_dbs / total_dbs > 0.8 else
                "⚠️ Consider migrating non-agent databases to Management Agent (MACS) for full API support."
            ) if total_dbs > 0 else "No databases found",
        }

        return {
            "compartment_id": compartment_id,
            "databases_by_type": databases_by_type,
            "api_compatibility": api_compatibility,
            "summary": summary,
            "profile_used": profile or "DEFAULT",
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def get_database_api_compatibility(
    database_insight_id: str,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get detailed API compatibility information for a specific database.

    This tool checks the management type of a database and returns which
    Operations Insights APIs are supported.

    Args:
        database_insight_id: Database insight OCID
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with API compatibility details
    """
    try:
        # Get client with optional profile
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile
            try:
                client = get_opsi_client()
            finally:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)
        else:
            client = get_opsi_client()

        # Get database insight details
        response = client.get_database_insight(database_insight_id)
        db_insight = response.data

        entity_source = getattr(db_insight, "entity_source", "UNKNOWN")
        database_type = db_insight.database_type
        status = db_insight.status

        # API compatibility matrix
        compatibility_matrix = {
            "MACS_MANAGED_EXTERNAL_DATABASE": {
                "sql_statistics": True,
                "resource_statistics": True,
                "capacity_trends": True,
                "forecasting": True,
                "sql_plans": True,
                "warehouse_queries": True,
            },
            "AUTONOMOUS": {
                "sql_statistics": True,
                "resource_statistics": True,
                "capacity_trends": True,
                "forecasting": True,
                "sql_plans": True,
                "warehouse_queries": True,
            },
            "EM_MANAGED_EXTERNAL_DATABASE": {
                "sql_statistics": False,
                "resource_statistics": True,
                "capacity_trends": True,
                "forecasting": False,
                "sql_plans": False,
                "warehouse_queries": True,
            },
            "PE_COMANAGED_DATABASE": {
                "sql_statistics": True,
                "resource_statistics": True,
                "capacity_trends": True,
                "forecasting": True,
                "sql_plans": True,
                "warehouse_queries": True,
            },
        }

        compatibility = compatibility_matrix.get(
            entity_source,
            {
                "sql_statistics": None,
                "resource_statistics": None,
                "capacity_trends": None,
                "forecasting": None,
                "sql_plans": None,
                "warehouse_queries": None,
            },
        )

        return {
            "database_insight_id": database_insight_id,
            "database_name": getattr(db_insight, "database_name", None),
            "database_display_name": getattr(db_insight, "database_display_name", None),
            "database_type": database_type,
            "entity_source": entity_source,
            "status": status,
            "api_compatibility": {
                "summarize_sql_statistics": {
                    "supported": compatibility["sql_statistics"],
                    "note": "Use warehouse queries for EM-Managed databases"
                    if not compatibility["sql_statistics"]
                    else "Full support",
                },
                "summarize_database_insight_resource_statistics": {
                    "supported": compatibility["resource_statistics"],
                    "note": "Full support",
                },
                "summarize_database_insight_resource_capacity_trend": {
                    "supported": compatibility["capacity_trends"],
                    "note": "Full support",
                },
                "summarize_database_insight_resource_forecast_trend": {
                    "supported": compatibility["forecasting"],
                    "note": "Limited for EM-Managed databases",
                },
                "get_sql_plan": {
                    "supported": compatibility["sql_plans"],
                    "note": "Not available for EM-Managed databases",
                },
                "query_warehouse_standard": {
                    "supported": compatibility["warehouse_queries"],
                    "note": "Requires warehouse to be enabled",
                },
            },
            "recommendations": _get_recommendations(entity_source, compatibility),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_insight_id": database_insight_id,
        }


def _get_recommendations(entity_source: str, compatibility: dict) -> list[str]:
    """Generate recommendations based on management type."""
    recommendations = []

    if entity_source == "EM_MANAGED_EXTERNAL_DATABASE":
        recommendations.extend(
            [
                "Consider enabling Operations Insights warehouse for SQL statistics",
                "For full API support, migrate to Management Agent (MACS)",
                "Use Database Management Service for SQL performance analysis",
            ]
        )
    elif entity_source in ["MACS_MANAGED_EXTERNAL_DATABASE", "AUTONOMOUS"]:
        recommendations.append("✅ Optimal configuration - all APIs fully supported")

    if not compatibility.get("sql_statistics"):
        recommendations.append("Enable warehouse queries for SQL statistics access")

    return recommendations if recommendations else ["No specific recommendations"]


def get_available_oci_profiles() -> dict[str, Any]:
    """
    List all available OCI CLI profiles for multi-tenancy support.

    Returns profile details including tenancy, region, and user information.

    Returns:
        Dictionary with available profiles and their configurations
    """
    try:
        from .config import get_oci_config
        import configparser
        from pathlib import Path

        # Read OCI config file
        config_file = Path.home() / ".oci" / "config"
        if not config_file.exists():
            return {
                "error": "OCI config file not found",
                "expected_location": str(config_file),
            }

        config = configparser.ConfigParser()
        config.read(config_file)

        profiles = {}
        for profile_name in config.sections():
            try:
                # Get profile config
                import os
                old_profile = os.environ.get("OCI_CLI_PROFILE")
                os.environ["OCI_CLI_PROFILE"] = profile_name

                try:
                    profile_config = get_oci_config()

                    # Get tenancy info
                    identity_client = oci.identity.IdentityClient(profile_config)
                    tenancy = identity_client.get_tenancy(profile_config["tenancy"]).data

                    profiles[profile_name] = {
                        "profile_name": profile_name,
                        "tenancy_id": profile_config.get("tenancy"),
                        "tenancy_name": tenancy.name,
                        "region": profile_config.get("region"),
                        "user_id": profile_config.get("user"),
                        "fingerprint": profile_config.get("fingerprint"),
                        "is_active": profile_name == (old_profile or "DEFAULT"),
                    }
                finally:
                    if old_profile:
                        os.environ["OCI_CLI_PROFILE"] = old_profile
                    else:
                        os.environ.pop("OCI_CLI_PROFILE", None)

            except Exception as e:
                profiles[profile_name] = {
                    "profile_name": profile_name,
                    "error": str(e),
                    "status": "invalid",
                }

        return {
            "profiles": profiles,
            "total_profiles": len(profiles),
            "config_file": str(config_file),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }
