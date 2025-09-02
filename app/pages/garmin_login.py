"""
Garmin Connect login and data synchronization page.
"""

import logging
import pickle
import base64
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
    def handle_garmin_login(n_clicks, email, password, remember_me, store_data):
        if not ctx.triggered or not n_clicks:
            return "", [], {"display": "none"}, [], {"display": "none"}, {}, {}

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

        client = GarminConnectClient()
        result = client.authenticate(email, password, remember_me=remember_me)

        if result["status"] == "MFA_REQUIRED":
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
                dbc.Alert("Authentication failed. Check credentials.", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                {},
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
        ],
        [Input("mfa-verify-button", "n_clicks")],
        [State("mfa-code", "value"), State("login-status-store", "data")],
        prevent_initial_call=True,
    )
    def handle_mfa_verification(n_clicks, mfa_code, store_data):
        if not ctx.triggered or not n_clicks:
            return "", [], {"display": "none"}, [], {"display": "none"}, {}, {}

        if not store_data.get("mfa_required"):
            return (
                dbc.Alert("Invalid MFA state.", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                store_data,
            )

        if not mfa_code or len(mfa_code) != 6:
            return (
                dbc.Alert("Enter a valid 6-digit MFA code.", color="danger"),
                store_data.get("mfa_content", []),
                {"display": "block"},
                [],
                {"display": "none"},
                {"display": "none"},
                store_data,
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
            return (
                "",
                [],
                {"display": "none"},
                success_content,
                {},
                {"display": "none"},
                {"logged_in": True, "email": email},
            )

        return (
            dbc.Alert("MFA verification failed.", color="danger"),
            store_data.get("mfa_content", []),
            {"display": "block"},
            [],
            {"display": "none"},
            {"display": "none"},
            store_data,
        )
