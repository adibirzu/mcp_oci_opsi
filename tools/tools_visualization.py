"""Enhanced FastMCP tools for visualization and capacity planning with ASCII charts."""

from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List

from .oci_clients import get_opsi_client
from ..config import get_oci_config
from ..scripts.visualization import (
    create_ascii_line_chart,
    create_capacity_summary,
    format_exadata_rack_info,
    format_oci_console_url,
    add_visualization_to_response,
)


def get_capacity_trend_with_visualization(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    database_id: Optional[str] = None,
    database_name: Optional[str] = "Database",
) -> Dict[str, Any]:
    """
    Get capacity planning trends WITH ASCII visualization chart.

    This tool returns capacity trend data along with an ASCII line chart
    visualization and an OCI Console URL for graphical view.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, STORAGE, MEMORY, IO).
        time_interval_start: Start time in ISO format (e.g., "2024-01-01T00:00:00Z").
        time_interval_end: End time in ISO format (e.g., "2024-01-31T23:59:59Z").
        database_id: Optional database OCID filter.
        database_name: Optional database name for chart title.

    Returns:
        Dictionary containing:
        - trend_data: Historical capacity trend data points
        - ascii_chart: ASCII line chart visualization
        - oci_console_url: Direct link to OCI Console for graphical view
        - summary: Key insights and statistics
    """
    try:
        client = get_opsi_client()
        config = get_oci_config()

        # Convert time strings to datetime
        time_start = datetime.fromisoformat(time_interval_start.replace("Z", "+00:00"))
        time_end = datetime.fromisoformat(time_interval_end.replace("Z", "+00:00"))

        kwargs = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
        }

        if database_id:
            kwargs["database_id"] = [database_id]

        response = client.summarize_database_insight_resource_capacity_trend(**kwargs)

        # Extract trend data
        trend_items = []
        if hasattr(response.data, "items"):
            for item in response.data.items:
                trend_items.append({
                    "timestamp": str(getattr(item, "end_timestamp", None)),
                    "capacity": float(getattr(item, "capacity", 0)),
                    "usage": float(getattr(item, "usage", 0)),
                    "utilization_percent": float(getattr(item, "utilization_percent", 0)),
                })

        # Create ASCII chart
        chart_title = f"{resource_metric} Capacity Trend: {database_name}"
        ascii_chart = create_ascii_line_chart(
            data_points=trend_items,
            value_key="utilization_percent",
            timestamp_key="timestamp",
            width=80,
            height=20,
            title=chart_title,
            show_forecast=False,
        )

        # Calculate statistics
        if trend_items:
            avg_util = sum(item["utilization_percent"] for item in trend_items) / len(trend_items)
            max_util = max(item["utilization_percent"] for item in trend_items)
            min_util = min(item["utilization_percent"] for item in trend_items)
            current_util = trend_items[-1]["utilization_percent"] if trend_items else 0

            # Calculate trend (comparing first half to second half)
            mid_point = len(trend_items) // 2
            first_half_avg = sum(item["utilization_percent"] for item in trend_items[:mid_point]) / mid_point if mid_point > 0 else 0
            second_half_avg = sum(item["utilization_percent"] for item in trend_items[mid_point:]) / (len(trend_items) - mid_point) if len(trend_items) > mid_point else 0
            trend_direction = "Increasing" if second_half_avg > first_half_avg else "Decreasing" if second_half_avg < first_half_avg else "Stable"

            summary = {
                "current_utilization": f"{current_util:.2f}%",
                "average_utilization": f"{avg_util:.2f}%",
                "peak_utilization": f"{max_util:.2f}%",
                "minimum_utilization": f"{min_util:.2f}%",
                "trend_direction": trend_direction,
                "data_points": len(trend_items),
            }
        else:
            summary = {"message": "No trend data available"}

        # Generate OCI Console URL
        region = config.get("region", "us-ashburn-1")
        console_url = None
        if database_id:
            console_url = format_oci_console_url(
                region=region,
                resource_type="database_insight",
                resource_id=database_id,
                page="capacity",
            )

        return {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval": f"{time_interval_start} to {time_interval_end}",
            "ascii_chart": ascii_chart,
            "trend_data": trend_items,
            "summary": summary,
            "oci_console_url": console_url,
            "note": "📊 For graphical charts and interactive visualization, open the OCI Console URL above",
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
        }


