# Python FITparse

## Library Overview
- Python library for parsing ANT/Garmin `.FIT` files
- Supports parsing binary fitness activity data files
- Currently seeking a new maintainer

## Key Features
- Parses various message types in FIT files (record, device_info, file_creator, event)
- Provides command-line tool `fitdump` for file conversion
- Supports extracting detailed activity data with units

## Installation
```
pip install fitparse
```

## Basic Usage Example
```python
import fitparse

# Load FIT file
fitfile = fitparse.FitFile("my_activity.fit")

# Iterate through "record" messages
for record in fitfile.get_messages("record"):
    for data in record:
        # Print data with optional units
        if data.units:
            print(f" * {data.name}: {data.value} ({data.units})")
        else:
            print(f" * {data.name}: {data.value}")
```

## Command-Line Usage
```
fitdump --help  # Shows available options for converting FIT files
```

## Notable Characteristics
- Supports component fields and compressed timestamp headers
- Aims to provide a clean, generic parsing approach
- Ongoing development with plans for more robust type conversion

## Recommended Alternative
If experiencing issues, the README suggests using [fitdecode](https://github.com/polyvertex/fitdecode)

## Licensing
MIT License