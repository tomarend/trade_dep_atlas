"""Country Exposure page — primary analytical view for the DependencyAtlas dashboard."""

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import callback, clientside_callback, dcc, html, Input, Output, State, no_update

from dashboard import data

dash.register_page(
    __name__,
    path="/country",
    name="Country Exposure",
    title="DependencyAtlas \u2014 Country Exposure",
)


def layout():
    country_options = [{"label": name, "value": iso3} for iso3, name in data.get_country_list()]
    default_country = data.get_default_country()

    return html.Div([
        # ── Page header ──────────────────────────────────────────────────
        html.Div([
            html.H3("Country Exposure"),
            html.P(
                "Supplier concentration and geopolitical risk by importing country.",
                className="page-subtitle",
            ),
        ], className="page-header"),

        # ── Country selector ─────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Label("Importing Country", html_for="country-selector", className="fw-semibold"),
                dcc.Dropdown(
                    id="country-selector",
                    options=country_options,
                    value=default_country,
                    searchable=True,
                    clearable=False,
                    placeholder="Select a country...",
                ),
            ], md=4),
        ], className="mb-3"),

        # ── Summary cards ────────────────────────────────────────────────
        html.Div(id="country-summary-cards", className="mb-3"),

        # ── Weight controls (collapsible) ────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "\u2699 Customize Weights",
                    id="weights-toggle",
                    color="light",
                    size="sm",
                    className="mb-2",
                ),
                dbc.Collapse(
                    dbc.Card(dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("HHI Concentration", className="small fw-semibold"),
                                dcc.Slider(
                                    id="weight-hhi", min=0, max=1, step=0.05, value=0.35,
                                    marks=None,
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    updatemode="drag",
                                ),
                            ], md=4),
                            dbc.Col([
                                dbc.Label("Geopolitical Risk", className="small fw-semibold"),
                                dcc.Slider(
                                    id="weight-geo", min=0, max=1, step=0.05, value=0.35,
                                    marks=None,
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    updatemode="drag",
                                ),
                            ], md=4),
                            dbc.Col([
                                dbc.Label("Essentiality", className="small fw-semibold"),
                                dcc.Slider(
                                    id="weight-ess", min=0, max=1, step=0.05, value=0.30,
                                    marks=None,
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    updatemode="drag",
                                ),
                            ], md=4),
                        ]),
                        html.Small(
                            "Weights are constrained to sum to 1.0. "
                            "Adjusting one slider proportionally adjusts the others.",
                            className="text-muted",
                        ),
                    ])),
                    id="weights-collapse",
                    is_open=False,
                ),
            ]),
        ], className="mb-3"),

        # ── Data store ───────────────────────────────────────────────────
        dcc.Store(id="country-data-store", storage_type="memory"),

        # ── AG Grid product table ────────────────────────────────────────
        dcc.Loading(
            dag.AgGrid(
                id="product-table",
                columnDefs=[
                    {
                        "field": "hs6",
                        "headerName": "HS6 Code",
                        "width": 120,
                        "filter": "agTextColumnFilter",
                        "pinned": "left",
                    },
                    {
                        "field": "description",
                        "headerName": "Product Description",
                        "flex": 2,
                        "filter": "agTextColumnFilter",
                        "tooltipField": "description",
                    },
                    {
                        "field": "weighted_composite",
                        "headerName": "Composite Score",
                        "width": 150,
                        "sort": "desc",
                        "filter": "agNumberColumnFilter",
                        "valueFormatter": {"function": "d3.format('.3f')(params.value)"},
                        "cellStyle": {
                            "function": """
                                params.value > 0.7 ? {'color': '#dc2626', 'fontWeight': '600'}
                                : params.value > 0.4 ? {'color': '#d97706', 'fontWeight': '600'}
                                : {'color': '#16a34a'}
                            """
                        },
                    },
                    {
                        "field": "hhi",
                        "headerName": "HHI",
                        "width": 100,
                        "filter": "agNumberColumnFilter",
                        "valueFormatter": {"function": "d3.format('.3f')(params.value)"},
                    },
                    {
                        "field": "basket_geo_risk",
                        "headerName": "Geo Risk",
                        "width": 110,
                        "filter": "agNumberColumnFilter",
                        "valueFormatter": {"function": "d3.format('.3f')(params.value)"},
                    },
                    {
                        "field": "essentiality_score",
                        "headerName": "Essentiality",
                        "width": 120,
                        "filter": "agNumberColumnFilter",
                        "valueFormatter": {"function": "d3.format('.3f')(params.value)"},
                    },
                    {
                        "field": "essentiality_tier",
                        "headerName": "Tier",
                        "width": 100,
                        "filter": "agSetColumnFilter",
                        "cellStyle": {
                            "function": """
                                params.value === 'critical' ? {'color': '#dc2626', 'fontWeight': '600'}
                                : params.value === 'important' ? {'color': '#d97706'}
                                : {}
                            """
                        },
                    },
                ],
                defaultColDef={
                    "sortable": True,
                    "resizable": True,
                    "filter": True,
                },
                dashGridOptions={
                    "rowSelection": {"mode": "singleRow", "checkboxes": False},
                    "animateRows": True,
                    "pagination": False,
                    "domLayout": "normal",
                },
                style={"height": "500px"},
                className="ag-theme-alpine",
            ),
            type="circle",
        ),

        # ── Drill-down placeholder (Plan 03) ─────────────────────────────
        html.Div(id="product-drilldown-container", className="mt-4"),
    ])


