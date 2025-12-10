"""FastMCP tools for OCI Operations Insights SQL Insights and advanced analytics."""

from datetime import datetime, timedelta
from typing import Any, Optional

from .oci_clients_enhanced import get_opsi_client, extract_region_from_ocid


def summarize_sql_insights(
    compartment_id: str,
    profile: Optional[str] = None,
    database_id: Optional[list[str]] = None,
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
    database_time_pct_greater_than: Optional[float] = None,
) -> dict[str, Any]:
    """

    **DEPRECATED**: This API returns 404 errors and is not available in OCI.

    **Reason**: 2 APIs return 404 - Not available

    **Status**: Not deployed to OCI service (as of Nov 2025)
    
    Get SQL performance insights with anomaly detection.

    Analyzes SQL statements that are consuming significant database time and
    identifies performance anomalies, trends, and outliers. This is a powerful
    tool for proactive performance monitoring.

    Args:
        compartment_id: Compartment OCID
        profile: OCI profile name for multi-tenancy support
        database_id: List of database insight OCIDs to analyze (optional)
        time_interval_start: Start time (ISO 8601 format, defaults to 7 days ago)
        time_interval_end: End time (ISO 8601 format, defaults to now)
        database_time_pct_greater_than: Filter to SQL consuming more than this % of DB time

    Returns:
        Dictionary containing SQL insights with performance analysis

    Example:
        >>> # Get SQL insights for past 24 hours, DB time > 5%
        >>> result = summarize_sql_insights(
        ...     compartment_id="ocid1.compartment...",
        ...     database_time_pct_greater_than=5.0,
        ...     time_interval_start=(datetime.now() - timedelta(days=1)).isoformat(),
        ...     time_interval_end=datetime.now().isoformat()
        ... )

        >>> # Multi-tenancy: Analyze specific databases in production
        >>> result = summarize_sql_insights(
        ...     compartment_id="ocid1.compartment...",
        ...     database_id=["ocid1.databaseinsight..."],
        ...     profile="production"
        ... )
    """
    try:
        client = get_opsi_client(profile=profile)

        # Default time range: last 7 days
        if not time_interval_end:
            time_interval_end = datetime.utcnow().isoformat()
        if not time_interval_start:
            start_time = datetime.utcnow() - timedelta(days=7)
            time_interval_start = start_time.isoformat()

        from oci.opsi.models import SummarizeSqlInsightsDetails

        details = SummarizeSqlInsightsDetails()
        details.compartment_id = compartment_id
        details.time_interval_start = time_interval_start
        details.time_interval_end = time_interval_end

        if database_id:
            details.database_id = database_id
        if database_time_pct_greater_than is not None:
            details.database_time_pct_greater_than = database_time_pct_greater_than

        response = client.summarize_sql_insights(
            summarize_sql_insights_details=details
        )

        items = []
        if hasattr(response.data, "items"):
            for insight in response.data.items:
                items.append({
                    "sql_identifier": insight.sql_identifier,
                    "sql_text": insight.sql_text[:500] if hasattr(insight, "sql_text") else None,  # Truncate
                    "database_details": {
                        "id": getattr(insight, "id", None),
                        "database_id": getattr(insight, "database_id", None),
                        "database_name": getattr(insight, "database_name", None),
                        "database_display_name": getattr(insight, "database_display_name", None),
                    },
                    "performance_metrics": {
                        "database_time_pct": getattr(insight, "database_time_pct", None),
                        "executions_per_hour": getattr(insight, "executions_per_hour", None),
                        "cpu_time_in_sec": getattr(insight, "cpu_time_in_sec", None),
                        "io_time_in_sec": getattr(insight, "io_time_in_sec", None),
                        "inefficient_wait_time_in_sec": getattr(insight, "inefficient_wait_time_in_sec", None),
                    },
                    "insights": {
                        "category": getattr(insight, "category", None),
                        "impact": getattr(insight, "impact", None),
                        "recommendation": getattr(insight, "recommendation", None),
                    },
                })

        return {
            "compartment_id": compartment_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "count": len(items),
            "items": items,
            "profile": profile,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "profile": profile,
            "success": False,
        }


