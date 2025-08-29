# Working Python Implementation Examples

## Overview

This document provides practical, working code examples for implementing Garmin Connect integration using various approaches. All examples include error handling, authentication management, and best practices for production use.

## Quick Start Examples

### Basic Authentication and Data Retrieval

#### Using python-garminconnect Library
```python
#!/usr/bin/env python3
"""
Basic Garmin Connect integration example
Demonstrates authentication, data retrieval, and error handling
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from garminconnect import (
    GarminConnect,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

class GarminConnectClient:
    def __init__(self, email=None, password=None):
        self.email = email or os.getenv('GARMIN_EMAIL')
        self.password = password or os.getenv('GARMIN_PASSWORD')
        self.api = GarminConnect()
        self.token_store = Path.home() / '.garmin_tokens'
        
        if not self.email or not self.password:
            raise ValueError("Email and password required (set GARMIN_EMAIL and GARMIN_PASSWORD env vars)")
    
    def authenticate(self):
        """Authenticate with Garmin Connect, handling MFA and errors"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"Authentication attempt {attempt + 1}/{max_retries}")
                self.api.login(self.email, self.password)
                print("✓ Authentication successful")
                return True
                
            except GarminConnectAuthenticationError as e:
                if "MFA" in str(e).upper():
                    print("Multi-factor authentication required")
                    mfa_code = input("Enter MFA code from your authenticator app: ")
                    try:
                        self.api.login(self.email, self.password, mfa_code)
                        print("✓ MFA authentication successful")
                        return True
                    except Exception as mfa_error:
                        print(f"✗ MFA authentication failed: {mfa_error}")
                        
                print(f"✗ Authentication failed: {e}")
                if attempt == max_retries - 1:
                    raise
                    
            except GarminConnectTooManyRequestsError:
                wait_time = (2 ** attempt) * 60  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"✗ Unexpected error: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(5)
        
        return False
    
    def get_user_profile(self):
        """Get user profile information"""
        try:
            profile = self.api.get_full_name()
            settings = self.api.get_unit_system()
            return {
                'name': profile,
                'units': settings,
                'retrieved_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Failed to get user profile: {e}")
            return None
    
    def get_recent_activities(self, limit=10):
        """Get recent activities with basic information"""
        try:
            activities = self.api.get_activities(0, limit)
            
            # Process and clean activity data
            processed_activities = []
            for activity in activities:
                processed_activity = {
                    'activity_id': activity.get('activityId'),
                    'name': activity.get('activityName'),
                    'type': activity.get('activityType', {}).get('typeKey'),
                    'start_time': activity.get('startTimeLocal'),
                    'duration': activity.get('duration'),
                    'distance': activity.get('distance'),
                    'calories': activity.get('calories'),
                    'avg_heart_rate': activity.get('averageHR'),
                    'max_heart_rate': activity.get('maxHR')
                }
                processed_activities.append(processed_activity)
            
            return processed_activities
            
        except Exception as e:
            print(f"Failed to get activities: {e}")
            return []
    
    def get_health_snapshot(self, date=None):
        """Get health metrics for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        health_data = {}
        
        try:
            # Steps data
            steps = self.api.get_steps_data(date)
            health_data['steps'] = steps
        except Exception as e:
            print(f"Failed to get steps data: {e}")
        
        try:
            # Heart rate data
            hr_data = self.api.get_heart_rates(date)
            health_data['heart_rate'] = hr_data
        except Exception as e:
            print(f"Failed to get heart rate data: {e}")
        
        try:
            # Sleep data
            sleep_data = self.api.get_sleep_data(date)
            health_data['sleep'] = sleep_data
        except Exception as e:
            print(f"Failed to get sleep data: {e}")
        
        try:
            # Body Battery data
            body_battery = self.api.get_body_battery(date)
            health_data['body_battery'] = body_battery
        except Exception as e:
            print(f"Failed to get body battery data: {e}")
        
        return health_data
    
    def download_activity(self, activity_id, format_type='gpx'):
        """Download activity file in specified format"""
        format_map = {
            'fit': GarminConnect.ActivityDownloadFormat.ORIGINAL,
            'gpx': GarminConnect.ActivityDownloadFormat.GPX,
            'tcx': GarminConnect.ActivityDownloadFormat.TCX,
            'csv': GarminConnect.ActivityDownloadFormat.CSV
        }
        
        if format_type not in format_map:
            raise ValueError(f"Unsupported format: {format_type}")
        
        try:
            data = self.api.download_activity(activity_id, format_map[format_type])
            return data
        except Exception as e:
            print(f"Failed to download activity {activity_id}: {e}")
            return None

def main():
    """Example usage of GarminConnectClient"""
    
    # Initialize client
    client = GarminConnectClient()
    
    # Authenticate
    if not client.authenticate():
        print("Authentication failed. Exiting.")
        return
    
    # Get user profile
    print("\n=== User Profile ===")
    profile = client.get_user_profile()
    if profile:
        print(json.dumps(profile, indent=2))
    
    # Get recent activities
    print("\n=== Recent Activities ===")
    activities = client.get_recent_activities(5)
    for activity in activities:
        print(f"• {activity['name']} ({activity['type']}) - {activity['start_time']}")
        print(f"  Distance: {activity['distance']:.2f}m, Duration: {activity['duration']}s")
    
    # Get today's health data
    print("\n=== Today's Health Data ===")
    health_data = client.get_health_snapshot()
    for data_type, data in health_data.items():
        if data:
            print(f"• {data_type}: {len(data) if isinstance(data, list) else 'Available'}")
    
    # Download latest activity
    if activities:
        latest_activity = activities[0]
        activity_id = latest_activity['activity_id']
        print(f"\n=== Downloading Latest Activity ({activity_id}) ===")
        
        gpx_data = client.download_activity(activity_id, 'gpx')
        if gpx_data:
            filename = f"activity_{activity_id}.gpx"
            with open(filename, 'wb') as f:
                f.write(gpx_data)
            print(f"✓ Saved to {filename}")

if __name__ == "__main__":
    main()
```

