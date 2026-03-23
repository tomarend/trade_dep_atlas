"""Product Risk stub page."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard import data

dash.register_page(
    __name__,
    path="/product",
    name="Product Risk",
    title="DependencyAtlas \u2014 Product Risk",
)


def layout():
    default_product = data.get_default_product()
    min_yr, max_yr = data.get_year_range()
    return html.Div(
        [
            html.Div(
                [
                    html.H3("Product Risk"),
                    html.P(
                        "Critical product identification, HHI scoring, and essentiality tiers.",
                        className="page-subtitle",
                    ),
                ],
                className="page-header",
            ),
            dcc.Loading(
                id="loading-product-content",
                type="circle",
                children=html.Div(
                    id="product-content-placeholder",
                    children=html.Div(
                        [
                            html.Div("\U0001f4e6", className="stub-icon"),
                            html.Span("Coming in Phase 5", className="stub-badge"),
                            html.H5("Product Risk Scorecards & Rankings"),
                            html.P(
                                "HS6 product risk scores, supplier trees, and "
                                "CRM/critical minerals highlights will appear here."
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        [
                                            html.Span("Default product", className="chip-label"),
                                            html.Span(": "),
                                            html.Span(default_product, className="chip-value"),
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
