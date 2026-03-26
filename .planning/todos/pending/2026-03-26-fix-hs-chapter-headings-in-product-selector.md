---
created: 2026-03-26T15:45:00Z
title: Fix HS chapter headings in product selector
area: dashboard
files:
  - dashboard/pages/product.py:23-32
---

## Problem

The HS2 chapter dropdown on the Product Risk page shows the description of the first HS6 product in each chapter rather than the actual chapter name. For example, chapter 27 (Mineral fuels, mineral oils, and products of their distillation) displays as "27 — Coal: anthracite, whether or not pulverised, but not agglomerated" because that's the first product alphabetically.

This makes it hard for users to find products — e.g. petroleum (270900) is under chapter 27, but the label says "Coal".

The issue is in `_build_hs2_options()` which grabs `p["description"]` from the first product encountered per HS2 code.

## Solution

Add proper HS chapter names. Options:
1. Add a `chapter_description` column to the `products` table mapping HS2 codes to official chapter titles (e.g. "27 — Mineral fuels, mineral oils...")
2. Or maintain a small lookup dict in product.py mapping HS2 codes to chapter names
3. Or use the `category` field from the products table if it maps to chapter-level descriptions