#### Using Garth Library Directly
```python
#!/usr/bin/env python3
"""
Direct Garth library usage example
Lower-level access to Garmin Connect APIs
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

import garth

class GarthClient:
    def __init__(self, email=None, password=None):
        self.email = email or os.getenv('GARMIN_EMAIL')
        self.password = password or os.getenv('GARMIN_PASSWORD')
        self.session_file = Path.home() / '.garth'
        
        if not self.email or not self.password:
            raise ValueError("Email and password required")
    
    def authenticate(self):
        """Authenticate with session resumption"""
        
        # Try to resume existing session
        if self.session_file.exists():
            try:
                garth.resume(str(self.session_file))
                if garth.client.username:
                    print(f"✓ Resumed session for {garth.client.username}")
                    return True
            except Exception as e:
                print(f"Session resume failed: {e}")
        
        # Fresh authentication
        try:
            print("Performing fresh authentication...")
            garth.login(self.email, self.password)
            garth.save(str(self.session_file))
            print(f"✓ Authenticated as {garth.client.username}")
            return True
            
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    def get_user_summary(self):
        """Get user summary data"""
        try:
            response = garth.connectapi("/userprofile-service/userprofile/user-settings")
            return response
        except Exception as e:
            print(f"Failed to get user summary: {e}")
            return None
    
    def get_activities(self, limit=20):
        """Get recent activities"""
        try:
            response = garth.connectapi(
                f"/activitylist-service/activities/search/activities?limit={limit}"
            )
            return response
        except Exception as e:
            print(f"Failed to get activities: {e}")
            return []
    
    def get_daily_summary(self, date):
        """Get daily health summary"""
        try:
            # Format date for API
            date_str = date.strftime('%Y-%m-%d')
            
            response = garth.connectapi(
                f"/usersummary-service/usersummary/daily/{date_str}"
            )
            return response
        except Exception as e:
            print(f"Failed to get daily summary: {e}")
            return None
    
    def download_activity_file(self, activity_id, file_type='fit'):
        """Download activity file"""
        try:
            if file_type == 'fit':
                url = f"/download-service/files/activity/{activity_id}"
            elif file_type == 'gpx':
                url = f"/download-service/export/gpx/activity/{activity_id}"
            elif file_type == 'tcx':
                url = f"/download-service/export/tcx/activity/{activity_id}"
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            data = garth.download(url)
            return data
            
        except Exception as e:
            print(f"Failed to download activity file: {e}")
            return None

def main():
    """Example usage of GarthClient"""
    
    client = GarthClient()
    
    # Authenticate
    if not client.authenticate():
        print("Authentication failed. Exiting.")
        return
    
    # Get user summary
    print("\n=== User Summary ===")
    user_summary = client.get_user_summary()
    if user_summary:
        print(f"User: {user_summary.get('displayName', 'Unknown')}")
        print(f"Units: {user_summary.get('unitSystem', 'Unknown')}")
    
    # Get recent activities
    print("\n=== Recent Activities ===")
    activities = client.get_activities(10)
    
    for activity in activities:
        print(f"• {activity.get('activityName')} - {activity.get('startTimeLocal')}")
        print(f"  Type: {activity.get('activityType', {}).get('typeKey')}")
        print(f"  Distance: {activity.get('distance', 0):.2f}m")
    
    # Get today's health summary
    print("\n=== Today's Health Summary ===")
    daily_summary = client.get_daily_summary(datetime.now())
    if daily_summary:
        print(f"Steps: {daily_summary.get('totalSteps', 0)}")
        print(f"Calories: {daily_summary.get('totalCalories', 0)}")
        print(f"Distance: {daily_summary.get('totalDistance', 0)}m")

if __name__ == "__main__":
    main()
```

