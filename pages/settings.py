"""
Settings page for Garmin Dashboard.

Provides database management, user preferences, and system information.
"""

import logging
from datetime import datetime

import dash
from dash import html, dcc, Input, Output, State, callback, ALL, ctx
import dash_bootstrap_components as dbc

# Import database utilities
try:
    import sys
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from data.db import get_db_config, init_database
    from data.models import Activity, Sample, RoutePoint, Lap
except ImportError:
    # Fallback for different path structures
    try:
        sys.path.insert(0, "/app/app")
        from app.data.db import get_db_config, init_database
        from app.data.models import Activity, Sample, RoutePoint, Lap
    except ImportError as e:
        logging.error(f"Failed to import database modules: {e}")
        get_db_config = None
        init_database = None

logger = logging.getLogger(__name__)


def layout():
    """Render settings page layout."""
    return dbc.Container([
        # Page header
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1([
                        html.I(className="fas fa-cog me-3"),
                        "Settings"
                    ], className="text-dark mb-0"),
                    html.P(
                        "Manage your dashboard settings and database",
                        className="text-muted lead"
                    )
                ])
            ])
        ], className="mb-4"),

        # Alerts container
        html.Div(id="settings-alerts-container"),

        # Database Management Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H4([
                            html.I(className="fas fa-database me-2"),
                            "Database Management"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        # Database info container
                        html.Div(id="database-info-container"),
                        
                        html.Hr(),
                        
                        # Database reset section
                        html.Div([
                            html.H5([
                                html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
                                "Reset Database"
                            ], className="text-danger"),
                            html.P([
                                "This will permanently delete all activities, routes, and samples from your database. ",
                                html.Strong("This action cannot be undone.", className="text-danger")
                            ], className="text-muted mb-3"),
                            
                            # Reset confirmation section
                            html.Div([
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="reset-confirmation-input",
                                        placeholder="Type 'DELETE' to confirm",
                                        value="",
                                        type="text"
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-trash me-2"), "Reset Database"],
                                        id="reset-database-btn",
                                        color="danger",
                                        disabled=True
                                    )
                                ], className="mb-3")
                            ]),
                            
                            # Reset status
                            html.Div(id="reset-status-container")
                        ])
                    ])
                ])
            ], width=12)
        ], className="mb-4"),

        # System Information Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H4([
                            html.I(className="fas fa-info-circle me-2"),
                            "System Information"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="system-info-container")
                    ])
                ])
            ], width=12)
        ])

    ], fluid=True)


def register_callbacks(app):
    """Register callbacks for settings page."""
    
    # Update database info
    @app.callback(
        Output("database-info-container", "children"),
        Input("database-info-container", "id"),  # Triggers on page load
        prevent_initial_call=False
    )
    def update_database_info(_):
        """Display current database information."""
        try:
            if get_db_config is None:
                return dbc.Alert(
                    "Database module not available. Please check installation.",
                    color="danger"
                )

            db_config = get_db_config()
            db_info = db_config.get_database_info()
            
            # Format database info
            info_cards = dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(f"{db_info['activities']:,}", className="text-primary mb-1"),
                            html.P("Activities", className="text-muted mb-0 small")
                        ], className="text-center")
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(f"{db_info['samples']:,}", className="text-success mb-1"),
                            html.P("Samples", className="text-muted mb-0 small")
                        ], className="text-center")
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(f"{db_info['route_points']:,}", className="text-info mb-1"),
                            html.P("Route Points", className="text-muted mb-0 small")
                        ], className="text-center")
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(f"{db_info['laps']:,}", className="text-warning mb-1"),
                            html.P("Laps", className="text-muted mb-0 small")
                        ], className="text-center")
                    ])
                ], width=3)
            ])

            return html.Div([
                html.P([
                    html.Strong("Database URL: "), 
                    html.Code(db_info['database_url'], className="text-muted")
                ], className="mb-3"),
                info_cards
            ])

        except Exception as e:
            logger.error(f"Error fetching database info: {e}")
            return dbc.Alert(
                f"Error loading database information: {str(e)}",
                color="danger"
            )

    # Enable/disable reset button based on confirmation text
    @app.callback(
        Output("reset-database-btn", "disabled"),
        Input("reset-confirmation-input", "value"),
        prevent_initial_call=False
    )
    def toggle_reset_button(confirmation_text):
        """Enable reset button only when 'DELETE' is typed."""
        return confirmation_text != "DELETE"

    # Handle database reset
    @app.callback(
        [Output("reset-status-container", "children"),
         Output("reset-confirmation-input", "value"),
         Output("database-info-container", "children", allow_duplicate=True),
         Output("settings-alerts-container", "children")],
        Input("reset-database-btn", "n_clicks"),
        State("reset-confirmation-input", "value"),
        prevent_initial_call=True
    )
    def reset_database(n_clicks, confirmation_text):
        """Reset the database after confirmation."""
        if not n_clicks or confirmation_text != "DELETE":
            return "", "", dash.no_update, ""

        try:
            if get_db_config is None or init_database is None:
                error_alert = dbc.Alert(
                    "Database modules not available. Cannot reset database.",
                    color="danger",
                    dismissable=True
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
            success_alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                "Database reset successfully! All data has been cleared."
            ], color="success", dismissable=True)
            
            # Generate updated database info
            new_db_info = update_database_info(None)
            
            status_message = html.Div([
                dbc.Alert([
                    html.I(className="fas fa-check me-2"),
                    f"Database reset completed at {datetime.now().strftime('%H:%M:%S')}"
                ], color="success", className="mb-0")
            ])
            
            return status_message, "", new_db_info, success_alert

        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            error_alert = dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Database reset failed: {str(e)}"
            ], color="danger", dismissable=True)
            
            error_status = html.Div([
                dbc.Alert([
                    html.I(className="fas fa-times me-2"),
                    f"Reset failed: {str(e)}"
                ], color="danger", className="mb-0")
            ])
            
            return error_status, "", dash.no_update, error_alert

    # Update system information
    @app.callback(
        Output("system-info-container", "children"),
        Input("system-info-container", "id"),  # Triggers on page load
        prevent_initial_call=False
    )
    def update_system_info(_):
        """Display system information."""
        try:
            import os
            import platform
            import sys
            from datetime import datetime

            system_info = [
                dbc.Row([
                    dbc.Col([
                        html.P([html.Strong("Python Version: "), platform.python_version()]),
                        html.P([html.Strong("Platform: "), platform.system(), " ", platform.release()]),
                        html.P([html.Strong("Current Time: "), datetime.now().strftime("%Y-%m-%d %H:%M:%S")]),
                        html.P([html.Strong("Working Directory: "), html.Code(os.getcwd(), className="text-muted")])
                    ], width=6),
                    dbc.Col([
                        html.P([html.Strong("Database Available: "), 
                               html.Span("Yes" if get_db_config else "No", 
                                       className="text-success" if get_db_config else "text-danger")]),
                        html.P([html.Strong("Environment: "), 
                               os.getenv("ENVIRONMENT", "development")]),
                        html.P([html.Strong("Debug Mode: "), 
                               os.getenv("DASH_DEBUG", "True")]),
                    ], width=6)
                ])
            ]

            return system_info

        except Exception as e:
            logger.error(f"Error fetching system info: {e}")
            return dbc.Alert(f"Error loading system information: {str(e)}", color="warning")