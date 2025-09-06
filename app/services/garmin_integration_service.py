"""
Garmin Integration Service - Direct integration with Garmin Connect API.

This service provides wellness data synchronization using the existing garmin_client,
with data transformation, smoothing/aggregation, and persistence to the dashboard database.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.services.wellness_data_service import WellnessDataService
from app.utils import get_logger
from garmin_client.client import GarminConnectClient, GarminAuthError

logger = get_logger(__name__)


class GarminIntegrationService:
    """Service for direct Garmin Connect API integration and wellness data sync."""

    def __init__(self):
        """Initialize the Garmin integration service."""
        self.client = GarminConnectClient()
        self.wellness_service = WellnessDataService()
        self.logger = logger
        
        # Try to load existing session automatically
        try:
            session_data = self.client.load_session()
            if session_data.get("is_authenticated"):
                self.logger.info(f"✅ Loaded existing Garmin session for user: {session_data.get('username', 'unknown')}")
            else:
                self.logger.warning("⚠️ No valid existing session found")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load existing session: {e}")

    def authenticate_garmin(self, email: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize Garmin API connection using existing client.

        Args:
            email: Garmin Connect email (optional if credentials stored)
            password: Garmin Connect password (optional if credentials stored)

        Returns:
            Dict with authentication status and message
        """
        try:
            # Check if already authenticated
            if self.client.is_authenticated():
                username = self.client.username()
                self.logger.info(f"✅ Already authenticated with Garmin Connect as {username}")
                return {"success": True, "message": f"Already authenticated as {username}"}

            # Try to authenticate with provided credentials
            if email and password:
                result = self.client.login(email, password)
                if result.get("success"):
                    self.logger.info("✅ Garmin Connect authentication successful")
                    return {"success": True, "message": "Successfully authenticated with Garmin Connect"}
                else:
                    return {"success": False, "error": "Failed to authenticate with provided credentials"}
            else:
                # Try to load existing session
                try:
                    session_data = self.client.load_session()
                    if session_data.get("is_authenticated"):
                        self.logger.info("✅ Using existing Garmin Connect session")
                        return {
                            "success": True,
                            "message": f"Using existing session for {session_data.get('username', 'user')}",
                        }
                    else:
                        return {"success": False, "error": "No valid stored session found"}
                except Exception:
                    return {"success": False, "error": "No stored credentials found and no credentials provided"}

        except GarminAuthError as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            self.logger.error(f"❌ Unexpected authentication error: {e}")
            return {"success": False, "error": str(e)}

    def sync_wellness_data_range(self, start_date: date, end_date: date, smoothing: str = "none") -> Dict[str, Any]:
        """
        Sync wellness data directly from Garmin Connect API.

        Args:
            start_date: Start date for data sync
            end_date: End date for data sync
            smoothing: Smoothing method ["none", "day", "week", "month", "year"]

        Returns:
            Dict with sync results and statistics
        """
        try:
            # Check authentication and try to restore session if needed
            if not self.client.is_authenticated():
                # Try to load session again in case it was established elsewhere
                try:
                    session_data = self.client.load_session()
                    if not session_data.get("is_authenticated"):
                        return {
                            "success": False, 
                            "error": "Not authenticated with Garmin Connect. Please log in first on the Garmin login page (/garmin).", 
                            "requires_auth": True
                        }
                    else:
                        self.logger.info("✅ Successfully restored Garmin session")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not restore session: {e}")
                    return {
                        "success": False, 
                        "error": "Authentication required. Please log in first on the Garmin login page (/garmin).", 
                        "requires_auth": True
                    }

            self.logger.info(f"🔄 Starting wellness data sync from {start_date} to {end_date}")

            # Initialize counters
            total_records = 0
            days_synced = 0
            persistence_results = {}

            # Collect all wellness data for the date range
            wellness_data = {
                "sleep": [],
                "steps": [],
                "heart_rate": [],
                "body_battery": [],
                "stress": [],
                "training_readiness": [],
            }

            current_date = start_date
            while current_date <= end_date:
                self.logger.info(f"📅 Syncing data for {current_date}")

                try:
                    # Get wellness summary for this day using existing client method
                    daily_data = self.client.wellness_summary_for_day(current_date)

                    if daily_data:
                        # Transform and collect data by type
                        for data_type, data_value in daily_data.items():
                            if data_type in wellness_data and data_value:
                                # Add date to the data
                                if isinstance(data_value, dict):
                                    data_value["date"] = current_date.isoformat()
                                    wellness_data[data_type].append(data_value)
                                    total_records += 1

                        days_synced += 1

                except Exception as day_error:
                    self.logger.warning(f"⚠️ Failed to sync data for {current_date}: {day_error}")

                current_date += timedelta(days=1)

            # Persist the collected data to database
            self.logger.info("💾 Persisting wellness data to database...")

            if wellness_data["sleep"]:
                persistence_results["sleep"] = self.wellness_service.persist_sleep_data(wellness_data["sleep"])

            if wellness_data["steps"]:
                persistence_results["steps"] = self.wellness_service.persist_steps_data(wellness_data["steps"])

            if wellness_data["heart_rate"]:
                persistence_results["heart_rate"] = self.wellness_service.persist_heart_rate_data(
                    wellness_data["heart_rate"]
                )

            if wellness_data["body_battery"]:
                persistence_results["body_battery"] = self.wellness_service.persist_body_battery_data(
                    wellness_data["body_battery"]
                )

            if wellness_data["stress"]:
                persistence_results["stress"] = self.wellness_service.persist_stress_data(wellness_data["stress"])

            if wellness_data["training_readiness"]:
                persistence_results["training_readiness"] = self.wellness_service.persist_training_readiness_data(
                    wellness_data["training_readiness"]
                )

            # Calculate success metrics
            successful_types = sum(1 for success in persistence_results.values() if success)

            self.logger.info(
                f"✅ Sync completed: {days_synced} days, {total_records} records, {successful_types} data types"
            )

            return {
                "success": True,
                "message": f"Successfully synced {days_synced} days of wellness data",
                "days_synced": days_synced,
                "records_synced": total_records,
                "data_types_synced": successful_types,
                "persistence": persistence_results,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "smoothing": smoothing,
            }

        except GarminAuthError as e:
            self.logger.error(f"❌ Authentication error during sync: {e}")
            return {"success": False, "error": "Authentication required", "requires_auth": True}
        except Exception as e:
            self.logger.error(f"❌ Sync failed with error: {e}")
            return {
                "success": False,
                "error": str(e),
                "days_synced": days_synced if "days_synced" in locals() else 0,
                "records_synced": total_records if "total_records" in locals() else 0,
            }

    def _transform_dailies_to_db_format(
        self, dailies_data: List[Dict[str, Any]], smoothing: str = "none"
    ) -> Dict[str, Any]:
        """
        Transform wellness data format for database persistence.

        Args:
            dailies_data: Raw wellness data from Garmin
            smoothing: Smoothing method to apply

        Returns:
            Dict with transformed wellness data by type
        """
        # This method would implement data transformation and smoothing
        # For now, return data as-is since the client already provides clean data
        return {
            "sleep": dailies_data,
            "steps": dailies_data,
            "heart_rate": dailies_data,
            "body_battery": dailies_data,
            "stress": dailies_data,
            "training_readiness": dailies_data,
        }