## Production-Ready Implementation

### Complete Garmin Connect Data Sync Service
```python
#!/usr/bin/env python3
"""
Production-ready Garmin Connect data synchronization service
Features: robust error handling, logging, database storage, incremental sync
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from contextlib import contextmanager

import schedule
import time
from garminconnect import GarminConnect, GarminConnectConnectionError, GarminConnectTooManyRequestsError, GarminConnectAuthenticationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('garmin_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SyncConfig:
    """Configuration for Garmin sync service"""
    email: str
    password: str
    db_path: str = "garmin_data.db"
    activity_dir: str = "activities"
    sync_interval_minutes: int = 60
    max_activities_per_sync: int = 50
    retry_attempts: int = 3
    retry_delay_seconds: int = 300

class GarminDataStorage:
    """Handle database operations for Garmin data"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        with self.get_connection() as conn:
            # Activities table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    activity_id INTEGER PRIMARY KEY,
                    activity_name TEXT,
                    activity_type TEXT,
                    start_time_local TEXT,
                    start_time_gmt TEXT,
                    duration REAL,
                    distance REAL,
                    calories INTEGER,
                    avg_heart_rate INTEGER,
                    max_heart_rate INTEGER,
                    elevation_gain REAL,
                    elevation_loss REAL,
                    avg_speed REAL,
                    max_speed REAL,
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Health metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    metric_type TEXT,
                    metric_value REAL,
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, metric_type)
                )
            """)
            
            # Sync status table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_type TEXT,
                    last_sync_time TIMESTAMP,
                    last_activity_id INTEGER,
                    status TEXT,
                    error_message TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_activities_start_time ON activities(start_time_local)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_health_date ON health_metrics(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sync_type ON sync_status(sync_type)")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def store_activity(self, activity_data: Dict[str, Any]) -> bool:
        """Store activity data in database"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO activities (
                        activity_id, activity_name, activity_type, start_time_local,
                        start_time_gmt, duration, distance, calories, avg_heart_rate,
                        max_heart_rate, elevation_gain, elevation_loss, avg_speed,
                        max_speed, raw_data, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    activity_data.get('activityId'),
                    activity_data.get('activityName'),
                    activity_data.get('activityType', {}).get('typeKey'),
                    activity_data.get('startTimeLocal'),
                    activity_data.get('startTimeGMT'),
                    activity_data.get('duration'),
                    activity_data.get('distance'),
                    activity_data.get('calories'),
                    activity_data.get('averageHR'),
                    activity_data.get('maxHR'),
                    activity_data.get('elevationGain'),
                    activity_data.get('elevationLoss'),
                    activity_data.get('averageSpeed'),
                    activity_data.get('maxSpeed'),
                    json.dumps(activity_data)
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to store activity {activity_data.get('activityId')}: {e}")
            return False
    
    def store_health_metric(self, date: str, metric_type: str, value: Any, raw_data: Dict = None) -> bool:
        """Store health metric in database"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO health_metrics (date, metric_type, metric_value, raw_data)
                    VALUES (?, ?, ?, ?)
                """, (date, metric_type, value, json.dumps(raw_data) if raw_data else None))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to store health metric {metric_type} for {date}: {e}")
            return False
    
    def get_last_activity_id(self) -> Optional[int]:
        """Get the ID of the most recent activity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT activity_id FROM activities 
                    ORDER BY start_time_local DESC LIMIT 1
                """)
                result = cursor.fetchone()
                return result['activity_id'] if result else None
        except Exception as e:
            logger.error(f"Failed to get last activity ID: {e}")
            return None
    
    def update_sync_status(self, sync_type: str, status: str, error_message: str = None, last_activity_id: int = None):
        """Update sync status in database"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sync_status (
                        sync_type, last_sync_time, last_activity_id, status, error_message, updated_at
                    ) VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (sync_type, last_activity_id, status, error_message))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update sync status: {e}")

class GarminSyncService:
    """Main service for syncing Garmin Connect data"""
    
    def __init__(self, config: SyncConfig):
        self.config = config
        self.storage = GarminDataStorage(config.db_path)
        self.api = GarminConnect()
        self.activity_dir = Path(config.activity_dir)
        self.activity_dir.mkdir(exist_ok=True)
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Garmin Connect"""
        if self.authenticated:
            try:
                # Test authentication with a simple API call
                self.api.get_user_summary()
                return True
            except GarminConnectAuthenticationError:
                self.authenticated = False
        
        for attempt in range(self.config.retry_attempts):
            try:
                logger.info(f"Authentication attempt {attempt + 1}")
                self.api.login(self.config.email, self.config.password)
                self.authenticated = True
                logger.info("✓ Authentication successful")
                return True
                
            except GarminConnectAuthenticationError as e:
                logger.error(f"Authentication failed: {e}")
                if attempt == self.config.retry_attempts - 1:
                    raise
                    
            except GarminConnectTooManyRequestsError:
                wait_time = self.config.retry_delay_seconds * (attempt + 1)
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Unexpected authentication error: {e}")
                if attempt == self.config.retry_attempts - 1:
                    raise
                time.sleep(self.config.retry_delay_seconds)
        
        return False
    
    def sync_activities(self) -> bool:
        """Sync recent activities from Garmin Connect"""
        try:
            logger.info("Starting activity sync")
            
            # Get recent activities
            activities = self.api.get_activities(0, self.config.max_activities_per_sync)
            logger.info(f"Retrieved {len(activities)} activities")
            
            synced_count = 0
            for activity in activities:
                activity_id = activity.get('activityId')
                
                if self.storage.store_activity(activity):
                    synced_count += 1
                    
                    # Download activity file (FIT format)
                    try:
                        fit_data = self.api.download_activity(
                            activity_id, 
                            GarminConnect.ActivityDownloadFormat.ORIGINAL
                        )
                        
                        if fit_data:
                            fit_file_path = self.activity_dir / f"{activity_id}.fit"
                            with open(fit_file_path, 'wb') as f:
                                f.write(fit_data)
                            logger.debug(f"Downloaded FIT file for activity {activity_id}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to download FIT file for activity {activity_id}: {e}")
                
                # Rate limiting
                time.sleep(1)
            
            logger.info(f"Synced {synced_count} activities")
            self.storage.update_sync_status("activities", "success", last_activity_id=activities[0].get('activityId') if activities else None)
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Activity sync failed: {error_msg}")
            self.storage.update_sync_status("activities", "error", error_msg)
            return False
    
    def sync_health_metrics(self, date: datetime = None) -> bool:
        """Sync health metrics for a specific date"""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        
        try:
            logger.info(f"Starting health metrics sync for {date_str}")
            
            # Sync various health metrics
            health_methods = [
                ('steps', self.api.get_steps_data),
                ('heart_rate', self.api.get_heart_rates),
                ('sleep', self.api.get_sleep_data),
                ('body_battery', self.api.get_body_battery),
                ('stress', self.api.get_stress_data),
            ]
            
            synced_metrics = 0
            for metric_name, method in health_methods:
                try:
                    data = method(date_str)
                    if data:
                        # Extract relevant values based on metric type
                        if metric_name == 'steps':
                            value = data.get('totalSteps', 0)
                        elif metric_name == 'heart_rate':
                            value = data.get('restingHeartRate')
                        elif metric_name == 'sleep':
                            value = data.get('totalSleepTimeSeconds', 0) / 3600  # Convert to hours
                        elif metric_name == 'body_battery':
                            value = data.get('bodyBatteryValuesArray', [{}])[-1].get('value')
                        elif metric_name == 'stress':
                            value = data.get('overallStressLevel')
                        else:
                            value = None
                        
                        if value is not None:
                            if self.storage.store_health_metric(date_str, metric_name, value, data):
                                synced_metrics += 1
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Failed to sync {metric_name} for {date_str}: {e}")
            
            logger.info(f"Synced {synced_metrics} health metrics for {date_str}")
            self.storage.update_sync_status("health_metrics", "success")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Health metrics sync failed for {date_str}: {error_msg}")
            self.storage.update_sync_status("health_metrics", "error", error_msg)
            return False
    
    def run_full_sync(self):
        """Run complete synchronization"""
        logger.info("Starting full synchronization")
        
        if not self.authenticate():
            logger.error("Authentication failed. Skipping sync.")
            return
        
        # Sync activities
        self.sync_activities()
        
        # Sync health metrics for today and yesterday
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        self.sync_health_metrics(today)
        self.sync_health_metrics(yesterday)
        
        logger.info("Full synchronization completed")
    
    def run_scheduler(self):
        """Run the sync service with scheduler"""
        logger.info(f"Starting Garmin sync scheduler (interval: {self.config.sync_interval_minutes} minutes)")
        
        # Schedule sync job
        schedule.every(self.config.sync_interval_minutes).minutes.do(self.run_full_sync)
        
        # Run initial sync
        self.run_full_sync()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    
    # Load configuration
    config = SyncConfig(
        email=os.getenv('GARMIN_EMAIL'),
        password=os.getenv('GARMIN_PASSWORD'),
        db_path=os.getenv('GARMIN_DB_PATH', 'garmin_data.db'),
        activity_dir=os.getenv('GARMIN_ACTIVITY_DIR', 'activities'),
        sync_interval_minutes=int(os.getenv('GARMIN_SYNC_INTERVAL', '60')),
        max_activities_per_sync=int(os.getenv('GARMIN_MAX_ACTIVITIES', '50'))
    )
    
    if not config.email or not config.password:
        logger.error("GARMIN_EMAIL and GARMIN_PASSWORD environment variables required")
        sys.exit(1)
    
    # Create and run sync service
    sync_service = GarminSyncService(config)
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run sync once and exit
        sync_service.run_full_sync()
    else:
        # Run with scheduler
        try:
            sync_service.run_scheduler()
        except KeyboardInterrupt:
            logger.info("Sync service stopped by user")
        except Exception as e:
            logger.error(f"Sync service failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
```

