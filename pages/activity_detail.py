"""
Activity detail page - Show detailed analysis and charts for a specific activity.
"""

from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.data.db import session_scope
from app.data.models import Activity, Sample

# This page uses manual routing - no registration needed


def layout(activity_id=None):
    """
    Layout for activity detail page.

    Args:
        activity_id: Activity ID from URL path
    """
    if not activity_id:
        return dbc.Alert("Invalid activity ID", color="danger")

    try:
        activity_id = int(activity_id)
    except ValueError:
        return dbc.Alert("Invalid activity ID format", color="danger")

    return dbc.Container(
        [
            dcc.Store(id="activity-data-store", data={"activity_id": activity_id}),
            # Header section
            dbc.Row([dbc.Col([html.Div(id="activity-header"), html.Hr()], width=12)]),
            # Charts and data section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Activity Charts", className="mb-0")]),
                                    dbc.CardBody([html.Div(id="activity-charts")]),
                                ]
                            )
                        ],
                        width=12,
                    )
                ],
                className="mb-4",
            ),
            # Route map section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Route Map", className="mb-0")]),
                                    dbc.CardBody([html.Div(id="activity-map")]),
                                ]
                            )
                        ],
                        width=12,
                    )
                ]
            ),
        ],
        fluid=True,
    )


@callback(Output("activity-header", "children"), Input("activity-data-store", "data"))
def update_activity_header(store_data):
    """Update activity header with basic info."""
    if not store_data or "activity_id" not in store_data:
        return dbc.Alert("No activity data", color="warning")

    activity_id = store_data["activity_id"]

    try:
        with session_scope() as session:
            activity = session.query(Activity).filter_by(id=activity_id).first()

            if not activity:
                return dbc.Alert(f"Activity {activity_id} not found", color="danger")

            # Format activity details
            duration_str = f"{activity.elapsed_time_s // 60:.0f} min" if activity.elapsed_time_s else "N/A"
            distance_str = f"{activity.distance_m/1000:.2f} km" if activity.distance_m else "N/A"
            speed_str = f"{activity.avg_speed_mps * 3.6:.1f} km/h" if activity.avg_speed_mps else "N/A"

            return html.Div(
                [
                    html.H1([html.I(className="fas fa-chart-line me-3"), f"Activity {activity_id}"]),
                    dbc.Row(
                        [
                            dbc.Col([html.Strong("Sport: "), activity.sport or "Unknown"], width=3),
                            dbc.Col([html.Strong("Duration: "), duration_str], width=3),
                            dbc.Col([html.Strong("Distance: "), distance_str], width=3),
                            dbc.Col([html.Strong("Avg Speed: "), speed_str], width=3),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Strong("Date: "),
                                    (
                                        activity.start_time_utc.strftime("%Y-%m-%d %H:%M:%S")
                                        if activity.start_time_utc
                                        else "Unknown"
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [html.Strong("Source: "), activity.source.upper() if activity.source else "Unknown"],
                                width=6,
                            ),
                        ]
                    ),
                ]
            )

    except Exception as e:
        return dbc.Alert(f"Error loading activity: {str(e)}", color="danger")


