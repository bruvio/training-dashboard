"""
FIT File Upload Page - Upload and import FIT files directly from the web interface.
"""

import base64
from datetime import datetime
import io
import logging
from pathlib import Path

from dash import Input, Output, State, ctx, dcc, html
import dash_bootstrap_components as dbc

from app.data.db import session_scope
from app.data.models import Activity, Lap, RoutePoint, Sample
from ingest.parser import ActivityParser, CorruptFileError, FileNotSupportedError

logger = logging.getLogger(__name__)

# This page uses manual routing - no registration needed


def layout():
    """Layout for FIT file upload page."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(
                                [html.I(className="fas fa-file-upload me-3"), "Import FIT Files"],
                                className="mb-4",
                            ),
                            html.P(
                                "Upload FIT files directly from your Garmin device to analyze your workouts. "
                                "Supports multiple file selection and automatic parsing with progress tracking.",
                                className="text-muted mb-4",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Upload section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5("File Upload", className="mb-0"),
                                            html.Small(
                                                "Drag and drop FIT files or click to select",
                                                className="text-muted d-block mt-1",
                                            ),
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # File upload component
                                            dcc.Upload(
                                                id="fit-file-upload",
                                                children=html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-cloud-upload-alt fa-3x mb-3 text-primary"
                                                        ),
                                                        html.H4("Drop FIT files here", className="mb-2"),
                                                        html.P(
                                                            "or click to select files from your computer",
                                                            className="text-muted",
                                                        ),
                                                        html.Small(
                                                            "Supported formats: .FIT (recommended), .TCX, .GPX",
                                                            className="text-muted",
                                                        ),
                                                    ],
                                                    className="text-center py-5",
                                                ),
                                                style={
                                                    "width": "100%",
                                                    "height": "200px",
                                                    "lineHeight": "200px",
                                                    "borderWidth": "2px",
                                                    "borderStyle": "dashed",
                                                    "borderRadius": "10px",
                                                    "borderColor": "#dee2e6",
                                                    "textAlign": "center",
                                                    "background": "#f8f9fa",
                                                    "cursor": "pointer",
                                                },
                                                style_active={
                                                    "borderColor": "#007bff",
                                                    "background": "rgba(0,123,255,0.05)",
                                                },
                                                multiple=True,  # Allow multiple file selection
                                            ),
                                            # Upload options
                                            html.Hr(className="my-4"),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Checkbox(
                                                                id="force-reimport",
                                                                label="Force reimport (overwrite existing activities)",
                                                                value=False,
                                                            )
                                                        ],
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Button(
                                                                [
                                                                    html.I(className="fas fa-times me-2"),
                                                                    "Clear Files",
                                                                ],
                                                                id="clear-files-btn",
                                                                color="outline-secondary",
                                                                size="sm",
                                                                className="float-end",
                                                            )
                                                        ],
                                                        width=6,
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    )
                ]
            ),
            # File list and progress section
            html.Div(id="upload-file-list", className="mt-4"),
            # Upload progress
            html.Div(id="upload-progress", className="mt-4"),
            # Results section
            html.Div(id="upload-results", className="mt-4"),
            # Action buttons - separate container to prevent upload interference
            html.Hr(className="my-4"),
            html.Div(
                [
                    dbc.Container(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Button(
                                                [html.I(className="fas fa-arrow-left me-2"), "Back to Activities"],
                                                href="/",
                                                color="outline-primary",
                                                className="me-2",
                                            ),
                                            html.Button(
                                                [html.I(className="fas fa-sync me-2"), "Process Files"],
                                                id="process-files-btn",
                                                className="btn btn-primary",
                                                disabled=True,
                                                style={
                                                    "pointerEvents": "auto",
                                                    "zIndex": 1000,
                                                    "position": "relative",
                                                },
                                                n_clicks=0,
                                                type="button",
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        className="mt-4",
                        fluid=False,
                    )
                ],
                style={"position": "relative", "zIndex": 999, "background": "white"},
                className="py-3",
            ),
            # Store for uploaded files data
            dcc.Store(id="uploaded-files-store", data=[]),
        ],
        fluid=True,
    )


def register_callbacks(app):
    """Register callbacks for the upload page."""

    @app.callback(
        [
            Output("upload-file-list", "children"),
            Output("uploaded-files-store", "data"),
            Output("process-files-btn", "disabled"),
        ],
        [Input("fit-file-upload", "contents"), Input("clear-files-btn", "n_clicks")],
        [State("fit-file-upload", "filename"), State("uploaded-files-store", "data")],
        prevent_initial_call=True,
    )
    def handle_file_selection(contents, clear_clicks, filenames, stored_files):
        """Handle file selection and display file list."""
        if ctx.triggered_id == "clear-files-btn":
            # Clear all files
            return [], [], True

        if not contents:
            return [], [], True

        # Process uploaded files
        file_data = []
        for content, filename in zip(contents, filenames):
            # Decode base64 content
            content_type, content_string = content.split(",")
            decoded = base64.b64decode(content_string)

            file_info = {
                "name": filename,
                "content": content_string,
                "size": len(decoded),
                "type": Path(filename).suffix.lower(),
            }
            file_data.append(file_info)

        # Create file list display
        file_cards = []
        for i, file_info in enumerate(file_data):
            size_mb = file_info["size"] / (1024 * 1024)
            file_type = file_info["type"].upper()

            # Determine file type icon and color
            if file_info["type"] in [".fit"]:
                icon = "fas fa-file-code"
                color = "success"
            elif file_info["type"] in [".tcx", ".gpx"]:
                icon = "fas fa-file-alt"
                color = "info"
            else:
                icon = "fas fa-file"
                color = "warning"

            card = dbc.Card(
                [
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.I(className=f"{icon} fa-2x text-{color}"),
                                        ],
                                        width=2,
                                        className="text-center",
                                    ),
                                    dbc.Col(
                                        [
                                            html.H6(file_info["name"], className="mb-1"),
                                            html.Small(
                                                f"{file_type} file • {size_mb:.1f} MB",
                                                className="text-muted",
                                            ),
                                        ],
                                        width=8,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Badge(
                                                "Ready",
                                                color="success",
                                                pill=True,
                                            )
                                        ],
                                        width=2,
                                        className="text-center",
                                    ),
                                ]
                            )
                        ]
                    )
                ],
                className="mb-2",
            )
            file_cards.append(card)

        file_list_content = [
            html.H5(f"{len(file_data)} Files Selected", className="mb-3"),
            html.Div(file_cards),
        ]

        return file_list_content, file_data, False

    @app.callback(
        [Output("upload-progress", "children"), Output("upload-results", "children")],
        [Input("process-files-btn", "n_clicks")],
        [State("uploaded-files-store", "data"), State("force-reimport", "value")],
        prevent_initial_call=True,
    )
    def process_uploaded_files(n_clicks, file_data, force_reimport):
        """Process the uploaded FIT files."""
        logger.info(
            f"Process files callback triggered: n_clicks={n_clicks}, file_data_len={len(file_data) if file_data else 0}"
        )

        if not n_clicks or n_clicks == 0 or not file_data:
            logger.info("Not processing - no clicks or no file data")
            return "", ""

        results = {"imported": 0, "skipped": 0, "errors": 0, "duplicates": 0, "error_details": []}

        # Create progress bar
        progress_content = [
            html.H5("Processing Files...", className="mb-3"),
            dbc.Progress(id="process-progress", value=0, className="mb-3"),
            html.Div(id="process-status"),
        ]

        # Process each file
        for i, file_info in enumerate(file_data):
            try:
                # Update progress (this is simplified - in a real app you'd use callbacks for real-time updates)
                _ = ((i + 1) / len(file_data)) * 100

                # Decode file content
                decoded_content = base64.b64decode(file_info["content"])

                # Create temporary file-like object
                file_like = io.BytesIO(decoded_content)

                # Process the file using existing import logic
                result = import_file_from_content(file_like, file_info["name"], force_reimport)

                if result["success"]:
                    results["imported"] += 1
                elif result.get("reason") == "duplicate":
                    results["duplicates"] += 1
                else:
                    results["skipped"] += 1

            except Exception as e:
                results["errors"] += 1
                results["error_details"].append({"file": file_info["name"], "error": str(e)})
                logger.error(f"Error processing {file_info['name']}: {e}")

        # Create results display
        results_content = create_results_display(results)

        # Update progress to complete
        progress_content = [
            html.H5("Processing Complete!", className="mb-3 text-success"),
            dbc.Progress(value=100, color="success", className="mb-3"),
        ]

        return progress_content, results_content


def import_file_from_content(file_content: io.BytesIO, filename: str, force_reimport: bool = False) -> dict:
    """Import a single file from its content."""
    try:
        # Calculate file hash for deduplication
        file_content.seek(0)
        content_bytes = file_content.read()
        file_content.seek(0)

        # Simple hash calculation (you might want to use a more robust method)
        import hashlib

        file_hash = hashlib.md5(content_bytes).hexdigest()

        with session_scope() as session:
            # Check for existing import (unless forcing reimport)
            if not force_reimport:
                existing = session.query(Activity).filter_by(file_hash=file_hash).first()
                if existing:
                    logger.debug(f"Skipping duplicate: {filename}")
                    return {"success": False, "reason": "duplicate"}

            # Create a temporary file for parsing
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix) as temp_file:
                temp_file.write(content_bytes)
                temp_file.flush()

                # Parse the activity file using existing parser
                activity_data = ActivityParser.parse_activity_file(Path(temp_file.name))
                if not activity_data:
                    return {"success": False, "reason": "no_data"}

            # Create Activity object (similar to CLI import logic)
            activity = Activity(
                external_id=activity_data.external_id or Path(filename).stem,
                file_hash=file_hash,
                source=Path(filename).suffix[1:].lower(),
                sport=activity_data.sport or "unknown",
                sub_sport=activity_data.sub_sport,
                start_time_utc=activity_data.start_time_utc or datetime.now(),
                elapsed_time_s=activity_data.elapsed_time_s or 0,
                moving_time_s=activity_data.moving_time_s,
                distance_m=activity_data.distance_m,
                avg_speed_mps=activity_data.avg_speed_mps,
                avg_pace_s_per_km=activity_data.avg_pace_s_per_km,
                avg_hr=activity_data.avg_hr,
                max_hr=activity_data.max_hr,
                avg_power_w=activity_data.avg_power_w,
                max_power_w=activity_data.max_power_w,
                elevation_gain_m=activity_data.elevation_gain_m,
                elevation_loss_m=activity_data.elevation_loss_m,
                calories=activity_data.calories,
                file_path=filename,  # Store original filename
            )

            session.add(activity)
            session.flush()  # Get the activity ID

            # Add samples if present
            if activity_data.samples:
                for sample_data in activity_data.samples:
                    if sample_data.timestamp:
                        sample = Sample(
                            activity_id=activity.id,
                            timestamp=sample_data.timestamp,
                            elapsed_time_s=sample_data.elapsed_time_s or 0,
                            latitude=sample_data.latitude,
                            longitude=sample_data.longitude,
                            altitude_m=sample_data.altitude_m,
                            heart_rate=sample_data.heart_rate,
                            power_w=sample_data.power_w,
                            cadence_rpm=sample_data.cadence_rpm,
                            speed_mps=sample_data.speed_mps,
                            temperature_c=sample_data.temperature_c,
                            # Advanced running dynamics
                            vertical_oscillation_mm=sample_data.vertical_oscillation_mm,
                            vertical_ratio=sample_data.vertical_ratio,
                            ground_contact_time_ms=sample_data.ground_contact_time_ms,
                            ground_contact_balance_pct=sample_data.ground_contact_balance_pct,
                            step_length_mm=sample_data.step_length_mm,
                            air_power_w=sample_data.air_power_w,
                            form_power_w=sample_data.form_power_w,
                            leg_spring_stiffness=sample_data.leg_spring_stiffness,
                            impact_loading_rate=sample_data.impact_loading_rate,
                            stryd_temperature_c=sample_data.stryd_temperature_c,
                            stryd_humidity_pct=sample_data.stryd_humidity_pct,
                        )
                        session.add(sample)

            # Add route points if present
            if activity_data.route_points:
                for i, (lat, lon, alt) in enumerate(activity_data.route_points):
                    if lat is not None and lon is not None:
                        route_point = RoutePoint(
                            activity_id=activity.id, sequence=i, latitude=lat, longitude=lon, altitude_m=alt
                        )
                        session.add(route_point)

            # Add laps if present
            if activity_data.laps:
                for lap_data in activity_data.laps:
                    lap = Lap(
                        activity_id=activity.id,
                        lap_index=lap_data.lap_index,
                        start_time_utc=lap_data.start_time_utc,
                        elapsed_time_s=lap_data.elapsed_time_s or 0,
                        moving_time_s=lap_data.elapsed_time_s,
                        distance_m=lap_data.distance_m,
                        avg_speed_mps=lap_data.avg_speed_mps,
                        avg_hr=lap_data.avg_hr,
                        max_hr=lap_data.max_hr,
                        avg_power_w=lap_data.avg_power_w,
                        max_power_w=lap_data.max_power_w,
                    )
                    session.add(lap)

            # Commit all changes
            session.commit()

            logger.info(f"Successfully imported {filename}")
            return {"success": True, "activity_id": activity.id}

    except (FileNotSupportedError, CorruptFileError) as e:
        logger.debug(f"Parse error for {filename}: {e}")
        return {"success": False, "reason": f"parse_error: {e}"}
    except Exception as e:
        logger.error(f"Import error for {filename}: {e}")
        return {"success": False, "reason": f"import_error: {e}"}


def create_results_display(results: dict) -> list:
    """Create a display for import results."""
    content = [
        html.H5("Import Results", className="mb-3"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H3(str(results["imported"]), className="text-success mb-1"),
                                        html.P("Imported", className="mb-0 text-muted"),
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
                                        html.H3(str(results["duplicates"]), className="text-warning mb-1"),
                                        html.P("Duplicates", className="mb-0 text-muted"),
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
                                        html.H3(str(results["skipped"]), className="text-info mb-1"),
                                        html.P("Skipped", className="mb-0 text-muted"),
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
                                        html.H3(str(results["errors"]), className="text-danger mb-1"),
                                        html.P("Errors", className="mb-0 text-muted"),
                                    ],
                                    className="text-center",
                                )
                            ]
                        )
                    ],
                    width=3,
                ),
            ],
            className="mb-4",
        ),
    ]

    # Add error details if any
    if results["errors"] > 0 and results["error_details"]:
        error_items = []
        for error in results["error_details"][:5]:  # Show first 5 errors
            error_items.append(html.Li([html.Strong(error["file"]), f": {error['error']}"], className="text-danger"))

        if len(results["error_details"]) > 5:
            error_items.append(
                html.Li(f"... and {len(results['error_details']) - 5} more errors", className="text-muted")
            )

        content.append(
            dbc.Alert(
                [
                    html.H6("Import Errors:", className="alert-heading"),
                    html.Ul(error_items, className="mb-0"),
                ],
                color="warning",
                className="mt-3",
            )
        )

    # Success message
    if results["imported"] > 0:
        content.append(
            dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"Successfully imported {results['imported']} activities! ",
                    html.A("View activities", href="/", className="alert-link"),
                ],
                color="success",
                className="mt-3",
            )
        )

    return content
