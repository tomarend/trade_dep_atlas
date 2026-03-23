"""Shared sidebar + content + footer layout for DependencyAtlas."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard import data


def _error_layout() -> dbc.Container:
    """Full-page error displayed when dashboard.duckdb is absent."""
    return dbc.Container(
        [
            dcc.Location(id="url"),
            dbc.Alert(
                [
                    html.H4("No data found", className="alert-heading"),
                    html.P(
                        "Run "
                        + html.Code("python -m pipeline").to_plotly_json()["props"]["children"]
                        + " to build the database, then restart the dashboard.",
                    ),
                ],
                color="danger",
                className="mt-5",
            ),
        ],
        fluid=False,
        className="py-5",
    )


def _build_error_layout() -> dbc.Container:
    """Return an error container without using .to_plotly_json() (simpler)."""
    return dbc.Container(
        [
            dcc.Location(id="url"),
            dbc.Alert(
                [
                    html.H4("No data found", className="alert-heading"),
                    html.P(
                        [
                            "Run ",
                            html.Code("python -m pipeline"),
                            " to build the database, then restart the dashboard.",
                        ]
                    ),
                ],
                color="danger",
                className="mt-5",
            ),
        ],
        fluid=False,
        className="py-5",
    )


def _build_sidebar() -> dbc.Col:
    """Left navigation sidebar."""
    return dbc.Col(
        [
            html.H4("DependencyAtlas", className="brand-title"),
            html.Hr(className="mt-1 mb-3"),
            dbc.Nav(
                [
                    dbc.NavLink("Country Exposure", href="/country", active="exact"),
                    dbc.NavLink("Product Risk", href="/product", active="exact"),
                    dbc.NavLink("About", href="/about", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        id="sidebar",
        width=2,
    )


def _build_footer() -> dbc.Row:
    """Full-width footer with live data freshness."""
    min_year, max_year = data.get_year_range()
    return dbc.Row(
        dbc.Col(
            html.Footer(
                f"Data: BACI {min_year}–{max_year} · CEPII",
                className="footer-text",
            ),
            width=12,
        )
    )


def create_layout() -> dbc.Container:
    """Return the full app layout (or error layout if DB is absent)."""
    if not data.db_available:
        return _build_error_layout()

    return dbc.Container(
        [
            dcc.Location(id="url", refresh=False),
            dbc.Row(
                [
                    _build_sidebar(),
                    dbc.Col(dash.page_container, id="page-content", width=10),
                ]
            ),
            _build_footer(),
        ],
        fluid=True,
    )
