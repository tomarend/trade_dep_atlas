# Feature Research

**Domain:** Trade dependency analytics dashboard
**Researched:** 2026-03-17
**Confidence:** HIGH

## Competitive Landscape Summary

Existing tools operate along a spectrum from raw trade data browsers to analytical dashboards:

| Tool | Focus | Strengths | Gap This Project Fills |
|------|-------|-----------|----------------------|
| **World Bank WITS** | Raw bilateral trade statistics, tariffs, NTMs | Broadest data coverage, simulation tools | No dependency scoring, no risk overlay, no vulnerability framing |
| **OEC (oec.world)** | Trade visualization + economic complexity | Beautiful treemaps, network viz, complexity indices, product space | Complexity ≠ vulnerability; no geopolitical risk; no concentration metrics |
| **Harvard Atlas** | Economic complexity research visualization | Product space, growth projections, academic rigor | Research-output tool, not risk-assessment; no supply concentration analysis |
| **EU RMIS** | Critical raw materials supply risk | Material flow analysis, supply risk methodology, country/material profiles | EU-only perspective, limited to ~70 candidate materials, not bilateral HS6 |
| **resourcetrade.earth** | Natural resource trade flows (Chatham House) | Sankey-like flows on map, clean UX, resource focus | Descriptive flows only, no risk scoring, limited to natural resources |
| **EC Access2Markets** | EU trade statistics + market access info | HS code search, tariff lookup, regulatory requirements | Trade facilitation tool, not analytical; no dependency/risk framing |

**Key insight:** No existing tool combines bilateral trade concentration (HHI), geopolitical risk scoring, and product essentiality into a unified vulnerability metric at HS6 granularity across all countries. This is unoccupied territory.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that users of trade analytics dashboards take for granted. Missing any of these makes the product feel incomplete or amateur.

| # | Feature | Why Expected | Complexity | Notes |
|---|---------|--------------|------------|-------|
| T1 | **Country selector with search** | Every trade tool starts with "pick a country"; WITS, OEC, Atlas all have this as primary entry point | Low | Dropdown with search/autocomplete, ~200 countries. ISO codes + names. Must handle name variants (e.g., "Korea, Rep." vs "South Korea") |
| T2 | **Product selector with HS hierarchy** | HS classification is universal in trade analytics; users expect to drill HS2→HS4→HS6 | Medium | Hierarchical selector with section/chapter/heading/subheading labels. ~5,000 HS6 products need good UX (tree or cascading dropdown) |
| T3 | **Ranked product vulnerability table** | Core value prop — "which products is this country most dependent on?" Must be a sortable, scannable table | Low | Sortable by composite score, HHI, geo risk, essentiality. This is the bread and butter of the Country→Products view |
| T4 | **Ranked country exposure table** | Inverse view — "which countries are most exposed for this product?" Also core | Low | Product→Countries view. Same sorting/filtering as T3 |
| T5 | **Time series charts** | Every reference tool (WITS, OEC, Atlas, resourcetrade.earth) shows evolution over time; users expect temporal context | Medium | Line charts showing score evolution over available BACI years (~20 years). Plotly line/area charts. Must handle missing data gracefully |
| T6 | **Choropleth world map** | Geographic context is table stakes for any international data dashboard. OEC, WITS, resourcetrade.earth all have maps | Medium | Color-coded by dependency score or sub-metric. Country→Products view: map of suppliers colored by risk. Product→Countries view: map of importers colored by exposure |
| T7 | **Composite dependency score display** | The product's core metric — must be prominently displayed, explained, and decomposable | Low | Show composite + 3 sub-scores (HHI, geo risk, essentiality). Visual decomposition (e.g., stacked bar or gauge). Tooltip explaining each. Users must trust the score, so transparency matters |
| T8 | **Score methodology explanation** | EU RMIS, Harvard Atlas, and OEC all have glossaries/methodology pages. Analytical credibility requires it | Low | Static page or expandable panel explaining HHI formula, risk index sources, essentiality classification. Links to data sources (BACI, Freedom House, etc.) |
| T9 | **Supplier breakdown for a product-country pair** | "Country X imports Product Y — from whom exactly?" Drilling into the bilateral flows behind a score | Medium | Bar chart or table showing top suppliers, their share %, and individual risk scores. This is what turns an abstract score into actionable intelligence |
| T10 | **Data freshness indicator** | Users need to know what years they're looking at, especially with retrospective data like BACI | Low | Header showing latest data year, range of available years |
| T11 | **Responsive data tables with export** | WITS and OEC both offer CSV/data download. Analysts expect to take data out | Low | CSV export of visible table data. Not bulk download of raw BACI — just the computed metrics shown on screen |
| T12 | **Loading states and performance** | Pre-computed data should feel instant; users abandon slow dashboards | Low | Skeleton loaders, progress indicators. Target <1s for view transitions given pre-computed data |

