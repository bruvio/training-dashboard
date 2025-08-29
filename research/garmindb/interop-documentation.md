# GarminDB Interop Documentation

## Key Features
- Python scripts for parsing health data into SQLite databases
- Automatically download and import Garmin daily monitoring files
- Extract and store sleep, weight, and heart rate data
- Download and import activity files
- Generate daily, weekly, monthly, and yearly data summaries
- Graph data using Jupyter notebooks or command line
- Export activities as TCX files

## Installation Options

### 1. PyPI Release
- Requires Python 3.x
- Install via: `pip install garmindb`
- Copy and configure `GarminConnectConfig.json`

### 2. From Source
- Use Git to clone repository
- Run `make setup`
- Configure `GarminConnectConfig.json`
- Run `make create_dbs`

## Key Commands
- Initial data download: `garmindb_cli.py --all --download --import --analyze`
- Update data: `garmindb_cli.py --all --download --import --analyze --latest`
- Backup databases: `garmindb_cli.py --backup`

## Additional Features
- Supports Jupyter notebooks for data analysis
- Plugin system for expanding data processing capabilities
- Compatible with SQLite browsers like SQLite Studio

## Unique Aspects
- Retains downloaded JSON and FIT files
- Creates default database views for easier data browsing
- Developed primarily on macOS

## Interoperability Benefits
Recommended for users wanting comprehensive tracking and analysis of Garmin health and activity data with existing database files.