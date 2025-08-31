"""
SQLAlchemy 2.0 models with type annotations for Garmin Dashboard.

Enhanced with research-validated patterns for performance and relationships.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

# Support for both SQLAlchemy 1.4+ and 2.0+
try:
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    SQLALCHEMY_2_0 = True

    class Base(DeclarativeBase):
        """Base class for all database models."""

except ImportError:
    # Fallback to SQLAlchemy 1.4 style
    from sqlalchemy.orm import declarative_base  # noqa: F811

    SQLALCHEMY_2_0 = False
    Base = declarative_base()

    # Type aliases for compatibility
    def Mapped(type_hint):
        return type_hint

    def mapped_column(*args, **kwargs):
        return Column(*args, **kwargs)


class Activity(Base):
    """
    Main activity model storing workout/exercise data from various sources.

    Supports FIT, TCX, GPX files and GarminDB integration with proper
    timezone handling and performance indexing.
    """

    __tablename__ = "activities"

    # Primary key and identifiers
    id = mapped_column(Integer, primary_key=True)
    external_id = mapped_column(String(100), index=True)
    garmin_activity_id = mapped_column(String(50), index=True)  # Garmin Connect activity ID
    file_hash = mapped_column(String(64))  # For deduplication

    # Activity metadata
    source = mapped_column(String(20))  # 'fit', 'tcx', 'gpx', 'garmindb'
    sport = mapped_column(String(30))
    sub_sport = mapped_column(String(30))

    # Temporal data (research-validated timezone handling)
    start_time_utc = mapped_column(DateTime(timezone=True), index=True)
    local_timezone = mapped_column(String(50))
    elapsed_time_s = mapped_column(Integer)
    moving_time_s = mapped_column(Integer)

    # Metrics with proper types from research
    distance_m = mapped_column(Float)
    avg_speed_mps = mapped_column(Float)
    avg_pace_s_per_km = mapped_column(Float)
    avg_hr = mapped_column(Integer)
    max_hr = mapped_column(Integer)
    avg_power_w = mapped_column(Float)
    max_power_w = mapped_column(Float)
    elevation_gain_m = mapped_column(Float)
    elevation_loss_m = mapped_column(Float)
    calories = mapped_column(Integer)

    # File tracking
    file_path = mapped_column(Text)
    ingested_on = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # User annotations
    comments = mapped_column(Text)  # User-editable comments for this activity

    # Relationships
    samples = relationship("Sample", back_populates="activity", cascade="all, delete-orphan", lazy="select")
    route_points = relationship("RoutePoint", back_populates="activity", cascade="all, delete-orphan", lazy="select")
    laps = relationship("Lap", back_populates="activity", cascade="all, delete-orphan", lazy="select")

    # Enhanced indexing from research
    __table_args__ = (
        Index("ix_activity_sport_date", "sport", "start_time_utc"),
        Index("ix_activity_hash", "file_hash"),
        Index("ix_activity_source", "source"),
    )

    def to_dict(self) -> dict:
        """Convert activity to dictionary for API/UI usage."""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "sport": self.sport,
            "sub_sport": self.sub_sport,
            "start_time": self.start_time_utc.isoformat() if self.start_time_utc else None,
            "elapsed_time_s": self.elapsed_time_s,
            "moving_time_s": self.moving_time_s,
            "distance_m": self.distance_m,
            "distance_km": round(self.distance_m / 1000, 2) if self.distance_m else None,
            "avg_speed_mps": self.avg_speed_mps,
            "avg_pace_s_per_km": self.avg_pace_s_per_km,
            "avg_hr": self.avg_hr,
            "max_hr": self.max_hr,
            "avg_power_w": self.avg_power_w,
            "max_power_w": self.max_power_w,
            "elevation_gain_m": self.elevation_gain_m,
            "calories": self.calories,
            "source": self.source,
        }


class Sample(Base):
    """
    Time series data points for activities (GPS, HR, power, etc.).

    Optimized for large datasets with proper indexing for time-based queries.
    """

    __tablename__ = "samples"

    id = mapped_column(Integer, primary_key=True)
    activity_id = mapped_column(Integer, ForeignKey("activities.id"), index=True)

    # Temporal
    timestamp = mapped_column(DateTime(timezone=True))
    elapsed_time_s = mapped_column(Integer)

    # GPS data
    latitude = mapped_column(Float)
    longitude = mapped_column(Float)
    altitude_m = mapped_column(Float)

    # Sensor data
    heart_rate = mapped_column(Integer)
    power_w = mapped_column(Float)
    cadence_rpm = mapped_column(Integer)
    speed_mps = mapped_column(Float)
    temperature_c = mapped_column(Float)

    # Advanced running dynamics (Stryd, Garmin, etc.)
    vertical_oscillation_mm = mapped_column(Float)  # Vertical movement
    vertical_ratio = mapped_column(Float)  # Vertical ratio %
    ground_contact_time_ms = mapped_column(Float)  # Ground contact time
    ground_contact_balance_pct = mapped_column(Float)  # L/R balance
    step_length_mm = mapped_column(Float)  # Step length
    air_power_w = mapped_column(Float)  # Air resistance power
    form_power_w = mapped_column(Float)  # Form power (Stryd)
    leg_spring_stiffness = mapped_column(Float)  # Leg stiffness
    impact_loading_rate = mapped_column(Float)  # Impact loading rate
    stryd_temperature_c = mapped_column(Float)  # Stryd temperature
    stryd_humidity_pct = mapped_column(Float)  # Stryd humidity

    # Relationship
    activity = relationship("Activity", back_populates="samples")

    __table_args__ = (
        Index("ix_sample_activity_time", "activity_id", "elapsed_time_s"),
        Index("ix_sample_timestamp", "timestamp"),
    )


class RoutePoint(Base):
    """
    Simplified GPS route points for map visualization.

    Derived from samples but optimized for rendering performance.
    """

    __tablename__ = "route_points"

    id = mapped_column(Integer, primary_key=True)
    activity_id = mapped_column(Integer, ForeignKey("activities.id"), index=True)
    sequence = mapped_column(Integer)  # Order in route

    # GPS coordinates
    latitude = mapped_column(Float)
    longitude = mapped_column(Float)
    altitude_m = mapped_column(Float)

    # Relationship
    activity = relationship("Activity", back_populates="route_points")

    __table_args__ = (Index("ix_route_activity_seq", "activity_id", "sequence"),)


class Lap(Base):
    """
    Lap/segment data for activities.

    Contains summary metrics for each lap or auto-detected segment.
    """

    __tablename__ = "laps"

    id = mapped_column(Integer, primary_key=True)
    activity_id = mapped_column(Integer, ForeignKey("activities.id"), index=True)
    lap_index = mapped_column(Integer)  # 0-based lap number

    # Temporal
    start_time_utc = mapped_column(DateTime(timezone=True))
    elapsed_time_s = mapped_column(Integer)
    moving_time_s = mapped_column(Integer)

    # Metrics
    distance_m = mapped_column(Float)
    avg_speed_mps = mapped_column(Float)
    avg_hr = mapped_column(Integer)
    max_hr = mapped_column(Integer)
    avg_power_w = mapped_column(Float)
    max_power_w = mapped_column(Float)
    avg_cadence_rpm = mapped_column(Integer)

    # Relationship
    activity = relationship("Activity", back_populates="laps")

    __table_args__ = (Index("ix_lap_activity_index", "activity_id", "lap_index"),)


class ActivityData:
    """
    Data transfer object for parsed activity data.

    Used to transfer data between parsers and database models.
    """

    def __init__(
        self,
        external_id: Optional[str] = None,
        sport: Optional[str] = None,
        sub_sport: Optional[str] = None,
        start_time_utc: Optional[datetime] = None,
        elapsed_time_s: Optional[int] = None,
        moving_time_s: Optional[int] = None,
        distance_m: Optional[float] = None,
        avg_speed_mps: Optional[float] = None,
        avg_pace_s_per_km: Optional[float] = None,
        avg_hr: Optional[int] = None,
        max_hr: Optional[int] = None,
        avg_power_w: Optional[float] = None,
        max_power_w: Optional[float] = None,
        elevation_gain_m: Optional[float] = None,
        elevation_loss_m: Optional[float] = None,
        calories: Optional[int] = None,
        samples: Optional[List["SampleData"]] = None,
        route_points: Optional[List[tuple]] = None,  # [(lat, lon, alt), ...]
        laps: Optional[List["LapData"]] = None,
        hr_zones: Optional[dict] = None,
    ):
        self.external_id = external_id
        self.sport = sport
        self.sub_sport = sub_sport
        self.start_time_utc = start_time_utc
        self.elapsed_time_s = elapsed_time_s
        self.moving_time_s = moving_time_s
        self.distance_m = distance_m
        self.avg_speed_mps = avg_speed_mps
        self.avg_pace_s_per_km = avg_pace_s_per_km
        self.avg_hr = avg_hr
        self.max_hr = max_hr
        self.avg_power_w = avg_power_w
        self.max_power_w = max_power_w
        self.elevation_gain_m = elevation_gain_m
        self.elevation_loss_m = elevation_loss_m
        self.calories = calories
        self.samples = samples or []
        self.route_points = route_points or []
        self.laps = laps or []
        self.hr_zones = hr_zones or {}


class SampleData:
    """Data transfer object for sample/trackpoint data."""

    def __init__(
        self,
        timestamp: Optional[datetime] = None,
        elapsed_time_s: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        altitude_m: Optional[float] = None,
        heart_rate: Optional[int] = None,
        power_w: Optional[float] = None,
        cadence_rpm: Optional[int] = None,
        speed_mps: Optional[float] = None,
        temperature_c: Optional[float] = None,
        # Advanced running dynamics
        vertical_oscillation_mm: Optional[float] = None,
        vertical_ratio: Optional[float] = None,
        ground_contact_time_ms: Optional[float] = None,
        ground_contact_balance_pct: Optional[float] = None,
        step_length_mm: Optional[float] = None,
        air_power_w: Optional[float] = None,
        form_power_w: Optional[float] = None,
        leg_spring_stiffness: Optional[float] = None,
        impact_loading_rate: Optional[float] = None,
        stryd_temperature_c: Optional[float] = None,
        stryd_humidity_pct: Optional[float] = None,
    ):
        self.timestamp = timestamp
        self.elapsed_time_s = elapsed_time_s
        self.latitude = latitude
        self.longitude = longitude
        self.altitude_m = altitude_m
        self.heart_rate = heart_rate
        self.power_w = power_w
        self.cadence_rpm = cadence_rpm
        self.speed_mps = speed_mps
        self.temperature_c = temperature_c
        # Advanced running dynamics
        self.vertical_oscillation_mm = vertical_oscillation_mm
        self.vertical_ratio = vertical_ratio
        self.ground_contact_time_ms = ground_contact_time_ms
        self.ground_contact_balance_pct = ground_contact_balance_pct
        self.step_length_mm = step_length_mm
        self.air_power_w = air_power_w
        self.form_power_w = form_power_w
        self.leg_spring_stiffness = leg_spring_stiffness
        self.impact_loading_rate = impact_loading_rate
        self.stryd_temperature_c = stryd_temperature_c
        self.stryd_humidity_pct = stryd_humidity_pct


class LapData:
    """Data transfer object for lap data."""

    def __init__(
        self,
        lap_index: int,
        start_time_utc: Optional[datetime] = None,
        elapsed_time_s: Optional[int] = None,
        distance_m: Optional[float] = None,
        avg_speed_mps: Optional[float] = None,
        avg_hr: Optional[int] = None,
        max_hr: Optional[int] = None,
        avg_power_w: Optional[float] = None,
        max_power_w: Optional[float] = None,
    ):
        self.lap_index = lap_index
        self.start_time_utc = start_time_utc
        self.elapsed_time_s = elapsed_time_s
        self.distance_m = distance_m
        self.avg_speed_mps = avg_speed_mps
        self.avg_hr = avg_hr
        self.max_hr = max_hr
        self.avg_power_w = avg_power_w
        self.max_power_w = max_power_w


class ImportResult:
    """Result of importing an activity file."""

    def __init__(self, imported: bool, reason: str = "", activity_id: Optional[int] = None):
        self.imported = imported
        self.reason = reason
        self.activity_id = activity_id
