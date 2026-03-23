"""Country Exposure stub page."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard import data

dash.register_page(
    __name__,
    path="/country",
    name="Country Exposure",
    title="DependencyAtlas \u2014 Country Exposure",
)


def layout():
    default_country = data.get_default_country()
    min_yr, max_yr = data.get_year_range()
    return html.Div(
        [
            html.Div(
                [
                    html.H3("Country Exposure"),
                    html.P(
                        "Supplier concentration and geopolitical risk by importing country.",
                        className="page-subtitle",
                    ),
                ],
                className="page-header",
            ),
            dcc.Loading(
                id="loading-country-content",
                type="circle",
                children=html.Div(
                    id="country-content-placeholder",
                    children=html.Div(
                        [
                            html.Div("\U0001f310", className="stub-icon"),
                            html.Span("Coming in Phase 4", className="stub-badge"),
                            html.H5("Country Exposure Maps & Tables"),
                            html.P(
                                "Choropleth maps, supplier concentration charts, and "
                                "risk breakdowns by country will appear here."
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        [
                                            html.Span("Default country", className="chip-label"),
                                            html.Span(": "),
                                            html.Span(default_country, className="chip-value"),
                                        ],
                                        className="stat-chip",
                                    ),
                                    html.Span(
                                        [
                                            html.Span("Years", className="chip-label"),
                                            html.Span(": "),
                                            html.Span(f"{min_yr}\u2013{max_yr}", className="chip-value"),
                                        ],
                                        className="stat-chip",
                                    ),
                                ],
                                className="mt-3",
                            ),
                        ],
                        className="stub-card",
                    ),
                ),
            ),
        ],
    )
