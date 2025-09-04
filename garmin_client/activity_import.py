"""
Activity Import Service for Garmin Dashboard.

Handles importing activities from Garmin Connect into the local database,
including downloading FIT files and parsing them for detailed metrics.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import hashlib

from app.data.db import session_scope
from app.data.models import Activity, Lap, Sample, RoutePoint, ImportResult
from ingest.parser import ActivityParser

from .client import GarminConnectClient, GarminAuthError

logger = logging.getLogger(__name__)


class ActivityImportService:
    """Service for importing activities from Garmin Connect to database."""

    def __init__(self, client: GarminConnectClient):
        self.client = client
        self.parser = ActivityParser()

    def import_activity_by_id(self, activity_id: str, download_fit: bool = True) -> Dict[str, Any]:
        """
        Import a specific activity from Garmin Connect into the database.

        Args:
            activity_id: Garmin Connect activity ID
            download_fit: Whether to download and parse FIT file for detailed data

        Returns:
            Dict with import status and details
        """
        try:
            if not self.client.is_authenticated():
                raise GarminAuthError("Client not authenticated")

            # Check if activity already exists in database
            with session_scope() as session:
                existing = session.query(Activity).filter_by(garmin_activity_id=activity_id).first()
                if existing:
                    return {
                        "success": True,
                        "status": "already_exists",
                        "activity_id": existing.id,
                        "message": f"Activity {activity_id} already exists in database",
                    }

            # Get activity summary from Garmin Connect
            activity_summary = self._get_activity_summary(activity_id)
            if not activity_summary:
                return {"success": False, "error": f"Could not retrieve activity {activity_id} from Garmin Connect"}

            # Download and parse FIT file if requested
            parsed_data = None
            if download_fit:
                try:
                    parsed_data = self._download_and_parse_fit(activity_id)
                except Exception as e:
                    logger.warning(f"Failed to download/parse FIT for {activity_id}: {e}")

            # Import to database
            with session_scope() as session:
                activity = self._create_activity_record(activity_summary, parsed_data)
                session.add(activity)
                session.flush()  # Get the ID

                activity_db_id = activity.id

                # Add laps if available
                if parsed_data and parsed_data.get("laps"):
                    for lap_data in parsed_data["laps"]:
                        lap = self._create_lap_record(activity_db_id, lap_data)
                        session.add(lap)

                # Add samples if available
                if parsed_data and parsed_data.get("samples"):
                    for sample_data in parsed_data["samples"]:
                        sample = self._create_sample_record(activity_db_id, sample_data)
                        session.add(sample)

                # Add route points if available
                if parsed_data and parsed_data.get("route_points"):
                    for point_data in parsed_data["route_points"]:
                        point = self._create_route_point_record(activity_db_id, point_data)
                        session.add(point)

                # Create import result record
                import_result = ImportResult(
                    file_path=f"garmin_connect://{activity_id}",
                    file_hash=self._generate_activity_hash(activity_summary),
                    activity_id=activity_db_id,
                    import_timestamp=datetime.now(timezone.utc),
                    processing_time_s=0.0,
                    samples_count=len(parsed_data.get("samples", [])) if parsed_data else 0,
                    laps_count=len(parsed_data.get("laps", [])) if parsed_data else 0,
                    route_points_count=len(parsed_data.get("route_points", [])) if parsed_data else 0,
                )
                session.add(import_result)

                logger.info(f"Successfully imported activity {activity_id} as database ID {activity_db_id}")

                return {
                    "success": True,
                    "status": "imported",
                    "activity_id": activity_db_id,
                    "garmin_activity_id": activity_id,
                    "samples": import_result.samples_count,
                    "laps": import_result.laps_count,
                    "route_points": import_result.route_points_count,
                    "message": f"Activity {activity_id} imported successfully",
                }

        except Exception as e:
            logger.error(f"Failed to import activity {activity_id}: {e}")
            return {"success": False, "error": str(e)}

    def import_activities_by_date_range(
        self, start_date: str, end_date: str, activity_types: Optional[List[str]] = None, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import activities from a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            activity_types: Optional list of activity types to filter
            limit: Optional limit on number of activities to import

        Returns:
            Dict with import summary
        """
        try:
            if not self.client.is_authenticated():
                raise GarminAuthError("Client not authenticated")

            # Get activities from Garmin Connect
            activities = self.client.get_activities_by_date(start_date, end_date, "")

            # Filter by activity type if specified
            if activity_types:
                activities = [a for a in activities if a.get("activityType") in activity_types]

            # Apply limit if specified
            if limit:
                activities = activities[:limit]

            imported_count = 0
            skipped_count = 0
            failed_count = 0
            results = []

            for activity in activities:
                activity_id = activity.get("activityId") or activity.get("activityIdStr")
                if not activity_id:
                    failed_count += 1
                    continue

                result = self.import_activity_by_id(str(activity_id))
                results.append(result)

                if result["success"]:
                    if result["status"] == "imported":
                        imported_count += 1
                    else:
                        skipped_count += 1
                else:
                    failed_count += 1

            return {
                "success": True,
                "total_activities": len(activities),
                "imported": imported_count,
                "skipped": skipped_count,
                "failed": failed_count,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to import activities for date range: {e}")
            return {"success": False, "error": str(e)}

    def _get_activity_summary(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Get activity summary from Garmin Connect."""
        try:
            return self.client.api.get_activity_by_id(activity_id)
        except Exception as e:
            logger.error(f"Failed to get activity summary for {activity_id}: {e}")
            return None

    def _download_and_parse_fit(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Download FIT file and parse it."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                fit_path = self.client.download_activity_fit(activity_id, Path(temp_dir))

                if fit_path and fit_path.exists():
                    return self.parser.parse_file(fit_path)

        except Exception as e:
            logger.warning(f"Failed to download/parse FIT for {activity_id}: {e}")

        return None

    def _create_activity_record(self, summary: Dict[str, Any], parsed_data: Optional[Dict[str, Any]]) -> Activity:
        """Create Activity database record from summary and parsed data."""
        garmin_id = summary.get("activityId") or summary.get("activityIdStr")

        return Activity(
            garmin_activity_id=str(garmin_id) if garmin_id else None,
            name=summary.get("activityName", ""),
            sport=summary.get("activityType", "unknown"),
            start_time=self._parse_datetime(summary.get("startTimeGMT") or summary.get("startTimeLocal")),
            end_time=self._parse_datetime(summary.get("endTimeGMT") or summary.get("endTimeLocal")),
            distance_m=summary.get("distance", 0.0),
            duration_s=summary.get("elapsedDuration", 0),
            calories=summary.get("calories"),
            avg_heart_rate=summary.get("averageHR"),
            max_heart_rate=summary.get("maxHR"),
            avg_speed_ms=summary.get("averageSpeed"),
            max_speed_ms=summary.get("maxSpeed"),
            total_ascent_m=summary.get("elevationGain"),
            total_descent_m=summary.get("elevationLoss"),
            min_elevation_m=summary.get("minElevation"),
            max_elevation_m=summary.get("maxElevation"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def _create_lap_record(self, activity_id: int, lap_data: Dict[str, Any]) -> Lap:
        """Create Lap database record."""
        return Lap(
            activity_id=activity_id,
            lap_number=lap_data.get("lap_number", 0),
            start_time=self._parse_datetime(lap_data.get("start_time")),
            end_time=self._parse_datetime(lap_data.get("end_time")),
            distance_m=lap_data.get("distance_m", 0.0),
            duration_s=lap_data.get("duration_s", 0),
            calories=lap_data.get("calories"),
            avg_heart_rate=lap_data.get("avg_heart_rate"),
            max_heart_rate=lap_data.get("max_heart_rate"),
            avg_speed_ms=lap_data.get("avg_speed_ms"),
            max_speed_ms=lap_data.get("max_speed_ms"),
        )

    def _create_sample_record(self, activity_id: int, sample_data: Dict[str, Any]) -> Sample:
        """Create Sample database record."""
        return Sample(
            activity_id=activity_id,
            timestamp=self._parse_datetime(sample_data.get("timestamp")),
            latitude=sample_data.get("latitude"),
            longitude=sample_data.get("longitude"),
            elevation_m=sample_data.get("elevation_m"),
            heart_rate=sample_data.get("heart_rate"),
            cadence=sample_data.get("cadence"),
            power_w=sample_data.get("power_w"),
            speed_ms=sample_data.get("speed_ms"),
            temperature_c=sample_data.get("temperature_c"),
        )

    def _create_route_point_record(self, activity_id: int, point_data: Dict[str, Any]) -> RoutePoint:
        """Create RoutePoint database record."""
        return RoutePoint(
            activity_id=activity_id,
            latitude=point_data.get("latitude"),
            longitude=point_data.get("longitude"),
            elevation_m=point_data.get("elevation_m"),
            timestamp=self._parse_datetime(point_data.get("timestamp")),
        )

    def _parse_datetime(self, dt_str: Any) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not dt_str:
            return None

        try:
            if isinstance(dt_str, datetime):
                return dt_str
            elif isinstance(dt_str, str):
                # Try common formats
                formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]
                for fmt in formats:
                    try:
                        return datetime.strptime(dt_str, fmt).replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
            elif isinstance(dt_str, (int, float)):
                # Assume timestamp
                return datetime.fromtimestamp(dt_str, tz=timezone.utc)

        except Exception as e:
            logger.warning(f"Failed to parse datetime {dt_str}: {e}")

        return None

    def _generate_activity_hash(self, summary: Dict[str, Any]) -> str:
        """Generate hash for activity summary."""
        key_data = f"{summary.get('activityId', '')}{summary.get('startTimeGMT', '')}{summary.get('distance', '')}"
        return hashlib.md5(key_data.encode()).hexdigest()
