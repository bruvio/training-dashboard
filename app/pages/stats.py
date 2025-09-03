"""
Statistics page for activity analytics and insights.
"""

from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from app.data.web_queries import get_activity_statistics, get_activity_trends
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
                                                f"{int(stats['avg_heart_rate'])}"
                                                if stats["avg_heart_rate"] > 0
                                                else "N/A",
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
