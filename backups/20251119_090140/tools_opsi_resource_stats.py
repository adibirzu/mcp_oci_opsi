"""Missing OPSI resource statistics APIs for detailed database performance queries."""

from datetime import datetime, timedelta
from typing import Any, Optional
import oci

from .oci_clients import get_opsi_client, extract_region_from_ocid


def summarize_database_insight_resource_statistics(
    compartment_id: str,
    resource_metric: str = "CPU",
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
    database_id: Optional[list[str]] = None,
    database_type: Optional[list[str]] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get resource statistics summary for database insights.

    Provides aggregated statistics (min, max, avg, usage change) for specified
    resource metrics across databases.

    Args:
        compartment_id: Compartment OCID to query
        resource_metric: Resource type - CPU, STORAGE, IO, MEMORY, MEMORY_PGA, MEMORY_SGA
        time_interval_start: Start time (ISO 8601), defaults to 30 days ago
        time_interval_end: End time (ISO 8601), defaults to now
        database_id: Filter by specific database insight OCIDs
        database_type: Filter by database type (e.g., ["ADW", "ATP", "ADB-D"])
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with resource statistics including usage trends and thresholds
    """
    try:
        # Handle profile switching
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            # Extract region from database insight OCID if provided
            # This ensures we query the correct regional endpoint (fixes cross-region 404 errors)
            region = None
            if database_id and len(database_id) > 0:
                # Database insight OCIDs don't contain region, so we need to query
                # the insight first to get the actual database OCID
                temp_client = get_opsi_client()
                try:
                    db_insight_response = temp_client.get_database_insight(database_id[0])
                    actual_database_id = getattr(db_insight_response.data, "database_id", None)
                    if actual_database_id:
                        # Extract region from the actual database OCID (e.g., ocid1.autonomousdatabase.oc1.phx.xxx)
                        region = extract_region_from_ocid(actual_database_id)
                except Exception:
                    # If we can't get the insight, fall back to profile region
                    pass

            client = get_opsi_client(region=region)

            # Default time range: last 30 days
            if not time_interval_end:
                time_interval_end = datetime.utcnow().isoformat() + "Z"
            if not time_interval_start:
                start_time = datetime.utcnow() - timedelta(days=30)
                time_interval_start = start_time.isoformat() + "Z"

            # Prepare request
            summarize_database_insight_resource_statistics_details = \
                oci.opsi.models.SummarizeDatabaseInsightResourceStatisticsDetails(
                    resource_metric=resource_metric,
                    time_interval_start=time_interval_start,
                    time_interval_end=time_interval_end,
                )

            kwargs = {
                "compartment_id": compartment_id,
                "summarize_database_insight_resource_statistics_details":
                    summarize_database_insight_resource_statistics_details,
            }

            if database_id:
                kwargs["database_id"] = database_id
            if database_type:
                kwargs["database_type"] = database_type

            response = client.summarize_database_insight_resource_statistics(**kwargs)

            items = []
            for item in response.data.items:
                items.append({
                    "database_details": {
                        "id": getattr(item.database_details, "id", None),
                        "database_id": getattr(item.database_details, "database_id", None),
                        "database_name": getattr(item.database_details, "database_name", None),
                        "database_display_name": getattr(item.database_details, "database_display_name", None),
                        "database_type": getattr(item.database_details, "database_type", None),
                    },
                    "current_statistics": {
                        "resource_name": item.current_statistics.resource_name,
                        "usage": item.current_statistics.usage,
                        "capacity": item.current_statistics.capacity,
                        "utilization_percent": item.current_statistics.utilization_percent,
                        "usage_change_percent": item.current_statistics.usage_change_percent,
                    },
                })

            return {
                "compartment_id": compartment_id,
                "resource_metric": resource_metric,
                "time_interval_start": time_interval_start,
                "time_interval_end": time_interval_end,
                "items": items,
                "count": len(items),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
        }


def summarize_database_insight_resource_usage(
    compartment_id: str,
    resource_metric: str = "CPU",
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
    database_id: Optional[list[str]] = None,
    analysis_time_interval: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get historical resource usage data for database insights.

    Provides time-series usage data for capacity planning and trend analysis.

    Args:
        compartment_id: Compartment OCID to query
        resource_metric: Resource type - CPU, STORAGE, IO, MEMORY
        time_interval_start: Start time (ISO 8601), defaults to 7 days ago
        time_interval_end: End time (ISO 8601), defaults to now
        database_id: Filter by specific database insight OCIDs
        analysis_time_interval: Time interval for aggregation (DAILY, HOURLY)
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with time-series usage data and aggregation details
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            # Extract region from database insight OCID if provided
            # This ensures we query the correct regional endpoint (fixes cross-region 404 errors)
            region = None
            if database_id and len(database_id) > 0:
                # Database insight OCIDs don't contain region, so we need to query
                # the insight first to get the actual database OCID
                temp_client = get_opsi_client()
                try:
                    db_insight_response = temp_client.get_database_insight(database_id[0])
                    actual_database_id = getattr(db_insight_response.data, "database_id", None)
                    if actual_database_id:
                        # Extract region from the actual database OCID (e.g., ocid1.autonomousdatabase.oc1.phx.xxx)
                        region = extract_region_from_ocid(actual_database_id)
                except Exception:
                    # If we can't get the insight, fall back to profile region
                    pass

            client = get_opsi_client(region=region)

            # Default time range: last 7 days
            if not time_interval_end:
                time_interval_end = datetime.utcnow().isoformat() + "Z"
            if not time_interval_start:
                start_time = datetime.utcnow() - timedelta(days=7)
                time_interval_start = start_time.isoformat() + "Z"

            kwargs = {
                "compartment_id": compartment_id,
                "resource_metric": resource_metric,
                "time_interval_start": time_interval_start,
                "time_interval_end": time_interval_end,
            }

            if database_id:
                kwargs["database_id"] = database_id
            if analysis_time_interval:
                kwargs["analysis_time_interval"] = analysis_time_interval

            response = client.summarize_database_insight_resource_usage(**kwargs)

            usage_data = []
            for usage in response.data.items:
                usage_data.append({
                    "end_timestamp": str(usage.end_timestamp),
                    "usage": usage.usage,
                    "capacity": usage.capacity,
                    "utilization_percent": usage.utilization_percent,
                })

            return {
                "compartment_id": compartment_id,
                "resource_metric": resource_metric,
                "time_interval_start": time_interval_start,
                "time_interval_end": time_interval_end,
                "usage_data": usage_data,
                "data_points": len(usage_data),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
        }


def summarize_database_insight_resource_utilization_insight(
    compartment_id: str,
    resource_metric: str = "CPU",
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
    database_id: Optional[list[str]] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get resource utilization insights with trend analysis and forecasts.

    Provides advanced analytics including pattern detection, anomalies,
    and projected utilization trends.

    Args:
        compartment_id: Compartment OCID to query
        resource_metric: Resource type - CPU, STORAGE, IO, MEMORY
        time_interval_start: Start time (ISO 8601), defaults to 30 days ago
        time_interval_end: End time (ISO 8601), defaults to now
        database_id: Filter by specific database insight OCIDs
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with utilization insights, trends, and recommendations
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            # Extract region from database insight OCID if provided
            # This ensures we query the correct regional endpoint (fixes cross-region 404 errors)
            region = None
            if database_id and len(database_id) > 0:
                # Database insight OCIDs don't contain region, so we need to query
                # the insight first to get the actual database OCID
                temp_client = get_opsi_client()
                try:
                    db_insight_response = temp_client.get_database_insight(database_id[0])
                    actual_database_id = getattr(db_insight_response.data, "database_id", None)
                    if actual_database_id:
                        # Extract region from the actual database OCID (e.g., ocid1.autonomousdatabase.oc1.phx.xxx)
                        region = extract_region_from_ocid(actual_database_id)
                except Exception:
                    # If we can't get the insight, fall back to profile region
                    pass

            client = get_opsi_client(region=region)

            # Default time range: last 30 days
            if not time_interval_end:
                time_interval_end = datetime.utcnow().isoformat() + "Z"
            if not time_interval_start:
                start_time = datetime.utcnow() - timedelta(days=30)
                time_interval_start = start_time.isoformat() + "Z"

            kwargs = {
                "compartment_id": compartment_id,
                "resource_metric": resource_metric,
                "time_interval_start": time_interval_start,
                "time_interval_end": time_interval_end,
            }

            if database_id:
                kwargs["database_id"] = database_id

            response = client.summarize_database_insight_resource_utilization_insight(**kwargs)

            insights = []
            for item in response.data.items:
                insights.append({
                    "database_details": {
                        "id": getattr(item.database_details, "id", None),
                        "database_name": getattr(item.database_details, "database_name", None),
                        "database_type": getattr(item.database_details, "database_type", None),
                    },
                    "utilization_insight": {
                        "high_utilization_threshold": item.current_utilization.high_utilization_threshold,
                        "low_utilization_threshold": item.current_utilization.low_utilization_threshold,
                    },
                })

            return {
                "compartment_id": compartment_id,
                "resource_metric": resource_metric,
                "time_interval_start": time_interval_start,
                "time_interval_end": time_interval_end,
                "insights": insights,
                "count": len(insights),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
        }


def summarize_database_insight_tablespace_usage_trend(
    compartment_id: str,
    time_interval_start: Optional[str] = None,
    time_interval_end: Optional[str] = None,
    database_id: Optional[list[str]] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get tablespace usage trends over time.

    Tracks tablespace growth patterns and capacity planning data.

    Args:
        compartment_id: Compartment OCID to query
        time_interval_start: Start time (ISO 8601), defaults to 30 days ago
        time_interval_end: End time (ISO 8601), defaults to now
        database_id: Filter by specific database insight OCIDs
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with tablespace usage trends and growth patterns
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            # Extract region from database insight OCID if provided
            # This ensures we query the correct regional endpoint (fixes cross-region 404 errors)
            region = None
            if database_id and len(database_id) > 0:
                # Database insight OCIDs don't contain region, so we need to query
                # the insight first to get the actual database OCID
                temp_client = get_opsi_client()
                try:
                    db_insight_response = temp_client.get_database_insight(database_id[0])
                    actual_database_id = getattr(db_insight_response.data, "database_id", None)
                    if actual_database_id:
                        # Extract region from the actual database OCID (e.g., ocid1.autonomousdatabase.oc1.phx.xxx)
                        region = extract_region_from_ocid(actual_database_id)
                except Exception:
                    # If we can't get the insight, fall back to profile region
                    pass

            client = get_opsi_client(region=region)

            # Default time range: last 30 days
            if not time_interval_end:
                time_interval_end = datetime.utcnow().isoformat() + "Z"
            if not time_interval_start:
                start_time = datetime.utcnow() - timedelta(days=30)
                time_interval_start = start_time.isoformat() + "Z"

            kwargs = {
                "compartment_id": compartment_id,
                "time_interval_start": time_interval_start,
                "time_interval_end": time_interval_end,
            }

            if database_id:
                kwargs["database_id"] = database_id

            response = client.summarize_database_insight_tablespace_usage_trend(**kwargs)

            tablespaces = []
            for item in response.data.items:
                tablespaces.append({
                    "database_details": {
                        "id": getattr(item, "id", None),
                        "database_id": getattr(item, "database_id", None),
                        "database_name": getattr(item, "database_name", None),
                    },
                    "tablespace_name": getattr(item, "tablespace_name", None),
                    "tablespace_type": getattr(item, "tablespace_type", None),
                    "usage_data": [
                        {
                            "end_timestamp": str(u.end_timestamp),
                            "usage": u.usage,
                            "capacity": u.capacity,
                            "utilization_percent": u.utilization_percent,
                        }
                        for u in getattr(item, "usage_data", [])
                    ],
                })

            return {
                "compartment_id": compartment_id,
                "time_interval_start": time_interval_start,
                "time_interval_end": time_interval_end,
                "tablespaces": tablespaces,
                "count": len(tablespaces),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }
