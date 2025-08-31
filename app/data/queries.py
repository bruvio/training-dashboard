"""
Database query functions for Garmin Dashboard.

Optimized queries for activity data retrieval with proper filtering,
sorting, and performance considerations.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func, or_, desc
from sqlalchemy.orm import Session, selectinload

from .models import Activity, Sample, RoutePoint


class ActivityQueries:
    """Optimized queries for Activity data."""

    @staticmethod
    def get_activities_by_date_range(
        session: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sport: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Activity]:
        """
        Get activities within a date range with optional sport filter.

        Args:
            session: Database session
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            sport: Sport type filter (optional)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of Activity objects
        """
        query = select(Activity)

        # Date filters
        if start_date:
            query = query.where(Activity.start_time_utc >= start_date)
        if end_date:
            # Add one day to include activities on the end date
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.where(Activity.start_time_utc <= end_datetime)

        # Sport filter
        if sport and sport.lower() != "all":
            query = query.where(Activity.sport == sport)

        # Order by most recent first
        query = query.order_by(desc(Activity.start_time_utc))

        # Pagination
        query = query.offset(offset).limit(limit)

        return session.scalars(query).all()

    @staticmethod
    def get_activity_with_details(
        session: Session,
        activity_id: int,
        include_samples: bool = True,
        include_route_points: bool = True,
        include_laps: bool = False,
    ) -> Optional[Activity]:
        """
        Get activity with optional related data for detail view.

        Args:
            session: Database session
            activity_id: Activity ID
            include_samples: Include sample data
            include_route_points: Include route points
            include_laps: Include lap data

        Returns:
            Activity with related data or None
        """
        query = select(Activity).where(Activity.id == activity_id)

        # Eagerly load related data to avoid N+1 queries
        if include_samples:
            query = query.options(selectinload(Activity.samples))
        if include_route_points:
            query = query.options(selectinload(Activity.route_points))
        if include_laps:
            query = query.options(selectinload(Activity.laps))

        return session.scalars(query).first()

    @staticmethod
    def get_activity_summary_stats(
        session: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sport: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get summary statistics for activities in date range.

        Args:
            session: Database session
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            sport: Sport type filter (optional)

        Returns:
            Dictionary with summary statistics
        """
        query = select(
            func.count(Activity.id).label("total_activities"),
            func.sum(Activity.distance_m).label("total_distance_m"),
            func.sum(Activity.elapsed_time_s).label("total_time_s"),
            func.sum(Activity.elevation_gain_m).label("total_elevation_m"),
            func.avg(Activity.avg_hr).label("avg_hr"),
            func.avg(Activity.avg_power_w).label("avg_power_w"),
            func.count(Activity.sport).label("sports_count"),
        )

        # Apply same filters as activity list
        if start_date:
            query = query.where(Activity.start_time_utc >= start_date)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.where(Activity.start_time_utc <= end_datetime)
        if sport and sport.lower() != "all":
            query = query.where(Activity.sport == sport)

        result = session.execute(query).first()

        return {
            "total_activities": result.total_activities or 0,
            "total_distance_km": round((result.total_distance_m or 0) / 1000, 1),
            "total_time_hours": round((result.total_time_s or 0) / 3600, 1),
            "total_elevation_m": round(result.total_elevation_m or 0, 0),
            "avg_hr": round(result.avg_hr or 0, 0),
            "avg_power_w": round(result.avg_power_w or 0, 0),
        }

    @staticmethod
    def get_sport_distribution(
        session: Session, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get distribution of activities by sport.

        Args:
            session: Database session
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            List of sport statistics
        """
        query = (
            select(
                Activity.sport,
                func.count(Activity.id).label("count"),
                func.sum(Activity.distance_m).label("total_distance_m"),
                func.sum(Activity.elapsed_time_s).label("total_time_s"),
            )
            .group_by(Activity.sport)
            .order_by(desc(func.count(Activity.id)))
        )

        # Apply date filters
        if start_date:
            query = query.where(Activity.start_time_utc >= start_date)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.where(Activity.start_time_utc <= end_datetime)

        results = session.execute(query).all()

        return [
            {
                "sport": result.sport,
                "count": result.count,
                "total_distance_km": round((result.total_distance_m or 0) / 1000, 1),
                "total_time_hours": round((result.total_time_s or 0) / 3600, 1),
            }
            for result in results
        ]

    @staticmethod
    def search_activities(session: Session, search_term: str, limit: int = 50) -> List[Activity]:
        """
        Search activities by external_id or sport.

        Args:
            session: Database session
            search_term: Search text
            limit: Maximum results

        Returns:
            List of matching activities
        """
        search_pattern = f"%{search_term.lower()}%"

        query = (
            select(Activity)
            .where(
                or_(
                    Activity.external_id.ilike(search_pattern),
                    Activity.sport.ilike(search_pattern),
                    Activity.sub_sport.ilike(search_pattern),
                )
            )
            .order_by(desc(Activity.start_time_utc))
            .limit(limit)
        )

        return session.scalars(query).all()


class SampleQueries:
    """Optimized queries for Sample data."""

    @staticmethod
    def get_activity_samples(session: Session, activity_id: int, downsample: Optional[int] = None) -> List[Sample]:
        """
        Get samples for an activity with optional downsampling.

        Args:
            session: Database session
            activity_id: Activity ID
            downsample: If provided, return every Nth sample for performance

        Returns:
            List of Sample objects
        """
        query = select(Sample).where(Sample.activity_id == activity_id).order_by(Sample.elapsed_time_s)

        samples = session.scalars(query).all()

        # Apply downsampling if requested and dataset is large
        if downsample and len(samples) > downsample:
            step = len(samples) // downsample
            samples = samples[:: max(step, 1)]

        return samples

    @staticmethod
    def get_sample_statistics(session: Session, activity_id: int) -> Dict[str, Any]:
        """
        Get summary statistics for activity samples.

        Args:
            session: Database session
            activity_id: Activity ID

        Returns:
            Dictionary with sample statistics
        """
        query = select(
            func.count(Sample.id).label("total_samples"),
            func.min(Sample.heart_rate).label("min_hr"),
            func.max(Sample.heart_rate).label("max_hr"),
            func.avg(Sample.heart_rate).label("avg_hr"),
            func.min(Sample.power_w).label("min_power"),
            func.max(Sample.power_w).label("max_power"),
            func.avg(Sample.power_w).label("avg_power"),
            func.min(Sample.altitude_m).label("min_altitude"),
            func.max(Sample.altitude_m).label("max_altitude"),
        ).where(Sample.activity_id == activity_id)

        result = session.execute(query).first()

        return {
            "total_samples": result.total_samples or 0,
            "hr_range": (result.min_hr, result.max_hr) if result.min_hr else None,
            "avg_hr": round(result.avg_hr or 0, 0),
            "power_range": (result.min_power, result.max_power) if result.min_power else None,
            "avg_power": round(result.avg_power or 0, 0),
            "altitude_range": (result.min_altitude, result.max_altitude) if result.min_altitude else None,
        }


class RoutePointQueries:
    """Optimized queries for RoutePoint data."""

    @staticmethod
    def get_activity_route(session: Session, activity_id: int, simplify: bool = True) -> List[Tuple[float, float]]:
        """
        Get route points for map visualization.

        Args:
            session: Database session
            activity_id: Activity ID
            simplify: Apply basic simplification for performance

        Returns:
            List of (latitude, longitude) tuples
        """
        query = (
            select(RoutePoint.latitude, RoutePoint.longitude)
            .where(RoutePoint.activity_id == activity_id)
            .order_by(RoutePoint.sequence)
        )

        points = session.execute(query).all()

        # Basic route simplification - take every Nth point for large routes
        if simplify and len(points) > 500:
            step = len(points) // 300  # Target ~300 points for smooth rendering
            points = points[:: max(step, 1)]

        return [(point.latitude, point.longitude) for point in points]

    @staticmethod
    def get_route_bounds(session: Session, activity_id: int) -> Optional[Dict[str, float]]:
        """
        Get bounding box for activity route.

        Args:
            session: Database session
            activity_id: Activity ID

        Returns:
            Dictionary with lat/lon bounds or None
        """
        query = select(
            func.min(RoutePoint.latitude).label("min_lat"),
            func.max(RoutePoint.latitude).label("max_lat"),
            func.min(RoutePoint.longitude).label("min_lon"),
            func.max(RoutePoint.longitude).label("max_lon"),
        ).where(RoutePoint.activity_id == activity_id)

        result = session.execute(query).first()

        if result.min_lat is None:
            return None

        return {
            "min_lat": result.min_lat,
            "max_lat": result.max_lat,
            "min_lon": result.min_lon,
            "max_lon": result.max_lon,
            "center_lat": (result.min_lat + result.max_lat) / 2,
            "center_lon": (result.min_lon + result.max_lon) / 2,
        }
