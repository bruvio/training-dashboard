"""
Activity Detail Page for Garmin Dashboard.

Research-validated implementation with dash-leaflet maps and synchronized
Plotly charts following enhanced PRP specifications.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import ndimage
from scipy.signal import savgol_filter

from app.data.web_queries import get_activity_by_id, get_activity_samples, check_database_connection

# Register this page with dynamic routing (Dash 2.17+ pattern)
dash.register_page(
    __name__,
    path="/activity/<activity_id>",
    title="Activity Detail - Garmin Dashboard",
    name="Activity Detail",
    description="View detailed activity information with maps and charts",
)


def layout(activity_id: str = None, **kwargs):
    """
    Layout for the activity detail page.

    Research-validated implementation with responsive layout,
    dash-leaflet map integration, and synchronized charts.
    """
    if not activity_id:
        return create_error_layout("No activity ID provided")

    return dbc.Container(
        [
            # Store components for data management
            dcc.Store(id="activity-detail-store", data={}),
            dcc.Store(id="activity-samples-store", data=[]),
            dcc.Store(id="activity-laps-store", data=[]),
            dcc.Store(id="route-bounds-store", data={}),
            # Loading states
            dcc.Loading(
                id="loading-activity-detail",
                type="default",
                children=[
                    # Back button and header
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [html.I(className="fas fa-arrow-left me-2"), "Back to Activities"],
                                        href="/",
                                        color="secondary",
                                        outline=True,
                                        size="sm",
                                        className="mb-3",
                                    )
                                ]
                            )
                        ]
                    ),
                    # Activity header
                    dbc.Row([dbc.Col([html.Div(id="activity-header")])], className="mb-4"),
                    # Main content row - Map and Summary
                    dbc.Row(
                        [
                            # Map column
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                [
                                                    html.H5(
                                                        [html.I(className="fas fa-map me-2"), "Route Map"],
                                                        className="mb-0",
                                                    )
                                                ]
                                            ),
                                            dbc.CardBody(
                                                [
                                                    html.Div(
                                                        [
                                                            dl.Map(
                                                                [
                                                                    dl.TileLayer(
                                                                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                                                                        attribution="&copy; OpenStreetMap contributors",
                                                                    ),
                                                                    dl.Polyline(
                                                                        id="route-polyline",
                                                                        positions=[],
                                                                        color="red",
                                                                        weight=3,
                                                                        opacity=0.8,
                                                                    ),
                                                                ],
                                                                id="activity-map",
                                                                style={"width": "100%", "height": "400px"},
                                                                center=[0, 0],
                                                                zoom=2,
                                                            )
                                                        ],
                                                        className="map-container",
                                                    ),
                                                    html.Div(id="map-status", className="mt-2 text-muted small"),
                                                ],
                                                className="p-0",
                                            ),
                                        ]
                                    )
                                ],
                                lg=8,
                                md=12,
                            ),
                            # Summary statistics column
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                [
                                                    html.H5(
                                                        [html.I(className="fas fa-chart-bar me-2"), "Activity Summary"],
                                                        className="mb-0",
                                                    )
                                                ]
                                            ),
                                            dbc.CardBody([html.Div(id="activity-summary")]),
                                        ]
                                    )
                                ],
                                lg=4,
                                md=12,
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Charts section
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    html.H5(
                                                                        [
                                                                            html.I(className="fas fa-chart-line me-2"),
                                                                            "Activity Charts",
                                                                        ],
                                                                        className="mb-0",
                                                                    ),
                                                                    dbc.Badge(
                                                                        "Interactive", color="info", className="ms-2"
                                                                    ),
                                                                ],
                                                                width="auto",
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    dbc.Row(
                                                                        [
                                                                            dbc.Col(
                                                                                [
                                                                                    dbc.Label(
                                                                                        "Chart Type:",
                                                                                        size="sm",
                                                                                        className="me-2",
                                                                                    ),
                                                                                    dbc.Select(
                                                                                        id="chart-type-selector",
                                                                                        options=[
                                                                                            {
                                                                                                "label": "Multi-subplot (Default)",
                                                                                                "value": "subplots",
                                                                                            },
                                                                                            {
                                                                                                "label": "Single Chart - Dual Y-axis",
                                                                                                "value": "dual_y",
                                                                                            },
                                                                                            {
                                                                                                "label": "Overlay - Single Y-axis",
                                                                                                "value": "overlay",
                                                                                            },
                                                                                        ],
                                                                                        value="subplots",
                                                                                        size="sm",
                                                                                    ),
                                                                                ],
                                                                                width=6,
                                                                            ),
                                                                            dbc.Col(
                                                                                [
                                                                                    dbc.Label(
                                                                                        "Smoothing:",
                                                                                        size="sm",
                                                                                        className="me-2",
                                                                                    ),
                                                                                    dbc.Select(
                                                                                        id="smoothing-selector",
                                                                                        options=[
                                                                                            {
                                                                                                "label": "None",
                                                                                                "value": "none",
                                                                                            },
                                                                                            {
                                                                                                "label": "Light",
                                                                                                "value": "light",
                                                                                            },
                                                                                            {
                                                                                                "label": "Medium",
                                                                                                "value": "medium",
                                                                                            },
                                                                                            {
                                                                                                "label": "Heavy",
                                                                                                "value": "heavy",
                                                                                            },
                                                                                        ],
                                                                                        value="none",
                                                                                        size="sm",
                                                                                    ),
                                                                                ],
                                                                                width=6,
                                                                            ),
                                                                        ]
                                                                    )
                                                                ],
                                                                className="ms-auto",
                                                            ),
                                                        ],
                                                        className="align-items-center",
                                                    ),
                                                ]
                                            ),
                                            dbc.CardBody(
                                                [
                                                    dcc.Graph(
                                                        id="activity-charts",
                                                        className="chart-container",
                                                        config={
                                                            "displayModeBar": True,
                                                            "displaylogo": False,
                                                            "modeBarButtonsToRemove": ["pan2d", "lasso2d"],
                                                        },
                                                    )
                                                ],
                                                className="p-2",
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),
                ],
            ),
            # Error state
            html.Div(id="error-state", style={"display": "none"}),
        ],
        fluid=True,
    )


def create_error_layout(error_message: str):
    """Create error layout for failed loads."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Alert(
                                [
                                    html.H4(
                                        [html.I(className="fas fa-exclamation-triangle me-2"), "Error Loading Activity"]
                                    ),
                                    html.P(error_message),
                                    dbc.Button("Back to Activities", href="/", color="primary"),
                                ],
                                color="danger",
                            )
                        ],
                        width=8,
                        className="mx-auto mt-5",
                    )
                ]
            )
        ]
    )


