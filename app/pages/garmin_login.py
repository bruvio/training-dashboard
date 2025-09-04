"""
Garmin Connect login and data synchronization page.
"""

import base64
import logging
import pickle

from dash import Input, Output, State, ctx, dcc, html  # noqa: E401
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


def layout():
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    [
                        html.H1(
                            [html.I(className="fas fa-user-lock me-3"), "Garmin Connect Integration"], className="mb-4"
                        ),
                        html.P(
                            "Connect to your Garmin Connect account to download and synchronize your activity data automatically.",
                            className="text-muted mb-4",
                        ),
                    ],
                    width=12,
                )
            ),
            dbc.Row(
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H5("Login to Garmin Connect", className="mb-0")),
                                dbc.CardBody(
                                    [
                                        dcc.Store(id="login-status-store", data={}),
                                        html.Div(
                                            id="login-form",
                                            children=[
                                                dbc.Form(
                                                    [
                                                        dbc.Row(
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label(
                                                                        "Email/Username", html_for="garmin-email"
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
                                                        ),
                                                        dbc.Row(
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Password", html_for="garmin-password"),
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
                                                        ),
                                                        dbc.Row(
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
                                                        ),
                                                        dbc.Row(
                                                            dbc.Col(
                                                                [
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(className="fas fa-sign-in-alt me-2"),
                                                                            "Login",
                                                                        ],
                                                                        id="login-button",
                                                                        color="primary",
                                                                        size="lg",
                                                                        className="w-100",
                                                                    ),
                                                                ],
                                                                width=12,
                                                            )
                                                        ),
                                                    ]
                                                )
                                            ],
                                        ),
                                        html.Div(id="mfa-section", children=[], style={"display": "none"}),
                                        html.Div(id="login-status", className="mt-3"),
                                        html.Div(id="success-section", children=[], style={"display": "none"}),
                                    ]
                                ),
                            ]
                        )
                    ],
                    width=8,
                ),
                justify="center",
                className="mb-4",
            ),
            dbc.Row(
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H5("Data Synchronization", className="mb-0")),
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
                                                                dbc.Button(
                                                                    [
                                                                        html.I(className="fas fa-sync me-2"),
                                                                        "Sync Activities",
                                                                    ],
                                                                    id="sync-button",
                                                                    color="success",
                                                                    size="lg",
                                                                    disabled=True,
                                                                ),
                                                            ],
                                                            width=6,
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        ),
                                        html.Div(id="sync-status", className="mt-3"),
                                        html.Div(id="sync-progress", className="mt-3", style={"display": "none"}),
                                        html.Hr(),
                                        html.H6("📋 Selective Activity Import", className="mt-4 mb-3"),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Button(
                                                            [
                                                                html.I(className="fas fa-list me-2"),
                                                                "List Available Activities",
                                                            ],
                                                            id="list-activities-button",
                                                            color="info",
                                                            outline=True,
                                                            disabled=True,  # Initially disabled
                                                        ),
                                                    ],
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Button(
                                                            [
                                                                html.I(className="fas fa-download me-2"),
                                                                "Import Selected",
                                                            ],
                                                            id="import-selected-button",
                                                            color="success",
                                                            disabled=True,  # Initially disabled
                                                        ),
                                                    ],
                                                    width=6,
                                                ),
                                            ]
                                        ),
                                        html.Div(id="activity-list-container", className="mt-3"),
                                        html.Div(id="import-status", className="mt-3"),
                                    ]
                                ),
                            ]
                        )
                    ],
                    width=8,
                ),
                justify="center",
            ),
        ],
        fluid=True,
    )


