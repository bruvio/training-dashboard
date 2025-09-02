"""
Settings page for Garmin Dashboard.

Provides database management, user preferences, and system information.
"""

from datetime import datetime
import logging

import dash
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc

# Import database utilities
try:
    import sys

    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from data.db import get_db_config, init_database
except ImportError:
    # Fallback for different path structures
    try:
        sys.path.insert(0, "/app/app")
        from app.data.db import get_db_config, init_database
    except ImportError as e:
        logging.error(f"Failed to import database modules: {e}")
        get_db_config = None
        init_database = None

from app.data.preferences import get_preferences
from app.utils import get_logger

logger = get_logger(__name__)


def layout():
    """Render settings page layout."""
    return dbc.Container(
        [
            # Page header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H1(
                                        [html.I(className="fas fa-cog me-3"), "Settings"], className="text-dark mb-0"
                                    ),
                                    html.P("Manage your dashboard settings and database", className="text-muted lead"),
                                ]
                            )
                        ]
                    )
                ],
                className="mb-4",
            ),
            # Alerts container
            html.Div(id="settings-alerts-container"),
            # Display Preferences Section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H4(
                                                [html.I(className="fas fa-paint-brush me-2"), "Display Preferences"],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="display-preferences-container"),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    )
                ],
                className="mb-4",
            ),
            # Database Management Section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H4(
                                                [html.I(className="fas fa-database me-2"), "Database Management"],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Database info container
                                            html.Div(id="database-info-container"),
                                            html.Hr(),
                                            # Database reset section
                                            html.Div(
                                                [
                                                    html.H5(
                                                        [
                                                            html.I(
                                                                className="fas fa-exclamation-triangle me-2 text-warning"
                                                            ),
                                                            "Reset Database",
                                                        ],
                                                        className="text-danger",
                                                    ),
                                                    html.P(
                                                        [
                                                            "This will permanently delete all activities, routes, and samples from your database. ",
                                                            html.Strong(
                                                                "This action cannot be undone.", className="text-danger"
                                                            ),
                                                        ],
                                                        className="text-muted mb-3",
                                                    ),
                                                    # Reset confirmation section
                                                    html.Div(
                                                        [
                                                            dbc.InputGroup(
                                                                [
                                                                    dbc.Input(
                                                                        id="reset-confirmation-input",
                                                                        placeholder="Type 'DELETE' to confirm",
                                                                        value="",
                                                                        type="text",
                                                                    ),
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(className="fas fa-trash me-2"),
                                                                            "Reset Database",
                                                                        ],
                                                                        id="reset-database-btn",
                                                                        color="danger",
                                                                        disabled=True,
                                                                    ),
                                                                ],
                                                                className="mb-3",
                                                            )
                                                        ]
                                                    ),
                                                    # Reset status
                                                    html.Div(id="reset-status-container"),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    )
                ],
                className="mb-4",
            ),
            # System Information Section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H4(
                                                [html.I(className="fas fa-info-circle me-2"), "System Information"],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody([html.Div(id="system-info-container")]),
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


