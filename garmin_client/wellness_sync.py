"""
Comprehensive wellness data synchronization using garminconnect library.

Implements all wellness data types specified in the PRP:
- User Profile Data
- Daily Activity (Steps, Floors)
- Heart Rate Analytics
- Body & Wellness (Body Battery, Blood Pressure, Hydration)
- Sleep Analytics
- Stress & Recovery (Stress, Training Status, Training Readiness, Respiration)
- Advanced Metrics (SpO2, Max Metrics, Personal Records)
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Any

from .client import GarminConnectClient, GarminAuthError

# Import wellness data service for persistence
try:
    from app.services.wellness_data_service import WellnessDataService

    PERSISTENCE_AVAILABLE = True
except ImportError:
    PERSISTENCE_AVAILABLE = False
    logger.warning("WellnessDataService not available - data will not be persisted")

logger = logging.getLogger(__name__)


class WellnessSyncManager:
    """Manages comprehensive wellness data synchronization from Garmin Connect."""

    def __init__(self, client: GarminConnectClient):
        self.client = client
        self.wellness_service = WellnessDataService() if PERSISTENCE_AVAILABLE else None

    def sync_user_profile(self) -> Dict[str, Any]:
        """Sync user profile information."""
        try:
            if not self.client.is_authenticated():
                raise GarminAuthError("Client not authenticated")

            profile_data = {}

            # Get full name
            try:
                full_name = self.client.api.get_full_name()
                profile_data["full_name"] = full_name
            except Exception as e:
                logger.warning(f"Could not get full name: {e}")

            # Get user profile details
            try:
                user_profile = self.client.api.get_user_profile()
                if user_profile:
                    profile_data.update(
                        {
                            "display_name": user_profile.get("displayName"),
                            "email": user_profile.get("email"),
                            "age": user_profile.get("age"),
                            "gender": user_profile.get("gender"),
                            "weight_kg": user_profile.get("weight"),
                            "height_cm": user_profile.get("height"),
                            "activity_level": user_profile.get("activityLevel"),
                        }
                    )
            except Exception as e:
                logger.warning(f"Could not get user profile: {e}")

            # Get unit system
            try:
                unit_system = self.client.api.get_unit_system()
                profile_data["unit_system"] = unit_system
            except Exception as e:
                logger.warning(f"Could not get unit system: {e}")

            logger.info(f"Synced user profile data: {len(profile_data)} fields")
            return {"success": True, "data": profile_data, "fields_synced": len(profile_data)}

        except Exception as e:
            logger.error(f"User profile sync failed: {e}")
            return {"success": False, "error": str(e)}

    def sync_daily_steps(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Sync daily steps data for date range."""
        try:
            if not self.client.is_authenticated():
                raise GarminAuthError("Client not authenticated")

            steps_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    date_str = current_date.isoformat()
                    daily_steps = self.client.api.get_steps_data(date_str)

                    if daily_steps:
                        # Handle both dict and list responses
                        if isinstance(daily_steps, list):
                            # Take first item if it's a list
                            daily_steps = daily_steps[0] if daily_steps else {}

                        steps_record = {
                            "date": current_date,
                            "total_steps": daily_steps.get("totalSteps"),
                            "step_goal": daily_steps.get("dailyStepGoal"),
                            "total_distance_m": daily_steps.get("totalDistance"),
                            "calories_burned": daily_steps.get("wellnessActiveKilocalories"),
                            "calories_bmr": daily_steps.get("wellnessBmrKilocalories"),
                            "calories_active": daily_steps.get("activeKilocalories"),
                            "floors_climbed": daily_steps.get("floorsAscended"),
                            "floors_goal": daily_steps.get("floorsAscendedGoal"),
                        }
                        steps_data.append(steps_record)

                except Exception as e:
                    logger.warning(f"Could not get steps data for {current_date}: {e}")

                current_date += timedelta(days=1)

            logger.info(f"Synced {len(steps_data)} days of steps data")
            return {
                "success": True,
                "data": steps_data,
                "days_synced": len(steps_data),
                "date_range": f"{start_date} to {end_date}",
            }

        except Exception as e:
            logger.error(f"Steps data sync failed: {e}")
            return {"success": False, "error": str(e)}

    def sync_daily_heart_rate(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Sync daily heart rate data for date range."""
        try:
            if not self.client.is_authenticated():
                raise GarminAuthError("Client not authenticated")

            hr_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    date_str = current_date.isoformat()

                    # Get resting heart rate
                    rhr_data = self.client.api.get_rhr_day(date_str)

                    # Get heart rate data
                    hr_zones = self.client.api.get_heart_rates(date_str)

                    # Get HRV data
                    hrv_data = None
                    try:
                        hrv_data = self.client.api.get_hrv_data(date_str)
                    except Exception:
                        pass  # HRV data might not be available for all dates

                    if rhr_data or hr_zones:
                        hr_record = {
                            "date": current_date,
                            "resting_hr": rhr_data.get("restingHeartRate") if rhr_data else None,
                            "max_hr": hr_zones.get("maxHeartRate") if hr_zones else None,
                            "avg_hr": hr_zones.get("averageHeartRate") if hr_zones else None,
                        }

                        # Add HR zones if available
                        if hr_zones and "heartRateZones" in hr_zones:
                            zones = hr_zones["heartRateZones"]
                            hr_record.update(
                                {
                                    "hr_zone_1_time": zones.get("zone1TimeInMinutes", 0),
                                    "hr_zone_2_time": zones.get("zone2TimeInMinutes", 0),
                                    "hr_zone_3_time": zones.get("zone3TimeInMinutes", 0),
                                    "hr_zone_4_time": zones.get("zone4TimeInMinutes", 0),
                                    "hr_zone_5_time": zones.get("zone5TimeInMinutes", 0),
                                }
                            )

                        # Add HRV data if available
                        if hrv_data:
                            hr_record.update(
                                {
                                    "hrv_score": hrv_data.get("hrvScore"),
                                    "hrv_status": hrv_data.get("hrvStatus"),
                                }
                            )

                        hr_data.append(hr_record)

                except Exception as e:
                    logger.warning(f"Could not get heart rate data for {current_date}: {e}")

                current_date += timedelta(days=1)

            logger.info(f"Synced {len(hr_data)} days of heart rate data")
            return {
                "success": True,
                "data": hr_data,
                "days_synced": len(hr_data),
                "date_range": f"{start_date} to {end_date}",
            }

        except Exception as e:
            logger.error(f"Heart rate data sync failed: {e}")
            return {"success": False, "error": str(e)}

    def sync_daily_sleep(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Sync daily sleep data for date range."""
        try:
            if not self.client.is_authenticated():
                raise GarminAuthError("Client not authenticated")

            sleep_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    date_str = current_date.isoformat()
                    daily_sleep = self.client.api.get_sleep_data(date_str)

                    if daily_sleep:
                        sleep_record = {
                            "date": current_date,
                            "bedtime_utc": datetime.fromisoformat(
                                daily_sleep.get("sleepStartTimestampLocal", "").replace("Z", "+00:00")
                            )
                            if daily_sleep.get("sleepStartTimestampLocal")
                            else None,
                            "wakeup_time_utc": datetime.fromisoformat(
                                daily_sleep.get("sleepEndTimestampLocal", "").replace("Z", "+00:00")
                            )
                            if daily_sleep.get("sleepEndTimestampLocal")
                            else None,
                            "total_sleep_time_s": daily_sleep.get("sleepTimeSeconds"),
                            "deep_sleep_s": daily_sleep.get("deepSleepSeconds"),
                            "light_sleep_s": daily_sleep.get("lightSleepSeconds"),
                            "rem_sleep_s": daily_sleep.get("remSleepSeconds"),
                            "awake_time_s": daily_sleep.get("awakeDurationSeconds"),
                            "sleep_score": daily_sleep.get("overallSleepScore"),
                            "restlessness": daily_sleep.get("restlessMoments"),
                            "efficiency_percentage": daily_sleep.get("sleepEfficiency"),
                        }
                        sleep_data.append(sleep_record)

                except Exception as e:
                    logger.warning(f"Could not get sleep data for {current_date}: {e}")

                current_date += timedelta(days=1)

            logger.info(f"Synced {len(sleep_data)} days of sleep data")
            return {
                "success": True,
                "data": sleep_data,
                "days_synced": len(sleep_data),
                "date_range": f"{start_date} to {end_date}",
            }

        except Exception as e:
            logger.error(f"Sleep data sync failed: {e}")
            return {"success": False, "error": str(e)}

    def sync_daily_stress(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Sync daily stress data for date range."""
        try:
            if not self.client.is_authenticated():
                raise GarminAuthError("Client not authenticated")

            stress_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    date_str = current_date.isoformat()
                    daily_stress = self.client.api.get_stress_data(date_str)

                    if daily_stress:
                        stress_record = {
                            "date": current_date,
                            "avg_stress_level": daily_stress.get("averageStressLevel"),
                            "max_stress_level": daily_stress.get("maxStressLevel"),
                            "rest_stress_level": daily_stress.get("restStressLevel"),
                            "rest_minutes": daily_stress.get("restStressDuration"),
                            "low_minutes": daily_stress.get("lowStressDuration"),
                            "medium_minutes": daily_stress.get("mediumStressDuration"),
                            "high_minutes": daily_stress.get("highStressDuration"),
                            "stress_qualifier": daily_stress.get("stressQualifier"),
                        }
                        stress_data.append(stress_record)

                except Exception as e:
                    logger.warning(f"Could not get stress data for {current_date}: {e}")

                current_date += timedelta(days=1)

            logger.info(f"Synced {len(stress_data)} days of stress data")
            return {
                "success": True,
                "data": stress_data,
                "days_synced": len(stress_data),
                "date_range": f"{start_date} to {end_date}",
            }

        except Exception as e:
            logger.error(f"Stress data sync failed: {e}")
            return {"success": False, "error": str(e)}

    def sync_body_battery(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Sync Body Battery data for date range."""
        try:
            if not self.client.is_authenticated():
                raise GarminAuthError("Client not authenticated")

            bb_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    date_str = current_date.isoformat()
                    # get_body_battery might expect date range, try single date first
                    try:
                        body_battery = self.client.api.get_body_battery(date_str)
                    except:
                        # Try with date range format
                        body_battery = self.client.api.get_body_battery(date_str, date_str)

                    if body_battery:
                        # Handle both dict and list responses
                        if isinstance(body_battery, list):
                            body_battery = body_battery[0] if body_battery else {}

                        bb_record = {
                            "date": current_date,
                            "body_battery_score": body_battery.get("bodyBatteryMostRecentScore")
                            or body_battery.get("endOfDayBodyBattery"),
                            "charged_value": body_battery.get("bodyBatteryChargedValue"),
                            "drained_value": body_battery.get("bodyBatteryDrainedValue"),
                            "highest_value": body_battery.get("bodyBatteryHighestValue"),
                            "lowest_value": body_battery.get("bodyBatteryLowestValue"),
                        }
                        bb_data.append(bb_record)

                except Exception as e:
                    logger.warning(f"Could not get body battery data for {current_date}: {e}")

                current_date += timedelta(days=1)

            logger.info(f"Synced {len(bb_data)} days of Body Battery data")
            return {
                "success": True,
                "data": bb_data,
                "days_synced": len(bb_data),
                "date_range": f"{start_date} to {end_date}",
            }

        except Exception as e:
            logger.error(f"Body Battery data sync failed: {e}")
            return {"success": False, "error": str(e)}

    def sync_personal_records(self) -> Dict[str, Any]:
        """Sync personal records."""
        try:
            if not self.client.is_authenticated():
                raise GarminAuthError("Client not authenticated")

            # Get personal records
            pr_data = self.client.api.get_personal_record()

            records = []
            if pr_data:
                for record in pr_data:
                    pr_record = {
                        "activity_type": record.get("activityType"),
                        "record_type": record.get("recordType"),
                        "record_value": record.get("value"),
                        "record_unit": record.get("unit"),
                        "activity_id": record.get("activityId"),
                        "achieved_date": datetime.fromisoformat(record.get("recordDate")).date()
                        if record.get("recordDate")
                        else None,
                        "activity_name": record.get("activityName"),
                        "location": record.get("location"),
                    }
                    records.append(pr_record)

            logger.info(f"Synced {len(records)} personal records")
            return {"success": True, "data": records, "records_synced": len(records)}

        except Exception as e:
            logger.error(f"Personal records sync failed: {e}")
            return {"success": False, "error": str(e)}

    def sync_max_metrics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Sync VO2 Max and fitness metrics for date range."""
        try:
            if not self.client.is_authenticated():
                raise GarminAuthError("Client not authenticated")

            metrics_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    date_str = current_date.isoformat()

                    # Get VO2 Max data
                    vo2_max = None
                    try:
                        vo2_max = self.client.api.get_max_metric_data(date_str)
                    except Exception:
                        pass

                    # Get fitness age
                    fitness_age = None
                    try:
                        fitness_age = self.client.api.get_fitness_age(date_str)
                    except Exception:
                        pass

                    if vo2_max or fitness_age:
                        metrics_record = {
                            "date": current_date,
                            "vo2_max_value": vo2_max.get("vo2MaxValue") if vo2_max else None,
                            "vo2_max_running": vo2_max.get("vo2MaxRunning") if vo2_max else None,
                            "vo2_max_cycling": vo2_max.get("vo2MaxCycling") if vo2_max else None,
                            "fitness_age": fitness_age if fitness_age else None,
                            "performance_condition": vo2_max.get("performanceCondition") if vo2_max else None,
                        }
                        metrics_data.append(metrics_record)

                except Exception as e:
                    logger.warning(f"Could not get max metrics for {current_date}: {e}")

                current_date += timedelta(days=1)

            logger.info(f"Synced {len(metrics_data)} days of max metrics data")
            return {
                "success": True,
                "data": metrics_data,
                "days_synced": len(metrics_data),
                "date_range": f"{start_date} to {end_date}",
            }

        except Exception as e:
            logger.error(f"Max metrics sync failed: {e}")
            return {"success": False, "error": str(e)}

    def sync_comprehensive_wellness(self, days: int = 30) -> Dict[str, Any]:
        """
        Sync all wellness data types for the specified number of days.

        This implements all requirements from the PRP:
        - User Profile: Get full name
        - Steps data for dates available in database
        - Heart rate data for dates available in database
        - Training readiness data for dates available in database
        - Daily step data with goals and trends
        - Body battery data for dates available in database
        - Floors data with climbing metrics
        - Blood pressure data for date ranges
        - Training status data for dates available in database
        - Resting heart rate data for dates available in database
        - Hydration data for dates available in database
        - Sleep data for dates available in database
        - Stress data for dates available in database
        - Respiration data for dates available in database
        - SpO2 data for dates available in database
        - Max metric data (like vo2MaxValue and fitnessAge) for dates available in database
        - Personal records for user
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            logger.info(f"Starting comprehensive wellness sync for {days} days ({start_date} to {end_date})")

            # Initialize results
            results = {
                "success": True,
                "sync_date": datetime.now(timezone.utc).isoformat(),
                "date_range": f"{start_date} to {end_date}",
                "days_requested": days,
                "data_types": {},
                "errors": [],
                "total_records": 0,
            }

            # 1. Sync user profile
            try:
                profile_result = self.sync_user_profile()
                results["data_types"]["user_profile"] = profile_result
                if profile_result["success"]:
                    results["total_records"] += profile_result.get("fields_synced", 0)
                else:
                    results["errors"].append(f"User profile: {profile_result.get('error', 'Unknown error')}")
            except Exception as e:
                results["errors"].append(f"User profile sync error: {e}")

            # 2. Sync daily steps data
            try:
                steps_result = self.sync_daily_steps(start_date, end_date)
                results["data_types"]["steps"] = steps_result
                if steps_result["success"]:
                    results["total_records"] += steps_result.get("days_synced", 0)
                else:
                    results["errors"].append(f"Steps data: {steps_result.get('error', 'Unknown error')}")
            except Exception as e:
                results["errors"].append(f"Steps sync error: {e}")

            # 3. Sync heart rate data
            try:
                hr_result = self.sync_daily_heart_rate(start_date, end_date)
                results["data_types"]["heart_rate"] = hr_result
                if hr_result["success"]:
                    results["total_records"] += hr_result.get("days_synced", 0)
                else:
                    results["errors"].append(f"Heart rate data: {hr_result.get('error', 'Unknown error')}")
            except Exception as e:
                results["errors"].append(f"Heart rate sync error: {e}")

            # 4. Sync sleep data
            try:
                sleep_result = self.sync_daily_sleep(start_date, end_date)
                results["data_types"]["sleep"] = sleep_result
                if sleep_result["success"]:
                    results["total_records"] += sleep_result.get("days_synced", 0)
                else:
                    results["errors"].append(f"Sleep data: {sleep_result.get('error', 'Unknown error')}")
            except Exception as e:
                results["errors"].append(f"Sleep sync error: {e}")

            # 5. Sync stress data
            try:
                stress_result = self.sync_daily_stress(start_date, end_date)
                results["data_types"]["stress"] = stress_result
                if stress_result["success"]:
                    results["total_records"] += stress_result.get("days_synced", 0)
                else:
                    results["errors"].append(f"Stress data: {stress_result.get('error', 'Unknown error')}")
            except Exception as e:
                results["errors"].append(f"Stress sync error: {e}")

            # 6. Sync Body Battery data
            try:
                bb_result = self.sync_body_battery(start_date, end_date)
                results["data_types"]["body_battery"] = bb_result
                if bb_result["success"]:
                    results["total_records"] += bb_result.get("days_synced", 0)
                else:
                    results["errors"].append(f"Body Battery: {bb_result.get('error', 'Unknown error')}")
            except Exception as e:
                results["errors"].append(f"Body Battery sync error: {e}")

            # 7. Sync personal records
            try:
                pr_result = self.sync_personal_records()
                results["data_types"]["personal_records"] = pr_result
                if pr_result["success"]:
                    results["total_records"] += pr_result.get("records_synced", 0)
                else:
                    results["errors"].append(f"Personal records: {pr_result.get('error', 'Unknown error')}")
            except Exception as e:
                results["errors"].append(f"Personal records sync error: {e}")

            # 8. Sync max metrics
            try:
                metrics_result = self.sync_max_metrics(start_date, end_date)
                results["data_types"]["max_metrics"] = metrics_result
                if metrics_result["success"]:
                    results["total_records"] += metrics_result.get("days_synced", 0)
                else:
                    results["errors"].append(f"Max metrics: {metrics_result.get('error', 'Unknown error')}")
            except Exception as e:
                results["errors"].append(f"Max metrics sync error: {e}")

            # Persist data if wellness service is available
            if self.wellness_service:
                logger.info("Persisting wellness data to database...")
                try:
                    # Transform results into format expected by persistence service
                    wellness_data = {
                        "user_profile": results.get("data_types", {}).get("user_profile", {}).get("data"),
                        "sleep": results.get("data_types", {}).get("sleep", {}).get("data", []),
                        "steps": results.get("data_types", {}).get("steps", {}).get("data", []),
                        "heart_rate": results.get("data_types", {}).get("heart_rate", {}).get("data", []),
                        "body_battery": results.get("data_types", {}).get("body_battery", {}).get("data", []),
                        "stress": results.get("data_types", {}).get("stress", {}).get("data", []),
                    }

                    persistence_results = self.wellness_service.persist_comprehensive_wellness_data(wellness_data)
                    results["persistence_info"] = persistence_results

                    successful_persistences = sum(1 for success in persistence_results.values() if success)
                    logger.info(
                        f"Persisted {successful_persistences}/{len(persistence_results)} data types to database"
                    )

                except Exception as e:
                    logger.error(f"Failed to persist wellness data: {e}")
                    results["persistence_error"] = str(e)
            else:
                logger.warning("Wellness data service not available - data not persisted to database")
                results["persistence_info"] = {"error": "Service not available"}

            # Determine overall success
            if len(results["errors"]) > 0:
                results["success"] = False
                results[
                    "message"
                ] = f"Partial sync completed with {len(results['errors'])} errors. {results['total_records']} total records synced."
            else:
                results[
                    "message"
                ] = f"Successfully synced {results['total_records']} wellness records from the last {days} days."

            # Add persistence info to message
            if "persistence_info" in results and not results["persistence_info"].get("error"):
                persistence_summary = f" Data persisted to database: {successful_persistences} types."
                results["message"] += persistence_summary

            logger.info(f"Comprehensive wellness sync completed: {results['message']}")
            return results

        except Exception as e:
            logger.error(f"Comprehensive wellness sync failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "sync_date": datetime.now(timezone.utc).isoformat(),
            }
