# Activity Download Capabilities and Formats

## Overview

Garmin Connect provides activity data in multiple formats, each with specific use cases, data richness, and compatibility considerations. Understanding these formats is crucial for choosing the right approach for data analysis and storage.

## Available File Formats

### 1. FIT (Flexible and Interoperable Data Transfer)

#### Overview
- **Developer**: Garmin (proprietary but open specification)
- **File Extension**: `.fit`
- **Format Type**: Binary
- **Data Richness**: Highest - contains all recorded metrics
- **File Size**: Smallest (typically 50-500KB)

#### Key Characteristics
- **Native Format**: Original format used by Garmin devices
- **Comprehensive Data**: Contains all sensor data, metadata, and device-specific metrics
- **Efficient Storage**: Highly compressed binary format
- **Device Compatibility**: Supported by most fitness platforms

#### Data Types Available in FIT Files
```
- GPS coordinates (latitude, longitude, altitude)
- Timestamps with millisecond precision
- Heart rate (instantaneous and zones)
- Power data (watts, left/right balance)
- Cadence (steps/minute for running, RPM for cycling)
- Speed and pace
- Temperature
- Activity-specific metrics (stroke rate for swimming, etc.)
- Device and sensor information
- Lap and interval markers
- Training effect and recovery data
```

#### Python Parsing Options
```python
# Using fitparse library
from fitparse import FitFile

fitfile = FitFile('activity.fit')
for record in fitfile.get_messages('record'):
    for data in record:
        print(f"{data.name}: {data.value}")

# Using fitdecode library  
import fitdecode

with fitdecode.FitReader('activity.fit') as fit:
    for frame in fit:
        if isinstance(frame, fitdecode.FitDataMessage):
            print(frame.name, frame.fields)
```

#### Advantages
- Complete data preservation
- Smallest file size
- Native device format
- Supports all Garmin-specific metrics

#### Disadvantages
- Proprietary format (licensing considerations)
- Requires specialized parsing libraries
- Binary format not human-readable
- Garmin owns derivative works of parsing code

### 2. GPX (GPS Exchange Format)

#### Overview
- **Standard**: Open XML-based format
- **File Extension**: `.gpx`
- **Format Type**: XML text
- **Primary Use**: GPS track data and waypoints
- **Compatibility**: Universal GPS format

#### Key Characteristics
```xml
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Garmin Connect">
  <metadata>
    <name>Activity Name</name>
    <time>2024-01-15T10:30:00Z</time>
  </metadata>
  <trk>
    <name>Track Name</name>
    <trkseg>
      <trkpt lat="40.7128" lon="-74.0060">
        <ele>10.5</ele>
        <time>2024-01-15T10:30:00Z</time>
        <extensions>
          <gpxtpx:TrackPointExtension>
            <gpxtpx:hr>145</gpxtpx:hr>
            <gpxtpx:cad>180</gpxtpx:cad>
          </gpxtpx:TrackPointExtension>
        </extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
```

#### Core Data Elements
- **Track Points**: GPS coordinates with timestamps
- **Elevation**: Altitude data
- **Waypoints**: Named locations
- **Routes**: Planned courses
- **Metadata**: Activity name, description, timestamps

#### Extended Data (via Extensions)
```xml
<extensions>
  <gpxtpx:TrackPointExtension>
    <gpxtpx:hr>145</gpxtpx:hr>        <!-- Heart rate -->
    <gpxtpx:cad>180</gpxtpx:cad>      <!-- Cadence -->
    <gpxtpx:atemp>22</gpxtpx:atemp>   <!-- Temperature -->
    <gpxtpx:power>250</gpxtpx:power>  <!-- Power watts -->
  </gpxtpx:TrackPointExtension>
</extensions>
```

