# Governance Reference Data

This directory contains reference data files for the geopolitical risk scoring module (`pipeline/georisk.py`).

## Required Files

### `wgi.csv` — World Bank Worldwide Governance Indicators
**Source:** https://info.worldbank.org/governance/wgi/

**Required columns:** `iso3, year, va, ps, ge, rq, rl, cc`

| Column | Description | Range |
|--------|-------------|-------|
| `iso3` | ISO 3166-1 alpha-3 country code | e.g., DEU, CHN |
| `year` | Year of observation | e.g., 1996–2023 |
| `va` | Voice and Accountability | ~-2.5 to +2.5 |
| `ps` | Political Stability and Absence of Violence | ~-2.5 to +2.5 |
| `ge` | Government Effectiveness | ~-2.5 to +2.5 |
| `rq` | Regulatory Quality | ~-2.5 to +2.5 |
| `rl` | Rule of Law | ~-2.5 to +2.5 |
| `cc` | Control of Corruption | ~-2.5 to +2.5 |

**How to download:**
1. Visit https://info.worldbank.org/governance/wgi/
2. Click "Download Data" → select all countries, all years, all indicators
3. Download as CSV
4. Reformat to the 8-column layout above (iso3, year, va, ps, ge, rq, rl, cc)
5. Place as `data/reference/governance/wgi.csv`

**Note:** Missing values for some countries/years are expected. The module handles `NA` gracefully.

---

### `freedom_house_fallback.csv` — Freedom House Scores (Optional)
**Source:** https://freedomhouse.org/report/freedom-world

**Required columns:** `iso3, year, fh_score`

| Column | Description | Range |
|--------|-------------|-------|
| `iso3` | ISO 3166-1 alpha-3 code | TWN, XKX, PSE |
| `year` | Year | e.g., 1996–2023 |
| `fh_score` | Freedom in the World aggregate score | 0–100 (higher = freer) |

**Purpose:** Provides governance risk for territories not in WGI:
- **TWN** — Taiwan (not in WGI due to UN representation issues)
- **XKX** — Kosovo (not universally recognized)
- **PSE** — Palestine (partial WGI coverage)

**Formula:** `governance_risk = 1 - (fh_score / 100)`

**Example content:**
```csv
iso3,year,fh_score
TWN,2022,94
TWN,2021,94
XKX,2022,52
PSE,2022,27
```

If this file is absent, the module logs a warning and these territories receive no geo-risk score.

---

### `gsdb_sanctions.csv` — Global Sanctions Data Base (Optional)
**Source:** https://www.globalsanctionsdatabase.com/
(Drexel University / Stanford University; Felbermayr et al. 2020)

**Required columns:** `sender_iso3, target_iso3, start_year, end_year`

| Column | Description |
|--------|-------------|
| `sender_iso3` | ISO3 of sanctioning country/bloc |
| `target_iso3` | ISO3 of sanctioned country |
| `start_year` | Year sanctions went into force |
| `end_year` | Year sanctions ended (empty = ongoing) |

**Purpose:** Sanctions act as a risk multiplier:
`geo_risk = min(1.0, governance_risk × (1 + sanctions_intensity))`

where `sanctions_intensity = active_sanctions_count / 10` (clamped to 1.0).

**Example content:**
```csv
sender_iso3,target_iso3,start_year,end_year
USA,IRN,1979,
EU,RUS,2014,
USA,RUS,2022,
USA,PRK,1950,
```

If this file is absent, all `sanctions_intensity` values are 0 (sanctions have no effect).
