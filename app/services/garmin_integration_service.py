"""
Garmin Integration Service - Bridge between bruvio-garmin script and web dashboard.

This service integrates the existing bruvio-garmin.py script functionality into the web
application, providing data transformation, smoothing/aggregation, and persistence.
"""

from datetime import date, timedelta
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Add project root to path to import bruvio-garmin functions
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.wellness_data_service import WellnessDataService
from app.utils import get_logger

logger = get_logger(__name__)

try:
    # Import bruvio-garmin functions - handle import gracefully
    import bruvio_garmin as bg

    BRUVIO_GARMIN_AVAILABLE = True
    logger.info("✅ bruvio-garmin script functions imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import bruvio-garmin functions: {e}")
    BRUVIO_GARMIN_AVAILABLE = False


class GarminIntegrationService:
    """Service to integrate bruvio-garmin script with web dashboard."""

    def __init__(self):
        """Initialize the Garmin integration service."""
        self.api = None
        self.wellness_service = WellnessDataService()
        self.logger = logger

    def authenticate_garmin(self, email: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize Garmin API connection using bruvio-garmin auth.

        Args:
            email: Garmin Connect email (optional if credentials stored)
            password: Garmin Connect password (optional if credentials stored)

        Returns:
            Dict with authentication status and message
        """
        if not BRUVIO_GARMIN_AVAILABLE:
            return {"success": False, "error": "bruvio-garmin script not available"}

        try:
            # Try to initialize API with stored credentials or provided ones
            self.api = bg.init_api(email, password)

            if self.api:
                self.logger.info("✅ Garmin Connect authentication successful")
                return {"success": True, "message": "Successfully authenticated with Garmin Connect"}
            else:
                return {"success": False, "error": "Authentication failed - invalid credentials"}

        except Exception as e:
            self.logger.error(f"❌ Garmin authentication error: {e}")
            return {"success": False, "error": f"Authentication error: {str(e)}"}

    def sync_wellness_data_range(self, start_date: date, end_date: date, smoothing: str = "none") -> Dict[str, Any]:
        """
        Sync wellness data using bruvio-garmin functions with smoothing options.

        Args:
            start_date: Start date for data sync
            end_date: End date for data sync
            smoothing: Smoothing method ["none", "day", "week", "month", "year"]

        Returns:
            Dict with sync results and statistics
        """
        if not self.api:
            auth_result = self.authenticate_garmin()
            if not auth_result["success"]:
                return auth_result

        if not BRUVIO_GARMIN_AVAILABLE:
            return {"success": False, "error": "bruvio-garmin script not available"}

        try:
            self.logger.info(f"🔄 Starting wellness data sync: {start_date} to {end_date}")

            # Calculate the number of days
            days = (end_date - start_date).days + 1

            # Fetch data using bruvio-garmin interval function
            dailies = bg.fetch_interval(self.api, start_date, end_date)

            if not dailies:
                return {"success": False, "error": "No data retrieved from Garmin Connect"}

            self.logger.info(f"📊 Retrieved {len(dailies)} days of data from Garmin")

            # Transform data to database format
            wellness_data = self._transform_dailies_to_db_format(dailies)

            # Apply smoothing/aggregation if requested
            if smoothing != "none":
                wellness_data = self._apply_smoothing(wellness_data, smoothing)
                self.logger.info(f"📈 Applied {smoothing} smoothing to data")

            # Persist to database using wellness service
            persistence_result = self.wellness_service.persist_comprehensive_wellness_data(wellness_data)

            successful_types = sum(1 for success in persistence_result.values() if success)
            total_types = len(persistence_result)

            return {
                "success": True,
                "records_synced": len(dailies),
                "date_range": f"{start_date} to {end_date}",
                "days_synced": days,
                "smoothing": smoothing,
                "persistence": persistence_result,
                "data_types_persisted": f"{successful_types}/{total_types}",
                "message": f"Successfully synced {len(dailies)} days of wellness data",
            }

        except Exception as e:
            self.logger.error(f"❌ Wellness data sync failed: {e}")
            return {"success": False, "error": f"Sync failed: {str(e)}"}

    def _transform_dailies_to_db_format(self, dailies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Transform bruvio-garmin dailies data to database format.

        Args:
            dailies: List of daily wellness data from bruvio-garmin

        Returns:
            Dict with wellness data organized by type for persistence
        """
        wellness_data = {
            "sleep": [],
            "stress": [],
            "steps": [],
            "heart_rate": [],
            "body_battery": [],
            "training_readiness": [],
            "personal_records": [],
        }

        for daily in dailies:
            try:
                # Parse the date
                daily_date = self._parse_date_from_daily(daily)
                if not daily_date:
                    continue

                # Transform sleep data
                if "sleep" in daily and daily["sleep"]:
                    sleep_data = self._transform_sleep_data(daily["sleep"], daily_date)
                    if sleep_data:
                        wellness_data["sleep"].append(sleep_data)

                # Transform stress data
                if "stress" in daily and daily["stress"]:
                    stress_data = self._transform_stress_data(daily["stress"], daily_date)
                    if stress_data:
                        wellness_data["stress"].append(stress_data)

                # Transform steps data
                if "steps" in daily and daily["steps"] is not None:
                    steps_data = self._transform_steps_data(daily, daily_date)
                    if steps_data:
                        wellness_data["steps"].append(steps_data)

                # Transform heart rate data
                if "resting_heart_rate" in daily or "hrv" in daily:
                    hr_data = self._transform_heart_rate_data(daily, daily_date)
                    if hr_data:
                        wellness_data["heart_rate"].append(hr_data)

                # Transform body battery data
                if "body_battery" in daily and daily["body_battery"]:
                    bb_data = self._transform_body_battery_data(daily["body_battery"], daily_date)
                    if bb_data:
                        wellness_data["body_battery"].append(bb_data)

            except Exception as e:
                self.logger.warning(f"⚠️ Failed to transform daily data for {daily_date}: {e}")
                continue

        return wellness_data

    def _transform_sleep_data(self, sleep_data: Dict[str, Any], daily_date: date) -> Optional[Dict[str, Any]]:
        """Transform sleep data from bruvio-garmin format to database format."""
        try:
            return {
                "date": daily_date,
                "total_sleep_time_s": sleep_data.get("totalSleepTimeSeconds"),
                "deep_sleep_s": sleep_data.get("deepSleepSeconds"),
                "light_sleep_s": sleep_data.get("lightSleepSeconds"),
                "rem_sleep_s": sleep_data.get("remSleepSeconds"),
                "awake_time_s": sleep_data.get("awakeDurationSeconds"),
                "sleep_score": sleep_data.get("overallSleepScore"),
                "efficiency_percentage": sleep_data.get("sleepEfficiency"),
                "restlessness": sleep_data.get("restlessMoments"),
            }
        except Exception as e:
            self.logger.warning(f"Sleep data transformation failed: {e}")
            return None

    def _transform_stress_data(self, stress_data: Dict[str, Any], daily_date: date) -> Optional[Dict[str, Any]]:
        """Transform stress data from bruvio-garmin format to database format."""
        try:
            return {
                "date": daily_date,
                "avg_stress_level": stress_data.get("averageStressLevel"),
                "max_stress_level": stress_data.get("maxStressLevel"),
                "rest_stress_level": stress_data.get("restStressLevel"),
                "rest_minutes": stress_data.get("restStressDuration"),
                "low_minutes": stress_data.get("lowStressDuration"),
                "medium_minutes": stress_data.get("mediumStressDuration"),
                "high_minutes": stress_data.get("highStressDuration"),
                "stress_qualifier": stress_data.get("stressQualifier"),
            }
        except Exception as e:
            self.logger.warning(f"Stress data transformation failed: {e}")
            return None

    def _transform_steps_data(self, daily_data: Dict[str, Any], daily_date: date) -> Optional[Dict[str, Any]]:
        """Transform steps data from bruvio-garmin format to database format."""
        try:
            return {
                "date": daily_date,
                "total_steps": daily_data.get("steps"),
                "step_goal": daily_data.get("stepGoal"),
                "total_distance_m": daily_data.get("totalDistance"),
                "calories_burned": daily_data.get("activeKilocalories"),
                "calories_bmr": daily_data.get("bmrKilocalories"),
                "calories_active": daily_data.get("activeKilocalories"),
                "floors_climbed": daily_data.get("floorsAscended"),
                "floors_goal": daily_data.get("floorsAscendedGoal"),
            }
        except Exception as e:
            self.logger.warning(f"Steps data transformation failed: {e}")
            return None

    def _transform_heart_rate_data(self, daily_data: Dict[str, Any], daily_date: date) -> Optional[Dict[str, Any]]:
        """Transform heart rate data from bruvio-garmin format to database format."""
        try:
            hr_data = {
                "date": daily_date,
                "resting_hr": daily_data.get("resting_heart_rate"),
                "max_hr": daily_data.get("maxHeartRate"),
                "avg_hr": daily_data.get("averageHeartRate"),
            }

            # Add HRV data if available
            if "hrv" in daily_data and daily_data["hrv"]:
                hrv_data = daily_data["hrv"]
                hr_data["hrv_score"] = hrv_data.get("lastNightAvg")
                hr_data["hrv_status"] = hrv_data.get("status")

            return hr_data
        except Exception as e:
            self.logger.warning(f"Heart rate data transformation failed: {e}")
            return None

    def _transform_body_battery_data(self, bb_data: Dict[str, Any], daily_date: date) -> Optional[Dict[str, Any]]:
        """Transform body battery data from bruvio-garmin format to database format."""
        try:
            return {
                "date": daily_date,
                "body_battery_score": bb_data.get("charged", 0) - bb_data.get("drained", 0),  # Net score
                "charged_value": bb_data.get("charged"),
                "drained_value": bb_data.get("drained"),
                "highest_value": bb_data.get("highestValue"),
                "lowest_value": bb_data.get("lowestValue"),
            }
        except Exception as e:
            self.logger.warning(f"Body battery data transformation failed: {e}")
            return None

    def _parse_date_from_daily(self, daily: Dict[str, Any]) -> Optional[date]:
        """Parse date from daily data entry."""
        try:
            # Try different possible date field names
            date_fields = ["date", "calendarDate", "summaryDate", "day"]

            for field in date_fields:
                if field in daily and daily[field]:
                    date_str = daily[field]
                    if isinstance(date_str, str):
                        # Handle different date formats
                        if "T" in date_str:
                            date_str = date_str.split("T")[0]  # Remove time part
                        return date.fromisoformat(date_str)
                    elif hasattr(date_str, "date"):
                        return date_str.date()

            return None
        except Exception as e:
            self.logger.warning(f"Date parsing failed: {e}")
            return None

    def _apply_smoothing(self, wellness_data: Dict[str, Any], smoothing: str) -> Dict[str, Any]:
        """
        Apply smoothing/aggregation to wellness data.

        Args:
            wellness_data: Raw wellness data
            smoothing: Smoothing method ["day", "week", "month", "year"]

        Returns:
            Smoothed wellness data
        """
        if smoothing == "none" or smoothing is None:
            return wellness_data

        try:
            smoothed_data = {}

            for data_type, records in wellness_data.items():
                if not records:
                    smoothed_data[data_type] = []
                    continue

                # Group records by time period based on smoothing method
                if smoothing == "day":
                    # No smoothing needed - already daily data
                    smoothed_data[data_type] = records

                elif smoothing == "week":
                    smoothed_data[data_type] = self._aggregate_by_week(records)

                elif smoothing == "month":
                    smoothed_data[data_type] = self._aggregate_by_month(records)

                elif smoothing == "year":
                    smoothed_data[data_type] = self._aggregate_by_year(records)

                else:
                    # Unknown smoothing method, return original data
                    smoothed_data[data_type] = records

            self.logger.info(f"Applied {smoothing} aggregation to {len(wellness_data)} data types")
            return smoothed_data

        except Exception as e:
            self.logger.warning(f"Smoothing failed: {e}, returning original data")
            return wellness_data

    def _aggregate_by_week(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate daily records by week (7-day periods)."""
        if not records:
            return []

        # Group records by week
        weeks = {}
        for record in records:
            record_date = record.get("date")
            if record_date:
                # Calculate week start (Monday)
                days_since_monday = record_date.weekday()
                week_start = record_date - timedelta(days=days_since_monday)

                if week_start not in weeks:
                    weeks[week_start] = []
                weeks[week_start].append(record)

        # Aggregate each week
        aggregated = []
        for week_start, week_records in weeks.items():
            agg_record = self._aggregate_records(week_records, week_start)
            if agg_record:
                aggregated.append(agg_record)

        return aggregated

    def _aggregate_by_month(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate daily records by month."""
        if not records:
            return []

        # Group records by month
        months = {}
        for record in records:
            record_date = record.get("date")
            if record_date:
                month_start = record_date.replace(day=1)

                if month_start not in months:
                    months[month_start] = []
                months[month_start].append(record)

        # Aggregate each month
        aggregated = []
        for month_start, month_records in months.items():
            agg_record = self._aggregate_records(month_records, month_start)
            if agg_record:
                aggregated.append(agg_record)

        return aggregated

    def _aggregate_by_year(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate daily records by year."""
        if not records:
            return []

        # Group records by year
        years = {}
        for record in records:
            record_date = record.get("date")
            if record_date:
                year_start = record_date.replace(month=1, day=1)

                if year_start not in years:
                    years[year_start] = []
                years[year_start].append(record)

        # Aggregate each year
        aggregated = []
        for year_start, year_records in years.items():
            agg_record = self._aggregate_records(year_records, year_start)
            if agg_record:
                aggregated.append(agg_record)

        return aggregated

    def _aggregate_records(self, records: List[Dict[str, Any]], period_date: date) -> Optional[Dict[str, Any]]:
        """
        Aggregate a list of records into a single record using appropriate statistics.

        Args:
            records: List of records to aggregate
            period_date: Date to use for the aggregated record

        Returns:
            Aggregated record or None if aggregation fails
        """
        if not records:
            return None

        try:
            # Initialize aggregated record
            agg_record = {"date": period_date}

            # Define which fields should be summed vs averaged
            sum_fields = [
                "total_sleep_time_s",
                "deep_sleep_s",
                "light_sleep_s",
                "rem_sleep_s",
                "awake_time_s",
                "total_steps",
                "total_distance_m",
                "calories_burned",
                "calories_bmr",
                "calories_active",
                "floors_climbed",
                "rest_minutes",
                "low_minutes",
                "medium_minutes",
                "high_minutes",
            ]

            avg_fields = [
                "sleep_score",
                "efficiency_percentage",
                "restlessness",
                "avg_stress_level",
                "max_stress_level",
                "rest_stress_level",
                "resting_hr",
                "max_hr",
                "avg_hr",
                "hrv_score",
                "body_battery_score",
                "charged_value",
                "drained_value",
                "highest_value",
                "lowest_value",
            ]

            # Aggregate sum fields
            for field in sum_fields:
                values = [r.get(field) for r in records if r.get(field) is not None]
                if values:
                    agg_record[field] = sum(values)

            # Aggregate average fields
            for field in avg_fields:
                values = [r.get(field) for r in records if r.get(field) is not None]
                if values:
                    agg_record[field] = sum(values) / len(values)

            # Handle special fields
            step_goals = [r.get("step_goal") for r in records if r.get("step_goal") is not None]
            if step_goals:
                agg_record["step_goal"] = max(step_goals)  # Use highest goal

            floors_goals = [r.get("floors_goal") for r in records if r.get("floors_goal") is not None]
            if floors_goals:
                agg_record["floors_goal"] = max(floors_goals)  # Use highest goal

            return agg_record

        except Exception as e:
            self.logger.warning(f"Record aggregation failed: {e}")
            return None

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and capabilities."""
        return {
            "bruvio_garmin_available": BRUVIO_GARMIN_AVAILABLE,
            "authenticated": self.api is not None,
            "wellness_service_available": self.wellness_service is not None,
            "supported_smoothing": ["none", "day", "week", "month", "year"],
            "supported_data_types": ["sleep", "stress", "steps", "heart_rate", "body_battery", "training_readiness"],
        }