# Main callback to load activity data
@callback(
    [
        Output("activity-detail-store", "data"),
        Output("activity-samples-store", "data"),
        Output("activity-laps-store", "data"),
        Output("route-bounds-store", "data"),
        Output("error-state", "children"),
        Output("error-state", "style"),
    ],
    [Input("url", "pathname")],
    prevent_initial_call=False,
)
def load_activity_data(pathname: str):
    """
    Load activity data, samples, and route information.

    Research-validated pattern for data loading with comprehensive
    error handling and graceful degradation.
    """
    try:
        # Extract activity ID from URL
        if not pathname or not pathname.startswith("/activity/"):
            return None, None, None, None, create_error_layout("Invalid activity URL"), {"display": "block"}

        activity_id_str = pathname.replace("/activity/", "")
        try:
            activity_id = int(activity_id_str)
        except ValueError:
            return None, None, None, None, create_error_layout("Invalid activity ID"), {"display": "block"}

        # Check database connection
        if not check_database_connection():
            return None, None, None, None, create_error_layout("Database connection failed"), {"display": "block"}

        # Load activity details
        activity = get_activity_by_id(activity_id)
        if not activity:
            return None, None, None, None, create_error_layout("Activity not found"), {"display": "block"}

        # Load sample data
        samples_df = get_activity_samples(activity_id)
        samples_data = samples_df.to_dict("records") if not samples_df.empty else []

        # Load route bounds for map centering
        route_bounds = None
        if samples_data:
            # Calculate bounds from samples with GPS data
            gps_samples = [s for s in samples_data if s.get("position_lat") and s.get("position_long")]
            if gps_samples:
                lats = [s["position_lat"] for s in gps_samples]
                lons = [s["position_long"] for s in gps_samples]

                route_bounds = {
                    "min_lat": min(lats),
                    "max_lat": max(lats),
                    "min_lon": min(lons),
                    "max_lon": max(lons),
                    "center_lat": sum(lats) / len(lats),
                    "center_lon": sum(lons) / len(lons),
                }

        # Load lap data for visualization
        from ..data.web_queries import get_activity_laps

        laps_data = get_activity_laps(activity_id)

        return activity, samples_data, laps_data, route_bounds, None, {"display": "none"}

    except Exception as e:
        error_msg = f"Unexpected error loading activity: {str(e)}"
        return None, None, None, None, create_error_layout(error_msg), {"display": "block"}