# ── Callbacks ────────────────────────────────────────────────────────────


@callback(
    Output("weights-collapse", "is_open"),
    Input("weights-toggle", "n_clicks"),
    State("weights-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_weights(n_clicks, is_open):
    return not is_open


# Proportional weight adjustment (clientside for instant feel)
clientside_callback(
    """
    function(hhi, geo, ess) {
        const sum = hhi + geo + ess;
        if (Math.abs(sum - 1.0) < 0.001) return window.dash_clientside.no_update;
        const tid = window.dash_clientside.callback_context.triggered_id;
        if (tid === 'weight-hhi') {
            const remainder = 1.0 - hhi;
            const otherSum = geo + ess;
            if (otherSum > 0) {
                return [hhi, Math.round(remainder * geo / otherSum * 20) / 20,
                        Math.round(remainder * ess / otherSum * 20) / 20];
            }
            return [hhi, Math.round(remainder / 2 * 20) / 20, Math.round(remainder / 2 * 20) / 20];
        } else if (tid === 'weight-geo') {
            const remainder = 1.0 - geo;
            const otherSum = hhi + ess;
            if (otherSum > 0) {
                return [Math.round(remainder * hhi / otherSum * 20) / 20, geo,
                        Math.round(remainder * ess / otherSum * 20) / 20];
            }
            return [Math.round(remainder / 2 * 20) / 20, geo, Math.round(remainder / 2 * 20) / 20];
        } else {
            const remainder = 1.0 - ess;
            const otherSum = hhi + geo;
            if (otherSum > 0) {
                return [Math.round(remainder * hhi / otherSum * 20) / 20,
                        Math.round(remainder * geo / otherSum * 20) / 20, ess];
            }
            return [Math.round(remainder / 2 * 20) / 20, Math.round(remainder / 2 * 20) / 20, ess];
        }
    }
    """,
    [Output("weight-hhi", "value"), Output("weight-geo", "value"), Output("weight-ess", "value")],
    [Input("weight-hhi", "value"), Input("weight-geo", "value"), Input("weight-ess", "value")],
    prevent_initial_call=True,
)


@callback(
    Output("country-data-store", "data"),
    Input("country-selector", "value"),
)
def load_country_data(country_iso3):
    """Load product scores for the selected country into the client-side store."""
    if not country_iso3:
        return no_update
    return data.get_product_scores(country_iso3)


@callback(
    Output("country-summary-cards", "children"),
    [Input("country-data-store", "data"),
     Input("weight-hhi", "value"),
     Input("weight-geo", "value"),
     Input("weight-ess", "value")],
)
def update_summary_cards(products, w_hhi, w_geo, w_ess):
    """Render summary cards with weight-adjusted scores."""
    if not products:
        return html.Div(
            "Select a country to view exposure analysis.",
            className="text-muted p-3",
        )

    # Recalculate composite scores with current weights
    for p in products:
        p["weighted_composite"] = (
            w_hhi * p["hhi"] + w_geo * p["basket_geo_risk"] + w_ess * p["essentiality_score"]
        )

    n = len(products)
    avg_composite = sum(p["weighted_composite"] for p in products) / n
    avg_hhi = sum(p["hhi"] for p in products) / n
    avg_geo = sum(p["basket_geo_risk"] for p in products) / n
    avg_ess = sum(p["essentiality_score"] for p in products) / n
    critical_count = sum(1 for p in products if p["essentiality_tier"] == "critical")
    high_risk = sum(1 for p in products if p["weighted_composite"] > 0.7)

    level = "high" if avg_composite > 0.7 else "medium" if avg_composite > 0.4 else "low"

    return dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Overall Exposure", className="text-muted mb-1 small fw-semibold"),
            html.H2(f"{avg_composite:.3f}", className=f"mb-0 score-value score-{level}"),
            html.Span(
                f"{n} products \u00b7 {high_risk} high-risk",
                className="text-muted small",
            ),
        ])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Concentration (HHI)", className="text-muted mb-1 small fw-semibold"),
            html.H3(f"{avg_hhi:.3f}", className="mb-0"),
        ])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Geo Risk", className="text-muted mb-1 small fw-semibold"),
            html.H3(f"{avg_geo:.3f}", className="mb-0"),
        ])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("Essentiality", className="text-muted mb-1 small fw-semibold"),
            html.H3(f"{avg_ess:.3f}", className="mb-0"),
            html.Span(f"{critical_count} critical", className="text-muted small"),
        ])), md=3),
    ], className="g-3")


@callback(
    Output("product-table", "rowData"),
    [Input("country-data-store", "data"),
     Input("weight-hhi", "value"),
     Input("weight-geo", "value"),
     Input("weight-ess", "value")],
)
def update_product_table(products, w_hhi, w_geo, w_ess):
    """Recalculate composite scores with current weights and update AG Grid."""
    if not products:
        return []
    for p in products:
        p["weighted_composite"] = round(
            w_hhi * p["hhi"] + w_geo * p["basket_geo_risk"] + w_ess * p["essentiality_score"],
            4,
        )
    products.sort(key=lambda x: x["weighted_composite"], reverse=True)
    return products
