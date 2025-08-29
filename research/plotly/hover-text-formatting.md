# Plotly Hover Text and Formatting

## Key Hover Modes
1. "closest" (default): Single hover label for point directly under cursor
2. "x" or "y": Hover label for points at same x/y coordinate
3. "x unified" or "y unified": Consolidated hover label across traces

## Customization Options
- Control hover label appearance via `layout.hoverlabel`
- Customize hover text in Plotly Express using `hover_name` and `hover_data`
- Format hover labels with d3 formatting syntax
- Set background color, font size, and font family for hover labels

## Advanced Features
- Hover on subplots with `hoversubplots="axis"`
- Create unified hover titles with custom formatting
- Add specific data columns to hover tooltips

## Example customization
```python
fig.update_layout(
    hoverlabel=dict(
        bgcolor="white",
        font_size=16,
        font_family="Rockwell"
    )
)
```

The documentation provides comprehensive examples demonstrating these hover text capabilities across different chart types.