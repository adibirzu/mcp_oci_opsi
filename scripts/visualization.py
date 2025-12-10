"""Visualization utilities for MCP OCI OPSI - ASCII charts and data formatting."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


def create_ascii_line_chart(
    data_points: List[Dict[str, Any]],
    value_key: str,
    timestamp_key: str,
    width: int = 80,
    height: int = 20,
    title: str = "",
    show_forecast: bool = False,
    forecast_data: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Create an ASCII line chart from time-series data.

    Args:
        data_points: List of data points with timestamp and value
        value_key: Key for the value in each data point
        timestamp_key: Key for the timestamp in each data point
        width: Width of the chart in characters
        height: Height of the chart in characters
        title: Chart title
        show_forecast: Whether to show forecast data
        forecast_data: Optional forecast data points

    Returns:
        ASCII art line chart as a string
    """
    if not data_points:
        return "No data available for visualization"

    # Extract values
    values = [float(dp.get(value_key, 0)) for dp in data_points]
    timestamps = [dp.get(timestamp_key, "") for dp in data_points]

    # Add forecast values if provided
    forecast_values = []
    if show_forecast and forecast_data:
        forecast_values = [float(dp.get(value_key, 0)) for dp in forecast_data]
        forecast_timestamps = [dp.get(timestamp_key, "") for dp in forecast_data]

    # Find min/max for scaling
    all_values = values + forecast_values if forecast_values else values
    min_val = min(all_values) if all_values else 0
    max_val = max(all_values) if all_values else 100

    # Add padding
    value_range = max_val - min_val
    if value_range == 0:
        value_range = 1
    min_val -= value_range * 0.1
    max_val += value_range * 0.1
    value_range = max_val - min_val

    # Build chart
    chart = []

    # Title
    if title:
        chart.append(f"\n{title.center(width)}")
        chart.append("=" * width)

    # Y-axis labels and plot area
    y_labels_width = 10
    plot_width = width - y_labels_width - 2

    # Create grid
    grid = [[' ' for _ in range(plot_width)] for _ in range(height)]

    # Scale values to plot area
    def scale_value(val):
        return int((val - min_val) / value_range * (height - 1))

    # Plot historical data
    scaled_values = [scale_value(v) for v in values]
    for i, y in enumerate(scaled_values):
        x = int(i * (plot_width - 1) / max(len(scaled_values) - 1, 1))
        y = height - 1 - min(y, height - 1)
        if 0 <= x < plot_width and 0 <= y < height:
            grid[y][x] = '●'

    # Connect dots with lines (historical)
    for i in range(len(scaled_values) - 1):
        x1 = int(i * (plot_width - 1) / max(len(scaled_values) - 1, 1))
        x2 = int((i + 1) * (plot_width - 1) / max(len(scaled_values) - 1, 1))
        y1 = height - 1 - min(scaled_values[i], height - 1)
        y2 = height - 1 - min(scaled_values[i + 1], height - 1)

        # Draw line between points
        steps = max(abs(x2 - x1), abs(y2 - y1))
        if steps > 0:
            for step in range(steps):
                x = x1 + (x2 - x1) * step // steps
                y = y1 + (y2 - y1) * step // steps
                if 0 <= x < plot_width and 0 <= y < height:
                    if grid[y][x] == ' ':
                        grid[y][x] = '─'

    # Plot forecast data with different symbol
    if show_forecast and forecast_data and forecast_values:
        total_points = len(values) + len(forecast_values)
        for i, val in enumerate(forecast_values):
            y = scale_value(val)
            x = int((len(values) + i) * (plot_width - 1) / max(total_points - 1, 1))
            y = height - 1 - min(y, height - 1)
            if 0 <= x < plot_width and 0 <= y < height:
                grid[y][x] = '◆'

        # Connect forecast dots with dashed lines
        for i in range(len(forecast_values) - 1):
            x1 = int((len(values) + i) * (plot_width - 1) / max(total_points - 1, 1))
            x2 = int((len(values) + i + 1) * (plot_width - 1) / max(total_points - 1, 1))
            y1_val = scale_value(forecast_values[i])
            y2_val = scale_value(forecast_values[i + 1])
            y1 = height - 1 - min(y1_val, height - 1)
            y2 = height - 1 - min(y2_val, height - 1)

            steps = max(abs(x2 - x1), abs(y2 - y1))
            if steps > 0:
                for step in range(steps):
                    x = x1 + (x2 - x1) * step // steps
                    y = y1 + (y2 - y1) * step // steps
                    if 0 <= x < plot_width and 0 <= y < height:
                        if grid[y][x] == ' ':
                            grid[y][x] = '┈' if step % 2 == 0 else ' '

    # Render grid with Y-axis labels
    for i, row in enumerate(grid):
        val_at_row = max_val - (i * value_range / (height - 1))
        y_label = f"{val_at_row:8.1f} │"
        chart.append(y_label + ''.join(row))

    # X-axis
    chart.append(" " * y_labels_width + "└" + "─" * plot_width)

    # X-axis labels (first, middle, last)
    if timestamps:
        x_axis = " " * (y_labels_width + 1)
        first_time = _format_timestamp(timestamps[0])
        x_axis += first_time

        if len(timestamps) > 2:
            mid_idx = len(timestamps) // 2
            mid_time = _format_timestamp(timestamps[mid_idx])
            mid_pos = plot_width // 2 - len(mid_time) // 2
            x_axis += " " * (mid_pos - len(first_time)) + mid_time

        last_time = _format_timestamp(timestamps[-1])
        last_pos = plot_width - len(last_time)
        current_len = len(x_axis) - y_labels_width - 1
        x_axis += " " * (last_pos - current_len) + last_time

        chart.append(x_axis)

    # Legend
    if show_forecast:
        chart.append("\n" + " " * y_labels_width + "  ● Historical    ◆ Forecast")

    return "\n".join(chart)