def register_callbacks(app):
    from garmin_client.client import GarminConnectClient

    @app.callback(
        [
            Output("login-form", "style", allow_duplicate=True),
            Output("success-section", "children", allow_duplicate=True),
            Output("success-section", "style", allow_duplicate=True),
            Output("sync-period", "disabled", allow_duplicate=True),
            Output("sync-button", "disabled", allow_duplicate=True),
            Output("sync-controls", "children", allow_duplicate=True),
            Output("list-activities-button", "disabled", allow_duplicate=True),
            Output("import-selected-button", "disabled", allow_duplicate=True),
        ],
        [Input("url", "pathname")],
        prevent_initial_call="initial_duplicate",
    )
    def check_existing_authentication(pathname):
        """Check for existing authentication on page load and update UI accordingly."""
        # Only check authentication when on the garmin page
        if pathname != "/garmin":
            return {}, [], {"display": "none"}, True, True, [], True, True

        client = GarminConnectClient()

        # Try to restore existing session
        restore_result = client.restore_session()

        if restore_result["status"] == "SUCCESS":
            # User is authenticated, show success state and enable sync controls
            success_content = [
                dbc.Alert(
                    [
                        html.H4("Already Logged In!"),
                        html.P("Your Garmin Connect session has been restored."),
                        html.Hr(),
                        html.P("You can now sync activities."),
                    ],
                    color="success",
                )
            ]

            # Enable sync controls
            sync_controls = [
                dbc.Alert(
                    "✅ Authenticated - You can now synchronize your activities.",
                    color="success",
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
                                    disabled=False,  # Enable the dropdown
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Action"),
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-sync me-2"),
                                        "Sync Activities",
                                    ],
                                    id="sync-button",
                                    color="success",
                                    size="lg",
                                    disabled=False,  # Enable the sync button
                                ),
                            ],
                            width=6,
                        ),
                    ]
                ),
            ]

            return (
                {"display": "none"},  # Hide login form
                success_content,
                {},  # Show success section
                False,  # Enable sync period dropdown
                False,  # Enable sync button
                sync_controls,
                False,  # Enable list activities button
                False,  # Enable import selected button
            )
        else:
            # No valid session found, show login form and disabled sync controls
            sync_controls = [
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
                                    disabled=True,  # Keep disabled
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Action"),
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-sync me-2"),
                                        "Sync Activities",
                                    ],
                                    id="sync-button",
                                    color="success",
                                    size="lg",
                                    disabled=True,  # Keep disabled
                                ),
                            ],
                            width=6,
                        ),
                    ]
                ),
            ]

            return (
                {},  # Show login form
                [],
                {"display": "none"},  # Hide success section
                True,  # Keep sync controls disabled
                True,  # Keep sync button disabled
                sync_controls,
                True,  # Keep list activities button disabled
                True,  # Keep import selected button disabled
            )

    @app.callback(
        [
            Output("login-status", "children"),
            Output("mfa-section", "children"),
            Output("mfa-section", "style"),
            Output("success-section", "children"),
            Output("success-section", "style"),
            Output("login-form", "style"),
            Output("login-status-store", "data"),
            Output("sync-period", "disabled"),
            Output("sync-button", "disabled"),
            Output("sync-controls", "children", allow_duplicate=True),
            Output("list-activities-button", "disabled", allow_duplicate=True),
            Output("import-selected-button", "disabled", allow_duplicate=True),
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
    def handle_garmin_login(n_clicks, email, password, remember_me, store_data):
        if not ctx.triggered or not n_clicks:
            return "", [], {"display": "none"}, [], {"display": "none"}, {}, {}, True, True, [], True, True

        if not email or not password:
            return (
                dbc.Alert("Please enter both email and password.", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                {},
                True,  # Keep sync controls disabled
                True,  # Keep sync button disabled
                [],  # Empty sync controls
                True,  # Keep list activities button disabled
                True,  # Keep import selected button disabled
            )

        client = GarminConnectClient()
        result = client.authenticate(email, password, remember_me=remember_me)

        # Debug logging to track what's happening
        logger.info(f"Authentication result: {result}")
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")

        if result["status"] == "MFA_REQUIRED":
            logger.info("🔐 MFA_REQUIRED status detected, creating MFA dialog")
            mfa_content = [
                dbc.Alert(
                    "Multi-Factor Authentication required. Please enter your MFA code.", color="info", className="mb-3"
                ),
                dbc.Form(
                    dbc.Row(
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
                    )
                ),
            ]
            # Create sync controls with disabled state during MFA
            sync_controls = [
                dbc.Alert(
                    "Please complete MFA authentication to enable data synchronization.",
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
                                    disabled=True,  # Keep disabled during MFA
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Action"),
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-sync me-2"),
                                        "Sync Activities",
                                    ],
                                    id="sync-button",
                                    color="success",
                                    size="lg",
                                    disabled=True,  # Keep disabled during MFA
                                ),
                            ],
                            width=6,
                        ),
                    ]
                ),
            ]

            return (
                "",
                mfa_content,
                {"display": "block"},
                [],
                {"display": "none"},
                {"display": "none"},
                {
                    "mfa_required": True,
                    "email": email,
                    "password": password,
                    "remember_me": remember_me,
                    "mfa_context": result.get("mfa_context"),
                    "mfa_content": mfa_content,
                },
                True,  # Keep sync controls disabled during MFA
                True,  # Keep sync button disabled during MFA
                sync_controls,  # Keep sync controls with disabled components
                True,  # Keep list activities button disabled during MFA
                True,  # Keep import selected button disabled during MFA
            )

        elif result["status"] == "SUCCESS":
            success_content = [
                dbc.Alert(
                    [
                        html.H4("Login Successful!"),
                        html.P(f"Connected to Garmin account: {email}"),
                        html.Hr(),
                        html.P("You can now sync activities."),
                    ],
                    color="success",
                )
            ]

            # Enable sync controls after successful login
            sync_controls = [
                dbc.Alert(
                    "✅ Authenticated - You can now synchronize your activities.",
                    color="success",
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
                                    disabled=False,  # Enable the dropdown
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Action"),
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-sync me-2"),
                                        "Sync Activities",
                                    ],
                                    id="sync-button",
                                    color="success",
                                    size="lg",
                                    disabled=False,  # Enable the sync button
                                ),
                            ],
                            width=6,
                        ),
                    ]
                ),
            ]

            return (
                "",
                [],
                {"display": "none"},
                success_content,
                {},
                {"display": "none"},
                {"logged_in": True, "email": email},
                False,  # Enable sync period dropdown
                False,  # Enable sync button
                sync_controls,  # Enable sync controls
                False,  # Enable list activities button
                False,  # Enable import selected button
            )

        else:
            return (
                dbc.Alert("Authentication failed. Check credentials.", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                {},
                True,  # Keep sync controls disabled on failure
                True,  # Keep sync button disabled on failure
                [],  # Empty sync controls
                True,  # Keep list activities button disabled on failure
                True,  # Keep import selected button disabled on failure
            )

    @app.callback(
        [
            Output("login-status", "children", allow_duplicate=True),
            Output("mfa-section", "children", allow_duplicate=True),
            Output("mfa-section", "style", allow_duplicate=True),
            Output("success-section", "children", allow_duplicate=True),
            Output("success-section", "style", allow_duplicate=True),
            Output("login-form", "style", allow_duplicate=True),
            Output("login-status-store", "data", allow_duplicate=True),
            Output("sync-period", "disabled", allow_duplicate=True),
            Output("sync-button", "disabled", allow_duplicate=True),
            Output("sync-controls", "children", allow_duplicate=True),
            Output("list-activities-button", "disabled", allow_duplicate=True),
            Output("import-selected-button", "disabled", allow_duplicate=True),
        ],
        [Input("mfa-verify-button", "n_clicks")],
        [State("mfa-code", "value"), State("login-status-store", "data")],
        prevent_initial_call=True,
    )
    def handle_mfa_verification(n_clicks, mfa_code, store_data):
        from dash import no_update

        if not ctx.triggered or not n_clicks:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        if not store_data.get("mfa_required"):
            # Create sync controls with disabled state for invalid MFA state
            sync_controls = [
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
                                    disabled=True,  # Keep disabled
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Action"),
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-sync me-2"),
                                        "Sync Activities",
                                    ],
                                    id="sync-button",
                                    color="success",
                                    size="lg",
                                    disabled=True,  # Keep disabled
                                ),
                            ],
                            width=6,
                        ),
                    ]
                ),
            ]

            return (
                dbc.Alert("Invalid MFA state.", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                store_data,
                True,  # Keep sync controls disabled
                True,  # Keep sync button disabled
                sync_controls,  # Keep sync controls with disabled components
                True,  # Keep list activities button disabled
                True,  # Keep import selected button disabled
            )

        if not mfa_code or len(mfa_code) != 6:
            # Create sync controls with disabled state for invalid MFA code
            sync_controls = [
                dbc.Alert(
                    "Please complete MFA authentication to enable data synchronization.",
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
                                    disabled=True,  # Keep disabled
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Action"),
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-sync me-2"),
                                        "Sync Activities",
                                    ],
                                    id="sync-button",
                                    color="success",
                                    size="lg",
                                    disabled=True,  # Keep disabled
                                ),
                            ],
                            width=6,
                        ),
                    ]
                ),
            ]

            return (
                dbc.Alert("Enter a valid 6-digit MFA code.", color="danger"),
                store_data.get("mfa_content", []),
                {"display": "block"},
                [],
                {"display": "none"},
                {"display": "none"},
                store_data,
                True,  # Keep sync controls disabled
                True,  # Keep sync button disabled
                sync_controls,  # Keep sync controls with disabled components
                True,  # Keep list activities button disabled
                True,  # Keep import selected button disabled
            )

        client = GarminConnectClient()
        email, password = store_data["email"], store_data["password"]

        mfa_context = None
        if store_data.get("mfa_context"):
            try:
                mfa_context = pickle.loads(base64.b64decode(store_data["mfa_context"]))
            except Exception as e:
                logger.error(f"Failed to deserialize MFA context: {e}")

        def web_mfa_callback():
            return mfa_code

        result = client.authenticate(
            email,
            password,
            mfa_callback=web_mfa_callback,
            remember_me=store_data.get("remember_me", False),
            mfa_context=mfa_context,
        )

        if result["status"] == "SUCCESS":
            success_content = [
                dbc.Alert(
                    [
                        html.H4("Login Successful!"),
                        html.P(f"Connected to Garmin account: {email}"),
                        html.Hr(),
                        html.P("You can now sync activities."),
                    ],
                    color="success",
                )
            ]

            # Enable sync controls after successful MFA verification
            sync_controls = [
                dbc.Alert(
                    "✅ Authenticated - You can now synchronize your activities.",
                    color="success",
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
                                    disabled=False,  # Enable the dropdown
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Action"),
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-sync me-2"),
                                        "Sync Activities",
                                    ],
                                    id="sync-button",
                                    color="success",
                                    size="lg",
                                    disabled=False,  # Enable the sync button
                                ),
                            ],
                            width=6,
                        ),
                    ]
                ),
            ]

            return (
                "",
                [],
                {"display": "none"},
                success_content,
                {},
                {"display": "none"},
                {"logged_in": True, "email": email},
                False,  # Enable sync period dropdown
                False,  # Enable sync button
                sync_controls,  # Enable sync controls
                False,  # Enable list activities button
                False,  # Enable import selected button
            )

        # Create sync controls with disabled state for MFA verification failure
        sync_controls = [
            dbc.Alert(
                "Please complete MFA authentication to enable data synchronization.",
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
                                disabled=True,  # Keep disabled
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Action"),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-sync me-2"),
                                    "Sync Activities",
                                ],
                                id="sync-button",
                                color="success",
                                size="lg",
                                disabled=True,  # Keep disabled
                            ),
                        ],
                        width=6,
                    ),
                ]
            ),
        ]

        return (
            dbc.Alert("MFA verification failed.", color="danger"),
            store_data.get("mfa_content", []),
            {"display": "block"},
            [],
            {"display": "none"},
            {"display": "none"},
            store_data,
            True,  # Keep sync controls disabled on MFA failure
            True,  # Keep sync button disabled on MFA failure
            sync_controls,  # Keep sync controls with disabled components
            True,  # Keep list activities button disabled on MFA failure
            True,  # Keep import selected button disabled on MFA failure
        )

    @app.callback(
        [
            Output("sync-status", "children"),
            Output("sync-progress", "children"),
            Output("sync-progress", "style"),
            Output("sync-button", "disabled", allow_duplicate=True),
        ],
        [Input("sync-button", "n_clicks")],
        [State("sync-period", "value")],
        prevent_initial_call=True,
    )
    def handle_sync_activities(n_clicks, sync_period):
        """Handle activity synchronization from Garmin Connect."""
        from datetime import datetime, timedelta
        import traceback

        if not ctx.triggered or not n_clicks:
            return "", [], {"display": "none"}, False

        try:
            # Show sync in progress
            progress_content = [
                dbc.Alert(
                    [
                        html.Div(
                            [
                                dbc.Spinner(size="sm", spinner_class_name="me-2"),
                                "Synchronizing activities from Garmin Connect...",
                            ],
                            className="d-flex align-items-center",
                        )
                    ],
                    color="info",
                    className="mb-3",
                )
            ]

            client = GarminConnectClient()

            # Check if client is authenticated
            if not client.is_authenticated():
                # Try to restore session
                restore_result = client.restore_session()
                if restore_result["status"] != "SUCCESS":
                    return (
                        dbc.Alert(
                            "Authentication required. Please login first.",
                            color="danger",
                        ),
                        [],
                        {"display": "none"},
                        False,  # Re-enable sync button
                    )

            # Calculate date range based on sync period
            end_date = datetime.now()
            if sync_period == "7":
                start_date = end_date - timedelta(days=7)
            elif sync_period == "30":
                start_date = end_date - timedelta(days=30)
            elif sync_period == "90":
                start_date = end_date - timedelta(days=90)
            else:  # "all"
                start_date = end_date - timedelta(days=365)  # Last year

            # Import sync function
            try:
                from garmin_client.garth_sync import sync_activities_from_garmin_connect
            except ImportError:
                # Create a simple sync using the existing client
                return (
                    dbc.Alert(
                        "Sync functionality not yet implemented. Coming soon!",
                        color="warning",
                    ),
                    [],
                    {"display": "none"},
                    False,  # Re-enable sync button
                )

            # Perform sync (this will be implemented in the next step)
            sync_result = sync_activities_from_garmin_connect(
                client=client,
                start_date=start_date,
                end_date=end_date,
            )

            # Show results
            if sync_result.get("success", False):
                status_content = dbc.Alert(
                    [
                        html.H5("✅ Sync Complete!", className="mb-3"),
                        html.P(f"Activities processed: {sync_result.get('activities_processed', 0)}"),
                        html.P(f"New activities: {sync_result.get('activities_new', 0)}"),
                        html.P(f"Updated activities: {sync_result.get('activities_updated', 0)}"),
                    ],
                    color="success",
                )
            else:
                error_msg = sync_result.get("error", "Unknown error occurred")
                status_content = dbc.Alert(
                    [
                        html.H5("❌ Sync Failed", className="mb-3"),
                        html.P(f"Error: {error_msg}"),
                    ],
                    color="danger",
                )

            return (
                status_content,
                [],
                {"display": "none"},
                False,  # Re-enable sync button
            )

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            logger.error(traceback.format_exc())

            return (
                dbc.Alert(
                    [
                        html.H5("❌ Sync Error", className="mb-3"),
                        html.P(f"An error occurred: {str(e)}"),
                    ],
                    color="danger",
                ),
                [],
                {"display": "none"},
                False,  # Re-enable sync button
            )

    @app.callback(
        [
            Output("activity-list-container", "children"),
            Output("list-activities-button", "disabled", allow_duplicate=True),
        ],
        [Input("list-activities-button", "n_clicks")],
        [State("sync-period", "value")],
        prevent_initial_call=True,
    )
    def list_available_activities(n_clicks, sync_period):
        """List available activities from Garmin Connect for selective import."""
        from datetime import datetime, timedelta

        if not ctx.triggered or not n_clicks:
            return [], False

        try:
            client = GarminConnectClient()

            # Check if client is authenticated
            if not client.is_authenticated():
                restore_result = client.restore_session()
                if restore_result["status"] != "SUCCESS":
                    return [
                        dbc.Alert(
                            "Authentication required. Please login first.",
                            color="danger",
                        )
                    ], False

            # Calculate date range based on sync period
            end_date = datetime.now()
            if sync_period == "7":
                start_date = end_date - timedelta(days=7)
            elif sync_period == "30":
                start_date = end_date - timedelta(days=30)
            elif sync_period == "90":
                start_date = end_date - timedelta(days=90)
            else:  # "all"
                start_date = end_date - timedelta(days=365)

            # For now, provide a placeholder implementation
            return [
                dbc.Alert(
                    "Activity listing functionality is in development. Please use the main 'Sync Activities' button for now.",
                    color="info",
                )
            ], False

        except Exception as e:
            logger.error(f"Failed to list activities: {e}")
            return [
                dbc.Alert(
                    f"Error listing activities: {str(e)}",
                    color="danger",
                )
            ], False

    @app.callback(
        [
            Output("import-status", "children"),
            Output("import-selected-button", "disabled", allow_duplicate=True),
        ],
        [Input("import-selected-button", "n_clicks")],
        [State("activity-list-container", "children")],
        prevent_initial_call=True,
    )
    def import_selected_activities(n_clicks, activity_cards):
        """Import selected activities from the activity list."""

        if not ctx.triggered or not n_clicks:
            return "", False

        try:
            return [
                dbc.Alert(
                    "Selective import functionality is in development. Please use the main 'Sync Activities' button for now.",
                    color="info",
                )
            ], False

        except Exception as e:
            logger.error(f"Failed to import selected activities: {e}")
            return [
                dbc.Alert(
                    f"Error importing activities: {str(e)}",
                    color="danger",
                )
            ], False
