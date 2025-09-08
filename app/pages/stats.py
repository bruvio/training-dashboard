"""
Statistics page for activity analytics and insights with date filtering.
"""

from datetime import date, timedelta

from dash import Input, Output, callback, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

from app.data.web_queries import (
    get_activity_statistics,
    get_activity_trends,
    get_body_battery_data,
    get_heart_rate_data,
    get_max_metrics_data,
    get_personal_records_data,
    get_sleep_data,
    get_steps_data,
    get_stress_data,
    get_training_readiness_data,
    get_wellness_statistics,
)
from app.utils import get_logger

logger = get_logger(__name__)


def layout():
    """Statistics page layout with date filtering."""
    return dbc.Container(
        [
            # Hidden trigger for initial data load
            dcc.Interval(id="stats-initial-load", interval=1000, n_intervals=0, max_intervals=1),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1([html.I(className="fas fa-chart-line me-3"), "Statistics"], className="mb-4"),
                            # Date Range Filter Card
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [html.I(className="fas fa-calendar-alt me-2"), "Date Range Filter"],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Select Date Range", className="form-label fw-bold"
                                                            ),
                                                            dcc.DatePickerRange(
                                                                id="stats-date-range",
                                                                start_date=date.today() - timedelta(days=90),
                                                                end_date=date.today(),
                                                                display_format="YYYY-MM-DD",
                                                                first_day_of_week=1,  # Monday
                                                                style={"width": "100%"},
                                                            ),
                                                        ],
                                                        md=8,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label("Quick Select", className="form-label fw-bold"),
                                                            dcc.Dropdown(
                                                                id="stats-quick-select",
                                                                options=[
                                                                    {"label": "Last 7 days", "value": 7},
                                                                    {"label": "Last 30 days", "value": 30},
                                                                    {"label": "Last 90 days", "value": 90},
                                                                    {"label": "Last 6 months", "value": 180},
                                                                    {"label": "Last year", "value": 365},
                                                                ],
                                                                value=90,
                                                                placeholder="Quick select range",
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                ]
                                            ),
                                            html.Hr(),
                                            html.Div(id="date-range-summary", className="text-center"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Statistics cards - now dynamic with date filtering
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
                            # Real-time wellness charts with date filtering
                            html.Div(id="real-time-wellness-charts"),
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
                                                ],
                                            ),
                                            html.Div(id="activity-chart"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Advanced Wellness Header
                            html.H2(
                                [html.I(className="fas fa-heartbeat me-3"), "Advanced Wellness"], className="mb-4 mt-5"
                            ),
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
                                                    dcc.Tab(label="HRV", value="hrv"),
                                                    dcc.Tab(label="VO2 Max", value="vo2max"),
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
                                                ],
                                            ),
                                            html.Div(id="energy-chart"),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Personal Records
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Personal Records", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            dcc.Tabs(
                                                id="health-tabs",
                                                value="personal-records",
                                                children=[
                                                    # dcc.Tab(label="SpO2 (Blood Oxygen)", value="spo2"),
                                                    dcc.Tab(label="Personal Records", value="personal-records")
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
            ),
        ],
        fluid=True,
    )


# Date Range Callbacks (using @callback decorator for automatic registration)
@callback(
    [Output("stats-date-range", "start_date"), Output("stats-date-range", "end_date")],
    Input("stats-quick-select", "value"),
)
def update_date_range_from_quick_select(days):
    """Update date range based on quick select dropdown."""
    if days is None:
        return date.today() - timedelta(days=90), date.today()

    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


@callback(
    Output("date-range-summary", "children"),
    [Input("stats-date-range", "start_date"), Input("stats-date-range", "end_date")],
)
def update_date_range_summary(start_date, end_date):
    """Update the date range summary display."""
    if not start_date or not end_date:
        return ""

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        days = (end - start).days + 1

        return dbc.Alert(
            [
                html.Strong("📊 Showing data for: "),
                f"{start.strftime('%B %d, %Y')} to {end.strftime('%B %d, %Y')} ",
                html.Span(f"({days} days)", className="text-muted"),
            ],
            color="info",
            className="mb-0 py-2",
        )

    except Exception:
        return dbc.Alert("Invalid date range", color="warning", className="mb-0 py-2")