def summarize_sql_plan_insights(
    compartment_id: str,
    sql_identifier: str,
    profile: Optional[str] = None,
    database_id: Optional[list[str]] = None,
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
) -> dict[str, Any]:
    """
    Analyze execution plan performance for a specific SQL statement.

    Identifies which execution plans are being used for a SQL statement and
    compares their performance. Useful for detecting plan regressions and
    identifying optimal plans.

    Args:
        compartment_id: Compartment OCID
        sql_identifier: SQL identifier to analyze
        profile: OCI profile name for multi-tenancy support
        database_id: List of database insight OCIDs (optional)
        time_interval_start: Start time (ISO 8601 format, defaults to 7 days ago)
        time_interval_end: End time (ISO 8601 format, defaults to now)

    Returns:
        Dictionary containing plan insights and performance comparison

    Example:
        >>> # Analyze plan performance for a specific SQL
        >>> result = summarize_sql_plan_insights(
        ...     compartment_id="ocid1.compartment...",
        ...     sql_identifier="abc123def456"
        ... )
        >>> for plan in result['items']:
        ...     print(f"Plan Hash: {plan['plan_hash']}, Avg Time: {plan['avg_elapsed_time']}")

        >>> # Multi-tenancy analysis
        >>> result = summarize_sql_plan_insights(
        ...     compartment_id="ocid1.compartment...",
        ...     sql_identifier="abc123def456",
        ...     profile="production"
        ... )
    """
    try:
        client = get_opsi_client(profile=profile)

        # Default time range: last 7 days
        if not time_interval_end:
            time_interval_end = datetime.utcnow().isoformat()
        if not time_interval_start:
            start_time = datetime.utcnow() - timedelta(days=7)
            time_interval_start = start_time.isoformat()

        from oci.opsi.models import SummarizeSqlPlanInsightsDetails

        details = SummarizeSqlPlanInsightsDetails()
        details.compartment_id = compartment_id
        details.sql_identifier = sql_identifier
        details.time_interval_start = time_interval_start
        details.time_interval_end = time_interval_end

        if database_id:
            details.database_id = database_id

        response = client.summarize_sql_plan_insights(
            summarize_sql_plan_insights_details=details
        )

        items = []
        if hasattr(response.data, "items"):
            for plan_insight in response.data.items:
                items.append({
                    "plan_hash": getattr(plan_insight, "plan_hash", None),
                    "plan_hash_value": getattr(plan_insight, "plan_hash_value", None),
                    "database_id": getattr(plan_insight, "database_id", None),
                    "database_name": getattr(plan_insight, "database_name", None),
                    "performance": {
                        "avg_elapsed_time_in_sec": getattr(plan_insight, "avg_elapsed_time_in_sec", None),
                        "avg_cpu_time_in_sec": getattr(plan_insight, "avg_cpu_time_in_sec", None),
                        "avg_buffer_gets": getattr(plan_insight, "avg_buffer_gets", None),
                        "avg_disk_reads": getattr(plan_insight, "avg_disk_reads", None),
                        "avg_rows_returned": getattr(plan_insight, "avg_rows_returned", None),
                        "executions": getattr(plan_insight, "executions", None),
                    },
                    "plan_stats": {
                        "io_cell_offload_eligible_bytes": getattr(plan_insight, "io_cell_offload_eligible_bytes", None),
                        "io_interconnect_bytes": getattr(plan_insight, "io_interconnect_bytes", None),
                        "physical_read_bytes": getattr(plan_insight, "physical_read_bytes", None),
                        "physical_write_bytes": getattr(plan_insight, "physical_write_bytes", None),
                    },
                    "insights": {
                        "category": getattr(plan_insight, "category", None),
                        "plan_status": getattr(plan_insight, "plan_status", None),
                        "recommendation": getattr(plan_insight, "recommendation", None),
                    },
                })

        return {
            "compartment_id": compartment_id,
            "sql_identifier": sql_identifier,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "count": len(items),
            "items": items,
            "profile": profile,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "sql_identifier": sql_identifier,
            "profile": profile,
            "success": False,
        }


