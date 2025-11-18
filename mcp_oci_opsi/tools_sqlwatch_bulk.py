"""FastMCP tools for bulk SQL Watch enablement and management."""

from typing import Any, Optional
import time

from .oci_clients_enhanced import get_dbm_client, list_all


def enable_sqlwatch_bulk(
    compartment_id: str,
    profile: Optional[str] = None,
    database_type_filter: Optional[str] = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Enable SQL Watch on multiple managed databases in bulk.

    SQL Watch is required for detailed SQL-level monitoring in Operations Insights.
    This tool enables it across multiple databases efficiently.

    Args:
        compartment_id: Compartment OCID
        profile: OCI profile name for multi-tenancy support
        database_type_filter: Filter by database type (e.g., "EXTERNAL_SIDB", "CLOUD_SIDB")
        dry_run: If True, only shows what would be done without making changes

    Returns:
        Dictionary with enablement results for each database

    Example:
        >>> # Dry run to see what would happen
        >>> result = enable_sqlwatch_bulk(
        ...     compartment_id="ocid1.compartment.oc1...",
        ...     dry_run=True
        ... )
        >>> print(f"Would enable on {result['summary']['would_enable']} databases")

        >>> # Actually enable
        >>> result = enable_sqlwatch_bulk(
        ...     compartment_id="ocid1.compartment.oc1...",
        ...     dry_run=False
        ... )
    """
    try:
        dbm_client = get_dbm_client(profile=profile)

        # List all managed databases
        managed_dbs = list_all(
            dbm_client.list_managed_databases,
            compartment_id=compartment_id,
            lifecycle_state="ACTIVE"
        )

        if database_type_filter:
            managed_dbs = [db for db in managed_dbs if db.database_type == database_type_filter]

        results = []
        enabled_count = 0
        already_enabled_count = 0
        failed_count = 0
        skipped_count = 0

        for db in managed_dbs:
            try:
                # Check current SQL Watch status
                status_response = dbm_client.get_sql_watch_status(
                    managed_database_id=db.id
                )

                current_status = status_response.data.status

                if current_status == "ENABLED":
                    results.append({
                        "database_id": db.id,
                        "database_name": db.name,
                        "database_type": getattr(db, "database_type", "Unknown"),
                        "action": "SKIPPED",
                        "reason": "Already enabled",
                        "status": "✓ Already Enabled"
                    })
                    already_enabled_count += 1
                    continue

                # Check if database is eligible
                management_option = getattr(db, "management_option", None)
                if management_option == "BASIC":
                    results.append({
                        "database_id": db.id,
                        "database_name": db.name,
                        "database_type": getattr(db, "database_type", "Unknown"),
                        "action": "SKIPPED",
                        "reason": "BASIC management - requires ADVANCED",
                        "status": "⚠ Not Eligible"
                    })
                    skipped_count += 1
                    continue

                if dry_run:
                    results.append({
                        "database_id": db.id,
                        "database_name": db.name,
                        "database_type": getattr(db, "database_type", "Unknown"),
                        "action": "WOULD_ENABLE",
                        "current_status": current_status,
                        "status": "📋 Dry Run"
                    })
                    enabled_count += 1
                else:
                    # Enable SQL Watch
                    enable_response = dbm_client.enable_sql_watch(
                        managed_database_id=db.id
                    )

                    work_request_id = enable_response.headers.get("opc-work-request-id")

                    results.append({
                        "database_id": db.id,
                        "database_name": db.name,
                        "database_type": getattr(db, "database_type", "Unknown"),
                        "action": "ENABLED",
                        "work_request_id": work_request_id,
                        "status": "✓ Enabled (pending)"
                    })
                    enabled_count += 1

                    # Small delay to avoid rate limiting
                    time.sleep(0.5)

            except Exception as e:
                results.append({
                    "database_id": db.id,
                    "database_name": db.name,
                    "database_type": getattr(db, "database_type", "Unknown"),
                    "action": "FAILED",
                    "error": str(e),
                    "status": "✗ Error"
                })
                failed_count += 1

        mode = "DRY_RUN" if dry_run else "EXECUTION"

        return {
            "compartment_id": compartment_id,
            "profile": profile,
            "mode": mode,
            "summary": {
                "total_databases": len(managed_dbs),
                "enabled" if not dry_run else "would_enable": enabled_count,
                "already_enabled": already_enabled_count,
                "skipped": skipped_count,
                "failed": failed_count
            },
            "databases": results,
            "recommendations": generate_bulk_recommendations(results, dry_run),
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


def generate_bulk_recommendations(results: list, dry_run: bool) -> list[str]:
    """Generate recommendations based on bulk enablement results."""
    recommendations = []

    if dry_run:
        would_enable = len([r for r in results if r["action"] == "WOULD_ENABLE"])
        if would_enable > 0:
            recommendations.append(
                f"✓ Ready to enable SQL Watch on {would_enable} database(s)\n"
                "  Run with dry_run=False to proceed"
            )
        else:
            recommendations.append("ℹ No databases need SQL Watch enablement")
    else:
        enabled = len([r for r in results if r["action"] == "ENABLED"])
        if enabled > 0:
            recommendations.append(
                f"✓ SQL Watch enablement initiated on {enabled} database(s)\n"
                "  Use check_sqlwatch_work_requests() to monitor progress"
            )

    failed = [r for r in results if r["action"] == "FAILED"]
    if failed:
        recommendations.append(
            f"\n⚠ {len(failed)} database(s) failed:\n"
            "  Review the error messages and check:\n"
            "  1. Database Management service is enabled\n"
            "  2. Required IAM permissions are in place\n"
            "  3. Database credentials are configured\n"
            "  4. Network connectivity is available"
        )

    skipped = [r for r in results if r["action"] == "SKIPPED" and "BASIC" in r.get("reason", "")]
    if skipped:
        recommendations.append(
            f"\nℹ {len(skipped)} database(s) skipped (BASIC management):\n"
            "  These databases require ADVANCED management features\n"
            "  to enable SQL Watch"
        )

    return recommendations


def check_sqlwatch_work_requests(
    compartment_id: str,
    profile: Optional[str] = None,
    hours_back: int = 1,
) -> dict[str, Any]:
    """
    Check the status of SQL Watch enablement work requests.

    Monitors the progress of SQL Watch enable/disable operations initiated
    through enable_sqlwatch_bulk or individual enable_sqlwatch calls.

    Args:
        compartment_id: Compartment OCID
        profile: OCI profile name for multi-tenancy support
        hours_back: How many hours back to check work requests (default: 1)

    Returns:
        Dictionary with work request status information

    Example:
        >>> result = check_sqlwatch_work_requests(
        ...     compartment_id="ocid1.compartment.oc1...",
        ...     hours_back=2
        ... )
        >>> for wr in result['work_requests']:
        ...     print(f"{wr['operation']}: {wr['status']}")
    """
    try:
        dbm_client = get_dbm_client(profile=profile)

        from datetime import datetime, timedelta

        # Calculate time range
        time_end = datetime.utcnow()
        time_start = time_end - timedelta(hours=hours_back)

        # List work requests
        work_requests = list_all(
            dbm_client.list_work_requests,
            compartment_id=compartment_id
        )

        # Filter for SQL Watch related requests in time range
        sqlwatch_requests = []
        for wr in work_requests:
            # Check if it's SQL Watch related
            operation_type = getattr(wr, "operation_type", "")
            if "SQL_WATCH" in operation_type or "ENABLE_SQL_WATCH" in operation_type or "DISABLE_SQL_WATCH" in operation_type:
                # Check time range
                time_accepted = getattr(wr, "time_accepted", None)
                if time_accepted and time_accepted >= time_start:
                    sqlwatch_requests.append({
                        "work_request_id": wr.id,
                        "operation_type": operation_type,
                        "status": wr.status,
                        "percent_complete": getattr(wr, "percent_complete", 0),
                        "time_accepted": str(time_accepted),
                        "time_started": str(getattr(wr, "time_started", None)),
                        "time_finished": str(getattr(wr, "time_finished", None)),
                        "resources": [{"entity_type": r.entity_type, "identifier": r.identifier}
                                     for r in getattr(wr, "resources", [])],
                    })

        # Summarize status
        status_counts = {}
        for req in sqlwatch_requests:
            status = req["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "compartment_id": compartment_id,
            "profile": profile,
            "time_range": {
                "start": str(time_start),
                "end": str(time_end),
                "hours_back": hours_back
            },
            "summary": {
                "total_requests": len(sqlwatch_requests),
                "status_counts": status_counts
            },
            "work_requests": sqlwatch_requests,
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


def disable_sqlwatch_bulk(
    compartment_id: str,
    profile: Optional[str] = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Disable SQL Watch on multiple managed databases in bulk.

    Use with caution - this will stop detailed SQL-level monitoring.

    Args:
        compartment_id: Compartment OCID
        profile: OCI profile name for multi-tenancy support
        dry_run: If True, only shows what would be done without making changes

    Returns:
        Dictionary with disable results for each database

    Example:
        >>> # Dry run to see what would happen
        >>> result = disable_sqlwatch_bulk(
        ...     compartment_id="ocid1.compartment.oc1...",
        ...     dry_run=True
        ... )
    """
    try:
        dbm_client = get_dbm_client(profile=profile)

        # List all managed databases
        managed_dbs = list_all(
            dbm_client.list_managed_databases,
            compartment_id=compartment_id,
            lifecycle_state="ACTIVE"
        )

        results = []
        disabled_count = 0
        already_disabled_count = 0
        failed_count = 0

        for db in managed_dbs:
            try:
                # Check current SQL Watch status
                status_response = dbm_client.get_sql_watch_status(
                    managed_database_id=db.id
                )

                current_status = status_response.data.status

                if current_status == "DISABLED":
                    results.append({
                        "database_id": db.id,
                        "database_name": db.name,
                        "action": "SKIPPED",
                        "reason": "Already disabled",
                        "status": "✓ Already Disabled"
                    })
                    already_disabled_count += 1
                    continue

                if dry_run:
                    results.append({
                        "database_id": db.id,
                        "database_name": db.name,
                        "action": "WOULD_DISABLE",
                        "current_status": current_status,
                        "status": "📋 Dry Run"
                    })
                    disabled_count += 1
                else:
                    # Disable SQL Watch
                    disable_response = dbm_client.disable_sql_watch(
                        managed_database_id=db.id
                    )

                    work_request_id = disable_response.headers.get("opc-work-request-id")

                    results.append({
                        "database_id": db.id,
                        "database_name": db.name,
                        "action": "DISABLED",
                        "work_request_id": work_request_id,
                        "status": "✓ Disabled (pending)"
                    })
                    disabled_count += 1

                    time.sleep(0.5)

            except Exception as e:
                results.append({
                    "database_id": db.id,
                    "database_name": db.name,
                    "action": "FAILED",
                    "error": str(e),
                    "status": "✗ Error"
                })
                failed_count += 1

        mode = "DRY_RUN" if dry_run else "EXECUTION"

        return {
            "compartment_id": compartment_id,
            "profile": profile,
            "mode": mode,
            "summary": {
                "total_databases": len(managed_dbs),
                "disabled" if not dry_run else "would_disable": disabled_count,
                "already_disabled": already_disabled_count,
                "failed": failed_count
            },
            "databases": results,
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
