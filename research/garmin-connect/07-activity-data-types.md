# Available Activity Data Types and Metadata

## Overview

Garmin Connect activities contain extensive metadata across various data categories, sensor inputs, and calculated metrics. This document provides comprehensive information about the data types, structures, and formats available through different access methods.

## Core Activity Metadata

### Basic Activity Information
```json
{
  "activityId": 12345678901,
  "activityName": "Morning Run",
  "description": "Easy pace recovery run",
  "startTimeLocal": "2024-01-15T06:30:00.000",
  "startTimeGMT": "2024-01-15T11:30:00.000",
  "activityType": {
    "typeId": 1,
    "typeKey": "running",
    "parentTypeId": 17,
    "isHidden": false,
    "restricted": false,
    "trailRunSubType": null
  },
  "eventType": {
    "typeId": 9,
    "typeKey": "fitness_equipment",
    "sortOrder": 1
  }
}
```

### Duration and Distance Metrics
```json
{
  "duration": 2847.756,                    // Total duration in seconds
  "movingDuration": 2787.0,               // Moving time only
  "elapsedDuration": 2847.756,            // Elapsed time including stops
  "distance": 8047.36,                    // Distance in meters
  "steps": 9823,                          // Total step count
  "averageSpeed": 2.89,                   // Average speed in m/s
  "maxSpeed": 4.12                        // Maximum speed in m/s
}
```

### Elevation and Environmental Data
```json
{
  "elevationGain": 145.0,                 // Total elevation gain in meters
  "elevationLoss": 142.0,                 // Total elevation loss in meters
  "minElevation": 85.2,                   // Minimum elevation in meters
  "maxElevation": 198.7,                  // Maximum elevation in meters
  "averageTemperature": 18.5,             // Average temperature in Celsius
  "minTemperature": 16.2,                 // Minimum temperature
  "maxTemperature": 21.3,                 // Maximum temperature
  "weather": {
    "weatherTypeId": 1,
    "windDirectionTypeId": 4,
    "windSpeedTypeId": 3,
    "precipitationTypeId": 0,
    "temp": 18,
    "apparentTemp": 20,
    "humidity": 65,
    "dewPoint": 12.1,
    "windSpeed": 8.2,
    "windGust": 14.5,
    "pressureMillibars": 1013.25,
    "visibility": 16.1,
    "cloudCover": 25
  }
}
```

## Heart Rate Data Types

### Basic Heart Rate Metrics
```json
{
  "averageHR": 145,                       // Average heart rate in BPM
  "maxHR": 172,                          // Maximum heart rate
  "averageRunningCadenceInStepsPerMinute": 180,  // Running cadence
  "maxRunningCadenceInStepsPerMinute": 196,
  "totalTrainingEffect": 3.2,            // Aerobic Training Effect
  "anaerobicTrainingEffect": 1.8,        // Anaerobic Training Effect
  "avgVerticalOscillation": 8.7,         // Average vertical oscillation in cm
  "avgVerticalRatio": 7.8,               // Vertical ratio percentage
  "avgGroundContactTime": 248,           // Ground contact time in milliseconds
  "avgStrideLength": 1.34                // Average stride length in meters
}
```

### Heart Rate Zones and Distribution
```json
{
  "timeInHRZone": [
    { "zoneLowBoundary": 0, "zoneHighBoundary": 127, "timeInZone": 0 },
    { "zoneLowBoundary": 127, "zoneHighBoundary": 144, "timeInZone": 856 },
    { "zoneLowBoundary": 144, "zoneHighBoundary": 162, "timeInZone": 1524 },
    { "zoneLowBoundary": 162, "zoneHighBoundary": 179, "timeInZone": 467 },
    { "zoneLowBoundary": 179, "zoneHighBoundary": 300, "timeInZone": 0 }
  ],
  "hrZones": [
    {
      "zoneNumber": 1,
      "zoneName": "Zone 1",
      "secsInZone": 0,
      "zoneRange": "50% - 60%"
    },
    {
      "zoneNumber": 2,
      "zoneName": "Zone 2", 
      "secsInZone": 856,
      "zoneRange": "60% - 70%"
    }
    // ... additional zones
  ]
}
```

