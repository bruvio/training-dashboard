# Garmin Connect Local Dashboard — PRP (Project Requirements & Plan)

> **Goal:** Build a private, local-first Python dashboard that reads your Garmin activities (FIT/TCX/GPX) from a folder or a GarminDB SQLite database and lets you browse by month/week, select a session, and visualize map, pace, power, heart rate, and other metrics.

---

## 1) Objectives & Outcomes

- **Single-pane dashboard** to explore all activities with:
  - Calendar filtering (month/week/day range) and text filters (sport/type).
  - **Session details** page with:
    - **Route map** (GPS track).
    - **Time-series charts**: pace, cadence, HR, power, elevation, temperature.
    - **Summary metrics**: distance, moving time, avg/max pace/HR/power, training load-like metrics where derivable.
- **Local ingest** from a directory of `.fit`, `.tcx`, `.gpx` files using open-source parsers.
- Optional **direct read** from an existing **GarminDB** SQLite file.
- Production-quality structure (CLI importer, reproducible env, tests, logging).

**Definition of Done (high-level)**  
Selecting any activity from the calendar populates a details view with map + synchronized charts for pace, HR, power (where available) and shows computed summary stats. All data is local.

---

## 2) Success Criteria / Acceptance Tests

- **Calendar views**: Can toggle **Month** and **Week**. Selecting a date range filters the activity list.
- **Activity list**: Shows key columns (date/time, sport, distance, duration, avg HR, avg pace, power if present). Sort & search work.
- **Details view**:
  - Map renders the full GPS polyline (FIT/TCX/GPX) accurately.
  - Charts render **pace**, **power**, **HR**, **elevation** vs time or distance.
  - Hover/crosshair shows synchronized values across charts.
- **Import**: Running `gd-import /path/to/activities` parses new files, de-duplicates by activity id+start time, and persists to SQLite.
- **GarminDB interop**: When pointed at an existing `garmin.db`, activities are readable and displayed.
- **Performance**: 5,000+ activities load in < 3s for calendar/list view (cached), activity detail charts render in < 2s on a modern laptop.
- **Testing**: Unit tests for parsers, derived metrics, and dedup logic; smoke test for UI routing.

---

## 3) Scope

