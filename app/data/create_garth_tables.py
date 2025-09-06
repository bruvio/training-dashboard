"""
Database migration script to create garth wellness data tables.
Run this to add the new tables for sleep, stress, steps, and intensity data.
"""

import logging

from sqlalchemy import text

from app.data.db import engine
from app.data.garth_models import Base

logger = logging.getLogger(__name__)


def create_garth_tables():
    """Create all garth wellness data tables."""
    try:
        # Create all tables defined in garth_models
        logger.info("Creating garth wellness data tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Garth wellness tables created successfully")

        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'daily_%' OR name = 'garmin_sessions'
                ORDER BY name;
            """
                )
            )

            tables = [row[0] for row in result]
            logger.info(f"Created tables: {tables}")

        return True

    except Exception as e:
        logger.error(f"Failed to create garth tables: {e}")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create tables
    success = create_garth_tables()

    if success:
        print("✅ Garth wellness data tables created successfully!")
        print("Tables created:")
        print("  - daily_sleep")
        print("  - daily_stress")
        print("  - daily_steps")
        print("  - daily_intensity")
        print("  - garmin_sessions")
    else:
        print("❌ Failed to create garth tables")
        exit(1)