#### Python Parsing
```python
import gpxpy

# Parse GPX file
with open('activity.gpx', 'r') as gpx_file:
    gpx = gpxpy.parse(gpx_file)

# Extract data
for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            print(f"Point: {point.latitude}, {point.longitude}")
            print(f"Elevation: {point.elevation}")
            print(f"Time: {point.time}")
            
            # Extensions data
            if point.extensions:
                hr = point.extensions.get('hr')
                cadence = point.extensions.get('cad')
```

#### Advantages
- Open standard, widely supported
- Human-readable XML format
- Excellent GPS data preservation
- Compatible with most mapping applications
- Supports custom extensions for additional data

#### Disadvantages
- Larger file sizes than FIT
- Limited native support for fitness metrics
- Extensions not standardized across platforms
- May lose some device-specific data

### 3. TCX (Training Center XML)

#### Overview
- **Developer**: Garmin (but open format)
- **File Extension**: `.tcx`
- **Format Type**: XML text
- **Focus**: Training and fitness data
- **Compatibility**: Supported by most fitness platforms

#### Key Characteristics
```xml
<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
  <Activities>
    <Activity Sport="Running">
      <Id>2024-01-15T10:30:00Z</Id>
      <Lap StartTime="2024-01-15T10:30:00Z">
        <TotalTimeSeconds>3600.0</TotalTimeSeconds>
        <DistanceMeters>10000.0</DistanceMeters>
        <MaximumSpeed>5.5</MaximumSpeed>
        <Calories>500</Calories>
        <AverageHeartRateBpm>
          <Value>145</Value>
        </AverageHeartRateBpm>
        <MaximumHeartRateBpm>
          <Value>175</Value>
        </MaximumHeartRateBpm>
        <Track>
          <Trackpoint>
            <Time>2024-01-15T10:30:00Z</Time>
            <Position>
              <LatitudeDegrees>40.7128</LatitudeDegrees>
              <LongitudeDegrees>-74.0060</LongitudeDegrees>
            </Position>
            <AltitudeMeters>10.5</AltitudeMeters>
            <DistanceMeters>0.0</DistanceMeters>
            <HeartRateBpm>
              <Value>140</Value>
            </HeartRateBpm>
            <Cadence>180</Cadence>
            <Extensions>
              <TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2">
                <Watts>250</Watts>
              </TPX>
            </Extensions>
          </Trackpoint>
        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>
```

#### Data Structure
- **Activities**: Top-level container for multiple activities
- **Laps**: Segments within activities (auto-lap, manual splits)
- **Tracks**: GPS coordinates and sensor data
- **Trackpoints**: Individual data points with timestamps

#### Native Support For
- Heart rate data (average, maximum, zones)
- Cadence (running steps, cycling RPM)
- Speed and pace calculations
- Distance and elevation
- Calories burned
- Activity type and sport classification
- Lap splits and intervals

#### Python Parsing
```python
from tcxparser import TCXParser

# Parse TCX file
tcx = TCXParser('activity.tcx')

# Basic activity data
print(f"Activity type: {tcx.activity_type}")
print(f"Distance: {tcx.distance}")
print(f"Duration: {tcx.duration}")
print(f"Calories: {tcx.calories}")

# Trackpoints data
for point in tcx.trackpoints:
    print(f"Time: {point.time}")
    print(f"Position: {point.latitude}, {point.longitude}")
    print(f"HR: {point.hr_value}")
    print(f"Cadence: {point.cadence}")
```

#### Advantages
- Rich fitness data structure
- Native support for training metrics
- Widely compatible with fitness software
- Structured lap and interval data
- Good balance of completeness and file size

#### Disadvantages
- Larger than FIT files
- XML verbosity
- Less universal than GPX for GPS applications
- May not capture all device-specific metrics

### 4. CSV (Comma-Separated Values)

#### Overview
- **Format**: Plain text, comma-delimited
- **Use Case**: Bulk export, data analysis
- **Availability**: Limited to bulk exports from Garmin Connect web

