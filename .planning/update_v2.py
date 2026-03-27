"""Append v2.0 requirements to REQUIREMENTS.md and add phases 7-9 to ROADMAP.md."""
import pathlib

BASE = pathlib.Path("/Users/tom/Documents/git/dashboard_trade_crit_dep/.planning")

# ─── REQUIREMENTS.md ───────────────────────────────────────────────────────────

req_path = BASE / "REQUIREMENTS.md"
req_text = req_path.read_text()

# Check if v2.0 section already added
if "## v2.0 Milestone Requirements" in req_text:
    print("Requirements v2.0 section already exists, skipping")
else:
    v2_reqs = """
---

## v2.0 Milestone Requirements

Requirements for the Dashboard Redesign milestone (Phases 7–9).
Extends v1 requirements — v1 IDs are preserved and still tracked.

### Data Pipeline (v2.0)

- [ ] **DATA-06**: Download only HS92 + HS22 BACI revisions (not all 7), reducing raw data from ~45GB to ~17GB
- [ ] **DATA-07**: BACI product code and country code metadata CSVs extracted to data/raw/ for HS92 and HS22 during download

### Scoring (v2.0)

- [ ] **SCOR-06**: Remove tier-based essentiality classification (critical/important/standard); pipeline/essentiality.py renamed to pipeline/flags.py, producing a `flags` list (e.g., crm_listed, energy, pharma, food, semiconductor, strategic_mineral) per product
- [ ] **SCOR-07**: Use global_export_hhi as empirical substitutability proxy in composite score, replacing hand-crafted tier-derived essentiality_score: `composite = w1*hhi + w2*geo_risk + w3*global_export_hhi`
- [ ] **SCOR-08**: DuckDB schema updated atomically: products dim has `flags LIST(VARCHAR)` column; `essentiality_score` and `essentiality_tier` removed; dependency_scores fact renames `essentiality_score` → `substitutability_score`

### Country View (v2.0)

- [ ] **CNTV-08**: Country page hero stat cards: total products, count above risk threshold, highest-risk product name, max composite score
- [ ] **CNTV-09**: Country page scatter plot — HHI (x) vs global_export_hhi/substitutability (y), markers sized by log(import value), colored by composite score, top 200–500 products by composite score
- [ ] **CNTV-10**: Country page bilateral risk panel — top-10 source countries ranked by weighted risk contribution `SUM(supplier_share × composite_score)`, displayed as horizontal bar chart with flag icons
- [ ] **CNTV-11**: Weight slider label updated from "Essentiality" to "Substitutability" in country and product views

### Product View (v2.0)

- [ ] **PRDV-07**: Product page horizontal concentration bars: top exporters shown as horizontal bars with width proportional to market share %, colored by geopolitical risk
- [ ] **PRDV-08**: Product page flag badges displayed below product name — EU CRM listed (with year), energy, pharma, semiconductor, strategic mineral — sourced from flags column
- [ ] **PRDV-09**: Remove dash-cytoscape force-directed network graph from product page and requirements (VIZZ-06 superseded); Sankey diagram remains as primary flow visualization

### Time Series (v2.0)

- [ ] **TIME-04**: Score trend chart updated to display substitutability_score (was essentiality_score), with correct axis label and methodology tooltip
- [ ] **TIME-05**: Year sparklines in AG Grid product tables using custom clientside JS SVG cellRenderer (6-point polyline, 60×20px) — not AG Grid Enterprise sparklineOptions

### Dashboard Shell (v2.0)

- [ ] **DASH-06**: All "essentiality" terminology replaced with "substitutability" across dashboard UI, weight sliders, chart labels, and methodology page explanation text
"""
    req_text = req_text + v2_reqs
    req_path.write_text(req_text)
    print(f"REQUIREMENTS.md updated: added v2.0 section ({len(v2_reqs)} chars)")

# ─── ROADMAP.md ────────────────────────────────────────────────────────────────

road_path = BASE / "ROADMAP.md"
road_text = road_path.read_text()

if "### Phase 7:" in road_text:
    print("ROADMAP.md phases 7-9 already exist, skipping")