def _format_timestamp(ts_str: str) -> str:
    """Format timestamp for display."""
    try:
        if 'T' in ts_str:
            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            return dt.strftime("%m/%d")
        return ts_str[:10]  # Return first 10 chars
    except:
        return ts_str[:10] if len(ts_str) >= 10 else ts_str


def create_capacity_summary(
    current_usage: float,
    current_capacity: float,
    forecast_usage: float,
    forecast_capacity: float,
    resource_type: str,
    database_name: str,
) -> str:
    """
    Create a textual capacity summary with bar visualization.

    Args:
        current_usage: Current resource usage
        current_capacity: Current resource capacity
        forecast_usage: Forecasted resource usage
        forecast_capacity: Forecasted resource capacity
        resource_type: Type of resource (CPU, STORAGE, etc.)
        database_name: Name of the database

    Returns:
        Formatted capacity summary string
    """
    current_pct = (current_usage / current_capacity * 100) if current_capacity > 0 else 0
    forecast_pct = (forecast_usage / forecast_capacity * 100) if forecast_capacity > 0 else 0

    summary = []
    summary.append(f"\n{'=' * 70}")
    summary.append(f"  {resource_type} Capacity Summary: {database_name}")
    summary.append(f"{'=' * 70}\n")

    # Current status
    summary.append(f"Current Status:")
    summary.append(f"  Usage:    {current_usage:>8.2f} / {current_capacity:>8.2f} ({current_pct:>5.1f}%)")
    summary.append(f"  {_create_progress_bar(current_pct, 50)}\n")

    # Forecast
    summary.append(f"Forecasted (30 days):")
    summary.append(f"  Usage:    {forecast_usage:>8.2f} / {forecast_capacity:>8.2f} ({forecast_pct:>5.1f}%)")
    summary.append(f"  {_create_progress_bar(forecast_pct, 50)}")

    # Growth
    growth_pct = ((forecast_usage - current_usage) / current_usage * 100) if current_usage > 0 else 0
    trend = "↑" if growth_pct > 0 else "↓" if growth_pct < 0 else "→"
    summary.append(f"\nGrowth Trend: {trend} {abs(growth_pct):.1f}%")

    # Recommendations
    if forecast_pct > 90:
        summary.append("\n⚠️  WARNING: Capacity will exceed 90% - consider scaling up")
    elif forecast_pct > 80:
        summary.append("\n⚡ CAUTION: Capacity approaching 80% - monitor closely")
    elif forecast_pct < 50:
        summary.append("\n✓ OK: Capacity utilization is healthy")

    summary.append(f"\n{'=' * 70}\n")

    return "\n".join(summary)


