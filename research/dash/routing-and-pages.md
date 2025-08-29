# Dash URL Routing and Multi-Page Applications

## Key Concepts for Multi-Page Dash Apps

### 1. URL Navigation Components
- `dcc.Location`: Represents browser address bar
- `dcc.Link`: Updates pathname without page refresh

### 2. Dash Pages (Version 2.5+) Simplification
- Automatically handles URL routing
- Requires three basic steps:
  1. Create page files in `/pages` directory
  2. Use `dash.register_page(__name__)` in each page
  3. Set `use_pages=True` in main app and include `dash.page_container`

### 3. Page Registration Options
- Automatically generates path from module name
- Can customize:
  - Path
  - Title
  - Name
  - Order of pages

### 4. Advanced Routing Features
- Support for:
  - Variable paths
  - Query string parameters
  - Redirects
  - Custom 404 pages
  - Meta tags for pages

### 5. Project Structure Options
- One page per file
- Flat project structure with separate callback and layout files

## Example Basic Multi-Page Structure
```python
app = Dash(__name__, use_pages=True)

app.layout = html.Div([
    dcc.Link('Page Links'),
    dash.page_container
])
```

The approach provides flexible, dynamic web application routing in Dash.