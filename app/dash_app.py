"""
Main Dash application with multi-page routing.

Research-validated implementation using Dash 2.17+ patterns with
Bootstrap theme integration and proper page container setup.
"""

import logging
import os

import dash
from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Dash app with research-validated configuration
app = dash.Dash(
    __name__,
    use_pages=False,  # Disable automatic page discovery - we'll register manually
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,  # Research-validated Bootstrap theme
        dbc.icons.FONT_AWESOME,  # Icons for better UX
    ],
    suppress_callback_exceptions=True,  # Allow dynamic callbacks
    title="Garmin Dashboard",
    update_title=None,  # Don't update title on page changes
)

# Configure app server for production
server = app.server
server.config.update(
    {
        "SECRET_KEY": os.environ.get("SECRET_KEY", "dev-key-change-in-production"),
    }
)

# Import page modules immediately after app creation to register callbacks
try:
    import sys

    # Add both possible paths to ensure imports work
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    if "/app/app" not in sys.path:
        sys.path.insert(0, "/app/app")

    # Import pages to register their callbacks with the app
    sys.path.insert(0, "/app")  # Ensure /app is first for pages import
    from app.pages import activity_detail, calendar, garmin_login, settings, fit_upload, stats

    # Register callbacks for pages that need them
    garmin_login.register_callbacks(app)
    settings.register_callbacks(app)
    fit_upload.register_callbacks(app)
    stats.register_callbacks(app)
    logger.info("✅ All page modules imported successfully - callbacks registered")

except ImportError as e:
    logger.error(f"❌ Failed to import page modules: {e}")
    # Fallback: try absolute imports
    try:
        import sys

        sys.path.insert(0, "/app")

        # Try importing directly from /app/pages
        import importlib.util

        # Load calendar module
        calendar_spec = importlib.util.spec_from_file_location("calendar", "/app/pages/calendar.py")
        calendar = importlib.util.module_from_spec(calendar_spec)
        calendar_spec.loader.exec_module(calendar)

        # Load activity_detail module
        activity_spec = importlib.util.spec_from_file_location("activity_detail", "/app/pages/activity_detail.py")
        activity_detail = importlib.util.module_from_spec(activity_spec)
        activity_spec.loader.exec_module(activity_detail)

        # Load garmin_login module
        garmin_spec = importlib.util.spec_from_file_location("garmin_login", "/app/pages/garmin_login.py")
        garmin_login = importlib.util.module_from_spec(garmin_spec)
        garmin_spec.loader.exec_module(garmin_login)

        # Load settings module
        settings_spec = importlib.util.spec_from_file_location("settings", "/app/pages/settings.py")
        settings = importlib.util.module_from_spec(settings_spec)
        settings_spec.loader.exec_module(settings)

        # Load fit_upload module
        fit_upload_spec = importlib.util.spec_from_file_location("fit_upload", "/app/pages/fit_upload.py")
        fit_upload = importlib.util.module_from_spec(fit_upload_spec)
        fit_upload_spec.loader.exec_module(fit_upload)

        # Load stats module
        stats_spec = importlib.util.spec_from_file_location("stats", "/app/pages/stats.py")
        stats = importlib.util.module_from_spec(stats_spec)
        stats_spec.loader.exec_module(stats)

        # Register callbacks for pages that need them
        garmin_login.register_callbacks(app)
        settings.register_callbacks(app)
        fit_upload.register_callbacks(app)
        stats.register_callbacks(app)
        logger.info("✅ Page modules imported via importlib - callbacks registered")

    except Exception as e2:
        logger.error(f"❌ Complete failure to import page modules: {e2}")


# Main application layout with navigation and page container
app.layout = dbc.Container(
    [
        # Navigation bar with research-validated Bootstrap components
        dbc.Navbar(
            [
                dbc.Row(
                    [
                        # Brand/Logo section
                        dbc.Col(
                            [
                                dbc.NavbarBrand(
                                    [html.I(className="fas fa-running me-2"), "Garmin Dashboard"],  # Running icon
                                    href="/",
                                    className="text-white fw-bold",
                                )
                            ],
                            width="auto",
                        ),
                        # Navigation links
                        dbc.Col(
                            [
                                dbc.Nav(
                                    [
                                        dbc.NavLink(
                                            [html.I(className="fas fa-calendar me-1"), "Activities"],
                                            href="/",
                                            active="exact",
                                            className="text-white",
                                        ),
                                        dbc.NavLink(
                                            [html.I(className="fas fa-chart-line me-1"), "Statistics"],
                                            href="/stats",
                                            active="exact",
                                            className="text-white",
                                        ),
                                        dbc.NavLink(
                                            [html.I(className="fas fa-download me-1"), "Garmin Sync"],
                                            href="/garmin",
                                            active="exact",
                                            className="text-white",
                                        ),
                                        dbc.NavLink(
                                            [html.I(className="fas fa-file-upload me-1"), "Import Files"],
                                            href="/upload",
                                            active="exact",
                                            className="text-white",
                                        ),
                                        dbc.NavLink(
                                            [html.I(className="fas fa-cog me-1"), "Settings"],
                                            href="/settings",
                                            active="exact",
                                            className="text-white",
                                        ),
                                    ],
                                    navbar=True,
                                    className="ms-auto",
                                )
                            ]
                        ),
                    ],
                    align="center",
                    className="w-100",
                    justify="between",
                )
            ],
            color="dark",
            dark=True,
            className="mb-4",
            sticky="top",  # Keep navigation visible on scroll
        ),
        # Client-side data store for session management
        dcc.Store(id="session-store", storage_type="session", data={}),
        dcc.Store(
            id="activity-filters",
            storage_type="session",
            data={"start_date": None, "end_date": None, "sport": "all", "search_term": ""},
        ),
        # Location component for URL routing
        dcc.Location(id="url", refresh=False),
        # Main content area - this is where pages will be rendered
        html.Div(id="page-content"),
        # Footer
        html.Footer(
            [
                dbc.Container(
                    [
                        html.Hr(className="my-4"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.P(
                                            [
                                                "🏃 Garmin Dashboard - Built with ",
                                                html.A(
                                                    "Dash",
                                                    href="https://dash.plotly.com/",
                                                    target="_blank",
                                                    className="text-decoration-none",
                                                ),
                                                " & ",
                                                html.A(
                                                    "Bootstrap",
                                                    href="https://getbootstrap.com/",
                                                    target="_blank",
                                                    className="text-decoration-none",
                                                ),
                                            ],
                                            className="text-muted small mb-0",
                                        )
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        html.P(
                                            [
                                                html.Span("Data stays local 🔒", className="text-success"),
                                            ],
                                            className="text-muted small mb-0 text-end",
                                        )
                                    ],
                                    width=6,
                                ),
                            ]
                        ),
                    ]
                )
            ]
        ),
    ],
    fluid=True,
    className="px-0",
)