### Advanced Heart Rate Metrics
```json
{
  "maxAvgPower_1": 285,                   // 1-second max average power
  "maxAvgPower_2": 278,                   // 2-second max average power
  "maxAvgPower_5": 265,                   // 5-second max average power
  "maxAvgPower_10": 258,                  // 10-second max average power
  "maxAvgPower_20": 252,                  // 20-second max average power
  "maxAvgPower_30": 248,                  // 30-second max average power
  "maxAvgPower_60": 235,                  // 1-minute max average power
  "maxAvgPower_120": 225,                 // 2-minute max average power
  "maxAvgPower_300": 212,                 // 5-minute max average power
  "maxAvgPower_600": 205,                 // 10-minute max average power
  "maxAvgPower_1200": 198,                // 20-minute max average power
  "maxAvgPower_1800": 192,                // 30-minute max average power
  "maxAvgPower_3600": 185,                // 60-minute max average power
  "avgPower": 180,                        // Average power for entire activity
  "maxPower": 425,                        // Maximum instantaneous power
  "normalizedPower": 188,                 // Normalized Power (TrainingPeaks metric)
  "intensityFactor": 0.78,                // Intensity Factor
  "trainingStressScore": 95.2             // Training Stress Score
}
```

## GPS and Location Data

### Track Points and Coordinates
```json
{
  "startLatitude": 40.712776,             // Starting latitude in decimal degrees
  "startLongitude": -74.005974,           // Starting longitude
  "endLatitude": 40.715123,               // Ending latitude
  "endLongitude": -74.008456,             // Ending longitude
  "hasPolyline": true,                    // Whether GPS track is available
  "polylinePoints": "encoded_polyline_string",  // Encoded GPS track
  "locationName": "New York, NY",         // Detected location
  "hasGeoFences": false,                  // Whether geofences were crossed
  "geoFences": []                         // List of geofence events
}
```

### GPS Quality and Accuracy Metrics
```json
{
  "gpsAccuracy": "HIGH",                  // GPS accuracy rating
  "satelliteCount": 12,                   // Number of satellites used
  "hdop": 1.2,                           // Horizontal dilution of precision
  "vdop": 1.8,                           // Vertical dilution of precision
  "hasBarometricAltitude": true,          // Whether barometric altitude available
  "altimeterCorrected": true,             // Whether altitude was corrected
  "manualActivity": false                 // Whether manually entered activity
}
```

## Activity-Specific Data Types

### Running-Specific Metrics
```json
{
  "averagePace": 358.2,                   // Average pace in seconds per kilometer
  "bestPace": 312.5,                      // Best pace during activity
  "averageMovingSpeed": 2.89,             // Average moving speed in m/s
  "averageRunningCadenceInStepsPerMinute": 180,
  "maxRunningCadenceInStepsPerMinute": 196,
  "strideLength": {
    "avg": 1.34,                          // Average stride length in meters
    "max": 1.52,                          // Maximum stride length
    "min": 1.18                           // Minimum stride length
  },
  "verticalOscillation": {
    "avg": 8.7,                           // Average in centimeters
    "max": 12.3,
    "min": 6.4
  },
  "groundContactTime": {
    "avg": 248,                           // Average in milliseconds
    "max": 285,
    "min": 220
  },
  "groundContactBalance": {
    "left": 49.2,                         // Left foot percentage
    "right": 50.8                         // Right foot percentage
  }
}
```

### Cycling-Specific Metrics
```json
{
  "avgBikingCadenceInRevPerMinute": 85,   // Average cycling cadence in RPM
  "maxBikingCadenceInRevPerMinute": 110,  // Maximum cycling cadence
  "avgPower": 180,                        // Average power in watts
  "maxPower": 425,                        // Maximum power
  "normalizedPower": 188,                 // Normalized Power
  "leftRightBalance": {
    "left": 48.5,                         // Left leg power percentage
    "right": 51.5                         // Right leg power percentage
  },
  "pedalSmoothness": {
    "left": 24.5,                         // Left pedal smoothness percentage
    "right": 26.8                         // Right pedal smoothness
  },
  "torqueEffectiveness": {
    "left": 92.3,                         // Left torque effectiveness
    "right": 93.1                         // Right torque effectiveness
  },
  "gears": {
    "frontGear": 2,                       // Front gear number
    "rearGear": 8,                        // Rear gear number
    "gearRatio": 2.8                      // Current gear ratio
  }
}
```

### Swimming-Specific Metrics
```json
{
  "poolLength": 25,                       // Pool length in meters
  "strokes": 1247,                        // Total stroke count
  "avgStrokes": 18,                       // Average strokes per length
  "avgStrokeDistance": 2.1,               // Average distance per stroke in meters
  "avgStrokeRate": 32,                    // Average stroke rate per minute
  "swimStroke": "freestyle",              // Primary stroke type
  "avgSwolf": 43,                         // Average SWOLF score
  "activeLengths": 64,                    // Number of active swimming lengths
  "poolLengths": 64,                      // Total pool lengths completed
  "restingTime": 145                      // Total resting time in seconds
}
```

