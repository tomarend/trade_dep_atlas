---
status: awaiting_human_verify
trigger: "The HS6 codes are somehow not correctly captured. In the country table it only says h ref blablabla and The product table is empty."
created: 2026-03-26T16:00:00.000Z
updated: 2026-03-26T16:20:00.000Z
---

## Current Focus

hypothesis: CONFIRMED — Two root causes found
test: Applied fixes and verified with tests
expecting: HS6 codes render as clickable links in country table; product page loads with data
next_action: Request human verification

## Symptoms

expected: HS6 product codes appear correctly in country table and product table is populated
actual: Country table shows "h ref blablabla" instead of HS6 codes; product table is empty
errors: None reported
reproduction: Look at the dashboard output
started: Unknown

## Eliminated

## Evidence

- timestamp: 2026-03-26T16:05
  checked: DuckDB database state
  found: Products table has 5679 rows with correct HS6 codes and descriptions. dependency_scores has data for 1995-2024.
  implication: Data is correctly stored — issue is in frontend rendering.

- timestamp: 2026-03-26T16:08
  checked: dash-ag-grid version
  found: dash-ag-grid 33.3.3 with Dash 4.0.0 — AG Grid 33 no longer renders HTML string cellRenderers as innerHTML
  implication: cellRenderer returning `<a href=...>` HTML string is shown as escaped text, explaining "h ref blablabla"

- timestamp: 2026-03-26T16:10
  checked: Default product selection for product page
  found: get_default_product() returns HS6 310410 (highest avg composite across ALL years), but it only exists in years 1995-2016. Dashboard defaults to year 2024, so get_importer_scores('310410', 2024) returns 0 rows.
  implication: Product page table is empty because default product has no data in the latest year.

- timestamp: 2026-03-26T16:15
  checked: Product page also has same cellRenderer pattern for country links
  found: product.py importer_name column uses same HTML-string cellRenderer
  implication: Both pages have the same cellRenderer issue

## Resolution

root_cause: |
  Two bugs:
  1. dash-ag-grid 33.3.3 cellRenderer HTML strings not rendered: The cellRenderer in country.py and product.py returns HTML template strings (`<a href=...>`), but AG Grid 33 treats cellRenderer function return strings as text content, not innerHTML. The raw HTML is displayed as escaped text ("h ref blablabla").
  2. get_default_product() selects wrong product: The query selects the HS6 with highest average composite_score across ALL years, but this product (310410) was concorded away after 2016 and has no data in the latest year (2024). The product page loads with this default and shows an empty table.
fix: |
  1. Created dashboard/assets/dashAgGridComponentFunctions.js with ProductLink and CountryLink React component renderers that create proper DOM `<a>` elements.
  2. Changed cellRenderer in country.py from HTML template to "ProductLink" component.
  3. Changed cellRenderer in product.py from HTML template to "CountryLink" component.
  4. Fixed get_default_product() in data.py to filter by latest year (WHERE year = max_year) so default product always has data.
verification: |
  - get_default_product() now returns 292244 (with 56 importer rows in 2024, vs 0 rows for old default 310410)
  - 80 tests pass (1 pre-existing georisk failure unrelated)
  - Component renderers will render proper clickable links in AG Grid 33
files_changed:
  - dashboard/assets/dashAgGridComponentFunctions.js
  - dashboard/pages/country.py
  - dashboard/pages/product.py
  - dashboard/data.py
