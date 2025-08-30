#!/usr/bin/env python3
"""
Launch script for the simplified Garmin Connect Desktop Application.

This script ensures proper setup and launches the simplified version
that works better on macOS.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Launch the desktop application."""
    try:
        # Import and run the simplified app
        from desktop_ui.main_window_simple import main as run_app

        print("🚀 Starting Garmin Connect Desktop Dashboard...")
        print("📍 Project root:", project_root)

        # Run the application
        run_app()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Try installing dependencies:")
        print("   pip install -r requirements.txt")
        print("\nOr with virtual environment:")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("   pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
