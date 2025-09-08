#!/usr/bin/env python3
"""
Simple test to verify activities sync with saved tokens.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

try:
    import garth

    logger.info(f"Garth {getattr(garth, '__version__', 'unknown')} available")
except ImportError:
    logger.error("Garth not available")
    sys.exit(1)


def test_activities():
    """Test activities retrieval with existing tokens."""
    token_file = Path.home() / ".garmin" / "tokens.json"

    if not token_file.exists():
        print("No saved tokens found. Run the login script first.")
        return False

    try:
        # Load tokens
        data = json.loads(token_file.read_text())
        if "oauth1_token" in data and "oauth2_token" in data:
            garth.client.oauth1_token = data["oauth1_token"]
            garth.client.oauth2_token = data["oauth2_token"]
        else:
            garth.client.load_tokens(data)

        logger.info("Tokens loaded successfully")

        # Test activities retrieval
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        logger.info(f"Fetching activities from {start.date()} to {end.date()}")

        # Try different methods to get activities
        activities = None

        # Method 1: garth.data.activities
        try:
            logger.info("Trying garth.data.activities...")
            activities = garth.data.activities(start=start.date(), end=end.date())
            logger.info(f"Method 1 success: got {len(activities) if activities else 0} activities")
        except Exception as e:
            logger.warning(f"Method 1 failed: {e}")

        # Method 2: Direct API call
        if not activities:
            try:
                logger.info("Trying direct connectapi call...")
                from garth import connectapi

                url = f"/activitylist-service/activities/search/activities"
                params = {
                    "start": 0,
                    "limit": 100,
                    "startDate": start.date().isoformat(),
                    "endDate": end.date().isoformat(),
                }
                response = connectapi(url, params=params)
                activities = response if isinstance(response, list) else response.get("activities", [])
                logger.info(f"Method 2 success: got {len(activities) if activities else 0} activities")
            except Exception as e:
                logger.warning(f"Method 2 failed: {e}")

        # Method 3: Using garth.client directly
        if not activities:
            try:
                logger.info("Trying garth.client.get...")
                url = "/activitylist-service/activities/search/activities"
                params = {
                    "start": 0,
                    "limit": 100,
                    "startDate": start.date().isoformat(),
                    "endDate": end.date().isoformat(),
                }
                response = garth.client.get("connectapi", url, params=params)
                activities = response if isinstance(response, list) else response.get("activities", [])
                logger.info(f"Method 3 success: got {len(activities) if activities else 0} activities")
            except Exception as e:
                logger.warning(f"Method 3 failed: {e}")

        if activities:
            print(f"✓ Successfully retrieved {len(activities)} activities!")

            # Display first few activities
            for i, activity in enumerate(activities[:5], 1):
                name = activity.get("activityName", "Unknown")
                activity_type = activity.get("activityType", {}).get("typeKey", "Unknown")
                start_time = activity.get("startTimeLocal", "No date")
                distance = activity.get("distance", 0)

                print(f"  {i}. {name} ({activity_type}) - {start_time}")
                if distance:
                    print(f"     Distance: {distance/1000:.1f} km")

            return True
        else:
            print("✗ No activities retrieved")
            return False

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_activities()
    sys.exit(0 if success else 1)
