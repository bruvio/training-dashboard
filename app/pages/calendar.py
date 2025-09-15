"""
Calendar page - Main activity list and calendar view.
"""

from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc

# This page uses manual routing - no registration needed


def layout():
    """
    Enhanced landing page with database summary and navigation actions.
    """
    return dbc.Container(
        [
            # Header with welcome message
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1([html.I(className="fas fa-running me-3"), "Garmin Dashboard"], className="mb-3"),
                            html.P(
                                "Your personal fitness data visualization and analysis platform.",
                                className="text-muted mb-4 fs-5",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Database summary section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [html.I(className="fas fa-database me-2"), "Database Summary"],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody([html.Div(id="database-summary-cards")]),
                                ],
                                className="mb-4",
                            )
                        ],
                        width=12,
                    )
                ]
            ),
            # Quick actions - Enhanced with requested buttons
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                [html.I(className="fas fa-download me-2"), "Connect to Garmin"],
                                                className="mb-3",
                                            ),
                                            html.P(
                                                "Login to your Garmin Connect account and sync your activities automatically.",
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-sign-in-alt me-2"), "Connect Now"],
                                                href="/garmin",
                                                color="primary",
                                                size="lg",
                                                className="w-100",
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=6,
                        md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                [html.I(className="fas fa-chart-line me-2"), "Statistics"],
                                                className="mb-3",
                                            ),
                                            html.P(
                                                "View comprehensive statistics, trends, and analytics of your fitness data.",
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-chart-bar me-2"), "View Stats"],
                                                href="/stats",
                                                color="info",
                                                size="lg",
                                                className="w-100",
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=6,
                        md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                [html.I(className="fas fa-upload me-2"), "Import Local FIT Files"],
                                                className="mb-3",
                                            ),
                                            html.P(
                                                "Upload FIT files directly from your Garmin device to analyze your workouts.",
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-file-upload me-2"), "Import Files"],
                                                href="/upload",
                                                color="secondary",
                                                size="lg",
                                                className="w-100",
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=6,
                        md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                [html.I(className="fas fa-cog me-2"), "Settings"],
                                                className="mb-3",
                                            ),
                                            html.P(
                                                "Configure application preferences, data sources, and display options.",
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-cogs me-2"), "Settings"],
                                                href="/settings",
                                                color="dark",
                                                size="lg",
                                                className="w-100",
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=6,
                        md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                [html.I(className="fas fa-sync-alt me-2"), "Sync Wellness"],
                                                className="mb-3",
                                            ),
                                            html.P(
                                                "Sync your latest wellness data including sleep, stress, and body battery metrics.",
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-download me-2"), "Sync Now"],
                                                href="/sync",
                                                color="success",
                                                size="lg",
                                                className="w-100",
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=6,
                        md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                [html.I(className="fas fa-list me-2"), "Activities"],
                                                className="mb-3",
                                            ),
                                            html.P(
                                                "Browse and analyze all activities in your database with detailed metrics.",
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-running me-2"), "View Activities"],
                                                href="/activities",
                                                color="warning",
                                                size="lg",
                                                className="w-100",
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=6,
                        md=4,
                        className="mb-3",
                    ),
                ],
                className="mb-5",
            ),
        ],
        fluid=True,
    )


# Database summary callback
@callback(
    Output("database-summary-cards", "children"),
    Input("url", "pathname"),
)
def update_database_summary(pathname):
    """Load and display database summary statistics."""
    try:
        from app.data.web_queries import get_activity_statistics, get_wellness_statistics

        # Get activity statistics (no date filter for overall summary)
        activity_stats = get_activity_statistics()

        # Get wellness statistics
        wellness_stats = get_wellness_statistics()

        return dbc.Row(
            [
                # Activity Statistics
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4(
                                            [html.I(className="fas fa-running me-2"), "Activities"],
                                            className="text-primary mb-3",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            str(activity_stats["total_activities"]),
                                                            className="text-success mb-1",
                                                        ),
                                                        html.P("Total Activities", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            f"{activity_stats['total_distance_km']:.1f} km",
                                                            className="text-info mb-1",
                                                        ),
                                                        html.P("Total Distance", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                            ],
                                            className="mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            f"{activity_stats['total_time_hours']:.1f}h",
                                                            className="text-warning mb-1",
                                                        ),
                                                        html.P("Total Time", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            (
                                                                f"{activity_stats['avg_heart_rate']:.0f} bpm"
                                                                if activity_stats["avg_heart_rate"] > 0
                                                                else "N/A"
                                                            ),
                                                            className="text-danger mb-1",
                                                        ),
                                                        html.P("Avg Heart Rate", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                            ]
                                        ),
                                    ]
                                )
                            ]
                        )
                    ],
                    width=6,
                    lg=4,
                ),
                # Wellness Statistics
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4(
                                            [html.I(className="fas fa-heart me-2"), "Wellness"],
                                            className="text-danger mb-3",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            str(wellness_stats["sleep"]["total_records"]),
                                                            className="text-primary mb-1",
                                                        ),
                                                        html.P("Sleep Records", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            (
                                                                f"{wellness_stats['sleep']['avg_sleep_hours']:.1f}h"
                                                                if wellness_stats["sleep"]["avg_sleep_hours"] > 0
                                                                else "N/A"
                                                            ),
                                                            className="text-info mb-1",
                                                        ),
                                                        html.P("Avg Sleep", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                            ],
                                            className="mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            str(wellness_stats["stress"]["total_records"]),
                                                            className="text-warning mb-1",
                                                        ),
                                                        html.P("Stress Records", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            str(wellness_stats["steps"]["total_records"]),
                                                            className="text-success mb-1",
                                                        ),
                                                        html.P("Steps Records", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                            ]
                                        ),
                                    ]
                                )
                            ]
                        )
                    ],
                    width=6,
                    lg=4,
                ),
                # Additional Metrics
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4(
                                            [html.I(className="fas fa-chart-bar me-2"), "Metrics"],
                                            className="text-success mb-3",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            str(wellness_stats["body_battery"]["total_records"]),
                                                            className="text-primary mb-1",
                                                        ),
                                                        html.P("Body Battery", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            str(wellness_stats["heart_rate"]["total_records"]),
                                                            className="text-danger mb-1",
                                                        ),
                                                        html.P("HR Records", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                            ],
                                            className="mb-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            str(wellness_stats["personal_records"]["total_records"]),
                                                            className="text-warning mb-1",
                                                        ),
                                                        html.P("Personal Records", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.H5(
                                                            (
                                                                f"{wellness_stats['max_metrics']['avg_vo2_max']:.1f}"
                                                                if wellness_stats["max_metrics"]["avg_vo2_max"] > 0
                                                                else "N/A"
                                                            ),
                                                            className="text-info mb-1",
                                                        ),
                                                        html.P("Avg VO2 Max", className="mb-0 small text-muted"),
                                                    ],
                                                    width=6,
                                                ),
                                            ]
                                        ),
                                    ]
                                )
                            ]
                        )
                    ],
                    width=12,
                    lg=4,
                ),
            ]
        )

    except Exception as e:
        return dbc.Alert(f"Error loading database summary: {str(e)}", color="warning")
