#!/usr/bin/env python3
"""Test script to verify metric selection functionality."""

import sys

sys.path.insert(0, "/app")

from app.data.db import session_scope
from app.data.models import Sample


import os
import pytest


def is_ci_environment():
    """Check if running in CI environment."""
    return os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'


@pytest.mark.skipif(is_ci_environment(), reason="Database not available in CI environment")
def test_activity_metrics():
    """Test which activities have metrics available."""

    with session_scope() as session:
        # Check metrics for activities 1, 3, and 4
        for activity_id in [1, 3, 4]:
            print(f"\n=== Activity {activity_id} ===")
            samples = session.query(Sample).filter_by(activity_id=activity_id).limit(10).all()

            if not samples:
                print("No samples found")
                continue

            print(f"Found {len(samples)} samples")

            # Check which metrics have data in the first few samples
            sample = samples[0]
            available_metrics = []

            metrics_to_check = [
                "heart_rate",
                "power_w",
                "cadence_rpm",
                "speed_mps",
                "altitude_m",
                "temperature_c",
                "vertical_oscillation_mm",
                "ground_contact_time_ms",
            ]

            for metric in metrics_to_check:
                value = getattr(sample, metric)
                if value is not None:
                    available_metrics.append(f"{metric}: {value}")

            print(f"Available metrics: {available_metrics}")

            # Check if we have any pace calculation (from speed)
            if sample.speed_mps and sample.speed_mps > 0:
                pace_per_km = (1000 / sample.speed_mps) / 60
                print(f"Calculated pace: {pace_per_km:.2f} min/km")


if __name__ == "__main__":
    test_activity_metrics()
