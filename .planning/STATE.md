---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Dashboard Redesign
status: planning
stopped_at: Requirements and roadmap defined — ready to plan phases
last_updated: "2026-03-26"
last_activity: 2026-03-26 — Roadmap and requirements updated for v2.0
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-26)

**Core value:** Instantly reveal which products make a country vulnerable due to concentrated, geopolitically risky import sources — and how that exposure has evolved over time.
**Current focus:** v2.0 — Pipeline + scoring rework, dashboard redesign, time series

## Current Position

Phase: Phase 7 (not started — planning)
Plan: —
Status: Requirements and roadmap defined, ready to plan phases 7-9
Last activity: 2026-03-26 — v2.0 milestone started, ROADMAP and REQUIREMENTS updated

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- No plans completed yet in v2.0

| Phase | Plans | Completed | Avg/Plan |
|-------|-------|-----------|---------|
| 7. Pipeline & Scoring Rework | TBD | — | — |
| 8. Dashboard Redesign | TBD | — | — |
| 9. Time Series (v2) | TBD | — | — |

Trend: —

*Updated after each plan execution*

## Decisions

- [Scoring]: Replace deterministic tier system (critical/important/standard) with global_export_hhi as substitutability proxy. Formula: `composite = w1*hhi + w2*geo_risk + w3*global_export_hhi`. global_export_hhi already computed in essentiality.py — just unused as score driver until now.
- [Scoring]: pipeline/essentiality.py renamed to pipeline/flags.py. Produces `flags: list[str]` instead of tier label. Retains `compute_global_export_hhi()` and `crm_listed_since`.
- [Data]: Download only HS92 + HS22 BACI revisions. HS92 covers full 1995-2024 time series. HS22 used for latest-year enriched product codes. All other revisions dropped (~28GB saved).
- [Data]: HS22 used for current-year display only; HS92 used for all time series (cross-year comparability). Footnote shown when HS22-only codes displayed.
- [Dashboard]: Layout redesigned to insight-first, visualization-forward. Country page: hero cards → scatter → bilateral panel → choropleth → grid. Product page: flags → concentration bars → Sankey → importer grid.
- [Dashboard]: Remove force-directed network graph (dash-cytoscape) — low insight density vs implementation cost. Sankey remains as primary flow visualization.
- [Viz]: Add scatter plot (HHI vs substitutability, colored by composite score, sized by import value). Concentration bars (exporter share). Bilateral risk panel (horizontal bars). Flag badges (EU CRM, energy, pharma, etc.).
- [Viz]: No AG Grid Enterprise sparklines — use custom clientside SVG cellRenderer (60×20px, polyline, 6 data points).

## Blockers / Open Questions

- BACI download deduplication: need to verify HS92 is downloaded before HS22 so HS92 wins for 2022-2024 overlap in ingest.py
- Governance index coverage: Taiwan, Kosovo, Palestine have no WGI data — handled in v1 with manual overrides, carry forward to v2.0
- DuckDB LIST(VARCHAR) column for flags: may require full DB rebuild (no ALTER TABLE support for list types)

## Session Continuity

Last session: 2026-03-26
Stopped at: Requirements and roadmap updated for v2.0 — next step is planning phases
Next step: `/gsd:discuss-phase 7` to plan Phase 7 (Pipeline & Scoring Rework)
