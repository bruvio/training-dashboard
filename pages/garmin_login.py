"""
Garmin Connect login and data synchronization page.
"""

from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta

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
        [Input("login-button", "n_clicks"), Input("mfa-submit-button", "n_clicks")],
        [
            State("garmin-email", "value"),
            State("garmin-password", "value"),
            State("mfa-code", "value"),
            State("login-status-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_garmin_login(login_clicks, mfa_clicks, email, password, mfa_code, store_data):
        """Handle Garmin Connect login process including MFA."""

        if not ctx.triggered:
            return "", [], {"display": "none"}, [], {"display": "none"}, {}, {}

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if triggered_id == "login-button" and login_clicks:
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

                # Attempt login
                result = client.login(email, password)

                if result["status"] == "success":
                    # Login successful
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

                elif result["status"] == "mfa_required":
                    # MFA required
                    mfa_content = [
                        dbc.Alert(
                            "Multi-Factor Authentication required. Check your email or authenticator app.",
                            color="warning",
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
                                                    placeholder="Enter 6-digit code",
                                                    maxlength=6,
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
                                                dbc.Button(
                                                    [html.I(className="fas fa-key me-2"), "Submit MFA Code"],
                                                    id="mfa-submit-button",
                                                    color="warning",
                                                    size="lg",
                                                    className="w-100",
                                                )
                                            ],
                                            width=12,
                                        )
                                    ]
                                ),
                            ]
                        ),
                    ]

                    return (
                        "",
                        mfa_content,
                        {},
                        [],
                        {"display": "none"},
                        {"display": "none"},
                        {"mfa_session": result.get("session_data", {}), "email": email},
                    )

                else:
                    # Login failed
                    return (
                        dbc.Alert(f"Login failed: {result.get('message', 'Unknown error')}", color="danger"),
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

        elif triggered_id == "mfa-submit-button" and mfa_clicks:
            if not mfa_code or len(mfa_code) != 6:
                return (
                    dbc.Alert("Please enter a valid 6-digit MFA code.", color="danger"),
                    [],
                    {},
                    [],
                    {"display": "none"},
                    {"display": "none"},
                    store_data,
                )

            try:
                # Import Garmin Connect client
                from garmin_client.client import GarminConnectClient

                # Initialize client with MFA session data
                client = GarminConnectClient()
                session_data = store_data.get("mfa_session", {})

                # Submit MFA code
                result = client.submit_mfa(mfa_code, session_data)

                if result["status"] == "success":
                    # MFA successful
                    success_content = [
                        dbc.Alert(
                            [
                                html.H4("Login Successful!", className="alert-heading"),
                                html.P(
                                    f"Successfully connected to Garmin Connect account: {store_data.get('email', 'Unknown')}"
                                ),
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
                        {"logged_in": True, "email": store_data.get("email")},
                    )
                else:
                    # MFA failed
                    return (
                        dbc.Alert(f"MFA verification failed: {result.get('message', 'Invalid code')}", color="danger"),
                        [],
                        {},
                        [],
                        {"display": "none"},
                        {"display": "none"},
                        store_data,
                    )

            except Exception as e:
                return (
                    dbc.Alert(f"MFA error: {str(e)}", color="danger"),
                    [],
                    {},
                    [],
                    {"display": "none"},
                    {"display": "none"},
                    store_data,
                )

        return "", [], {"display": "none"}, [], {"display": "none"}, {}, {}

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
                # Import sync functionality
                pass

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
