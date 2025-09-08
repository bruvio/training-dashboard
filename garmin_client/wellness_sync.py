#!/usr/bin/env python3
"""
wellness_sync.py — wrapper-first Garmin wellness sync with robust fallbacks.

Fetches per-day:
- sleep, steps, stress, resting_hr, hrv, body_battery, training_readiness, **vo2max**

Notes:
- Resting HR parsed from multiple shapes incl. allMetrics.metricsMap.WELLNESS_RESTING_HEART_RATE[0].value
- VO2max parsed from wrapper `vo2max` (list/dict) or API fallbacks (get_vo2max / get_max_metrics)
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
import os
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from . import client as _client


def get_client() -> "_client.GarminConnectClient":
    token_dir = os.getenv("GARMINTOKENS") or "~/.garminconnect"
    gc = _client.GarminConnectClient(token_dir=token_dir)
    st = gc.load_session()
    if not st.get("is_authenticated"):
        email = os.getenv("EMAIL")
        password = os.getenv("PASSWORD")
        if not (email and password):
            raise RuntimeError("Not authenticated and missing EMAIL/PASSWORD for login.")
        res = gc.login(email, password)
        if not (res and res.get("success")):
            raise RuntimeError("Login did not succeed.")
    return gc


# ------------ helpers ------------
def _to_date(d: Any) -> date:
    if isinstance(d, date):
        return d
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    raise TypeError("Date must be date, datetime, or YYYY-MM-DD string")


def _daterange(s: date, e: date) -> Iterable[date]:
    cur = s
    while cur <= e:
        yield cur
        cur += timedelta(days=1)


def _df(rows: List[Dict[str, Any]], cols: List[str]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
    return df.reset_index(drop=True)


def _num(x):
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _extract_rhr(payload: Any) -> Optional[float]:
    if not isinstance(payload, dict):
        return None
    for k in ("restingHeartRate", "restingHR", "restingHr", "rhr"):
        v = payload.get(k)
        if v is not None:
            return _num(v)
    for node_key in ("summary", "summaryDTO", "heartRateSummary", "dailySummary", "daySummary"):
        node = payload.get(node_key)
        if isinstance(node, dict):
            for k in ("restingHeartRate", "restingHR", "restingHr", "minHeartRate", "lowestHeartRate", "min", "lowest"):
                v = node.get(k)
                if v is not None:
                    return _num(v)
    all_metrics = payload.get("allMetrics") or {}
    metrics_map = all_metrics.get("metricsMap") or {}
    arr = metrics_map.get("WELLNESS_RESTING_HEART_RATE")
    if isinstance(arr, list) and arr:
        v = (arr[0] or {}).get("value")
        if v is not None:
            return _num(v)
    return None


def _extract_vo2max(obj: Any) -> Optional[float]:
    """Pull a single VO2max value from common shapes (wrapper/API)."""
    if obj is None:
        return None

    def from_dict(d: dict) -> Optional[float]:
        if not isinstance(d, dict):
            return None
        # 1) prefer nested "generic" node used by your bundle
        gen = d.get("generic") or {}
        for k in ("vo2MaxPreciseValue", "vo2MaxValue", "value"):
            v = gen.get(k)
            if v is not None:
                return _num(v)
        # 2) top-level fallbacks sometimes used by APIs
        for k in ("vo2MaxPreciseValue", "vo2MaxValue", "value"):
            v = d.get(k)
            if v is not None:
                return _num(v)
        return None

    # List (common): take the first non-null candidate
    if isinstance(obj, list) and obj:
        for item in obj:
            v = from_dict(item)
            if v is not None:
                return v
        return None

    # Dict
    if isinstance(obj, dict):
        return from_dict(obj)

    return None


def aggregate_df(df: pd.DataFrame, how: str) -> pd.DataFrame:
    if how in (None, "", "none"):
        return df.copy()
    if df.empty:
        return df.copy()
    out = df.copy()
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"])
        out = out.set_index("date")
    num = out.select_dtypes(include="number")
    if num.empty:
        return out.reset_index()
    rule = {"day": "D", "week": "W-MON", "month": "MS", "year": "YS"}.get(how, "D")
    out = num.resample(rule).mean().reset_index()
    return out


# ------------ core ------------
class WellnessSync:
    """Wrapper-first (wellness_summary_for_day), then raw API fallbacks."""

    def __init__(self, client: Optional[_client.GarminConnectClient] = None) -> None:
        self.client = client or get_client()

    def _try(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None

    def _call_api(self, api, name: str, *args):
        """Call api.<name>(*args) if it exists; otherwise return None."""
        fn = getattr(api, name, None)
        if not callable(fn):
            return None
        try:
            return fn(*args)
        except Exception:
            return None

    def fetch_range(self, start: str | date, end: str | date, include_extras: bool = True) -> Dict[str, pd.DataFrame]:
        """
        fetch_range _summary_

        Parameters
        ----------
        start : str | date
        end : str | date
        include_extras : bool, optional
            by default True

        Returns
        -------
        Dict[str, pd.DataFrame]
        """
        s = _to_date(start)
        e = _to_date(end)
        if s > e:
            s, e = e, s
        api = getattr(self.client, "api", self.client)

        rows_sleep: List[Dict[str, Any]] = []
        rows_steps: List[Dict[str, Any]] = []
        rows_stress: List[Dict[str, Any]] = []
        rows_rhr: List[Dict[str, Any]] = []
        rows_hrv: List[Dict[str, Any]] = []
        rows_bb: List[Dict[str, Any]] = []
        rows_tr: List[Dict[str, Any]] = []
        rows_vo2: List[Dict[str, Any]] = []

        for d in _daterange(s, e):
            ds = d.isoformat()
            blob = self._try(getattr(self.client, "wellness_summary_for_day"), ds)

            # ----- Sleep (wrapper) -----
            total_sec = sleep_min = eff = quality = deep = light = rem = awake = None
            if isinstance(blob, dict):
                sl = blob.get("sleep")
                if isinstance(sl, dict):
                    dto = sl.get("dailySleepDTO") or {}
                    dur = dto.get("sleepTimeSeconds") or sl.get("totalSleepSeconds") or sl.get("durationInSeconds")
                    if dur is not None:
                        try:
                            total_sec = int(float(dur))
                            sleep_min = int(round(total_sec / 60))
                        except Exception:
                            pass
                    eff = sl.get("sleepEfficiency") or dto.get("sleepEfficiency") or sl.get("efficiency")
                    quality = sl.get("overallSleepScore") or sl.get("quality")
                    deep = dto.get("deepSleepSeconds") or sl.get("deepSleepSeconds")
                    light = dto.get("lightSleepSeconds") or sl.get("lightSleepSeconds")
                    rem = dto.get("remSleepSeconds") or sl.get("remSleepSeconds")
                    awake = dto.get("awakeSeconds") or sl.get("awakeSeconds")

            # ----- Steps (wrapper, then API) -----
            steps_total = calories = distance_m = None
            if isinstance(blob, dict):
                st = blob.get("steps")
                if isinstance(st, dict):
                    steps_total = st.get("steps") or st.get("totalSteps") or st.get("value")
                    calories = st.get("calories") or st.get("activeKilocalories")
                    distance_m = st.get("distanceInMeters") or st.get("distance") or st.get("totalDistance")
                elif isinstance(st, list):
                    tot = cal = dist = 0.0
                    for it in st:
                        if not isinstance(it, dict):
                            continue
                        tot += _num(it.get("steps") or it.get("totalSteps") or it.get("value") or 0) or 0
                        cal += _num(it.get("calories") or it.get("activeKilocalories") or 0) or 0
                        dist += (
                            _num(it.get("distanceInMeters") or it.get("distance") or it.get("totalDistance") or 0) or 0
                        )
                    steps_total = int(tot) if tot else None
                    calories = cal if cal else None
                    distance_m = dist if dist else None
            if steps_total is None:
                steps = self._call_api(api, "get_daily_steps", ds, ds) or self._call_api(api, "get_steps_data", ds)
                if isinstance(steps, list):
                    tot = cal = dist = 0.0
                    for it in steps:
                        if not isinstance(it, dict):
                            continue
                        tot += _num(it.get("steps") or it.get("totalSteps") or it.get("value") or 0) or 0
                        cal += _num(it.get("calories") or it.get("activeKilocalories") or 0) or 0
                        dist += (
                            _num(it.get("distanceInMeters") or it.get("distance") or it.get("totalDistance") or 0) or 0
                        )
                    steps_total = int(tot) if tot else None
                    calories = calories or (cal if cal else None)
                    distance_m = distance_m or (dist if dist else None)
                elif isinstance(steps, dict):
                    steps_total = steps.get("steps") or steps.get("totalSteps") or steps.get("value")
                    calories = calories or steps.get("calories") or steps.get("activeKilocalories")
                    distance_m = (
                        distance_m
                        or steps.get("distanceInMeters")
                        or steps.get("distance")
                        or steps.get("totalDistance")
                    )

            # ----- Stress (wrapper) -----
            avg_stress = max_stress = rest_sec = None
            if isinstance(blob, dict):
                ss = blob.get("stress")
                if isinstance(ss, dict):
                    avg_stress = (
                        ss.get("avgStressLevel") or ss.get("averageStressLevel") or ss.get("overallStressLevel")
                    )
                    max_stress = ss.get("maxStressLevel") or ss.get("max")
                    rest_sec = ss.get("restStressDuration") or ss.get("restStressSec")

            # ----- Resting HR (API + robust parse) -----
            rhr_payload = (
                self._call_api(api, "get_rhr_day", ds)
                or self._call_api(api, "get_daily_hr", ds)
                or self._call_api(api, "get_resting_heart_rate", ds)
                or self._call_api(api, "get_rhr", ds)
            )
            rhr_val = _extract_rhr(rhr_payload) if isinstance(rhr_payload, dict) else None
            if rhr_val is None and isinstance(blob, dict) and isinstance(blob.get("sleep"), dict):
                rhr_val = _extract_rhr(blob.get("sleep"))

            # ----- HRV -----
            hrv_val = None
            if isinstance(blob, dict):
                hv = blob.get("hrv")
                if isinstance(hv, dict):
                    sm = hv.get("hrvSummary") or {}
                    hrv_val = sm.get("lastNightAvg") or sm.get("weeklyAvg") or hv.get("hrvValue") or hv.get("dailyAvg")
            if hrv_val is None:
                hv = self._call_api(api, "get_hrv_data", ds)
                if isinstance(hv, dict):
                    sm = hv.get("hrvSummary") or {}
                    hrv_val = sm.get("lastNightAvg") or sm.get("weeklyAvg") or hv.get("hrvValue") or hv.get("dailyAvg")

            # ----- Body Battery -----
            bb = self._call_api(api, "get_body_battery", ds, ds) or self._call_api(api, "get_body_battery_data", ds, ds)
            bb_avg = bb_charge = bb_drain = None
            if isinstance(bb, list) and bb:
                b0 = bb[0]
                bb_charge = b0.get("charged")
                bb_drain = b0.get("drained")
                levels = []
                for item in b0.get("bodyBatteryValuesArray") or []:
                    if isinstance(item, (list, tuple)):
                        if len(item) >= 3 and isinstance(item[2], (int, float)):
                            levels.append(item[2])
                        elif len(item) >= 2 and isinstance(item[1], (int, float)):
                            levels.append(item[1])
                if levels:
                    try:
                        bb_avg = float(pd.Series(levels).mean())
                    except Exception:
                        bb_avg = sum(levels) / len(levels)
            elif isinstance(bb, dict):
                bb_avg = bb.get("bodyBatteryAverage")
                bb_charge = bb.get("bodyBatteryCharge")
                bb_drain = bb.get("bodyBatteryDrain")

            # ----- Training Readiness -----
            trd = self._call_api(api, "get_training_readiness", ds)
            tr_score = (trd.get("trainingReadinessScore") or trd.get("score")) if isinstance(trd, dict) else None

            # ----- VO2max (wrapper first, then API; SAFE CALLS) -----
            vo2_val = None
            if isinstance(blob, dict):
                vo2_val = _extract_vo2max(blob.get("vo2max"))
            if vo2_val is None:
                vo2_raw = (
                    self._call_api(api, "get_vo2max", ds)
                    or self._call_api(api, "get_vo2_max", ds)
                    or self._call_api(api, "get_max_metrics", ds)
                )
                if isinstance(vo2_raw, dict) and vo2_raw and "vo2max" not in vo2_raw:
                    # e.g. {"running": {...}, "cycling": {...}}
                    cand = []
                    for v in vo2_raw.values():
                        if isinstance(v, dict):
                            vv = v.get("vo2MaxPreciseValue") or v.get("vo2MaxValue") or v.get("value")
                            if vv is not None:
                                cand.append(vv)
                    if cand:
                        try:
                            vo2_val = float(sum(map(float, cand)) / len(cand))
                        except Exception:
                            vo2_val = _num(cand[0])
                if vo2_val is None:
                    vo2_val = _extract_vo2max(vo2_raw)

            # ----- Collect rows -----
            rows_sleep.append(
                {
                    "date": ds,
                    "total_sleep_seconds": total_sec,
                    "sleep_min": sleep_min,
                    "efficiency": eff,
                    "quality": quality,
                    "deep_sec": deep,
                    "light_sec": light,
                    "rem_sec": rem,
                    "awake_sec": awake,
                }
            )
            rows_steps.append({"date": ds, "steps": steps_total, "calories": calories, "distance_m": distance_m})
            rows_stress.append({"date": ds, "stress_avg": avg_stress, "stress_max": max_stress, "rest_sec": rest_sec})
            rows_rhr.append({"date": ds, "resting_hr": rhr_val})
            rows_hrv.append({"date": ds, "hrv": hrv_val})
            rows_vo2.append({"date": ds, "vo2max": vo2_val})
            if include_extras:
                rows_bb.append({"date": ds, "avg": bb_avg, "charge": bb_charge, "drain": bb_drain})
                rows_tr.append({"date": ds, "score": tr_score})

        result: Dict[str, pd.DataFrame] = {
            "sleep": _df(
                rows_sleep,
                [
                    "date",
                    "total_sleep_seconds",
                    "sleep_min",
                    "efficiency",
                    "quality",
                    "deep_sec",
                    "light_sec",
                    "rem_sec",
                    "awake_sec",
                ],
            ),
            "steps": _df(rows_steps, ["date", "steps", "calories", "distance_m"]),
            "stress": _df(rows_stress, ["date", "stress_avg", "stress_max", "rest_sec"]),
            "resting_hr": _df(rows_rhr, ["date", "resting_hr"]),
            "hrv": _df(rows_hrv, ["date", "hrv"]),
            "vo2max": _df(rows_vo2, ["date", "vo2max"]),
        }
        if include_extras:
            bbdf = _df(rows_bb, ["date", "avg", "charge", "drain"])
            if not bbdf.empty:
                result["body_battery"] = bbdf
            trdf = _df(rows_tr, ["date", "score"])
            if not trdf.empty:
                result["training_readiness"] = trdf
        return result


class WellnessSyncManager:
    """Manager class for comprehensive wellness data syncing."""

    def __init__(self, client: Optional[_client.GarminConnectClient] = None) -> None:
        self.client = client or get_client()
        self.wellness_sync = WellnessSync(self.client)

    def sync_comprehensive_wellness(self, days: int = 30) -> Dict[str, Any]:
        """
        Perform comprehensive wellness sync for the specified number of days.
        Returns a result dictionary with success status and metrics.
        """
        try:
            from datetime import datetime, timedelta

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)

            # Fetch wellness data using the WellnessSync class
            wellness_data = self.wellness_sync.fetch_range(start=start_date, end=end_date, include_extras=True)

            # Count total non-null records across all wellness types
            total_records = 0
            for wellness_type, df in wellness_data.items():
                if not df.empty:
                    # Count non-null values excluding the date column
                    data_columns = [col for col in df.columns if col != "date"]
                    for col in data_columns:
                        total_records += df[col].notna().sum()

            return {
                "success": True,
                "total_records": total_records,
                "wellness_data": wellness_data,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_synced": days,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "total_records": 0}
