"""Shared sidebar + content + footer layout for DependencyAtlas."""

import dash
import dash_bootstrap_components as dbc
from dash import clientside_callback, dcc, html, Input, Output

from dashboard import data


def _build_sidebar() -> dbc.Col:
    min_year, max_year = data.get_year_range()
    return dbc.Col(
        [
            html.Div(
                [
                    html.H4([
                        html.Span("Dependency", className="brand-dim"),
                        html.Span("Atlas", className="brand-accent"),
                    ], className="brand-title"),
                    html.P("Import risk analytics", className="brand-tagline"),
                ],
                className="brand-wrap",
            ),
            html.Hr(className="mt-0 mb-1"),
            dbc.Nav(
                [
                    dbc.NavLink("Country Exposure", href="/country", active="exact"),
                    dbc.NavLink("Product Risk", href="/product", active="exact"),
                    dbc.NavLink("About", href="/about", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
            html.Hr(className="sidebar-divider"),
            html.Div([
                html.P([
                    "Viewing: ",
                    html.Strong(str(max_year), id="year-label"),
                ], className="year-display mb-1 small text-muted"),
                dcc.Slider(
                    id="year-slider",
                    min=min_year,
                    max=max_year,
                    value=max_year,
                    step=1,
                    marks={y: str(y) for y in range(min_year, max_year + 1, 5)},
                    tooltip={"placement": "bottom"},
                    updatemode="mouseup",
                ),
            ], className="year-slider-wrap px-3"),
        ],
        id="sidebar",
        width=2,
    )


def _build_footer() -> dbc.Row:
    min_year, max_year = data.get_year_range()
    return dbc.Row(
        dbc.Col(
            html.Footer(
                f"Data: BACI {min_year}\u2013{max_year} \u00b7 CEPII \u00b7 WGI \u00b7 GSDB",
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
    _, max_year = data.get_year_range()
    page_children = [dash.page_container]
    if not data.db_available:
        page_children = [_offline_banner()] + page_children
    return dbc.Container(
        [
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="year-store", data=max_year, storage_type="session"),
            dbc.Row(
                [
                    _build_sidebar(),
                    dbc.Col(page_children, id="page-content", width=10),
                ],
                className="g-0",
            ),
            _build_footer(),
        ],
        fluid=True,
    )


# Sync slider -> store + label (clientside for instant feel)
clientside_callback(
    "function(year) { return [year, String(year)]; }",
    [Output("year-store", "data"), Output("year-label", "children")],
    Input("year-slider", "value"),
)
