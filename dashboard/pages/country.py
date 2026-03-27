"""Country Exposure page — primary analytical view for the DependencyAtlas dashboard."""

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import callback, clientside_callback, dcc, html, Input, Output, State, no_update

import math

from dashboard import data

dash.register_page(
    __name__,
    path="/country",
    name="Country Exposure",
    title="DependencyAtlas \u2014 Country Exposure",
)


def layout(**kwargs):
    country_options = [{"label": name, "value": iso3} for iso3, name in data.get_country_list()]
    default_country = data.get_default_country()

    # Handle URL query parameter ?iso3=XXX
    iso3_param = kwargs.get("iso3")
    if iso3_param:
        valid_iso3s = {iso3 for iso3, _ in data.get_country_list()}
        if iso3_param in valid_iso3s:
            default_country = iso3_param

    return html.Div([
        # -- Page header --
        html.Div([
            html.H3("Country Exposure"),
            html.P(
                "Supplier concentration and geopolitical risk by importing country.",
                className="page-subtitle",
            ),
        ], className="page-header"),

        # -- Country selector --
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

        # -- Summary cards --
        html.Div(id="country-summary-cards", className="mb-3"),

        # -- Product Risk Landscape (scatter plot) --
        html.Div(id="country-scatter-container", className="mb-3"),

        # -- Bilateral Risk Panel --
        html.Div(id="country-bilateral-container", className="mb-3"),

        # -- Weight controls (collapsible) --
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
                                dbc.Label("Substitutability", className="small fw-semibold"),
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

        # -- Data store --
        dcc.Store(id="country-data-store", storage_type="memory"),

        # -- AG Grid product table --
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
                        # Cross-link to product view
                        "cellRenderer": "ProductLink",
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
                        "field": "substitutability_score",
                        "headerName": "Substitutability",
                        "width": 140,
                        "filter": "agNumberColumnFilter",
                        "valueFormatter": {"function": "d3.format('.3f')(params.value)"},
                    },
                    {
                        "field": "flags",
                        "headerName": "Flags",
                        "flex": 1,
                        "filter": "agTextColumnFilter",
                        "valueFormatter": {"function": "(params.value || []).join(', ')"},
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
                dangerously_allow_code=True,
            ),
            type="circle",
        ),

        # -- Drill-down panel --
        html.Div(id="product-drilldown-container", className="mt-4"),
    ])


# -- Callbacks --


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
    [Input("country-selector", "value"),
     Input("year-store", "data")],
)
def load_country_data(country_iso3, year):
    """Load product scores for the selected country and year into the client-side store."""
    if not country_iso3:
        return no_update
    return data.get_product_scores(country_iso3, year=year)


@callback(
    Output("country-summary-cards", "children"),
    [Input("country-data-store", "data"),
     Input("weight-hhi", "value"),
     Input("weight-geo", "value"),
     Input("weight-ess", "value")],
)
def update_summary_cards(products, w_hhi, w_geo, w_ess):
    """Render hero stat cards and country overview radar."""
    if not products:
        return html.Div(
            "Select a country to view exposure analysis.",
            className="text-muted p-3",
        )

    for p in products:
        p["weighted_composite"] = (
            w_hhi * p["hhi"] + w_geo * p["basket_geo_risk"] + w_ess * p["substitutability_score"]
        )

    # ── Hero stats (D-01) ──────────────────────────────────────────────────
    n = len(products)
    above_threshold = sum(
        1 for p in products if p["weighted_composite"] > data.RISK_THRESHOLD
    )
    top_product = max(products, key=lambda p: p["weighted_composite"])
    top_desc = (top_product.get("description") or top_product["hs6"])[:50]
    max_score = top_product["weighted_composite"]
    level = "high" if max_score > 0.7 else "medium" if max_score > 0.4 else "low"

    # ── Country overview radar (D-02) ────────────────────────────────────
    avg_hhi = sum(p["hhi"] for p in products) / n
    avg_geo = sum(p["basket_geo_risk"] for p in products) / n
    avg_ess = sum(p["substitutability_score"] for p in products) / n

    overview_radar = go.Figure()
    overview_radar.add_trace(go.Scatterpolar(
        r=[avg_hhi, avg_geo, avg_ess],
        theta=["HHI Concentration", "Geo Risk", "Substitutability"],
        fill="toself",
        fillcolor="rgba(37, 99, 235, 0.15)",
        line=dict(color="#2563eb"),
    ))
    overview_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        title="Risk Profile",
        template="plotly_white",
        font_family="Inter",
        margin=dict(l=40, r=40, t=50, b=30),
        height=230,
    )

    # ── Layout: 4 hero cards (md=8, 2x2 grid) + radar (md=4) (D-02) ────
    hero_cards = dbc.Col([
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Total Products", className="text-muted mb-1 small fw-semibold"),
                html.H2(f"{n}", className="mb-0"),
            ])), md=6, className="mb-2"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Above Risk Threshold", className="text-muted mb-1 small fw-semibold"),
                html.H2(f"{above_threshold}", className="mb-0 text-danger" if above_threshold > 0 else "mb-0"),
                html.Span(f"score > {data.RISK_THRESHOLD}", className="text-muted small"),
            ])), md=6, className="mb-2"),
        ]),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Highest-Risk Product", className="text-muted mb-1 small fw-semibold"),
                html.P(top_desc, className="mb-0 fw-semibold", style={"fontSize": "0.85rem"}),
            ])), md=6),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.P("Max Composite Score", className="text-muted mb-1 small fw-semibold"),
                html.H2(f"{max_score:.3f}", className=f"mb-0 score-value score-{level}"),
            ])), md=6),
        ]),
    ], md=8)

    return html.Div([
        dbc.Row([
            hero_cards,
            dbc.Col(
                dcc.Graph(
                    id="country-overview-radar",
                    figure=overview_radar,
                    config={"displayModeBar": False},
                ),
                md=4,
            ),
        ], className="g-3"),
    ])


