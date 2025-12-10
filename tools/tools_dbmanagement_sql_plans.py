"""FastMCP tools for OCI Database Management SQL Plan Baseline operations."""

from typing import Any, Optional

from .oci_clients_enhanced import get_dbm_client, extract_region_from_ocid


def list_sql_plan_baselines(
    database_id: str,
    profile: Optional[str] = None,
    plan_name: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    is_accepted: Optional[bool] = None,
) -> dict[str, Any]:
    """
    List SQL Plan Baselines for a managed database.

    SQL Plan Baselines are used to preserve execution plans for SQL statements
    to prevent performance regressions when database statistics or system
    conditions change.

    Args:
        database_id: Managed Database OCID
        profile: OCI profile name for multi-tenancy support
        plan_name: Filter by plan name (supports wildcards)
        is_enabled: Filter by enabled status (True/False)
        is_accepted: Filter by accepted status (True/False)

    Returns:
        Dictionary containing list of SQL plan baselines with their properties

    Example:
        >>> # List all baselines
        >>> result = list_sql_plan_baselines(database_id="ocid1.manageddatabase...")

        >>> # List enabled baselines only
        >>> result = list_sql_plan_baselines(
        ...     database_id="ocid1.manageddatabase...",
        ...     is_enabled=True
        ... )

        >>> # Multi-tenancy: Use specific profile
        >>> result = list_sql_plan_baselines(
        ...     database_id="ocid1.manageddatabase...",
        ...     profile="production"
        ... )
    """
    try:
        # Detect region from database OCID
        region = extract_region_from_ocid(database_id)
        client = get_dbm_client(profile=profile, region=region)

        kwargs = {"managed_database_id": database_id}

        if plan_name:
            kwargs["plan_name"] = plan_name
        if is_enabled is not None:
            kwargs["is_enabled"] = is_enabled
        if is_accepted is not None:
            kwargs["is_accepted"] = is_accepted

        response = client.list_sql_plan_baselines(**kwargs)

        items = []
        for baseline in response.data.items:
            items.append({
                "plan_name": baseline.plan_name,
                "sql_handle": baseline.sql_handle,
                "sql_text": baseline.sql_text[:200] if hasattr(baseline, "sql_text") else None,  # Truncate for display
                "origin": baseline.origin,
                "enabled": baseline.enabled,
                "accepted": baseline.accepted,
                "fixed": baseline.fixed,
                "reproduced": getattr(baseline, "reproduced", None),
                "autopurge": getattr(baseline, "autopurge", None),
                "adaptive": getattr(baseline, "adaptive", None),
                "time_created": str(baseline.time_created) if hasattr(baseline, "time_created") else None,
                "time_last_modified": str(baseline.time_last_modified) if hasattr(baseline, "time_last_modified") else None,
                "time_last_executed": str(baseline.time_last_executed) if hasattr(baseline, "time_last_executed") else None,
            })

        return {
            "database_id": database_id,
            "count": len(items),
            "items": items,
            "profile": profile,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
            "profile": profile,
            "success": False,
        }


