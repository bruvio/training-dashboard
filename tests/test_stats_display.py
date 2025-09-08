#!/usr/bin/env python3
"""
Test stats page display by manually calling callback functions.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dash import Dash
import dash_bootstrap_components as dbc

from app.data.web_queries import get_sleep_data, get_steps_data, get_stress_data
from app.pages.stats import register_callbacks


def test_direct_callback_call():
    """Test calling the callback functions directly."""
    print("🧪 Testing stats page callback functions directly...")

    # Create a mock app
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Register callbacks
    register_callbacks(app)

    # Test the data queries that the callbacks use
    print("\n📊 Testing data queries...")

    try:
        # Test sleep data query (same as callback)
        sleep_df = get_sleep_data(days=90)
        print(f"✅ Sleep data query: {len(sleep_df)} rows")
        if not sleep_df.empty:
            print("   Sample data:", sleep_df.head(1).to_dict("records"))

        # Test steps data query
        steps_df = get_steps_data(days=90)
        print(f"✅ Steps data query: {len(steps_df)} rows")
        if not steps_df.empty:
            print("   Sample data:", steps_df.head(1).to_dict("records"))

        # Test stress data query
        stress_df = get_stress_data(days=90)
        print(f"✅ Stress data query: {len(stress_df)} rows")
        if not stress_df.empty:
            print("   Sample data:", stress_df.head(1).to_dict("records"))

        print(f"\n📈 Results:")
        print(f"   Sleep records: {len(sleep_df)}")
        print(f"   Steps records: {len(steps_df)}")
        print(f"   Stress records: {len(stress_df)}")

        if len(sleep_df) > 0 or len(steps_df) > 0 or len(stress_df) > 0:
            print("✅ Data is available - callbacks should show charts")
            print("💡 If stats page is empty, the issue is likely callback registration or triggering")
        else:
            print("❌ No data found - this explains why stats page is empty")

    except Exception as e:
        print(f"❌ Error testing data queries: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_direct_callback_call()