## Environmental and Sensor Data

### Temperature and Weather Conditions
```json
{
  "temperature": {
    "avg": 18.5,                          // Average temperature in Celsius
    "max": 21.3,                          // Maximum temperature
    "min": 16.2,                          // Minimum temperature
    "at_start": 17.8,                     // Temperature at activity start
    "at_end": 19.2                        // Temperature at activity end
  },
  "humidity": 65,                         // Relative humidity percentage
  "dewPoint": 12.1,                       // Dew point in Celsius
  "windSpeed": 8.2,                       // Wind speed in km/h
  "windDirection": 225,                   // Wind direction in degrees
  "windGust": 14.5,                       // Wind gust speed
  "pressure": 1013.25,                    // Atmospheric pressure in millibars
  "visibility": 16.1,                     // Visibility in kilometers
  "uvIndex": 4,                           // UV index
  "cloudCover": 25                        // Cloud cover percentage
}
```

### Device and Sensor Information
```json
{
  "device": {
    "deviceId": 123456789,
    "deviceTypePk": 2441,
    "deviceVersionPk": 3688,
    "displayName": "Forerunner 955",
    "partNumber": "010-02638-00",
    "softwareVersionString": "20.26",
    "maxHeartRate": 185,
    "restingHeartRate": 52
  },
  "sensors": [
    {
      "sensorType": "heart_rate",
      "deviceId": "HRM-Pro_123456",
      "batteryLevel": 85,
      "connected": true
    },
    {
      "sensorType": "foot_pod",
      "deviceId": "FootPod_789012", 
      "batteryLevel": 62,
      "connected": true
    }
  ]
}
```

## Training Load and Performance Metrics

### Training Effect and Load
```json
{
  "aerobicTrainingEffect": 3.2,           // Aerobic TE (0.0-5.0 scale)
  "aerobicTrainingEffectMessage": "Maintaining",
  "anaerobicTrainingEffect": 1.8,         // Anaerobic TE (0.0-5.0 scale)
  "anaerobicTrainingEffectMessage": "Minor Impact",
  "trainingStressScore": 95.2,            // Training Stress Score
  "intensityFactor": 0.78,                // Intensity Factor
  "chronicTrainingLoad": 42.5,            // CTL (fitness)
  "acuteTrainingLoad": 55.8,              // ATL (fatigue)
  "trainingStressBalance": -13.3,         // TSB (form)
  "vo2MaxValue": 52.4,                    // Estimated VO2 Max
  "lactateThresholdHeartRate": 165,       // LT heart rate
  "lactateThresholdSpeed": 4.2,           // LT pace/speed
  "recoveryTime": 18                      // Recovery time in hours
}
```

### Performance Condition and Recovery
```json
{
  "performanceCondition": 5,              // Performance condition (+/- 20 scale)
  "performanceConditionMessage": "Good",
  "recoveryHeartRate": 118,               // Heart rate 1 minute after activity
  "lactateThresholdBpm": 165,             // Lactate threshold heart rate
  "workoutBenefitType": "TEMPO",          // Primary workout benefit
  "primaryBenefit": {
    "benefitType": "TEMPO",
    "message": "This activity improved your lactate threshold."
  },
  "trainingReadiness": {
    "score": 72,                          // Training readiness score (0-100)
    "status": "BALANCED",
    "message": "You're ready for a challenging workout.",
    "hrv": 45.2,                          // Heart rate variability
    "sleepScore": 78,                     // Sleep quality score
    "recoveryStatus": "RECOVERED"
  }
}
```

## Lap and Split Data

### Lap Summary Information
```json
{
  "laps": [
    {
      "startTimeInSeconds": 0,
      "lapIndex": 0,
      "totalDistanceInMeters": 1609.34,    // 1 mile
      "totalTimeInSeconds": 358.2,
      "averageSpeed": 4.49,                // m/s
      "maxSpeed": 5.12,
      "averageHeartRate": 142,
      "maxHeartRate": 156,
      "averagePower": 185,
      "maxPower": 245,
      "calories": 89,
      "averageCadence": 182,
      "maxCadence": 194,
      "elevationGain": 12.5,
      "elevationLoss": 8.3,
      "avgVerticalOscillation": 8.4,
      "avgGroundContactTime": 245,
      "avgStrideLength": 1.36
    }
    // Additional laps...
  ]
}
```

