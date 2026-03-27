---
status: testing
phase: 06-time-series-advanced-viz
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md]
started: 2026-03-26T15:30:00Z
updated: 2026-03-26T15:30:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 1
name: Year Slider in Sidebar
expected: |
  The sidebar shows a horizontal year slider between the navigation pills and the bottom info section. The slider range is 1995–2024 with tick marks every 5 years. A "Viewing: YYYY" label displays above the slider showing the currently selected year (defaults to 2024).
awaiting: user response

## Tests

### 1. Year Slider in Sidebar
expected: The sidebar shows a horizontal year slider between the navigation pills and the bottom info section. The slider range is 1995–2024 with tick marks every 5 years. A "Viewing: YYYY" label displays above the slider showing the currently selected year (defaults to 2024).
result: [pending]

### 2. Year Change Updates Country Data
expected: On the Country Exposure page, drag the year slider to a different year (e.g. 2010). The AG Grid table reloads with data for the selected year — scores and rankings should change visibly compared to 2024.
result: [pending]

### 3. Year Persists Across Pages
expected: Set the year slider to a non-default year (e.g. 2005). Navigate from Country Exposure to Product Risk using the sidebar nav. The slider remains at 2005 and the "Viewing: 2005" label is still shown.
result: [pending]

### 4. Country Drill-Down Trend Chart
expected: On Country Exposure, click a row to open the drill-down panel. Below the radar and bar charts, a 30-year trend chart appears showing a blue "Composite Score" line spanning 1995–2024. A vertical dashed line marks the currently selected year. The chart title includes the country and product names.
result: [pending]

### 5. Trend Chart Sub-Score Toggles
expected: On the country drill-down trend chart, the legend shows HHI (purple), Geo Risk (red), and Essentiality (green) entries that are initially hidden (greyed out in legend). Clicking a legend entry toggles that sub-score line on/off on the chart.
result: [pending]

### 6. Product Page Trend Chart
expected: On Product Risk, select a product (e.g. from the HS hierarchy). A trend chart section appears below the choropleth map showing the global average composite score over 1995–2024 with the same blue line + toggleable sub-scores pattern. A vertical dashed line marks the selected year.
result: [pending]

### 7. Sankey Flow Diagram
expected: On Product Risk with a product selected, a Sankey diagram appears showing trade flows from top-10 exporters (left) to top-10 importers (right). Link widths are proportional to trade value. Link colors indicate exporter geo risk (green = low, red = high). An "Other" category aggregates remaining countries.
result: [pending]

### 8. Network Graph
expected: On Product Risk with a product selected, a force-directed network graph appears showing countries as circular nodes connected by directed edges. Node sizes vary by trade volume (larger = more trade). Node colors indicate geo risk tier. The graph is interactive — nodes can be dragged.
result: [pending]

## Summary

total: 8
passed: 0
issues: 0
pending: 8
skipped: 0

## Gaps

[none yet]