### Docker Deployment Example

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY garmin_sync.py .
COPY config/ ./config/

# Create directories for data
RUN mkdir -p /data/activities /data/db

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GARMIN_DB_PATH=/data/db/garmin_data.db
ENV GARMIN_ACTIVITY_DIR=/data/activities

# Create non-root user
RUN groupadd -r garmin && useradd -r -g garmin garmin
RUN chown -R garmin:garmin /app /data
USER garmin

# Health check
HEALTHCHECK --interval=30m --timeout=10s --start-period=5m --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('${GARMIN_DB_PATH}'); conn.execute('SELECT 1'); conn.close()" || exit 1

# Run the sync service
CMD ["python", "garmin_sync.py"]
```

#### Docker Compose Configuration
```yaml
version: '3.8'

services:
  garmin-sync:
    build: .
    container_name: garmin-sync
    environment:
      - GARMIN_EMAIL=${GARMIN_EMAIL}
      - GARMIN_PASSWORD=${GARMIN_PASSWORD}
      - GARMIN_SYNC_INTERVAL=60
      - GARMIN_MAX_ACTIVITIES=50
    volumes:
      - ./data/db:/data/db
      - ./data/activities:/data/activities
      - ./logs:/app/logs
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - garmin-network

  # Optional: Add database viewer
  garmin-db-viewer:
    image: sqlitebrowser/sqlitebrowser
    container_name: garmin-db-viewer
    volumes:
      - ./data/db:/data
    ports:
      - "8080:8080"
    networks:
      - garmin-network

