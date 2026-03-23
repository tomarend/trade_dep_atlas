"""Shared sidebar + content + footer layout for DependencyAtlas."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard import data


def _build_sidebar() -> dbc.Col:
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


def _offline_banner() -> dbc.Alert:
    return dbc.Alert(
        [
            html.Strong("No data found. "),
            "Run ",
            html.Code("python -m pipeline"),
            " to build the database, then restart the dashboard.",
        ],
        color="warning",
        dismissable=True,
        className="mb-3",
    )


def create_layout() -> dbc.Container:
    page_children = [dash.page_container]
    if not data.db_available:
        page_children = [_offline_banner()] + page_children
    return dbc.Container(
        [
            dcc.Location(id="url", refresh=False),
            dbc.Row(
                [
                    _build_sidebar(),
                    dbc.Col(page_children, id="page-content", width=10),
                ]
            ),
            _build_footer(),
        ],
        fluid=True,
    )