def summarize_addm_db_findings(
    compartment_id: str,
    profile: Optional[str] = None,
    database_id: Optional[list[str]] = None,
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
    defined_tag_equals: Optional[dict] = None,
    freeform_tag_equals: Optional[dict] = None,
) -> dict[str, Any]:
    """

    **DEPRECATED**: This API returns 404 errors and is not available in OCI.

    **Reason**: 2 APIs return 404 - Not available

    **Status**: Not deployed to OCI service (as of Nov 2025)
    
    Get consolidated ADDM (Automatic Database Diagnostic Monitor) findings.

    ADDM analyzes AWR data and provides recommendations for performance
    improvement. This tool consolidates ADDM findings across multiple
    databases in your fleet.

    Args:
        compartment_id: Compartment OCID
        profile: OCI profile name for multi-tenancy support
        database_id: List of database insight OCIDs to analyze (optional)
        time_interval_start: Start time (ISO 8601 format, defaults to 7 days ago)
        time_interval_end: End time (ISO 8601 format, defaults to now)
        defined_tag_equals: Filter by defined tags
        freeform_tag_equals: Filter by freeform tags

    Returns:
        Dictionary containing ADDM findings and recommendations

    Example:
        >>> # Get ADDM findings for all databases
        >>> result = summarize_addm_db_findings(
        ...     compartment_id="ocid1.compartment..."
        ... )

        >>> # Get findings for specific databases in production
        >>> result = summarize_addm_db_findings(
        ...     compartment_id="ocid1.compartment...",
        ...     database_id=["ocid1.databaseinsight1...", "ocid1.databaseinsight2..."],
        ...     profile="production"
        ... )

        >>> # Filter by time period
        >>> result = summarize_addm_db_findings(
        ...     compartment_id="ocid1.compartment...",
        ...     time_interval_start=(datetime.now() - timedelta(days=1)).isoformat(),
        ...     time_interval_end=datetime.now().isoformat()
        ... )
    """
    try:
        client = get_opsi_client(profile=profile)

        # Default time range: last 7 days
        if not time_interval_end:
            time_interval_end = datetime.utcnow().isoformat()
        if not time_interval_start:
            start_time = datetime.utcnow() - timedelta(days=7)
            time_interval_start = start_time.isoformat()

        kwargs = {
            "compartment_id": compartment_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
        }

        if database_id:
            kwargs["database_id"] = database_id
        if defined_tag_equals:
            kwargs["defined_tag_equals"] = defined_tag_equals
        if freeform_tag_equals:
            kwargs["freeform_tag_equals"] = freeform_tag_equals

        response = client.summarize_addm_db_findings(**kwargs)

        items = []
        if hasattr(response.data, "items"):
            for finding in response.data.items:
                items.append({
                    "finding_id": getattr(finding, "id", None),
                    "database_details": {
                        "database_id": getattr(finding, "database_id", None),
                        "database_name": getattr(finding, "database_name", None),
                        "database_display_name": getattr(finding, "database_display_name", None),
                    },
                    "finding": {
                        "category": getattr(finding, "category", None),
                        "name": getattr(finding, "name", None),
                        "message": getattr(finding, "message", None),
                        "impact": getattr(finding, "impact", None),
                        "impact_avg_active_sessions": getattr(finding, "impact_avg_active_sessions", None),
                        "impact_db_time_in_secs": getattr(finding, "impact_db_time_in_secs", None),
                        "impact_percent": getattr(finding, "impact_percent", None),
                    },
                    "recommendation": {
                        "recommendation_text": getattr(finding, "recommendation_text", None),
                        "recommendation_count": getattr(finding, "recommendation_count", None),
                    },
                    "time_info": {
                        "analysis_db_time_in_secs": getattr(finding, "analysis_db_time_in_secs", None),
                        "time_interval_start": str(getattr(finding, "time_interval_start", None)),
                        "time_interval_end": str(getattr(finding, "time_interval_end", None)),
                    },
                })

        return {
            "compartment_id": compartment_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
            "count": len(items),
            "items": items,
            "profile": profile,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "profile": profile,
            "success": False,
        }


def get_sql_insight_details(
    compartment_id: str,
    sql_identifier: str,
    database_id: str,
    profile: Optional[str] = None,
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get detailed insights for a specific SQL statement on a specific database.

    Provides comprehensive performance analysis including execution history,
    resource consumption patterns, and optimization recommendations.

    Args:
        compartment_id: Compartment OCID
        sql_identifier: SQL identifier to analyze
        database_id: Database insight OCID
        profile: OCI profile name for multi-tenancy support
        time_interval_start: Start time (ISO 8601 format, defaults to 7 days ago)
        time_interval_end: End time (ISO 8601 format, defaults to now)

    Returns:
        Dictionary containing detailed SQL performance insights

    Example:
        >>> result = get_sql_insight_details(
        ...     compartment_id="ocid1.compartment...",
        ...     sql_identifier="abc123def456",
        ...     database_id="ocid1.databaseinsight..."
        ... )
        >>> print(f"Total executions: {result['total_executions']}")
        >>> print(f"Avg elapsed time: {result['avg_elapsed_time']}")
    """
    try:
        # First get the insights summary
        insights_result = summarize_sql_insights(
            compartment_id=compartment_id,
            profile=profile,
            database_id=[database_id],
            time_interval_start=time_interval_start,
            time_interval_end=time_interval_end,
        )

        # Then get the plan insights
        plan_result = summarize_sql_plan_insights(
            compartment_id=compartment_id,
            sql_identifier=sql_identifier,
            profile=profile,
            database_id=[database_id],
            time_interval_start=time_interval_start,
            time_interval_end=time_interval_end,
        )

        # Find the matching SQL in insights
        matching_sql = None
        if insights_result.get("success") and insights_result.get("items"):
            for item in insights_result["items"]:
                if item.get("sql_identifier") == sql_identifier:
                    matching_sql = item
                    break

        return {
            "compartment_id": compartment_id,
            "sql_identifier": sql_identifier,
            "database_id": database_id,
            "sql_insights": matching_sql,
            "plan_insights": plan_result.get("items", []),
            "plan_count": len(plan_result.get("items", [])),
            "profile": profile,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "sql_identifier": sql_identifier,
            "database_id": database_id,
            "profile": profile,
            "success": False,
        }
