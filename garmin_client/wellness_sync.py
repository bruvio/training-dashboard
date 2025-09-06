#!/usr/bin/env python3
"""
wellness_sync.py — refactored to mirror bruvio-garmin interval flow.

- Uses your client.GarminConnectClient
- Per-day: first uses client.wellness_summary_for_day(date) like your script,
  then falls back to raw api.* calls.
- Critically: parses resting HR from Garmin's metricsMap shape:
  allMetrics.metricsMap.WELLNESS_RESTING_HEART_RATE[0].value
- Adds robust step distance fallback for 'totalDistance' as well as 'distanceInMeters'.
- Returns tidy DataFrames for sleep, steps, stress, resting_hr, hrv, body_battery, training_readiness.
- Provides aggregate_df(df, how) helper (none/day/week/month/year).
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import client as _client


# ---------------------------
# Bootstrap client (your API)
# ---------------------------
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


# ---------------------------
# Helpers
# ---------------------------
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
    """
    Extract resting HR from a variety of Garmin shapes, including:
    - top-level keys (restingHeartRate / restingHr / restingHR)
    - nested summary nodes
    - metricsMap.WELLNESS_RESTING_HEART_RATE[0].value (the one your JSON shows)
    """
    if not isinstance(payload, dict):
        return None

    # direct keys first
    for k in ("restingHeartRate", "restingHR", "restingHr", "rhr"):
        v = payload.get(k)
        if v is not None:
            return _num(v)

    # common nested "summary" style nodes
    for node_key in ("summary", "summaryDTO", "heartRateSummary", "dailySummary", "daySummary"):
        node = payload.get(node_key)
        if isinstance(node, dict):
            for k in ("restingHeartRate", "restingHR", "restingHr", "minHeartRate", "lowestHeartRate", "min", "lowest"):
                v = node.get(k)
                if v is not None:
                    return _num(v)

    # Garmin metricsMap (this is what your bruvio JSON uses)
    # allMetrics.metricsMap.WELLNESS_RESTING_HEART_RATE -> [ { "value": 56.0, "calendarDate": "YYYY-MM-DD" }, ... ]
    all_metrics = payload.get("allMetrics") or {}
    metrics_map = all_metrics.get("metricsMap") or {}
    arr = metrics_map.get("WELLNESS_RESTING_HEART_RATE")
    if isinstance(arr, list) and arr:
        first = arr[0]
        if isinstance(first, dict):
            v = first.get("value")
            if v is not None:
                return _num(v)

    return None


def aggregate_df(df: pd.DataFrame, how: str) -> pd.DataFrame:
    """Aggregate by day/week/month/year (numeric cols)."""
    if how in (None, "", "none"):
        return df.copy()
    if df.empty:
        return df.copy()
    df2 = df.copy()
    if "date" in df2.columns:
        df2["date"] = pd.to_datetime(df2["date"])
        df2 = df2.set_index("date")
    num = df2.select_dtypes(include="number")
    if num.empty:
        return df2.reset_index()
    rule = {"day": "D", "week": "W-MON", "month": "MS", "year": "YS"}.get(how, "D")
    out = num.resample(rule).mean()
    out = out.reset_index()
    return out


# ---------------------------
# Core class
# ---------------------------
class WellnessSync:
    """Wrapper-first (your aggregator), then raw API fallbacks — like bruvio-garmin."""

    def __init__(self, client: Optional[_client.GarminConnectClient] = None) -> None:
        self.client = client or get_client()

    def _try(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None

    def fetch_range(self, start: str | date, end: str | date, include_extras: bool = True) -> Dict[str, pd.DataFrame]:
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

        for d in _daterange(s, e):
            ds = d.isoformat()

            # 1) Wrapper bundle (like your working script)
            blob = self._try(getattr(self.client, "wellness_summary_for_day"), ds)

            # Sleep (wrapper)
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

            # Steps (wrapper + fallbacks)
            steps_total = calories = distance_m = None
            if isinstance(blob, dict):
                st = blob.get("steps")
                if isinstance(st, dict):
                    steps_total = st.get("steps") or st.get("totalSteps") or st.get("value")
                    calories = st.get("calories") or st.get("activeKilocalories")
                    # distance can be 'distanceInMeters', 'distance', or 'totalDistance'
                    distance_m = st.get("distanceInMeters") or st.get("distance") or st.get("totalDistance")
                elif isinstance(st, list):
                    tot = cal = dist = 0.0
                    for it in st:
                        if not isinstance(it, dict):
                            continue
                        tot += _num(it.get("steps") or it.get("value") or 0) or 0
                        cal += _num(it.get("calories") or it.get("activeKilocalories") or 0) or 0
                        dist += (
                            _num(it.get("distanceInMeters") or it.get("distance") or it.get("totalDistance") or 0) or 0
                        )
                    steps_total = int(tot) if tot else None
                    calories = cal if cal else None
                    distance_m = dist if dist else None

            if steps_total is None:
                # fall back to raw API
                steps = self._try(getattr(api, "get_daily_steps"), ds, ds) or self._try(
                    getattr(api, "get_steps_data"), ds
                )
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

            # Stress (wrapper)
            avg_stress = max_stress = rest_sec = None
            if isinstance(blob, dict):
                ss = blob.get("stress")
                if isinstance(ss, dict):
                    avg_stress = (
                        ss.get("avgStressLevel") or ss.get("averageStressLevel") or ss.get("overallStressLevel")
                    )
                    max_stress = ss.get("maxStressLevel") or ss.get("max")
                    rest_sec = ss.get("restStressDuration") or ss.get("restStressSec")

            # Resting HR — raw API and robust parse (metricsMap)
            rhr_val = None
            rhr_payload = (
                self._try(getattr(api, "get_rhr_day"), ds)
                or self._try(getattr(api, "get_daily_hr"), ds)
                or self._try(getattr(api, "get_resting_heart_rate"), ds)
                or self._try(getattr(api, "get_rhr"), ds)
            )
            if isinstance(rhr_payload, dict):
                rhr_val = _extract_rhr(rhr_payload)
            # very last resort: sometimes sleep blob carries restingHeartRate
            if rhr_val is None and isinstance(blob, dict) and isinstance(blob.get("sleep"), dict):
                rhr_val = _extract_rhr(blob.get("sleep"))

            # HRV (prefer lastNightAvg)
            hrv_val = None
            if isinstance(blob, dict):
                hv = blob.get("hrv")
                if isinstance(hv, dict):
                    sm = hv.get("hrvSummary") or {}
                    hrv_val = sm.get("lastNightAvg") or sm.get("weeklyAvg") or hv.get("hrvValue") or hv.get("dailyAvg")
            if hrv_val is None:
                hv = self._try(getattr(api, "get_hrv_data"), ds)
                if isinstance(hv, dict):
                    sm = hv.get("hrvSummary") or {}
                    hrv_val = sm.get("lastNightAvg") or sm.get("weeklyAvg") or hv.get("hrvValue") or hv.get("dailyAvg")

            # Body Battery & Training Readiness (raw API)
            bb_avg = bb_charge = bb_drain = None
            bb = self._try(getattr(api, "get_body_battery"), ds, ds) or self._try(
                getattr(api, "get_body_battery_data"), ds, ds
            )
            if isinstance(bb, list) and bb:
                b0 = bb[0]
                bb_charge = b0.get("charged")
                bb_drain = b0.get("drained")
                levels = []
                arr = b0.get("bodyBatteryValuesArray") or []
                for item in arr:
                    if isinstance(item, (list, tuple)):
                        # [timestamp, level] or [timestamp, state, level, ...]
                        if len(item) >= 3 and isinstance(item[2], (int, float)):
                            levels.append(item[2])
                        elif len(item) >= 2 and isinstance(item[1], (int, float)):
                            levels.append(item[1])
                if levels:
                    try:
                        import pandas as _pd

                        bb_avg = float(_pd.Series(levels).mean())
                    except Exception:
                        bb_avg = sum(levels) / len(levels)
            elif isinstance(bb, dict):
                bb_avg = bb.get("bodyBatteryAverage")
                bb_charge = bb.get("bodyBatteryCharge")
                bb_drain = bb.get("bodyBatteryDrain")

            tr_score = None
            trd = self._try(getattr(api, "get_training_readiness"), ds)
            if isinstance(trd, dict):
                tr_score = trd.get("trainingReadinessScore") or trd.get("score")

            # Collect rows
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
            rows_steps.append(
                {
                    "date": ds,
                    "steps": steps_total,
                    "calories": calories,
                    "distance_m": distance_m,
                }
            )
            rows_stress.append(
                {
                    "date": ds,
                    "stress_avg": avg_stress,
                    "stress_max": max_stress,
                    "rest_sec": rest_sec,
                }
            )
            rows_rhr.append({"date": ds, "resting_hr": rhr_val})
            rows_hrv.append({"date": ds, "hrv": hrv_val})
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
        }
        if include_extras:
            bbdf = _df(rows_bb, ["date", "avg", "charge", "drain"])
            if not bbdf.empty:
                result["body_battery"] = bbdf
            trdf = _df(rows_tr, ["date", "score"])
            if not trdf.empty:
                result["training_readiness"] = trdf
        return result
