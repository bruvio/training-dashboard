"""
Wellness Data Persistence Service Layer.

This service handles the transformation and persistence of wellness data
from the Garmin API sync operations to the database. It acts as the critical
bridge between the sync layer and the database models.
"""

from datetime import date, datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional

from app.data.db import session_scope
from app.data.garmin_models import (
    DailyBodyBattery,
    DailyHeartRate,
    DailySleep,
    DailySteps,
    DailyStress,
    DailyTrainingReadiness,
    PersonalRecords,
    UserProfile,
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
                        sleep_date = self._parse_date(sleep_data.get("date"))
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
                                bedtime_utc=sleep_data.get("bedtime_utc"),
                                wakeup_time_utc=sleep_data.get("wakeup_time_utc"),
                                total_sleep_time_s=sleep_data.get("total_sleep_time_s", 0),
                                deep_sleep_s=sleep_data.get("deep_sleep_s", 0),
                                light_sleep_s=sleep_data.get("light_sleep_s", 0),
                                rem_sleep_s=sleep_data.get("rem_sleep_s", 0),
                                awake_time_s=sleep_data.get("awake_time_s", 0),
                                sleep_score=sleep_data.get("sleep_score"),
                                restlessness=sleep_data.get("restlessness"),
                                efficiency_percentage=sleep_data.get("efficiency_percentage"),
                                data_source="garminconnect",
                                retrieved_at=datetime.now(timezone.utc),
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
                        steps_date = self._parse_date(steps_data.get("date"))
                        if not steps_date:
                            continue

                        # Check if record exists
                        existing = session.query(DailySteps).filter_by(date=steps_date).first()

                        if existing:
                            # Update existing record
                            existing.total_steps = steps_data.get("total_steps", 0)
                            existing.step_goal = steps_data.get("step_goal", 0)
                            existing.total_distance_m = steps_data.get("total_distance_m", 0)
                            existing.calories_burned = steps_data.get("calories_burned", 0)
                            existing.calories_bmr = steps_data.get("calories_bmr", 0)
                            existing.calories_active = steps_data.get("calories_active", 0)
                            existing.floors_climbed = steps_data.get("floors_climbed", 0)
                            existing.floors_goal = steps_data.get("floors_goal", 0)
                            existing.data_source = "garminconnect"
                            existing.retrieved_at = datetime.now(timezone.utc)
                        else:
                            # Create new record
                            steps_record = DailySteps(
                                date=steps_date,
                                total_steps=steps_data.get("total_steps", 0),
                                step_goal=steps_data.get("step_goal", 0),
                                total_distance_m=steps_data.get("total_distance_m", 0),
                                calories_burned=steps_data.get("calories_burned", 0),
                                calories_bmr=steps_data.get("calories_bmr", 0),
                                calories_active=steps_data.get("calories_active", 0),
                                floors_climbed=steps_data.get("floors_climbed", 0),
                                floors_goal=steps_data.get("floors_goal", 0),
                                data_source="garminconnect",
                                retrieved_at=datetime.now(timezone.utc),
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
                        hr_date = self._parse_date(hr_data.get("date"))
                        if not hr_date:
                            continue

                        # Check if record exists
                        existing = session.query(DailyHeartRate).filter_by(date=hr_date).first()

                        if existing:
                            # Update existing record
                            existing.resting_hr = hr_data.get("resting_hr")
                            existing.max_hr = hr_data.get("max_hr")
                            existing.avg_hr = hr_data.get("avg_hr")
                            existing.hrv_score = hr_data.get("hrv_score")
                            existing.hrv_status = hr_data.get("hrv_status")
                            existing.data_source = "garminconnect"
                            existing.retrieved_at = datetime.now(timezone.utc)
                        else:
                            # Create new record
                            hr_record = DailyHeartRate(
                                date=hr_date,
                                resting_hr=hr_data.get("resting_hr"),
                                max_hr=hr_data.get("max_hr"),
                                avg_hr=hr_data.get("avg_hr"),
                                hrv_score=hr_data.get("hrv_score"),
                                hrv_status=hr_data.get("hrv_status"),
                                data_source="garminconnect",
                                retrieved_at=datetime.now(timezone.utc),
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

    def persist_training_readiness_data(self, tr_records: List[Dict[str, Any]]) -> bool:
        """Persist Training Readiness data to database."""
        try:
            with session_scope() as session:
                persisted_count = 0

                for tr_data in tr_records:
                    try:
                        tr_date = self._parse_date(tr_data.get("date"))
                        if not tr_date:
                            continue

                        # Check if record exists
                        existing = session.query(DailyTrainingReadiness).filter_by(date=tr_date).first()

                        if existing:
                            # Update existing record
                            existing.training_readiness_score = tr_data.get("score")
                            existing.hrv_score = tr_data.get("hrv_weekly_average")
                            existing.sleep_score = tr_data.get("sleep_score")
                            existing.recovery_time_hours = (
                                tr_data.get("recovery_time", 0) // 60 if tr_data.get("recovery_time") else None
                            )
                            existing.hrv_status = tr_data.get("level")
                            existing.sleep_status = tr_data.get("feedback_short")
                            existing.stress_status = tr_data.get("feedback_long")
                            existing.data_source = "garminconnect"
                            existing.retrieved_at = datetime.utcnow()
                        else:
                            # Create new record
                            tr_record = DailyTrainingReadiness(
                                date=tr_date,
                                training_readiness_score=tr_data.get("score"),
                                hrv_score=tr_data.get("hrv_weekly_average"),
                                sleep_score=tr_data.get("sleep_score"),
                                recovery_time_hours=tr_data.get("recovery_time", 0) // 60
                                if tr_data.get("recovery_time")
                                else None,
                                hrv_status=tr_data.get("level"),
                                sleep_status=tr_data.get("feedback_short"),
                                stress_status=tr_data.get("feedback_long"),
                                data_source="garminconnect",
                                retrieved_at=datetime.utcnow(),
                            )
                            session.add(tr_record)

                        persisted_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to persist individual Training Readiness record: {e}")
                        continue

                logger.info(f"Successfully persisted {persisted_count} Training Readiness records")
                return persisted_count > 0

        except Exception as e:
            logger.error(f"Failed to persist Training Readiness data: {e}")
            return False

    def persist_stress_data(self, stress_records: List[Dict[str, Any]]) -> bool:
        """Persist stress data to database."""
        try:
            with session_scope() as session:
                persisted_count = 0

                for stress_data in stress_records:
                    try:
                        stress_date = self._parse_date(stress_data.get("date"))
                        if not stress_date:
                            continue

                        # Check if record exists
                        existing = session.query(DailyStress).filter_by(date=stress_date).first()

                        if existing:
                            # Update existing record
                            existing.avg_stress_level = stress_data.get("avg_stress_level")
                            existing.max_stress_level = stress_data.get("max_stress_level")
                            existing.rest_stress_level = stress_data.get("rest_stress_level")
                            existing.rest_minutes = stress_data.get("rest_minutes", 0)
                            existing.low_minutes = stress_data.get("low_minutes", 0)
                            existing.medium_minutes = stress_data.get("medium_minutes", 0)
                            existing.high_minutes = stress_data.get("high_minutes", 0)
                            existing.stress_qualifier = stress_data.get("stress_qualifier")
                            existing.data_source = "garminconnect"
                            existing.retrieved_at = datetime.now(timezone.utc)
                        else:
                            # Create new record
                            stress_record = DailyStress(
                                date=stress_date,
                                avg_stress_level=stress_data.get("avg_stress_level"),
                                max_stress_level=stress_data.get("max_stress_level"),
                                rest_stress_level=stress_data.get("rest_stress_level"),
                                rest_minutes=stress_data.get("rest_minutes", 0),
                                low_minutes=stress_data.get("low_minutes", 0),
                                medium_minutes=stress_data.get("medium_minutes", 0),
                                high_minutes=stress_data.get("high_minutes", 0),
                                stress_qualifier=stress_data.get("stress_qualifier"),
                                data_source="garminconnect",
                                retrieved_at=datetime.now(timezone.utc),
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

    def persist_personal_records_data(self, pr_records: List[Dict[str, Any]]) -> bool:
        """
        Persist personal records data to the database.

        Args:
            pr_records: List of personal record dictionaries

        Returns:
            bool: True if persistence was successful
        """
        try:
            with session_scope() as session:
                persisted_count = 0
                for pr_data in pr_records:
                    try:
                        # Check if record already exists
                        existing_record = (
                            session.query(PersonalRecords)
                            .filter(
                                PersonalRecords.activity_type == pr_data.get("activity_type"),
                                PersonalRecords.record_type == pr_data.get("record_type"),
                                PersonalRecords.activity_id == pr_data.get("activity_id"),
                            )
                            .first()
                        )

                        if existing_record:
                            # Update existing record if it's newer or has better value
                            if pr_data.get("achieved_date") and (
                                not existing_record.achieved_date
                                or pr_data["achieved_date"] >= existing_record.achieved_date
                            ):
                                existing_record.record_value = pr_data.get("record_value")
                                existing_record.record_unit = pr_data.get("record_unit")
                                existing_record.achieved_date = pr_data.get("achieved_date")
                                existing_record.activity_name = pr_data.get("activity_name")
                                existing_record.location = pr_data.get("location")
                                existing_record.retrieved_at = datetime.now(timezone.utc)
                                persisted_count += 1
                        else:
                            # Create new record
                            new_record = PersonalRecords(
                                activity_type=pr_data.get("activity_type"),
                                record_type=pr_data.get("record_type"),
                                record_value=pr_data.get("record_value"),
                                record_unit=pr_data.get("record_unit"),
                                activity_id=pr_data.get("activity_id"),
                                achieved_date=pr_data.get("achieved_date"),
                                activity_name=pr_data.get("activity_name"),
                                location=pr_data.get("location"),
                            )
                            session.add(new_record)
                            persisted_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to persist personal record: {e}")
                        continue

                session.commit()
                logger.info(f"Successfully persisted {persisted_count} personal records")
                return persisted_count > 0

        except Exception as e:
            logger.error(f"Failed to persist personal records data: {e}")
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

        # Training Readiness data
        if "training_readiness" in wellness_data and wellness_data["training_readiness"]:
            results["training_readiness"] = self.persist_training_readiness_data(wellness_data["training_readiness"])

        # Stress data
        if "stress" in wellness_data and wellness_data["stress"]:
            results["stress"] = self.persist_stress_data(wellness_data["stress"])

        # Personal records data
        if "personal_records" in wellness_data and wellness_data["personal_records"]:
            results["personal_records"] = self.persist_personal_records_data(wellness_data["personal_records"])

        # TODO: Implement persistence for remaining data types:
        # - intensity_minutes
        # - hydration
        # - respiration
        # - spo2
        # - training_status
        # - max_metrics

        successful_types = sum(1 for success in results.values() if success)
        total_types = len(results)

        logger.info(
            f"Wellness data persistence summary: {successful_types}/{total_types} data types persisted successfully"
        )

        return results

    def _parse_date(self, date_input: Any) -> Optional[date]:
        """Parse date input in various formats."""
        if not date_input:
            return None

        # If it's a datetime object, extract the date part
        if isinstance(date_input, datetime):
            return date_input.date()

        # If it's already a date object, return it
        if isinstance(date_input, date):
            return date_input

        try:
            # Try YYYY-MM-DD format
            return datetime.strptime(str(date_input), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            try:
                # Try timestamp format
                return datetime.fromtimestamp(int(date_input) / 1000).date()
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
        existing_record.bedtime_utc = sleep_data.get("bedtime_utc")
        existing_record.wakeup_time_utc = sleep_data.get("wakeup_time_utc")
        existing_record.total_sleep_time_s = sleep_data.get("total_sleep_time_s", 0)
        existing_record.deep_sleep_s = sleep_data.get("deep_sleep_s", 0)
        existing_record.light_sleep_s = sleep_data.get("light_sleep_s", 0)
        existing_record.rem_sleep_s = sleep_data.get("rem_sleep_s", 0)
        existing_record.awake_time_s = sleep_data.get("awake_time_s", 0)
        existing_record.sleep_score = sleep_data.get("sleep_score")
        existing_record.restlessness = sleep_data.get("restlessness")
        existing_record.efficiency_percentage = sleep_data.get("efficiency_percentage")
        existing_record.data_source = "garminconnect"
        existing_record.retrieved_at = datetime.now(timezone.utc)

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
