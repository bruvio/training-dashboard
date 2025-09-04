"""
Wellness Data Persistence Service Layer.

This service handles the transformation and persistence of wellness data
from the Garmin API sync operations to the database. It acts as the critical
bridge between the sync layer and the database models.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional


from app.data.db import session_scope
from app.data.garmin_models import (
    UserProfile,
    DailySleep,
    DailyStress,
    DailySteps,
    DailyBodyBattery,
    DailyHeartRate,
)

logger = logging.getLogger(__name__)


class WellnessDataService:
    """Service for persisting wellness data to database."""

    def persist_user_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Persist user profile data to database."""
        try:
            with session_scope() as session:
                # Check if profile exists
                existing = (
                    session.query(UserProfile).filter_by(user_id=str(profile_data.get("userProfileId", ""))).first()
                )

                if existing:
                    # Update existing profile
                    # Update existing profile with valid fields only
                    if profile_data.get("displayName"):
                        existing.display_name = profile_data.get("displayName")
                    if profile_data.get("fullName"):
                        existing.full_name = profile_data.get("fullName")
                    if profile_data.get("email"):
                        existing.email = profile_data.get("email")
                    if profile_data.get("gender"):
                        existing.gender = profile_data.get("gender")
                    if profile_data.get("timeZone"):
                        existing.time_zone = profile_data.get("timeZone")
                    existing.data_source = "garminconnect"
                    existing.retrieved_at = datetime.utcnow()
                else:
                    # Create new profile
                    profile = UserProfile(
                        user_id=str(profile_data.get("userProfileId", "")),
                        display_name=profile_data.get("displayName"),
                        full_name=profile_data.get("fullName"),
                        email=profile_data.get("email"),
                        gender=profile_data.get("gender"),
                        time_zone=profile_data.get("timeZone"),
                        data_source="garminconnect",
                        retrieved_at=datetime.utcnow(),
                    )
                    session.add(profile)

                logger.info("Successfully persisted user profile data")
                return True

        except Exception as e:
            logger.error(f"Failed to persist user profile: {e}")
            return False

    def persist_sleep_data(self, sleep_records: List[Dict[str, Any]]) -> bool:
        """Persist sleep data to database."""
        try:
            with session_scope() as session:
                persisted_count = 0

                for sleep_data in sleep_records:
                    try:
                        sleep_date = self._parse_date(sleep_data.get("calendarDate"))
                        if not sleep_date:
                            continue

                        # Check if record exists
                        existing = session.query(DailySleep).filter_by(date=sleep_date).first()

                        if existing:
                            # Update existing record
                            self._update_sleep_record(existing, sleep_data)
                        else:
                            # Create new record
                            sleep_record = DailySleep(
                                date=sleep_date,
                                bedtime_utc=self._parse_datetime(sleep_data.get("sleepTimeSeconds")),
                                wakeup_time_utc=self._parse_datetime(sleep_data.get("sleepEndTimestampGMT")),
                                total_sleep_time_s=sleep_data.get("sleepTimeSeconds", 0),
                                deep_sleep_s=sleep_data.get("deepSleepSeconds", 0),
                                light_sleep_s=sleep_data.get("lightSleepSeconds", 0),
                                rem_sleep_s=sleep_data.get("remSleepSeconds", 0),
                                awake_time_s=sleep_data.get("awakeSleepSeconds", 0),
                                sleep_score=sleep_data.get("overallSleepScore"),
                                restlessness=sleep_data.get("restlessness"),
                                data_source="garminconnect",
                                retrieved_at=datetime.utcnow(),
                            )
                            session.add(sleep_record)

                        persisted_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to persist individual sleep record: {e}")
                        continue

                logger.info(f"Successfully persisted {persisted_count} sleep records")
                return persisted_count > 0

        except Exception as e:
            logger.error(f"Failed to persist sleep data: {e}")
            return False

    def persist_steps_data(self, steps_records: List[Dict[str, Any]]) -> bool:
        """Persist steps data to database."""
        try:
            with session_scope() as session:
                persisted_count = 0

                for steps_data in steps_records:
                    try:
                        steps_date = self._parse_date(steps_data.get("calendarDate"))
                        if not steps_date:
                            continue

                        # Check if record exists
                        existing = session.query(DailySteps).filter_by(date=steps_date).first()

                        if existing:
                            # Update existing record
                            existing.total_steps = steps_data.get("totalSteps", 0)
                            existing.step_goal = steps_data.get("dailyStepGoal", 0)
                            existing.total_distance_m = steps_data.get("totalDistance", 0)
                            existing.calories_burned = steps_data.get("wellnessKilocalories", 0)
                            existing.data_source = "garminconnect"
                            existing.retrieved_at = datetime.utcnow()
                        else:
                            # Create new record
                            steps_record = DailySteps(
                                date=steps_date,
                                total_steps=steps_data.get("totalSteps", 0),
                                step_goal=steps_data.get("dailyStepGoal", 0),
                                total_distance_m=steps_data.get("totalDistance", 0),
                                calories_burned=steps_data.get("wellnessKilocalories", 0),
                                data_source="garminconnect",
                                retrieved_at=datetime.utcnow(),
                            )
                            session.add(steps_record)

                        persisted_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to persist individual steps record: {e}")
                        continue

                logger.info(f"Successfully persisted {persisted_count} steps records")
                return persisted_count > 0

        except Exception as e:
            logger.error(f"Failed to persist steps data: {e}")
            return False

    def persist_heart_rate_data(self, hr_records: List[Dict[str, Any]]) -> bool:
        """Persist heart rate data to database."""
        try:
            with session_scope() as session:
                persisted_count = 0

                for hr_data in hr_records:
                    try:
                        hr_date = self._parse_date(hr_data.get("calendarDate"))
                        if not hr_date:
                            continue

                        # Check if record exists
                        existing = session.query(DailyHeartRate).filter_by(date=hr_date).first()

                        if existing:
                            # Update existing record
                            existing.resting_hr = hr_data.get("restingHeartRate")
                            existing.max_hr = hr_data.get("maxHeartRate")
                            existing.avg_hr = hr_data.get("averageHeartRate")
                            existing.data_source = "garminconnect"
                            existing.retrieved_at = datetime.utcnow()
                        else:
                            # Create new record
                            hr_record = DailyHeartRate(
                                date=hr_date,
                                resting_hr=hr_data.get("restingHeartRate"),
                                max_hr=hr_data.get("maxHeartRate"),
                                avg_hr=hr_data.get("averageHeartRate"),
                                data_source="garminconnect",
                                retrieved_at=datetime.utcnow(),
                            )
                            session.add(hr_record)

                        persisted_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to persist individual heart rate record: {e}")
                        continue

                logger.info(f"Successfully persisted {persisted_count} heart rate records")
                return persisted_count > 0

        except Exception as e:
            logger.error(f"Failed to persist heart rate data: {e}")
            return False

    def persist_body_battery_data(self, bb_records: List[Dict[str, Any]]) -> bool:
        """Persist Body Battery data to database."""
        try:
            with session_scope() as session:
                persisted_count = 0

                for bb_data in bb_records:
                    try:
                        bb_date = self._parse_date(bb_data.get("date"))
                        if not bb_date:
                            continue

                        # Check if record exists
                        existing = session.query(DailyBodyBattery).filter_by(date=bb_date).first()

                        if existing:
                            # Update existing record
                            existing.charged_value = bb_data.get("charged", 0)
                            existing.drained_value = bb_data.get("drained", 0)
                            existing.highest_value = bb_data.get("highestLevel", 0)
                            existing.lowest_value = bb_data.get("lowestLevel", 0)
                            existing.data_source = "garminconnect"
                            existing.retrieved_at = datetime.utcnow()
                        else:
                            # Create new record
                            bb_record = DailyBodyBattery(
                                date=bb_date,
                                charged_value=bb_data.get("charged", 0),
                                drained_value=bb_data.get("drained", 0),
                                highest_value=bb_data.get("highestLevel", 0),
                                lowest_value=bb_data.get("lowestLevel", 0),
                                data_source="garminconnect",
                                retrieved_at=datetime.utcnow(),
                            )
                            session.add(bb_record)

                        persisted_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to persist individual Body Battery record: {e}")
                        continue

                logger.info(f"Successfully persisted {persisted_count} Body Battery records")
                return persisted_count > 0

        except Exception as e:
            logger.error(f"Failed to persist Body Battery data: {e}")
            return False

    def persist_stress_data(self, stress_records: List[Dict[str, Any]]) -> bool:
        """Persist stress data to database."""
        try:
            with session_scope() as session:
                persisted_count = 0

                for stress_data in stress_records:
                    try:
                        stress_date = self._parse_date(stress_data.get("calendarDate"))
                        if not stress_date:
                            continue

                        # Check if record exists
                        existing = session.query(DailyStress).filter_by(date=stress_date).first()

                        if existing:
                            # Update existing record
                            existing.avg_stress_level = stress_data.get("overallStressLevel")
                            existing.rest_minutes = stress_data.get("restStressDuration", 0) // 60
                            existing.low_minutes = stress_data.get("lowStressDuration", 0) // 60
                            existing.medium_minutes = stress_data.get("mediumStressDuration", 0) // 60
                            existing.high_minutes = stress_data.get("highStressDuration", 0) // 60
                            existing.stress_qualifier = stress_data.get("stressQualifier")
                            existing.data_source = "garminconnect"
                            existing.retrieved_at = datetime.utcnow()
                        else:
                            # Create new record
                            stress_record = DailyStress(
                                date=stress_date,
                                avg_stress_level=stress_data.get("overallStressLevel"),
                                rest_minutes=stress_data.get("restStressDuration", 0) // 60,
                                low_minutes=stress_data.get("lowStressDuration", 0) // 60,
                                medium_minutes=stress_data.get("mediumStressDuration", 0) // 60,
                                high_minutes=stress_data.get("highStressDuration", 0) // 60,
                                stress_qualifier=stress_data.get("stressQualifier"),
                                data_source="garminconnect",
                                retrieved_at=datetime.utcnow(),
                            )
                            session.add(stress_record)

                        persisted_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to persist individual stress record: {e}")
                        continue

                logger.info(f"Successfully persisted {persisted_count} stress records")
                return persisted_count > 0

        except Exception as e:
            logger.error(f"Failed to persist stress data: {e}")
            return False

    def persist_comprehensive_wellness_data(self, wellness_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Persist comprehensive wellness data from sync operations.

        Args:
            wellness_data: Dictionary containing all wellness data types

        Returns:
            Dictionary with success status for each data type
        """
        results = {}

        # User profile data
        if "user_profile" in wellness_data:
            results["user_profile"] = self.persist_user_profile(wellness_data["user_profile"])

        # Sleep data
        if "sleep" in wellness_data and wellness_data["sleep"]:
            results["sleep"] = self.persist_sleep_data(wellness_data["sleep"])

        # Steps data
        if "steps" in wellness_data and wellness_data["steps"]:
            results["steps"] = self.persist_steps_data(wellness_data["steps"])

        # Heart rate data
        if "heart_rate" in wellness_data and wellness_data["heart_rate"]:
            results["heart_rate"] = self.persist_heart_rate_data(wellness_data["heart_rate"])

        # Body Battery data
        if "body_battery" in wellness_data and wellness_data["body_battery"]:
            results["body_battery"] = self.persist_body_battery_data(wellness_data["body_battery"])

        # Stress data
        if "stress" in wellness_data and wellness_data["stress"]:
            results["stress"] = self.persist_stress_data(wellness_data["stress"])

        # TODO: Implement persistence for remaining data types:
        # - intensity_minutes
        # - hydration
        # - respiration
        # - spo2
        # - training_readiness
        # - training_status
        # - max_metrics
        # - personal_records

        successful_types = sum(1 for success in results.values() if success)
        total_types = len(results)

        logger.info(
            f"Wellness data persistence summary: {successful_types}/{total_types} data types persisted successfully"
        )

        return results

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string in various formats."""
        if not date_str:
            return None

        try:
            # Try YYYY-MM-DD format
            return datetime.strptime(str(date_str), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            try:
                # Try timestamp format
                return datetime.fromtimestamp(int(date_str) / 1000).date()
            except (ValueError, TypeError):
                return None

    def _parse_datetime(self, timestamp: Any) -> Optional[datetime]:
        """Parse timestamp to datetime."""
        if not timestamp:
            return None

        try:
            return datetime.fromtimestamp(int(timestamp) / 1000)
        except (ValueError, TypeError):
            return None

    def _map_profile_field(self, api_field: str) -> str:
        """Map API field names to database field names."""
        field_mapping = {
            "userProfileId": "user_id",
            "displayName": "display_name",
            "fullName": "full_name",
            "birthDate": "birth_date",
            "timeZone": "time_zone",
            "measurementSystem": "measurement_system",
        }
        return field_mapping.get(api_field, api_field.lower())

    def _update_sleep_record(self, existing_record: DailySleep, sleep_data: Dict[str, Any]):
        """Update existing sleep record with new data."""
        existing_record.bedtime_utc = self._parse_datetime(sleep_data.get("sleepTimeSeconds"))
        existing_record.wakeup_time_utc = self._parse_datetime(sleep_data.get("sleepEndTimestampGMT"))
        existing_record.total_sleep_time_s = sleep_data.get("sleepTimeSeconds", 0)
        existing_record.deep_sleep_s = sleep_data.get("deepSleepSeconds", 0)
        existing_record.light_sleep_s = sleep_data.get("lightSleepSeconds", 0)
        existing_record.rem_sleep_s = sleep_data.get("remSleepSeconds", 0)
        existing_record.awake_time_s = sleep_data.get("awakeSleepSeconds", 0)
        existing_record.sleep_score = sleep_data.get("overallSleepScore")
        existing_record.restlessness = sleep_data.get("restlessness")
        existing_record.data_source = "garminconnect"
        existing_record.retrieved_at = datetime.utcnow()

    def get_wellness_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get wellness data summary for the dashboard."""
        try:
            with session_scope() as session:
                end_date = date.today()
                start_date = date.today() - timedelta(days=days)

                # Get counts for each data type
                sleep_count = (
                    session.query(DailySleep).filter(DailySleep.date >= start_date, DailySleep.date <= end_date).count()
                )

                steps_count = (
                    session.query(DailySteps).filter(DailySteps.date >= start_date, DailySteps.date <= end_date).count()
                )

                hr_count = (
                    session.query(DailyHeartRate)
                    .filter(DailyHeartRate.date >= start_date, DailyHeartRate.date <= end_date)
                    .count()
                )

                bb_count = (
                    session.query(DailyBodyBattery)
                    .filter(DailyBodyBattery.date >= start_date, DailyBodyBattery.date <= end_date)
                    .count()
                )

                stress_count = (
                    session.query(DailyStress)
                    .filter(DailyStress.date >= start_date, DailyStress.date <= end_date)
                    .count()
                )

                return {
                    "period_days": days,
                    "data_availability": {
                        "sleep": sleep_count,
                        "steps": steps_count,
                        "heart_rate": hr_count,
                        "body_battery": bb_count,
                        "stress": stress_count,
                    },
                    "total_records": sleep_count + steps_count + hr_count + bb_count + stress_count,
                    "coverage_percentage": min(
                        100, (sleep_count + steps_count + hr_count + bb_count + stress_count) / (days * 5) * 100
                    ),
                }

        except Exception as e:
            logger.error(f"Failed to get wellness summary: {e}")
            return {
                "period_days": days,
                "data_availability": {},
                "total_records": 0,
                "coverage_percentage": 0,
                "error": str(e),
            }
