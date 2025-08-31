"""
Garmin Connect login and data synchronization page.
"""

from datetime import datetime, timedelta
import logging

from dash import Input, Output, State, ctx, dcc, html
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

# This page uses manual routing - no registration needed


def layout():
    """
    Layout for Garmin Connect login and data sync page.
    """
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(
                                [html.I(className="fas fa-user-lock me-3"), "Garmin Connect Integration"],
                                className="mb-4",
                            ),
                            html.P(
                                "Connect to your Garmin Connect account to download and synchronize your activity data automatically.",
                                className="text-muted mb-4",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Login section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Login to Garmin Connect", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            dcc.Store(id="login-status-store", data={}),
                                            # Login form
                                            html.Div(
                                                id="login-form",
                                                children=[
                                                    dbc.Form(
                                                        [
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Email/Username",
                                                                                html_for="garmin-email",
                                                                            ),
                                                                            dbc.Input(
                                                                                type="email",
                                                                                id="garmin-email",
                                                                                placeholder="your.email@example.com",
                                                                                required=True,
                                                                            ),
                                                                        ],
                                                                        width=12,
                                                                        className="mb-3",
                                                                    )
                                                                ]
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Password", html_for="garmin-password"
                                                                            ),
                                                                            dbc.Input(
                                                                                type="password",
                                                                                id="garmin-password",
                                                                                placeholder="Enter your password",
                                                                                required=True,
                                                                            ),
                                                                        ],
                                                                        width=12,
                                                                        className="mb-3",
                                                                    )
                                                                ]
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Checkbox(
                                                                                id="remember-me-checkbox",
                                                                                label="Remember my credentials",
                                                                                value=False,
                                                                                className="mb-3",
                                                                            ),
                                                                        ],
                                                                        width=12,
                                                                    )
                                                                ]
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Button(
                                                                                [
                                                                                    html.I(
                                                                                        className="fas fa-sign-in-alt me-2"
                                                                                    ),
                                                                                    "Login",
                                                                                ],
                                                                                id="login-button",
                                                                                color="primary",
                                                                                size="lg",
                                                                                className="w-100",
                                                                            )
                                                                        ],
                                                                        width=12,
                                                                    )
                                                                ]
                                                            ),
                                                        ]
                                                    )
                                                ],
                                            ),
                                            # MFA section (hidden by default)
                                            html.Div(id="mfa-section", children=[], style={"display": "none"}),
                                            # Status messages
                                            html.Div(id="login-status", className="mt-3"),
                                            # Success section (hidden by default)
                                            html.Div(id="success-section", children=[], style={"display": "none"}),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=8,
                    )
                ],
                justify="center",
                className="mb-4",
            ),
            # Data sync section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Data Synchronization", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="sync-controls",
                                                children=[
                                                    dbc.Alert(
                                                        "Please login first to enable data synchronization.",
                                                        color="info",
                                                        className="mb-3",
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Sync Period"),
                                                                    dbc.Select(
                                                                        id="sync-period",
                                                                        options=[
                                                                            {"label": "Last 7 days", "value": "7"},
                                                                            {"label": "Last 30 days", "value": "30"},
                                                                            {"label": "Last 90 days", "value": "90"},
                                                                            {"label": "All activities", "value": "all"},
                                                                        ],
                                                                        value="30",
                                                                        disabled=True,
                                                                    ),
                                                                ],
                                                                width=6,
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Action"),
                                                                    html.Div(
                                                                        [
                                                                            dbc.Button(
                                                                                [
                                                                                    html.I(
                                                                                        className="fas fa-sync me-2"
                                                                                    ),
                                                                                    "Sync Activities",
                                                                                ],
                                                                                id="sync-button",
                                                                                color="success",
                                                                                size="lg",
                                                                                disabled=True,
                                                                            )
                                                                        ]
                                                                    ),
                                                                ],
                                                                width=6,
                                                            ),
                                                        ]
                                                    ),
                                                ],
                                            ),
                                            # Sync status
                                            html.Div(id="sync-status", className="mt-3"),
                                            # Progress bar
                                            html.Div(id="sync-progress", className="mt-3", style={"display": "none"}),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=8,
                    )
                ],
                justify="center",
            ),
        ],
        fluid=True,
    )


