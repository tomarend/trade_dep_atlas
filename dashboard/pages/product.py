"""Product Risk page — second analytical view for the DependencyAtlas dashboard."""

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import callback, dcc, html, Input, Output, State, no_update

from dashboard import data

dash.register_page(
    __name__,
    path="/product",
    name="Product Risk",
    title="DependencyAtlas \u2014 Product Risk",
)


def _build_hs2_options(products):
    """Build HS2 chapter dropdown options from product list."""
    seen = {}
    for p in products:
        hs2 = p["hs2"]
        if hs2 not in seen:
            seen[hs2] = p["description"]
    return [
        {"label": f"{hs2} \u2014 {desc[:60]}", "value": hs2}
        for hs2, desc in sorted(seen.items())
    ]


def _build_hs4_options(products, hs2):
    """Build HS4 heading dropdown options filtered by HS2."""
    seen = {}
    for p in products:
        if p["hs2"] == hs2:
            hs4 = p["hs4"]
            if hs4 not in seen:
                seen[hs4] = p["description"]
    return [
        {"label": f"{hs4} \u2014 {desc[:60]}", "value": hs4}
        for hs4, desc in sorted(seen.items())
    ]


def _build_hs6_options(products, hs4):
    """Build HS6 product dropdown options filtered by HS4."""
    return [
        {"label": f"{p['hs6']} \u2014 {p['description'][:60]}", "value": p["hs6"]}
        for p in products
        if p["hs4"] == hs4
    ]


def layout():
    products = data.get_product_list()
    default_hs6 = data.get_default_product()

    # Find hs2/hs4 for default product
    default_hs2, default_hs4 = None, None
    for p in products:
        if p["hs6"] == default_hs6:
            default_hs2 = p["hs2"]
            default_hs4 = p["hs4"]
            break

    if not default_hs2 and products:
        default_hs2 = products[0]["hs2"]
        default_hs4 = products[0]["hs4"]
        default_hs6 = products[0]["hs6"]

    hs2_options = _build_hs2_options(products)
    hs4_options = _build_hs4_options(products, default_hs2) if default_hs2 else []
    hs6_options = _build_hs6_options(products, default_hs4) if default_hs4 else []

    return html.Div([
        # -- Page header --
        html.Div([
            html.H3("Product Risk"),
            html.P(
                "Import dependency analysis by HS6 product across all importing countries.",
                className="page-subtitle",
            ),
        ], className="page-header"),

        # -- HS Hierarchy Selector --
        dbc.Row([
            dbc.Col([
                dbc.Label("HS2 Chapter", html_for="product-hs2-selector", className="fw-semibold"),
                dcc.Dropdown(
                    id="product-hs2-selector",
                    options=hs2_options,
                    value=default_hs2,
                    searchable=True,
                    clearable=False,
                    placeholder="Select HS2 chapter...",
                ),
            ], md=4),
            dbc.Col([
                dbc.Label("HS4 Heading", html_for="product-hs4-selector", className="fw-semibold"),
                dcc.Dropdown(
                    id="product-hs4-selector",
                    options=hs4_options,
                    value=default_hs4,
                    searchable=True,
                    clearable=False,
                    placeholder="Select HS4 heading...",
                ),
            ], md=4),
            dbc.Col([
                dbc.Label("HS6 Product", html_for="product-hs6-selector", className="fw-semibold"),
                dcc.Dropdown(
                    id="product-hs6-selector",
                    options=hs6_options,
                    value=default_hs6,
                    searchable=True,
                    clearable=False,
                    placeholder="Select HS6 product...",
                ),
            ], md=4),
        ], className="mb-3"),

        # -- Summary cards --
        html.Div(id="product-summary-cards", className="mb-3"),

        # -- Data store --
        dcc.Store(id="product-data-store", storage_type="memory"),

        # -- Importer table placeholder (Plan 02) --
        html.Div(id="importer-table-container"),

        # -- Map placeholder (Plan 02) --
        html.Div(id="product-map-container", className="mt-3"),
    ])


# -- Callbacks --


@callback(
    [Output("product-hs4-selector", "options"),
     Output("product-hs4-selector", "value")],
    Input("product-hs2-selector", "value"),
)
def update_hs4_options(hs2):
    """Filter HS4 options when HS2 changes."""
    if not hs2:
        return [], None
    products = data.get_product_list()
    opts = _build_hs4_options(products, hs2)
    val = opts[0]["value"] if opts else None
    return opts, val


@callback(
    [Output("product-hs6-selector", "options"),
     Output("product-hs6-selector", "value")],
    Input("product-hs4-selector", "value"),
)
def update_hs6_options(hs4):
    """Filter HS6 options when HS4 changes."""
    if not hs4:
        return [], None
    products = data.get_product_list()
    opts = _build_hs6_options(products, hs4)
    val = opts[0]["value"] if opts else None
    return opts, val


@callback(
    Output("product-data-store", "data"),
    Input("product-hs6-selector", "value"),
)
def load_product_data(hs6):
    """Load importer scores for the selected product into the store."""
    if not hs6:
        return no_update
    return data.get_importer_scores(hs6)


@callback(
    Output("product-summary-cards", "children"),
    Input("product-data-store", "data"),
    State("product-hs6-selector", "value"),
)
def update_product_summary(importer_data, hs6):
    """Render summary cards and radar chart for the selected product."""
    if not importer_data or not hs6:
        return html.Div(
            "Select a product to view global dependency analysis.",
            className="text-muted p-3",
        )

    summary = data.get_product_summary(hs6)

    # Get essentiality info from product list
    products = data.get_product_list()
    ess_tier = "standard"
    ess_score = summary["avg_essentiality"]
    for p in products:
        if p["hs6"] == hs6:
            break

    avg_composite = summary["avg_composite"]
    level = "high" if avg_composite > 0.7 else "medium" if avg_composite > 0.4 else "low"

    # Product-level radar chart
    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(
        r=[summary["avg_hhi"], summary["avg_geo_risk"], summary["avg_essentiality"]],
        theta=["HHI Concentration", "Geo Risk", "Essentiality"],
        fill="toself",
        fillcolor="rgba(37, 99, 235, 0.15)",
        line=dict(color="#2563eb"),
    ))
    radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        title="Risk Profile Overview",
        template="plotly_white",
        font_family="Inter",
        margin=dict(l=40, r=40, t=50, b=30),
        height=250,
    )

    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Global Exposure", className="text-muted mb-1 small fw-semibold"),
                html.H2(f"{avg_composite:.3f}", className=f"mb-0 score-value score-{level}"),
                html.Span(
                    f"{summary['importer_count']} importers \u00b7 {summary['high_risk_count']} high-risk",
                    className="text-muted small",
                ),
            ])), md=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Concentration (HHI)", className="text-muted mb-1 small fw-semibold"),
                html.H3(f"{summary['avg_hhi']:.3f}", className="mb-0"),
            ])), md=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Geo Risk", className="text-muted mb-1 small fw-semibold"),
                html.H3(f"{summary['avg_geo_risk']:.3f}", className="mb-0"),
            ])), md=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Essentiality", className="text-muted mb-1 small fw-semibold"),
                html.H3(f"{summary['avg_essentiality']:.3f}", className="mb-0"),
            ])), md=3),
        ], className="g-3"),
        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    id="product-overview-radar",
                    figure=radar,
                    config={"displayModeBar": False},
                ),
                md=4,
                className="mx-auto mt-3",
            ),
        ]),
    ])
