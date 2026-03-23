"""Methodology / About page for DependencyAtlas."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard import data

dash.register_page(
    __name__,
    path="/about",
    name="About",
    title="DependencyAtlas — Methodology",
)

# ---------------------------------------------------------------------------
# Tab content builders
# ---------------------------------------------------------------------------


def _tab_hhi() -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5("Herfindahl–Hirschman Index (HHI)"),
                dcc.Markdown(
                    r"""
### Formula

$$HHI = \sum_{i=1}^{n} s_i^2$$

where $s_i$ is supplier $i$'s share of import value for the product-importer pair
(expressed as a fraction 0–1, so the raw HHI range is already 0–1).
""",
                    mathjax=True,
                ),
                html.H6("Interpretation", className="mt-3"),
                html.Ul(
                    [
                        html.Li("HHI = 1.0 — complete monopoly (single supplier)"),
                        html.Li("HHI ≈ 0 — many equally-sized suppliers"),
                        html.Li("Scores are normalised to 0–1 before composite computation"),
                    ]
                ),
                html.H6("Why HHI instead of alternatives?", className="mt-3"),
                dcc.Markdown(
                    """
HHI's quadratic weighting means it is **sensitive to the largest suppliers** — a single supplier
with 80% share raises HHI far more than eight suppliers each with 10%.
This captures tail risk better than a simple supplier count (which treats all suppliers equally)
or a diversity index (which downweights dominant suppliers).
HHI is also widely used in competition policy work (US DOJ, EU DG COMP), giving results
that are directly comparable to published concentration analyses.
"""
                ),
            ]
        ),
        className="mt-3",
    )


def _tab_georisk() -> dbc.Card:
    wgi_dimensions = [
        "Voice & Accountability",
        "Political Stability & Absence of Violence",
        "Government Effectiveness",
        "Regulatory Quality",
        "Rule of Law",
        "Control of Corruption",
    ]
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5("Geopolitical Risk"),
                html.H6("WGI 6 Governance Dimensions", className="mt-3"),
                dbc.ListGroup(
                    [dbc.ListGroupItem(d) for d in wgi_dimensions],
                    flush=True,
                    className="mb-3",
                ),
                html.H6("Coverage Gaps"),
                dcc.Markdown(
                    """
For territories without WGI coverage, **Freedom House** scores are used as a fallback.
This affects primarily: Taiwan, Kosovo, and Palestine.
"""
                ),
                html.H6("Sanctions Multiplier", className="mt-3"),
                dcc.Markdown(
                    r"""
Sourced from the **Global Sanctions Database (GSDB)** (Drexel University / Stanford).

$$geo\_risk = governance\_risk \times (1 + sanctions\_intensity)$$

- **governance_risk** — normalised 0–1 (higher = worse governance), derived from WGI/Freedom House
- **sanctions_intensity** — total sanction events normalised 0–1 (GSDB bilateral sanctions)
""",
                    mathjax=True,
                ),
            ]
        ),
        className="mt-3",
    )


def _tab_essentiality() -> dbc.Card:
    tiers = [
        {
            "Tier": "Critical",
            "Score Range": "0.85–1.0",
            "Examples": "Critical raw materials (EU CRM 2023), USGS critical minerals",
        },
        {
            "Tier": "Important",
            "Score Range": "0.45–0.7",
            "Examples": "Energy products, pharma, food staples, semiconductors",
        },
        {
            "Tier": "Standard",
            "Score Range": "0.1–0.3",
            "Examples": "General industrial inputs",
        },
    ]
    rows = [
        html.Tr([html.Td(t["Tier"]), html.Td(t["Score Range"]), html.Td(t["Examples"])])
        for t in tiers
    ]
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5("Essentiality"),
                dbc.Table(
                    [
                        html.Thead(
                            html.Tr([html.Th("Tier"), html.Th("Score Range"), html.Th("Examples")])
                        ),
                        html.Tbody(rows),
                    ],
                    striped=True,
                    bordered=True,
                    hover=True,
                    responsive=True,
                    className="mt-3",
                ),
                html.H6("Within-tier gradient", className="mt-3"),
                dcc.Markdown(
                    """
A product's exact score **within its tier** is modulated by its global export HHI.
A critical material with highly concentrated global supply (few producing countries)
scores at the **top** of the Critical range.
"""
                ),
                html.H6("Data sources"),
                dbc.ListGroup(
                    [
                        dbc.ListGroupItem("EU Critical Raw Materials list (CRM 2023) — European Commission"),
                        dbc.ListGroupItem("USGS Critical Minerals List (2022) — US Geological Survey"),
                    ],
                    flush=True,
                ),
            ]
        ),
        className="mt-3",
    )


def _tab_sources() -> dbc.Card:
    min_yr, max_yr = data.get_year_range()
    sources = [
        {
            "Dataset": "BACI bilateral trade",
            "Provider": "CEPII",
            "Coverage": "~200 countries, ~5,000 HS6 products",
            "Notes": "Reconciled from UN COMTRADE",
        },
        {
            "Dataset": "Worldwide Governance Indicators (WGI)",
            "Provider": "World Bank",
            "Coverage": "~210 countries, 1996–present",
            "Notes": "6 governance dimensions",
        },
        {
            "Dataset": "Freedom House Freedom in the World",
            "Provider": "Freedom House",
            "Coverage": "~210 territories",
            "Notes": "Used where WGI has gaps",
        },
        {
            "Dataset": "Global Sanctions Database (GSDB)",
            "Provider": "Drexel/Stanford",
            "Coverage": "sanctions since 1950",
            "Notes": "Bilateral sanctions intensity",
        },
        {
            "Dataset": "EU Critical Raw Materials List",
            "Provider": "European Commission",
            "Coverage": "~34 materials (CRM 2023)",
            "Notes": "Mapped to HS6 codes",
        },
        {
            "Dataset": "USGS Critical Minerals list",
            "Provider": "US Geological Survey",
            "Coverage": "~50 minerals (2022)",
            "Notes": "Mapped to HS6 codes",
        },
    ]
    rows = [
        html.Tr(
            [html.Td(s["Dataset"]), html.Td(s["Provider"]), html.Td(s["Coverage"]), html.Td(s["Notes"])]
        )
        for s in sources
    ]
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5("Data Sources"),
                dcc.Markdown(
                    f"Trade data spans **{min_yr}–{max_yr}** (latest year: {max_yr})."
                ),
                dbc.Table(
                    [
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th("Dataset"),
                                    html.Th("Provider"),
                                    html.Th("Coverage"),
                                    html.Th("Notes"),
                                ]
                            )
                        ),
                        html.Tbody(rows),
                    ],
                    striped=True,
                    bordered=True,
                    hover=True,
                    responsive=True,
                    className="mt-3",
                ),
            ]
        ),
        className="mt-3",
    )


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

layout = dbc.Container(
    [
        html.Div([
        html.H3("Methodology"),
        html.P("Scoring methodology and data sources for the supply-risk index.",
               className="page-subtitle"),
    ], className="page-header"),
        dbc.Tabs(
            [
                dbc.Tab(_tab_hhi(), label="HHI Concentration", tab_id="tab-hhi"),
                dbc.Tab(_tab_georisk(), label="Geopolitical Risk", tab_id="tab-georisk"),
                dbc.Tab(_tab_essentiality(), label="Essentiality", tab_id="tab-essentiality"),
                dbc.Tab(_tab_sources(), label="Data Sources", tab_id="tab-sources"),
            ],
            id="about-tabs",
            active_tab="tab-hhi",
        ),
    ],
    fluid=False,
    className="py-4 about-content",
)