# Callback for activity header
@callback(Output("activity-header", "children"), [Input("activity-detail-store", "data")])
def update_activity_header(activity_data: Optional[Dict[str, Any]]):
    """Update the activity header with basic information."""
    if not activity_data or not isinstance(activity_data, dict):
        return html.Div()

    # Format start time
    start_time_str = "Unknown"
    if activity_data.get("start_time"):
        try:
            if isinstance(activity_data["start_time"], str):
                dt = datetime.fromisoformat(activity_data["start_time"].replace("Z", "+00:00"))
            else:
                dt = activity_data["start_time"]
            start_time_str = dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except (ValueError, TypeError):
            start_time_str = str(activity_data["start_time"])

    # Sport emoji mapping
    sport_emoji_map = {"running": "🏃", "cycling": "🚴", "swimming": "🏊", "hiking": "🥾", "walking": "🚶"}

    sport = activity_data.get("sport", "unknown")
    sport_emoji = sport_emoji_map.get(sport, "⚽")

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H2(
                        [
                            sport_emoji,
                            " ",
                            activity_data.get("name", f"{sport.title()} Activity"),
                            dbc.Badge(
                                activity_data.get("source", "unknown").upper(), color="secondary", className="ms-3"
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P(
                                        [html.I(className="fas fa-calendar me-2"), start_time_str],
                                        className="text-muted mb-2",
                                    )
                                ],
                                lg=6,
                            ),
                            dbc.Col(
                                [
                                    html.P(
                                        [
                                            html.I(className="fas fa-clock me-2"),
                                            format_duration(activity_data.get("total_time_s", 0)),
                                        ],
                                        className="text-muted mb-2",
                                    )
                                ],
                                lg=6,
                            ),
                        ]
                    ),
                ]
            )
        ],
        color="light",
        outline=True,
    )


# Callback for activity summary statistics
@callback(Output("activity-summary", "children"), [Input("activity-detail-store", "data")])
def update_activity_summary(activity_data: Optional[Dict[str, Any]]):
    """Update the activity summary statistics."""
    if not activity_data or not isinstance(activity_data, dict):
        return html.Div()

    summary_cards = []

    # Distance
    if activity_data.get("total_distance_km"):
        summary_cards.append(
            create_stat_card("Distance", f"{activity_data['total_distance_km']:.2f} km", "fas fa-route", "primary")
        )

    # Duration
    duration_str = format_duration(activity_data.get("total_time_s", 0))
    summary_cards.append(create_stat_card("Duration", duration_str, "fas fa-clock", "info"))

    # Average Heart Rate
    if activity_data.get("avg_hr"):
        summary_cards.append(
            create_stat_card("Avg HR", f"{int(activity_data['avg_hr'])} bpm", "fas fa-heartbeat", "danger")
        )

    # Average Power
    if activity_data.get("avg_power_w"):
        summary_cards.append(
            create_stat_card("Avg Power", f"{int(activity_data['avg_power_w'])} W", "fas fa-bolt", "warning")
        )

    # Elevation Gain
    if activity_data.get("elevation_gain_m"):
        summary_cards.append(
            create_stat_card("Elevation", f"{int(activity_data['elevation_gain_m'])} m", "fas fa-mountain", "success")
        )

    # Calories
    if activity_data.get("calories"):
        summary_cards.append(create_stat_card("Calories", f"{int(activity_data['calories'])}", "fas fa-fire", "danger"))

    return html.Div(summary_cards)


def create_stat_card(title: str, value: str, icon: str, color: str):
    """Create a statistics card."""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(className=f"{icon} fa-lg text-{color} mb-2"),
                            html.H4(value, className="mb-0"),
                            html.P(title, className="text-muted small mb-0"),
                        ],
                        className="text-center",
                    )
                ]
            )
        ],
        className="mb-3",
    )


