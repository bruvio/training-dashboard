"""
FIT File Upload Page - Upload and import FIT files directly from the web interface.
Fixed version that processes files immediately on upload (proper Dash pattern).
"""

import base64
from datetime import datetime
import hashlib
import io
import logging
from pathlib import Path
import tempfile

from dash import Input, Output, State, callback, ctx, dcc, html
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
                                "Files will be processed immediately after selection.",
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
                                                "Drag and drop FIT files or click to select - files will be imported immediately",
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
                                                        width=8,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Button(
                                                                [
                                                                    html.I(className="fas fa-arrow-left me-2"),
                                                                    "Back to Activities",
                                                                ],
                                                                href="/",
                                                                color="outline-primary",
                                                                size="sm",
                                                            )
                                                        ],
                                                        width=4,
                                                        className="text-end",
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
        ],
        fluid=True,
    )


def register_callbacks(app):
    """Register callbacks for the upload page."""

    @app.callback(
        [
            Output("upload-file-list", "children"),
            Output("upload-progress", "children"),
            Output("upload-results", "children"),
        ],
        [Input("fit-file-upload", "contents")],
        [State("fit-file-upload", "filename"), State("force-reimport", "value")],
        prevent_initial_call=True,
    )
    def handle_file_upload(contents, filenames, force_reimport):
        """Handle file upload and immediate processing."""

        if not contents or not filenames:
            return [], "", ""

        logger.info(f"Processing {len(contents)} uploaded files")

        # Show initial progress
        progress_content = [
            html.H5("Processing Files...", className="mb-3"),
            dbc.Progress(value=20, color="primary", className="mb-3"),
            html.P("Parsing and importing files...", className="text-muted"),
        ]

        results = {"imported": 0, "skipped": 0, "errors": 0, "duplicates": 0, "error_details": []}
        file_list_items = []

        # Process each uploaded file immediately
        for i, (content, filename) in enumerate(zip(contents, filenames)):
            try:
                # Decode base64 content
                content_type, content_string = content.split(",")
                decoded_content = base64.b64decode(content_string)

                size_mb = len(decoded_content) / (1024 * 1024)
                file_type = Path(filename).suffix.upper()

                # Process the file using existing import logic
                file_like = io.BytesIO(decoded_content)
                result = import_file_from_content(file_like, filename, force_reimport)

                # Determine status and icon
                if result["success"]:
                    results["imported"] += 1
                    status = "Imported"
                    status_color = "success"
                    icon = "fas fa-check-circle"
                    detail = f"Activity ID: {result.get('activity_id', 'Unknown')}"
                elif result.get("reason") == "duplicate":
                    results["duplicates"] += 1
                    status = "Duplicate"
                    status_color = "warning"
                    icon = "fas fa-exclamation-triangle"
                    detail = "Already exists in database"
                else:
                    results["skipped"] += 1
                    status = "Skipped"
                    status_color = "secondary"
                    icon = "fas fa-minus-circle"
                    detail = result.get("reason", "Unknown reason")

            except Exception as e:
                results["errors"] += 1
                results["error_details"].append({"file": filename, "error": str(e)})
                logger.error(f"Error processing {filename}: {e}")
                status = "Error"
                status_color = "danger"
                icon = "fas fa-times-circle"
                size_mb = 0
                file_type = "UNKNOWN"
                detail = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)

            # Create file item display
            file_item = dbc.ListGroupItem(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [html.I(className=f"{icon} fa-lg text-{status_color}")],
                                width=1,
                                className="text-center",
                            ),
                            dbc.Col(
                                [
                                    html.H6(filename, className="mb-1"),
                                    html.Small(f"{file_type} • {size_mb:.1f} MB", className="text-muted d-block"),
                                    html.Small(detail, className="text-muted"),
                                ],
                                width=9,
                            ),
                            dbc.Col(
                                [
                                    dbc.Badge(status, color=status_color, pill=True),
                                ],
                                width=2,
                                className="text-end",
                            ),
                        ],
                        align="center",
                    )
                ],
                className="py-2",
            )
            file_list_items.append(file_item)

        # Create file list display
        file_list_content = [
            html.H5(f"{len(contents)} Files Processed", className="mb-3"),
            dbc.ListGroup(file_list_items),
        ]

        # Create results display
        results_content = create_results_display(results)

        # Final progress
        final_progress = [
            html.H5("Import Complete!", className="mb-3 text-success"),
            dbc.Progress(value=100, color="success", className="mb-3"),
        ]

        return file_list_content, final_progress, results_content


def import_file_from_content(file_content: io.BytesIO, filename: str, force_reimport: bool = False) -> dict:
    """Import a single file from its content."""
    try:
        # Calculate file hash for deduplication
        file_content.seek(0)
        content_bytes = file_content.read()
        file_content.seek(0)

        file_hash = hashlib.md5(content_bytes).hexdigest()

        with session_scope() as session:
            # Check for existing import (unless forcing reimport)
            if not force_reimport:
                existing = session.query(Activity).filter_by(file_hash=file_hash).first()
                if existing:
                    logger.debug(f"Skipping duplicate: {filename}")
                    return {"success": False, "reason": "duplicate"}

            # Create a temporary file for parsing
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
        html.H5("Import Summary", className="mb-3"),
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
                                    className="text-center py-2",
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
                                    className="text-center py-2",
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
                                    className="text-center py-2",
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
                                    className="text-center py-2",
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