def register_callbacks(app):
    """Register callbacks with the given Dash app instance."""

    @app.callback(
        [
            Output("login-status", "children"),
            Output("mfa-section", "children"),
            Output("mfa-section", "style"),
            Output("success-section", "children"),
            Output("success-section", "style"),
            Output("login-form", "style"),
            Output("login-status-store", "data"),
        ],
        [Input("login-button", "n_clicks")],
        [
            State("garmin-email", "value"),
            State("garmin-password", "value"),
            State("remember-me-checkbox", "value"),
            State("login-status-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_garmin_login(login_clicks, email, password, remember_me, store_data):
        """Handle Garmin Connect login process including MFA."""

        if not ctx.triggered or not login_clicks:
            return "", [], {"display": "none"}, [], {"display": "none"}, {}, {}

        # Handle login button click
        if not email or not password:
            return (
                dbc.Alert("Please enter both email and password.", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                {},
            )

        try:
            # Import Garmin Connect client
            from garmin_client.client import GarminConnectClient

            # Initialize client
            client = GarminConnectClient()

            # Attempt authentication without MFA callback first
            success = client.authenticate(email, password, remember_me=remember_me)

            if success == "MFA_REQUIRED":
                # MFA required - show MFA input dialog
                mfa_content = [
                    dbc.Alert(
                        "Multi-Factor Authentication required. Please enter your MFA code.",
                        color="info",
                        className="mb-3",
                    ),
                    dbc.Form(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("MFA Code", html_for="mfa-code"),
                                            dbc.Input(
                                                type="text",
                                                id="mfa-code",
                                                placeholder="Enter 6-digit MFA code",
                                                maxLength=6,
                                                pattern="[0-9]{6}",
                                                required=True,
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-key me-2"), "Verify MFA"],
                                                id="mfa-verify-button",
                                                color="primary",
                                                size="lg",
                                                className="w-100",
                                            ),
                                        ],
                                        width=12,
                                    )
                                ]
                            )
                        ]
                    ),
                ]

                return (
                    "",
                    mfa_content,
                    {"display": "block"},  # Show MFA section explicitly
                    [],
                    {"display": "none"},
                    {"display": "none"},  # Hide login form
                    {"mfa_required": True, "email": email, "password": password, "remember_me": remember_me},
                )
            elif success:
                # Authentication successful
                success_content = [
                    dbc.Alert(
                        [
                            html.H4("Login Successful!", className="alert-heading"),
                            html.P(f"Successfully connected to Garmin Connect account: {email}"),
                            html.Hr(),
                            html.P("You can now sync your activities from Garmin Connect.", className="mb-0"),
                        ],
                        color="success",
                    )
                ]

                return (
                    "",
                    [],
                    {"display": "none"},
                    success_content,
                    {},
                    {"display": "none"},
                    {"logged_in": True, "email": email},
                )
            else:
                # Authentication failed - provide more specific feedback
                error_message = "Authentication failed. Please check your credentials and try again."
                if "oauth" in str(success).lower():
                    error_message = "Garmin Connect authentication is currently experiencing issues. This may be due to recent changes in Garmin's API or temporary server issues. Please try again later or ensure your Garmin Connect account is in good standing."

                return (
                    dbc.Alert(error_message, color="danger"),
                    [],
                    {"display": "none"},
                    [],
                    {"display": "none"},
                    {},
                    {},
                )

        except Exception as e:
            return (
                dbc.Alert(f"Login error: {str(e)}", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                {},
            )

        # MFA handling would go here in the future

        return "", [], {"display": "none"}, [], {"display": "none"}, {}, {}

    @app.callback(
        [
            Output("login-status", "children", allow_duplicate=True),
            Output("mfa-section", "children", allow_duplicate=True),
            Output("mfa-section", "style", allow_duplicate=True),
            Output("success-section", "children", allow_duplicate=True),
            Output("success-section", "style", allow_duplicate=True),
            Output("login-form", "style", allow_duplicate=True),
            Output("login-status-store", "data", allow_duplicate=True),
        ],
        [Input("mfa-verify-button", "n_clicks")],
        [
            State("mfa-code", "value"),
            State("login-status-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_mfa_verification(mfa_clicks, mfa_code, store_data):
        """Handle MFA code verification."""

        if not ctx.triggered or not mfa_clicks:
            return "", [], {"display": "none"}, [], {"display": "none"}, {}, {}

        if not store_data.get("mfa_required"):
            return (
                dbc.Alert("Invalid MFA state.", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                {},
            )

        if not mfa_code or len(mfa_code) != 6:
            return (
                dbc.Alert("Please enter a valid 6-digit MFA code.", color="danger"),
                store_data.get("mfa_content", []),
                {"display": "block"},  # Keep MFA section visible
                [],
                {"display": "none"},
                {"display": "none"},
                store_data,
            )

        try:
            from garmin_client.client import GarminConnectClient

            # Initialize client and authenticate with MFA
            client = GarminConnectClient()
            email = store_data["email"]
            password = store_data["password"]

            # Create MFA callback that returns the provided code
            def web_mfa_callback():
                logger.info(f"MFA callback called, returning code: {mfa_code}")
                return mfa_code

            success = client.authenticate(
                email, password, mfa_callback=web_mfa_callback, remember_me=store_data.get("remember_me", False)
            )

            if success:
                success_content = [
                    dbc.Alert(
                        [
                            html.H4("Login Successful!", className="alert-heading"),
                            html.P(f"Successfully connected to Garmin Connect account: {email}"),
                            html.Hr(),
                            html.P("You can now sync your activities from Garmin Connect.", className="mb-0"),
                        ],
                        color="success",
                    )
                ]

                return (
                    "",
                    [],
                    {"display": "none"},
                    success_content,
                    {},
                    {"display": "none"},
                    {"logged_in": True, "email": email},
                )
            else:
                return (
                    dbc.Alert("MFA verification failed. Please try again.", color="danger"),
                    store_data.get("mfa_content", []),
                    {"display": "block"},  # Keep MFA section visible
                    [],
                    {"display": "none"},
                    {"display": "none"},
                    store_data,
                )

        except Exception as e:
            return (
                dbc.Alert(f"MFA verification error: {str(e)}", color="danger"),
                store_data.get("mfa_content", []),
                {"display": "block"},  # Keep MFA section visible
                [],
                {"display": "none"},
                {"display": "none"},
                store_data,
            )

    @app.callback(
        [
            Output("sync-controls", "children"),
            Output("sync-status", "children"),
            Output("sync-progress", "children"),
            Output("sync-progress", "style"),
        ],
        [Input("sync-button", "n_clicks"), Input("login-status-store", "data")],
        [State("sync-period", "value")],
        prevent_initial_call=True,
    )
    def handle_data_sync(sync_clicks, login_status, sync_period):
        """Handle data synchronization from Garmin Connect."""

        # Update sync controls based on login status
        if login_status.get("logged_in"):
            sync_controls = [
                dbc.Alert(f"Logged in as: {login_status.get('email', 'Unknown')}", color="success", className="mb-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Sync Period"),
                                dbc.Select(
                                    id="sync-period",
                                    options=[
                                        {"label": "Last 7 days", "value": "7"},
                                        {"label": "Last 30 days", "value": "30"},
                                        {"label": "Last 90 days", "value": "90"},
                                        {"label": "All activities", "value": "all"},
                                    ],
                                    value="30",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Action"),
                                html.Div(
                                    [
                                        dbc.Button(
                                            [html.I(className="fas fa-sync me-2"), "Sync Activities"],
                                            id="sync-button",
                                            color="success",
                                            size="lg",
                                        )
                                    ]
                                ),
                            ],
                            width=6,
                        ),
                    ]
                ),
            ]
        else:
            sync_controls = [
                dbc.Alert("Please login first to enable data synchronization.", color="info", className="mb-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Sync Period"),
                                dbc.Select(
                                    id="sync-period",
                                    options=[
                                        {"label": "Last 7 days", "value": "7"},
                                        {"label": "Last 30 days", "value": "30"},
                                        {"label": "Last 90 days", "value": "90"},
                                        {"label": "All activities", "value": "all"},
                                    ],
                                    value="30",
                                    disabled=True,
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Action"),
                                html.Div(
                                    [
                                        dbc.Button(
                                            [html.I(className="fas fa-sync me-2"), "Sync Activities"],
                                            id="sync-button",
                                            color="success",
                                            size="lg",
                                            disabled=True,
                                        )
                                    ]
                                ),
                            ],
                            width=6,
                        ),
                    ]
                ),
            ]

        # Handle sync button clicks
        if sync_clicks and login_status.get("logged_in"):
            try:
                # Determine date range
                if sync_period == "all":
                    start_date = None
                else:
                    days = int(sync_period)
                    start_date = datetime.now() - timedelta(days=days)

                # Start sync process
                status_message = dbc.Alert(
                    [
                        html.I(className="fas fa-spinner fa-spin me-2"),
                        f"Syncing activities from Garmin Connect ({sync_period} days)...",
                    ],
                    color="info",
                )

                progress_bar = dbc.Progress(value=0, striped=True, animated=True, className="mb-3")

                return sync_controls, status_message, progress_bar, {}

            except Exception as e:
                error_message = dbc.Alert(f"Sync error: {str(e)}", color="danger")
                return sync_controls, error_message, "", {"display": "none"}

        return sync_controls, "", "", {"display": "none"}

    # Callback to load saved credentials on page load
    @app.callback(
        [
            Output("garmin-email", "value"),
            Output("garmin-password", "value"),
            Output("remember-me-checkbox", "value"),
        ],
        [Input("url", "pathname")],
        prevent_initial_call=False,
    )
    def load_saved_credentials(pathname):
        """Load saved credentials when navigating to the Garmin login page."""
        if pathname != "/garmin":
            return "", "", False

        try:
            from garmin_client.client import GarminConnectClient

            client = GarminConnectClient()
            credentials = client.load_credentials()

            if credentials:
                return credentials.get("email", ""), credentials.get("password", ""), True
            else:
                return "", "", False

        except Exception:
            return "", "", False
