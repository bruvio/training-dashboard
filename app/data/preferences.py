"""
User preferences management for Garmin Dashboard.

Handles storing and retrieving user display preferences that affect
how activities are visualized throughout the application.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils import get_logger

logger = get_logger(__name__)

# Default preferences
DEFAULT_PREFERENCES = {
    "theme": "light",
    "units": "metric",  # metric or imperial
    "default_chart_type": "line",  # line, bar, scatter
    "show_heart_rate_zones": True,
    "show_power_zones": True,
    "map_style": "openstreetmap",  # openstreetmap, satellite
    "activities_per_page": 20,
    "default_sort": "date_desc",  # date_desc, date_asc, distance_desc, etc.
    "show_activity_thumbnails": True,
    "enable_animations": True,
    "date_format": "%Y-%m-%d %H:%M",
}


class UserPreferences:
    """Manage user preferences with file-based storage."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize preferences manager."""
        if config_dir is None:
            # Use a data directory for preferences
            config_dir = Path("data/.config")

        self.config_dir = config_dir
        self.config_file = config_dir / "preferences.json"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load preferences
        self._preferences = self._load_preferences()

    def _load_preferences(self) -> Dict[str, Any]:
        """Load preferences from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    preferences = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**DEFAULT_PREFERENCES, **preferences}
            else:
                logger.info("No preferences file found, using defaults")
                return DEFAULT_PREFERENCES.copy()
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
            return DEFAULT_PREFERENCES.copy()

    def _save_preferences(self) -> bool:
        """Save preferences to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self._preferences, f, indent=2)
            logger.debug("Preferences saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        return self._preferences.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set a preference value."""
        self._preferences[key] = value
        return self._save_preferences()

    def update(self, preferences: Dict[str, Any]) -> bool:
        """Update multiple preferences at once."""
        self._preferences.update(preferences)
        return self._save_preferences()

    def get_all(self) -> Dict[str, Any]:
        """Get all preferences."""
        return self._preferences.copy()

    def reset_to_defaults(self) -> bool:
        """Reset all preferences to defaults."""
        self._preferences = DEFAULT_PREFERENCES.copy()
        return self._save_preferences()


# Global preferences instance
_preferences_instance: Optional[UserPreferences] = None


def get_preferences() -> UserPreferences:
    """Get the global preferences instance."""
    global _preferences_instance
    if _preferences_instance is None:
        _preferences_instance = UserPreferences()
    return _preferences_instance


def get_preference(key: str, default: Any = None) -> Any:
    """Convenience function to get a single preference."""
    return get_preferences().get(key, default)


def set_preference(key: str, value: Any) -> bool:
    """Convenience function to set a single preference."""
    return get_preferences().set(key, value)