else:
    # Find the Progress section and insert before it
    phases_v2 = """
---

## v2.0 Milestone: Dashboard Redesign

Phases 7–9 continue from v1 execution order. Each phase builds on prior output.
v2.0 goal: empirical scoring, lean data pipeline, insight-first visualization.

- [ ] **Phase 7: Pipeline & Scoring Rework** - Replace tier scoring with global_export_hhi, slim BACI download to HS92+HS22, rebuild DuckDB schema
- [ ] **Phase 8: Dashboard Redesign** - Country page hero/scatter/bilateral, product page concentration bars/flags, remove network graph
- [ ] **Phase 9: Time Series** - Update trend charts for substitutability, add sparklines via custom SVG cellRenderer

### Phase 7: Pipeline & Scoring Rework
**Goal**: Pipeline downloads only HS92 + HS22 data, scoring uses empirical global_export_hhi as substitutability proxy, and DuckDB schema is fully updated with no tier columns
**Depends on**: Phase 5 (completed v1 codebase)
**Requirements**: DATA-06, DATA-07, SCOR-06, SCOR-07, SCOR-08
**Success Criteria** (what must be TRUE):
  1. Running the download step fetches only HS92 and HS22 files (~17GB total, not ~45GB)
  2. pipeline/flags.py produces a `flags` list per product; no essentiality_tier or essentiality_score in any pipeline output
  3. Composite score formula uses `w3 * global_export_hhi` as third component; weights still sum to 1.0 and can be adjusted
  4. DuckDB products dim has `flags` LIST column and `global_export_hhi`; dependency_scores has `substitutability_score`; no essentiality_tier column
  5. Full pipeline run completes end-to-end and dashboard launches without ColumnNotFound errors
**Plans**: TBD

Plans:
- [ ] 07-01-PLAN.md — TBD

### Phase 8: Dashboard Redesign
**Goal**: Country page is insight-first with hero cards, scatter plot, and bilateral risk panel; product page has concentration bars and flag badges; network graph removed; all "essentiality" labels replaced
**Depends on**: Phase 7
**Requirements**: CNTV-08, CNTV-09, CNTV-10, CNTV-11, PRDV-07, PRDV-08, PRDV-09, DASH-06
**Success Criteria** (what must be TRUE):
  1. Country page: 4 hero stat cards visible above the fold with correct values from DuckDB
  2. Country page: scatter plot renders top-200 products with HHI (x) vs substitutability (y), sized by import value
  3. Country page: bilateral risk panel shows top-10 source countries as horizontal bars, ranked by weighted risk contribution
  4. Product page: concentration bar chart renders top exporters with share % bars colored by geo risk
  5. Product page: flag badges displayed for applicable products (EU CRM, energy, pharma, etc.)
  6. Network graph and dash-cytoscape removed; no import errors on startup
  7. Zero occurrences of "essentiality" in UI-visible text (slider labels, chart titles, cards)
**Plans**: TBD

Plans:
- [ ] 08-01-PLAN.md — TBD

### Phase 9: Time Series
**Goal**: Score trend charts show substitutability instead of essentiality, and AG Grid product tables have year sparklines
**Depends on**: Phase 8
**Requirements**: TIME-04, TIME-05
**Success Criteria** (what must be TRUE):
  1. Score trend line chart labels and tooltip show "Substitutability" not "Essentiality"
  2. AG Grid product tables have a "Trend" column with SVG sparklines (6 data points, 60×20px)
  3. Sparklines render without AG Grid Enterprise errors in browser console
**Plans**: TBD

Plans:
- [ ] 09-01-PLAN.md — TBD

"""
    # Insert before the ## Progress section
    if "## Progress" in road_text:
        road_text = road_text.replace("## Progress", phases_v2 + "## Progress", 1)
    else:
        road_text = road_text + phases_v2

    # Update Progress table to include v2.0 phases
    progress_addition = """| 7. Pipeline & Scoring Rework | TBD | Not started | - |
| 8. Dashboard Redesign | TBD | Not started | - |
| 9. Time Series (v2) | TBD | Not started | - |
"""
    # Append before the closing line
    if "---\n*Roadmap created:" in road_text:
        road_text = road_text.replace(
            "---\n*Roadmap created:",
            progress_addition + "\n---\n*Roadmap created:",
            1
        )
    elif "*Roadmap created:" in road_text:
        road_text = road_text.replace(
            "*Roadmap created:",
            progress_addition + "\n*Roadmap created:",
            1
        )

    road_path.write_text(road_text)
    print(f"ROADMAP.md updated: added phases 7-9 ({len(phases_v2)} chars)")

print("Done.")