### Differentiators (Competitive Advantage)

Features that no single existing tool provides. These justify this dashboard's existence.

| # | Feature | Value Proposition | Complexity | Notes |
|---|---------|-------------------|------------|-------|
| D1 | **Composite vulnerability scoring (HHI + geo risk + essentiality)** | No existing tool combines these three dimensions. EU RMIS does supply risk + economic importance for ~70 materials; this does it for ALL 5,000 HS6 products across ALL countries | High | Core algorithmic differentiator. Must be well-calibrated — academic rigor matters for portfolio credibility. Weight tuning (slider or preset profiles) would add power |
| D2 | **Geopolitical risk layer on trade flows** | WITS/OEC show trade volumes but never flag that 80% of supply comes from sanctioned or poorly-governed states | High | Requires maintained sanctions lists + governance indices (Freedom House, V-Dem, World Governance Indicators). The "so what" that turns trade data into intelligence |
| D3 | **Sankey diagram: supplier→importer flows** | resourcetrade.earth has flow visualization but only for natural resources and without risk coloring. Sankey with risk-colored flows is unique | High | Show flows from suppliers to an importer for a product, width = trade share, color = geopolitical risk of supplier. Plotly Sankey with custom styling. Visually striking portfolio piece |
| D4 | **Network graph of trade dependencies** | OEC's product space shows product relatedness; this shows supplier-importer dependency networks with risk encoding. Different concept, equally visual | High | Force-directed graph: nodes = countries, edges = trade flows, color/size = risk/volume. Impressive for portfolio, complex to make readable. Consider limiting to top-N suppliers to avoid hairball |
| D5 | **Dual entry points (Country→Products AND Product→Countries)** | Most tools are country-first or product-first. Supporting both perspectives with the same scoring framework doubles utility | Medium | Two landing views with cross-linking. "Germany depends on China for rare earths" (country view) ↔ "Rare earths are concentrated in China" (product view). Deep-linking between them |
| D6 | **Product essentiality classification** | No tool systematically rates how critical each HS6 product is (energy, pharma, food, semiconductors, CRMs score higher). EU RMIS does this only for ~70 raw materials | Medium | Curated essentiality tiers (critical/important/standard) with transparent methodology. Draws from EU CRM lists, energy/pharma/food/semiconductor categorization |
| D7 | **Score decomposition visualization** | Show WHY a product scores high: is it concentration? geopolitical risk? essentiality? Radar chart or stacked bar per product | Low | Radar/spider chart for a single product-country pair. Allows users to distinguish "concentrated but friendly" from "diverse but hostile" from "concentrated AND hostile" |
| D8 | **Year-over-year trend sparklines in tables** | Tables with inline sparklines (à la Edward Tufte) showing 20-year trend next to current score. No trade dashboard does this well | Medium | Miniature line charts embedded in table cells. Shows trajectory at a glance without clicking through to time series view |
| D9 | **Animated temporal evolution** | Slider or play button to animate dependency changes over time on the map or charts. Hans Rosling / Gapminder style | Medium | Year slider with play/pause animating choropleth map or scatter plot. Visually compelling for portfolio showcase. Plotly has animation frames support |
| D10 | **"What changed?" alerts / highlights** | Surface products where dependency score increased significantly year-over-year. "Emerging vulnerabilities" panel | Medium | Computed from time-series diff. E.g., "Lithium dependency for Germany: score rose from 0.4 to 0.8 over 5 years". Adds narrative to raw data |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem natural to build but would hurt the project through scope explosion, misleading results, or architectural complexity.