#### Characteristics
```csv
Activity Type,Date,Favorite,Title,Distance,Calories,Time,Avg HR,Max HR,Aerobic TE,Avg Run Cadence,Max Run Cadence,Avg Pace,Best Pace,Elev Gain,Elev Loss,Avg Stride Length,Avg Vertical Ratio,Avg Vertical Oscillation,Avg Ground Contact Time,Training Stress Score,Grit,Flow,Bottom Time,Min Temp,Max Temp,Moving Time,Elapsed Time,Min Elevation,Max Elevation
Running,2024-01-15,false,"Morning Run",10.5,450,3600,145,175,3.2,180,200,5:42,4:15,150,145,1.2,8.5,10.2,250,,,,,15,18,3450,3600,5,125
```

#### Data Available
- Basic activity summary metrics
- Performance statistics (pace, heart rate, cadence)
- Environmental data (temperature, elevation)
- Training load metrics (Training Effect, TSS)
- Activity metadata (title, date, type)

#### Python Processing
```python
import pandas as pd

# Load CSV data
df = pd.read_csv('activities.csv')

# Basic analysis
print(f"Total activities: {len(df)}")
print(f"Activity types: {df['Activity Type'].value_counts()}")
print(f"Average distance: {df['Distance'].mean():.2f}")

# Time series analysis
df['Date'] = pd.to_datetime(df['Date'])
monthly_distance = df.groupby(df['Date'].dt.to_period('M'))['Distance'].sum()
```

#### Advantages
- Simple format, easy to process
- Excellent for statistical analysis
- Works with any spreadsheet software
- Bulk export available
- Small file size for summary data

#### Disadvantages
- No GPS track data
- Limited to summary metrics
- No detailed sensor data
- Bulk export only (not per-activity)

## Download Methods and APIs

### Official API Downloads

#### Activity API Endpoints
```python
# Using official API (requires approval)
import requests
from requests_oauthlib import OAuth1

auth = OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)

# Download FIT file
fit_response = requests.get(
    f"https://apis.garmin.com/wellness-api/rest/activities/{activity_id}/fit",
    auth=auth
)

# Download GPX file
gpx_response = requests.get(
    f"https://apis.garmin.com/wellness-api/rest/activities/{activity_id}/gpx",
    auth=auth
)

# Download TCX file
tcx_response = requests.get(
    f"https://apis.garmin.com/wellness-api/rest/activities/{activity_id}/tcx",
    auth=auth
)
```

### Unofficial Library Downloads

#### python-garminconnect
```python
from garminconnect import GarminConnect

api = GarminConnect()
api.login(email, password)

# Get recent activities
activities = api.get_activities(0, 10)

# Download in different formats
for activity in activities:
    activity_id = activity['activityId']
    
    # Download FIT file (original format)
    fit_data = api.download_activity(activity_id, GarminConnect.ActivityDownloadFormat.ORIGINAL)
    
    # Download GPX file
    gpx_data = api.download_activity(activity_id, GarminConnect.ActivityDownloadFormat.GPX)
    
    # Download TCX file
    tcx_data = api.download_activity(activity_id, GarminConnect.ActivityDownloadFormat.TCX)
    
    # Download CSV summary
    csv_data = api.download_activity(activity_id, GarminConnect.ActivityDownloadFormat.CSV)
```

#### Garth Direct API Access
```python
import garth

# Login and get activity data
garth.login(email, password)

# Direct API calls
activities = garth.connectapi(f"/activitylist-service/activities/search/activities")

# Download specific format
activity_id = activities[0]['activityId']
fit_data = garth.download(f"/download-service/files/activity/{activity_id}")
```

## Format Conversion Tools

### FIT to GPX Conversion
```python
# Using fit2gpx library
from fit2gpx import Converter

conv = Converter()
gpx = conv.fit_to_gpx(f_in='activity.fit', f_out='activity.gpx')
```

