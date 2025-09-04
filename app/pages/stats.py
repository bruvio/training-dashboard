"""
Statistics page for activity analytics and insights.
"""

from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from app.data.web_queries import (
    get_activity_statistics,
    get_activity_trends,
    get_intensity_data,
    get_sleep_data,
    get_steps_data,
    get_stress_data,
    get_wellness_statistics,
    get_heart_rate_data,
    get_body_battery_data,
    get_training_readiness_data,
    get_spo2_data,
    get_personal_records_data,
    get_max_metrics_data,
)
from app.utils import get_logger

logger = get_logger(__name__)


def layout():
    """Statistics page layout."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1([html.I(className="fas fa-chart-line me-3"), "Statistics"], className="mb-4"),
                            # Statistics cards - now dynamic
                            html.Div(id="stats-cards-container"),
                            # Activity trends chart
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Activity Trends", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="activity-trends-chart"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Wellness Statistics Header
                            html.H2([html.I(className="fas fa-heart me-3"), "Wellness Data"], className="mb-4 mt-5"),
                            # Wellness statistics cards
                            html.Div(id="wellness-stats-container"),
                            # Sleep data visualization
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Sleep Analysis", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            dcc.Tabs(
                                                id="sleep-tabs",
                                                value="sleep-quality",
                                                children=[
                                                    dcc.Tab(label="Sleep Quality", value="sleep-quality"),
                                                    dcc.Tab(label="Sleep Stages", value="sleep-stages"),
                                                ],
                                            ),
                                            html.Div(id="sleep-chart"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Stress data visualization
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Stress Analysis", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="stress-chart"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Steps and activity data
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Daily Activity", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            dcc.Tabs(
                                                id="activity-tabs",
                                                value="steps",
                                                children=[
                                                    dcc.Tab(label="Daily Steps", value="steps"),
                                                    dcc.Tab(label="Intensity Minutes", value="intensity"),
                                                ],
                                            ),
                                            html.Div(id="activity-chart"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Advanced Wellness Header
                            html.H2([html.I(className="fas fa-heartbeat me-3"), "Advanced Wellness"], className="mb-4 mt-5"),
                            # Heart Rate Analytics
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Heart Rate Analytics", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            dcc.Tabs(
                                                id="hr-tabs",
                                                value="resting-hr",
                                                children=[
                                                    dcc.Tab(label="Resting Heart Rate", value="resting-hr"),
                                                    dcc.Tab(label="HR Zones", value="hr-zones"),
                                                    dcc.Tab(label="HRV", value="hrv"),
                                                ],
                                            ),
                                            html.Div(id="hr-chart"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Body Battery and Training
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Energy & Training", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            dcc.Tabs(
                                                id="energy-tabs",
                                                value="body-battery",
                                                children=[
                                                    dcc.Tab(label="Body Battery", value="body-battery"),
                                                    dcc.Tab(label="Training Readiness", value="training-readiness"),
                                                    dcc.Tab(label="VO2 Max", value="vo2-max"),
                                                ],
                                            ),
                                            html.Div(id="energy-chart"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Advanced Health Metrics
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Advanced Health Metrics", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            dcc.Tabs(
                                                id="health-tabs",
                                                value="spo2",
                                                children=[
                                                    dcc.Tab(label="SpO2 (Blood Oxygen)", value="spo2"),
                                                    dcc.Tab(label="Personal Records", value="personal-records"),
                                                ],
                                            ),
                                            html.Div(id="health-chart"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                        ],
                        width=12,
                    )
                ]
            )
        ],
        fluid=True,
    )


def register_callbacks(app):
    """Register callbacks for statistics page."""

    @app.callback(Output("stats-cards-container", "children"), Input("stats-cards-container", "id"))
    def update_stats_cards(_):
        """Update statistics cards with real data."""
        try:
            stats = get_activity_statistics()

            # Check if statistics failed to load
            warning_alert = None
            if stats.get("stats_failed"):
                warning_alert = dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Warning: Statistics may be incomplete due to a data loading issue.",
                    ],
                    color="warning",
                    className="mb-3",
                )

            stats_row = dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(str(stats["total_activities"]), className="text-primary mb-1"),
                                            html.P("Total Activities", className="mb-0 text-muted"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                f"{stats['total_distance_km']:.1f} km", className="text-success mb-1"
                                            ),
                                            html.P("Total Distance", className="mb-0 text-muted"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(f"{stats['total_time_hours']:.1f}h", className="text-info mb-1"),
                                            html.P("Total Time", className="mb-0 text-muted"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                (
                                                    f"{int(stats['avg_heart_rate'])}"
                                                    if stats["avg_heart_rate"] > 0
                                                    else "N/A"
                                                ),
                                                className="text-warning mb-1",
                                            ),
                                            html.P("Avg Heart Rate", className="mb-0 text-muted"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                ]
            )

            # Return warning alert and stats cards if warning exists, otherwise just stats
            if warning_alert:
                return html.Div([warning_alert, stats_row])
            return stats_row
        except Exception as e:
            logger.error(f"Error updating stats cards: {e}")
            return dbc.Alert("Error loading statistics. Please try refreshing the page.", color="danger")

    @app.callback(Output("activity-trends-chart", "children"), Input("activity-trends-chart", "id"))
    def update_trends_chart(_):
        """Update activity trends chart."""
        try:
            trends = get_activity_trends()

            if not trends["months"]:
                return dbc.Alert(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "No activity data available yet. Import some activities to see trends here.",
                    ],
                    color="info",
                )

            # Create dual-axis chart for activities and distance
            fig = go.Figure()

            # Add activity count bars
            fig.add_trace(
                go.Bar(
                    x=trends["months"],
                    y=trends["activity_counts"],
                    name="Activity Count",
                    yaxis="y",
                    marker_color="lightblue",
                )
            )

            # Add distance line
            fig.add_trace(
                go.Scatter(
                    x=trends["months"],
                    y=trends["distances_km"],
                    mode="lines+markers",
                    name="Distance (km)",
                    yaxis="y2",
                    line=dict(color="red", width=2),
                )
            )

            # Update layout for dual axes
            fig.update_layout(
                title="Activity Trends Over Time",
                xaxis=dict(title="Month"),
                yaxis=dict(title="Number of Activities", side="left"),
                yaxis2=dict(title="Distance (km)", overlaying="y", side="right"),
                height=400,
                showlegend=True,
                hovermode="x unified",
            )

            return dcc.Graph(figure=fig)

        except Exception as e:
            logger.error(f"Error updating trends chart: {e}")
            return dbc.Alert("Error loading trends data. Please try refreshing the page.", color="danger")

    @app.callback(Output("wellness-stats-container", "children"), Input("wellness-stats-container", "id"))
    def update_wellness_stats(_):
        """Update wellness statistics cards."""
        try:
            stats = get_wellness_statistics()

            if stats.get("stats_failed"):
                return dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Wellness data not available. Please login to Garmin and sync your data.",
                    ],
                    color="info",
                    className="mb-3",
                )

            # First row - Core wellness metrics
            core_stats_row = dbc.Row(
                [
                    # Sleep stats
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                str(stats["sleep"]["avg_sleep_score"]), className="text-primary mb-1"
                                            ),
                                            html.P("Avg Sleep Score", className="mb-0 text-muted"),
                                            html.Small(
                                                f"{stats['sleep']['avg_sleep_hours']}h avg", className="text-muted"
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                    # Stress stats
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                str(stats["stress"]["avg_stress_level"]), className="text-warning mb-1"
                                            ),
                                            html.P("Avg Stress Level", className="mb-0 text-muted"),
                                            html.Small(
                                                f"{stats['stress']['total_records']} days", className="text-muted"
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                    # Steps stats
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                f"{stats['steps']['avg_daily_steps']:,}", className="text-success mb-1"
                                            ),
                                            html.P("Avg Daily Steps", className="mb-0 text-muted"),
                                            html.Small(
                                                f"{stats['steps']['total_walking_distance_km']} km total",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                    # Intensity stats
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                f"{stats['intensity']['avg_vigorous_minutes']}",
                                                className="text-danger mb-1",
                                            ),
                                            html.P("Avg Vigorous Min", className="mb-0 text-muted"),
                                            html.Small(
                                                f"{stats['intensity']['avg_moderate_minutes']} moderate",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                ]
            )

            # Second row - Advanced wellness metrics 
            advanced_stats_row = dbc.Row(
                [
                    # Heart Rate stats
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                f"{int(stats['heart_rate']['avg_resting_hr'])}" 
                                                if stats['heart_rate']['avg_resting_hr'] > 0 else "N/A",
                                                className="text-info mb-1"
                                            ),
                                            html.P("Avg Resting HR", className="mb-0 text-muted"),
                                            html.Small(
                                                f"{stats['heart_rate']['total_records']} days",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                    # Body Battery stats
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                f"{int(stats['body_battery']['avg_body_battery'])}"
                                                if stats['body_battery']['avg_body_battery'] > 0 else "N/A",
                                                className="text-success mb-1"
                                            ),
                                            html.P("Avg Body Battery", className="mb-0 text-muted"),
                                            html.Small(
                                                f"{stats['body_battery']['total_records']} days",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                    # Training Readiness stats
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                f"{int(stats['training_readiness']['avg_score'])}"
                                                if stats['training_readiness']['avg_score'] > 0 else "N/A",
                                                className="text-primary mb-1"
                                            ),
                                            html.P("Training Readiness", className="mb-0 text-muted"),
                                            html.Small(
                                                f"{stats['training_readiness']['total_records']} days",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                    # VO2 Max stats
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                f"{stats['max_metrics']['avg_vo2_max']}"
                                                if stats['max_metrics']['avg_vo2_max'] > 0 else "N/A",
                                                className="text-danger mb-1"
                                            ),
                                            html.P("Avg VO2 Max", className="mb-0 text-muted"),
                                            html.Small(
                                                f"{stats['personal_records']['total_records']} PRs",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        md=3,
                        className="mb-3",
                    ),
                ]
            )

            return html.Div([core_stats_row, advanced_stats_row])

        except Exception as e:
            logger.error(f"Error updating wellness stats: {e}")
            return dbc.Alert("Error loading wellness statistics.", color="danger")

    @app.callback(Output("sleep-chart", "children"), Input("sleep-tabs", "value"))
    def update_sleep_chart(active_tab):
        """Update sleep visualization based on selected tab."""
        try:
            sleep_df = get_sleep_data(days=90)

            if sleep_df.empty:
                return dbc.Alert(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "No sleep data available. Please sync your Garmin data to see sleep analysis.",
                    ],
                    color="info",
                )

            fig = go.Figure()

            if active_tab == "sleep-quality":
                # Sleep quality line chart
                fig.add_trace(
                    go.Scatter(
                        x=sleep_df.index,
                        y=sleep_df["sleep_score"],
                        mode="lines+markers",
                        name="Sleep Score",
                        line=dict(color="blue", width=2),
                        hovertemplate="<b>%{x}</b><br>Sleep Score: %{y}<extra></extra>",
                    )
                )

                fig.update_layout(
                    title="Daily Sleep Quality Score (0-100)",
                    xaxis_title="Date",
                    yaxis_title="Sleep Score",
                    height=400,
                    hovermode="x unified",
                )

            elif active_tab == "sleep-stages":
                # Sleep stages stacked bar chart
                fig.add_trace(
                    go.Bar(
                        x=sleep_df.index,
                        y=sleep_df["deep_sleep_hours"],
                        name="Deep Sleep",
                        marker_color="darkblue",
                    )
                )
                fig.add_trace(
                    go.Bar(
                        x=sleep_df.index,
                        y=sleep_df["light_sleep_hours"],
                        name="Light Sleep",
                        marker_color="lightblue",
                    )
                )
                fig.add_trace(
                    go.Bar(
                        x=sleep_df.index,
                        y=sleep_df["rem_sleep_hours"],
                        name="REM Sleep",
                        marker_color="purple",
                    )
                )
                fig.add_trace(
                    go.Bar(
                        x=sleep_df.index,
                        y=sleep_df["awake_hours"],
                        name="Awake",
                        marker_color="red",
                    )
                )

                fig.update_layout(
                    title="Daily Sleep Stages",
                    xaxis_title="Date",
                    yaxis_title="Hours",
                    height=400,
                    barmode="stack",
                    hovermode="x unified",
                )

            return dcc.Graph(figure=fig)

        except Exception as e:
            logger.error(f"Error updating sleep chart: {e}")
            return dbc.Alert("Error loading sleep data.", color="danger")

    @app.callback(Output("stress-chart", "children"), Input("stress-chart", "id"))
    def update_stress_chart(_):
        """Update stress visualization."""
        try:
            stress_df = get_stress_data(days=90)

            if stress_df.empty:
                return dbc.Alert(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "No stress data available. Please sync your Garmin data to see stress analysis.",
                    ],
                    color="info",
                )

            fig = go.Figure()

            # Daily stress levels as scatter plot
            fig.add_trace(
                go.Scatter(
                    x=stress_df.index,
                    y=stress_df["avg_stress_level"],
                    mode="markers",
                    name="Daily Stress Level",
                    marker=dict(color="lightcoral", size=6),
                    hovertemplate="<b>%{x}</b><br>Stress Level: %{y}<extra></extra>",
                )
            )

            # 28-day rolling average
            fig.add_trace(
                go.Scatter(
                    x=stress_df.index,
                    y=stress_df["rolling_avg_28d"],
                    mode="lines",
                    name="28-day Rolling Average",
                    line=dict(color="red", width=2),
                    hovertemplate="<b>%{x}</b><br>Rolling Average: %{y:.1f}<extra></extra>",
                )
            )

            fig.update_layout(
                title="Daily Stress Levels with 28-Day Trend",
                xaxis_title="Date",
                yaxis_title="Stress Level (0-100)",
                height=400,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )

            return dcc.Graph(figure=fig)

        except Exception as e:
            logger.error(f"Error updating stress chart: {e}")
            return dbc.Alert("Error loading stress data.", color="danger")

    @app.callback(Output("activity-chart", "children"), Input("activity-tabs", "value"))
    def update_activity_chart(active_tab):
        """Update activity visualization based on selected tab."""
        try:
            if active_tab == "steps":
                steps_df = get_steps_data(days=90)

                if steps_df.empty:
                    return dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "No steps data available. Please sync your Garmin data to see activity analysis.",
                        ],
                        color="info",
                    )

                fig = go.Figure()

                # Daily steps bar chart
                fig.add_trace(
                    go.Bar(
                        x=steps_df.index,
                        y=steps_df["total_steps"],
                        name="Daily Steps",
                        marker_color="lightgreen",
                        hovertemplate="<b>%{x}</b><br>Steps: %{y:,}<extra></extra>",
                    )
                )

                # Step goal line (if available)
                if "step_goal" in steps_df.columns and steps_df["step_goal"].notna().any():
                    fig.add_trace(
                        go.Scatter(
                            x=steps_df.index,
                            y=steps_df["step_goal"],
                            mode="lines",
                            name="Step Goal",
                            line=dict(color="darkgreen", width=2, dash="dash"),
                            hovertemplate="<b>%{x}</b><br>Goal: %{y:,}<extra></extra>",
                        )
                    )

                fig.update_layout(
                    title="Daily Steps vs Goal",
                    xaxis_title="Date",
                    yaxis_title="Steps",
                    height=400,
                    hovermode="x unified",
                )

            elif active_tab == "intensity":
                intensity_df = get_intensity_data(days=90)

                if intensity_df.empty:
                    return dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "No intensity data available. Please sync your Garmin data to see intensity analysis.",
                        ],
                        color="info",
                    )

                fig = go.Figure()

                # Moderate intensity minutes
                fig.add_trace(
                    go.Bar(
                        x=intensity_df.index,
                        y=intensity_df["moderate_minutes"],
                        name="Moderate Minutes",
                        marker_color="orange",
                    )
                )

                # Vigorous intensity minutes (stacked)
                fig.add_trace(
                    go.Bar(
                        x=intensity_df.index,
                        y=intensity_df["vigorous_minutes"],
                        name="Vigorous Minutes",
                        marker_color="red",
                    )
                )

                fig.update_layout(
                    title="Daily Intensity Minutes (Moderate vs Vigorous)",
                    xaxis_title="Date",
                    yaxis_title="Minutes",
                    height=400,
                    barmode="stack",
                    hovermode="x unified",
                )

            return dcc.Graph(figure=fig)

        except Exception as e:
            logger.error(f"Error updating activity chart: {e}")
            return dbc.Alert("Error loading activity data.", color="danger")

    @app.callback(Output("hr-chart", "children"), Input("hr-tabs", "value"))
    def update_hr_chart(active_tab):
        """Update heart rate visualization based on selected tab."""
        try:
            hr_df = get_heart_rate_data(days=90)

            if hr_df.empty:
                return dbc.Alert(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "No heart rate data available. Please sync your Garmin data to see heart rate analysis.",
                    ],
                    color="info",
                )

            fig = go.Figure()

            if active_tab == "resting-hr":
                # Resting heart rate trend
                fig.add_trace(
                    go.Scatter(
                        x=hr_df.index,
                        y=hr_df["resting_hr"],
                        mode="lines+markers",
                        name="Resting HR",
                        line=dict(color="red", width=2),
                        hovertemplate="<b>%{x}</b><br>Resting HR: %{y} bpm<extra></extra>",
                    )
                )
                fig.update_layout(
                    title="Daily Resting Heart Rate Trend",
                    yaxis_title="Heart Rate (bpm)",
                    height=400,
                    hovermode="x unified",
                )

            elif active_tab == "hr-zones":
                # HR zones stacked bar chart
                fig.add_trace(go.Bar(x=hr_df.index, y=hr_df["hr_zone_1_time"], name="Zone 1", marker_color="lightblue"))
                fig.add_trace(go.Bar(x=hr_df.index, y=hr_df["hr_zone_2_time"], name="Zone 2", marker_color="green"))
                fig.add_trace(go.Bar(x=hr_df.index, y=hr_df["hr_zone_3_time"], name="Zone 3", marker_color="orange"))
                fig.add_trace(go.Bar(x=hr_df.index, y=hr_df["hr_zone_4_time"], name="Zone 4", marker_color="red"))
                fig.add_trace(go.Bar(x=hr_df.index, y=hr_df["hr_zone_5_time"], name="Zone 5", marker_color="darkred"))
                fig.update_layout(
                    title="Daily Heart Rate Zone Distribution",
                    yaxis_title="Time (minutes)",
                    height=400,
                    barmode="stack",
                    hovermode="x unified",
                )

            elif active_tab == "hrv":
                # HRV score trend
                fig.add_trace(
                    go.Scatter(
                        x=hr_df.index,
                        y=hr_df["hrv_score"],
                        mode="lines+markers",
                        name="HRV Score",
                        line=dict(color="purple", width=2),
                        hovertemplate="<b>%{x}</b><br>HRV Score: %{y}<extra></extra>",
                    )
                )
                fig.update_layout(
                    title="Heart Rate Variability (HRV) Score",
                    yaxis_title="HRV Score",
                    height=400,
                    hovermode="x unified",
                )

            return dcc.Graph(figure=fig)

        except Exception as e:
            logger.error(f"Error updating heart rate chart: {e}")
            return dbc.Alert("Error loading heart rate data.", color="danger")

    @app.callback(Output("energy-chart", "children"), Input("energy-tabs", "value"))
    def update_energy_chart(active_tab):
        """Update energy and training visualization based on selected tab."""
        try:
            if active_tab == "body-battery":
                bb_df = get_body_battery_data(days=90)
                if bb_df.empty:
                    return dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "No Body Battery data available. Please sync your Garmin data.",
                        ],
                        color="info",
                    )

                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=bb_df.index,
                        y=bb_df["body_battery_score"],
                        mode="markers",
                        name="Daily Score",
                        marker=dict(color="lightgreen", size=6),
                        hovertemplate="<b>%{x}</b><br>Body Battery: %{y}<extra></extra>",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=bb_df.index,
                        y=bb_df["bb_7d_avg"],
                        mode="lines",
                        name="7-day Average",
                        line=dict(color="green", width=2),
                        hovertemplate="<b>%{x}</b><br>7-day Average: %{y:.1f}<extra></extra>",
                    )
                )
                fig.update_layout(
                    title="Body Battery Energy Levels",
                    yaxis_title="Body Battery Score (0-100)",
                    height=400,
                    hovermode="x unified",
                )

            elif active_tab == "training-readiness":
                tr_df = get_training_readiness_data(days=90)
                if tr_df.empty:
                    return dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "No Training Readiness data available. Please sync your Garmin data.",
                        ],
                        color="info",
                    )

                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=tr_df.index,
                        y=tr_df["training_readiness_score"],
                        mode="lines+markers",
                        name="Training Readiness",
                        line=dict(color="blue", width=2),
                        hovertemplate="<b>%{x}</b><br>Readiness: %{y}<extra></extra>",
                    )
                )
                fig.update_layout(
                    title="Training Readiness Score",
                    yaxis_title="Readiness Score (0-100)",
                    height=400,
                    hovermode="x unified",
                )

            elif active_tab == "vo2-max":
                vo2_df = get_max_metrics_data(days=365)
                if vo2_df.empty:
                    return dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "No VO2 Max data available. Please sync your Garmin data.",
                        ],
                        color="info",
                    )

                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=vo2_df.index,
                        y=vo2_df["vo2_max_value"],
                        mode="lines+markers",
                        name="VO2 Max",
                        line=dict(color="red", width=2),
                        hovertemplate="<b>%{x}</b><br>VO2 Max: %{y}<extra></extra>",
                    )
                )
                fig.update_layout(
                    title="VO2 Max Fitness Trend",
                    yaxis_title="VO2 Max (ml/kg/min)",
                    height=400,
                    hovermode="x unified",
                )

            return dcc.Graph(figure=fig)

        except Exception as e:
            logger.error(f"Error updating energy chart: {e}")
            return dbc.Alert("Error loading energy/training data.", color="danger")

    @app.callback(Output("health-chart", "children"), Input("health-tabs", "value"))
    def update_health_chart(active_tab):
        """Update advanced health metrics visualization based on selected tab."""
        try:
            if active_tab == "spo2":
                spo2_df = get_spo2_data(days=90)
                if spo2_df.empty:
                    return dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "No SpO2 data available. Please sync your Garmin data.",
                        ],
                        color="info",
                    )

                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=spo2_df.index,
                        y=spo2_df["avg_spo2_percentage"],
                        mode="lines+markers",
                        name="Average SpO2",
                        line=dict(color="blue", width=2),
                        hovertemplate="<b>%{x}</b><br>SpO2: %{y}%<extra></extra>",
                    )
                )
                fig.update_layout(
                    title="Blood Oxygen Saturation (SpO2)",
                    yaxis_title="SpO2 (%)",
                    height=400,
                    hovermode="x unified",
                )
                return dcc.Graph(figure=fig)

            elif active_tab == "personal-records":
                pr_data = get_personal_records_data()
                if not pr_data:
                    return dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "No personal records available. Sync your activities to see achievements.",
                        ],
                        color="info",
                    )

                # Create a table of personal records
                pr_rows = []
                for record in pr_data[:10]:  # Show top 10 records
                    pr_rows.append(
                        html.Tr([
                            html.Td(record["activity_type"] or "N/A"),
                            html.Td(record["record_type"] or "N/A"),
                            html.Td(f"{record['record_value']} {record['record_unit']}" if record["record_value"] else "N/A"),
                            html.Td(record["achieved_date"].strftime("%Y-%m-%d") if record["achieved_date"] else "N/A"),
                        ])
                    )

                return html.Div([
                    html.H5("Recent Personal Records"),
                    dbc.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("Sport"),
                                html.Th("Record Type"),
                                html.Th("Value"),
                                html.Th("Date Achieved"),
                            ])
                        ]),
                        html.Tbody(pr_rows)
                    ], bordered=True, hover=True, responsive=True, striped=True)
                ])

        except Exception as e:
            logger.error(f"Error updating health chart: {e}")
            return dbc.Alert("Error loading health data.", color="danger")
