# Python TCXParser

## Library Overview
python-tcxparser is a "minimal parser for Garmin's TCX file format" designed to extract workout and fitness tracking data from TCX files.

## Installation
Install via pip:
```
pip install python-tcxparser
```

## Compatibility
- Supports Python 3.7+
- BSD licensed

## Key Features
The library can extract multiple data points from TCX files, including:
- Workout latitude/longitude
- Activity type (running, walking)
- Workout duration
- Distance
- Calories burned
- Heart rate metrics
- Altitude data
- Cadence
- Power output
- Total steps/strokes

## Usage Example
```python
import tcxparser
tcx = tcxparser.TCXParser('/path/to/workout.tcx')

# Example data extraction
print(tcx.duration)        # Workout duration
print(tcx.latitude)        # Starting latitude
print(tcx.activity_type)   # Type of activity
print(tcx.distance)        # Workout distance
```

## Advanced Feature
The library supports heart rate zone analysis:
```python
zones = tcx.hr_percent_in_zones({
    "Z0": (0, 99), 
    "Z1": (100, 129), 
    "Z2": (130, 200)
})
```

## Maintainer
Vinod Kurup (vinod@kurup.com)