def get_resource_forecast_with_visualization(
    compartment_id: str,
    resource_metric: str,
    time_interval_start: str,
    time_interval_end: str,
    forecast_days: int = 30,
    database_id: Optional[str] = None,
    database_name: Optional[str] = "Database",
) -> Dict[str, Any]:
    """
    Get ML-based resource forecast WITH ASCII visualization chart.

    This tool provides capacity forecasting with both historical and predicted
    values displayed in an ASCII chart, similar to the OCI Console forecast view.

    Args:
        compartment_id: Compartment OCID.
        resource_metric: Resource metric (CPU, STORAGE, MEMORY, IO).
        time_interval_start: Start time in ISO format.
        time_interval_end: End time in ISO format.
        forecast_days: Number of days to forecast (default 30).
        database_id: Optional database OCID filter.
        database_name: Optional database name for chart title.

    Returns:
        Dictionary containing:
        - historical_data: Historical trend data
        - forecast_data: ML-predicted future values with confidence intervals
        - ascii_chart: Combined historical + forecast visualization
        - oci_console_url: Direct link to OCI Console
        - recommendations: Capacity planning recommendations
    """
    try:
        client = get_opsi_client()
        config = get_oci_config()

        # Get historical trend first
        time_start = datetime.fromisoformat(time_interval_start.replace("Z", "+00:00"))
        time_end = datetime.fromisoformat(time_interval_end.replace("Z", "+00:00"))

        # Historical data
        trend_kwargs = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
        }
        if database_id:
            trend_kwargs["database_id"] = [database_id]

        trend_response = client.summarize_database_insight_resource_capacity_trend(**trend_kwargs)

        historical_data = []
        if hasattr(trend_response.data, "items"):
            for item in trend_response.data.items:
                historical_data.append({
                    "timestamp": str(getattr(item, "end_timestamp", None)),
                    "usage": float(getattr(item, "usage", 0)),
                    "capacity": float(getattr(item, "capacity", 0)),
                    "utilization_percent": float(getattr(item, "utilization_percent", 0)),
                })

        # Forecast data
        forecast_kwargs = {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
            "forecast_days": forecast_days,
        }
        if database_id:
            forecast_kwargs["database_id"] = [database_id]

        forecast_response = client.summarize_database_insight_resource_forecast_trend(**forecast_kwargs)

        forecast_data = []
        if hasattr(forecast_response.data, "items"):
            for item in forecast_response.data.items:
                forecast_data.append({
                    "timestamp": str(getattr(item, "end_timestamp", None)),
                    "usage": float(getattr(item, "usage", 0)),
                    "high_value": float(getattr(item, "high_value", 0)),
                    "low_value": float(getattr(item, "low_value", 0)),
                })

        # Create combined ASCII chart
        chart_title = f"{resource_metric} Forecast (Historical + {forecast_days}d Prediction): {database_name}"
        ascii_chart = create_ascii_line_chart(
            data_points=historical_data,
            value_key="utilization_percent",
            timestamp_key="timestamp",
            width=80,
            height=20,
            title=chart_title,
            show_forecast=True,
            forecast_data=[
                {
                    "timestamp": fp["timestamp"],
                    "utilization_percent": fp["usage"]  # Forecast usage as percentage
                }
                for fp in forecast_data
            ],
        )

        # Calculate recommendations
        recommendations = []
        if historical_data and forecast_data:
            current_util = historical_data[-1]["utilization_percent"]
            last_forecast = forecast_data[-1] if forecast_data else None

            if last_forecast:
                forecast_util = last_forecast["usage"]
                high_forecast = last_forecast["high_value"]

                if high_forecast > 90:
                    recommendations.append(
                        "🔴 CRITICAL: Forecasted capacity will exceed 90% - immediate action required"
                    )
                    recommendations.append(
                        f"   → Recommendation: Scale up {resource_metric} capacity or optimize resource usage"
                    )
                elif high_forecast > 80:
                    recommendations.append(
                        "🟡 WARNING: Forecasted capacity will exceed 80% - plan for scaling"
                    )
                    recommendations.append(
                        f"   → Recommendation: Schedule capacity increase for {resource_metric} in next 2-4 weeks"
                    )
                elif high_forecast > 70:
                    recommendations.append(
                        "🟢 MONITOR: Capacity approaching 70% - continue monitoring"
                    )
                else:
                    recommendations.append(
                        "✅ OK: Capacity forecast is healthy - no immediate action needed"
                    )

                # Growth rate
                growth_pct = ((forecast_util - current_util) / current_util * 100) if current_util > 0 else 0
                if abs(growth_pct) > 20:
                    recommendations.append(
                        f"   📈 Trend: {resource_metric} usage growing at {abs(growth_pct):.1f}% over forecast period"
                    )

        # Summary statistics
        summary = {
            "current_utilization": f"{historical_data[-1]['utilization_percent']:.2f}%" if historical_data else "N/A",
            "forecast_days": forecast_days,
            "forecast_points": len(forecast_data),
            "historical_points": len(historical_data),
        }

        if forecast_data:
            summary["forecast_utilization_end"] = f"{forecast_data[-1]['usage']:.2f}%"
            summary["forecast_high_confidence"] = f"{forecast_data[-1]['high_value']:.2f}%"
            summary["forecast_low_confidence"] = f"{forecast_data[-1]['low_value']:.2f}%"

        # Generate OCI Console URL
        region = config.get("region", "us-ashburn-1")
        console_url = None
        if database_id:
            console_url = format_oci_console_url(
                region=region,
                resource_type="database_insight",
                resource_id=database_id,
                page="forecast",
            )

        return {
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
            "forecast_days": forecast_days,
            "ascii_chart": ascii_chart,
            "historical_data": historical_data[-10:] if len(historical_data) > 10 else historical_data,  # Last 10 points
            "forecast_data": forecast_data,
            "summary": summary,
            "recommendations": recommendations,
            "oci_console_url": console_url,
            "note": "📊 For interactive forecast charts with confidence bands, open the OCI Console URL above",
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "resource_metric": resource_metric,
        }


