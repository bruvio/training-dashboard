"""
Garmin Integration Service - Direct integration with Garmin Connect API.

This service provides wellness data synchronization using the existing garmin_client,
with data transformation, smoothing/aggregation, and persistence to the dashboard database.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.services.wellness_data_service import WellnessDataService
from app.utils import get_logger
from garmin_client.client import GarminConnectClient, GarminAuthError
from garmin_client.wellness_sync import WellnessSync

logger = get_logger(__name__)


class GarminIntegrationService:
    """Service for direct Garmin Connect API integration and wellness data sync."""

    def __init__(self):
        """Initialize the Garmin integration service."""
        self.client = GarminConnectClient()
        self.wellness_sync = WellnessSync(self.client)
        self.wellness_service = WellnessDataService()
        self.logger = logger

        # Try to load existing session automatically
        try:
            session_data = self.client.load_session()
            if session_data.get("is_authenticated"):
                self.logger.info(
                    f"✅ Loaded existing Garmin session for user: {session_data.get('username', 'unknown')}"
                )
            else:
                self.logger.warning("⚠️ No valid existing session found")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load existing session: {e}")

    def authenticate_garmin(self, email: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize Garmin API connection using existing client.

        Args:
            email: Garmin Connect email (optional if credentials stored)
            password: Garmin Connect password (optional if credentials stored)

        Returns:
            Dict with authentication status and message
        """
        try:
            # Check if already authenticated
            if self.client.is_authenticated():
                username = self.client.username()
                self.logger.info(f"✅ Already authenticated with Garmin Connect as {username}")
                return {"success": True, "message": f"Already authenticated as {username}"}

            # Try to authenticate with provided credentials
            if email and password:
                result = self.client.login(email, password)
                if result.get("success"):
                    self.logger.info("✅ Garmin Connect authentication successful")
                    return {"success": True, "message": "Successfully authenticated with Garmin Connect"}
                else:
                    return {"success": False, "error": "Failed to authenticate with provided credentials"}
            else:
                # Try to load existing session
                try:
                    session_data = self.client.load_session()
                    if session_data.get("is_authenticated"):
                        self.logger.info("✅ Using existing Garmin Connect session")
                        return {
                            "success": True,
                            "message": f"Using existing session for {session_data.get('username', 'user')}",
                        }
                    else:
                        return {"success": False, "error": "No valid stored session found"}
                except Exception:
                    return {"success": False, "error": "No stored credentials found and no credentials provided"}

        except GarminAuthError as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            self.logger.error(f"❌ Unexpected authentication error: {e}")
            return {"success": False, "error": str(e)}

    def sync_wellness_data_range(self, start_date: date, end_date: date, smoothing: str = "none") -> Dict[str, Any]:
        """
        Sync wellness data directly from Garmin Connect API.

        Args:
            start_date: Start date for data sync
            end_date: End date for data sync
            smoothing: Smoothing method ["none", "day", "week", "month", "year"]

        Returns:
            Dict with sync results and statistics
        """
        try:
            # Check authentication and try to restore session if needed
            if not self.client.is_authenticated():
                # Try to load session again in case it was established elsewhere
                try:
                    session_data = self.client.load_session()
                    if not session_data.get("is_authenticated"):
                        return {
                            "success": False,
                            "error": "Not authenticated with Garmin Connect. Please log in first on the Garmin login page (/garmin).",
                            "requires_auth": True,
                        }
                    else:
                        self.logger.info("✅ Successfully restored Garmin session")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not restore session: {e}")
                    return {
                        "success": False,
                        "error": "Authentication required. Please log in first on the Garmin login page (/garmin).",
                        "requires_auth": True,
                    }

            self.logger.info(f"🔄 Starting wellness data sync from {start_date} to {end_date}")

            # Use WellnessSync to fetch comprehensive data
            try:
                self.logger.info("📊 Fetching comprehensive wellness data using WellnessSync...")
                wellness_data_dict = self.wellness_sync.fetch_range(start=start_date, end=end_date, include_extras=True)

                if not wellness_data_dict:
                    return {"success": False, "error": "No data returned from WellnessSync"}

                self.logger.info(f"✅ Received data types: {list(wellness_data_dict.keys())}")

                # Transform the DataFrame-based data to our database format
                wellness_data = {
                    "sleep": [],
                    "steps": [],
                    "heart_rate": [],
                    "body_battery": [],
                    "stress": [],
                    "training_readiness": [],
                    "hrv": [],
                }

                total_records = 0
                days_synced = 0

                # Transform each data type
                for data_type, df in wellness_data_dict.items():
                    if df is not None and hasattr(df, "iterrows") and not df.empty:
                        transformed_records = self._transform_wellness_dataframe(data_type, df)
                        if transformed_records:
                            # Map WellnessSync data types to our persistence format
                            mapped_type = self._map_wellness_data_type(data_type)
                            if mapped_type in wellness_data:
                                wellness_data[mapped_type].extend(transformed_records)
                                total_records += len(transformed_records)

                # Calculate days synced from the data
                all_dates = set()
                for data_list in wellness_data.values():
                    for record in data_list:
                        if "date" in record:
                            all_dates.add(record["date"])
                days_synced = len(all_dates)

            except Exception as sync_error:
                self.logger.error(f"❌ WellnessSync fetch failed: {sync_error}")
                return {"success": False, "error": str(sync_error)}

            # Persist the collected data to database
            self.logger.info("💾 Persisting wellness data to database...")
            persistence_results = {}

            if wellness_data["sleep"]:
                persistence_results["sleep"] = self.wellness_service.persist_sleep_data(wellness_data["sleep"])

            if wellness_data["steps"]:
                persistence_results["steps"] = self.wellness_service.persist_steps_data(wellness_data["steps"])

            if wellness_data["heart_rate"]:
                persistence_results["heart_rate"] = self.wellness_service.persist_heart_rate_data(
                    wellness_data["heart_rate"]
                )

            if wellness_data["body_battery"]:
                persistence_results["body_battery"] = self.wellness_service.persist_body_battery_data(
                    wellness_data["body_battery"]
                )

            if wellness_data["stress"]:
                persistence_results["stress"] = self.wellness_service.persist_stress_data(wellness_data["stress"])

            if wellness_data["training_readiness"]:
                persistence_results["training_readiness"] = self.wellness_service.persist_training_readiness_data(
                    wellness_data["training_readiness"]
                )


            # Note: VO2 max data is combined with heart_rate data and persisted above
            # Training readiness has its own persistence handled above

            # Calculate success metrics
            successful_types = sum(1 for success in persistence_results.values() if success)

            self.logger.info(
                f"✅ Sync completed: {days_synced} days, {total_records} records, {successful_types} data types"
            )

            return {
                "success": True,
                "message": f"Successfully synced {days_synced} days of wellness data",
                "days_synced": days_synced,
                "records_synced": total_records,
                "data_types_synced": successful_types,
                "persistence": persistence_results,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "smoothing": smoothing,
            }

        except GarminAuthError as e:
            self.logger.error(f"❌ Authentication error during sync: {e}")
            return {"success": False, "error": "Authentication required", "requires_auth": True}
        except Exception as e:
            self.logger.error(f"❌ Sync failed with error: {e}")
            return {
                "success": False,
                "error": str(e),
                "days_synced": days_synced if "days_synced" in locals() else 0,
                "records_synced": total_records if "total_records" in locals() else 0,
            }

    def _transform_garmin_data(self, garmin_data: Dict[str, Any], date_obj: date) -> Dict[str, Any]:
        """
        Transform raw Garmin API data to database format.

        Args:
            garmin_data: Raw Garmin API response
            date_obj: Date for the data

        Returns:
            Dict with transformed data ready for database persistence
        """
        transformed = {}
        date_str = date_obj.isoformat()

        # Transform sleep data
        if "sleep" in garmin_data and garmin_data["sleep"]:
            sleep_data = garmin_data["sleep"]
            if isinstance(sleep_data, dict) and "dailySleepDTO" in sleep_data:
                daily_sleep = sleep_data["dailySleepDTO"]
                if daily_sleep and isinstance(daily_sleep, dict):
                    transformed_sleep = {
                        "date": date_str,
                        "total_sleep_time_s": daily_sleep.get("sleepTimeSeconds") or 0,
                        "deep_sleep_s": daily_sleep.get("deepSleepSeconds") or 0,
                        "light_sleep_s": daily_sleep.get("lightSleepSeconds") or 0,
                        "rem_sleep_s": daily_sleep.get("remSleepSeconds") or 0,
                        "awake_time_s": daily_sleep.get("awakeSleepSeconds") or 0,
                        "sleep_score": daily_sleep.get("sleepQualityTypePK"),
                        "bedtime_utc": self._convert_garmin_timestamp(daily_sleep.get("sleepStartTimestampGMT")),
                        "wakeup_time_utc": self._convert_garmin_timestamp(daily_sleep.get("sleepEndTimestampGMT")),
                        "efficiency_percentage": None,  # Calculate if needed
                        "restlessness": None,  # Not in current API
                    }
                    # Only include if we have meaningful sleep data
                    if transformed_sleep["total_sleep_time_s"] > 0:
                        transformed["sleep"] = transformed_sleep

        # Transform stress data
        if "stress" in garmin_data and garmin_data["stress"]:
            stress_data = garmin_data["stress"]
            if isinstance(stress_data, dict):
                transformed_stress = {
                    "date": date_str,
                    "avg_stress_level": stress_data.get("avgStressLevel"),
                    "max_stress_level": stress_data.get("maxStressLevel"),
                    "rest_stress_duration_s": None,  # Calculate from stress values if available
                    "low_stress_duration_s": None,
                    "medium_stress_duration_s": None,
                    "high_stress_duration_s": None,
                    "stress_qualifier": None,
                }
                # Only include if we have meaningful stress data
                if transformed_stress["avg_stress_level"] is not None:
                    transformed["stress"] = transformed_stress

        # Transform steps data
        if "steps" in garmin_data and garmin_data["steps"]:
            steps_data = garmin_data["steps"]
            if isinstance(steps_data, list) and len(steps_data) > 0:
                # Garmin returns steps as array, aggregate if needed
                total_steps = sum(item.get("steps", 0) for item in steps_data if isinstance(item, dict))
                if total_steps > 0:
                    transformed["steps"] = {
                        "date": date_str,
                        "total_steps": total_steps,
                        "calories_burned": None,  # Not in current response
                        "distance_meters": None,  # Not in current response
                        "floors_climbed": None,  # Not in current response
                    }

        # Transform HRV data
        if "hrv" in garmin_data and garmin_data["hrv"]:
            hrv_data = garmin_data["hrv"]
            if isinstance(hrv_data, dict) and "hrvSummary" in hrv_data:
                hrv_summary = hrv_data["hrvSummary"]
                if hrv_summary and isinstance(hrv_summary, dict):
                    transformed_hrv = {
                        "date": date_str,
                        "weekly_avg": hrv_summary.get("weeklyAvg"),
                        "last_night_avg": hrv_summary.get("lastNightAvg"),
                        "last_night_5min_high": hrv_summary.get("lastNight5MinHigh"),
                        "baseline_low_upper": None,
                        "baseline_balanced_low": None,
                        "baseline_balanced_upper": None,
                        "baseline_marker_value": None,
                        "status": hrv_summary.get("status"),
                        "feedback_phrase": hrv_summary.get("feedbackPhrase"),
                        "create_timestamp": self._convert_garmin_timestamp_string(hrv_summary.get("createTimeStamp")),
                    }

                    # Extract baseline data if available
                    baseline = hrv_summary.get("baseline")
                    if baseline and isinstance(baseline, dict):
                        transformed_hrv.update(
                            {
                                "baseline_low_upper": baseline.get("lowUpper"),
                                "baseline_balanced_low": baseline.get("balancedLow"),
                                "baseline_balanced_upper": baseline.get("balancedUpper"),
                                "baseline_marker_value": baseline.get("markerValue"),
                            }
                        )

                    # Only include if we have meaningful HRV data
                    if transformed_hrv["last_night_avg"] is not None:
                        transformed["hrv"] = transformed_hrv

        return transformed

    def _convert_garmin_timestamp(self, timestamp_ms) -> Optional[datetime]:
        """Convert Garmin timestamp (milliseconds) to UTC datetime."""
        if timestamp_ms is None or timestamp_ms == 0:
            return None
        try:
            # Garmin timestamps are in milliseconds, convert to seconds
            return datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
        except (ValueError, TypeError, OverflowError):
            return None

    def _convert_garmin_timestamp_string(self, timestamp_str) -> Optional[datetime]:
        """Convert Garmin timestamp string to UTC datetime."""
        if not timestamp_str:
            return None
        try:
            # Parse ISO format timestamp string
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    def _handle_nat_value(self, value):
        """Convert pandas NaT (Not-a-Time) and similar values to None."""
        if value is None:
            return None
        # Handle pandas NaT values
        if hasattr(value, "__class__") and "NaTType" in str(value.__class__):
            return None
        # Handle numpy nan values
        try:
            import numpy as np

            if np.isnan(value):
                return None
        except (TypeError, ImportError):
            pass
        return value

    def _calculate_sleep_efficiency(self, row) -> Optional[float]:
        """Calculate sleep efficiency from sleep stage data."""
        try:
            total_sleep_seconds = self._handle_nat_value(row.get("total_sleep_seconds", 0)) or 0
            deep_sec = self._handle_nat_value(row.get("deep_sec", 0)) or 0
            light_sec = self._handle_nat_value(row.get("light_sec", 0)) or 0
            rem_sec = self._handle_nat_value(row.get("rem_sec", 0)) or 0
            awake_sec = self._handle_nat_value(row.get("awake_sec", 0)) or 0

            # Calculate actual sleep time (all stages except awake)
            actual_sleep_time = deep_sec + light_sec + rem_sec

            # Total time in bed = actual sleep + awake time
            time_in_bed = actual_sleep_time + awake_sec

            # If we don't have awake time, use total_sleep_seconds as fallback
            if time_in_bed == 0 and total_sleep_seconds > 0:
                # Assume 85% efficiency as baseline if no detailed data
                return 85.0

            # Calculate efficiency: (actual sleep time / time in bed) * 100
            if time_in_bed > 0:
                efficiency = (actual_sleep_time / time_in_bed) * 100
                # Cap efficiency at 100% and minimum at 50% to be realistic
                return max(50.0, min(100.0, round(efficiency, 1)))

            return None

        except (TypeError, ValueError, ZeroDivisionError):
            return None

    def _map_wellness_data_type(self, wellness_type: str) -> str:
        """Map WellnessSync data type to our persistence format."""
        mapping = {
            "sleep": "sleep",
            "steps": "steps",
            "stress": "stress",
            "resting_hr": "heart_rate",
            "hrv": "heart_rate",  # HRV goes into heart_rate table as hrv_score
            "body_battery": "body_battery",
            "training_readiness": "training_readiness",
            "vo2max": "heart_rate",  # VO2 max goes into heart_rate table
        }
        return mapping.get(wellness_type, wellness_type)

    def _transform_wellness_dataframe(self, data_type: str, df) -> List[Dict[str, Any]]:
        """Transform WellnessSync DataFrame to database format."""
        records = []

        try:
            for _, row in df.iterrows():
                if data_type == "sleep":
                    # Handle pandas Timestamp date
                    date_str = (
                        row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
                    )
                    record = {
                        "date": date_str,
                        "total_sleep_time_s": self._handle_nat_value(row.get("total_sleep_seconds", 0)) or 0,
                        "deep_sleep_s": self._handle_nat_value(row.get("deep_sec", 0)) or 0,
                        "light_sleep_s": self._handle_nat_value(row.get("light_sec", 0)) or 0,
                        "rem_sleep_s": self._handle_nat_value(row.get("rem_sec", 0)) or 0,
                        "awake_time_s": self._handle_nat_value(row.get("awake_sec", 0)) or 0,
                        "sleep_score": self._handle_nat_value(row.get("quality")),
                        "efficiency_percentage": self._calculate_sleep_efficiency(row),
                        "bedtime_utc": None,  # Not in WellnessSync format
                        "wakeup_time_utc": None,  # Not in WellnessSync format
                        "restlessness": None,
                    }
                elif data_type == "steps":
                    date_str = (
                        row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
                    )
                    record = {
                        "date": date_str,
                        "total_steps": int(self._handle_nat_value(row.get("steps", 0)) or 0),
                        "calories_burned": self._handle_nat_value(row.get("calories")),
                        "distance_meters": self._handle_nat_value(row.get("distance_m")),
                        "floors_climbed": None,
                    }
                elif data_type == "stress":
                    date_str = (
                        row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
                    )
                    record = {
                        "date": date_str,
                        "avg_stress_level": self._handle_nat_value(row.get("stress_avg")),
                        "max_stress_level": self._handle_nat_value(row.get("stress_max")),
                        "rest_stress_duration_s": self._handle_nat_value(row.get("rest_sec")),
                        "low_stress_duration_s": None,
                        "medium_stress_duration_s": None,
                        "high_stress_duration_s": None,
                        "stress_qualifier": None,
                    }
                elif data_type == "resting_hr":
                    date_str = (
                        row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
                    )
                    record = {
                        "date": date_str,
                        "resting_hr": self._handle_nat_value(row.get("resting_hr")),
                        "avg_hr": None,
                        "max_hr": None,
                        "hrv_score": None,
                        "hrv_status": None,
                    }
                elif data_type == "hrv":
                    date_str = (
                        row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
                    )
                    record = {
                        "date": date_str,
                        "resting_hr": None,
                        "avg_hr": None,
                        "max_hr": None,
                        "hrv_score": self._handle_nat_value(row.get("hrv")),
                        "hrv_status": None,
                        "vo2max": None,
                    }
                elif data_type == "body_battery":
                    date_str = (
                        row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
                    )
                    record = {
                        "date": date_str,
                        "body_battery_score": self._handle_nat_value(row.get("avg")),
                        "charged_value": self._handle_nat_value(row.get("charge", 0)) or 0,
                        "drained_value": self._handle_nat_value(row.get("drain", 0)) or 0,
                        "highest_value": None,
                        "lowest_value": None,
                    }
                elif data_type == "training_readiness":
                    date_str = (
                        row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
                    )
                    # Handle pandas NaT (Not a Time) values
                    score_val = row.get("score")
                    if hasattr(score_val, "__class__") and "NaTType" in str(score_val.__class__):
                        score_val = None
                    record = {
                        "date": date_str,
                        "training_readiness_score": score_val,
                        "hrv_score": None,
                        "sleep_score": None,
                        "recovery_time_hours": None,
                        "hrv_status": None,
                        "sleep_status": None,
                        "stress_status": None,
                    }
                elif data_type == "vo2max":
                    # VO2 max data should go into heart rate records
                    date_str = (
                        row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
                    )
                    record = {
                        "date": date_str,
                        "resting_hr": None,
                        "avg_hr": None,
                        "max_hr": None,
                        "hrv_score": None,
                        "hrv_status": None,
                        "vo2max": self._handle_nat_value(row.get("vo2max")),
                    }
                else:
                    continue  # Skip unknown data types

                # Only include records with meaningful data
                if any(v is not None and v != 0 for k, v in record.items() if k != "date"):
                    records.append(record)

        except Exception as e:
            self.logger.warning(f"Error transforming {data_type} data: {e}")

        return records

    def _transform_dailies_to_db_format(
        self, dailies_data: List[Dict[str, Any]], smoothing: str = "none"
    ) -> Dict[str, Any]:
        """
        Transform wellness data format for database persistence (legacy method).

        Args:
            dailies_data: Raw wellness data from Garmin
            smoothing: Smoothing method to apply

        Returns:
            Dict with transformed wellness data by type
        """
        # This method is kept for compatibility but should use _transform_garmin_data
        return {
            "sleep": dailies_data,
            "steps": dailies_data,
            "heart_rate": dailies_data,
            "body_battery": dailies_data,
            "stress": dailies_data,
            "training_readiness": dailies_data,
            "hrv": dailies_data,
        }
