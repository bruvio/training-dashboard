"""
Activity Detail Page for Garmin Dashboard.

Research-validated implementation with dash-leaflet maps and synchronized
Plotly charts following enhanced PRP specifications.
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from app.data.web_queries import get_activity_by_id, get_activity_samples, check_database_connection
from app.data.queries import RoutePointQueries
from app.data.db import session_scope

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
                                                    html.H5(
                                                        [html.I(className="fas fa-chart-line me-2"), "Activity Charts"],
                                                        className="mb-0",
                                                    ),
                                                    dbc.Badge("Synchronized", color="info", className="ms-2"),
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
            return None, None, None, create_error_layout("Invalid activity URL"), {"display": "block"}

        activity_id_str = pathname.replace("/activity/", "")
        try:
            activity_id = int(activity_id_str)
        except ValueError:
            return None, None, None, create_error_layout("Invalid activity ID"), {"display": "block"}

        # Check database connection
        if not check_database_connection():
            return None, None, None, create_error_layout("Database connection failed"), {"display": "block"}

        # Load activity details
        activity = get_activity_by_id(activity_id)
        if not activity:
            return None, None, None, create_error_layout("Activity not found"), {"display": "block"}

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

        return activity, samples_data, route_bounds, None, {"display": "none"}

    except Exception as e:
        error_msg = f"Unexpected error loading activity: {str(e)}"
        return None, None, None, create_error_layout(error_msg), {"display": "block"}


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
    [Input("activity-samples-store", "data"), Input("activity-detail-store", "data")],
)
def update_activity_charts(samples_data: Optional[List[Dict]], activity_data: Optional[Dict]):
    """
    Create synchronized multi-subplot charts with research-validated patterns.

    Implements downsampling, proper axis labels, and unified hover mode
    as specified in the enhanced PRP.
    """
    if not samples_data or not isinstance(samples_data, list):
        return create_empty_chart_figure()

    # Convert to DataFrame for easier processing
    df = pd.DataFrame(samples_data)

    if df.empty:
        return create_empty_chart_figure()

    # Apply downsampling for performance (research recommendation)
    if len(df) > 5000:
        downsample_factor = len(df) // 2000
        df = df.iloc[:: max(downsample_factor, 1)]

    # Prepare time axis (convert seconds to minutes for readability)
    if "elapsed_time_s" in df.columns:
        df["elapsed_time_min"] = df["elapsed_time_s"] / 60
        x_axis = df["elapsed_time_min"]
        x_title = "Time (minutes)"
    else:
        x_axis = df.index
        x_title = "Sample Index"

    # Create subplots with research-validated configuration
    subplot_titles = []
    subplot_count = 0

    # Determine which subplots to include based on available data
    has_pace = "speed_mps" in df.columns and df["speed_mps"].notna().any()
    has_hr = "heart_rate_bpm" in df.columns and df["heart_rate_bpm"].notna().any()
    has_power = "power_w" in df.columns and df["power_w"].notna().any()
    has_elevation = "altitude_m" in df.columns and df["altitude_m"].notna().any()

    if has_pace:
        subplot_titles.append("Pace (min/km)")
        subplot_count += 1
    if has_hr:
        subplot_titles.append("Heart Rate (bpm)")
        subplot_count += 1
    if has_power:
        subplot_titles.append("Power (W)")
        subplot_count += 1
    if has_elevation:
        subplot_titles.append("Elevation (m)")
        subplot_count += 1

    if subplot_count == 0:
        return create_empty_chart_figure("No chart data available")

    # Create subplots
    fig = make_subplots(
        rows=subplot_count,
        cols=1,
        shared_xaxes=True,
        subplot_titles=subplot_titles,
        vertical_spacing=0.02,
        specs=[[{"secondary_y": False}]] * subplot_count,
    )

    current_row = 1

    # Add pace subplot
    if has_pace:
        # Convert speed to pace (research-validated formula)
        pace_data = []
        for speed in df["speed_mps"]:
            if speed and speed > 0:
                pace_min_per_km = (1000 / speed) / 60  # Convert to minutes per km
                pace_data.append(pace_min_per_km)
            else:
                pace_data.append(None)

        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=pace_data,
                mode="lines",
                name="Pace",
                line=dict(color="blue", width=2),
                hovertemplate="Time: %{x:.1f} min<br>Pace: %{y:.2f} min/km<extra></extra>",
            ),
            row=current_row,
            col=1,
        )
        current_row += 1

    # Add heart rate subplot
    if has_hr:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df["heart_rate_bpm"],
                mode="lines",
                name="Heart Rate",
                line=dict(color="red", width=2),
                hovertemplate="Time: %{x:.1f} min<br>HR: %{y} bpm<extra></extra>",
            ),
            row=current_row,
            col=1,
        )
        current_row += 1

    # Add power subplot
    if has_power:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df["power_w"],
                mode="lines",
                name="Power",
                line=dict(color="green", width=2),
                hovertemplate="Time: %{x:.1f} min<br>Power: %{y} W<extra></extra>",
            ),
            row=current_row,
            col=1,
        )
        current_row += 1

    # Add elevation subplot with area fill
    if has_elevation:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df["altitude_m"],
                mode="lines",
                fill="tonexty",
                name="Elevation",
                line=dict(color="brown", width=2),
                hovertemplate="Time: %{x:.1f} min<br>Elevation: %{y} m<extra></extra>",
            ),
            row=current_row,
            col=1,
        )

    # Update layout with research-validated synchronized hover
    fig.update_layout(
        hovermode="x unified",
        height=600,
        showlegend=False,
        title={
            "text": f"Activity Data - {activity_data.get('name', 'Unknown') if activity_data and activity_data.get('name') else 'Unknown'}",
            "x": 0.5,
            "xanchor": "center",
        },
    )

    # Format x-axis
    fig.update_xaxes(title_text=x_title, row=subplot_count, col=1)

    # Format y-axes with appropriate titles
    row = 1
    if has_pace:
        fig.update_yaxes(title_text="min/km", row=row, col=1)
        row += 1
    if has_hr:
        fig.update_yaxes(title_text="bpm", row=row, col=1)
        row += 1
    if has_power:
        fig.update_yaxes(title_text="Watts", row=row, col=1)
        row += 1
    if has_elevation:
        fig.update_yaxes(title_text="meters", row=row, col=1)

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