| # | Feature | Why Requested | Why Problematic | Alternative |
|---|---------|---------------|-----------------|-------------|
| A1 | **Tariff simulation / trade policy modeling** | OEC has tariff simulator; policy analysts love "what-if" | Completely different analytical domain. Requires tariff schedules, gravity models, elasticity estimates. Months of additional work for questionable accuracy | Link to WITS simulation tool or OEC tariff simulator. Stay in your lane: vulnerability analysis, not policy simulation |
| A2 | **Predictive forecasting of dependency scores** | "Where will dependency be in 5 years?" is a natural question | BACI is retrospective annual data. Extrapolation from trade data alone is unreliable — geopolitics, technology, and policy all cause non-linear shifts. Harvard Atlas does growth projections but backed by deep academic methodology | Show historical trend and let users draw conclusions. Label clearly as descriptive analytics. Maybe add simple trend arrows (↑↓→) but never point forecasts |
| A3 | **Subnational / regional trade data** | OEC 5.0 added subnational data for 30+ countries | Requires entirely different data sources per country. BACI is country-level. Would 10x data complexity for marginal value in a dependency context | Country-level analysis is the right granularity for supply chain dependency. Subnational is noise for this use case |
| A4 | **Company-level / Bill of Lading data** | OEC has "Company Explorer" for US BoL data | Proprietary data, enormous volume, different analytical framework. HS6 country-level analysis is the right abstraction for structural dependency | Link to OEC or ImportGenius for users who want firm-level drill-down |
| A5 | **Export dependency analysis** | "Which countries depend on exporting X?" is a valid question | PROJECT.md explicitly scopes to import vulnerability. Export dependency is a different (less urgent) policy question. Adding it doubles every view | Mark as v2+ consideration. The import vulnerability story is strong enough alone |
| A6 | **User accounts, saved views, sharing** | Dashboards often have "save my analysis" features | For a portfolio piece, adds auth complexity (OWASP surface), database requirements, and session management for zero analytical value | Shareable URL state (filters encoded in URL params). No auth needed. Copy-paste link to share a specific view |
| A7 | **Natural language / AI chat interface** | OEC added an AI chat feature. Trendy | Distraction from core analytical UX. LLM integration adds API costs, latency, and unreliable responses about nuanced trade data. Impressive as a gimmick, unreliable as a tool | Build excellent filtering and drill-down UX instead. The structured interface IS the interface |
| A8 | **Real-time data updates / streaming** | "Is this data live?" | BACI is annual retrospective data with ~2 year lag. No real-time trade data exists at this granularity. Pretending otherwise misleads users | Show latest BACI vintage prominently. Annual update pipeline is the right cadence |
| A9 | **Custom formula / scoring builder** | "Let me define my own weighting" | Power-user feature that makes the default experience worse (paradox of choice) and creates untested score combinations. Calibrating the default well is more valuable | Offer 2-3 preset profiles (e.g., "Security focus" = high geo-risk weight, "Economic focus" = high essentiality weight, "Balanced" = equal) instead of free-form sliders |
| A10 | **Multi-language support / i18n** | International users, EU-style multilingual | Significant string management overhead. Product names in HS6 are already English-standardized. Portfolio piece targets English-speaking audience | English only. Country names handle gracefully (display native names optionally) |

---

## Feature Dependencies

```
T1 (Country selector) ──┐
                         ├──→ T3 (Product vulnerability table) ──→ T9 (Supplier breakdown)
T2 (Product selector) ──┘                                       ──→ D7 (Score decomposition)

D1 (Composite scoring) ──→ T3, T4, T5, T6, T7 (all views depend on the scoring pipeline)
                       ──→ D2 (geo risk is a sub-component)
                       ──→ D6 (essentiality is a sub-component)

D1 (Composite scoring) ──→ D3 (Sankey needs scores for coloring)
                       ──→ D4 (Network needs scores for encoding)
                       ──→ D8 (Sparklines need historical scores)
                       ──→ D9 (Animation needs full time series)
                       ──→ D10 ("What changed?" needs time-series diff)

T5 (Time series) ──→ D9 (Animation builds on time series)
                 ──→ D10 ("What changed?" needs time-series data)

T6 (Choropleth) ──→ D9 (Animated map extends static map)

D5 (Dual entry points) depends on T3 + T4 being implemented with cross-linking
```

