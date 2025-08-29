# Dash Leaflet

## Key Features
- Light wrapper around React-Leaflet
- Follows React-Leaflet API naming conventions
- Designed for interactive mapping in Dash applications

## Installation
```bash
pip install dash
pip install dash-leaflet
```

## Basic Usage Example
```python
from dash import Dash
import dash_leaflet as dl

app = Dash()
app.layout = dl.Map(
    dl.TileLayer(), 
    style={'height': '50vh'}, 
    center=[56, 10], 
    zoom=6
)

if __name__ == '__main__':
    app.run_server()
```

## Documentation
- Full documentation available at https://dash-leaflet.com
- Interactive example gallery
- Note: Version 1.0.0 introduced breaking changes

## Support
- Ask questions on StackOverflow using the "dash-leaflet" tag
- GitHub issues are for bug reports only

## Development
- Requires Python 3.12 and uv
- Clone repository
- Create virtual environment
- Install dependencies via uv and npm

## Key Characteristics
- Open source (MIT License)
- Primarily written in TypeScript (84.1%) and Python (12.6%)
- Active development with 234 stars and 45 forks

Recommended for developers seeking an interactive mapping solution within Dash applications.