def register_callbacks(app):
    """Register callbacks for settings page."""

    # Display preferences callback
    @app.callback(
        Output("display-preferences-container", "children"),
        Input("display-preferences-container", "id"),
        prevent_initial_call=False,
    )
    def display_preferences_form(_):
        """Display preferences form with current settings."""
        try:
            prefs = get_preferences()
            current_prefs = prefs.get_all()

            return dbc.Form(
                [
                    # Units selection
                    dbc.Row(
                        [
                            dbc.Col([dbc.Label("Units")], width=3),
                            dbc.Col(
                                [
                                    dbc.RadioItems(
                                        id="units-radio",
                                        options=[
                                            {"label": "Metric (km, kg, °C)", "value": "metric"},
                                            {"label": "Imperial (mi, lb, °F)", "value": "imperial"},
                                        ],
                                        value=current_prefs.get("units", "metric"),
                                        inline=True,
                                    )
                                ],
                                width=9,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Chart type selection
                    dbc.Row(
                        [
                            dbc.Col([dbc.Label("Default Chart Type")], width=3),
                            dbc.Col(
                                [
                                    dbc.Select(
                                        id="chart-type-select",
                                        options=[
                                            {"label": "Line Charts", "value": "line"},
                                            {"label": "Bar Charts", "value": "bar"},
                                            {"label": "Scatter Plots", "value": "scatter"},
                                        ],
                                        value=current_prefs.get("default_chart_type", "line"),
                                    )
                                ],
                                width=9,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Activities per page
                    dbc.Row(
                        [
                            dbc.Col([dbc.Label("Activities Per Page")], width=3),
                            dbc.Col(
                                [
                                    dbc.Select(
                                        id="activities-per-page-select",
                                        options=[
                                            {"label": "10", "value": 10},
                                            {"label": "20", "value": 20},
                                            {"label": "50", "value": 50},
                                            {"label": "100", "value": 100},
                                        ],
                                        value=current_prefs.get("activities_per_page", 20),
                                    )
                                ],
                                width=9,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Default sort order
                    dbc.Row(
                        [
                            dbc.Col([dbc.Label("Default Sort Order")], width=3),
                            dbc.Col(
                                [
                                    dbc.Select(
                                        id="default-sort-select",
                                        options=[
                                            {"label": "Newest First", "value": "date_desc"},
                                            {"label": "Oldest First", "value": "date_asc"},
                                            {"label": "Longest Distance", "value": "distance_desc"},
                                            {"label": "Shortest Distance", "value": "distance_asc"},
                                        ],
                                        value=current_prefs.get("default_sort", "date_desc"),
                                    )
                                ],
                                width=9,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Checkboxes for various display options
                    dbc.Row(
                        [
                            dbc.Col([dbc.Label("Display Options")], width=3),
                            dbc.Col(
                                [
                                    dbc.Checklist(
                                        id="display-options-checklist",
                                        options=[
                                            {"label": "Show Heart Rate Zones", "value": "show_heart_rate_zones"},
                                            {"label": "Show Power Zones", "value": "show_power_zones"},
                                            {"label": "Show Activity Thumbnails", "value": "show_activity_thumbnails"},
                                            {"label": "Enable Animations", "value": "enable_animations"},
                                        ],
                                        value=[
                                            key
                                            for key, value in current_prefs.items()
                                            if key
                                            in [
                                                "show_heart_rate_zones",
                                                "show_power_zones",
                                                "show_activity_thumbnails",
                                                "enable_animations",
                                            ]
                                            and value
                                        ],
                                    )
                                ],
                                width=9,
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Save button
                    dbc.Row(
                        [
                            dbc.Col(width=3),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [html.I(className="fas fa-save me-2"), "Save Preferences"],
                                        id="save-preferences-btn",
                                        color="primary",
                                        className="me-2",
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-undo me-2"), "Reset to Defaults"],
                                        id="reset-preferences-btn",
                                        color="outline-secondary",
                                    ),
                                ],
                                width=9,
                            ),
                        ],
                    ),
                    # Status display
                    html.Div(id="preferences-status", className="mt-3"),
                ]
            )
        except Exception as e:
            logger.error(f"Error displaying preferences: {e}")
            return dbc.Alert("Error loading preferences form", color="danger")

    # Save preferences callback
    @app.callback(
        Output("preferences-status", "children"),
        [
            Input("save-preferences-btn", "n_clicks"),
            Input("reset-preferences-btn", "n_clicks"),
        ],
        [
            State("units-radio", "value"),
            State("chart-type-select", "value"),
            State("activities-per-page-select", "value"),
            State("default-sort-select", "value"),
            State("display-options-checklist", "value"),
        ],
        prevent_initial_call=True,
    )
    def handle_preferences_actions(
        save_clicks, reset_clicks, units, chart_type, activities_per_page, default_sort, display_options
    ):
        """Handle saving or resetting preferences."""
        ctx = dash.callback_context
        if not ctx.triggered:
            return ""

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        try:
            prefs = get_preferences()

            if button_id == "reset-preferences-btn":
                # Reset to defaults
                success = prefs.reset_to_defaults()
                if success:
                    return dbc.Alert("Preferences reset to defaults successfully!", color="success", dismissable=True)
                else:
                    return dbc.Alert("Error resetting preferences", color="danger", dismissable=True)

            elif button_id == "save-preferences-btn":
                # Save current form values
                new_prefs = {
                    "units": units,
                    "default_chart_type": chart_type,
                    "activities_per_page": int(activities_per_page),
                    "default_sort": default_sort,
                    "show_heart_rate_zones": "show_heart_rate_zones" in (display_options or []),
                    "show_power_zones": "show_power_zones" in (display_options or []),
                    "show_activity_thumbnails": "show_activity_thumbnails" in (display_options or []),
                    "enable_animations": "enable_animations" in (display_options or []),
                }

                success = prefs.update(new_prefs)
                if success:
                    logger.info(f"Preferences updated: {new_prefs}")
                    return dbc.Alert("Preferences saved successfully!", color="success", dismissable=True)
                else:
                    return dbc.Alert("Error saving preferences", color="danger", dismissable=True)

        except Exception as e:
            logger.error(f"Error handling preferences: {e}")
            return dbc.Alert("Error updating preferences", color="danger", dismissable=True)

        return ""

    # Update database info
    @app.callback(
        Output("database-info-container", "children"),
        Input("database-info-container", "id"),  # Triggers on page load
        prevent_initial_call=False,
    )
    def update_database_info(_):
        """Display current database information."""
        try:
            if get_db_config is None:
                return dbc.Alert("Database module not available. Please check installation.", color="danger")

            db_config = get_db_config()
            db_info = db_config.get_database_info()

            # Format database info
            info_cards = dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(f"{db_info['activities']:,}", className="text-primary mb-1"),
                                            html.P("Activities", className="text-muted mb-0 small"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(f"{db_info['samples']:,}", className="text-success mb-1"),
                                            html.P("Samples", className="text-muted mb-0 small"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(f"{db_info['route_points']:,}", className="text-info mb-1"),
                                            html.P("Route Points", className="text-muted mb-0 small"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(f"{db_info['laps']:,}", className="text-warning mb-1"),
                                            html.P("Laps", className="text-muted mb-0 small"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                ]
            )

            return html.Div(
                [
                    html.P(
                        [html.Strong("Database URL: "), html.Code(db_info["database_url"], className="text-muted")],
                        className="mb-3",
                    ),
                    info_cards,
                ]
            )

        except Exception as e:
            logger.error(f"Error fetching database info: {e}")
            return dbc.Alert(f"Error loading database information: {str(e)}", color="danger")

    # Enable/disable reset button based on confirmation text
    @app.callback(
        Output("reset-database-btn", "disabled"), Input("reset-confirmation-input", "value"), prevent_initial_call=False
    )
    def toggle_reset_button(confirmation_text):
        """Enable reset button only when 'DELETE' is typed."""
        return confirmation_text != "DELETE"

    # Handle database reset
    @app.callback(
        [
            Output("reset-status-container", "children"),
            Output("reset-confirmation-input", "value"),
            Output("database-info-container", "children", allow_duplicate=True),
            Output("settings-alerts-container", "children"),
        ],
        Input("reset-database-btn", "n_clicks"),
        State("reset-confirmation-input", "value"),
        prevent_initial_call=True,
    )
    def reset_database(n_clicks, confirmation_text):
        """Reset the database after confirmation."""
        if not n_clicks or confirmation_text != "DELETE":
            return "", "", dash.no_update, ""

        try:
            if get_db_config is None or init_database is None:
                error_alert = dbc.Alert(
                    "Database modules not available. Cannot reset database.", color="danger", dismissable=True
                )
                return "", "", dash.no_update, error_alert

            logger.info("Starting database reset...")

            # Get database config and reset
            db_config = get_db_config()

            # Drop all tables
            db_config.drop_all_tables()
            logger.info("All tables dropped")

            # Recreate tables
            db_config.create_all_tables()
            logger.info("All tables recreated")

            # Clear input and update info
            success_alert = dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    "Database reset successfully! All data has been cleared.",
                ],
                color="success",
                dismissable=True,
            )

            # Generate updated database info
            new_db_info = update_database_info(None)

            status_message = html.Div(
                [
                    dbc.Alert(
                        [
                            html.I(className="fas fa-check me-2"),
                            f"Database reset completed at {datetime.now().strftime('%H:%M:%S')}",
                        ],
                        color="success",
                        className="mb-0",
                    )
                ]
            )

            return status_message, "", new_db_info, success_alert

        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            error_alert = dbc.Alert(
                [html.I(className="fas fa-exclamation-triangle me-2"), f"Database reset failed: {str(e)}"],
                color="danger",
                dismissable=True,
            )

            error_status = html.Div(
                [
                    dbc.Alert(
                        [html.I(className="fas fa-times me-2"), f"Reset failed: {str(e)}"],
                        color="danger",
                        className="mb-0",
                    )
                ]
            )

            return error_status, "", dash.no_update, error_alert

    # Update system information
    @app.callback(
        Output("system-info-container", "children"),
        Input("system-info-container", "id"),  # Triggers on page load
        prevent_initial_call=False,
    )
    def update_system_info(_):
        """Display system information."""
        try:
            from datetime import datetime
            import os
            import platform

            system_info = [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.P([html.Strong("Python Version: "), platform.python_version()]),
                                html.P([html.Strong("Platform: "), platform.system(), " ", platform.release()]),
                                html.P([html.Strong("Current Time: "), datetime.now().strftime("%Y-%m-%d %H:%M:%S")]),
                                html.P(
                                    [html.Strong("Working Directory: "), html.Code(os.getcwd(), className="text-muted")]
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                html.P(
                                    [
                                        html.Strong("Database Available: "),
                                        html.Span(
                                            "Yes" if get_db_config else "No",
                                            className="text-success" if get_db_config else "text-danger",
                                        ),
                                    ]
                                ),
                                html.P([html.Strong("Environment: "), os.getenv("ENVIRONMENT", "development")]),
                                html.P([html.Strong("Debug Mode: "), os.getenv("DASH_DEBUG", "True")]),
                            ],
                            width=6,
                        ),
                    ]
                )
            ]

            return system_info

        except Exception as e:
            logger.error(f"Error fetching system info: {e}")
            return dbc.Alert(f"Error loading system information: {str(e)}", color="warning")