### Multi-format Processing Pipeline
```python
def process_activity(activity_id, formats=['fit', 'gpx', 'tcx']):
    results = {}
    
    for format_type in formats:
        try:
            if format_type == 'fit':
                data = api.download_activity(activity_id, GarminConnect.ActivityDownloadFormat.ORIGINAL)
                results['fit'] = parse_fit_file(data)
            elif format_type == 'gpx':
                data = api.download_activity(activity_id, GarminConnect.ActivityDownloadFormat.GPX)
                results['gpx'] = parse_gpx_file(data)
            elif format_type == 'tcx':
                data = api.download_activity(activity_id, GarminConnect.ActivityDownloadFormat.TCX)
                results['tcx'] = parse_tcx_file(data)
        except Exception as e:
            print(f"Failed to download {format_type}: {e}")
    
    return results
```

## Best Practices for Data Download

### Incremental Sync Strategy
```python
def sync_activities(api, last_sync_date=None):
    """Download only new activities since last sync"""
    
    if last_sync_date:
        # Get activities since last sync
        activities = api.get_activities_by_date(
            last_sync_date.isoformat(),
            datetime.now().isoformat()
        )
    else:
        # Initial sync - get all activities
        activities = api.get_activities(0, 1000)  # Adjust limit as needed
    
    for activity in activities:
        activity_id = activity['activityId']
        
        # Check if already downloaded
        if not activity_exists_locally(activity_id):
            download_activity_files(activity_id)
```

### Storage Organization
```python
import os
from datetime import datetime

def organize_activity_files(activity_data, activity_id):
    """Organize downloaded files by date and activity type"""
    
    activity_date = datetime.fromisoformat(activity_data['startTimeLocal'])
    activity_type = activity_data['activityType']['typeKey']
    
    # Create directory structure: YYYY/MM/activity_type/
    base_dir = f"activities/{activity_date.year:04d}/{activity_date.month:02d}/{activity_type}"
    os.makedirs(base_dir, exist_ok=True)
    
    # File naming: YYYYMMDD_HHMMSS_activity_id.format
    timestamp = activity_date.strftime("%Y%m%d_%H%M%S")
    
    file_paths = {
        'fit': f"{base_dir}/{timestamp}_{activity_id}.fit",
        'gpx': f"{base_dir}/{timestamp}_{activity_id}.gpx",
        'tcx': f"{base_dir}/{timestamp}_{activity_id}.tcx"
    }
    
    return file_paths
```

### Error Handling and Retry Logic
```python
import time
import random

def robust_download(api, activity_id, format_type, max_retries=3):
    """Download with retry logic and error handling"""
    
    for attempt in range(max_retries):
        try:
            data = api.download_activity(activity_id, format_type)
            return data
        except GarminConnectTooManyRequestsError:
            # Rate limited - wait with exponential backoff
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Rate limited, waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Download attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
```

## Data Validation and Quality Checks

### File Integrity Checks
```python
def validate_activity_file(file_path, format_type):
    """Validate downloaded activity files"""
    
    try:
        if format_type == 'fit':
            from fitparse import FitFile
            fitfile = FitFile(file_path)
            # Check if file can be parsed
            list(fitfile.get_messages())
            
        elif format_type == 'gpx':
            import gpxpy
            with open(file_path, 'r') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
                # Check for tracks
                return len(gpx.tracks) > 0
                
        elif format_type == 'tcx':
            from tcxparser import TCXParser
            tcx = TCXParser(file_path)
            # Check for valid duration
            return tcx.duration is not None
            
        return True
    except Exception as e:
        print(f"File validation failed: {e}")
        return False
```

### Data Completeness Checks
```python
def check_data_completeness(activity_data, file_data):
    """Compare API metadata with file contents"""
    
    checks = {
        'duration_match': abs(activity_data['duration'] - file_data['duration']) < 10,
        'distance_match': abs(activity_data['distance'] - file_data['distance']) < 100,
        'has_gps_data': file_data.get('gps_points', 0) > 0,
        'has_hr_data': file_data.get('hr_points', 0) > 0
    }
    
    return all(checks.values()), checks
```