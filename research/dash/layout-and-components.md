# Dash App Layout and Components

## Layout Fundamentals
- The `layout` describes the visual structure of a Dash application
- Composed of a hierarchical tree of components
- Can be a list of components (in Dash 2.17+)

## Key Component Types

### 1. Dash HTML Components (`dash.html`)
- Provides classes for all HTML tags
- Attributes like `style`, `class`, and `id` are set through keyword arguments
- Example: `html.H1('Hello Dash', style={'textAlign': 'center'})`

### 2. Dash Core Components (`dash.dcc`)
- Higher-level interactive components
- Includes dropdowns, graphs, markdown blocks
- Configurable through keyword arguments
- Generated using React.js

## Layout Structure Example
```python
app.layout = html.Div([
    html.H1('Title'),
    html.Div('Subtitle'),
    dcc.Graph(id='example-graph')
])
```

## Key Layout Principles
- Components are declarative
- `children` property is special and can contain strings, numbers, or nested components
- Styling can be done inline using dictionaries
- Supports camelCase for CSS properties (e.g., `textAlign`)

The documentation emphasizes creating flexible, interactive web applications using Python and these component libraries.