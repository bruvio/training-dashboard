"""
Database models for Garmin wellness data downloaded via garth library.

These models complement the existing activity-focused models with daily wellness metrics.
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Float, Index, Integer, String, Text

# Use same base class as other models
from .models import Base, mapped_column


class DailySleep(Base):
    """Daily sleep data from Garmin Connect via garth.DailySleep.list()."""

    __tablename__ = "daily_sleep"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)  # Date of the sleep (local time)

    # Sleep timing
    bedtime_utc = mapped_column(DateTime(timezone=True))
    wakeup_time_utc = mapped_column(DateTime(timezone=True))

    # Sleep metrics (all in seconds unless noted)
    total_sleep_time_s = mapped_column(Integer)  # Total time asleep
    deep_sleep_s = mapped_column(Integer)
    light_sleep_s = mapped_column(Integer)
    rem_sleep_s = mapped_column(Integer)
    awake_time_s = mapped_column(Integer)

    # Sleep quality metrics
    sleep_score = mapped_column(Integer)  # 0-100 sleep score
    restlessness = mapped_column(Float)  # Restlessness level

    # Data source tracking
    data_source = mapped_column(String(50), default="garth")  # Always garth for this model
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_sleep_date", "date"),
        Index("ix_sleep_retrieved", "retrieved_at"),
    )


class DailyStress(Base):
    """Daily stress data from Garmin Connect via garth.DailyStress.list()."""

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
    data_source = mapped_column(String(50), default="garth")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_stress_date", "date"),
        Index("ix_stress_avg", "avg_stress_level"),
    )


class DailySteps(Base):
    """Daily steps and activity data from Garmin Connect via garth.DailySteps.list()."""

    __tablename__ = "daily_steps"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)

    # Step metrics
    total_steps = mapped_column(Integer)
    step_goal = mapped_column(Integer)  # Daily step goal

    # Distance metrics
    total_distance_m = mapped_column(Float)  # Total distance in meters

    # Calorie metrics
    calories_burned = mapped_column(Integer)
    calories_bmr = mapped_column(Integer)  # Base metabolic rate calories
    calories_active = mapped_column(Integer)  # Active calories

    # Activity metrics
    floors_climbed = mapped_column(Integer)
    floors_goal = mapped_column(Integer)

    # Data source tracking
    data_source = mapped_column(String(50), default="garth")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_steps_date", "date"),
        Index("ix_steps_total", "total_steps"),
    )


class DailyIntensityMinutes(Base):
    """Daily intensity minutes from Garmin Connect via garth.DailyIntensityMinutes.list()."""

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
    data_source = mapped_column(String(50), default="garth")
    retrieved_at = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_intensity_date", "date"),
        Index("ix_intensity_score", "intensity_score"),
    )


class GarminSession(Base):
    """Track Garmin Connect authentication sessions and data sync status."""

    __tablename__ = "garmin_sessions"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(String(255), index=True)  # Garmin Connect email

    # Session tracking
    authenticated_at = mapped_column(DateTime(timezone=True))
    last_sync_at = mapped_column(DateTime(timezone=True))
    session_valid = mapped_column(Integer, default=1)  # 1=valid, 0=expired

    # Sync progress tracking
    last_sleep_sync = mapped_column(Date)  # Last date of sleep data synced
    last_stress_sync = mapped_column(Date)  # Last date of stress data synced
    last_steps_sync = mapped_column(Date)  # Last date of steps data synced
    last_intensity_sync = mapped_column(Date)  # Last date of intensity data synced

    # Error tracking
    last_error = mapped_column(Text)  # Last sync error message
    error_count = mapped_column(Integer, default=0)  # Consecutive error count

    __table_args__ = (
        Index("ix_garmin_session_email", "email"),
        Index("ix_garmin_session_auth", "authenticated_at"),
        Index("ix_garmin_session_valid", "session_valid"),
    )


class WellnessDataTransferObject:
    """Data transfer object for consolidated wellness data from garth APIs."""

    def __init__(
        self,
        date: date,
        sleep_data: Optional[dict] = None,
        stress_data: Optional[dict] = None,
        steps_data: Optional[dict] = None,
        intensity_data: Optional[dict] = None,
    ):
        self.date = date
        self.sleep_data = sleep_data or {}
        self.stress_data = stress_data or {}
        self.steps_data = steps_data or {}
        self.intensity_data = intensity_data or {}

    def to_dict(self) -> dict:
        """Convert to dictionary for API/UI usage."""
        return {
            "date": self.date.isoformat(),
            "sleep": self.sleep_data,
            "stress": self.stress_data,
            "steps": self.steps_data,
            "intensity": self.intensity_data,
        }