# Callback for map updates
@callback(
    [
        Output("route-polyline", "positions"),
        Output("activity-map", "center"),
        Output("activity-map", "zoom"),
        Output("map-status", "children"),
    ],
    [Input("activity-samples-store", "data"), Input("route-bounds-store", "data")],
)
def update_activity_map(samples_data: Optional[List[Dict]], route_bounds: Optional[Dict]):
    """
    Update the activity map with route polyline and proper centering.

    Research-validated dash-leaflet integration with GPS route visualization.
    """
    if not samples_data or not isinstance(samples_data, list):
        return [], [0, 0], 2, "No GPS data available for this activity"

    # Extract GPS coordinates from samples
    route_positions = []
    for sample in samples_data:
        if sample.get("position_lat") and sample.get("position_long"):
            route_positions.append([sample["position_lat"], sample["position_long"]])

    if not route_positions:
        return [], [0, 0], 2, "No GPS data available for this activity"

    # Calculate map center and zoom
    if route_bounds:
        center_lat = route_bounds["center_lat"]
        center_lon = route_bounds["center_lon"]

        # Calculate appropriate zoom level based on route bounds
        lat_diff = route_bounds["max_lat"] - route_bounds["min_lat"]
        lon_diff = route_bounds["max_lon"] - route_bounds["min_lon"]
        max_diff = max(lat_diff, lon_diff)

        # Empirical zoom calculation
        if max_diff > 1.0:
            zoom = 8
        elif max_diff > 0.1:
            zoom = 10
        elif max_diff > 0.01:
            zoom = 13
        else:
            zoom = 15

        center = [center_lat, center_lon]
        status = f"Route with {len(route_positions)} GPS points"

    else:
        # Fallback to first point
        center = route_positions[0]
        zoom = 13
        status = f"Route with {len(route_positions)} GPS points"

    return route_positions, center, zoom, status


# Callback for activity charts
@callback(
    Output("activity-charts", "figure"),
    [
        Input("activity-samples-store", "data"),
        Input("activity-detail-store", "data"),
        Input("activity-laps-store", "data"),
        Input("chart-type-selector", "value"),
        Input("smoothing-selector", "value"),
    ],
)
def update_activity_charts(
    samples_data: Optional[List[Dict]],
    activity_data: Optional[Dict],
    laps_data: Optional[List[Dict]] = None,
    chart_type: str = "subplots",
    smoothing: str = "none",
):
    """
    Create fitplotter-style interactive charts with multiple view modes.

    Implements chart type selection, data smoothing, and enhanced interactivity
    inspired by the fitplotter library.
    """
    if not samples_data or not isinstance(samples_data, list):
        return create_empty_chart_figure()

    # Convert to DataFrame for easier processing
    df = pd.DataFrame(samples_data)

    if df.empty:
        return create_empty_chart_figure()

    # Apply intelligent downsampling for performance
    if len(df) > 5000:
        downsample_factor = len(df) // 2500
        df = df.iloc[:: max(downsample_factor, 1)]

    # Prepare time axis
    if "elapsed_time_s" in df.columns:
        df["elapsed_time_min"] = df["elapsed_time_s"] / 60
        x_axis = df["elapsed_time_min"]
        x_title = "Time (minutes)"
    else:
        x_axis = df.index
        x_title = "Sample Index"

    # Determine available data types
    data_types = []
    if "speed_mps" in df.columns and df["speed_mps"].notna().any():
        data_types.append(("pace", "Pace", "min/km", "blue"))
    if "heart_rate_bpm" in df.columns and df["heart_rate_bpm"].notna().any():
        data_types.append(("heart_rate", "Heart Rate", "bpm", "red"))
    if "power_w" in df.columns and df["power_w"].notna().any():
        data_types.append(("power", "Power", "W", "green"))
    if "altitude_m" in df.columns and df["altitude_m"].notna().any():
        data_types.append(("elevation", "Elevation", "m", "brown"))
    if "cadence_rpm" in df.columns and df["cadence_rpm"].notna().any():
        data_types.append(("cadence", "Cadence", "rpm", "orange"))

    if not data_types:
        return create_empty_chart_figure("No chart data available")

    # Prepare data with smoothing
    prepared_data = prepare_chart_data(df, data_types, smoothing)

    # Create charts based on selected type
    if chart_type == "subplots":
        return create_subplot_chart(x_axis, x_title, prepared_data, data_types, activity_data, laps_data)
    elif chart_type == "dual_y":
        return create_dual_y_chart(x_axis, x_title, prepared_data, data_types, activity_data, laps_data)
    elif chart_type == "overlay":
        return create_overlay_chart(x_axis, x_title, prepared_data, data_types, activity_data, laps_data)
    else:
        return create_subplot_chart(x_axis, x_title, prepared_data, data_types, activity_data, laps_data)