def get_exadata_system_visualization(
    exadata_insight_id: str,
    compartment_id: str,
) -> Dict[str, Any]:
    """
    Get Exadata system rack visualization and topology information.

    This tool provides a text-based visualization of the Exadata system
    rack configuration, similar to the OCI Console rack view.

    Args:
        exadata_insight_id: Exadata Insight OCID.
        compartment_id: Compartment OCID.

    Returns:
        Dictionary containing:
        - rack_visualization: Text-based rack diagram
        - system_details: Exadata system hardware configuration
        - database_list: Databases running on the system
        - oci_console_url: Direct link to graphical rack view
    """
    try:
        client = get_opsi_client()
        config = get_oci_config()

        # Get Exadata insight details
        exadata_response = client.get_exadata_insight(exadata_insight_id=exadata_insight_id)
        exadata_data = exadata_response.data

        exadata_name = getattr(exadata_data, "exadata_display_name", "Unknown")
        exadata_type = getattr(exadata_data, "exadata_type", "Unknown")

        # Get resource statistics summary to find databases
        kwargs = {
            "exadata_insight_id": exadata_insight_id,
            "resource_metric": "CPU",
        }

        # Try to get member database information
        members_response = client.summarize_exadata_members(
            exadata_insight_id=exadata_insight_id,
            exadata_type="DBMACHINE",
        )

        databases = []
        storage_servers = 0
        compute_servers = 0

        if hasattr(members_response.data, "items"):
            for member in members_response.data.items:
                entity_type = getattr(member, "entity_type", "")
                if entity_type == "DATABASE":
                    databases.append({
                        "name": getattr(member, "entity_name", "Unknown"),
                        "type": getattr(member, "entity_type", "Unknown"),
                        "status": "Active",  # From insight status
                    })
                elif entity_type == "STORAGE_SERVER":
                    storage_servers += 1
                elif entity_type == "HOST":
                    compute_servers += 1

        # Create rack visualization
        rack_viz = format_exadata_rack_info(
            exadata_id=exadata_insight_id,
            exadata_name=exadata_name,
            databases=databases,
            storage_servers=storage_servers,
            compute_servers=compute_servers,
        )

        # Generate OCI Console URL
        region = config.get("region", "us-ashburn-1")
        console_url = format_oci_console_url(
            region=region,
            resource_type="exadata_insight",
            resource_id=exadata_insight_id,
        )

        return {
            "exadata_id": exadata_insight_id,
            "exadata_name": exadata_name,
            "exadata_type": exadata_type,
            "rack_visualization": rack_viz,
            "system_summary": {
                "compute_servers": compute_servers,
                "storage_servers": storage_servers,
                "databases_count": len(databases),
            },
            "databases": databases,
            "oci_console_url": console_url,
            "note": "🖼️  For graphical rack visualization with interactive components, open the OCI Console URL above",
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "exadata_insight_id": exadata_insight_id,
        }