def register_callbacks(app):
    """Register callbacks for statistics page."""

    @app.callback(
        Output("stats-cards-container", "children"),
        [Input("stats-date-range", "start_date"), Input("stats-date-range", "end_date")],
    )
    def update_stats_cards(start_date, end_date):
        """Update statistics cards with real data filtered by date range."""
        try:
            # Convert string dates to date objects
            start_date_obj = None
            end_date_obj = None

            if start_date:
                start_date_obj = date.fromisoformat(start_date)
            if end_date:
                end_date_obj = date.fromisoformat(end_date)

            stats = get_activity_statistics(start_date_obj, end_date_obj)

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
                                                (
                                                    f"{int(stats['heart_rate']['avg_resting_hr'])}"
                                                    if stats["heart_rate"]["avg_resting_hr"] > 0
                                                    else "N/A"
                                                ),
                                                className="text-info mb-1",
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
                                                (
                                                    f"{int(stats['body_battery']['avg_body_battery'])}"
                                                    if stats["body_battery"]["avg_body_battery"] > 0
                                                    else "N/A"
                                                ),
                                                className="text-success mb-1",
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
                                                (
                                                    f"{int(stats['training_readiness']['avg_score'])}"
                                                    if stats["training_readiness"]["avg_score"] > 0
                                                    else "N/A"
                                                ),
                                                className="text-primary mb-1",
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
                ]
            )

            return html.Div([core_stats_row, advanced_stats_row])

        except Exception as e:
            logger.error(f"Error updating wellness stats: {e}")
            return dbc.Alert("Error loading wellness statistics.", color="danger")

    @app.callback(
        Output("sleep-chart", "children"),
        [
            Input("sleep-tabs", "value"),
            Input("stats-initial-load", "n_intervals"),
            Input("stats-date-range", "start_date"),
            Input("stats-date-range", "end_date"),
        ],
    )
    def update_sleep_chart(active_tab, n_intervals, start_date, end_date):
        """Update sleep visualization based on selected tab and date range."""
        try:
            # Use date range filter or default to 90 days
            if start_date and end_date:
                start_date_obj = date.fromisoformat(start_date)
                end_date_obj = date.fromisoformat(end_date)
                sleep_df = get_sleep_data(
                    start_date=start_date_obj.strftime("%Y-%m-%d"), end_date=end_date_obj.strftime("%Y-%m-%d")
                )
            else:
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
                if "sleep_score" in sleep_df.columns and sleep_df["sleep_score"].notna().any():
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

                # Sleep efficiency (calculated from sleep stages)
                if "efficiency_percentage" in sleep_df.columns and sleep_df["efficiency_percentage"].notna().any():
                    fig.add_trace(
                        go.Scatter(
                            x=sleep_df.index,
                            y=sleep_df["efficiency_percentage"],
                            mode="lines+markers",
                            name="Sleep Efficiency (%)",
                            line=dict(color="green", width=2),
                            hovertemplate="<b>%{x}</b><br>Efficiency: %{y}%<extra></extra>",
                        )
                    )

                fig.update_layout(
                    title="Sleep Quality & Efficiency",
                    xaxis_title="Date",
                    yaxis_title="Score/Percentage",
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

    @app.callback(
        Output("stress-chart", "children"),
        [
            Input("stats-initial-load", "n_intervals"),
            Input("stats-date-range", "start_date"),
            Input("stats-date-range", "end_date"),
        ],
    )
    def update_stress_chart(n_intervals, start_date, end_date):
        """Update stress visualization based on date range."""
        try:
            # Use date range filter or default to 90 days
            if start_date and end_date:
                start_date_obj = date.fromisoformat(start_date)
                end_date_obj = date.fromisoformat(end_date)
                stress_df = get_stress_data(
                    start_date=start_date_obj.strftime("%Y-%m-%d"), end_date=end_date_obj.strftime("%Y-%m-%d")
                )
            else:
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

    @app.callback(
        Output("activity-chart", "children"),
        [Input("activity-tabs", "value"), Input("stats-initial-load", "n_intervals")],
    )
    def update_activity_chart(active_tab, n_intervals):
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

            return dcc.Graph(figure=fig)

        except Exception as e:
            logger.error(f"Error updating activity chart: {e}")
            return dbc.Alert("Error loading activity data.", color="danger")

    @app.callback(
        Output("hr-chart", "children"),
        [Input("hr-tabs", "value"), Input("stats-date-range", "start_date"), Input("stats-date-range", "end_date")],
    )
    def update_hr_chart(active_tab, start_date, end_date):
        """Update heart rate visualization based on selected tab and date range."""
        try:
            # Use date range filter or default to 30 days
            if start_date and end_date:
                start_date_obj = date.fromisoformat(start_date)
                end_date_obj = date.fromisoformat(end_date)
                hr_df = get_heart_rate_data(
                    start_date=start_date_obj.strftime("%Y-%m-%d"), end_date=end_date_obj.strftime("%Y-%m-%d")
                )
            else:
                hr_df = get_heart_rate_data(days=30)

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
                    yaxis=dict(range=[45, 65]),  # Set reasonable range for resting HR
                    height=400,
                    hovermode="x unified",
                )

            elif active_tab == "hrv":
                # HRV score trend
                if "hrv_score" in hr_df.columns and hr_df["hrv_score"].notna().any():
                    hrv_data = hr_df["hrv_score"].dropna()
                    fig.add_trace(
                        go.Scatter(
                            x=hrv_data.index,
                            y=hrv_data.values,
                            mode="lines+markers",
                            name="HRV Score",
                            line=dict(color="purple", width=2),
                            marker=dict(size=8),
                            hovertemplate="<b>%{x}</b><br>HRV Score: %{y}<extra></extra>",
                        )
                    )

                    # Set appropriate y-axis range for HRV data visibility
                    hrv_min, hrv_max = hrv_data.min(), hrv_data.max()
                    y_margin = max(2, (hrv_max - hrv_min) * 0.1) if hrv_max > hrv_min else 5

                    fig.update_layout(
                        title="Heart Rate Variability (HRV) Score",
                        yaxis_title="HRV Score",
                        yaxis=dict(range=[hrv_min - y_margin, hrv_max + y_margin], autorange=False),
                        height=400,
                        hovermode="x unified",
                    )
                else:
                    return dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "No HRV data available. This metric may not be supported by your Garmin device or requires additional sync.",
                        ],
                        color="info",
                    )

            elif active_tab == "vo2max":
                # VO2 Max fitness trend
                if "vo2max" in hr_df.columns and hr_df["vo2max"].notna().any():
                    vo2_data = hr_df["vo2max"].dropna()
                    fig.add_trace(
                        go.Scatter(
                            x=vo2_data.index,
                            y=vo2_data.values,
                            mode="lines+markers",
                            name="VO2 Max",
                            line=dict(color="green", width=2),
                            marker=dict(size=8),
                            hovertemplate="<b>%{x}</b><br>VO2 Max: %{y} ml/kg/min<extra></extra>",
                        )
                    )
                    fig.update_layout(
                        title="VO2 Max Fitness Level",
                        yaxis_title="VO2 Max (ml/kg/min)",
                        height=400,
                        hovermode="x unified",
                        yaxis=dict(range=[50, 70]),  # Set reasonable range for VO2 Max
                    )
                else:
                    return dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "No VO2 Max data available. Please sync your Garmin data to see VO2 Max measurements.",
                        ],
                        color="info",
                    )

            return dcc.Graph(figure=fig)

        except Exception as e:
            logger.error(f"Error updating heart rate chart: {e}")
            return dbc.Alert("Error loading heart rate data.", color="danger")

    @app.callback(
        Output("energy-chart", "children"),
        [Input("energy-tabs", "value"), Input("stats-date-range", "start_date"), Input("stats-date-range", "end_date")],
    )
    def update_energy_chart(active_tab, start_date, end_date):
        """Update energy and training visualization based on selected tab and date range."""
        try:
            if active_tab == "body-battery":
                # Use date range filter or default to 90 days
                if start_date and end_date:
                    start_date_obj = date.fromisoformat(start_date)
                    end_date_obj = date.fromisoformat(end_date)
                    bb_df = get_body_battery_data(
                        start_date=start_date_obj.strftime("%Y-%m-%d"), end_date=end_date_obj.strftime("%Y-%m-%d")
                    )
                else:
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
                # Use date range filter or default to 90 days
                if start_date and end_date:
                    start_date_obj = date.fromisoformat(start_date)
                    end_date_obj = date.fromisoformat(end_date)
                    tr_df = get_training_readiness_data(
                        start_date=start_date_obj.strftime("%Y-%m-%d"), end_date=end_date_obj.strftime("%Y-%m-%d")
                    )
                else:
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
            # if active_tab == "spo2":
            #     spo2_df = get_spo2_data(days=90)
            #     if spo2_df.empty:
            #         return dbc.Alert(
            #             [
            #                 html.I(className="fas fa-info-circle me-2"),
            #                 "No SpO2 data available. Please sync your Garmin data.",
            #             ],
            #             color="info",
            #         )

            #     fig = go.Figure()
            #     fig.add_trace(
            #         go.Scatter(
            #             x=spo2_df.index,
            #             y=spo2_df["avg_spo2_percentage"],
            #             mode="lines+markers",
            #             name="Average SpO2",
            #             line=dict(color="blue", width=2),
            #             hovertemplate="<b>%{x}</b><br>SpO2: %{y}%<extra></extra>",
            #         )
            #     )
            #     fig.update_layout(
            #         title="Blood Oxygen Saturation (SpO2)",
            #         yaxis_title="SpO2 (%)",
            #         height=400,
            #         hovermode="x unified",
            #     )
            #     return dcc.Graph(figure=fig)

            if active_tab == "personal-records":
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
                        html.Tr(
                            [
                                html.Td(record["activity_type"] or "N/A"),
                                html.Td(record["record_type"] or "N/A"),
                                html.Td(
                                    f"{record['record_value']} {record['record_unit']}"
                                    if record["record_value"]
                                    else "N/A"
                                ),
                                html.Td(str(record["achieved_date"]) if record["achieved_date"] else "N/A"),
                            ]
                        )
                    )

                return html.Div(
                    [
                        html.H5("Recent Personal Records"),
                        dbc.Table(
                            [
                                html.Thead(
                                    [
                                        html.Tr(
                                            [
                                                html.Th("Sport"),
                                                html.Th("Record Type"),
                                                html.Th("Value"),
                                                html.Th("Date Achieved"),
                                            ]
                                        )
                                    ]
                                ),
                                html.Tbody(pr_rows),
                            ],
                            bordered=True,
                            hover=True,
                            responsive=True,
                            striped=True,
                        ),
                    ]
                )

        except Exception as e:
            logger.error(f"Error updating health chart: {e}")
            return dbc.Alert("Error loading health data.", color="danger")


def create_wellness_chart(df, title, y_columns):
    """Create a simple wellness data chart using plotly."""
    if df.empty:
        return dbc.Alert(f"No data available for {title}", color="info", className="text-center")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    fig = go.Figure()
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8"]

    for i, col in enumerate(y_columns):
        if col not in df.columns:
            continue

        data = df[df[col].notna()]
        if data.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=data["date"],
                y=data[col],
                mode="lines+markers",
                name=col.replace("_", " ").title(),
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6),
            )
        )

    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Value", height=400, showlegend=True)

    return dcc.Graph(figure=fig)