**Critical path:** D1 (scoring pipeline) → T3/T4 (core tables) → T5/T6 (charts/maps) → D3/D4 (advanced viz)

The scoring pipeline (D1 + D2 + D6) is the foundation. Nothing visual works without it.

---

## MVP Definition

### Launch With (v1) — "Analytically complete, visually impressive"

Everything needed to tell the dependency story and showcase visualization craft:

| Feature | Rationale |
|---------|-----------|
| D1: Composite vulnerability scoring | Core differentiator. The product IS the scoring |
| D2: Geopolitical risk layer | Without this, it's just another HHI calculator |
| D5: Dual entry (Country→Products, Product→Countries) | Both perspectives needed for complete story |
| D6: Product essentiality classification | Critical for surfacing the products that matter |
| T1-T4: Selectors + ranked tables | Basic navigation and data display |
| T5: Time series charts | Temporal evolution is expected |
| T6: Choropleth map | Geographic context is essential for a trade dashboard |
| T7: Composite score display + decomposition | Users need to see and trust the score |
| T8: Methodology explanation | Analytical credibility |
| T9: Supplier breakdown | Drilling into the "why" behind a score |
| T10-T12: Freshness, tables, performance | Baseline quality |
| D7: Score decomposition (radar/spider) | Simple to build, high insight value |
| D3: Sankey diagram | Portfolio visual showpiece. High wow-factor |

### Add After Validation (v1.x) — "Polish and depth"

Features that enhance the experience but aren't needed for initial impact:

| Feature | Rationale |
|---------|-----------|
| D4: Network graph | Complex to make readable; adds after Sankey proves the flow-viz value |
| D8: Sparklines in tables | Tufte-quality polish; adds after core tables are proven |
| D9: Animated temporal evolution | Impressive but requires tuning; adds after static time series works |
| D10: "What changed?" alerts | Requires time-series diff logic; natural v1.x addition |
| A6 (modified): Shareable URL state | Encode view state in URL params for sharing without auth |
| A9 (modified): 2-3 preset scoring profiles | E.g., "Security", "Economic", "Balanced" weight presets |

### Future Consideration (v2+) — "Expansion if validated"

| Feature | Rationale |
|---------|-----------|
| A5: Export dependency analysis | Valid but doubles scope; only after import story is solid |
| Comparison mode (country vs country) | "How does Germany's risk profile compare to France?" |
| Sector-level aggregation view | Roll up HS6 to sector groupings (automotive, electronics, pharma) |
| API for programmatic access | If the scoring methodology gains traction |
| Embeddable chart widgets | For analysts to embed in reports |
| PDF / report generation | "Generate a country dependency briefing" |

---

## Sources

- EU RMIS (Raw Materials Information System): https://rmis.jrc.ec.europa.eu/ — country profiles, material profiles, supply risk methodology
- EU Critical Raw Materials methodology: https://single-market-economy.ec.europa.eu/sectors/raw-materials/areas-specific-interest/critical-raw-materials_en — economic importance + supply risk framework
- World Bank WITS: https://wits.worldbank.org/ — trade statistics, tariffs, simulation tools, GVC analysis
- OEC (Observatory of Economic Complexity): https://oec.world/ — trade visualizations, economic complexity, treemaps, network graphs, tariff simulator
- Harvard Atlas of Economic Complexity: https://atlas.hks.harvard.edu/ — product space, growth projections, complexity research visualization
- resourcetrade.earth (Chatham House): https://resourcetrade.earth/ — natural resource flow visualization
- EC Access2Markets: https://trade.ec.europa.eu/access-to-markets/en/statistics — EU trade statistics
- OECD Data Explorer: https://data-explorer.oecd.org/ — trade data, trade facilitation indicators