networks:
  garmin-network:
    driver: bridge
```

#### Environment File (.env)
```bash
# Garmin Connect credentials
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_secure_password

# Sync configuration
GARMIN_SYNC_INTERVAL=60
GARMIN_MAX_ACTIVITIES=50
GARMIN_DB_PATH=/data/db/garmin_data.db
GARMIN_ACTIVITY_DIR=/data/activities

# Security
SECRET_KEY=your-secret-key-here
```

### Usage Examples

#### Running the Sync Service
```bash
# One-time sync
python garmin_sync.py --once

# Continuous sync with scheduler
python garmin_sync.py

# Docker deployment
docker-compose up -d

# Check logs
docker-compose logs -f garmin-sync
```

#### Querying Synced Data
```python
#!/usr/bin/env python3
"""
Example queries for synced Garmin data
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def query_recent_activities(db_path: str, days: int = 30):
    """Query recent activities"""
    with sqlite3.connect(db_path) as conn:
        query = """
            SELECT activity_name, activity_type, start_time_local, 
                   distance, duration, calories, avg_heart_rate
            FROM activities 
            WHERE start_time_local >= date('now', '-{} days')
            ORDER BY start_time_local DESC
        """.format(days)
        
        df = pd.read_sql_query(query, conn)
        return df

def query_health_trends(db_path: str, metric_type: str, days: int = 90):
    """Query health metric trends"""
    with sqlite3.connect(db_path) as conn:
        query = """
            SELECT date, metric_value
            FROM health_metrics
            WHERE metric_type = ? AND date >= date('now', '-{} days')
            ORDER BY date
        """.format(days)
        
        df = pd.read_sql_query(query, conn, params=[metric_type])
        return df

# Usage
if __name__ == "__main__":
    db_path = "garmin_data.db"
    
    # Get recent activities
    activities = query_recent_activities(db_path)
    print("Recent Activities:")
    print(activities.head())
    
    # Get step trends
    steps = query_health_trends(db_path, "steps")
    print("\nStep Trends:")
    print(steps.tail())
```

This comprehensive implementation provides a production-ready foundation for integrating with Garmin Connect, including robust error handling, data persistence, scheduling, and containerized deployment options.