# URL routing callback
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    """Manual routing for pages."""
    logger.info(f"Routing to pathname: {pathname}")

    if pathname == "/" or pathname is None:
        # Calendar/activity list page
        try:
            from app.pages.calendar import layout as calendar_layout

            logger.info("Loading calendar page")
            return calendar_layout()
        except Exception as e:
            logger.error(f"Error loading calendar: {e}")
            return html.Div([html.H2(f"Error loading calendar: {str(e)}")])

    elif pathname.startswith("/activity/"):
        # Activity detail page
        try:
            activity_id = pathname.split("/activity/")[1]
            logger.info(f"Loading activity detail for ID: {activity_id}")
            from app.pages.activity_detail import layout as activity_layout

            return activity_layout(activity_id)
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid activity ID: {e}")
            return html.Div([html.H2("404 - Invalid activity ID")])
        except Exception as e:
            logger.error(f"Error loading activity detail: {e}")
            return html.Div([html.H2(f"Error loading activity: {str(e)}")])

    elif pathname == "/garmin":
        # Garmin Connect sync page
        try:
            from app.pages.garmin_login import layout as garmin_layout
            logger.info("Loading Garmin sync page")
            return garmin_layout()
        except Exception as e:
            logger.error(f"Error loading Garmin page: {e}")
            return html.Div([html.H2(f"Error loading Garmin sync: {str(e)}")])

    elif pathname == "/upload":
        # FIT file upload page
        try:
            from app.pages.fit_upload import layout as upload_layout
            logger.info("Loading FIT upload page")
            return upload_layout()
        except Exception as e:
            logger.error(f"Error loading upload page: {e}")
            return html.Div([html.H2(f"Error loading upload page: {str(e)}")])

    elif pathname == "/settings":
        # Settings page
        try:
            from app.pages.settings import layout as settings_layout
            logger.info("Loading settings page")
            return settings_layout()
        except Exception as e:
            logger.error(f"Error loading settings page: {e}")
            return html.Div([html.H2(f"Error loading settings: {str(e)}")])

    elif pathname == "/stats":
        # Statistics page
        try:
            from app.pages.stats import layout as stats_layout
            logger.info("Loading statistics page")
            return stats_layout()
        except Exception as e:
            logger.error(f"Error loading statistics page: {e}")
            return html.Div([html.H2(f"Error loading statistics: {str(e)}")])

    else:
        logger.info(f"Unknown pathname: {pathname}")
        return html.Div([html.H2("404 - Page not found")])


def update_session_data(pathname, session_data):
    """Update session data based on URL changes."""
    if session_data is None:
        session_data = {}
    session_data["current_page"] = pathname
    return session_data


# Error handling for page not found
def page_not_found():
    """Return 404 page layout."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H1("404", className="display-1 text-muted"),
                                    html.H2("Page Not Found", className="mb-3"),
                                    html.P("The page you're looking for doesn't exist.", className="text-muted mb-4"),
                                    dbc.Button(
                                        [html.I(className="fas fa-home me-2"), "Go Home"], href="/", color="primary"
                                    ),
                                ],
                                className="text-center",
                            )
                        ],
                        width=6,
                        className="mx-auto",
                    )
                ],
                className="min-vh-50 d-flex align-items-center",
            )
        ]
    )


# Add custom CSS for enhanced styling
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Custom CSS for Garmin Dashboard */
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner table {
                border-collapse: separate;
                border-spacing: 0;
            }
            
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
                background-color: #f8f9fa;
                border-bottom: 2px solid #dee2e6;
                font-weight: 600;
            }
            
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner tr:hover {
                background-color: rgba(0,123,255,0.05);
                cursor: pointer;
            }
            
            /* Loading animations */
            .loading-spinner {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(0,123,255,0.3);
                border-radius: 50%;
                border-top-color: #007bff;
                animation: spin 1s ease-in-out infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            /* Responsive map container */
            .map-container {
                position: relative;
                height: 400px;
                width: 100%;
                margin-bottom: 1rem;
            }
            
            /* Chart container */
            .chart-container {
                margin-bottom: 2rem;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

# Page modules are imported above right after app creation

if __name__ == "__main__":
    # Development server configuration
    debug_mode = os.environ.get("DASH_DEBUG", "True").lower() == "true"
    port = int(os.environ.get("PORT", 8050))
    host = os.environ.get("HOST", "127.0.0.1")

    logger.info(f"Starting Garmin Dashboard on {host}:{port}")
    logger.info(f"Debug mode: {debug_mode}")

    app.run(debug=debug_mode, host=host, port=port)