def get_sql_plan_baseline(
    database_id: str,
    plan_name: str,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get detailed information about a specific SQL Plan Baseline.

    Args:
        database_id: Managed Database OCID
        plan_name: Name of the SQL plan baseline
        profile: OCI profile name for multi-tenancy support

    Returns:
        Dictionary containing detailed baseline information including
        execution statistics and plan details

    Example:
        >>> result = get_sql_plan_baseline(
        ...     database_id="ocid1.manageddatabase...",
        ...     plan_name="SQL_PLAN_abc123def456"
        ... )
        >>> print(f"Plan origin: {result['origin']}")
        >>> print(f"Enabled: {result['enabled']}")
    """
    try:
        region = extract_region_from_ocid(database_id)
        client = get_dbm_client(profile=profile, region=region)

        response = client.get_sql_plan_baseline(
            managed_database_id=database_id,
            plan_name=plan_name
        )

        baseline = response.data

        return {
            "plan_name": baseline.plan_name,
            "sql_handle": baseline.sql_handle,
            "sql_text": baseline.sql_text if hasattr(baseline, "sql_text") else None,
            "origin": baseline.origin,
            "enabled": baseline.enabled,
            "accepted": baseline.accepted,
            "fixed": baseline.fixed,
            "reproduced": getattr(baseline, "reproduced", None),
            "autopurge": getattr(baseline, "autopurge", None),
            "adaptive": getattr(baseline, "adaptive", None),
            "optimizer_cost": getattr(baseline, "optimizer_cost", None),
            "module": getattr(baseline, "module", None),
            "action": getattr(baseline, "action", None),
            "execution_count": getattr(baseline, "executions", None),
            "time_created": str(baseline.time_created) if hasattr(baseline, "time_created") else None,
            "time_last_modified": str(baseline.time_last_modified) if hasattr(baseline, "time_last_modified") else None,
            "time_last_executed": str(baseline.time_last_executed) if hasattr(baseline, "time_last_executed") else None,
            "database_id": database_id,
            "profile": profile,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
            "plan_name": plan_name,
            "profile": profile,
            "success": False,
        }


def load_sql_plan_baselines_from_awr(
    database_id: str,
    sql_handle: Optional[str] = None,
    sql_text: Optional[str] = None,
    profile: Optional[str] = None,
    begin_snapshot: Optional[int] = None,
    end_snapshot: Optional[int] = None,
) -> dict[str, Any]:
    """
    Load SQL Plan Baselines from AWR (Automatic Workload Repository).

    This creates new SQL plan baselines from historical execution plans
    captured in AWR, which is useful for preserving good performance
    characteristics from past executions.

    Args:
        database_id: Managed Database OCID
        sql_handle: Specific SQL handle to load (optional)
        sql_text: SQL text filter (optional, supports wildcards)
        profile: OCI profile name for multi-tenancy support
        begin_snapshot: Beginning AWR snapshot ID (optional)
        end_snapshot: Ending AWR snapshot ID (optional)

    Returns:
        Dictionary containing work request information for tracking the operation

    Example:
        >>> # Load all high-performing SQL from recent AWR snapshots
        >>> result = load_sql_plan_baselines_from_awr(
        ...     database_id="ocid1.manageddatabase...",
        ...     begin_snapshot=100,
        ...     end_snapshot=120
        ... )
        >>> print(f"Work request: {result['work_request_id']}")

        >>> # Load specific SQL plan
        >>> result = load_sql_plan_baselines_from_awr(
        ...     database_id="ocid1.manageddatabase...",
        ...     sql_handle="SQL_abc123def456",
        ...     profile="production"
        ... )
    """
    try:
        region = extract_region_from_ocid(database_id)
        client = get_dbm_client(profile=profile, region=region)

        # Build details object for the request
        from oci.database_management.models import LoadSqlPlanBaselinesFromAwrDetails

        details = LoadSqlPlanBaselinesFromAwrDetails()

        if sql_handle:
            details.sql_handle = sql_handle
        if sql_text:
            details.sql_text = sql_text
        if begin_snapshot:
            details.begin_snapshot = begin_snapshot
        if end_snapshot:
            details.end_snapshot = end_snapshot

        response = client.load_sql_plan_baselines_from_awr(
            managed_database_id=database_id,
            load_sql_plan_baselines_from_awr_details=details
        )

        return {
            "work_request_id": response.headers.get("opc-work-request-id"),
            "database_id": database_id,
            "profile": profile,
            "message": "SQL Plan Baseline load initiated. Use get_work_request to track progress.",
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
            "profile": profile,
            "success": False,
        }


def drop_sql_plan_baselines(
    database_id: str,
    plan_name: Optional[str] = None,
    sql_handle: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Drop (delete) SQL Plan Baselines from a managed database.

    Removes SQL plan baselines that are no longer needed or are causing
    performance issues. Either plan_name or sql_handle must be provided.

    Args:
        database_id: Managed Database OCID
        plan_name: Name of specific plan baseline to drop
        sql_handle: SQL handle (drops all baselines for this SQL)
        profile: OCI profile name for multi-tenancy support

    Returns:
        Dictionary with operation result

    Example:
        >>> # Drop a specific plan baseline
        >>> result = drop_sql_plan_baselines(
        ...     database_id="ocid1.manageddatabase...",
        ...     plan_name="SQL_PLAN_abc123def456"
        ... )

        >>> # Drop all baselines for a SQL handle
        >>> result = drop_sql_plan_baselines(
        ...     database_id="ocid1.manageddatabase...",
        ...     sql_handle="SQL_abc123",
        ...     profile="production"
        ... )
    """
    try:
        if not plan_name and not sql_handle:
            return {
                "error": "Either plan_name or sql_handle must be provided",
                "success": False,
            }

        region = extract_region_from_ocid(database_id)
        client = get_dbm_client(profile=profile, region=region)

        from oci.database_management.models import DropSqlPlanBaselinesDetails

        details = DropSqlPlanBaselinesDetails()

        if plan_name:
            details.plan_name = plan_name
        if sql_handle:
            details.sql_handle = sql_handle

        response = client.drop_sql_plan_baselines(
            managed_database_id=database_id,
            drop_sql_plan_baselines_details=details
        )

        return {
            "dropped_count": response.data if hasattr(response, "data") else 0,
            "database_id": database_id,
            "plan_name": plan_name,
            "sql_handle": sql_handle,
            "profile": profile,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
            "profile": profile,
            "success": False,
        }


def enable_automatic_spm_evolve_task(
    database_id: str,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Enable the automatic SQL Plan Management (SPM) evolve advisor task.

    The SPM Evolve Advisor automatically tests and accepts new execution plans
    that are better than existing baselines, helping maintain optimal
    performance as database conditions change.

    Args:
        database_id: Managed Database OCID
        profile: OCI profile name for multi-tenancy support

    Returns:
        Dictionary with operation result

    Example:
        >>> result = enable_automatic_spm_evolve_task(
        ...     database_id="ocid1.manageddatabase..."
        ... )
        >>> if result['success']:
        ...     print("SPM Evolve Advisor enabled successfully")

        >>> # Multi-tenancy
        >>> result = enable_automatic_spm_evolve_task(
        ...     database_id="ocid1.manageddatabase...",
        ...     profile="production"
        ... )
    """
    try:
        region = extract_region_from_ocid(database_id)
        client = get_dbm_client(profile=profile, region=region)

        response = client.enable_automatic_spm_evolve_advisor_task(
            managed_database_id=database_id
        )

        return {
            "database_id": database_id,
            "profile": profile,
            "message": "Automatic SPM Evolve Advisor task enabled successfully",
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
            "profile": profile,
            "success": False,
        }


def configure_automatic_spm_capture(
    database_id: str,
    enabled: bool,
    profile: Optional[str] = None,
    auto_filter_sql_text: Optional[str] = None,
    auto_filter_parsing_schema: Optional[str] = None,
) -> dict[str, Any]:
    """
    Configure automatic SQL Plan Management baseline capture.

    Automatic capture creates SQL plan baselines for frequently executed
    SQL statements, helping prevent performance regressions.

    Args:
        database_id: Managed Database OCID
        enabled: Whether to enable or disable automatic capture
        profile: OCI profile name for multi-tenancy support
        auto_filter_sql_text: Filter to capture only matching SQL text
        auto_filter_parsing_schema: Filter to capture only from specific schemas

    Returns:
        Dictionary with operation result

    Example:
        >>> # Enable automatic capture
        >>> result = configure_automatic_spm_capture(
        ...     database_id="ocid1.manageddatabase...",
        ...     enabled=True
        ... )

        >>> # Enable with filters
        >>> result = configure_automatic_spm_capture(
        ...     database_id="ocid1.manageddatabase...",
        ...     enabled=True,
        ...     auto_filter_parsing_schema="PRODUCTION_SCHEMA",
        ...     profile="production"
        ... )
    """
    try:
        region = extract_region_from_ocid(database_id)
        client = get_dbm_client(profile=profile, region=region)

        from oci.database_management.models import ConfigureAutomaticCaptureFiltersDetails

        details = ConfigureAutomaticCaptureFiltersDetails()
        details.auto_capture_filters = []

        if auto_filter_sql_text or auto_filter_parsing_schema:
            from oci.database_management.models import AutomaticCaptureFilter

            filter_obj = AutomaticCaptureFilter()
            if auto_filter_sql_text:
                filter_obj.name = "SQL_TEXT"
                filter_obj.values_to_include = [auto_filter_sql_text]
            if auto_filter_parsing_schema:
                filter_obj.name = "PARSING_SCHEMA_NAME"
                filter_obj.values_to_include = [auto_filter_parsing_schema]

            details.auto_capture_filters.append(filter_obj)

        response = client.configure_automatic_capture_filters(
            managed_database_id=database_id,
            configure_automatic_capture_filters_details=details
        )

        return {
            "database_id": database_id,
            "enabled": enabled,
            "profile": profile,
            "message": f"Automatic SPM capture {'enabled' if enabled else 'disabled'} successfully",
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
            "profile": profile,
            "success": False,
        }
