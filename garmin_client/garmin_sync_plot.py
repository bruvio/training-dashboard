#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd
import matplotlib.pyplot as plt

import wellness_sync as ws

def _coerce_numeric(s: pd.Series) -> pd.Series:
    try: return pd.to_numeric(s, errors="coerce")
    except Exception: return s

def _plot_df(df: pd.DataFrame, ycols: List[str], title: str, outdir: Path):
    if df.empty: 
        print(f"[plot] {title}: empty DataFrame, skipping"); 
        return
    x = pd.to_datetime(df["date"]) if "date" in df.columns else pd.to_datetime(df.index)
    any_saved = False
    for y in ycols:
        if y not in df.columns: continue
        ys = _coerce_numeric(df[y]).dropna()
        if ys.empty:
            print(f"[plot] {title}: '{y}' has no numeric/non-null data, skipping")
            continue
        plt.figure()
        plt.plot(x.loc[ys.index], ys)
        plt.title(f"{title}: {y}")
        plt.xlabel("Date"); plt.ylabel(y)
        outdir.mkdir(parents=True, exist_ok=True)
        out_path = outdir / f"{title.replace(' ','_').lower()}-{y}.png"
        plt.savefig(out_path, bbox_inches="tight"); plt.close()
        any_saved = True
        print(f"[plot] saved {out_path}")
    if not any_saved: print(f"[plot] {title}: no plottable series")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True); p.add_argument("--end", required=True)
    p.add_argument("--aggregate","--agg", dest="aggregate", default="none",
                   choices=["none","day","week","month","year"])
    p.add_argument("--save-dir","--out", dest="save_dir", default="./plots")
    args = p.parse_args()

    client = ws.get_client()
    sync = ws.WellnessSync(client)
    data = sync.fetch_range(args.start, args.end, include_extras=True)

    for k, df in data.items():
        if isinstance(df, pd.DataFrame):
            nonnull = {c: int(df[c].notna().sum()) for c in df.columns if c != "date"}
            print(f"{k}: {len(df)} rows; non-null counts: {nonnull}")

    outdir = Path(args.save_dir) if args.save_dir else Path("./plots")
    for key, df in data.items():
        if not isinstance(df, pd.DataFrame) or df.empty: continue
        df2 = ws.aggregate_df(df, args.aggregate) if args.aggregate != "none" else df
        if key == "sleep":
            y = [c for c in ("total_sleep_seconds","sleep_min","efficiency","quality","deep_sec","light_sec","rem_sec","awake_sec") if c in df2.columns]
        elif key == "steps":
            y = [c for c in ("steps","calories","distance_m") if c in df2.columns]
        elif key == "stress":
            y = [c for c in ("stress_avg","stress_max","rest_sec") if c in df2.columns]
        elif key == "resting_hr":
            y = ["resting_hr"] if "resting_hr" in df2.columns else []
        elif key == "hrv":
            y = [c for c in ("hrv","rmssd","sdnn") if c in df2.columns]
        elif key == "vo2max":
            y = ["vo2max"] if "vo2max" in df2.columns else []
        elif key == "body_battery":
            y = [c for c in ("avg","charge","drain","min","max") if c in df2.columns]
        elif key == "training_readiness":
            y = ["score"] if "score" in df2.columns else []
        else:
            y = list(df2.select_dtypes("number").columns)
        _plot_df(df2, y, key.replace("_"," ").title(), outdir)

    print(f"Saved plots to: {outdir.resolve()}")

if __name__ == "__main__":
    main()
