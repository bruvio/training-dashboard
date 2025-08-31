# flake8: noqa 
"""
Database configuration and session management for Garmin Dashboard.

Provides SQLAlchemy engine setup, session management, and database utilities
with proper connection handling and performance optimization.
"""

from contextlib import contextmanager
import logging
import os
from typing import TYPE_CHECKING, Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
else:
    # For SQLAlchemy 1.4 compatibility
    try:
        from sqlalchemy.engine import Engine
    except ImportError:
        from sqlalchemy import engine

        Engine = engine.Engine

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration and connection management."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database configuration.

        Args:
            database_url: SQLAlchemy database URL. Defaults to SQLite file.
        """
        # Use provided URL, then environment variable, then default
        self.database_url = database_url or os.getenv("DATABASE_URL") or "sqlite:///garmin_dashboard.db"

        logger.info(f"Database URL: {self.database_url}")
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None

    @property
    def engine(self):
        """Get or create SQLAlchemy engine with optimized settings."""
        if self._engine is None:
            connect_args = {}

            # SQLite-specific optimizations
            if self.database_url.startswith("sqlite"):
                connect_args = {
                    "check_same_thread": False,  # Allow multi-threading
                }
                # Enable Write-Ahead Logging for better concurrency
                pool_class = StaticPool
            else:
                pool_class = None

            self._engine = create_engine(
                self.database_url,
                connect_args=connect_args,
                poolclass=pool_class,
                echo=False,  # Set to True for SQL debugging
                future=True,  # Use SQLAlchemy 2.0 style
            )

            # Set SQLite-specific pragmas for performance
            if self.database_url.startswith("sqlite"):
                with self._engine.connect() as conn:
                    conn.execute(text("PRAGMA journal_mode=WAL"))
                    conn.execute(text("PRAGMA synchronous=NORMAL"))
                    conn.execute(text("PRAGMA cache_size=10000"))
                    conn.execute(text("PRAGMA temp_store=MEMORY"))
                    conn.commit()

        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get session factory for creating database sessions."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine, expire_on_commit=False, autoflush=True, autocommit=False, future=True
            )
        return self._session_factory

    @property
    def scoped_session_factory(self) -> scoped_session:
        """Get scoped session factory for web applications."""
        if self._scoped_session is None:
            self._scoped_session = scoped_session(self.session_factory)
        return self._scoped_session

    def create_all_tables(self):
        """Create all database tables and indexes."""
        logger.info("Creating database tables...")
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created successfully.")

    def drop_all_tables(self):
        """Drop all database tables (use with caution!)."""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(self.engine)
        logger.info("All tables dropped.")

    def get_session(self) -> Session:
        """Create a new database session."""
        return self.session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope for database operations.

        Usage:
            with db_config.session_scope() as session:
                activity = Activity(...)
                session.add(activity)
                # Automatically commits on success, rollbacks on exception
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close_all_sessions(self):
        """Close all active sessions (useful for cleanup)."""
        if self._scoped_session:
            self._scoped_session.remove()

    def get_database_info(self) -> dict:
        """Get database information for debugging/monitoring."""
        with self.session_scope() as session:
            # Get table counts
            from .models import Activity, Lap, RoutePoint, Sample

            activity_count = session.query(Activity).count()
            sample_count = session.query(Sample).count()
            route_point_count = session.query(RoutePoint).count()
            lap_count = session.query(Lap).count()

            return {
                "database_url": self.database_url,
                "activities": activity_count,
                "samples": sample_count,
                "route_points": route_point_count,
                "laps": lap_count,
            }


# Global database instance
_db_config: Optional[DatabaseConfig] = None


def get_db_config() -> DatabaseConfig:
    """Get the global database configuration instance."""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def init_database(database_url: Optional[str] = None) -> DatabaseConfig:
    """
    Initialize the database with optional custom URL.

    Args:
        database_url: Custom database URL (optional)

    Returns:
        DatabaseConfig instance
    """
    global _db_config
    _db_config = DatabaseConfig(database_url)
    _db_config.create_all_tables()
    return _db_config


def get_session() -> Session:
    """Get a new database session using the global config."""
    return get_db_config().get_session()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Get a transactional session scope using the global config."""
    with get_db_config().session_scope() as session:
        yield session


def close_database():
    """Close database connections and clean up."""
    global _db_config
    if _db_config:
        _db_config.close_all_sessions()
        _db_config = None
