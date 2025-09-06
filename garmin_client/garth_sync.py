"""
Sync helpers that work on every garth version.

- Prefer module-level singleton `garth.client`.
- If `.activities` is missing, fall back to raw Connect API endpoints via `.connectapi`.
- Added health data sync: sleep, HRV, steps, stress data.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List

try:
    import garth  # type: ignore
except Exception:
    garth = None

logger = logging.getLogger(__name__)


def _fetch_activities_via_connectapi(c, start_date, end_date) -> List[dict]:
    # Try modern activity-service search first
    paths = [
        f"activity-service/activities/search/activities?start=0&limit=200&startDate={start_date}&endDate={end_date}",
        f"activitylist-service/activities/search/activities?start=0&limit=200&startDate={start_date}&endDate={end_date}",
    ]
    for p in paths:
        try:
            items = c.connectapi(p)
            if isinstance(items, list):
                return items
        except Exception:
            continue
    return []


def sync_health_data(days: int, data_types: List[str] = None) -> Dict:
    """
    Sync health and wellness data from Garmin Connect.

    Args:
        days: Number of days to sync
        data_types: List of data types to sync ['sleep', 'hrv', 'steps', 'stress'].
                   If None, syncs all available types.

    Returns:
        Dict with sync results and data statistics
    """
    if garth is None:
        return {
            "ok": True,
            "wellness_synced": False,
            "dev_mode": True,
            "msg": f"(dev) Would sync {days} days of health data.",
            "data": {},
        }

    if data_types is None:
        data_types = ["sleep", "hrv", "steps", "stress"]

    results = {
        "ok": True,
        "wellness_synced": True,
        "days": days,
        "sync_date": datetime.now().isoformat(),
        "data": {},
        "errors": [],
    }

    try:
        # Sleep Data
        if "sleep" in data_types:
            try:
                logger.info(f"Syncing sleep data for {days} days...")

                # Daily sleep quality scores
                daily_sleep = garth.DailySleep.list(period=days)
                sleep_quality_data = [
                    {"date": item.calendar_date.isoformat(), "sleep_quality_score": item.value} for item in daily_sleep
                ]

                # Detailed sleep data
                sleep_details = []
                if daily_sleep:
                    latest_date = daily_sleep[0].calendar_date
                    detailed_sleep = garth.SleepData.list(latest_date, days)

                    for sd in detailed_sleep:
                        if hasattr(sd, "daily_sleep_dto") and sd.daily_sleep_dto:
                            dto = sd.daily_sleep_dto
                            sleep_details.append(
                                {
                                    "date": dto.get("calendar_date"),
                                    "sleep_start_timestamp": dto.get("sleep_start_timestamp_local"),
                                    "sleep_end_timestamp": dto.get("sleep_end_timestamp_local"),
                                    "deep_sleep_hours": dto.get("deep_sleep_seconds", 0) / 3600,
                                    "light_sleep_hours": dto.get("light_sleep_seconds", 0) / 3600,
                                    "rem_sleep_hours": dto.get("rem_sleep_seconds", 0) / 3600,
                                    "awake_hours": dto.get("awake_sleep_seconds", 0) / 3600,
                                    "total_sleep_hours": dto.get("total_sleep_seconds", 0) / 3600,
                                }
                            )

                results["data"]["sleep"] = {
                    "quality": sleep_quality_data,
                    "details": sleep_details,
                    "quality_records": len(sleep_quality_data),
                    "details_records": len(sleep_details),
                }

                logger.info(f"Sleep data: {len(sleep_quality_data)} quality, {len(sleep_details)} detailed records")

            except Exception as e:
                error_msg = f"Sleep data sync failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        # HRV Data
        if "hrv" in data_types:
            try:
                logger.info(f"Syncing HRV data for {days} days...")

                hrv_data = garth.DailyHRV.list(period=days)
                hrv_records = [
                    {"date": item.calendar_date.isoformat(), "hrv_value": item.value}
                    for item in hrv_data
                    if hasattr(item, "value") and item.value is not None
                ]

                results["data"]["hrv"] = {"records": hrv_records, "count": len(hrv_records)}

                logger.info(f"HRV data: {len(hrv_records)} records")

            except Exception as e:
                error_msg = f"HRV data sync failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        # Steps Data
        if "steps" in data_types:
            try:
                logger.info(f"Syncing steps data for {days} days...")

                # Daily steps
                daily_steps = garth.DailySteps.list(period=days)
                steps_records = [{"date": item.calendar_date.isoformat(), "steps": item.value} for item in daily_steps]

                # Weekly steps (if available)
                weekly_records = []
                try:
                    weekly_periods = min(days // 7 + 1, 12)  # Max 12 weeks
                    weekly_steps = garth.WeeklySteps.list(period=weekly_periods)
                    weekly_records = [
                        {"week_start_date": item.calendar_date.isoformat(), "weekly_steps": item.value}
                        for item in weekly_steps
                    ]
                except Exception as e:
                    logger.warning(f"Weekly steps not available: {e}")

                results["data"]["steps"] = {
                    "daily": steps_records,
                    "weekly": weekly_records,
                    "daily_count": len(steps_records),
                    "weekly_count": len(weekly_records),
                }

                logger.info(f"Steps data: {len(steps_records)} daily, {len(weekly_records)} weekly records")

            except Exception as e:
                error_msg = f"Steps data sync failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        # Stress Data
        if "stress" in data_types:
            try:
                logger.info(f"Syncing stress data for {days} days...")

                # Daily stress
                daily_stress = garth.DailyStress.list(period=days)
                stress_records = [
                    {
                        "date": item.calendar_date.isoformat(),
                        "overall_stress_level": item.overall_stress_level,
                        "rest_stress_duration": item.rest_stress_duration,
                        "low_stress_duration": item.low_stress_duration,
                        "medium_stress_duration": item.medium_stress_duration,
                        "high_stress_duration": item.high_stress_duration,
                    }
                    for item in daily_stress
                ]

                # Weekly stress (if available)
                weekly_stress_records = []
                try:
                    weekly_periods = min(days // 7 + 1, 12)
                    weekly_stress = garth.WeeklyStress.list(period=weekly_periods)
                    weekly_stress_records = [
                        {"week_start_date": item.calendar_date.isoformat(), "weekly_stress": item.value}
                        for item in weekly_stress
                    ]
                except Exception as e:
                    logger.warning(f"Weekly stress not available: {e}")

                results["data"]["stress"] = {
                    "daily": stress_records,
                    "weekly": weekly_stress_records,
                    "daily_count": len(stress_records),
                    "weekly_count": len(weekly_stress_records),
                }

                logger.info(f"Stress data: {len(stress_records)} daily, {len(weekly_stress_records)} weekly records")

            except Exception as e:
                error_msg = f"Stress data sync failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        # Calculate totals
        total_records = 0
        for data_type, data in results["data"].items():
            if data_type == "sleep":
                total_records += data.get("quality_records", 0) + data.get("details_records", 0)
            elif data_type in ["hrv"]:
                total_records += data.get("count", 0)
            else:  # steps, stress
                total_records += data.get("daily_count", 0) + data.get("weekly_count", 0)

        results["total_records"] = total_records

        if results["errors"]:
            results["ok"] = False
            results[
                "msg"
            ] = f"Partial sync completed with {len(results['errors'])} errors. {total_records} total records."
        else:
            results["msg"] = f"Successfully synced {total_records} health records from the last {days} days."

        return results

    except Exception as e:
        logger.exception("Health data sync failed: %s", e)
        return {"ok": False, "error": str(e), "wellness_synced": False, "data": {}}


def sync_recent(days: int) -> Dict:
    """
    Original function for syncing activities (kept for backward compatibility).
    Note: Activity data has limited availability through garth library.
    """
    if garth is None:
        return {
            "ok": True,
            "activities_fetched": 0,
            "wellness_synced": False,
            "dev_mode": True,
            "msg": f"(dev) Would sync last {days} days.",
        }
    try:
        c = garth.client  # ALWAYS use the module-level client
        end = datetime.now(timezone.utc).date()
        start = (datetime.now(timezone.utc) - timedelta(days=days)).date()

        # Path A: helper exists
        if hasattr(c, "activities"):
            try:
                acts = c.activities(start=start, limit=500)
                count = len(list(acts))
                return {
                    "ok": True,
                    "activities_fetched": count,
                    "wellness_synced": False,
                    "msg": f"Synced {count} activities from the last {days} days.",
                }
            except Exception as e:
                logger.info("activities() helper failed on this garth, falling back: %s", e)

        # Path B: raw connectapi
        items = _fetch_activities_via_connectapi(c, start.isoformat(), end.isoformat())
        count = len(items)
        return {
            "ok": True,
            "activities_fetched": count,
            "wellness_synced": False,
            "msg": f"Synced {count} activities from the last {days} days.",
        }
    except Exception as e:
        logger.exception("Sync failed: %s", e)
        return {"ok": False, "error": str(e)}


def sync_comprehensive(days: int) -> Dict:
    """
    Comprehensive sync that attempts both activities and health data.
    """
    if garth is None:
        return {
            "ok": True,
            "activities_fetched": 0,
            "wellness_synced": False,
            "dev_mode": True,
            "msg": f"(dev) Would sync {days} days of comprehensive data.",
        }

    # Sync activities (limited data available)
    activity_result = sync_recent(days)

    # Sync health data (comprehensive data available)
    health_result = sync_health_data(days)

    # Combine results
    return {
        "ok": activity_result.get("ok", False) and health_result.get("ok", False),
        "activities_fetched": activity_result.get("activities_fetched", 0),
        "wellness_synced": health_result.get("wellness_synced", False),
        "health_data": health_result.get("data", {}),
        "total_health_records": health_result.get("total_records", 0),
        "errors": health_result.get("errors", []),
        "msg": f"Activities: {activity_result.get('msg', 'Failed')} | Health: {health_result.get('msg', 'Failed')}",
    }