@callback(
    Output("country-scatter-container", "children"),
    [Input("country-selector", "value"),
     Input("year-store", "data")],
)
def update_scatter_plot(country_iso3, year):
    """Render scatter plot: HHI vs substitutability, sized by import value, coloured by composite (D-03)."""
    if not country_iso3:
        return html.Div()
    scatter = data.get_scatter_data(country_iso3, year=year)
    if not scatter:
        return html.Div("No product risk data available.", className="text-muted p-3")

    marker_sizes = [
        max(5, min(30, 8 * math.log1p(r["total_import_value_usd"] or 1e3)))
        for r in scatter
    ]
    hover_texts = [
        (
            f"<b>{r['hs6']}</b><br>"
            f"{(r['description'] or '')[:60]}<br>"
            f"Composite: {r['composite_score']:.3f}<br>"
            f"HHI: {r['hhi']:.3f}<br>"
            f"Substitutability: {r['substitutability_score']:.3f}"
        )
        for r in scatter
    ]

    fig = go.Figure(go.Scatter(
        x=[r["hhi"] for r in scatter],
        y=[r["substitutability_score"] for r in scatter],
        mode="markers",
        marker=dict(
            size=marker_sizes,
            color=[r["composite_score"] for r in scatter],
            colorscale=[[0, "#22c55e"], [0.5, "#f59e0b"], [1, "#ef4444"]],
            cmin=0,
            cmax=1,
            showscale=True,
            colorbar=dict(title="Composite<br>Score", thickness=12),
            opacity=0.8,
        ),
        text=hover_texts,
        hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="HHI (Concentration)",
        yaxis_title="Substitutability",
        template="plotly_white",
        font_family="Inter",
        height=400,
        margin=dict(l=60, r=20, t=20, b=50),
        showlegend=False,
    )

    return html.Div([
        html.H6("Product Risk Landscape", className="fw-semibold mb-2"),
        dcc.Graph(
            id="country-scatter-plot",
            figure=fig,
            config={"displayModeBar": False},
        ),
    ])


@callback(
    Output("country-bilateral-container", "children"),
    [Input("country-selector", "value"),
     Input("year-store", "data")],
)
def update_bilateral_panel(country_iso3, year):
    """Render horizontal bar chart of top-10 source countries by weighted risk (D-08)."""
    if not country_iso3:
        return html.Div()
    bilateral = data.get_bilateral_risk(country_iso3, year=year)
    if not bilateral:
        return html.Div("No bilateral risk data available.", className="text-muted p-3")

    # Build flag-emoji labels (D-09) using ISO3->ISO2 lookup
    tick_labels = []
    for r in bilateral:
        iso2 = data._ISO3_TO_ISO2.get(r["exporter_iso3"], "").upper()
        if iso2 and len(iso2) == 2:
            emoji = "".join(chr(127397 + ord(c)) for c in iso2)
            tick_labels.append(f"{emoji} {r['exporter_name']}")
        else:
            tick_labels.append(r["exporter_name"])

    values = [r["weighted_risk_contribution"] for r in bilateral]
    geo_risks = [r["mean_geo_risk"] for r in bilateral]

    fig = go.Figure(go.Bar(
        y=tick_labels,
        x=values,
        orientation="h",
        marker=dict(
            color=geo_risks,
            colorscale=[[0, "#22c55e"], [0.5, "#f59e0b"], [1, "#ef4444"]],
            cmin=0,
            cmax=1,
            showscale=True,
            colorbar=dict(title="Geo<br>Risk", thickness=12),
        ),
        text=[f"{v:.3f}" for v in values],
        textposition="outside",
        hovertemplate="%{y}: %{x:.3f} weighted risk<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Weighted Risk Contribution",
        xaxis_range=[0, max(values) * 1.25 if values else 1],
        template="plotly_white",
        font_family="Inter",
        height=320,
        margin=dict(l=160, r=80, t=10, b=40),
        showlegend=False,
        yaxis=dict(autorange="reversed"),
    )

    return html.Div([
        html.H6("Key Supply Risk Sources", className="fw-semibold mb-2"),
        dcc.Graph(
            id="country-bilateral-chart",
            figure=fig,
            config={"displayModeBar": False},
        ),
    ])


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
            w_hhi * p["hhi"] + w_geo * p["basket_geo_risk"] + w_ess * p["substitutability_score"],
            4,
        )
    products.sort(key=lambda x: x["weighted_composite"], reverse=True)
    return products


@callback(
    Output("product-drilldown-container", "children"),
    Input("product-table", "selectedRows"),
    [State("country-selector", "value"),
     State("weight-hhi", "value"),
     State("weight-geo", "value"),
     State("weight-ess", "value"),
     State("year-store", "data")],
)
def render_drilldown(selected_rows, country_iso3, w_hhi, w_geo, w_ess, year):
    """Render drill-down panel when a product row is selected."""
    if not selected_rows or not country_iso3:
        return html.Div()

    product = selected_rows[0]
    hs6 = product["hs6"]
    description = product.get("description", hs6)

    suppliers = data.get_supplier_breakdown(country_iso3, hs6, year=year)
    if not suppliers:
        return dbc.Alert(f"No supplier data available for {hs6}.", color="warning")

    # -- Supplier Table --
    supplier_table = dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Supplier Country"),
                html.Th("Share %"),
                html.Th("Trade Value (USD)"),
                html.Th("Geo Risk"),
                html.Th("Region"),
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(s["exporter_name"]),
                    html.Td(f"{s['supplier_share'] * 100:.1f}%"),
                    html.Td(f"${s['value_usd']:,.0f}"),
                    html.Td(
                        html.Span(
                            f"{s['exporter_geo_risk']:.3f}",
                            style={"color": "#dc2626" if s["exporter_geo_risk"] > 0.7
                                   else "#d97706" if s["exporter_geo_risk"] > 0.4
                                   else "#16a34a", "fontWeight": "600"},
                        )
                    ),
                    html.Td(s.get("region", "\u2014")),
                ]) for s in suppliers
            ]),
        ],
        bordered=True,
        hover=True,
        striped=True,
        size="sm",
        className="mt-2",
    )

    # -- Choropleth Map --
    choropleth_data = {
        "iso3": [s["exporter_iso3"] for s in suppliers],
        "name": [s["exporter_name"] for s in suppliers],
        "geo_risk": [s["exporter_geo_risk"] for s in suppliers],
        "share": [s["supplier_share"] * 100 for s in suppliers],
    }

    choropleth_fig = px.choropleth(
        choropleth_data,
        locations="iso3",
        color="geo_risk",
        hover_name="name",
        hover_data={"share": ":.1f", "geo_risk": ":.3f", "iso3": False},
        color_continuous_scale="RdYlGn_r",
        range_color=[0, 1],
        labels={"geo_risk": "Geo Risk", "share": "Share %"},
        title=f"Supplier Geopolitical Risk \u2014 {description}",
        template="plotly_white",
    )
    choropleth_fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=350,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="LightGray",
            projection_type="natural earth",
        ),
        font_family="Inter",
    )

    # -- Radar Chart: Score Decomposition --
    radar_fig = go.Figure()
    radar_fig.add_trace(go.Scatterpolar(
        r=[product["hhi"], product["basket_geo_risk"], product["substitutability_score"]],
        theta=["HHI Concentration", "Geo Risk", "Substitutability"],
        fill="toself",
        name=hs6,
        fillcolor="rgba(37, 99, 235, 0.15)",
        line=dict(color="#2563eb"),
    ))
    radar_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        title=f"Score Decomposition \u2014 {hs6}",
        template="plotly_white",
        font_family="Inter",
        margin=dict(l=60, r=60, t=50, b=40),
        height=300,
    )

    # -- Bar Chart: Supplier Share Concentration --
    top_suppliers = suppliers[:10]
    bar_fig = px.bar(
        x=[s["exporter_name"] for s in top_suppliers],
        y=[s["supplier_share"] * 100 for s in top_suppliers],
        color=[s["exporter_geo_risk"] for s in top_suppliers],
        color_continuous_scale="RdYlGn_r",
        range_color=[0, 1],
        labels={"x": "Supplier", "y": "Share %", "color": "Geo Risk"},
        title=f"Top Suppliers by Share \u2014 {hs6}",
        template="plotly_white",
    )
    bar_fig.update_layout(
        xaxis_tickangle=-45,
        font_family="Inter",
        margin=dict(l=60, r=20, t=50, b=80),
        height=300,
        showlegend=False,
    )

    # -- Trend Chart --
    trend_data = data.get_score_trend(country_iso3, hs6)
    if trend_data:
        min_year, max_year = data.get_year_range()
        all_years = list(range(min_year, max_year + 1))
        trend_by_year = {r["year"]: r for r in trend_data}

        # Build series with None gaps for missing years
        years = all_years
        composite_vals = [trend_by_year[y]["composite_score"] if y in trend_by_year else None for y in all_years]
        hhi_vals = [trend_by_year[y]["hhi"] if y in trend_by_year else None for y in all_years]
        geo_vals = [trend_by_year[y]["basket_geo_risk"] if y in trend_by_year else None for y in all_years]
        ess_vals = [trend_by_year[y]["substitutability_score"] if y in trend_by_year else None for y in all_years]

        trend_fig = go.Figure()
        trend_fig.add_trace(go.Scatter(
            x=years, y=composite_vals, mode="lines+markers",
            name="Composite", line=dict(color="#2563eb", width=2),
            marker=dict(size=4), connectgaps=False,
        ))
        trend_fig.add_trace(go.Scatter(
            x=years, y=hhi_vals, mode="lines",
            name="HHI", line=dict(color="#8b5cf6", width=1.5, dash="dot"),
            visible="legendonly", connectgaps=False,
        ))
        trend_fig.add_trace(go.Scatter(
            x=years, y=geo_vals, mode="lines",
            name="Geo Risk", line=dict(color="#dc2626", width=1.5, dash="dot"),
            visible="legendonly", connectgaps=False,
        ))
        trend_fig.add_trace(go.Scatter(
            x=years, y=ess_vals, mode="lines",
            name="Substitutability", line=dict(color="#059669", width=1.5, dash="dot"),
            visible="legendonly", connectgaps=False,
        ))
        trend_fig.add_vline(
            x=year, line_dash="dash", line_color="gray",
            annotation_text="Selected", annotation_position="top right",
        )
        trend_fig.update_layout(
            template="plotly_white", font_family="Inter",
            title=f"Score Trend \u2014 {hs6}",
            xaxis_title="Year", yaxis_title="Score",
            yaxis_range=[0, 1], height=300,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=50, r=20, t=60, b=40),
        )
        trend_section = dbc.Row([
            dbc.Col([
                html.H6("Score Trend (1995\u20132024)", className="fw-semibold mb-2"),
                dcc.Graph(id="drilldown-trend-chart", figure=trend_fig, config={"displayModeBar": False}),
            ], md=12),
        ], className="g-3 mt-3")
    else:
        trend_section = dbc.Row([
            dbc.Col(html.P("No historical data available.", className="text-muted"), md=12),
        ], className="g-3 mt-3")

    # -- Assemble drill-down panel --
    weighted = product.get("weighted_composite", product.get("composite_score", 0))

    return html.Div([
        html.Hr(className="my-4"),
        html.Div([
            html.H5(f"Product Detail: {hs6} \u2014 {description}", className="mb-1"),
            html.Span(
                f"Flags: {', '.join(product.get('flags') or []) or '\u2014'} \u00b7 "
                f"Composite: {weighted:.3f}",
                className="text-muted small",
            ),
        ], className="drilldown-header mb-3"),

        dbc.Row([
            dbc.Col([
                html.H6("Supplier Breakdown", className="fw-semibold mb-2"),
                supplier_table,
            ], md=6),
            dbc.Col([
                dcc.Graph(
                    id="supplier-choropleth",
                    figure=choropleth_fig,
                    config={"displayModeBar": False},
                ),
            ], md=6),
        ], className="g-3"),

        dbc.Row([
            dbc.Col([
                dcc.Graph(
                    id="product-radar",
                    figure=radar_fig,
                    config={"displayModeBar": False},
                ),
            ], md=5),
            dbc.Col([
                dcc.Graph(
                    id="supplier-bar",
                    figure=bar_fig,
                    config={"displayModeBar": False},
                ),
            ], md=7),
        ], className="g-3 mt-3"),

        trend_section,
    ], className="drilldown-panel")