### In-Scope
- Local-only **Python** app (no cloud dependency).
- **Dash** web UI (or **Panel** alternative) + **Plotly** charts + **dash-leaflet** (or **folium**) for maps.
- Parsing **FIT** via [`fitparse`](https://github.com/dtcooper/python-fitparse), **TCX** via `tcxparser` (or lxml), **GPX** via `gpxpy`.
- Optional **GarminDB** ingestion/interop via [`GarminDB`](https://github.com/tcgoetz/GarminDB).
- SQLite storage (via SQLAlchemy) with simple schema (Activities, Laps, Samples, RoutePoints).

### Out of Scope (v1)
- Authentication to Garmin’s private APIs (may violate ToS).  
  Use **official export** or **GarminDB** sync.
- Training load/VO2max modeling beyond simple derived metrics.
- Multi-user auth and remote deployment.

---

## 4) Assumptions & Constraints

- **Local-first**; runs on macOS/Linux/Windows with **Python ≥ 3.10**.
- You have legal rights to the data. Respect **Garmin Connect ToS** (avoid scraping).
- GPS coordinates exist for most outdoor activities; indoor workouts may lack route data.
- Power/HR may be absent in some sessions — charts must gracefully handle missing series.

---

## 5) Key Design Decisions

- **UI Framework**: **Dash** chosen for rich, Python-native, reactive components; alternative: **Panel** (Bokeh) if desired.
- **Charts**: **Plotly** for interactivity and synchronized hover.
- **Maps**: Preferred **dash-leaflet** for native Dash integration; acceptable fallback is **folium** (static-ish) inside an iframe.
- **Storage**: **SQLite** (file: `garmin_dashboard.db`) via **SQLAlchemy** for portability and speed.
- **Ingestion**: Separate CLI (`gd-import`) scans folders, parses files, normalizes data, computes derived metrics, and writes to DB.

---

## 6) Architecture Overview

```mermaid
flowchart LR
  subgraph Input
    A[Local folder
FIT/TCX/GPX] -->|parse| N[Normalizer]
    B[GarminDB SQLite] -->|read| N
  end

  N -->|SQLAlchemy| D[(SQLite: garmin_dashboard.db)]

  subgraph App (Dash)
    UI[Calendar + Filters + Table] --> API[Query Layer]
    API --> D
    UI --> DET[Details View]
    DET --> MAP[Map (dash-leaflet)]
    DET --> CH1[Pace/HR/Power/Elev
(Plotly)]
  end
```

---

## 7) Data Model (SQLite)

### Tables
- **activities**
  - `id` (PK), `source` (fit/tcx/gpx/garminDB), `external_id` (from file/garmin), `sport`, `sub_sport`
  - `start_time_utc`, `local_tz`, `elapsed_time_s`, `moving_time_s`
  - `distance_m`, `avg_speed_mps`, `avg_pace_s_per_km`, `avg_hr`, `avg_power_w`, `elevation_gain_m`, `elevation_loss_m`
  - `file_path`, `ingested_on`
- **laps**
  - `id` (PK), `activity_id` (FK), `index`, `start_time_utc`, `elapsed_time_s`, `distance_m`, `avg_hr`, `avg_power_w`
- **samples** (time series; might be large → indexed)
  - `id` (PK), `activity_id` (FK), `t_s` (seconds from start) or `timestamp`
  - `lat`, `lon`, `alt_m`, `hr`, `power_w`, `cadence_spm/rpm`, `speed_mps`, `temp_c`
- **route_points** (thin geometry for map; can be derived from samples)
  - `id` (PK), `activity_id` (FK), `seq`, `lat`, `lon`, `alt_m`

**Indexes**  
- `activities(start_time_utc)`, `samples(activity_id, t_s)`, `route_points(activity_id, seq)`.

---

## 8) Ingestion & Normalization

### CLI: `gd-import`
- Recursively scan for `*.fit`, `*.tcx`, `*.gpx`.
- For each file:
  1. **Identify** activity (hash + start_time) to avoid duplicates.
  2. **Parse** with appropriate parser:
     - FIT → `fitparse`
     - TCX → `tcxparser` (or lxml)
     - GPX → `gpxpy`
  3. **Extract**: metadata (sport, start time), summary metrics, and time series.
  4. **Derive**:
     - Pace from speed (`pace = 1000 / speed_mps` → sec/km; guard speed=0).
     - Moving time (exclude samples with speed below threshold).
     - Elevation gain/loss (smoothed).
  5. **Persist** into DB.

- **GarminDB path**: If provided `--garmin-db /path/garmin.db`, read directly from its schema and map to our tables.

**Idempotency**: Skip if `(external_id,start_time)` already present.  
**Logging**: structured logs with counts, parse errors, skipped files.

---

## 9) Dashboard UX

### A) Calendar & Filters
- **DatePickerRange** (Dash) with **Month/Week** toggle.
- Sport/type filter (Run, Ride, Swim, Strength, Other).
- Free-text search (title/notes if available).

### B) Activity Table
- Paginated, sortable **DataTable** with key metrics.
- Clicking a row navigates to the **Details** route (`/activity/<id>`).

### C) Details View
- **Map** (dash-leaflet): route polyline, start/finish markers, optional colored pace segments.
- **Charts** (Plotly):
  - Pace (sec/km) vs distance or time (smoothed).
  - HR (bpm), Power (W), Cadence, Elevation (m).
- **Sync cursor/hover** across charts; display exact values + timestamp.
- **Summary panel**: distance, moving time, avg/max pace/HR/power, elevation gain.

---

## 10) Tech Stack

- **Core parsing**: `fitparse`, `gpxpy`, `tcxparser`
- **Interop**: `GarminDB`
- **UI**: `dash`, `dash-bootstrap-components`, `dash-leaflet`, `plotly`
- **Data**: `pandas`, `numpy`, `sqlalchemy`, `sqlite`
- **Utilities**: `pyyaml`, `python-dateutil`, `typer` (for CLI), `rich` (logs)
- **Testing**: `pytest`
- **Env**: `pip-tools` or `poetry`

---

## 11) Configuration

`config.yaml` (example):

```yaml
data_dir: "/path/to/activities"
sqlite_path: "garmin_dashboard.db"
garmin_db_path: null  # set to a path to use an existing GarminDB SQLite
elevation_smoothing_window: 9
moving_speed_threshold_mps: 1.0
timezone: "Europe/London"
```

---

## 12) Security & Privacy

- Data stays **local**. No external upload.
- **No scraping** of Garmin Connect. Use official data export or GarminDB sync.
- Provide a **redaction** option to hide exact coordinates (rounding/jitter) for privacy when sharing screenshots.

---

## 13) Performance Considerations

- Use **chunked inserts** for samples.
- Cache activity list query results.
- Downsample series for chart display (RDP or rolling window) when > 50k points.
- Lazy-load samples only on the details view.

---

## 14) Error Handling

- Per-file try/catch with clear reasons (unsupported message, corrupt file).
- Validation for mandatory fields (start time, at least one metric or GPS).
- UI warnings for missing series (e.g., “No power data available”).

---

## 15) Directory Layout

```
garmin-dashboard/
├─ app/
│  ├─ __init__.py
│  ├─ dash_app.py              # Dash UI + callbacks
│  ├─ views/
│  │  ├─ calendar.py
│  │  ├─ activity_table.py
│  │  └─ activity_detail.py
│  ├─ components/
│  │  ├─ charts.py             # Plotly figure builders
│  │  └─ map.py                # dash-leaflet helpers
│  └─ data/
│     ├─ db.py                 # SQLAlchemy models/session
│     └─ queries.py
├─ ingest/
│  ├─ importer.py              # parse + normalize + persist
│  ├─ fit_parser.py
│  ├─ tcx_parser.py
│  ├─ gpx_parser.py
│  └─ garmin_db_reader.py
├─ cli/
│  └─ gd_import.py             # Typer CLI entrypoint
├─ tests/
├─ config.yaml
├─ requirements.in / pyproject.toml
├─ README.md
└─ Makefile
```

---

## 16) Milestones

- **M1 — Ingest (2–3 days):** parsers, DB schema, dedup, CLI import, basic tests.
- **M2 — Core UI (3–4 days):** calendar filters, activity table, routing.
- **M3 — Details View (3–5 days):** map + charts + synchronized hover + summary.
- **M4 — Polish (2–3 days):** caching, downsampling, error messages, docs.

---

## 17) Deliverables

- Working **Dash app** (`python -m app.dash_app`) reading from SQLite.
- **CLI importer** `gd-import` to build/refresh DB from local files or GarminDB.
- **Tests** + **README** + **Makefile** (dev tasks).
- This **PRP** document.

---

## 18) Stretch Goals

- Year heatmap (training volume) with **cal-plot-like** view.
- Export selected session to **CSV/Parquet**.
- Power/HR zones distribution.
- Swim lap splits and stroke type summaries.
- Segment coloring by pace/power on the map.
- GPX export of any FIT-only activity.

---

## 19) Acceptance Checklist (tick to ship v1)

- [ ] Importer populates SQLite from sample FIT/TCX/GPX set.
- [ ] Calendar filters list to expected activities.
- [ ] Selecting an activity shows route + charts + summary.
- [ ] Missing series handled gracefully.
- [ ] README documents setup and usage.
- [ ] Basic unit tests pass in CI.

---

## 20) Getting Started (dev quickstart)

```bash
# create env
python -m venv .venv && source .venv/bin/activate
pip install -U pip pip-tools
pip-compile -o requirements.txt requirements.in
pip install -r requirements.txt

# import data
python -m cli.gd_import /path/to/activities --garmin-db /optional/path/garmin.db

# run app
python -m app.dash_app
```

---

## 21) License

This project is intended for **personal use** with your own exported Garmin data.  
Follow all applicable **terms of service** and local laws.
