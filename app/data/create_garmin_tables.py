"""
Database migration script for comprehensive Garmin wellness data tables.

Creates all tables required for garminconnect library integration as specified in PRP.
This script extends the existing database with comprehensive wellness tracking.
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .db import get_database_url
from .models import Base
from .garmin_models import (
    UserProfile,
    DailySleep,
    DailyStress,
    DailySteps,
    DailyIntensityMinutes,
    DailyBodyBattery,
    BloodPressureReadings,
    DailyHydration,
    DailyRespiration,
    DailySpo2,
    DailyTrainingReadiness,
    TrainingStatus,
    MaxMetrics,
    PersonalRecords,
    DailyHeartRate,
    GarminSession,
)

logger = logging.getLogger(__name__)


def create_garmin_tables(drop_existing: bool = False):
    """
    Create all Garmin wellness data tables.

    Args:
        drop_existing: If True, drops existing tables before creating new ones
    """
    try:
        # Get database connection
        engine = create_engine(get_database_url())

        # List of all Garmin model tables to create
        garmin_tables = [
            UserProfile,
            DailySleep,
            DailyStress,
            DailySteps,
            DailyIntensityMinutes,
            DailyBodyBattery,
            BloodPressureReadings,
            DailyHydration,
            DailyRespiration,
            DailySpo2,
            DailyTrainingReadiness,
            TrainingStatus,
            MaxMetrics,
            PersonalRecords,
            DailyHeartRate,
            GarminSession,
        ]

        logger.info("Creating Garmin wellness data tables...")

        if drop_existing:
            logger.warning("Dropping existing Garmin tables...")
            with engine.begin() as conn:
                for table_class in reversed(garmin_tables):  # Reverse order for dependencies
                    table_name = table_class.__tablename__
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                        logger.info(f"Dropped table: {table_name}")
                    except Exception as e:
                        logger.warning(f"Could not drop table {table_name}: {e}")

        # Create all tables
        with engine.begin() as conn:
            Base.metadata.create_all(conn, tables=[t.__table__ for t in garmin_tables])

        logger.info("Successfully created all Garmin wellness data tables:")
        for table_class in garmin_tables:
            logger.info(f"  ✅ {table_class.__tablename__}")

        # Verify tables were created
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            with engine.begin() as conn:
                # Check if all tables exist
                for table_class in garmin_tables:
                    table_name = table_class.__tablename__
                    result = conn.execute(
                        text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    )
                    if result.fetchone() is None:
                        raise Exception(f"Table {table_name} was not created successfully")

            logger.info("✅ All Garmin wellness tables verified successfully")
            return True

        except Exception as e:
            logger.error(f"Table verification failed: {e}")
            return False
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to create Garmin tables: {e}")
        return False


def list_garmin_tables():
    """List all Garmin-related tables in the database."""
    try:
        engine = create_engine(get_database_url())

        garmin_table_names = [
            "user_profile",
            "daily_sleep",
            "daily_stress",
            "daily_steps",
            "daily_intensity",
            "daily_body_battery",
            "blood_pressure_readings",
            "daily_hydration",
            "daily_respiration",
            "daily_spo2",
            "daily_training_readiness",
            "training_status",
            "max_metrics",
            "personal_records",
            "daily_heart_rate",
            "garmin_sessions",
        ]

        with engine.begin() as conn:
            existing_tables = []
            for table_name in garmin_table_names:
                result = conn.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                if result.fetchone() is not None:
                    existing_tables.append(table_name)

            logger.info(f"Existing Garmin tables: {existing_tables}")
            return existing_tables

    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        return []


def get_table_info(table_name: str):
    """Get detailed information about a specific table."""
    try:
        engine = create_engine(get_database_url())

        with engine.begin() as conn:
            # Check if table exists
            result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
            if result.fetchone() is None:
                logger.warning(f"Table {table_name} does not exist")
                return None

            # Get table schema
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = result.fetchall()

            # Get index information
            result = conn.execute(text(f"PRAGMA index_list({table_name})"))
            indexes = result.fetchall()

            # Get row count
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = result.fetchone()[0]

            info = {
                "table_name": table_name,
                "columns": [
                    {"name": col[1], "type": col[2], "nullable": not col[3], "primary_key": bool(col[5])}
                    for col in columns
                ],
                "indexes": [{"name": idx[1], "unique": bool(idx[2])} for idx in indexes],
                "row_count": row_count,
            }

            logger.info(
                f"Table {table_name}: {len(info['columns'])} columns, {len(info['indexes'])} indexes, {row_count} rows"
            )
            return info

    except Exception as e:
        logger.error(f"Failed to get info for table {table_name}: {e}")
        return None


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Create tables
    success = create_garmin_tables()

    if success:
        print("✅ Garmin wellness data tables created successfully!")

        # List existing tables
        tables = list_garmin_tables()
        print(f"Created {len(tables)} Garmin tables:")
        for table in tables:
            print(f"  - {table}")

        # Show sample table info
        if tables:
            sample_table = tables[0]
            info = get_table_info(sample_table)
            if info:
                print(f"\nSample table info ({sample_table}):")
                print(f"  Columns: {len(info['columns'])}")
                print(f"  Indexes: {len(info['indexes'])}")
                print(f"  Rows: {info['row_count']}")
    else:
        print("❌ Failed to create Garmin wellness data tables")
        exit(1)
