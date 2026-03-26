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
# Shared helpers
# ---------------------------------------------------------------------------

def _section_label(text: str) -> html.P:
    """Small uppercase section label — FORMULA, INTERPRETATION, etc."""
    return html.P(text, className="method-label")


def _formula_box(markdown_text: str) -> html.Div:
    """Styled formula block with light background."""
    return html.Div(
        dcc.Markdown(markdown_text, mathjax=True),
        className="formula-box",
    )


def _section(label: str, *children) -> html.Div:
    """Labelled section block with consistent spacing."""
    return html.Div(
        [_section_label(label), *children],
        className="method-section",
    )


# ---------------------------------------------------------------------------
# Tab: HHI Concentration
# ---------------------------------------------------------------------------

def _tab_hhi() -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.P(
                """The Herfindahl–Hirschman Index measures how concentrated a country's imports
                of a given product are across its supplier countries. A score of 1 means total
                dependence on a single supplier; a score near 0 means supply is spread across
                many roughly equal partners.""",
                className="method-intro",
            ),

            _section(
                "FORMULA",
                _formula_box(
                    r"""$$HHI = \sum_{i=1}^{n} s_i^2$$

Where $s_i$ is supplier $i$'s share of total import value for the product–importer
pair, expressed as a fraction between 0 and 1."""
                ),
            ),

            _section(
                "INTERPRETATION",
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Span("HHI = 1.0", className="interp-value"),
                            html.Span("Complete monopoly — single supplier", className="interp-desc"),
                        ], className="interp-row"),
                        html.Div([
                            html.Span("HHI > 0.25", className="interp-value"),
                            html.Span("Highly concentrated supply", className="interp-desc"),
                        ], className="interp-row"),
                        html.Div([
                            html.Span("HHI 0.15–0.25", className="interp-value"),
                            html.Span("Moderately concentrated", className="interp-desc"),
                        ], className="interp-row"),
                        html.Div([
                            html.Span("HHI < 0.15", className="interp-value"),
                            html.Span("Unconcentrated — many suppliers", className="interp-desc"),
                        ], className="interp-row"),
                    ], md=8),
                ]),
            ),

            _section(
                "WHY HHI?",
                html.P(
                    """HHI's quadratic weighting makes it sensitive to dominant suppliers —
                    a single 80% supplier raises HHI far more than eight suppliers each at 10%.
                    This captures tail risk better than a simple supplier count.
                    HHI is also the standard measure used in US DOJ and EU DG COMP competition
                    analysis, making results directly comparable to published work.""",
                    className="method-text",
                ),
            ),
        ]),
        className="method-card",
    )


# ---------------------------------------------------------------------------
# Tab: Geopolitical Risk
# ---------------------------------------------------------------------------

def _tab_georisk() -> dbc.Card:
    wgi_dims = [
        ("Voice & Accountability", "extent of political participation and free expression"),
        ("Political Stability", "likelihood of political instability or politically-motivated violence"),
        ("Government Effectiveness", "quality of public services and civil service"),
        ("Regulatory Quality", "ability to formulate sound policies enabling private development"),
        ("Rule of Law", "confidence in contract enforcement, property rights, courts"),
        ("Control of Corruption", "extent of public power exercised for private gain"),
    ]

    return dbc.Card(
        dbc.CardBody([
            html.P(
                """Geopolitical risk for each supplier country is built
                from two inputs: governance quality (World Bank WGI) and
                sanctions exposure (GSDB). Higher scores mean greater risk.""",
                className="method-intro",
            ),

            _section(
                "COMPOSITE FORMULA",
                _formula_box(
                    r"""$$R_{\text{geo}} = R_{\text{gov}} \times \bigl(1 + S_{\text{sanc}}\bigr)$$

Where $R_{\text{gov}}$ is governance risk (0–1, higher = worse), derived from WGI / Freedom House; $S_{\text{sanc}}$ is bilateral sanctions intensity (0–1, GSDB)"""
                ),
            ),

            _section(
                "WGI GOVERNANCE DIMENSIONS",
                html.P(
                    "Six dimensions are averaged and inverted so that higher values indicate worse governance:",
                    className="method-text",
                ),
                html.Div([
                    html.Div([
                        html.Span(f"{i+1}.", className="wgi-num"),
                        html.Div([
                            html.Span(name, className="wgi-name"),
                            html.Span(desc, className="wgi-desc"),
                        ], className="wgi-text"),
                    ], className="wgi-row")
                    for i, (name, desc) in enumerate(wgi_dims)
                ], className="wgi-list"),
            ),

            _section(
                "COVERAGE GAPS",
                html.P(
                    """WGI excludes some territories. For Taiwan, Kosovo, and Palestine,
                    Freedom House Freedom in the World scores are used as a fallback,
                    rescaled to the WGI range.""",
                    className="method-text",
                ),
            ),

            _section(
                "SANCTIONS DATA",
                html.P(
                    """Sanctions intensity is sourced from the Global Sanctions Database (GSDB),
                    maintained by Drexel University and Stanford. It captures bilateral sanction
                    episodes between 1950 and the present, normalised to a 0–1 intensity score
                    per country pair.""",
                    className="method-text",
                ),
            ),
        ]),
        className="method-card",
    )


# ---------------------------------------------------------------------------
# Tab: Substitutability
# ---------------------------------------------------------------------------

