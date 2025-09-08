#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import wellness_sync as ws


def _coerce_numeric(s: pd.Series) -> pd.Series:
    try:
        return pd.to_numeric(s, errors="coerce")
    except Exception:
        return s


def plot_wellness_data_range(
    start_date: str,
    end_date: str,
    aggregate: str = "none",
    save_dir: str = "./plots",
    show_plots: bool = True,
    plot_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Enhanced function to plot wellness data within a given date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        aggregate: Aggregation method ("none", "day", "week", "month", "year")
        save_dir: Directory to save plots
        show_plots: Whether to display plots
        plot_types: Specific types of data to plot (None for all)

    Returns:
        Dictionary with plot information and statistics
    """
    # Initialize client and sync
    client = ws.get_client()
    sync = ws.WellnessSync(client)

    # Fetch wellness data
    data = sync.fetch_range(start_date, end_date, include_extras=True)

    # Filter plot types if specified
    if plot_types:
        data = {k: v for k, v in data.items() if k in plot_types}

    # Setup plotting
    plt.style.use("seaborn-v0_8" if hasattr(plt.style, "seaborn-v0_8") else "default")
    outdir = Path(save_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    plot_results = {
        "plots_created": [],
        "data_summary": {},
        "date_range": f"{start_date} to {end_date}",
        "aggregation": aggregate,
    }

    # Process each data type
    for key, df in data.items():
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue

        # Apply aggregation
        df_processed = ws.aggregate_df(df, aggregate) if aggregate != "none" else df

        # Store data summary
        nonnull_counts = {c: int(df_processed[c].notna().sum()) for c in df_processed.columns if c != "date"}
        plot_results["data_summary"][key] = {"total_rows": len(df_processed), "non_null_counts": nonnull_counts}

        # Create enhanced plots
        plots_created = _create_enhanced_plots(df_processed, key, outdir, show_plots)
        plot_results["plots_created"].extend(plots_created)

    return plot_results


def _create_enhanced_plots(df: pd.DataFrame, data_type: str, outdir: Path, show_plots: bool = True) -> List[str]:
    """Create enhanced plots for a specific wellness data type."""
    plots_created = []

    # Define plot configurations for each data type
    plot_configs = {
        "sleep": {
            "metrics": ["sleep_min", "efficiency", "quality", "deep_sec", "light_sec", "rem_sec", "awake_sec"],
            "colors": ["#4A90E2", "#50C878", "#FFD700", "#2E4BC6", "#87CEEB", "#DDA0DD", "#FF6B6B"],
            "layout": (3, 3),
        },
        "steps": {
            "metrics": ["steps", "calories", "distance_m"],
            "colors": ["#FF6B35", "#F7931E", "#C41E3A"],
            "layout": (2, 2),
        },
        "stress": {
            "metrics": ["stress_avg", "stress_max", "rest_sec"],
            "colors": ["#FF4444", "#CC0000", "#50C878"],
            "layout": (2, 2),
        },
        "resting_hr": {"metrics": ["resting_hr"], "colors": ["#E74C3C"], "layout": (1, 1)},
        "hrv": {"metrics": ["hrv"], "colors": ["#9B59B6"], "layout": (1, 1)},
        "vo2max": {"metrics": ["vo2max"], "colors": ["#27AE60"], "layout": (1, 1)},
        "body_battery": {
            "metrics": ["avg", "charge", "drain"],
            "colors": ["#F39C12", "#27AE60", "#E74C3C"],
            "layout": (2, 2),
        },
        "training_readiness": {"metrics": ["score"], "colors": ["#3498DB"], "layout": (1, 1)},
    }

    if data_type not in plot_configs:
        return plots_created

    config = plot_configs[data_type]
    available_metrics = [m for m in config["metrics"] if m in df.columns and df[m].notna().any()]

    if not available_metrics:
        return plots_created

    # Prepare date column
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Create subplot layout
    rows, cols = config["layout"]
    fig, axes = plt.subplots(rows, cols, figsize=(15, 4 * rows))
    if rows * cols == 1:
        axes = [axes]
    elif rows == 1:
        axes = axes
    else:
        axes = axes.flatten()

    # Create individual metric plots
    for i, metric in enumerate(available_metrics):
        if i >= len(axes):
            break

        ax = axes[i]
        data_clean = df.dropna(subset=[metric])

        if data_clean.empty:
            ax.text(0.5, 0.5, f"No data for {metric}", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(f'{metric.replace("_", " ").title()}')
            continue

        # Plot with enhanced styling
        color = config["colors"][i % len(config["colors"])]
        ax.plot(data_clean["date"], data_clean[metric], color=color, linewidth=2, marker="o", markersize=3)
        ax.set_title(f'{metric.replace("_", " ").title()}', fontsize=12, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=45)

        # Add trend line if enough data points
        if len(data_clean) > 3:
            z = np.polyfit(range(len(data_clean)), data_clean[metric], 1)
            p = np.poly1d(z)
            ax.plot(data_clean["date"], p(range(len(data_clean))), "--", alpha=0.7, color="red", linewidth=1)

    # Hide unused subplots
    for i in range(len(available_metrics), len(axes)):
        axes[i].set_visible(False)

    # Adjust layout and save
    plt.suptitle(f'{data_type.replace("_", " ").title()} Metrics', fontsize=16, fontweight="bold")
    plt.tight_layout()

    # Save plot
    plot_filename = f"{data_type}_enhanced.png"
    plot_path = outdir / plot_filename
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plots_created.append(str(plot_path))

    if show_plots:
        plt.show()
    else:
        plt.close()

    return plots_created


def _plot_df(df: pd.DataFrame, ycols: List[str], title: str, outdir: Path):
    if df.empty:
        print(f"[plot] {title}: empty DataFrame, skipping")
        return
    x = pd.to_datetime(df["date"]) if "date" in df.columns else pd.to_datetime(df.index)
    any_saved = False
    for y in ycols:
        if y not in df.columns:
            continue
        ys = _coerce_numeric(df[y]).dropna()
        if ys.empty:
            print(f"[plot] {title}: '{y}' has no numeric/non-null data, skipping")
            continue
        plt.figure()
        plt.plot(x.loc[ys.index], ys)
        plt.title(f"{title}: {y}")
        plt.xlabel("Date")
        plt.ylabel(y)
        outdir.mkdir(parents=True, exist_ok=True)
        out_path = outdir / f"{title.replace(' ','_').lower()}-{y}.png"
        plt.savefig(out_path, bbox_inches="tight")
        plt.close()
        any_saved = True
        print(f"[plot] saved {out_path}")
    if not any_saved:
        print(f"[plot] {title}: no plottable series")


def main():
    p = argparse.ArgumentParser(description="Plot Garmin wellness data with enhanced visualizations")
    p.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    p.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    p.add_argument(
        "--aggregate",
        "--agg",
        dest="aggregate",
        default="none",
        choices=["none", "day", "week", "month", "year"],
        help="Data aggregation method",
    )
    p.add_argument("--save-dir", "--out", dest="save_dir", default="./plots", help="Directory to save plots")
    p.add_argument("--enhanced", action="store_true", help="Use enhanced plotting with subplots and trend lines")
    p.add_argument(
        "--plot-types",
        nargs="*",
        choices=["sleep", "steps", "stress", "resting_hr", "hrv", "vo2max", "body_battery", "training_readiness"],
        help="Specific data types to plot (default: all available)",
    )
    p.add_argument("--show", action="store_true", help="Display plots in addition to saving")
    args = p.parse_args()

    try:
        if args.enhanced:
            # Use enhanced plotting function
            results = plot_wellness_data_range(
                start_date=args.start,
                end_date=args.end,
                aggregate=args.aggregate,
                save_dir=args.save_dir,
                show_plots=args.show,
                plot_types=args.plot_types,
            )

            print(f"📊 Enhanced Wellness Data Plotting Complete")
            print(f"📅 Date Range: {results['date_range']}")
            print(f"📈 Aggregation: {results['aggregation']}")
            print(f"📁 Plots saved to: {Path(args.save_dir).resolve()}")
            print(f"🖼️ Total plots created: {len(results['plots_created'])}")

            # Print data summary
            print("\n📋 Data Summary:")
            for data_type, summary in results["data_summary"].items():
                print(f"  {data_type}: {summary['total_rows']} rows")
                for metric, count in summary["non_null_counts"].items():
                    if count > 0:
                        print(f"    - {metric}: {count} values")

        else:
            # Use original plotting method
            client = ws.get_client()
            sync = ws.WellnessSync(client)
            data = sync.fetch_range(args.start, args.end, include_extras=True)

            # Filter plot types if specified
            if args.plot_types:
                data = {k: v for k, v in data.items() if k in args.plot_types}

            for k, df in data.items():
                if isinstance(df, pd.DataFrame):
                    nonnull = {c: int(df[c].notna().sum()) for c in df.columns if c != "date"}
                    print(f"{k}: {len(df)} rows; non-null counts: {nonnull}")

            outdir = Path(args.save_dir) if args.save_dir else Path("./plots")
            for key, df in data.items():
                if not isinstance(df, pd.DataFrame) or df.empty:
                    continue
                df2 = ws.aggregate_df(df, args.aggregate) if args.aggregate != "none" else df
                if key == "sleep":
                    y = [
                        c
                        for c in (
                            "total_sleep_seconds",
                            "sleep_min",
                            "efficiency",
                            "quality",
                            "deep_sec",
                            "light_sec",
                            "rem_sec",
                            "awake_sec",
                        )
                        if c in df2.columns
                    ]
                elif key == "steps":
                    y = [c for c in ("steps", "calories", "distance_m") if c in df2.columns]
                elif key == "stress":
                    y = [c for c in ("stress_avg", "stress_max", "rest_sec") if c in df2.columns]
                elif key == "resting_hr":
                    y = ["resting_hr"] if "resting_hr" in df2.columns else []
                elif key == "hrv":
                    y = [c for c in ("hrv", "rmssd", "sdnn") if c in df2.columns]
                elif key == "vo2max":
                    y = ["vo2max"] if "vo2max" in df2.columns else []
                elif key == "body_battery":
                    y = [c for c in ("avg", "charge", "drain", "min", "max") if c in df2.columns]
                elif key == "training_readiness":
                    y = ["score"] if "score" in df2.columns else []
                else:
                    y = list(df2.select_dtypes("number").columns)
                _plot_df(df2, y, key.replace("_", " ").title(), outdir)

            print(f"Saved plots to: {outdir.resolve()}")

    except Exception as e:
        print(f"❌ Error creating plots: {e}")
        return 1

    return 0


if __name__ == "__main__":
    main()