def prepare_chart_data(df: pd.DataFrame, data_types: list, smoothing: str = "none"):
    """Prepare and smooth chart data based on selected smoothing level."""
    prepared_data = {}

    for data_key, display_name, unit, color in data_types:
        if data_key == "pace" and "speed_mps" in df.columns:
            # Convert speed to pace (min/km), handling zero speeds
            speed_kmh = df["speed_mps"] * 3.6
            pace_data = np.where(speed_kmh > 0.1, 60 / speed_kmh, np.nan)
            # Cap pace at reasonable max (15 min/km)
            pace_data = np.where(pace_data > 15, 15, pace_data)
            prepared_data[data_key] = pace_data
        elif data_key == "heart_rate" and "heart_rate_bpm" in df.columns:
            prepared_data[data_key] = df["heart_rate_bpm"].values
        elif data_key == "power" and "power_w" in df.columns:
            prepared_data[data_key] = df["power_w"].values
        elif data_key == "elevation" and "altitude_m" in df.columns:
            prepared_data[data_key] = df["altitude_m"].values
        elif data_key == "cadence" and "cadence_rpm" in df.columns:
            prepared_data[data_key] = df["cadence_rpm"].values

    # Apply smoothing if requested
    if smoothing != "none":
        window_sizes = {"light": 5, "medium": 15, "heavy": 31}
        window = window_sizes.get(smoothing, 5)

        for key, data in prepared_data.items():
            if len(data) > window and not np.all(np.isnan(data)):
                try:
                    # Use Savitzky-Golay filter for better smoothing
                    if len(data) > window:
                        smooth_data = savgol_filter(data, min(window, len(data) // 3 * 2 - 1), 3, mode="nearest")
                        prepared_data[key] = smooth_data
                except:
                    # Fallback to simple moving average
                    prepared_data[key] = ndimage.uniform_filter1d(data, size=window, mode="nearest")

    return prepared_data


def add_lap_markers(fig, x_axis, laps_data: Optional[List[Dict]] = None, subplot_row: int = None):
    """Add lap markers to chart figure."""
    if not laps_data:
        return

    for i, lap in enumerate(laps_data):
        start_time_min = lap.get("start_time_s", 0) / 60
        lap.get("end_time_s", 0) / 60

        # Add vertical line at lap start
        fig.add_vline(
            x=start_time_min,
            line=dict(color="rgba(255, 0, 0, 0.6)", width=1, dash="dash"),
            annotation_text=f"L{lap.get('lap_index', i)}",
            annotation_position="top",
            annotation_font_size=10,
            row=subplot_row,
            col=1 if subplot_row else None,
        )


def create_subplot_chart(
    x_axis,
    x_title: str,
    prepared_data: dict,
    data_types: list,
    activity_data: dict,
    laps_data: Optional[List[Dict]] = None,
):
    """Create multi-subplot chart layout similar to fitplotter."""
    n_charts = len(data_types)
    fig = make_subplots(
        rows=n_charts,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=[f"{display_name} ({unit})" for _, display_name, unit, _ in data_types],
    )

    for i, (data_key, display_name, unit, color) in enumerate(data_types, 1):
        if data_key in prepared_data:
            y_data = prepared_data[data_key]
            valid_mask = ~np.isnan(y_data)

            fig.add_trace(
                go.Scatter(
                    x=x_axis[valid_mask],
                    y=y_data[valid_mask],
                    mode="lines",
                    name=display_name,
                    line=dict(color=color, width=2),
                    hovertemplate=f"<b>{display_name}</b><br>Time: %{{x:.1f}} min<br>{display_name}: %{{y:.1f}} {unit}<extra></extra>",
                    showlegend=False,
                ),
                row=i,
                col=1,
            )

            # Update y-axis for this subplot
            fig.update_yaxes(title_text=unit, row=i, col=1)

    # Add lap markers to each subplot
    for i in range(1, n_charts + 1):
        add_lap_markers(fig, x_axis, laps_data, subplot_row=i)

    # Update layout
    fig.update_xaxes(title_text=x_title, row=n_charts, col=1)
    fig.update_layout(
        height=150 * n_charts + 100,
        showlegend=False,
        title_text=activity_data.get("name", "Activity Charts") if activity_data else "Activity Charts",
        hovermode="x unified",
    )

    return fig


def create_dual_y_chart(
    x_axis,
    x_title: str,
    prepared_data: dict,
    data_types: list,
    activity_data: dict,
    laps_data: Optional[List[Dict]] = None,
):
    """Create dual y-axis chart with primary and secondary metrics."""
    fig = go.Figure()

    # Primary axis (first available metric)
    primary_data = None
    secondary_data = []

    for i, (data_key, display_name, unit, color) in enumerate(data_types):
        if data_key in prepared_data:
            y_data = prepared_data[data_key]
            valid_mask = ~np.isnan(y_data)

            if i == 0:  # First metric goes on primary y-axis
                fig.add_trace(
                    go.Scatter(
                        x=x_axis[valid_mask],
                        y=y_data[valid_mask],
                        mode="lines",
                        name=f"{display_name} ({unit})",
                        line=dict(color=color, width=2),
                        hovertemplate=f"<b>{display_name}</b><br>Time: %{{x:.1f}} min<br>{display_name}: %{{y:.1f}} {unit}<extra></extra>",
                        yaxis="y",
                    )
                )
                primary_data = (display_name, unit, color)
            else:  # Other metrics go on secondary y-axis
                fig.add_trace(
                    go.Scatter(
                        x=x_axis[valid_mask],
                        y=y_data[valid_mask],
                        mode="lines",
                        name=f"{display_name} ({unit})",
                        line=dict(color=color, width=2, dash="dot"),
                        hovertemplate=f"<b>{display_name}</b><br>Time: %{{x:.1f}} min<br>{display_name}: %{{y:.1f}} {unit}<extra></extra>",
                        yaxis="y2",
                    )
                )
                secondary_data.append((display_name, unit, color))

    # Add lap markers
    add_lap_markers(fig, x_axis, laps_data)

    # Update layout with dual y-axes
    fig.update_layout(
        title_text=activity_data.get("name", "Activity Chart") if activity_data else "Activity Chart",
        xaxis_title=x_title,
        yaxis=dict(
            title=f"{primary_data[1]}" if primary_data else "Primary Metric",
            side="left",
            color=primary_data[2] if primary_data else "blue",
        ),
        yaxis2=dict(
            title=f"{secondary_data[0][1]}" if secondary_data else "Secondary Metric",
            side="right",
            overlaying="y",
            color=secondary_data[0][2] if secondary_data else "red",
        ),
        height=500,
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    return fig


def create_overlay_chart(
    x_axis,
    x_title: str,
    prepared_data: dict,
    data_types: list,
    activity_data: dict,
    laps_data: Optional[List[Dict]] = None,
):
    """Create overlay chart with normalized data on single y-axis."""
    fig = go.Figure()

    # Normalize all data to 0-100 scale for overlay visualization
    for data_key, display_name, unit, color in data_types:
        if data_key in prepared_data:
            y_data = prepared_data[data_key]
            valid_mask = ~np.isnan(y_data)

            if valid_mask.sum() > 0:
                # Normalize to 0-100 scale
                valid_data = y_data[valid_mask]
                data_min, data_max = np.min(valid_data), np.max(valid_data)
                if data_max > data_min:
                    normalized_data = ((valid_data - data_min) / (data_max - data_min)) * 100
                else:
                    normalized_data = np.full_like(valid_data, 50)

                fig.add_trace(
                    go.Scatter(
                        x=x_axis[valid_mask],
                        y=normalized_data,
                        mode="lines",
                        name=f"{display_name}",
                        line=dict(color=color, width=2),
                        hovertemplate=f"<b>{display_name}</b><br>Time: %{{x:.1f}} min<br>Normalized: %{{y:.1f}}%<br>Actual: %{{customdata:.1f}} {unit}<extra></extra>",
                        customdata=valid_data,
                    )
                )

    # Add lap markers
    add_lap_markers(fig, x_axis, laps_data)

    fig.update_layout(
        title_text=(
            activity_data.get("name", "Activity Chart (Normalized)") if activity_data else "Activity Chart (Normalized)"
        ),
        xaxis_title=x_title,
        yaxis_title="Normalized Value (%)",
        height=500,
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    return fig


def create_empty_chart_figure(message: str = "No data available"):
    """Create empty figure with message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="gray")
    )
    fig.update_layout(height=400, showlegend=False, xaxis={"visible": False}, yaxis={"visible": False})
    return fig


def format_duration(total_seconds: int) -> str:
    """Format duration in seconds to readable string."""
    if not total_seconds:
        return "0:00"

    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"
