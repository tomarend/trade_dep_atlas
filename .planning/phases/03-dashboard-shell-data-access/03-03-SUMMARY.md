---
phase: 03-dashboard-shell-data-access
plan: 03
subsystem: ui
tags: [dockerfile, gunicorn, ui-polish, inter-font, mathjax, dash-bootstrap-components]

requires: [03-01, 03-02]
provides:
  - Dockerfile for production deployment (Python 3.12-slim, gunicorn, port 8050)
  - Visual polish: Inter font, dark sidebar, two-tone brand title, page-header pattern
  - Restructured Methodology page with labelled sections, formula boxes, interpretation rows
  - MathJax formula fix (subscript notation replaces \text{…\_…})
  - pyproject.toml packages.find fix so dashboard package installs correctly

affects: [all future phases that extend dashboard pages]

tech-stack:
  added: [gunicorn>=25.1.0]
  patterns:
    - Google Fonts Inter loaded via external_stylesheets in app.py
    - Brand title uses two-tone spans (.brand-dim / .brand-accent) inside .brand-title
    - About page uses .method-section / .method-label / .formula-box pattern for structured content
    - MathJax formulas use subscript notation (R_{\text{sub}}) not \text{word\_word}

key-files:
  created:
    - Dockerfile
  modified:
    - dashboard/app.py (Inter font in external_stylesheets)
    - dashboard/layout.py (two-tone brand spans, g-0 row)
    - dashboard/assets/custom.css (Inter base font, brand styles, method-* classes, tier-card, source-item)
    - dashboard/pages/about.py (full restructure: method-section pattern, formula boxes, interp rows)
    - dashboard/pages/country.py (page-header, stub-card, stat-chips)
    - dashboard/pages/product.py (page-header, stub-card, stat-chips)
    - pyproject.toml (added [tool.setuptools.packages.find] include = ["pipeline*", "dashboard*"])

key-decisions:
  - "Inter (Google Fonts, 300–800) chosen as base font — clean, readable at small sizes"
  - "Brand title: 'Dependency' (light 300, slate) + 'Atlas' (heavy 800, white)"
  - "About page structured with method-label + method-section pattern (no mixed H5/H6 headings)"
  - "Geo-risk formula uses R_{\\text{geo}} subscript notation to avoid MathJax \\text{word\\_word} bug"
  - "pyproject.toml packages.find added to prevent setuptools discovering data/ as a top-level package"

patterns-established:
  - "CSS file writes: create_file to /tmp/, then cp — avoids terminal heredoc encoding corruption"
  - "page-header div pattern: H3 + .page-subtitle inside .page-header, used on all content pages"
  - "method-section pattern: .method-label (uppercase) + content div with hairline dividers"
  - "formula-box: grey bg, blue left border — visually distinct from prose"

requirements-completed: [DASH-05]

human-verified: true
verified-by: user checkpoint approval 2026-03-23

duration: ~45min (including bug fixes and visual polish iterations)
completed: 2026-03-23
---

# Phase 03 Plan 03 Summary

**Dockerfile + production gunicorn setup, visual polish pass (Inter font, dark sidebar, two-tone brand title), and restructured Methodology page. Human checkpoint passed.**

All three pages confirmed working in browser: `/` (home), `/country`, `/product`, `/about`.
App runs offline-safe when `data/dashboard.duckdb` is absent.
