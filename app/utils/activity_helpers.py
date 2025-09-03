"""
Shared helper functions for activity data processing.

Contains utilities for parsing durations, sorting activities, and map defaults
to reduce code duplication across calendar and activity detail pages.
"""

from datetime import datetime
from typing import Any, Dict, List


def parse_duration_to_seconds(duration_str: str) -> int:
    """
    Parse duration string to seconds.

    Supports formats:
    - "MM:SS" (e.g., "59:51")
    - "H:MM:SS" (e.g., "1:39:45")

    Args:
        duration_str: Duration string in MM:SS or H:MM:SS format

    Returns:
        Duration in seconds, 0 if parsing fails
    """
    if not duration_str or ":" not in duration_str:
        return 0

    try:
        time_parts = duration_str.split(":")
        if len(time_parts) == 2:  # MM:SS format
            return int(time_parts[0]) * 60 + int(time_parts[1])
        elif len(time_parts) == 3:  # H:MM:SS format
            return int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
        else:
            return 0
    except (ValueError, IndexError):
        return 0


def get_activity_sort_key(activity: Dict[str, Any], sort_by: str) -> Any:
    """
    Get sort key for activity based on sort criteria.

    Args:
        activity: Activity dictionary
        sort_by: Sort criteria (date_desc, date_asc, distance_desc, distance_asc,
                duration_desc, duration_asc)

    Returns:
        Sort key value appropriate for the sort criteria
    """
    if sort_by in ("date_desc", "date_asc"):
        # Convert start_time string to datetime for proper sorting
        start_time_str = activity.get("start_time", "")
        if start_time_str:
            # Try different datetime formats
            formats = [
                "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone
                "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO format with microseconds and timezone
                "%Y-%m-%dT%H:%M:%S",  # ISO format without timezone
                "%Y-%m-%dT%H:%M:%S.%f",  # ISO format with microseconds
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(start_time_str, fmt)
                except ValueError:
                    continue
        return datetime.min

    elif sort_by in ("distance_desc", "distance_asc"):
        return activity.get("distance_km", 0)

    elif sort_by in ("duration_desc", "duration_asc"):
        duration_str = activity.get("duration_str", "0:00")
        return parse_duration_to_seconds(duration_str)

    return ""


def sort_activities(activities: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    """
    Sort activities based on sort criteria.

    Args:
        activities: List of activity dictionaries
        sort_by: Sort criteria

    Returns:
        Sorted list of activities
    """
    if not activities:
        return activities

    reverse_sort = sort_by.endswith("_desc")
    return sorted(activities, key=lambda activity: get_activity_sort_key(activity, sort_by), reverse=reverse_sort)


def get_neutral_map_defaults() -> tuple:
    """
    Get neutral map center and zoom for activities with no GPS data.

    Returns:
        Tuple of (center_coordinates, zoom_level, message)
    """
    return [0, 0], 2, "No GPS data available for this activity"


def get_map_center_from_route(route_positions: List[List[float]]) -> tuple:
    """
    Get map center and zoom from route positions.

    Args:
        route_positions: List of [lat, lon] coordinate pairs

    Returns:
        Tuple of (center_coordinates, zoom_level)
    """
    if not route_positions:
        return [0, 0], 2

    # Center on first GPS point with appropriate zoom
    return route_positions[0], 13


def has_valid_distance(activity: Dict[str, Any]) -> bool:
    """
    Check if activity has valid distance data.

    Args:
        activity: Activity dictionary

    Returns:
        True if activity has valid distance data, False otherwise
    """
    distance = activity.get("distance_km")
    return distance is not None and isinstance(distance, (int, float)) and distance >= 0


def filter_activities_by_distance(
    activities: List[Dict[str, Any]], min_distance: float, max_distance: float
) -> List[Dict[str, Any]]:
    """
    Filter activities by distance range, excluding those with missing/invalid distance.

    Args:
        activities: List of activity dictionaries
        min_distance: Minimum distance in km
        max_distance: Maximum distance in km

    Returns:
        Filtered list of activities with valid distance in range
    """

    def distance_in_range(activity_item):
        if not has_valid_distance(activity_item):
            return False
        distance = activity_item.get("distance_km")
        return min_distance <= distance <= max_distance

    return [activity for activity in activities if distance_in_range(activity)]


def is_valid_gps_coordinate(lat: Any, lng: Any) -> bool:
    """
    Validate GPS coordinates for proper type and range.

    Args:
        lat: Latitude value to validate
        lng: Longitude value to validate

    Returns:
        True if both coordinates are valid, False otherwise
    """
    try:
        # Check if values are not None and are numeric
        if lat is None or lng is None:
            return False

        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            return False

        # Check if within valid ranges
        return -90 <= lat <= 90 and -180 <= lng <= 180
    except (TypeError, ValueError):
        return False


def extract_valid_route_positions(samples_data: List[Dict[str, Any]]) -> List[List[float]]:
    """
    Extract valid GPS route positions with robust validation.

    Args:
        samples_data: List of sample dictionaries containing GPS data

    Returns:
        List of [lat, lng] coordinate pairs that pass validation
    """
    if not samples_data or not isinstance(samples_data, list):
        return []

    route_positions = []
    for sample in samples_data:
        lat = sample.get("position_lat")
        lng = sample.get("position_long")

        if is_valid_gps_coordinate(lat, lng):
            route_positions.append([lat, lng])

    return route_positions
