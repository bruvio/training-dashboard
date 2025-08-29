# GPXpy

## Library Overview
- A Python library for parsing and manipulating GPX (GPS eXchange Format) files
- Supports GPX versions 1.0 and 1.1
- Allows reading, creating, and modifying GPS track data

## Key Features
- Parse existing GPX files
- Create new GPX tracks and points
- Extract track, waypoint, and route information
- Calculate GPS-related statistics

## Installation
Typically installed via pip:
```
pip install gpxpy
```

## Basic Usage Example
```python
import gpxpy
import gpxpy.gpx

# Parsing an existing GPX file
gpx_file = open('track.gpx', 'r')
gpx = gpxpy.parse(gpx_file)

# Iterate through tracks, segments, and points
for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            print(f'Point: {point.latitude}, {point.longitude}')
```

## Creating a New GPX File
```python
gpx = gpxpy.gpx.GPX()
track = gpxpy.gpx.GPXTrack()
gpx.tracks.append(track)

segment = gpxpy.gpx.GPXTrackSegment()
track.segments.append(segment)

# Add track points
segment.points.append(gpxpy.gpx.GPXTrackPoint(2.1234, 5.1234, elevation=1234))
```

## Notable Characteristics
- Uses lxml for faster XML parsing when available
- Preserves GPX extensions
- Provides heuristics to remove GPS errors when calculating statistics
- Supports Python 3.6+

## Additional Tools
- Companion command-line tools available: `pip install gpx-cmd-tools`

## Licensing
- Apache License, Version 2.0