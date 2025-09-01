"""
Web-specific database queries for Dash application.

Research-validated patterns for integrating SQLAlchemy with Dash callbacks,
including session management and query optimization.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import desc, func, or_, text

from .db import session_scope
from .models import Activity, Lap, Sample
from ..utils import get_logger, log_error

logger = get_logger(__name__)


def get_activities_for_date_range(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sport: Optional[str] = None,
    search_term: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get activities for date range with optional filters.

    Research-validated query pattern with proper session management
    and performance optimization for web applications.

    Args:
        start_date: Start date filter
        end_date: End date filter
        sport: Sport type filter ("all" means no filter)
        search_term: Search term for activity name/description

    Returns:
        List of activity dictionaries ready for Dash DataTable
    """
    with session_scope() as session:
        query = session.query(Activity).order_by(desc(Activity.start_time_utc))

        # Apply date range filter
        if start_date:
            query = query.filter(Activity.start_time_utc >= start_date)
        if end_date:
            # Include the entire end date
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(Activity.start_time_utc <= end_datetime)

        # Apply sport filter
        if sport and sport != "all":
            # Map UI sport values to database sport types
            sport_mapping = {
                "running": ["running", "treadmill_running", "trail_running"],
                "cycling": ["cycling", "road_biking", "mountain_biking"],
                "swimming": ["swimming", "open_water_swimming"],
                "hiking": ["hiking", "walking"],
                "strength": ["strength_training", "generic"],
                "cardio": ["cardio", "elliptical", "fitness_equipment"],
                "skiing": ["downhill_skiing", "cross_country_skiing", "snowboarding"],
                "other": [],  # Will match any sport not in other categories
            }

            if sport in sport_mapping and sport_mapping[sport]:
                query = query.filter(Activity.sport.in_(sport_mapping[sport]))
            elif sport == "other":
                # Find activities not in any other category
                all_mapped_sports = []
                for sports_list in sport_mapping.values():
                    all_mapped_sports.extend(sports_list)
                query = query.filter(~Activity.sport.in_(all_mapped_sports))

        # Apply search filter
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(or_(Activity.name.ilike(search_pattern), Activity.description.ilike(search_pattern)))

        # Execute query and convert to list
        activities = query.limit(1000).all()  # Limit for performance

        # Convert to format expected by DataTable
        result = []
        for activity in activities:
            # Map database sport to UI display format
            sport_emoji_map = {
                "running": "🏃 Running",
                "treadmill_running": "🏃 Running",
                "trail_running": "🏃 Trail Running",
                "cycling": "🚴 Cycling",
                "road_biking": "🚴 Cycling",
                "mountain_biking": "🚴 MTB",
                "swimming": "🏊 Swimming",
                "open_water_swimming": "🏊 Open Water",
                "hiking": "🥾 Hiking",
                "walking": "🚶 Walking",
                "strength_training": "💪 Strength",
                "generic": "💪 Strength",
                "cardio": "🏋️ Cardio",
                "elliptical": "🏋️ Elliptical",
                "fitness_equipment": "🏋️ Gym",
                "downhill_skiing": "🎿 Skiing",
                "cross_country_skiing": "🎿 XC Ski",
                "snowboarding": "🏂 Snowboard",
            }

            sport_display = sport_emoji_map.get(activity.sport, f"⚽ {activity.sport.title()}")

            # Format duration
            if activity.elapsed_time_s:
                hours = int(activity.elapsed_time_s // 3600)
                minutes = int((activity.elapsed_time_s % 3600) // 60)
                seconds = int(activity.elapsed_time_s % 60)
                if hours > 0:
                    duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "N/A"

            result.append(
                {
                    "id": activity.id,
                    "name": activity.name or f"{activity.sport.title()} Activity",  # Include custom name
                    "start_time": (
                        activity.start_time_utc.strftime("%Y-%m-%d %H:%M:%S") if activity.start_time_utc else "N/A"
                    ),
                    "sport": sport_display,
                    "distance_km": round(activity.distance_m / 1000, 2) if activity.distance_m else 0,
                    "duration_str": duration_str,
                    "avg_hr": int(activity.avg_hr) if activity.avg_hr else None,
                    "avg_power_w": int(activity.avg_power_w) if activity.avg_power_w else None,
                    "elevation_gain_m": int(activity.elevation_gain_m) if activity.elevation_gain_m else 0,
                }
            )

        return result


def get_activity_summary_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sport: Optional[str] = None,
    search_term: Optional[str] = None,
) -> Dict[str, str]:
    """
    Get summary statistics for filtered activities.

    Research-validated aggregation queries with proper NULL handling.

    Args:
        start_date: Start date filter
        end_date: End date filter
        sport: Sport type filter
        search_term: Search term filter

    Returns:
        Dictionary with formatted summary statistics
    """
    with session_scope() as session:
        query = session.query(Activity)

        # Apply same filters as activity list
        if start_date:
            query = query.filter(Activity.start_time_utc >= start_date)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(Activity.start_time_utc <= end_datetime)

        if sport and sport != "all":
            sport_mapping = {
                "running": ["running", "treadmill_running", "trail_running"],
                "cycling": ["cycling", "road_biking", "mountain_biking"],
                "swimming": ["swimming", "open_water_swimming"],
                "hiking": ["hiking", "walking"],
                "strength": ["strength_training", "generic"],
                "cardio": ["cardio", "elliptical", "fitness_equipment"],
                "skiing": ["downhill_skiing", "cross_country_skiing", "snowboarding"],
                "other": [],
            }

            if sport in sport_mapping and sport_mapping[sport]:
                query = query.filter(Activity.sport.in_(sport_mapping[sport]))
            elif sport == "other":
                all_mapped_sports = []
                for sports_list in sport_mapping.values():
                    all_mapped_sports.extend(sports_list)
                query = query.filter(~Activity.sport.in_(all_mapped_sports))

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(or_(Activity.name.ilike(search_pattern), Activity.description.ilike(search_pattern)))

        # Create aggregation query with same filters
        agg_query = session.query(
            func.count(Activity.id).label("total_activities"),
            func.sum(Activity.distance_m).label("distance_m"),
            func.sum(Activity.elapsed_time_s).label("total_time_s"),
            func.avg(Activity.avg_hr).label("avg_hr"),
            func.avg(Activity.avg_power_w).label("avg_power"),
            func.sum(Activity.elevation_gain_m).label("total_elevation_m"),
        )

        # Apply same filters as the main query
        if start_date:
            agg_query = agg_query.filter(Activity.start_time_utc >= start_date)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            agg_query = agg_query.filter(Activity.start_time_utc <= end_datetime)

        if sport and sport != "all":
            sport_mapping = {
                "running": ["running", "treadmill_running", "trail_running"],
                "cycling": ["cycling", "road_biking", "mountain_biking"],
                "swimming": ["swimming", "open_water_swimming"],
                "hiking": ["hiking", "walking"],
                "strength": ["strength_training", "generic"],
                "cardio": ["cardio", "elliptical", "fitness_equipment"],
                "skiing": ["downhill_skiing", "cross_country_skiing", "snowboarding"],
                "other": [],
            }

            if sport in sport_mapping and sport_mapping[sport]:
                agg_query = agg_query.filter(Activity.sport.in_(sport_mapping[sport]))
            elif sport == "other":
                all_mapped_sports = []
                for sports_list in sport_mapping.values():
                    all_mapped_sports.extend(sports_list)
                agg_query = agg_query.filter(~Activity.sport.in_(all_mapped_sports))

        if search_term:
            search_pattern = f"%{search_term}%"
            agg_query = agg_query.filter(
                or_(Activity.name.ilike(search_pattern), Activity.description.ilike(search_pattern))
            )

        stats = agg_query.first()

        # Format results with proper NULL handling
        total_activities = stats.total_activities or 0
        total_distance_km = (stats.distance_m or 0) / 1000
        total_time_s = stats.total_time_s or 0
        avg_hr = stats.avg_hr or 0
        avg_power = stats.avg_power or 0
        total_elevation_m = stats.total_elevation_m or 0

        # Format total time
        if total_time_s > 0:
            hours = int(total_time_s // 3600)
            minutes = int((total_time_s % 3600) // 60)
            total_time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        else:
            total_time_str = "0h"

        return {
            "total_activities": str(total_activities),
            "total_distance": f"{total_distance_km:.1f} km",
            "total_time": total_time_str,
            "avg_hr": f"{int(avg_hr)} bpm" if avg_hr > 0 else "N/A",
            "avg_power": f"{int(avg_power)} W" if avg_power > 0 else "N/A",
            "elevation_gain": f"{int(total_elevation_m)} m",
        }


def get_activity_by_id(activity_id: int) -> Optional[Dict[str, Any]]:
    """
    Get single activity by ID for detail page.

    Research-validated pattern for detail views with proper
    error handling and data formatting.

    Args:
        activity_id: Activity database ID

    Returns:
        Activity dictionary or None if not found
    """
    with session_scope() as session:
        activity = session.query(Activity).filter(Activity.id == activity_id).first()

        if not activity:
            return None

        return {
            "id": activity.id,
            "external_id": activity.external_id,
            "name": activity.name or f"{activity.sport.title()} Activity",
            "description": getattr(activity, "description", None),
            "sport": activity.sport,
            "sub_sport": getattr(activity, "sub_sport", None),
            "start_time": activity.start_time_utc,
            "total_distance_km": (activity.distance_m / 1000 if activity.distance_m else 0),
            "total_time_s": activity.elapsed_time_s or 0,
            "moving_time_s": getattr(activity, "moving_time_s", None) or 0,
            "avg_hr": activity.avg_hr,
            "max_hr": getattr(activity, "max_hr", None),
            "avg_power_w": activity.avg_power_w,
            "max_power_w": getattr(activity, "max_power_w", None),
            "elevation_gain_m": activity.elevation_gain_m or 0,
            "elevation_loss_m": activity.elevation_loss_m or 0,
            "avg_speed_mps": getattr(activity, "avg_speed_mps", None),
            "avg_pace_s_per_km": getattr(activity, "avg_pace_s_per_km", None),
            "calories": getattr(activity, "calories", None),
            "source": getattr(activity, "source", "unknown"),
            "file_path": activity.file_path,
            "ingested_on": getattr(activity, "ingested_on", None),
        }


def get_activity_samples(activity_id: int) -> Optional[pd.DataFrame]:
    """
    Get time series samples for activity charts and maps.

    Research-validated pattern for time series data preparation
    with pandas DataFrame conversion for Plotly integration.

    Args:
        activity_id: Activity database ID

    Returns:
        DataFrame with time series data or None if not found
    """
    with session_scope() as session:
        # Check if activity exists
        activity = session.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            return None

        # Get samples ordered by time
        samples = session.query(Sample).filter(Sample.activity_id == activity_id).order_by(Sample.elapsed_time_s).all()

        if not samples:
            return pd.DataFrame()  # Return empty DataFrame

        data = [
            {
                "elapsed_time_s": sample.elapsed_time_s,
                "position_lat": sample.latitude,
                "position_long": sample.longitude,
                "altitude_m": sample.altitude_m,
                "heart_rate_bpm": sample.heart_rate,
                "power_w": sample.power_w,
                "cadence_rpm": sample.cadence_rpm,
                "speed_mps": sample.speed_mps,
                "temperature_c": sample.temperature_c,
                # Advanced running dynamics
                "vertical_oscillation_mm": sample.vertical_oscillation_mm,
                "vertical_ratio": sample.vertical_ratio,
                "ground_contact_time_ms": sample.ground_contact_time_ms,
                "ground_contact_balance_pct": sample.ground_contact_balance_pct,
                "step_length_mm": sample.step_length_mm,
                "air_power_w": sample.air_power_w,
                "form_power_w": sample.form_power_w,
                "leg_spring_stiffness": sample.leg_spring_stiffness,
                "impact_loading_rate": sample.impact_loading_rate,
                "stryd_temperature_c": sample.stryd_temperature_c,
                "stryd_humidity_pct": sample.stryd_humidity_pct,
            }
            for sample in samples
        ]
        df = pd.DataFrame(data)

        # Add computed columns
        if not df.empty:
            # Convert elapsed time to datetime for plotting
            df["timestamp"] = pd.to_datetime(df["elapsed_time_s"], unit="s")

            # Convert speed to km/h
            df["speed_kmh"] = df["speed_mps"] * 3.6

        return df


def get_activity_laps(activity_id: int) -> List[Dict[str, Any]]:
    """
    Get lap data for activity charts and analysis.

    Research-validated pattern for lap marker visualization
    with proper data formatting for chart integration.

    Args:
        activity_id: Activity database ID

    Returns:
        List of lap dictionaries with timing and metrics
    """
    with session_scope() as session:
        # Check if activity exists
        activity = session.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            return []

        # Get laps ordered by lap index
        laps = session.query(Lap).filter(Lap.activity_id == activity_id).order_by(Lap.lap_index).all()

        if not laps:
            return []

        # Convert to list of dictionaries
        result = []
        cumulative_time = 0
        cumulative_distance = 0

        for lap in laps:
            lap_data = {
                "lap_index": lap.lap_index,
                "start_time_s": cumulative_time,
                "elapsed_time_s": lap.elapsed_time_s or 0,
                "distance_m": lap.distance_m or 0,
                "avg_speed_mps": lap.avg_speed_mps,
                "avg_hr": lap.avg_hr,
                "max_hr": lap.max_hr,
                "avg_power_w": lap.avg_power_w,
                "max_power_w": lap.max_power_w,
                "avg_cadence_rpm": lap.avg_cadence_rpm,
                "moving_time_s": lap.moving_time_s,
                "end_time_s": cumulative_time + (lap.elapsed_time_s or 0),
            }

            result.append(lap_data)

            # Update cumulative values for next lap
            cumulative_time += lap.elapsed_time_s or 0
            cumulative_distance += lap.distance_m or 0

        return result


def get_activity_navigation(activity_id: int) -> Dict[str, Optional[int]]:
    """
    Get previous/next activity IDs for navigation based on chronological order.

    Args:
        activity_id: Current activity ID

    Returns:
        Dict with 'previous' and 'next' activity IDs (None if not available)
    """
    with session_scope() as session:
        # Get the current activity and its start_time
        current_activity = session.query(Activity).filter(Activity.id == activity_id).first()
        if not current_activity:
            logger.warning(f"Activity with ID {activity_id} not found")
            return {"previous": None, "next": None}

        # Find previous activity (chronologically before)
        previous_activity = (
            session.query(Activity)
            .filter(Activity.start_time_utc < current_activity.start_time_utc)
            .order_by(Activity.start_time_utc.desc())
            .first()
        )

        # Find next activity (chronologically after)
        next_activity = (
            session.query(Activity)
            .filter(Activity.start_time_utc > current_activity.start_time_utc)
            .order_by(Activity.start_time_utc.asc())
            .first()
        )

        return {
            "previous": previous_activity.id if previous_activity else None,
            "next": next_activity.id if next_activity else None,
        }


import logging

def update_activity_name(activity_id: int, new_name: str) -> bool:
    """
    Update activity name in database.

    Args:
        activity_id: Activity ID to update
        new_name: New name for the activity

    Returns:
        True if successful, False otherwise
    """
    try:
        with session_scope() as session:
            if (
                activity := session.query(Activity)
                .filter(Activity.id == activity_id)
                .first()
            ):
                activity.name = new_name.strip() or None
                session.commit()
                logger.info(f"Updated activity {activity_id} name to: {new_name}")
                return True
            logger.warning(f"Activity {activity_id} not found for name update")
            return False
    except Exception as e:
        logging.error(f"Failed to update activity name for activity_id={activity_id}: {e}", exc_info=True)
        return False


def get_filter_options() -> Dict[str, Any]:
    """
    Get available filter options for the main page.

    Returns:
        Dict with sports, duration ranges, and distance ranges
    """
    with session_scope() as session:
        # Get unique sports
        sports = (
            session.query(Activity.sport).distinct().filter(Activity.sport.isnot(None)).order_by(Activity.sport).all()
        )
        sport_list = [sport[0] for sport in sports]

        # Get duration ranges
        duration_stats = session.query(
            func.min(Activity.elapsed_time_s).label("min_duration"),
            func.max(Activity.elapsed_time_s).label("max_duration"),
        ).first()

        # Get distance ranges
        distance_stats = session.query(
            func.min(Activity.distance_m).label("min_distance"),
            func.max(Activity.distance_m).label("max_distance"),
        ).first()

        return {
            "sports": sport_list,
            "duration_range": {
                "min": duration_stats.min_duration or 0,
                "max": duration_stats.max_duration or 0,
            },
            "distance_range": {
                "min": (distance_stats.min_distance or 0) / 1000,  # Convert to km
                "max": (distance_stats.max_distance or 0) / 1000,
            },
        }


def get_activity_statistics() -> Dict[str, Any]:
    """
    Get activity statistics for the stats page.

    Returns:
        Dict with total activities, distance, time, and average heart rate
    """
    try:
        with session_scope() as session:
            stats = (
                session.query(
                    func.count(Activity.id).label("total_activities"),
                    func.sum(Activity.distance_m).label("total_distance_m"),
                    func.sum(Activity.elapsed_time_s).label("total_time_s"),
                    func.avg(Activity.avg_hr).label("avg_heart_rate"),
                )
                .filter(Activity.distance_m.isnot(None))
                .first()
            )

            # Convert to user-friendly format
            total_distance_km = (stats.total_distance_m or 0) / 1000
            total_time_s = stats.total_time_s or 0
            total_time_hours = total_time_s / 3600

            return {
                "total_activities": stats.total_activities or 0,
                "total_distance_km": round(total_distance_km, 2),
                "total_time_hours": round(total_time_hours, 1),
                "avg_heart_rate": round(stats.avg_heart_rate or 0, 0),
            }
    except Exception as e:
        log_error(e, "Failed to get activity statistics")
        return {"total_activities": 0, "total_distance_km": 0, "total_time_hours": 0, "avg_heart_rate": 0}


def get_activity_trends() -> Dict[str, Any]:
    """
    Get activity trends data for charts and visualizations.

    Returns:
        Dict with monthly activity counts and distance trends
    """
    try:
        with session_scope() as session:
            # Get monthly activity counts for last 12 months
            monthly_stats = (
                session.query(
                    func.strftime("%Y-%m", Activity.start_time_utc).label("month"),
                    func.count(Activity.id).label("count"),
                    func.sum(Activity.distance_m).label("total_distance"),
                )
                .filter(Activity.start_time_utc >= datetime.now().replace(month=1, day=1) - pd.DateOffset(years=1))
                .group_by(func.strftime("%Y-%m", Activity.start_time_utc))
                .order_by("month")
                .all()
            )

            months = [stat.month for stat in monthly_stats]
            counts = [stat.count for stat in monthly_stats]
            distances = [(stat.total_distance or 0) / 1000 for stat in monthly_stats]  # Convert to km

            return {"months": months, "activity_counts": counts, "distances_km": distances}
    except Exception as e:
        log_error(e, "Failed to get activity trends")
        return {"months": [], "activity_counts": [], "distances_km": []}


def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Research-validated health check pattern for web applications.

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        with session_scope() as session:
            session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
