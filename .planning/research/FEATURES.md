# Features Research — v2.0

**Milestone context:** Adding new features to existing dashboard. Focus on what changes vs what is carried forward.

## Feature Categories

### 1. Pipeline — Lean Download + BACI Metadata

**Table stakes:**
- Download only HS92 + HS22 (currently downloads all 7 revisions, ~45GB). Change: filter `discover_baci_urls()` by revision slug (`HS92`, `HS22`). Saves ~37GB.
- Use BACI's `product_codes_HS92_V*.csv` and `product_codes_HS22_V*.csv` for product descriptions (authoritative, per-revision). Replace hand-built `data/reference/hs_product_descriptions.csv`.
- Use BACI's `country_codes_V*.csv` for country ISO2/ISO3 mapping. Already partially used; make it primary source.

**Complexity:** Low. Pure data plumbing, no logic changes.

### 2. Scoring — Empirical Formula

**Table stakes:**
- Replace `w3 * essentiality_score` with `w3 * global_export_hhi` in `composite.py`.
- `global_export_- `global_export_- `global_export_- `global_export_- `global_export_- `global_export_- `global_st- `global_export_- `globaepurp- `global_export_- `global_export_- `global_export_- `global_export_- `global_export_- `global_export_- `global_sthhi- `global_export_-`comp- `global_export_- `global_export_- `globalport_hhi`

**Complexity:****Complexity:****Complexity:****Complexity:****Complexity:****Complexity:****Complexity:****Complexity:****Complexity:****Complexity:****Complexity:****C Flags

**Table stakes:**
- `flags` column on every product: comma-separated list of applicable labels, e.g. `"EU_CRM,Energy"` or `""`.
- Flag sources (from existing classification logic in `essentiali- Flag sources (from existing classification logic in `essentiali- Flag sources (from existing classification logiti- Flag sources (from existing classification logic in `esnergy` — HS2=27 (excluding 2716)
  - `F  - `F  - `F  - S4 in {3102,3103,3104,3105,2510,2809}
  - `Pharma_API` — HS2=29
  - `Food` — HS2 in 01-24
  - `Finished_Pharma` — HS2=30
  - `Semiconductor` — specific HS6 list (already in config)
- Rendered in UI as colored badges/chips (Dash `html.Span` with CSS class). No score impact.
- Filterable in AG Grid as text column.

**Complexity:** Low. The classification logic already exists in `essentiality.py`. Repurpose to produce a flags string instead of/alongside a score.

### 4. Country Page — Insight-First Redesign

**Table stakes — Hero Stats:**
- 3-4 stat cards: total critical products expos- 3-4 skiest singl- 3-4 stat cards: total critical products expos- 3-4 skiest singl- 3-4 stat cards: total critical products  bu- 3-4 stat cards: total critical products expos- 3-4 skiest singl- 3-4 stat cards: total critical products expos- 3-4 skiest singl- 3-4 stat cards: total critical products  bu- 3-4 stat cards: total critical products expos- 3-4 skiest singl- 3-4 stat cards: total criticaie- 3-4 stat cards: total critical products expos- 3-4  Size: - 3-4 stat cards: totach poi- 3-4 stat cards: total crhe- 3-4 stat cards: total criticqua- 3-4 stat cards: total critical products expos- 3-4 skiest Ho- 3-4 stat cards: total critical products expos- 3-4 skiest singl- 3-4 stat cards: total crduce overplotting
- New query needed: `get_- New query needed: `get_- New query needed: `get_- New query needed: `get_- New query needed: `get_- New query needed: `get_- New query needed: `g To- New query needed: `get_- New query needed: ppliers" narrative: top 5-10 countries by `SUM(supplier_share * composite_score)` for that importer
- Rendered as horizontal bars or ranked cards with: country name, flag emoji, N critical products, weighted risk score
- New query needed: `get_top_bilateral_risk(importer_iso3, year)` → (exporter_iso3, name, product_count, weighted_risk)

**Already exists (keep + restyle):** Choropleth, AG Grid table, cross-linking.

**Complexity:** Medium. Two new queries + two new chart components. Rest is restyling.

### 5. Product Page — Insight-First Redesign

**Table stakes — Concentration Bars:**
- Horizontal bar chart: top 10-15 exporters for the product, sorted by share %
- Color-encoded by geo-risk (red = high, green = low)
- `get_supplier_breakdown()` already exists, returns the right data
- Replaces or supplements the existing supplier table

**Table stakes — Sankey Diagram:**
- ALREADY IMPLEMENTED in `dashboard/pages/product.py` (lines 508-650). Top 10 exporters → top 10 importers.
- Needs: redesign of positioning/styling to fit new insight-first layout. Logic is sound.
- Query `get_trade_flows()` already exists in `data.py`.

**Table stakes — Flag Badges:**
- Show flags for the selected product as colored chips
- Query: `products` dim `flags` column (needs to be added in pipeline phase)

**Already exists (keep + restyle):** Choropleth o**Already exists (keep + restyle):** Choropleth o**Already exxity:** Low. Sankey already exists. Concentration bars = new `go.Bar` component. Flags = CSS badges.

### 6. Time Series

**Table stakes — Year Slider:**
- Was Phase 6 from v1 (planned but never- Was Phase 6 from v1 (planned but never- Was Phase 6 frbar updating `year-stor- Was .Store
- Already wired: `year-store` already exists in app from v1 partial work (check `app.py`)

**Table stakes — Trend Line Charts:**
- `get_score_trend()` already exi- `get_score_trend()` already exite, hhi, geo_risk, essentiality per year)
- Needs: update column name `essentiality_score` → `substitutability_score` (global_export_hhi)
- Multi-line chart with toggleable sub-scores
- Component alread- Compoally built in country page drill-down (`dashboard/pages/country.py:510`)

**Table stakes — Sparklines in Table Rows:**
- Mini 20-year trend for each product in the AG Grid table
- Implementation: custom AG Grid cell renderer with inline SVG (see STACK.md)
- Requires pre-computing normalized trend arrays and storing in DuckDB (or computing on the fly per product)
- Recommended: compute on page load for visible rows only (AG Grid virtualizes rows- R**HS92 footnote:**
- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `cr- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Stew.- Static `ht- Static `ht- Static `hder i- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `ht- Static `Features Deferred to v3
- Animated temporal choropleth (play/pause)
- HS22 snapshot toggle vs HS92 (- HS22 snapshot toggle vs HS92 (- HS22 snap"What changed?" year-over-year panel
- AG Grid Enterprise upgrade (sparklines, advanced filtering)
