"""
garmin_client/sync.py

Fetch activities and (optionally) wellness data using `python-garminconnect`.
Returns normalized structures ready for the Dash page.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .client import GarminConnectClient, GarminAuthError
from .wellness_sync import WellnessSyncManager

logger = logging.getLogger(__name__)


def _daterange_days(end: datetime, days: int) -> Tuple[datetime, datetime]:
    end = end.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days - 1)
    return start, end


def _get(d: Dict[str, Any], *path, default=None):
    cur = d
    for k in path:
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(k)
        else:
            return default
    return cur if cur is not None else default


def _normalize_activities(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    norm: List[Dict[str, Any]] = []
    for a in items:
        act_id = a.get("activityId") or a.get("activityIdStr") or a.get("activity_id")
        start_local = a.get("startTimeLocal") or a.get("startTimeGMT") or a.get("startTime")
        name = a.get("activityName") or a.get("activityNameOriginal") or a.get("title") or ""
        act_type = _get(a, "activityType", "typeKey") or _get(a, "activityTypeDTO", "typeKey") or a.get("activityType")

        dist_m = a.get("distance") or a.get("distanceInMeters") or _get(a, "summaryDTO", "distance")
        dur_s = a.get("duration") or a.get("elapsedDuration") or _get(a, "summaryDTO", "duration")
        cal = a.get("calories") or _get(a, "summaryDTO", "calories")
        avg_hr = a.get("averageHR") or a.get("avgHr") or _get(a, "summaryDTO", "averageHR")
        max_hr = a.get("maxHR") or _get(a, "summaryDTO", "maxHR")
        avg_speed = a.get("averageSpeed") or _get(a, "summaryDTO", "averageSpeed")  # m/s
        elev_gain = a.get("elevationGain") or _get(a, "summaryDTO", "elevationGain")

        # Derived
        distance_km = float(dist_m) / 1000.0 if dist_m else None
        duration_min = float(dur_s) / 60.0 if dur_s else None
        speed_kmh = (
            float(avg_speed) * 3.6
            if avg_speed
            else (distance_km * 60.0 / duration_min if distance_km and duration_min else None)
        )
        pace_min_per_km = (duration_min / distance_km) if (duration_min and distance_km and distance_km > 0) else None

        norm.append(
            {
                "activity_id": act_id,
                "name": name,
                "type": act_type,
                "start": start_local,
                "distance_km": round(distance_km, 3) if distance_km is not None else None,
                "duration_min": round(duration_min, 2) if duration_min is not None else None,
                "avg_hr": avg_hr,
                "max_hr": max_hr,
                "speed_kmh": round(speed_kmh, 2) if speed_kmh is not None else None,
                "pace_min_per_km": round(pace_min_per_km, 2) if pace_min_per_km is not None else None,
                "calories": cal,
                "elev_gain_m": elev_gain,
            }
        )
    return norm


def sync_range(
    email: Optional[str] = None,
    password: Optional[str] = None,
    days: int = 30,
    download_fit: bool = False,
    fit_dir: Optional[Path] = None,
    fetch_wellness: bool = True,
) -> Dict[str, Any]:
    """
    High-level orchestrator; returns a summary dict for the UI.
    """
    now = datetime.now()
    start = (now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=max(1, int(days)) - 1)).date()
    end = now.date()

    client = GarminConnectClient()
    state = client.load_session()
    if not state.get("is_authenticated"):
        if not email or not password:
            return {"ok": False, "error": "No valid session. Email & password required."}
        login_result = client.login(email, password, remember=True)
        if login_result.get("mfa_required"):
            return {"ok": False, "mfa_required": True, "message": "MFA required"}

    # Fetch activities
    try:
        activities = client.get_activities_by_date(start, end, activity_type="")
    except GarminAuthError as e:
        return {"ok": False, "error": str(e)}

    # Optional: download FIT files
    fit_saved = 0
    fit_paths: List[Path] = []
    if download_fit:
        fit_dir = fit_dir or Path("./data/fit")
        for act in activities:
            act_id = act.get("activityId") or act.get("activity_id") or act.get("activityIdStr")
            if act_id is None:
                continue
            try:
                p = client.download_activity_fit(act_id, fit_dir)
                fit_paths.append(p)
                fit_saved += 1
            except Exception as e:
                logger.warning("Failed to download FIT for %s: %s", act_id, e)

    # Optional: comprehensive wellness data sync
    wellness_records = 0
    wellness_days: List[Dict[str, Any]] = []
    comprehensive_wellness = {}
    if fetch_wellness:
        try:
            # Use comprehensive wellness sync manager
            wellness_manager = WellnessSyncManager(client)
            wellness_result = wellness_manager.sync_comprehensive_wellness(days=days)

            if wellness_result.get("success"):
                comprehensive_wellness = wellness_result
                wellness_records = wellness_result.get("total_records", 0)
                logger.info(f"Comprehensive wellness sync completed: {wellness_records} records")
            else:
                logger.warning(f"Comprehensive wellness sync failed: {wellness_result.get('error', 'Unknown error')}")

            # Fallback to basic wellness summaries if comprehensive sync fails
            if wellness_records == 0:
                logger.info("Using fallback basic wellness sync")
                d = start
                while d <= end:
                    try:
                        w = client.wellness_summary_for_day(d)
                        wellness_days.append({"date": d.isoformat(), **w})
                        wellness_records += sum(1 for k, v in w.items() if v)
                    except Exception:
                        pass
                    d = d + timedelta(days=1)

        except Exception as e:
            logger.error(f"Wellness sync error: {e}")
            # Basic fallback
            d = start
            while d <= end:
                try:
                    w = client.wellness_summary_for_day(d)
                    wellness_days.append({"date": d.isoformat(), **w})
                    wellness_records += sum(1 for k, v in w.items() if v)
                except Exception:
                    pass
                d = d + timedelta(days=1)

    return {
        "ok": True,
        "activities_count": len(activities),
        "activities": activities,
        "activities_norm": _normalize_activities(activities),
        "fit_downloaded": fit_saved,
        "fit_paths": [str(p) for p in fit_paths],
        "wellness_records": wellness_records,
        "wellness_days": wellness_days,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
