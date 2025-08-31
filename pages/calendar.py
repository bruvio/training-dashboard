"""
Calendar page - Main activity list and calendar view.
"""

from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc

from app.data.db import session_scope
from app.data.models import Activity

# This page uses manual routing - no registration needed


def layout():
    """
    Main layout for the calendar/activity list page.
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
            # Quick actions
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
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                [html.I(className="fas fa-upload me-2"), "Import FIT Files"],
                                                className="mb-3",
                                            ),
                                            html.P(
                                                "Upload FIT files directly from your Garmin device to analyze your workouts.",
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-file-upload me-2"), "Import Files"],
                                                color="secondary",
                                                size="lg",
                                                className="w-100",
                                                disabled=True,
                                                title="Use CLI: python -m cli.gd_import [directory]",
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=4,
                    ),
                ],
                className="mb-5",
            ),
            # Activity overview
            dbc.Row([dbc.Col([html.Div(id="activity-summary-cards")], width=12)], className="mb-4"),
            # Activity table
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
                                                    dbc.Col([html.H5("Your Activities", className="mb-0")], width=6),
                                                    dbc.Col(
                                                        [
                                                            html.Div(
                                                                [
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(className="fas fa-sync me-2"),
                                                                            "Refresh",
                                                                        ],
                                                                        id="refresh-activities",
                                                                        color="outline-primary",
                                                                        size="sm",
                                                                        className="float-end",
                                                                    )
                                                                ]
                                                            )
                                                        ],
                                                        width=6,
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody([html.Div(id="activity-table-container")]),
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


@callback(Output("activity-summary-cards", "children"), Input("url", "pathname"))
def update_activity_summary(pathname):
    """Load and display activity summary statistics."""
    try:
        with session_scope() as session:
            total_activities = session.query(Activity).count()

            if total_activities == 0:
                return dbc.Alert(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "No activities found. Get started by connecting your Garmin account or importing FIT files.",
                    ],
                    color="info",
                    className="text-center",
                )

            # Calculate some basic stats
            total_distance = session.query(Activity.distance_m).filter(Activity.distance_m.isnot(None)).scalar() or 0
            total_time = (
                session.query(Activity.elapsed_time_s).filter(Activity.elapsed_time_s.isnot(None)).scalar() or 0
            )

            return dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H3(str(total_activities), className="text-primary mb-1"),
                                            html.P("Total Activities", className="mb-0 text-muted"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H3(f"{total_distance/1000:.0f} km", className="text-success mb-1"),
                                            html.P("Total Distance", className="mb-0 text-muted"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H3(f"{total_time//3600:.0f}h", className="text-info mb-1"),
                                            html.P("Total Time", className="mb-0 text-muted"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=4,
                    ),
                ]
            )

    except Exception as e:
        return dbc.Alert(f"Error loading summary: {str(e)}", color="warning")


@callback(
    Output("activity-table-container", "children"), [Input("url", "pathname"), Input("refresh-activities", "n_clicks")]
)
def update_activity_table(pathname, n_clicks):
    """Load and display activities in a table format."""
    try:
        with session_scope() as session:
            activities = session.query(Activity).all()

            if not activities:
                return dbc.Alert(
                    [
                        html.H4("No Activities Found", className="alert-heading"),
                        html.P("Import some FIT files to see your activities here."),
                        html.Hr(),
                        html.P("Use the import command: python -m cli.gd_import [data_directory]"),
                    ],
                    color="info",
                )

            # Create activity cards
            activity_cards = []
            for activity in activities:
                duration_str = f"{activity.elapsed_time_s // 60:.0f} min" if activity.elapsed_time_s else "N/A"
                distance_str = f"{activity.distance_m/1000:.2f} km" if activity.distance_m else "N/A"

                card = dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H5(f"Activity {activity.id}", className="card-title"),
                                html.P(
                                    [
                                        html.Strong("Sport: "),
                                        activity.sport or "Unknown",
                                        html.Br(),
                                        html.Strong("Duration: "),
                                        duration_str,
                                        html.Br(),
                                        html.Strong("Distance: "),
                                        distance_str,
                                        html.Br(),
                                        html.Strong("Date: "),
                                        (
                                            activity.start_time_utc.strftime("%Y-%m-%d %H:%M")
                                            if activity.start_time_utc
                                            else "Unknown"
                                        ),
                                    ]
                                ),
                                dbc.Button("View Details", href=f"/activity/{activity.id}", color="primary", size="sm"),
                            ]
                        )
                    ],
                    className="mb-3",
                )
                activity_cards.append(card)

            return html.Div(activity_cards)

    except Exception as e:
        return dbc.Alert(f"Error loading activities: {str(e)}", color="danger")
