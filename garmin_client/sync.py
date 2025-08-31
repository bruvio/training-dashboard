"""
Garmin Connect data synchronization module.
Handles downloading and processing activity data from Garmin Connect.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from app.data.db import session_scope
from app.data.models import Activity, Sample
from .client import GarminConnectClient

logger = logging.getLogger(__name__)


def sync_activities_from_garmin(
    email: str,
    password: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    max_activities: Optional[int] = None,
) -> Dict:
    """
    Sync activities from Garmin Connect to local database.

    Args:
        email: Garmin Connect email
        password: Garmin Connect password
        start_date: Start date for activity sync (defaults to 30 days ago)
        end_date: End date for activity sync (defaults to today)
        max_activities: Maximum number of activities to sync

    Returns:
        Dictionary with sync results and statistics
    """

    results = {
        "success": False,
        "activities_processed": 0,
        "activities_new": 0,
        "activities_updated": 0,
        "errors": [],
        "start_time": datetime.now(),
        "end_time": None,
    }

    try:
        # Initialize Garmin Connect client
        client = GarminConnectClient()

        # Login to Garmin Connect
        logger.info(f"Logging in to Garmin Connect for {email}")
        login_result = client.login(email, password)

        if not login_result.get("success"):
            results["errors"].append(f"Login failed: {login_result.get('message', 'Unknown error')}")
            return results

        # Set default date range if not provided
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        logger.info(f"Syncing activities from {start_date.date()} to {end_date.date()}")

        # Get activities from Garmin Connect
        activities = client.get_activities(start_date=start_date, end_date=end_date, max_activities=max_activities)

        if not activities:
            logger.info("No activities found in the specified date range")
            results["success"] = True
            return results

        logger.info(f"Found {len(activities)} activities to process")

        # Process each activity
        with session_scope() as session:
            for activity_data in activities:
                try:
                    # Check if activity already exists
                    garmin_id = activity_data.get("activityId")
                    existing_activity = session.query(Activity).filter_by(garmin_activity_id=garmin_id).first()

                    if existing_activity:
                        # Update existing activity
                        updated = update_activity_from_garmin(session, existing_activity, activity_data, client)
                        if updated:
                            results["activities_updated"] += 1
                    else:
                        # Create new activity
                        new_activity = create_activity_from_garmin(session, activity_data, client)
                        if new_activity:
                            results["activities_new"] += 1

                    results["activities_processed"] += 1

                except Exception as e:
                    error_msg = f"Error processing activity {garmin_id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    continue

            # Commit all changes
            session.commit()
            logger.info("Successfully committed all activity data to database")

        results["success"] = True
        logger.info(
            f"Sync completed successfully. Processed: {results['activities_processed']}, New: {results['activities_new']}, Updated: {results['activities_updated']}"
        )

    except Exception as e:
        error_msg = f"Sync failed with error: {str(e)}"
        logger.error(error_msg)
        results["errors"].append(error_msg)

    finally:
        results["end_time"] = datetime.now()
        results["duration_seconds"] = (results["end_time"] - results["start_time"]).total_seconds()

    return results


def create_activity_from_garmin(session, activity_data: Dict, client: GarminConnectClient) -> Optional[Activity]:
    """
    Create a new Activity record from Garmin Connect data.

    Args:
        session: Database session
        activity_data: Raw activity data from Garmin Connect
        client: Garmin Connect client for additional data requests

    Returns:
        Created Activity object or None if creation failed
    """
    try:
        # Extract basic activity information
        garmin_id = activity_data.get("activityId")

        # Create new Activity record
        activity = Activity(
            garmin_activity_id=garmin_id,
            sport=activity_data.get("activityType", {}).get("typeKey", "unknown"),
            start_time_utc=(
                datetime.fromisoformat(activity_data.get("startTimeGMT", "").replace("Z", "+00:00"))
                if activity_data.get("startTimeGMT")
                else None
            ),
            elapsed_time_s=activity_data.get("elapsedDuration"),
            distance_m=activity_data.get("distance"),
            avg_speed_mps=activity_data.get("averageSpeed"),
            max_speed_mps=activity_data.get("maxSpeed"),
            elevation_gain_m=activity_data.get("elevationGain"),
            elevation_loss_m=activity_data.get("elevationLoss"),
            avg_heart_rate=activity_data.get("averageHR"),
            max_heart_rate=activity_data.get("maxHR"),
            calories=activity_data.get("calories"),
            source="garmin_connect",
        )

        session.add(activity)
        session.flush()  # Get the ID

        # Download detailed activity data if available
        try:
            detailed_data = client.get_activity_details(garmin_id)
            if detailed_data and detailed_data.get("samples"):
                create_samples_from_garmin(session, activity.id, detailed_data["samples"])

        except Exception as e:
            logger.warning(f"Could not download detailed data for activity {garmin_id}: {e}")

        logger.info(f"Created new activity: {garmin_id} ({activity.sport})")
        return activity

    except Exception as e:
        logger.error(f"Failed to create activity from Garmin data: {e}")
        return None


def update_activity_from_garmin(session, activity: Activity, activity_data: Dict, client: GarminConnectClient) -> bool:
    """
    Update an existing Activity record with fresh Garmin Connect data.

    Args:
        session: Database session
        activity: Existing Activity object
        activity_data: Fresh activity data from Garmin Connect
        client: Garmin Connect client for additional data requests

    Returns:
        True if activity was updated, False otherwise
    """
    try:
        updated = False

        # Update basic fields if they've changed
        new_distance = activity_data.get("distance")
        if new_distance and new_distance != activity.distance_m:
            activity.distance_m = new_distance
            updated = True

        new_duration = activity_data.get("elapsedDuration")
        if new_duration and new_duration != activity.elapsed_time_s:
            activity.elapsed_time_s = new_duration
            updated = True

        new_calories = activity_data.get("calories")
        if new_calories and new_calories != activity.calories:
            activity.calories = new_calories
            updated = True

        # Update timestamp for tracking
        if updated:
            activity.updated_at = datetime.utcnow()
            logger.info(f"Updated activity: {activity.garmin_activity_id}")

        return updated

    except Exception as e:
        logger.error(f"Failed to update activity {activity.garmin_activity_id}: {e}")
        return False


def create_samples_from_garmin(session, activity_id: int, samples_data: List[Dict]) -> int:
    """
    Create Sample records from Garmin Connect detailed activity data.

    Args:
        session: Database session
        activity_id: ID of the parent Activity
        samples_data: List of sample data points from Garmin

    Returns:
        Number of samples created
    """
    try:
        samples_created = 0

        for sample_data in samples_data:
            try:
                sample = Sample(
                    activity_id=activity_id,
                    elapsed_time_s=sample_data.get("elapsed_time", 0),
                    latitude=sample_data.get("latitude"),
                    longitude=sample_data.get("longitude"),
                    altitude_m=sample_data.get("altitude"),
                    heart_rate=sample_data.get("heart_rate"),
                    speed_mps=sample_data.get("speed"),
                    power_w=sample_data.get("power"),
                    cadence_rpm=sample_data.get("cadence"),
                    temperature_c=sample_data.get("temperature"),
                )

                session.add(sample)
                samples_created += 1

            except Exception as e:
                logger.warning(f"Could not create sample at time {sample_data.get('elapsed_time', 'unknown')}: {e}")
                continue

        logger.info(f"Created {samples_created} samples for activity {activity_id}")
        return samples_created

    except Exception as e:
        logger.error(f"Failed to create samples for activity {activity_id}: {e}")
        return 0


def get_sync_status() -> Dict:
    """
    Get current synchronization status and statistics.

    Returns:
        Dictionary with sync status information
    """
    try:
        with session_scope() as session:
            # Count activities by source
            total_activities = session.query(Activity).count()
            garmin_activities = session.query(Activity).filter_by(source="garmin_connect").count()
            fit_file_activities = session.query(Activity).filter_by(source="fit_file").count()

            # Get latest activity dates
            latest_activity = session.query(Activity).order_by(Activity.start_time_utc.desc()).first()
            latest_garmin_activity = (
                session.query(Activity)
                .filter_by(source="garmin_connect")
                .order_by(Activity.start_time_utc.desc())
                .first()
            )

            return {
                "total_activities": total_activities,
                "garmin_activities": garmin_activities,
                "fit_file_activities": fit_file_activities,
                "latest_activity_date": latest_activity.start_time_utc.isoformat() if latest_activity else None,
                "latest_garmin_sync_date": (
                    latest_garmin_activity.start_time_utc.isoformat() if latest_garmin_activity else None
                ),
                "last_updated": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        return {"error": str(e), "last_updated": datetime.utcnow().isoformat()}