@callback(Output("activity-charts", "children"), Input("activity-data-store", "data"))
def update_activity_charts(store_data):
    """Update activity charts with sample data."""
    if not store_data or "activity_id" not in store_data:
        return dbc.Alert("No activity data", color="warning")

    activity_id = store_data["activity_id"]

    try:
        with session_scope() as session:
            # Get activity samples
            samples = session.query(Sample).filter_by(activity_id=activity_id).order_by(Sample.elapsed_time_s).all()

            if not samples:
                return dbc.Alert("No sample data found for this activity", color="info")

            # Convert to DataFrame
            sample_data = []
            for sample in samples:
                sample_data.append(
                    {
                        "time": sample.elapsed_time_s,
                        "heart_rate": sample.heart_rate,
                        "speed": sample.speed_mps * 3.6 if sample.speed_mps else None,  # Convert to km/h
                        "altitude": sample.altitude_m,
                        "power": sample.power_w,
                        "cadence": sample.cadence_rpm,
                    }
                )

            df = pd.DataFrame(sample_data)

            charts = []

            # Heart Rate Chart
            if "heart_rate" in df.columns and df["heart_rate"].notna().any():
                fig_hr = px.line(
                    df,
                    x="time",
                    y="heart_rate",
                    title="Heart Rate Over Time",
                    labels={"time": "Time (seconds)", "heart_rate": "Heart Rate (bpm)"},
                )
                fig_hr.update_layout(height=300)
                charts.append(dcc.Graph(figure=fig_hr))

            # Speed Chart
            if "speed" in df.columns and df["speed"].notna().any():
                fig_speed = px.line(
                    df,
                    x="time",
                    y="speed",
                    title="Speed Over Time",
                    labels={"time": "Time (seconds)", "speed": "Speed (km/h)"},
                )
                fig_speed.update_layout(height=300)
                charts.append(dcc.Graph(figure=fig_speed))

            # Altitude Chart
            if "altitude" in df.columns and df["altitude"].notna().any():
                fig_alt = px.line(
                    df,
                    x="time",
                    y="altitude",
                    title="Elevation Profile",
                    labels={"time": "Time (seconds)", "altitude": "Altitude (m)"},
                )
                fig_alt.update_layout(height=300)
                charts.append(dcc.Graph(figure=fig_alt))

            if not charts:
                return dbc.Alert("No chart data available", color="info")

            return html.Div(charts)

    except Exception as e:
        return dbc.Alert(f"Error loading charts: {str(e)}", color="danger")


@callback(Output("activity-map", "children"), Input("activity-data-store", "data"))
def update_activity_map(store_data):
    """Update activity route map."""
    if not store_data or "activity_id" not in store_data:
        return dbc.Alert("No activity data", color="warning")

    activity_id = store_data["activity_id"]

    try:
        with session_scope() as session:
            # Get GPS coordinates from samples
            samples = (
                session.query(Sample)
                .filter_by(activity_id=activity_id)
                .filter(Sample.latitude.isnot(None), Sample.longitude.isnot(None))
                .order_by(Sample.elapsed_time_s)
                .all()
            )

            if not samples:
                return dbc.Alert("No GPS data found for this activity", color="info")

            # Create route data
            lats = [sample.latitude for sample in samples]
            lons = [sample.longitude for sample in samples]

            if not lats or not lons:
                return dbc.Alert("No valid GPS coordinates found", color="info")

            # Create map
            fig = go.Figure()

            # Add route line
            fig.add_trace(
                go.Scattermapbox(
                    mode="lines+markers",
                    lon=lons,
                    lat=lats,
                    marker={"size": 4, "color": "red"},
                    line={"width": 3, "color": "red"},
                    name="Route",
                    hovertemplate="<b>Lat:</b> %{lat}<br><b>Lon:</b> %{lon}<extra></extra>",
                )
            )

            # Add start marker
            fig.add_trace(
                go.Scattermapbox(
                    mode="markers",
                    lon=[lons[0]],
                    lat=[lats[0]],
                    marker={"size": 12, "color": "green"},
                    name="Start",
                    hovertemplate="<b>Start</b><extra></extra>",
                )
            )

            # Add end marker
            fig.add_trace(
                go.Scattermapbox(
                    mode="markers",
                    lon=[lons[-1]],
                    lat=[lats[-1]],
                    marker={"size": 12, "color": "red"},
                    name="End",
                    hovertemplate="<b>End</b><extra></extra>",
                )
            )

            # Calculate center and zoom
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)

            fig.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(center=dict(lat=center_lat, lon=center_lon), zoom=12),
                showlegend=True,
                height=400,
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
            )

            return dcc.Graph(figure=fig)

    except Exception as e:
        return dbc.Alert(f"Error loading map: {str(e)}", color="danger")
