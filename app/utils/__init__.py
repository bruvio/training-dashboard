"""Utility modules for the Garmin Dashboard application."""

from .activity_helpers import (
    extract_valid_route_positions,
    filter_activities_by_distance,
    get_activity_sort_key,
    get_map_center_from_route,
    get_neutral_map_defaults,
    has_valid_distance,
    is_valid_gps_coordinate,
    parse_duration_to_seconds,
    sort_activities,
)
from .logging_config import DashboardLogger, get_logger, log_error, log_function_call

__all__ = [
    "DashboardLogger",
    "get_logger",
    "log_error",
    "log_function_call",
    "parse_duration_to_seconds",
    "get_activity_sort_key",
    "sort_activities",
    "get_neutral_map_defaults",
    "get_map_center_from_route",
    "has_valid_distance",
    "filter_activities_by_distance",
    "is_valid_gps_coordinate",
    "extract_valid_route_positions",
]
