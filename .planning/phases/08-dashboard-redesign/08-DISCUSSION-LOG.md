# Phase 8: Dashboard Redesign — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27

---

## Todo Review

**Surfaced todo:** "Fix HS chapter headings in product selector"
**Resolution:** Reviewed and closed — resolved by Phase 7's authoritative BACI `product_codes_HS*.csv` mapping. Not folded into Phase 8.

---

## Area 1: Hero Cards (CNTV-08)

**Q: What is the risk threshold for "count above risk threshold"?**
Options presented: 0.5 (economic midpoint), 0.7 (existing), user-adjustable
*User selected: 0.7 — keep existing threshold*

**Q: Does the overview radar chart survive?**
Options presented: Keep it (complementary to scatter), Remove it (scatter makes it redundant)
Agent recommendation: Keep — geo risk dimension not in scatter, radar provides one-glance country profile
*User selected: Keep the radar chart*

---

## Area 2: Scatter Plot (CNTV-09)

**Q: Where does the scatter plot sit on the country page?**
Options presented: Between hero cards and AG Grid, Below AG Grid, Collapsed panel
*User selected: Between hero cards and AG Grid*

**Q: What happens when you click a scatter point?**
Options presented: Selects product in AG Grid, Tooltip only, Navigates to product page
*User selected: Tooltip only — scatter is read-only*

---

## Area 3: Bilateral Risk Panel (CNTV-10)

**Q: Where on the page does the bilateral panel sit?**
Options presented: Alongside scatter (side-by-side), Below scatter / above weight controls, Below AG Grid
*User selected: Below scatter, above weight controls*

**Q: Flag icons — emoji or flagcdn.com images?**
Options presented: Unicode emoji, flagcdn.com PNG, Agent's call
*User selected: flagcdn.com PNG images*

---

## Area 4: Product Page Layout (PRDV-07, PRDV-09)

**Q: Where does the concentration bar chart slot in?**
Options presented: Replace network graph position (bottom), Near top below summary cards, Between choropleth and Sankey
*User selected: Near top, below summary cards*

**Q: Color scale for geo risk on concentration bars?**
Options presented: Cool-to-hot gradient (consistent), Single-hue sequential (geo risk distinct encoding), Agent's call
*User selected: Cool-to-hot gradient — consistent with dashboard*

---

## Area 5: Terminology Replacement (DASH-06)

**Q: What happens to the About page "Essentiality" tab?**
Options presented: Full rewrite (rename + new formula + 8 flags), Minimal touch (rename + formula only), Remove tab
*User selected: Full rewrite*

**Q: AG Grid column formerly "Essentiality Tier" — what becomes it?**
Options presented: "Flags" (flags list), "Substitutability" (score value), Remove column
*Agent selected: "Flags" — direct successor to tier column, shows the flags list*
