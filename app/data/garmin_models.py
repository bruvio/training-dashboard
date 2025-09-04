"""
Database models for comprehensive Garmin wellness data via garminconnect library.

These models support all wellness data types specified in the PRP:
- User Profile Data
- Daily Activity (Steps, Floors)
- Heart Rate Analytics
- Body & Wellness (Body Battery, Blood Pressure, Hydration)
- Sleep Analytics
- Stress & Recovery (Stress, Training Status, Training Readiness, Respiration)
- Advanced Metrics (SpO2, Max Metrics, Personal Records)
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Float, Index, Integer, String, Text, Boolean

# Use same base class as other models
from .models import Base, mapped_column


class UserProfile(Base):
    """User profile information from Garmin Connect."""

    __tablename__ = "user_profile"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(String(100), unique=True, index=True)  # Garmin user ID

    # Profile information
    full_name = mapped_column(String(255))
    display_name = mapped_column(String(255))
    email = mapped_column(String(255))

    # Physical attributes
    age = mapped_column(Integer)
    gender = mapped_column(String(10))
    weight_kg = mapped_column(Float)
    height_cm = mapped_column(Float)

    # Activity level and preferences
    activity_level = mapped_column(String(50))
    unit_system = mapped_column(String(20))  # metric/imperial
    time_zone = mapped_column(String(50))

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_user_profile_user_id", "user_id"),
        Index("ix_user_profile_retrieved", "retrieved_at"),
    )


class DailySleep(Base):
    """Daily sleep data from Garmin Connect."""

    __tablename__ = "daily_sleep"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Sleep timing
    bedtime_utc = mapped_column(DateTime(timezone=True))
    wakeup_time_utc = mapped_column(DateTime(timezone=True))

    # Sleep metrics (all in seconds unless noted)
    total_sleep_time_s = mapped_column(Integer)
    deep_sleep_s = mapped_column(Integer)
    light_sleep_s = mapped_column(Integer)
    rem_sleep_s = mapped_column(Integer)
    awake_time_s = mapped_column(Integer)

    # Sleep quality metrics
    sleep_score = mapped_column(Integer)  # 0-100 sleep score
    restlessness = mapped_column(Float)
    efficiency_percentage = mapped_column(Float)

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_sleep_date", "date"),
        Index("ix_sleep_retrieved", "retrieved_at"),
    )


class DailyStress(Base):
    """Daily stress data from Garmin Connect."""

    __tablename__ = "daily_stress"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Stress metrics
    avg_stress_level = mapped_column(Integer)  # Average stress level (0-100)
    max_stress_level = mapped_column(Integer)  # Peak stress level
    rest_stress_level = mapped_column(Integer)  # Resting stress level

    # Stress breakdown (minutes spent in each level)
    rest_minutes = mapped_column(Integer)  # Minutes in rest (0-25)
    low_minutes = mapped_column(Integer)  # Minutes in low stress (26-50)
    medium_minutes = mapped_column(Integer)  # Minutes in medium stress (51-75)
    high_minutes = mapped_column(Integer)  # Minutes in high stress (76-100)

    # Overall wellness indicators
    stress_qualifier = mapped_column(String(20))  # "balanced", "stressful", etc.

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_stress_date", "date"),
        Index("ix_stress_avg", "avg_stress_level"),
    )


class DailySteps(Base):
    """Daily steps and activity data from Garmin Connect."""

    __tablename__ = "daily_steps"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Step metrics
    total_steps = mapped_column(Integer)
    step_goal = mapped_column(Integer)

    # Distance metrics
    total_distance_m = mapped_column(Float)

    # Calorie metrics
    calories_burned = mapped_column(Integer)
    calories_bmr = mapped_column(Integer)  # Base metabolic rate calories
    calories_active = mapped_column(Integer)  # Active calories

    # Activity metrics
    floors_climbed = mapped_column(Integer)
    floors_goal = mapped_column(Integer)

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_steps_date", "date"),
        Index("ix_steps_total", "total_steps"),
    )


class DailyIntensityMinutes(Base):
    """Daily intensity minutes from Garmin Connect."""

    __tablename__ = "daily_intensity"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Intensity metrics (WHO/AHA guidelines)
    vigorous_minutes = mapped_column(Integer)  # High intensity minutes
    moderate_minutes = mapped_column(Integer)  # Moderate intensity minutes

    # Goals and targets
    vigorous_goal = mapped_column(Integer)  # Weekly vigorous goal
    moderate_goal = mapped_column(Integer)  # Weekly moderate goal

    # Intensity score
    intensity_score = mapped_column(Integer)  # Overall intensity score

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_intensity_date", "date"),
        Index("ix_intensity_score", "intensity_score"),
    )


class DailyBodyBattery(Base):
    """Body Battery data from Garmin Connect."""

    __tablename__ = "daily_body_battery"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Body Battery metrics
    body_battery_score = mapped_column(Integer)  # 0-100
    charged_value = mapped_column(Integer)  # Energy gained
    drained_value = mapped_column(Integer)  # Energy lost
    highest_value = mapped_column(Integer)  # Peak value
    lowest_value = mapped_column(Integer)  # Lowest value

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_body_battery_date", "date"),
        Index("ix_body_battery_score", "body_battery_score"),
    )


class BloodPressureReadings(Base):
    """Blood pressure readings from Garmin Connect."""

    __tablename__ = "blood_pressure_readings"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, index=True)
    reading_time = mapped_column(DateTime(timezone=True))

    # Blood pressure metrics
    systolic = mapped_column(Integer)
    diastolic = mapped_column(Integer)
    pulse = mapped_column(Integer)

    # Additional context
    notes = mapped_column(Text)

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_bp_date", "date"),
        Index("ix_bp_reading_time", "reading_time"),
    )


class DailyHydration(Base):
    """Hydration tracking from Garmin Connect."""

    __tablename__ = "daily_hydration"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Hydration metrics
    goal_ml = mapped_column(Integer)
    consumed_ml = mapped_column(Integer)
    percentage_goal = mapped_column(Float)

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_hydration_date", "date"),
        Index("ix_hydration_consumed", "consumed_ml"),
    )


class DailyRespiration(Base):
    """Respiration data from Garmin Connect."""

    __tablename__ = "daily_respiration"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Respiration metrics
    avg_respiration_rate = mapped_column(Float)  # breaths per minute
    max_respiration_rate = mapped_column(Float)
    min_respiration_rate = mapped_column(Float)

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_respiration_date", "date"),
        Index("ix_respiration_avg", "avg_respiration_rate"),
    )


class DailySpo2(Base):
    """SpO2 (blood oxygen) data from Garmin Connect."""

    __tablename__ = "daily_spo2"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # SpO2 metrics
    avg_spo2_percentage = mapped_column(Float)  # Average oxygen saturation
    min_spo2_percentage = mapped_column(Float)  # Minimum oxygen saturation
    max_spo2_percentage = mapped_column(Float)  # Maximum oxygen saturation

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_spo2_date", "date"),
        Index("ix_spo2_avg", "avg_spo2_percentage"),
    )


class DailyTrainingReadiness(Base):
    """Training readiness data from Garmin Connect."""

    __tablename__ = "daily_training_readiness"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Training readiness metrics
    training_readiness_score = mapped_column(Integer)  # 0-100
    hrv_score = mapped_column(Integer)
    sleep_score = mapped_column(Integer)
    recovery_time_hours = mapped_column(Integer)

    # Contributing factors
    hrv_status = mapped_column(String(50))
    sleep_status = mapped_column(String(50))
    stress_status = mapped_column(String(50))

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_training_readiness_date", "date"),
        Index("ix_training_readiness_score", "training_readiness_score"),
    )


class TrainingStatus(Base):
    """Training status data from Garmin Connect."""

    __tablename__ = "training_status"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Training status metrics
    training_status_key = mapped_column(String(50))  # e.g., "MAINTAINING", "PRODUCTIVE"
    training_status_name = mapped_column(String(100))  # Human readable name
    load_ratio = mapped_column(Float)  # Training load ratio

    # Training load details
    acute_load = mapped_column(Float)  # Short term training load
    chronic_load = mapped_column(Float)  # Long term training load

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_training_status_date", "date"),
        Index("ix_training_status_key", "training_status_key"),
    )


class MaxMetrics(Base):
    """Max metrics (VO2 Max, Fitness Age, etc.) from Garmin Connect."""

    __tablename__ = "max_metrics"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # VO2 Max metrics
    vo2_max_value = mapped_column(Float)
    vo2_max_running = mapped_column(Float)  # Running specific VO2 Max
    vo2_max_cycling = mapped_column(Float)  # Cycling specific VO2 Max

    # Fitness metrics
    fitness_age = mapped_column(Integer)  # Calculated fitness age

    # Performance condition
    performance_condition = mapped_column(Integer)  # -20 to +20

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_max_metrics_date", "date"),
        Index("ix_vo2_max", "vo2_max_value"),
        Index("ix_fitness_age", "fitness_age"),
    )


class PersonalRecords(Base):
    """Personal records from Garmin Connect."""

    __tablename__ = "personal_records"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    activity_type = mapped_column(String(50), index=True)  # e.g., "running", "cycling"
    record_type = mapped_column(String(50), index=True)  # e.g., "fastest_5k", "longest_distance"

    # Record details
    record_value = mapped_column(Float)  # The actual record value
    record_unit = mapped_column(String(20))  # Unit of measurement
    activity_id = mapped_column(String(100))  # Associated activity ID
    achieved_date = mapped_column(Date)  # When the record was set

    # Additional context
    activity_name = mapped_column(String(255))  # Name of the record-setting activity
    location = mapped_column(String(255))  # Where the record was set

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_pr_activity_type", "activity_type"),
        Index("ix_pr_record_type", "record_type"),
        Index("ix_pr_achieved_date", "achieved_date"),
        Index("ix_pr_record_value", "record_value"),
    )


class DailyHeartRate(Base):
    """Daily heart rate data from Garmin Connect."""

    __tablename__ = "daily_heart_rate"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Heart rate metrics
    resting_hr = mapped_column(Integer)  # Resting heart rate
    max_hr = mapped_column(Integer)  # Maximum heart rate for the day
    avg_hr = mapped_column(Integer)  # Average heart rate

    # Time in heart rate zones (minutes)
    hr_zone_1_time = mapped_column(Integer)  # Very light
    hr_zone_2_time = mapped_column(Integer)  # Light
    hr_zone_3_time = mapped_column(Integer)  # Moderate
    hr_zone_4_time = mapped_column(Integer)  # Hard
    hr_zone_5_time = mapped_column(Integer)  # Maximum

    # HRV data
    hrv_score = mapped_column(Float)  # Heart Rate Variability score
    hrv_status = mapped_column(String(50))  # HRV status description

    # Data source tracking
    data_source = mapped_column(String(50), default="garminconnect")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_hr_date", "date"),
        Index("ix_resting_hr", "resting_hr"),
        Index("ix_hrv_score", "hrv_score"),
    )


class GarminSession(Base):
    """Track Garmin Connect authentication sessions and data sync status."""

    __tablename__ = "garmin_sessions"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(String(255), index=True)

    # Session tracking
    authenticated_at = mapped_column(DateTime(timezone=True))
    last_sync_at = mapped_column(DateTime(timezone=True))
    session_valid = mapped_column(Boolean, default=True)

    # Sync progress tracking
    last_sleep_sync = mapped_column(Date)
    last_stress_sync = mapped_column(Date)
    last_steps_sync = mapped_column(Date)
    last_intensity_sync = mapped_column(Date)
    last_heart_rate_sync = mapped_column(Date)
    last_body_battery_sync = mapped_column(Date)
    last_blood_pressure_sync = mapped_column(Date)
    last_hydration_sync = mapped_column(Date)
    last_respiration_sync = mapped_column(Date)
    last_spo2_sync = mapped_column(Date)
    last_training_readiness_sync = mapped_column(Date)
    last_training_status_sync = mapped_column(Date)
    last_max_metrics_sync = mapped_column(Date)
    last_personal_records_sync = mapped_column(Date)

    # Error tracking
    last_error = mapped_column(Text)
    error_count = mapped_column(Integer, default=0)

    __table_args__ = (
        Index("ix_garmin_session_email", "email"),
        Index("ix_garmin_session_auth", "authenticated_at"),
        Index("ix_garmin_session_valid", "session_valid"),
    )


class WellnessDataTransferObject:
    """Data transfer object for consolidated wellness data from garminconnect APIs."""

    def __init__(
        self,
        date: date,
        user_profile: Optional[dict] = None,
        sleep_data: Optional[dict] = None,
        stress_data: Optional[dict] = None,
        steps_data: Optional[dict] = None,
        intensity_data: Optional[dict] = None,
        body_battery_data: Optional[dict] = None,
        blood_pressure_data: Optional[dict] = None,
        hydration_data: Optional[dict] = None,
        respiration_data: Optional[dict] = None,
        spo2_data: Optional[dict] = None,
        training_readiness_data: Optional[dict] = None,
        training_status_data: Optional[dict] = None,
        max_metrics_data: Optional[dict] = None,
        personal_records_data: Optional[list] = None,
        heart_rate_data: Optional[dict] = None,
    ):
        self.date = date
        self.user_profile = user_profile or {}
        self.sleep_data = sleep_data or {}
        self.stress_data = stress_data or {}
        self.steps_data = steps_data or {}
        self.intensity_data = intensity_data or {}
        self.body_battery_data = body_battery_data or {}
        self.blood_pressure_data = blood_pressure_data or {}
        self.hydration_data = hydration_data or {}
        self.respiration_data = respiration_data or {}
        self.spo2_data = spo2_data or {}
        self.training_readiness_data = training_readiness_data or {}
        self.training_status_data = training_status_data or {}
        self.max_metrics_data = max_metrics_data or {}
        self.personal_records_data = personal_records_data or []
        self.heart_rate_data = heart_rate_data or {}

    def to_dict(self) -> dict:
        """Convert to dictionary for API/UI usage."""
        return {
            "date": self.date.isoformat(),
            "user_profile": self.user_profile,
            "sleep": self.sleep_data,
            "stress": self.stress_data,
            "steps": self.steps_data,
            "intensity": self.intensity_data,
            "body_battery": self.body_battery_data,
            "blood_pressure": self.blood_pressure_data,
            "hydration": self.hydration_data,
            "respiration": self.respiration_data,
            "spo2": self.spo2_data,
            "training_readiness": self.training_readiness_data,
            "training_status": self.training_status_data,
            "max_metrics": self.max_metrics_data,
            "personal_records": self.personal_records_data,
            "heart_rate": self.heart_rate_data,
        }