### Auto-Pause and Manual Markers
```json
{
  "autoPauseEvents": [
    {
      "eventTime": 1245.6,
      "pauseType": "AUTO",
      "reason": "STOPPED",
      "duration": 45.2
    }
  ],
  "markers": [
    {
      "markerTime": 804.5,
      "markerType": "MANUAL",
      "message": "Water stop",
      "latitude": 40.713456,
      "longitude": -74.007123
    }
  ]
}
```

## Detailed Time Series Data

### Sample Rate and Data Points
```json
{
  "sampleRates": {
    "gps": "1Hz",                         // GPS points per second
    "heart_rate": "1Hz",                  // Heart rate samples per second
    "power": "1Hz",                       // Power samples per second
    "cadence": "1Hz",                     // Cadence samples per second
    "temperature": "0.1Hz"                // Temperature samples per second
  },
  "timeSeriesData": {
    "metricsDescriptors": [
      {
        "metricsIndex": 3,
        "metricsKey": "directSpeed",
        "unit": "m/s"
      },
      {
        "metricsIndex": 4,
        "metricsKey": "directHeartRate",
        "unit": "bpm"
      }
    ],
    "activityDetailMetrics": [
      {
        "metrics": [null, null, null, 2.89, 142, null, null, 180],
        "timeOffsetInSeconds": 0
      },
      {
        "metrics": [null, null, null, 2.94, 144, null, null, 182], 
        "timeOffsetInSeconds": 1
      }
      // Continues for entire activity duration...
    ]
  }
}
```

## Data Access Patterns by API Method

### Official API Data Structure
```python
# Health API - JSON format
{
  "summaries": [
    {
      "userId": "user123",
      "calendarDate": "2024-01-15",
      "totalSteps": 8547,
      "totalDistance": 6847,
      "activeCalories": 456,
      "bmrCalories": 1456,
      "totalCalories": 1912,
      "sleepHours": 7.5,
      "stressAverage": 32,
      "bodyBatteryDrained": 45,
      "bodyBatteryCharged": 32,
      "bodyBatteryHighestValue": 95,
      "bodyBatteryLowestValue": 15
    }
  ]
}

# Activity API - Multiple formats available
# FIT file: Binary format with all sensor data
# GPX file: GPS track with extensions
# TCX file: Training-focused XML format
```

### python-garminconnect Library Data
```python
# Activity details structure
activity_details = {
    'activityId': 12345678901,
    'activityName': 'Morning Run',
    'startTimeLocal': '2024-01-15T06:30:00.000',
    'distance': 8047.36,
    'duration': 2847.756,
    'averageSpeed': 2.89,
    'calories': 456,
    'averageHR': 145,
    'maxHR': 172,
    'averageRunningCadenceInStepsPerMinute': 180,
    'elevationGain': 145.0,
    'elevationLoss': 142.0
}

# Health metrics structure  
health_data = {
    'date': '2024-01-15',
    'totalSteps': 8547,
    'activeCalories': 456,
    'bmrCalories': 1456,
    'restingHeartRate': 52,
    'maxHeartRate': 172,
    'bodyBatteryDrained': 45,
    'bodyBatteryCharged': 32,
    'stressAverage': 32,
    'sleepScore': 78
}
```

## Data Quality and Completeness Indicators

### Quality Metrics
```json
{
  "dataQuality": {
    "gpsAccuracy": "HIGH",               // GPS signal quality
    "heartRateSource": "CHEST_STRAP",   // HR data source
    "powerMeterAccuracy": "CALIBRATED", // Power meter status
    "temperatureSource": "DEVICE",      // Temperature data source
    "altitudeSource": "BAROMETRIC",     // Elevation data source
    "completeness": {
      "gps_track": 99.8,                // Percentage of GPS data points
      "heart_rate": 98.5,               // Percentage of HR data points  
      "power_data": 97.2,               // Percentage of power data points
      "cadence_data": 96.8              // Percentage of cadence data points
    }
  }
}
```

### Missing Data Handling
```json
{
  "dataGaps": [
    {
      "dataType": "heart_rate",
      "startTime": 1245.6,
      "endTime": 1289.3,
      "duration": 43.7,
      "reason": "SENSOR_DISCONNECT"
    }
  ],
  "interpolated": [
    {
      "dataType": "elevation",
      "method": "LINEAR",
      "pointCount": 23,
      "confidence": 0.85
    }
  ]
}
```

This comprehensive data structure documentation enables developers to understand the full scope of available activity data and plan appropriate data handling and storage strategies.