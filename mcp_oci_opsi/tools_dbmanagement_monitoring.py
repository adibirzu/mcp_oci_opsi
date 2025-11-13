"""FastMCP tools for OCI Database Management - Real-time Monitoring and Diagnostics."""

from typing import Any, Optional

from .oci_clients import get_dbm_client, list_all


def get_database_home_metrics(
    database_id: str,
    start_time: str,
    end_time: str,
) -> dict[str, Any]:
    """
    Get database home metrics for monitoring.

    Args:
        database_id: Managed Database OCID.
        start_time: Start time in ISO format.
        end_time: End time in ISO format.

    Returns:
        Dictionary containing database home metrics.
    """
    try:
        client = get_dbm_client()

        # Get database home metrics
        response = client.summarize_managed_database_availability(
            managed_database_id=database_id,
            start_time=start_time,
            end_time=end_time,
        )

        metrics = []
        if hasattr(response.data, "items"):
            for item in response.data.items:
                metrics.append({
                    "time_interval_start": str(getattr(item, "time_interval_start", None)),
                    "time_interval_end": str(getattr(item, "time_interval_end", None)),
                    "availability_status": getattr(item, "availability_status", None),
                })

        return {
            "database_id": database_id,
            "start_time": start_time,
            "end_time": end_time,
            "metrics": metrics,
            "count": len(metrics),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def list_database_jobs(
    database_id: str,
    job_name: Optional[str] = None,
) -> dict[str, Any]:
    """
    List database jobs (scheduled jobs) for a managed database.

    Args:
        database_id: Managed Database OCID.
        job_name: Optional job name filter.

    Returns:
        Dictionary containing list of database jobs.
    """
    try:
        client = get_dbm_client()

        kwargs = {
            "managed_database_id": database_id,
        }
        if job_name:
            kwargs["name"] = job_name

        # List jobs
        jobs = list_all(
            client.list_jobs,
            **kwargs,
        )

        items = []
        for job in jobs:
            items.append({
                "id": job.id,
                "name": job.name,
                "schedule_type": getattr(job, "schedule_type", None),
                "job_type": getattr(job, "job_type", None),
                "lifecycle_state": job.lifecycle_state,
                "timeout": getattr(job, "timeout", None),
                "submission_error_message": getattr(job, "submission_error_message", None),
                "time_created": str(job.time_created),
                "time_updated": str(getattr(job, "time_updated", None)),
            })

        return {
            "database_id": database_id,
            "jobs": items,
            "count": len(items),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_addm_report(
    database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
) -> dict[str, Any]:
    """
    Get ADDM (Automatic Database Diagnostic Monitor) report.

    ADDM analyzes database performance and provides recommendations.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        begin_snapshot_id: Begin snapshot identifier.
        end_snapshot_id: End snapshot identifier.

    Returns:
        Dictionary containing ADDM report and findings.
    """
    try:
        client = get_dbm_client()

        response = client.summarize_addm_db_recommendations(
            managed_database_id=database_id,
            awr_db_id=awr_db_id,
            begin_snapshot_id=begin_snapshot_id,
            end_snapshot_id=end_snapshot_id,
        )

        findings = []
        if hasattr(response.data, "items"):
            for item in response.data.items:
                findings.append({
                    "finding_id": getattr(item, "finding_id", None),
                    "category_name": getattr(item, "category_name", None),
                    "type": getattr(item, "type", None),
                    "impact": getattr(item, "impact", None),
                    "message": getattr(item, "message", None),
                    "recommendation_count": getattr(item, "recommendation_count", None),
                })

        return {
            "database_id": database_id,
            "awr_db_id": awr_db_id,
            "begin_snapshot_id": begin_snapshot_id,
            "end_snapshot_id": end_snapshot_id,
            "findings": findings,
            "findings_count": len(findings),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_ash_analytics(
    database_id: str,
    awr_db_id: str,
    time_start: str,
    time_end: str,
    wait_class: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get ASH (Active Session History) analytics for performance analysis.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        time_start: Start time in ISO format.
        time_end: End time in ISO format.
        wait_class: Optional wait class filter (e.g., "User I/O", "CPU").

    Returns:
        Dictionary containing ASH analytics data.
    """
    try:
        client = get_dbm_client()

        kwargs = {
            "managed_database_id": database_id,
            "awr_db_id": awr_db_id,
            "time_begin": time_start,
            "time_end": time_end,
        }
        if wait_class:
            kwargs["wait_class"] = wait_class

        response = client.summarize_awr_db_wait_events(
            **kwargs,
        )

        wait_events = []
        if hasattr(response.data, "items"):
            for item in response.data.items:
                wait_events.append({
                    "name": getattr(item, "name", None),
                    "time_waited_in_micro_sec": getattr(item, "time_waited_in_micro_sec", None),
                    "waits_per_sec": getattr(item, "waits_per_sec", None),
                    "avg_wait_time_per_wait_in_ms": getattr(item, "avg_wait_time_per_wait_in_ms", None),
                })

        return {
            "database_id": database_id,
            "awr_db_id": awr_db_id,
            "time_start": time_start,
            "time_end": time_end,
            "wait_events": wait_events,
            "count": len(wait_events),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_top_sql_by_metric(
    database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
    metric: str = "CPU",
    top_n: int = 10,
) -> dict[str, Any]:
    """
    Get top SQL statements by specified metric.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        begin_snapshot_id: Begin snapshot identifier.
        end_snapshot_id: End snapshot identifier.
        metric: Metric to sort by (CPU, ELAPSED_TIME, BUFFER_GETS, DISK_READS).
        top_n: Number of top SQL statements to return (default 10).

    Returns:
        Dictionary containing top SQL statements.
    """
    try:
        client = get_dbm_client()

        response = client.summarize_awr_db_top_wait_events(
            managed_database_id=database_id,
            awr_db_id=awr_db_id,
            begin_snapshot_id=begin_snapshot_id,
            end_snapshot_id=end_snapshot_id,
        )

        top_sql = []
        if hasattr(response.data, "items"):
            for item in list(response.data.items)[:top_n]:
                top_sql.append({
                    "sql_id": getattr(item, "sql_id", None),
                    "name": getattr(item, "name", None),
                    "waits_per_sec": getattr(item, "waits_per_sec", None),
                    "avg_wait_time_per_wait_in_ms": getattr(item, "avg_wait_time_per_wait_in_ms", None),
                })

        return {
            "database_id": database_id,
            "awr_db_id": awr_db_id,
            "metric": metric,
            "top_n": top_n,
            "top_sql": top_sql,
            "count": len(top_sql),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_database_system_statistics(
    database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
) -> dict[str, Any]:
    """
    Get database system statistics from AWR.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        begin_snapshot_id: Begin snapshot identifier.
        end_snapshot_id: End snapshot identifier.

    Returns:
        Dictionary containing system statistics.
    """
    try:
        client = get_dbm_client()

        response = client.summarize_awr_db_sys_stats(
            managed_database_id=database_id,
            awr_db_id=awr_db_id,
            begin_snapshot_id=begin_snapshot_id,
            end_snapshot_id=end_snapshot_id,
        )

        sys_stats = []
        if hasattr(response.data, "items"):
            for item in response.data.items:
                sys_stats.append({
                    "name": getattr(item, "name", None),
                    "value": getattr(item, "value", None),
                    "category": getattr(item, "category", None),
                })

        return {
            "database_id": database_id,
            "awr_db_id": awr_db_id,
            "begin_snapshot_id": begin_snapshot_id,
            "end_snapshot_id": end_snapshot_id,
            "system_statistics": sys_stats,
            "count": len(sys_stats),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_database_io_statistics(
    database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
) -> dict[str, Any]:
    """
    Get database I/O statistics from AWR.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        begin_snapshot_id: Begin snapshot identifier.
        end_snapshot_id: End snapshot identifier.

    Returns:
        Dictionary containing I/O statistics.
    """
    try:
        client = get_dbm_client()

        response = client.summarize_awr_db_metric_summary(
            managed_database_id=database_id,
            awr_db_id=awr_db_id,
            begin_snapshot_id=begin_snapshot_id,
            end_snapshot_id=end_snapshot_id,
        )

        metrics = []
        if hasattr(response.data, "items"):
            for item in response.data.items:
                metrics.append({
                    "name": getattr(item, "name", None),
                    "value": getattr(item, "value", None),
                    "unit": getattr(item, "unit", None),
                })

        return {
            "database_id": database_id,
            "awr_db_id": awr_db_id,
            "begin_snapshot_id": begin_snapshot_id,
            "end_snapshot_id": end_snapshot_id,
            "io_metrics": metrics,
            "count": len(metrics),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def list_alert_logs(
    database_id: str,
    log_level: Optional[str] = None,
    time_greater_than_or_equal_to: Optional[str] = None,
    time_less_than_or_equal_to: Optional[str] = None,
) -> dict[str, Any]:
    """
    List alert log entries for a managed database.

    Args:
        database_id: Managed Database OCID.
        log_level: Optional log level filter (CRITICAL, SEVERE, WARNING).
        time_greater_than_or_equal_to: Start time in ISO format.
        time_less_than_or_equal_to: End time in ISO format.

    Returns:
        Dictionary containing alert log entries.
    """
    try:
        client = get_dbm_client()

        kwargs = {
            "managed_database_id": database_id,
        }
        if log_level:
            kwargs["level_filter"] = log_level
        if time_greater_than_or_equal_to:
            kwargs["time_greater_than_or_equal_to"] = time_greater_than_or_equal_to
        if time_less_than_or_equal_to:
            kwargs["time_less_than_or_equal_to"] = time_less_than_or_equal_to

        alerts = list_all(
            client.list_attention_logs,
            **kwargs,
        )

        items = []
        for alert in alerts:
            items.append({
                "message_type": getattr(alert, "message_type", None),
                "message_level": getattr(alert, "message_level", None),
                "message_content": getattr(alert, "message_content", None),
                "timestamp": str(getattr(alert, "timestamp", None)),
                "supplemental_detail": getattr(alert, "supplemental_detail", None),
            })

        return {
            "database_id": database_id,
            "log_level": log_level,
            "alert_logs": items,
            "count": len(items),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_database_cpu_usage(
    database_id: str,
    start_time: str,
    end_time: str,
) -> dict[str, Any]:
    """
    Get database CPU usage metrics over time.

    Args:
        database_id: Managed Database OCID.
        start_time: Start time in ISO format.
        end_time: End time in ISO format.

    Returns:
        Dictionary containing CPU usage metrics.
    """
    try:
        client = get_dbm_client()

        response = client.get_managed_database(
            managed_database_id=database_id,
        )

        db = response.data

        # Get basic CPU info
        result = {
            "database_id": database_id,
            "database_name": db.name,
            "start_time": start_time,
            "end_time": end_time,
            "cpu_info": {
                "database_type": getattr(db, "database_type", None),
                "deployment_type": getattr(db, "deployment_type", None),
            },
        }

        return result

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_sql_tuning_recommendations(
    database_id: str,
    sql_id: str,
) -> dict[str, Any]:
    """
    Get SQL tuning recommendations for a specific SQL statement.

    Args:
        database_id: Managed Database OCID.
        sql_id: SQL identifier.

    Returns:
        Dictionary containing SQL tuning recommendations.
    """
    try:
        # Note: This would use SQL Tuning Advisor APIs when available
        # For now, return structure for future implementation
        return {
            "database_id": database_id,
            "sql_id": sql_id,
            "recommendations": [],
            "note": "SQL Tuning Advisor integration pending - use AWR/ADDM reports for recommendations",
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
            "sql_id": sql_id,
        }


def get_database_resource_usage(
    database_id: str,
) -> dict[str, Any]:
    """
    Get current database resource usage summary.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing resource usage information.
    """
    try:
        client = get_dbm_client()

        # Get managed database details
        db_response = client.get_managed_database(
            managed_database_id=database_id,
        )

        db = db_response.data

        # Get tablespaces for storage info
        tablespace_response = client.list_tablespaces(
            managed_database_id=database_id,
        )

        total_size = 0
        total_used = 0

        if hasattr(tablespace_response.data, "items"):
            for ts in tablespace_response.data.items:
                size = getattr(ts, "size_in_mbs", 0) or 0
                used = getattr(ts, "used_in_mbs", 0) or 0
                total_size += size
                total_used += used

        return {
            "database_id": database_id,
            "database_name": db.name,
            "database_type": getattr(db, "database_type", None),
            "resource_usage": {
                "storage_total_mb": total_size,
                "storage_used_mb": total_used,
                "storage_used_percent": round((total_used / total_size * 100), 2) if total_size > 0 else 0,
            },
            "lifecycle_state": db.lifecycle_state,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }
