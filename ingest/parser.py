"""
Unified ActivityParser class with error handling for Garmin Dashboard.

Research-based implementation supporting FIT, TCX, and GPX file formats
with comprehensive error handling and data normalization.
"""

import logging
import hashlib
from pathlib import Path
from typing import Optional

# File format parsers (research-validated)
try:
    import fitparse

    FITPARSE_AVAILABLE = True
except ImportError:
    FITPARSE_AVAILABLE = False
    logging.warning("fitparse not available - FIT file support disabled")

try:
    import tcxparser

    TCXPARSER_AVAILABLE = True
except ImportError:
    TCXPARSER_AVAILABLE = False
    logging.warning("tcxparser not available - TCX file support disabled")

try:
    import gpxpy

    GPXPY_AVAILABLE = True
except ImportError:
    GPXPY_AVAILABLE = False
    logging.warning("gpxpy not available - GPX file support disabled")

from app.data.models import ActivityData, SampleData, LapData

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Base exception for parsing errors."""


class FileNotSupportedError(ParserError):
    """Raised when file format is not supported."""


class CorruptFileError(ParserError):
    """Raised when file is corrupt or unreadable."""


class ActivityParser:
    """
    Unified activity file parser with error handling.

    Supports FIT, TCX, and GPX files following research-validated patterns
    from the enhanced PRP specification.
    """

    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """
        Calculate SHA-256 hash of file for deduplication.

        Args:
            file_path: Path to the file

        Returns:
            Hex string hash of file contents
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except (OSError, IOError) as e:
            raise CorruptFileError(f"Cannot read file {file_path}: {e}")

    @staticmethod
    def parse_activity_file(file_path: Path) -> Optional[ActivityData]:
        """
        Parse activity file based on extension with unified error handling.

        Args:
            file_path: Path to activity file

        Returns:
            ActivityData object or None if parsing fails

        Raises:
            FileNotSupportedError: If file format is not supported
            CorruptFileError: If file is corrupt or unreadable
        """
        if not file_path.exists():
            raise CorruptFileError(f"File does not exist: {file_path}")

        suffix = file_path.suffix.lower()

        try:
            if suffix == ".fit":
                return ActivityParser.parse_fit_file(file_path)
            elif suffix == ".tcx":
                return ActivityParser.parse_tcx_file(file_path)
            elif suffix == ".gpx":
                return ActivityParser.parse_gpx_file(file_path)
            else:
                raise FileNotSupportedError(
                    f"Unsupported file format: {suffix}. " "Supported formats: .fit, .tcx, .gpx"
                )
        except Exception as e:
            if isinstance(e, (FileNotSupportedError, CorruptFileError)):
                raise
            else:
                logger.warning(f"Parsing error for {file_path}: {e}")
                raise CorruptFileError(f"Parse error: {e}")

    @staticmethod
    def parse_fit_file(file_path: Path) -> Optional[ActivityData]:
        """
        Parse FIT file using fitparse library.

        Research-validated implementation extracting message-based data
        with units and proper error handling.

        Args:
            file_path: Path to FIT file

        Returns:
            ActivityData object or None
        """
        if not FITPARSE_AVAILABLE:
            raise FileNotSupportedError("fitparse library not available")

        try:
            # Load FIT file with fitparse
            fitfile = fitparse.FitFile(str(file_path))

            # Extract session/activity metadata
            activity_data = ActivityData()
            samples = []
            laps = []
            route_points = []

            # Parse session messages for activity metadata
            for session in fitfile.get_messages("session"):
                activity_data.sport = session.get_value("sport") or "unknown"
                activity_data.sub_sport = session.get_value("sub_sport")
                activity_data.start_time_utc = session.get_value("start_time")
                activity_data.elapsed_time_s = session.get_value("total_elapsed_time")
                activity_data.moving_time_s = session.get_value("total_timer_time")
                activity_data.distance_m = session.get_value("total_distance")
                activity_data.avg_hr = session.get_value("avg_heart_rate")
                activity_data.max_hr = session.get_value("max_heart_rate")
                activity_data.avg_power_w = session.get_value("avg_power")
                activity_data.max_power_w = session.get_value("max_power")
                activity_data.elevation_gain_m = session.get_value("total_ascent")
                activity_data.elevation_loss_m = session.get_value("total_descent")
                activity_data.calories = session.get_value("total_calories")
                break  # Use first session

            # Parse file_id for external_id
            for file_id in fitfile.get_messages("file_id"):
                activity_data.external_id = str(file_id.get_value("serial_number") or file_path.stem)
                break

            # Parse record messages for time series data
            elapsed_time = 0
            for record in fitfile.get_messages("record"):
                timestamp = record.get_value("timestamp")
                if not timestamp:
                    continue

                # GPS coordinates (convert from semicircles to degrees)
                lat = record.get_value("position_lat")
                lon = record.get_value("position_long")
                if lat is not None and lon is not None:
                    # Convert from semicircles to degrees
                    lat = lat * (180 / (2**31))
                    lon = lon * (180 / (2**31))

                # Extract advanced running dynamics
                vertical_oscillation = record.get_value("vertical_oscillation")
                if vertical_oscillation is not None:
                    # Convert from mm to mm (already in correct units)
                    vertical_oscillation_mm = float(vertical_oscillation)
                else:
                    vertical_oscillation_mm = None
                
                # Ground contact time (stance_time) - convert from ms to ms
                ground_contact_time = record.get_value("stance_time")
                if ground_contact_time is not None:
                    ground_contact_time_ms = float(ground_contact_time)
                else:
                    # Try Ground Time field (from Stryd)
                    ground_time = record.get_value("Ground Time")
                    ground_contact_time_ms = float(ground_time) if ground_time is not None else None

                sample = SampleData(
                    timestamp=timestamp,
                    elapsed_time_s=elapsed_time,
                    latitude=lat,
                    longitude=lon,
                    altitude_m=record.get_value("altitude"),
                    heart_rate=record.get_value("heart_rate"),
                    power_w=record.get_value("power"),
                    cadence_rpm=record.get_value("cadence"),
                    speed_mps=record.get_value("speed"),
                    temperature_c=record.get_value("temperature"),
                    # Advanced running dynamics
                    vertical_oscillation_mm=vertical_oscillation_mm,
                    vertical_ratio=record.get_value("vertical_ratio"),
                    ground_contact_time_ms=ground_contact_time_ms,
                    ground_contact_balance_pct=record.get_value("stance_time_balance"),
                    step_length_mm=record.get_value("step_length"),
                    air_power_w=record.get_value("Air Power"),
                    form_power_w=record.get_value("Form Power"),
                    leg_spring_stiffness=record.get_value("Leg Spring Stiffness"),
                    impact_loading_rate=record.get_value("Impact Loading Rate"),
                    stryd_temperature_c=record.get_value("Stryd Temperature"),
                    stryd_humidity_pct=record.get_value("Stryd Humidity"),
                )
                samples.append(sample)

                # Add to route points if GPS data available
                if lat is not None and lon is not None:
                    route_points.append((lat, lon, sample.altitude_m))

                elapsed_time += 1  # Increment for each record

            # Parse lap messages
            for lap_idx, lap in enumerate(fitfile.get_messages("lap")):
                # Get lap speed or calculate from distance/time
                avg_speed_mps = lap.get_value("avg_speed")
                if not avg_speed_mps:
                    # Calculate from distance and time if not provided
                    distance = lap.get_value("total_distance")
                    time = lap.get_value("total_elapsed_time")
                    if distance and time and time > 0:
                        avg_speed_mps = distance / time

                lap_data = LapData(
                    lap_index=lap_idx,
                    start_time_utc=lap.get_value("start_time"),
                    elapsed_time_s=lap.get_value("total_elapsed_time"),
                    distance_m=lap.get_value("total_distance"),
                    avg_speed_mps=avg_speed_mps,
                    avg_hr=lap.get_value("avg_heart_rate"),
                    max_hr=lap.get_value("max_heart_rate"),
                    avg_power_w=lap.get_value("avg_power"),
                    max_power_w=lap.get_value("max_power"),
                )
                laps.append(lap_data)

            activity_data.samples = samples
            activity_data.route_points = route_points
            activity_data.laps = laps

            # Derive missing metrics if not present
            ActivityParser._derive_metrics(activity_data)

            return activity_data

        except Exception as e:
            logger.error(f"FIT parsing error for {file_path}: {e}")
            raise CorruptFileError(f"FIT parse error: {e}")

    @staticmethod
    def parse_tcx_file(file_path: Path) -> Optional[ActivityData]:
        """
        Parse TCX file using tcxparser library.

        Research-validated implementation with direct property access
        and HR zone analysis capabilities.

        Args:
            file_path: Path to TCX file

        Returns:
            ActivityData object or None
        """
        if not TCXPARSER_AVAILABLE:
            raise FileNotSupportedError("tcxparser library not available")

        try:
            # Parse TCX file
            tcx = tcxparser.TCXParser(str(file_path))

            # Extract activity data using direct properties (research pattern)
            activity_data = ActivityData(
                external_id=file_path.stem,  # Use filename as external ID
                sport=tcx.activity_type or "unknown",
                start_time_utc=tcx.started_at,
                elapsed_time_s=int(tcx.duration) if tcx.duration else None,
                distance_m=tcx.distance,
                avg_hr=int(tcx.hr_avg) if tcx.hr_avg else None,
                max_hr=int(tcx.hr_max) if tcx.hr_max else None,
                calories=int(tcx.calories) if tcx.calories else None,
            )

            # Get HR zones using research-validated method
            if hasattr(tcx, "hr_percent_in_zones") and tcx.hr_max:
                try:
                    hr_zones = tcx.hr_percent_in_zones(
                        {
                            "Z1": (0, int(tcx.hr_max * 0.7)),
                            "Z2": (int(tcx.hr_max * 0.7), int(tcx.hr_max * 0.8)),
                            "Z3": (int(tcx.hr_max * 0.8), int(tcx.hr_max * 0.9)),
                            "Z4": (int(tcx.hr_max * 0.9), int(tcx.hr_max * 0.95)),
                            "Z5": (int(tcx.hr_max * 0.95), int(tcx.hr_max * 1.1)),
                        }
                    )
                    activity_data.hr_zones = hr_zones
                except Exception:
                    logger.debug("Could not calculate HR zones")

            # Parse trackpoints for time series data
            samples = []
            route_points = []

            if hasattr(tcx, "trackpoints"):
                for i, point in enumerate(tcx.trackpoints):
                    try:
                        sample = SampleData(
                            timestamp=point.time if hasattr(point, "time") else None,
                            elapsed_time_s=i,  # Use index as elapsed time approximation
                            latitude=float(point.latitude) if hasattr(point, "latitude") and point.latitude else None,
                            longitude=(
                                float(point.longitude) if hasattr(point, "longitude") and point.longitude else None
                            ),
                            altitude_m=(
                                float(point.elevation) if hasattr(point, "elevation") and point.elevation else None
                            ),
                            heart_rate=int(point.hr_value) if hasattr(point, "hr_value") and point.hr_value else None,
                            speed_mps=float(point.speed) if hasattr(point, "speed") and point.speed else None,
                        )
                        samples.append(sample)

                        # Add to route if GPS available
                        if sample.latitude and sample.longitude:
                            route_points.append((sample.latitude, sample.longitude, sample.altitude_m))

                    except (ValueError, AttributeError) as e:
                        logger.debug(f"Skipping trackpoint {i}: {e}")
                        continue

            activity_data.samples = samples
            activity_data.route_points = route_points

            # Derive missing metrics
            ActivityParser._derive_metrics(activity_data)

            return activity_data

        except Exception as e:
            logger.error(f"TCX parsing error for {file_path}: {e}")
            raise CorruptFileError(f"TCX parse error: {e}")

    @staticmethod
    def parse_gpx_file(file_path: Path) -> Optional[ActivityData]:
        """
        Parse GPX file using gpxpy library.

        Research-validated implementation with track/segment/point hierarchy
        and GPS statistics calculation.

        Args:
            file_path: Path to GPX file

        Returns:
            ActivityData object or None
        """
        if not GPXPY_AVAILABLE:
            raise FileNotSupportedError("gpxpy library not available")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                gpx = gpxpy.parse(f)

            # Initialize activity data
            activity_data = ActivityData(
                external_id=file_path.stem,
                sport="unknown",  # GPX doesn't specify sport type
                start_time_utc=None,
                distance_m=None,
            )

            samples = []
            route_points = []
            all_points = []

            # Extract all track points (research pattern: track/segment/point hierarchy)
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        all_points.append(point)

                        # Convert to route point tuple
                        route_points.append((point.latitude, point.longitude, point.elevation))

            if all_points:
                # Set start time from first point
                if all_points[0].time:
                    activity_data.start_time_utc = all_points[0].time

                # Convert points to samples
                start_time = all_points[0].time
                for i, point in enumerate(all_points):
                    elapsed_time_s = 0
                    if point.time and start_time:
                        elapsed_time_s = int((point.time - start_time).total_seconds())

                    sample = SampleData(
                        timestamp=point.time,
                        elapsed_time_s=elapsed_time_s,
                        latitude=point.latitude,
                        longitude=point.longitude,
                        altitude_m=point.elevation,
                        # GPX typically doesn't have HR/power data
                        heart_rate=None,
                        power_w=None,
                        speed_mps=None,
                    )
                    samples.append(sample)

            # Calculate distance using gpxpy built-in methods
            if gpx.tracks:
                try:
                    # Use gpxpy's built-in distance calculation
                    total_distance = 0
                    for track in gpx.tracks:
                        track_distance = track.length_2d()
                        if track_distance:
                            total_distance += track_distance

                    activity_data.distance_m = total_distance

                    # Calculate elapsed time
                    if all_points and len(all_points) > 1:
                        if all_points[0].time and all_points[-1].time:
                            elapsed = all_points[-1].time - all_points[0].time
                            activity_data.elapsed_time_s = int(elapsed.total_seconds())

                except Exception as e:
                    logger.debug(f"Could not calculate GPX statistics: {e}")

            activity_data.samples = samples
            activity_data.route_points = route_points

            # Derive missing metrics
            ActivityParser._derive_metrics(activity_data)

            return activity_data

        except Exception as e:
            logger.error(f"GPX parsing error for {file_path}: {e}")
            raise CorruptFileError(f"GPX parse error: {e}")

    @staticmethod
    def _derive_metrics(activity_data: ActivityData):
        """
        Derive missing metrics from available data.

        Research-validated calculations for pace, speed, etc.

        Args:
            activity_data: ActivityData object to enhance
        """
        try:
            # Calculate average speed if distance and time available
            if (
                activity_data.distance_m
                and activity_data.elapsed_time_s
                and activity_data.elapsed_time_s > 0
                and not activity_data.avg_speed_mps
            ):
                activity_data.avg_speed_mps = activity_data.distance_m / activity_data.elapsed_time_s

            # Calculate pace from speed (research-validated formula)
            if activity_data.avg_speed_mps and activity_data.avg_speed_mps > 0:
                # Pace in seconds per km
                activity_data.avg_pace_s_per_km = 1000 / activity_data.avg_speed_mps

            # Set moving time to elapsed time if not available
            if not activity_data.moving_time_s and activity_data.elapsed_time_s:
                activity_data.moving_time_s = activity_data.elapsed_time_s

        except (ZeroDivisionError, TypeError, AttributeError) as e:
            logger.debug(f"Could not derive metrics: {e}")


def calculate_file_hash(file_path: Path) -> str:
    """
    Convenience function to calculate file hash.

    Args:
        file_path: Path to file

    Returns:
        SHA-256 hex hash of file contents
    """
    return ActivityParser.calculate_file_hash(file_path)
