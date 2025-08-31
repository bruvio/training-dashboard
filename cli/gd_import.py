"""
Garmin Dashboard Activity Importer CLI.

Typer-based CLI with Rich progress bars following PRP specifications.
Supports FIT, TCX, GPX files with comprehensive error handling and deduplication.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
)
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

# Import our modules
from app.data.db import init_database, session_scope, get_db_config
from app.data.models import Activity, Sample, RoutePoint, Lap, ImportResult
from ingest.parser import ActivityParser, FileNotSupportedError, CorruptFileError, calculate_file_hash

# Initialize Rich console
console = Console()

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

# Create Typer app
app = typer.Typer(
    name="gd-import",
    help="🏃 Garmin Dashboard Activity Importer - Import activities from FIT/TCX/GPX files",
    epilog="For more information, visit: https://github.com/your-repo/garmin-dashboard",
)


@app.command()
def import_activities(
    data_dir: Path = typer.Argument(
        ...,
        help="📁 Directory containing activity files (FIT/TCX/GPX)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    garmin_db: Optional[Path] = typer.Option(
        None,
        "--garmin-db",
        help="🔗 Path to existing GarminDB SQLite file (optional)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    force_reimport: bool = typer.Option(False, "--force", help="🔄 Reimport all files, ignoring duplicates"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="📝 Enable verbose logging"),
    database_url: Optional[str] = typer.Option(
        None, "--database-url", help="🗄️ Custom database URL (default: sqlite:///garmin_dashboard.db)"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="🧪 Preview what would be imported without making changes"),
):
    """
    Import activity files from directory with progress tracking and error handling.

    🎯 Supports FIT, TCX, and GPX files with automatic parsing and deduplication.
    ⚡ Features Rich progress bars and comprehensive error reporting.
    """

    # Configure logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Display welcome message
    console.print(
        Panel.fit(
            f"🏃 [bold blue]Garmin Dashboard Activity Importer[/bold blue]\n"
            f"📂 Source: [green]{data_dir}[/green]\n"
            f"🔄 Force reimport: [yellow]{force_reimport}[/yellow]\n"
            f"🧪 Dry run: [yellow]{dry_run}[/yellow]",
            title="Import Configuration",
        )
    )

    # Validate data directory
    if not data_dir.exists() or not data_dir.is_dir():
        console.print(f"❌ [red]Error:[/red] Directory {data_dir} does not exist or is not a directory")
        raise typer.Exit(1)

    # Initialize database (skip if dry run)
    if not dry_run:
        try:
            db_config = init_database(database_url)
            console.print(f"✅ Database initialized: [green]{db_config.database_url}[/green]")
        except Exception as e:
            console.print(f"❌ [red]Database Error:[/red] {e}")
            raise typer.Exit(1)
    else:
        console.print("🧪 [yellow]Dry run mode - no database operations[/yellow]")

    # Scan for activity files
    console.print("\n🔍 [bold]Scanning for activity files...[/bold]")
    activity_files = scan_activity_files(data_dir)

    if not activity_files:
        console.print(f"⚠️ [yellow]No activity files found in {data_dir}[/yellow]")
        console.print("📝 Supported formats: .fit, .tcx, .gpx")
        raise typer.Exit(0)

    # Display scan results
    file_stats = analyze_files(activity_files)
    display_scan_results(file_stats)

    if dry_run:
        console.print("\n🧪 [yellow]Dry run complete - no files imported[/yellow]")
        raise typer.Exit(0)

    # Import files with progress tracking
    import_results = import_files_with_progress(activity_files, force_reimport=force_reimport)

    # Display final results
    display_import_results(import_results)

    # Optional: Handle GarminDB integration
    if garmin_db:
        console.print(f"\n🔗 [yellow]GarminDB integration not yet implemented[/yellow]")
        console.print(f"📝 Planned for future release: {garmin_db}")


def scan_activity_files(data_dir: Path) -> List[Path]:
    """
    Recursively scan directory for supported activity files.

    Args:
        data_dir: Directory to scan

    Returns:
        List of activity file paths
    """
    supported_extensions = {".fit", ".tcx", ".gpx"}
    activity_files = []

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True
    ) as progress:
        scan_task = progress.add_task("Scanning files...", total=None)

        for extension in supported_extensions:
            pattern = f"*{extension}"
            files = list(data_dir.rglob(pattern))
            activity_files.extend(files)

            # Also check uppercase extensions
            pattern_upper = f"*{extension.upper()}"
            files_upper = list(data_dir.rglob(pattern_upper))
            activity_files.extend(files_upper)

        progress.update(scan_task, description=f"Found {len(activity_files)} files")

    return sorted(activity_files)


def analyze_files(files: List[Path]) -> dict:
    """
    Analyze file types and sizes.

    Args:
        files: List of file paths

    Returns:
        Dictionary with file statistics
    """
    stats = {"total": len(files), "by_type": {}, "total_size": 0, "largest_file": None, "largest_size": 0}

    for file_path in files:
        try:
            size = file_path.stat().st_size
            stats["total_size"] += size

            if size > stats["largest_size"]:
                stats["largest_file"] = file_path
                stats["largest_size"] = size

            ext = file_path.suffix.lower()
            stats["by_type"][ext] = stats["by_type"].get(ext, 0) + 1

        except OSError:
            continue

    return stats


def display_scan_results(stats: dict):
    """
    Display file scan results in formatted table.

    Args:
        stats: File statistics dictionary
    """
    table = Table(title="📊 Scan Results")
    table.add_column("File Type", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right", style="magenta")
    table.add_column("Percentage", justify="right", style="green")

    for ext, count in stats["by_type"].items():
        percentage = (count / stats["total"]) * 100
        table.add_row(ext.upper(), str(count), f"{percentage:.1f}%")

    console.print(table)

    # Display summary
    size_mb = stats["total_size"] / (1024 * 1024)
    console.print(f"📁 Total files: [bold]{stats['total']}[/bold]")
    console.print(f"💾 Total size: [bold]{size_mb:.1f} MB[/bold]")

    if stats["largest_file"]:
        largest_mb = stats["largest_size"] / (1024 * 1024)
        console.print(f"📄 Largest file: [bold]{stats['largest_file'].name}[/bold] ({largest_mb:.1f} MB)")


def import_files_with_progress(files: List[Path], force_reimport: bool = False) -> dict:
    """
    Import files with Rich progress bars and error handling.

    Args:
        files: List of file paths to import
        force_reimport: Whether to force reimport of duplicates

    Returns:
        Dictionary with import results
    """
    results = {"imported": 0, "skipped": 0, "errors": 0, "duplicates": 0, "error_details": []}

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        import_task = progress.add_task("Importing activities...", total=len(files))

        for file_path in files:
            try:
                # Update progress with current file
                progress.update(import_task, description=f"Importing {file_path.name}...")

                # Import the file
                result = import_single_file(file_path, force_reimport)

                # Update counters
                if result.imported:
                    results["imported"] += 1
                elif result.reason == "duplicate":
                    results["duplicates"] += 1
                else:
                    results["skipped"] += 1

            except Exception as e:
                results["errors"] += 1
                results["error_details"].append({"file": str(file_path), "error": str(e)})
                logger.warning(f"⚠️ Error importing {file_path.name}: {e}")

            progress.advance(import_task)

        progress.update(import_task, description="Import complete!")

    return results


def import_single_file(file_path: Path, force_reimport: bool = False) -> ImportResult:
    """
    Import a single activity file with comprehensive error handling.

    Args:
        file_path: Path to activity file
        force_reimport: Whether to force reimport of duplicates

    Returns:
        ImportResult indicating success/failure
    """
    try:
        # Calculate file hash for deduplication
        file_hash = calculate_file_hash(file_path)

        with session_scope() as session:
            # Check for existing import (unless forcing reimport)
            if not force_reimport:
                existing = session.query(Activity).filter_by(file_hash=file_hash).first()
                if existing:
                    logger.debug(f"Skipping duplicate: {file_path.name}")
                    return ImportResult(imported=False, reason="duplicate")

            # Parse the activity file
            try:
                activity_data = ActivityParser.parse_activity_file(file_path)
                if not activity_data:
                    return ImportResult(imported=False, reason="no_data")

            except (FileNotSupportedError, CorruptFileError) as e:
                logger.debug(f"Parse error for {file_path}: {e}")
                return ImportResult(imported=False, reason=f"parse_error: {e}")

            # Create Activity object
            activity = Activity(
                external_id=activity_data.external_id or file_path.stem,
                file_hash=file_hash,
                source=file_path.suffix[1:].lower(),  # Remove dot and lowercase
                sport=activity_data.sport or "unknown",
                sub_sport=activity_data.sub_sport,
                start_time_utc=activity_data.start_time_utc or datetime.now(timezone.utc),
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
                file_path=str(file_path),
            )

            session.add(activity)
            session.flush()  # Get the activity ID

            # Add samples if present
            if activity_data.samples:
                for sample_data in activity_data.samples:
                    if sample_data.timestamp:  # Only add samples with timestamps
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
                        moving_time_s=lap_data.elapsed_time_s,  # Use elapsed as fallback
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

            logger.debug(f"Successfully imported {file_path.name}")
            return ImportResult(imported=True, activity_id=activity.id)

    except Exception as e:
        logger.error(f"Import error for {file_path}: {e}")
        return ImportResult(imported=False, reason=f"import_error: {e}")


def display_import_results(results: dict):
    """
    Display final import results with Rich formatting.

    Args:
        results: Import results dictionary
    """
    console.print("\n" + "=" * 50)
    console.print("🎉 [bold green]Import Complete![/bold green]")
    console.print("=" * 50)

    # Create results table
    table = Table(title="📈 Import Summary")
    table.add_column("Result", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right", style="magenta")

    table.add_row("✅ Imported", str(results["imported"]))
    table.add_row("⏭️ Skipped", str(results["skipped"]))
    table.add_row("🔄 Duplicates", str(results["duplicates"]))
    table.add_row("❌ Errors", str(results["errors"]))

    console.print(table)

    # Display errors if any
    if results["errors"] > 0:
        console.print(f"\n⚠️ [yellow]{results['errors']} errors occurred:[/yellow]")
        for error in results["error_details"][:5]:  # Show first 5 errors
            console.print(f"  • {Path(error['file']).name}: {error['error']}")

        if len(results["error_details"]) > 5:
            console.print(f"  ... and {len(results['error_details']) - 5} more")

    # Show database statistics
    if results["imported"] > 0:
        try:
            db_config = get_db_config()
            db_info = db_config.get_database_info()
            console.print(f"\n📊 [bold]Database Statistics:[/bold]")
            console.print(f"  Activities: {db_info['activities']}")
            console.print(f"  Samples: {db_info['samples']}")
            console.print(f"  Route Points: {db_info['route_points']}")
        except Exception as e:
            logger.debug(f"Could not get database statistics: {e}")


@app.command()
def status():
    """
    📊 Show database status and statistics.
    """
    try:
        db_config = get_db_config()
        db_info = db_config.get_database_info()

        console.print(
            Panel.fit(
                f"🗄️ Database: [green]{db_info['database_url']}[/green]\n"
                f"📊 Activities: [bold]{db_info['activities']}[/bold]\n"
                f"📈 Samples: [bold]{db_info['samples']}[/bold]\n"
                f"🗺️ Route Points: [bold]{db_info['route_points']}[/bold]\n"
                f"🏃 Laps: [bold]{db_info['laps']}[/bold]",
                title="Database Status",
            )
        )

    except Exception as e:
        console.print(f"❌ [red]Error getting database status:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
