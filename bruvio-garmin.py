#!/usr/bin/env python3
"""
Garmin Connect data collector and visualizer.

Features
- Auth via tokenstore and (fallback) username/password + MFA
- Daily summary for a given date: sleep, stress, steps, RHR, body battery, HRV, VO₂max, training readiness
- Interval summary for a date range (inclusive)
- Personal Records translator: converts PR records into human-readable text with unit inference and a partial, extensible type mapping
- Visualization: Seaborn plots for daily or weekly summaries (multiple metrics)

Usage
  export EMAIL=you@example.com
  export PASSWORD=yourPassword   # optional when tokens exist

  pip install garminconnect garth requests seaborn matplotlib pandas

  # Daily
  python garmin_tools.py daily --date 2025-09-04

  # Interval
  python garmin_tools.py interval --start 2025-08-28 --end 2025-09-04 --plot weekly

  # Personal records
  python garmin_tools.py prs
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from garth.exc import GarthHTTPError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("garmin_tools")

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TOKENSTORE = os.getenv("GARMINTOKENS") or "~/.garminconnect"
TOKENSTORE_B64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"


def _get_mfa() -> str:
    return input("MFA one-time code: ")


def init_api(email: Optional[str] = EMAIL, password: Optional[str] = PASSWORD) -> Optional[Garmin]:
    token_dir = os.path.expanduser(TOKENSTORE)
    try:
        garmin = Garmin()
        garmin.login(TOKENSTORE)
        return garmin
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        log.info("Token login failed, trying credentials.")
        try:
            if not email or not password:
                email = input("Login e-mail: ")
                from getpass import getpass

                password = getpass("Enter password: ")

            garmin = Garmin(email=email, password=password, is_cn=False, return_on_mfa=True)
            result1, result2 = garmin.login()
            if result1 == "needs_mfa":
                mfa_code = _get_mfa()
                garmin.resume_login(result2, mfa_code)

            garmin.garth.dump(TOKENSTORE)
            token_base64 = garmin.garth.dumps()
            with open(os.path.expanduser(TOKENSTORE_B64), "w") as fh:
                fh.write(token_base64)

            garmin.login(TOKENSTORE)
            return garmin
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            log.error("Login failed: %s", err)
            return None


@dataclass
class DailySummary:
    date: str
    sleep: Any | None
    stress: Any | None
    steps: Any | None
    resting_hr: Any | None
    body_battery: Any | None
    hrv: Any | None
    vo2max: Any | None
    training_readiness: Any | None

    @staticmethod
    def save_to_file(dailies: "DailySummary | list[DailySummary]", filepath: str) -> None:
        """Save one or more DailySummary objects to a JSON file."""
        if isinstance(dailies, DailySummary):
            data = [asdict(dailies)]
        else:
            data = [asdict(d) for d in dailies]
        Path(filepath).write_text(json.dumps(data, indent=2), encoding="utf-8")
        log.info("Saved %d daily summaries to %s", len(data), filepath)


def fetch_daily(api: Garmin, date: dt.date) -> DailySummary:
    d = date.isoformat()

    def try_call(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            log.debug("%s failed: %s", getattr(fn, "__name__", fn), e)
            return None

    return DailySummary(
        date=d,
        sleep=try_call(api.get_sleep_data, d),
        stress=try_call(api.get_stress_data, d),
        steps=try_call(api.get_daily_steps, d, d),
        resting_hr=try_call(api.get_rhr_day, d),
        body_battery=try_call(api.get_body_battery, d, d),
        hrv=try_call(api.get_hrv_data, d),
        vo2max=try_call(api.get_max_metrics, d),
        training_readiness=try_call(api.get_training_readiness, d),
    )


def fetch_interval(api: Garmin, start: dt.date, end: dt.date) -> List[DailySummary]:
    per_day: List[DailySummary] = []
    cur = start
    while cur <= end:
        per_day.append(fetch_daily(api, cur))
        cur += dt.timedelta(days=1)
    return per_day


# ------------------------------- Visualization -------------------------------

# (unchanged plotting functions ...)


def _flatten_daily_row(d: DailySummary) -> Dict[str, Any]:
    """Turn a DailySummary with nested dicts into flat scalar columns.
    Handles the shapes returned by garminconnect for 2024/2025 (lists for
    steps/body_battery/vo2max/training_readiness and nested dicts for HRV/sleep/RHR).
    Missing fields become None.
    """
    row = asdict(d)
    out: Dict[str, Any] = {"date": pd.to_datetime(row.get("date"))}

    # ---------------- Steps ----------------
    steps_obj = row.get("steps")
    steps_total = None
    if isinstance(steps_obj, list) and steps_obj:
        # New shape
        steps_total = steps_obj[0].get("totalSteps") or steps_obj[0].get("steps")
    elif isinstance(steps_obj, dict):
        steps_total = steps_obj.get("totalSteps") or steps_obj.get("steps")
    out["steps_total"] = steps_total

    # ---------------- Resting HR ----------------
    rhr = row.get("resting_hr")
    rhr_val = None
    if isinstance(rhr, dict):
        # Newer API nests under allMetrics.metricsMap.WELLNESS_RESTING_HEART_RATE[0].value
        try:
            rhr_val = (
                rhr.get("allMetrics", {}).get("metricsMap", {}).get("WELLNESS_RESTING_HEART_RATE", [{}])[0].get("value")
            )
        except Exception:
            rhr_val = None
        if rhr_val is None:
            rhr_val = rhr.get("value")
    out["resting_hr"] = rhr_val

    # ---------------- VO2max ----------------
    vo2 = row.get("vo2max")
    vo2_val = None
    if isinstance(vo2, list) and vo2:
        g = vo2[0].get("generic") or {}
        vo2_val = g.get("vo2MaxPreciseValue") or g.get("vo2MaxValue")
    elif isinstance(vo2, dict):
        vo2_val = vo2.get("vo2MaxPreciseValue") or vo2.get("vo2MaxValue")
    out["vo2max"] = vo2_val

    # ---------------- Training readiness ----------------
    tr = row.get("training_readiness")
    tr_score = None
    if isinstance(tr, list) and tr:
        # take the latest timestamp entry
        try:
            latest = max(tr, key=lambda x: x.get("timestamp", ""))
        except Exception:
            latest = tr[-1]
        tr_score = latest.get("score")
    elif isinstance(tr, dict):
        tr_score = tr.get("overallScore") or tr.get("score")
    out["training_readiness"] = tr_score

    # ---------------- Body Battery ----------------
    bb = row.get("body_battery")
    bb_avg = bb_charge = bb_drain = None
    if isinstance(bb, list) and bb:
        b = bb[0]
        bb_charge = b.get("charged")
        bb_drain = b.get("drained")
        # compute average level if we have values array
        levels = []
        arr = b.get("bodyBatteryValuesArray") or []
        for item in arr:
            # shape can be [ts, level] or [ts, status, level, version]
            if isinstance(item, (list, tuple)):
                if len(item) >= 3 and isinstance(item[2], (int, float)):
                    levels.append(item[2])
                elif len(item) >= 2 and isinstance(item[1], (int, float)):
                    levels.append(item[1])
        if levels:
            bb_avg = float(pd.Series(levels).mean())
    elif isinstance(bb, dict):
        bb_avg = bb.get("bodyBatteryAverage")
        bb_charge = bb.get("bodyBatteryCharge")
        bb_drain = bb.get("bodyBatteryDrain")
    out["body_battery_avg"] = bb_avg
    out["body_battery_charge"] = bb_charge
    out["body_battery_drain"] = bb_drain

    # ---------------- HRV ----------------
    hrv = row.get("hrv")
    hrv_val = None
    if isinstance(hrv, dict):
        # Prefer lastNightAvg, then weeklyAvg
        summary = hrv.get("hrvSummary") or {}
        hrv_val = summary.get("lastNightAvg") or summary.get("weeklyAvg")
        if hrv_val is None:
            hrv_val = hrv.get("hrvValue") or hrv.get("dailyAvg")
    out["hrv"] = hrv_val

    # ---------------- Sleep (minutes) ----------------
    sleep = row.get("sleep")
    sleep_min = None
    if isinstance(sleep, dict):
        dto = sleep.get("dailySleepDTO") or {}
        dur = dto.get("sleepTimeSeconds") or sleep.get("totalSleepSeconds") or sleep.get("durationInSeconds")
        if dur is not None:
            sleep_min = int(round(dur / 60))
    out["sleep_min"] = sleep_min

    # ---------------- Stress ----------------
    stress = row.get("stress")
    avg_stress = None
    if isinstance(stress, dict):
        # Try common fields
        avg_stress = (
            stress.get("avgStressLevel") or stress.get("averageStressLevel") or stress.get("overallStressLevel")
        )
        # Or compute mean from values array
        if avg_stress is None:
            arr = stress.get("stressLevelValuesArray") or []
            vals = []
            for item in arr:
                # shape can be [ts, level]
                if isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], (int, float)):
                    vals.append(item[1])
            if vals:
                avg_stress = float(pd.Series(vals).mean())
    out["stress"] = avg_stress

    return out


# (rest of visualization and CLI unchanged)


def _aggregate(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    df = df.set_index("date")
    if mode == "weekly":
        rule = "W"
    else:
        rule = "D"
    # Sum counters, mean continuous metrics
    agg = {
        "steps_total": "sum",
        "sleep_min": "sum",
        "resting_hr": "mean",
        "vo2max": "mean",
        "training_readiness": "mean",
        "body_battery_avg": "mean",
        "body_battery_charge": "mean",
        "body_battery_drain": "mean",
        "hrv": "mean",
        "stress": "mean",
    }
    out = df.resample(rule).agg(agg).reset_index()
    return out


def _line(ax, data: pd.DataFrame, x: str, y: str, title: str, ylabel: str):
    sns.lineplot(data=data, x=x, y=y, marker="o", ax=ax)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Date")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6))
    for label in ax.get_xticklabels():
        label.set_rotation(30)
        label.set_horizontalalignment("right")


def plot_data(dailies: List[DailySummary], mode: str = "daily", save: Optional[str] = None) -> None:
    flat = pd.DataFrame([_flatten_daily_row(d) for d in dailies]).sort_values("date")
    plot_df = _aggregate(flat, mode)

    sns.set_theme(style="whitegrid")

    # We'll create two figures to keep things readable
    fig1, axes1 = plt.subplots(2, 2, figsize=(14, 9))
    _line(axes1[0, 0], plot_df, "date", "steps_total", f"Steps ({mode})", "steps")
    _line(axes1[0, 1], plot_df, "date", "sleep_min", f"Sleep Duration ({mode})", "minutes")
    _line(axes1[1, 0], plot_df, "date", "resting_hr", f"Resting HR ({mode})", "bpm")
    _line(axes1[1, 1], plot_df, "date", "vo2max", f"VO2max ({mode})", "mL·kg^-1·min^-1")
    plt.tight_layout()

    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 9))
    _line(axes2[0, 0], plot_df, "date", "training_readiness", f"Training Readiness ({mode})", "score")
    _line(axes2[0, 1], plot_df, "date", "body_battery_avg", f"Body Battery Avg ({mode})", "score")
    _line(axes2[1, 0], plot_df, "date", "hrv", f"HRV ({mode})", "ms (avg)")
    _line(axes2[1, 1], plot_df, "date", "stress", f"Stress ({mode})", "level")
    plt.tight_layout()

    if save:
        out_dir = Path(save)
        out_dir.mkdir(parents=True, exist_ok=True)
        fig1.savefig(out_dir / f"metrics_1_{mode}.png", dpi=150, bbox_inches="tight")
        fig2.savefig(out_dir / f"metrics_2_{mode}.png", dpi=150, bbox_inches="tight")
    plt.show()


# ------------------------------- CLI -----------------------------------------


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="Garmin Connect summaries and visualization")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_daily = sub.add_parser("daily")
    p_daily.add_argument("--date", default=dt.date.today().isoformat())
    p_daily.add_argument("--plot", choices=["daily", "weekly"], default="daily")

    p_int = sub.add_parser("interval")
    p_int.add_argument("--start", required=True)
    p_int.add_argument("--end", required=True)
    p_int.add_argument("--plot", choices=["daily", "weekly"], default="daily")

    args = p.parse_args(argv)

    api = init_api()
    if not api:
        return 1

    if args.cmd == "daily":
        date = dt.date.fromisoformat(args.date)
        daily = fetch_daily(api, date)
        DailySummary.save_to_file(daily, "output.json")
        plot_data([daily], mode=args.plot)

    elif args.cmd == "interval":
        start = dt.date.fromisoformat(args.start)
        end = dt.date.fromisoformat(args.end)
        dailies = fetch_interval(api, start, end)
        plot_data(dailies, mode=args.plot)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# python bruvio-garmin.py daily --date 2025-09-04 --plot daily

# Interval (inclusive) and weekly view
# python bruvio-garmin.py interval --start 2025-08-28 --end 2025-09-04 --plot weekly