def _tab_substitutability() -> dbc.Card:
    flags = [
        {"name": "crm_listed", "desc": "EU Critical Raw Materials (CRM 2023) or USGS Critical Minerals"},
        {"name": "strategic_mineral", "desc": "Broader set of strategic minerals mapped from HS4 codes"},
        {"name": "energy", "desc": "HS chapter 27 commodities (fossil fuels, excludes electricity HS 2716)"},
        {"name": "food", "desc": "HS chapters 01–24 (agricultural and food products)"},
        {"name": "fertilizer", "desc": "HS chapter 31 (fertilizers)"},
        {"name": "pharma", "desc": "HS chapters 29–30 (organic chemicals and pharmaceutical products)"},
        {"name": "semiconductor", "desc": "Key HS6 codes for integrated circuits and semiconductor wafers"},
        {"name": "hs22_only", "desc": "Product first appeared in the HS 2022 revision (no historical data pre-2022)"},
    ]

    flag_rows = html.Div([
        html.Div([
            html.Code(f["name"], className="flag-code"),
            html.Span(f["desc"], className="flag-desc"),
        ], className="flag-row")
        for f in flags
    ], className="flag-list mb-3")

    return dbc.Card(
        dbc.CardBody([
            html.P(
                """Substitutability measures how difficult it is for the global economy to
                replace a product's supply from alternative sources, independent of any
                single importing country's exposure.""",
                className="method-intro",
            ),

            _section(
                "SUBSTITUTABILITY SCORE",
                html.P(
                    [
                        "The score is defined as ",
                        html.Code("substitutability_score = √(global_export_hhi)"),
                        """, where the global export HHI captures how concentrated
                        worldwide exports of that product are across all supplying
                        nations. A score near 1 means a single dominant exporter
                        controls global supply, making the product hard to substitute.""",
                    ],
                    className="method-text",
                ),
            ),

            _section("PRODUCT FLAGS", flag_rows),

            _section(
                "DATA SOURCES",
                html.Div([
                    html.Div([
                        html.Span("EU Critical Raw Materials List (CRM 2023)", className="src-name"),
                        html.Span("European Commission", className="src-provider"),
                    ], className="src-row"),
                    html.Div([
                        html.Span("USGS Critical Minerals List (2022)", className="src-name"),
                        html.Span("US Geological Survey", className="src-provider"),
                    ], className="src-row"),
                    html.Div([
                        html.Span("BACI Global Trade (HS 1992 & 2022 revisions)", className="src-name"),
                        html.Span("CEPII", className="src-provider"),
                    ], className="src-row"),
                ], className="src-list"),
            ),
        ]),
        className="method-card",
    )


# ---------------------------------------------------------------------------
# Tab: Data Sources
# ---------------------------------------------------------------------------

def _tab_sources() -> dbc.Card:
    min_yr, max_yr = data.get_year_range()
    sources = [
        {
            "dataset": "BACI Bilateral Trade",
            "provider": "CEPII",
            "coverage": f"{min_yr}–{max_yr}",
            "detail": "~200 countries, ~5,000 HS6 products. Reconciled mirror flows from UN COMTRADE.",
        },
        {
            "dataset": "Worldwide Governance Indicators (WGI)",
            "provider": "World Bank",
            "coverage": "1996–present",
            "detail": "6 governance dimensions across ~210 countries.",
        },
        {
            "dataset": "Freedom in the World",
            "provider": "Freedom House",
            "coverage": "Annual",
            "detail": "Political rights & civil liberties. Used as WGI fallback for Taiwan, Kosovo, Palestine.",
        },
        {
            "dataset": "Global Sanctions Database (GSDB)",
            "provider": "Drexel / Stanford",
            "coverage": "1950–present",
            "detail": "Bilateral sanctions episodes. Normalised to per-country intensity scores.",
        },
        {
            "dataset": "EU Critical Raw Materials List",
            "provider": "European Commission",
            "coverage": "CRM 2023",
            "detail": "34 critical raw materials mapped to HS6 codes.",
        },
        {
            "dataset": "USGS Critical Minerals",
            "provider": "US Geological Survey",
            "coverage": "2022 list",
            "detail": "~50 minerals mapped to HS6 codes.",
        },
    ]

    return dbc.Card(
        dbc.CardBody([
            html.P(
                f"All datasets are integrated and harmonised at the HS6 product level. "
                f"Trade data spans {min_yr}–{max_yr}.",
                className="method-intro",
            ),

            _section(
                "SOURCE DATASETS",
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span(s["dataset"], className="src-name"),
                            html.Span(s["coverage"], className="src-coverage"),
                        ], className="src-header"),
                        html.Div([
                            html.Span(s["provider"], className="src-provider"),
                            html.Span(s["detail"], className="src-detail"),
                        ], className="src-body"),
                    ], className="source-item")
                    for s in sources
                ], className="source-list"),
            ),
        ]),
        className="method-card",
    )


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

layout = dbc.Container(
    [
        html.Div([
            html.H3("Methodology"),
            html.P(
                "How supply-chain risk is measured — formulas, data sources, and design rationale.",
                className="page-subtitle",
            ),
        ], className="page-header"),

        dbc.Tabs(
            [
                dbc.Tab(_tab_hhi(), label="HHI Concentration", tab_id="tab-hhi"),
                dbc.Tab(_tab_georisk(), label="Geopolitical Risk", tab_id="tab-georisk"),
                dbc.Tab(_tab_substitutability(), label="Substitutability", tab_id="tab-substitutability"),
                dbc.Tab(_tab_sources(), label="Data Sources", tab_id="tab-sources"),
            ],
            id="about-tabs",
            active_tab="tab-hhi",
        ),
    ],
    fluid=False,
    className="py-4 about-content",
)