def _create_progress_bar(percentage: float, width: int = 50) -> str:
    """Create a text-based progress bar."""
    filled = int(width * percentage / 100)
    empty = width - filled

    # Color indicators
    if percentage >= 90:
        symbol = "█"
        color = "🔴"
    elif percentage >= 80:
        symbol = "█"
        color = "🟡"
    else:
        symbol = "█"
        color = "🟢"

    bar = "[" + symbol * filled + "░" * empty + "]"
    return f"{color} {bar} {percentage:>5.1f}%"


def format_exadata_rack_info(
    exadata_id: str,
    exadata_name: str,
    databases: List[Dict[str, Any]],
    storage_servers: int,
    compute_servers: int,
) -> str:
    """
    Format Exadata rack information in a readable structure.

    Args:
        exadata_id: Exadata system OCID
        exadata_name: Exadata system name
        databases: List of databases on the system
        storage_servers: Number of storage servers
        compute_servers: Number of compute servers

    Returns:
        Formatted Exadata rack information
    """
    output = []
    output.append(f"\n{'=' * 80}")
    output.append(f"  Exadata System: {exadata_name}")
    output.append(f"{'=' * 80}\n")

    # System overview
    output.append(f"System ID: {exadata_id}")
    output.append(f"\nHardware Configuration:")
    output.append(f"  ├─ Compute Servers:  {compute_servers}")
    output.append(f"  ├─ Storage Servers:  {storage_servers}")
    output.append(f"  └─ Databases:        {len(databases)}")

    # Database list
    if databases:
        output.append(f"\nDatabases on System:")
        for i, db in enumerate(databases, 1):
            db_name = db.get('name', 'Unknown')
            db_type = db.get('type', 'Unknown')
            db_status = db.get('status', 'Unknown')
            is_last = i == len(databases)
            prefix = "  └─" if is_last else "  ├─"
            output.append(f"{prefix} {db_name} ({db_type}) - Status: {db_status}")

    output.append(f"\n{'=' * 80}\n")

    return "\n".join(output)


def format_oci_console_url(
    region: str,
    resource_type: str,
    resource_id: str,
    page: Optional[str] = None,
) -> str:
    """
    Generate OCI Console URL for a resource.

    Args:
        region: OCI region (e.g., "us-ashburn-1", "uk-london-1")
        resource_type: Type of resource (database, exadata, opsi)
        resource_id: Resource OCID
        page: Optional specific page/tab

    Returns:
        OCI Console URL
    """
    base_url = "https://cloud.oracle.com"

    # Map resource types to console paths
    resource_paths = {
        "database_insight": f"/operations-insights/database-insights/{resource_id}",
        "exadata_insight": f"/operations-insights/exadata-insights/{resource_id}",
        "exadata": f"/db/exadata/{resource_id}",
        "autonomous_database": f"/db/adb/{resource_id}",
        "database": f"/db/databases/{resource_id}",
        "host_insight": f"/operations-insights/host-insights/{resource_id}",
    }

    path = resource_paths.get(resource_type, f"/{resource_type}/{resource_id}")
    url = f"{base_url}{path}?region={region}"

    if page:
        url += f"&page={page}"

    return url


def add_visualization_to_response(
    response: Dict[str, Any],
    chart_data: Optional[Dict[str, Any]] = None,
    console_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add visualization and console URL to a response dictionary.

    Args:
        response: Original response dictionary
        chart_data: Optional chart configuration
        console_url: Optional OCI console URL

    Returns:
        Enhanced response with visualization
    """
    if chart_data:
        response["visualization"] = chart_data

    if console_url:
        response["oci_console_url"] = console_url
        response["note"] = "For graphical visualization, open the OCI Console URL"

    return response
