"""FastMCP tools for diagnosing Operations Insights authorization and configuration issues."""

from typing import Any, Optional
from datetime import datetime, timedelta

from .oci_clients_enhanced import get_opsi_client, get_dbm_client, get_identity_client
from .config_enhanced import get_oci_config


def diagnose_opsi_permissions(
    compartment_id: str,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Diagnose Operations Insights IAM permissions and identify missing policies.

    This tool checks what Operations Insights operations work and which fail,
    helping identify missing IAM permissions for SQL-level insights.

    Args:
        compartment_id: Compartment OCID to test permissions in
        profile: OCI profile name for multi-tenancy support

    Returns:
        Dictionary with permission test results and recommendations

    Example:
        >>> result = diagnose_opsi_permissions(
        ...     compartment_id="ocid1.compartment.oc1...",
        ...     profile="production"
        ... )
        >>> for test in result['tests']:
        ...     print(f"{test['operation']}: {test['status']}")
    """
    try:
        opsi_client = get_opsi_client(profile=profile)

        test_results = []
        required_permissions = []

        # Test 1: List database insights (basic read)
        try:
            opsi_client.list_database_insights(
                compartment_id=compartment_id,
                limit=1
            )
            test_results.append({
                "operation": "list_database_insights",
                "status": "✓ ALLOWED",
                "permission": "OPSI_DATABASE_INSIGHT_READ",
                "level": "basic"
            })
        except Exception as e:
            test_results.append({
                "operation": "list_database_insights",
                "status": "✗ DENIED",
                "error": str(e),
                "permission": "OPSI_DATABASE_INSIGHT_READ",
                "level": "basic"
            })
            required_permissions.append("Allow group <your-group> to read opsi-database-insights in compartment <your-compartment>")

        # Test 2: Summarize SQL statistics (SQL-level insights)
        try:
            time_end = datetime.utcnow()
            time_start = time_end - timedelta(days=1)

            opsi_client.summarize_sql_statistics(
                compartment_id=compartment_id,
                time_interval_start=time_start.isoformat(),
                time_interval_end=time_end.isoformat(),
                limit=1
            )
            test_results.append({
                "operation": "summarize_sql_statistics",
                "status": "✓ ALLOWED",
                "permission": "OPSI_WAREHOUSE_DATA_OBJECT_READ",
                "level": "sql-insights"
            })
        except Exception as e:
            error_msg = str(e)
            test_results.append({
                "operation": "summarize_sql_statistics",
                "status": "✗ DENIED",
                "error": error_msg,
                "permission": "OPSI_WAREHOUSE_DATA_OBJECT_READ",
                "level": "sql-insights"
            })

            if "NotAuthorizedOrNotFound" in error_msg or "authorization" in error_msg.lower():
                required_permissions.append("Allow group <your-group> to read opsi-warehouse-data-objects in compartment <your-compartment>")

        # Test 3: Query warehouse (advanced SQL queries)
        try:
            opsi_client.query_opsi_data_objects(
                compartment_id=compartment_id,
                query_opsi_data_object_data_details={
                    "compartmentId": compartment_id,
                    "dataObjectType": "HOST_INSIGHTS_DATA_OBJECT",
                    "query": "SELECT 1 FROM dual"
                }
            )
            test_results.append({
                "operation": "query_opsi_data_objects",
                "status": "✓ ALLOWED",
                "permission": "OPSI_DATA_OBJECTS_QUERY",
                "level": "advanced"
            })
        except Exception as e:
            error_msg = str(e)
            test_results.append({
                "operation": "query_opsi_data_objects",
                "status": "✗ DENIED",
                "error": error_msg,
                "permission": "OPSI_DATA_OBJECTS_QUERY",
                "level": "advanced"
            })

            if "NotAuthorizedOrNotFound" in error_msg or "authorization" in error_msg.lower():
                required_permissions.append("Allow group <your-group> to use opsi-data-objects in compartment <your-compartment>")

        # Determine overall status
        allowed_count = sum(1 for t in test_results if "✓" in t["status"])
        denied_count = sum(1 for t in test_results if "✗" in t["status"])

        return {
            "compartment_id": compartment_id,
            "profile": profile,
            "summary": {
                "total_tests": len(test_results),
                "allowed": allowed_count,
                "denied": denied_count,
                "status": "FULL_ACCESS" if denied_count == 0 else "PARTIAL_ACCESS" if allowed_count > 0 else "NO_ACCESS"
            },
            "tests": test_results,
            "required_permissions": required_permissions if required_permissions else None,
            "recommendations": generate_permission_recommendations(test_results),
            "success": True
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "profile": profile,
            "success": False
        }


def generate_permission_recommendations(test_results: list) -> list[str]:
    """Generate actionable permission recommendations based on test results."""
    recommendations = []

    # Check what's failing
    denied_operations = [t for t in test_results if "✗" in t["status"]]

    if not denied_operations:
        recommendations.append("✓ All tested permissions are working correctly")
        return recommendations

    # Basic read permissions
    if any(t["operation"] == "list_database_insights" for t in denied_operations):
        recommendations.append(
            "CRITICAL: Missing basic read permissions. Add policy:\n"
            "  Allow group <YourGroup> to read opsi-database-insights in compartment <YourCompartment>"
        )

    # SQL-level insights
    if any(t["level"] == "sql-insights" for t in denied_operations):
        recommendations.append(
            "IMPORTANT: Missing SQL-level insights permissions. Add policies:\n"
            "  Allow group <YourGroup> to read opsi-warehouse-data-objects in compartment <YourCompartment>\n"
            "  Allow group <YourGroup> to read opsi-sql-search in compartment <YourCompartment>"
        )

    # Advanced permissions
    if any(t["level"] == "advanced" for t in denied_operations):
        recommendations.append(
            "OPTIONAL: Missing advanced query permissions. Add policy:\n"
            "  Allow group <YourGroup> to use opsi-data-objects in compartment <YourCompartment>"
        )

    # General recommendation
    recommendations.append(
        "\nFor full Operations Insights functionality, use this comprehensive policy:\n"
        "  Allow group <YourGroup> to manage operations-insights-family in compartment <YourCompartment>"
    )

    return recommendations


def check_sqlwatch_status_bulk(
    compartment_id: str,
    profile: Optional[str] = None,
    lifecycle_state: str = "ACTIVE",
) -> dict[str, Any]:
    """
    Check SQL Watch status across all managed databases in a compartment.

    SQL Watch is required for detailed SQL-level monitoring in Operations Insights.
    This tool helps identify which databases need SQL Watch enabled.

    Args:
        compartment_id: Compartment OCID
        profile: OCI profile name for multi-tenancy support
        lifecycle_state: Filter by lifecycle state (default: ACTIVE)

    Returns:
        Dictionary with SQL Watch status for each database

    Example:
        >>> result = check_sqlwatch_status_bulk(
        ...     compartment_id="ocid1.compartment.oc1...",
        ...     profile="production"
        ... )
        >>> print(f"SQL Watch enabled: {result['summary']['enabled_count']}")
        >>> print(f"SQL Watch disabled: {result['summary']['disabled_count']}")
    """
    try:
        dbm_client = get_dbm_client(profile=profile)

        # List all managed databases
        from .oci_clients_enhanced import list_all

        managed_dbs = list_all(
            dbm_client.list_managed_databases,
            compartment_id=compartment_id,
            lifecycle_state=lifecycle_state
        )

        results = []
        enabled_count = 0
        disabled_count = 0
        error_count = 0

        for db in managed_dbs:
            try:
                # Check SQL Watch status
                response = dbm_client.get_sql_watch_status(
                    managed_database_id=db.id
                )

                is_enabled = response.data.status == "ENABLED"

                results.append({
                    "database_id": db.id,
                    "database_name": db.name,
                    "database_type": getattr(db, "database_type", "Unknown"),
                    "sqlwatch_status": response.data.status,
                    "sqlwatch_enabled": is_enabled,
                    "em_managed": getattr(db, "management_option", None) == "ADVANCED",
                    "status": "✓ Enabled" if is_enabled else "✗ Disabled"
                })

                if is_enabled:
                    enabled_count += 1
                else:
                    disabled_count += 1

            except Exception as e:
                results.append({
                    "database_id": db.id,
                    "database_name": db.name,
                    "database_type": getattr(db, "database_type", "Unknown"),
                    "sqlwatch_status": "ERROR",
                    "sqlwatch_enabled": False,
                    "error": str(e),
                    "status": "⚠ Error"
                })
                error_count += 1

        return {
            "compartment_id": compartment_id,
            "profile": profile,
            "summary": {
                "total_databases": len(results),
                "enabled_count": enabled_count,
                "disabled_count": disabled_count,
                "error_count": error_count,
                "enabled_percentage": (enabled_count / len(results) * 100) if results else 0
            },
            "databases": results,
            "recommendations": generate_sqlwatch_recommendations(results),
            "success": True
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "profile": profile,
            "success": False
        }


def generate_sqlwatch_recommendations(database_results: list) -> list[str]:
    """Generate recommendations based on SQL Watch status."""
    recommendations = []

    disabled_dbs = [db for db in database_results if not db.get("sqlwatch_enabled")]
    em_managed = [db for db in disabled_dbs if db.get("em_managed")]

    if not disabled_dbs:
        recommendations.append("✓ SQL Watch is enabled on all databases")
        return recommendations

    recommendations.append(
        f"⚠ SQL Watch is disabled on {len(disabled_dbs)} database(s)"
    )

    if em_managed:
        recommendations.append(
            f"\n{len(em_managed)} EM-managed database(s) require SQL Watch enablement:\n"
            "  For EM-managed databases, SQL Watch must be enabled through Enterprise Manager\n"
            "  or using the enable_sqlwatch() tool with proper credentials"
        )

    non_em = [db for db in disabled_dbs if not db.get("em_managed")]
    if non_em:
        recommendations.append(
            f"\n{len(non_em)} non-EM database(s) can be enabled using:\n"
            "  enable_sqlwatch_bulk() tool"
        )

    recommendations.append(
        "\nSQL Watch is required for:\n"
        "  - Detailed SQL performance metrics\n"
        "  - SQL text and execution statistics\n"
        "  - SQL tuning recommendations\n"
        "  - Advanced performance analytics"
    )

    return recommendations


def check_database_insights_configuration(
    compartment_id: str,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Check Operations Insights configuration for all database insights.

    Identifies databases that are registered but may have incomplete configuration
    for SQL-level monitoring.

    Args:
        compartment_id: Compartment OCID
        profile: OCI profile name for multi-tenancy support

    Returns:
        Dictionary with configuration status for each database insight

    Example:
        >>> result = check_database_insights_configuration(
        ...     compartment_id="ocid1.compartment.oc1...",
        ...     profile="production"
        ... )
        >>> for db in result['databases']:
        ...     if db['issues']:
        ...         print(f"{db['name']}: {db['issues']}")
    """
    try:
        opsi_client = get_opsi_client(profile=profile)

        # List all database insights
        from .oci_clients_enhanced import list_all

        insights = list_all(
            opsi_client.list_database_insights,
            compartment_id=compartment_id,
            lifecycle_state="ACTIVE"
        )

        results = []
        fully_configured = 0
        issues_found = 0

        for insight in insights:
            issues = []

            # Check if enabled
            if insight.status != "ENABLED":
                issues.append(f"Status is {insight.status}, not ENABLED")

            # Check entity source (should be EM or MDS for EM-managed)
            entity_source = getattr(insight, "entity_source", "Unknown")
            if entity_source == "EM_MANAGED_EXTERNAL_DATABASE":
                # This is EM-managed, check additional requirements
                if not hasattr(insight, "enterprise_manager_identifier"):
                    issues.append("Missing Enterprise Manager identifier")
                if not hasattr(insight, "enterprise_manager_bridge_id"):
                    issues.append("Missing Enterprise Manager bridge configuration")

            # Check for SQL collection features
            # Note: Some attributes may not be available depending on database type
            db_info = {
                "database_id": insight.id,
                "database_name": insight.database_name,
                "database_display_name": getattr(insight, "database_display_name", insight.database_name),
                "database_type": insight.database_type,
                "entity_source": entity_source,
                "status": insight.status,
                "lifecycle_state": insight.lifecycle_state,
                "issues": issues,
                "configuration_status": "✓ Fully Configured" if not issues else "⚠ Issues Found",
                "em_managed": entity_source == "EM_MANAGED_EXTERNAL_DATABASE"
            }

            results.append(db_info)

            if not issues:
                fully_configured += 1
            else:
                issues_found += 1

        return {
            "compartment_id": compartment_id,
            "profile": profile,
            "summary": {
                "total_insights": len(results),
                "fully_configured": fully_configured,
                "issues_found": issues_found,
                "em_managed_count": sum(1 for db in results if db["em_managed"])
            },
            "databases": results,
            "recommendations": generate_insights_recommendations(results),
            "success": True
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "profile": profile,
            "success": False
        }


def generate_insights_recommendations(database_results: list) -> list[str]:
    """Generate recommendations based on database insights configuration."""
    recommendations = []

    em_managed = [db for db in database_results if db.get("em_managed")]
    issues = [db for db in database_results if db.get("issues")]

    if not issues:
        recommendations.append("✓ All database insights are fully configured")
        return recommendations

    if em_managed:
        recommendations.append(
            f"⚠ {len(em_managed)} EM-managed database(s) detected\n"
            "\nFor EM-managed databases, ensure:\n"
            "1. Enterprise Manager bridge is properly configured\n"
            "2. EM agent is running and can communicate with OCI\n"
            "3. SQL Watch is enabled in Enterprise Manager\n"
            "4. EM Discovery job has run successfully\n"
            "5. Database credentials are configured in EM for monitoring"
        )

    recommendations.append(
        "\nFor SQL-level insights to work, verify:\n"
        "1. IAM permissions (use diagnose_opsi_permissions tool)\n"
        "2. SQL Watch status (use check_sqlwatch_status_bulk tool)\n"
        "3. Database Management service is enabled\n"
        "4. Network connectivity between database and OCI services"
    )

    return recommendations


def get_comprehensive_diagnostics(
    compartment_id: str,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Run comprehensive diagnostics for Operations Insights SQL analytics issues.

    This combines all diagnostic checks to provide a complete picture of
    configuration and permission issues.

    Args:
        compartment_id: Compartment OCID
        profile: OCI profile name for multi-tenancy support

    Returns:
        Dictionary with complete diagnostic results and action plan

    Example:
        >>> result = get_comprehensive_diagnostics(
        ...     compartment_id="ocid1.compartment.oc1...",
        ...     profile="production"
        ... )
        >>> print(result['action_plan'])
    """
    try:
        print("Running comprehensive diagnostics...")

        # 1. Check IAM permissions
        print("  1/3 Checking IAM permissions...")
        perm_result = diagnose_opsi_permissions(compartment_id, profile)

        # 2. Check SQL Watch status
        print("  2/3 Checking SQL Watch status...")
        sqlwatch_result = check_sqlwatch_status_bulk(compartment_id, profile)

        # 3. Check database insights configuration
        print("  3/3 Checking database insights configuration...")
        insights_result = check_database_insights_configuration(compartment_id, profile)

        # Generate action plan
        action_plan = []
        priority = 1

        # Permission issues (highest priority)
        if perm_result.get("summary", {}).get("denied", 0) > 0:
            action_plan.append({
                "priority": priority,
                "category": "IAM Permissions",
                "issue": f"{perm_result['summary']['denied']} permission(s) denied",
                "actions": perm_result.get("required_permissions", []),
                "severity": "CRITICAL"
            })
            priority += 1

        # SQL Watch issues
        disabled_count = sqlwatch_result.get("summary", {}).get("disabled_count", 0)
        if disabled_count > 0:
            action_plan.append({
                "priority": priority,
                "category": "SQL Watch",
                "issue": f"SQL Watch disabled on {disabled_count} database(s)",
                "actions": [
                    "Use enable_sqlwatch_bulk() to enable SQL Watch on eligible databases",
                    "For EM-managed databases, enable SQL Watch through Enterprise Manager"
                ],
                "severity": "HIGH"
            })
            priority += 1

        # Configuration issues
        config_issues = insights_result.get("summary", {}).get("issues_found", 0)
        if config_issues > 0:
            action_plan.append({
                "priority": priority,
                "category": "Configuration",
                "issue": f"{config_issues} database(s) with configuration issues",
                "actions": insights_result.get("recommendations", []),
                "severity": "MEDIUM"
            })
            priority += 1

        # Overall status
        overall_status = "HEALTHY"
        if len(action_plan) > 0:
            severities = [item["severity"] for item in action_plan]
            if "CRITICAL" in severities:
                overall_status = "CRITICAL_ISSUES"
            elif "HIGH" in severities:
                overall_status = "HIGH_PRIORITY_ISSUES"
            else:
                overall_status = "MINOR_ISSUES"

        return {
            "compartment_id": compartment_id,
            "profile": profile,
            "overall_status": overall_status,
            "diagnostics": {
                "permissions": perm_result,
                "sqlwatch": sqlwatch_result,
                "insights_configuration": insights_result
            },
            "action_plan": action_plan,
            "summary": {
                "total_databases": insights_result.get("summary", {}).get("total_insights", 0),
                "permission_issues": perm_result.get("summary", {}).get("denied", 0),
                "sqlwatch_disabled": disabled_count,
                "configuration_issues": config_issues,
                "em_managed_databases": insights_result.get("summary", {}).get("em_managed_count", 0)
            },
            "success": True
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "profile": profile,
            "success": False
        }
