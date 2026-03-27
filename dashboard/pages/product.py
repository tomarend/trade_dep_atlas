"""Product Risk page — second analytical view for the DependencyAtlas dashboard."""

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import callback, dcc, html, Input, Output, State, no_update
from urllib.parse import parse_qs


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


def layout(**kwargs):
    products = data.get_product_list()
    default_hs6 = data.get_default_product()

    # Check for URL query parameter ?hs6=XXXXXX
    hs6_param = kwargs.get("hs6")
    if hs6_param:
        # Validate it exists in our product list
        for p in products:
            if p["hs6"] == hs6_param:
                default_hs6 = hs6_param
                break

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

        # -- Concentration bar chart --
        html.Div(id="product-concentration-container", className="mb-3"),

        # -- Data store --
        dcc.Store(id="product-data-store", storage_type="memory"),

        # -- AG Grid importer table --
        dcc.Loading(
            dag.AgGrid(
                id="importer-table",
                columnDefs=[
                    {
                        "field": "importer_iso3",
                        "headerName": "ISO3 Code",
                        "width": 100,
                        "filter": "agTextColumnFilter",
                        "pinned": "left",
                    },
                    {
                        "field": "importer_name",
                        "headerName": "Country",
                        "flex": 2,
                        "filter": "agTextColumnFilter",
                        # Cross-link to country view
                        "cellRenderer": "CountryLink",
                    },
                    {
                        "field": "composite_score",
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
                    {
                        "field": "sparkline",
                        "headerName": "Trend",
                        "width": 80,
                        "cellRenderer": "TrendSparkline",
                        "sortable": False,
                        "filter": False,
                        "resizable": False,
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

        # -- Choropleth map --
        html.Div(id="product-map-container", className="mt-3"),

        # -- Trend chart --
        html.Div(id="product-trend-container", className="mt-3"),

        # -- Sankey flow diagram --
        html.Div(id="product-sankey-container", className="mt-4"),

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
    [Input("product-hs6-selector", "value"),
     Input("year-store", "data")],
)
def load_product_data(hs6, year):
    """Load importer scores for the selected product and year into the store."""
    if not hs6:
        return no_update
    importers = data.get_importer_scores(hs6, year=year)
    sparklines = data.get_sparklines_for_product(hs6)
    for imp in importers:
        imp["sparkline"] = sparklines.get(imp["importer_iso3"], [])
    return importers


@callback(
    Output("product-summary-cards", "children"),
    Input("product-data-store", "data"),
    [State("product-hs6-selector", "value"),
     State("year-store", "data")],
)
def update_product_summary(importer_data, hs6, year):
    """Render summary cards and radar chart for the selected product."""
    if not importer_data or not hs6:
        return html.Div(
            "Select a product to view global dependency analysis.",
            className="text-muted p-3",
        )

    summary = data.get_product_summary(hs6, year=year)

    _BADGE_COLORS = {
        "crm_listed": "danger", "energy": "warning", "pharma": "info",
        "semiconductor": "secondary", "strategic_mineral": "dark",
        "fertilizer": "success", "hs22_only": "light",
    }
    flags = summary.get("flags") or []
    crm_year = summary.get("crm_listed_since")

    badge_row = html.Div(
        [
            dbc.Badge(
                (f"CRM {crm_year}" if (flag == "crm_listed" and crm_year)
                 else flag.replace("_", " ").title()),
                color=_BADGE_COLORS.get(flag, "secondary"),
                text_color="dark" if flag == "hs22_only" else None,
                className="me-1 mb-1",
            )
            for flag in flags
        ],
        className="mb-2",
    ) if flags else html.Div()

    avg_composite = summary["avg_composite"]
    level = "high" if avg_composite > 0.7 else "medium" if avg_composite > 0.4 else "low"

    # Product-level radar chart
    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(
        r=[summary["avg_hhi"], summary["avg_geo_risk"], summary["avg_substitutability"]],
        theta=["HHI Concentration", "Geo Risk", "Substitutability"],
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
        badge_row,
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
                html.P("Substitutability", className="text-muted mb-1 small fw-semibold"),
                html.H3(f"{summary['avg_substitutability']:.3f}", className="mb-0"),
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



@callback(
    Output("product-concentration-container", "children"),
    Input("product-hs6-selector", "value"),
    State("year-store", "data"),
)
def update_concentration_bars(hs6, year):
    """Render horizontal bar chart of top global exporters for the selected product."""
    if not hs6:
        return html.Div()
    exporters = data.get_product_exporters(hs6, year=year)
    if not exporters:
        return html.Div("No exporter data available.", className="text-muted p-3")

    # Build flag-emoji-prefixed labels using _ISO3_TO_ISO2 lookup
    tick_labels = []
    for r in exporters:
        iso2 = data._ISO3_TO_ISO2.get(r["exporter_iso3"], "").upper()
        if iso2 and len(iso2) == 2:
            emoji = "".join(chr(127397 + ord(c)) for c in iso2)
            tick_labels.append(f"{emoji} {r['exporter_name']}")
        else:
            tick_labels.append(r["exporter_name"])

    shares = [round(r["supplier_share"] * 100, 2) for r in exporters]
    geo_risks = [r["exporter_geo_risk"] for r in exporters]

    fig = go.Figure(go.Bar(
        y=tick_labels,
        x=shares,
        orientation="h",
        marker=dict(
            color=geo_risks,
            colorscale=[[0, "#22c55e"], [0.5, "#f59e0b"], [1, "#ef4444"]],
            cmin=0,
            cmax=1,
            showscale=True,
            colorbar=dict(title="Geo<br>Risk", thickness=12),
        ),
        text=[f"{s:.1f}%" for s in shares],
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f}% export share<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Global Export Share (%)",
        xaxis_range=[0, max(shares) * 1.25 if shares else 100],
        template="plotly_white",
        font_family="Inter",
        height=max(280, len(exporters) * 28),
        margin=dict(l=160, r=80, t=10, b=40),
        showlegend=False,
        yaxis=dict(autorange="reversed"),
    )

    return html.Div([
        html.H6("Export Concentration — Top Suppliers", className="fw-semibold mb-2"),
        dcc.Graph(
            id="product-concentration-chart",
            figure=fig,
            config={"displayModeBar": False},
        ),
    ])


@callback(
    Output("importer-table", "rowData"),
    Input("product-data-store", "data"),
)
def update_importer_table(importer_data):
    """Populate AG Grid with importer scores from the data store."""
    if not importer_data:
        return []
    return importer_data


@callback(
    Output("product-map-container", "children"),
    Input("product-data-store", "data"),
    State("product-hs6-selector", "value"),
)
def update_product_choropleth(importer_data, hs6):
    """Render choropleth world map of importers colored by dependency score."""
    if not importer_data:
        return html.Div(
            "Select a product to view the dependency map.",
            className="text-muted p-3",
        )

    # Look up product description
    description = hs6 or ""
    products = data.get_product_list()
    for p in products:
        if p["hs6"] == hs6:
            description = p["description"]
            break

    choropleth_data = {
        "iso3": [r["importer_iso3"] for r in importer_data],
        "name": [r["importer_name"] for r in importer_data],
        "composite_score": [r["composite_score"] for r in importer_data],
        "hhi": [r["hhi"] for r in importer_data],
    }

    fig = px.choropleth(
        choropleth_data,
        locations="iso3",
        color="composite_score",
        hover_name="name",
        hover_data={"composite_score": ":.3f", "hhi": ":.3f", "iso3": False},
        color_continuous_scale="YlOrRd",
        range_color=[0, 1],
        labels={"composite_score": "Dependency Score", "hhi": "HHI"},
        title=f"Import Dependency by Country \u2014 {description}",
        template="plotly_white",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=400,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="LightGray",
            projection_type="natural earth",
        ),
        font_family="Inter",
    )

    return dcc.Graph(
        id="product-choropleth",
        figure=fig,
        config={"displayModeBar": False},
    )



@callback(
    Output("product-trend-container", "children"),
    [Input("product-hs6-selector", "value"),
     Input("year-store", "data")],
)
def update_product_trend(hs6, year):
    """Render product-level trend chart showing global dependency evolution over time."""
    if not hs6:
        return html.Div()

    trend_data = data.get_product_trend(hs6)
    if not trend_data:
        return html.P("No historical data available.", className="text-muted")

    # Look up product description
    description = hs6
    products = data.get_product_list()
    for p in products:
        if p["hs6"] == hs6:
            description = p["description"]
            break

    min_year, max_year = data.get_year_range()
    all_years = list(range(min_year, max_year + 1))
    trend_by_year = {r["year"]: r for r in trend_data}

    composite_vals = [trend_by_year[y]["composite_score"] if y in trend_by_year else None for y in all_years]
    hhi_vals = [trend_by_year[y]["hhi"] if y in trend_by_year else None for y in all_years]
    geo_vals = [trend_by_year[y]["basket_geo_risk"] if y in trend_by_year else None for y in all_years]
    subst_vals = [trend_by_year[y]["substitutability_score"] if y in trend_by_year else None for y in all_years]

    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=all_years, y=composite_vals, mode="lines+markers",
        name="Composite", line=dict(color="#2563eb", width=2),
        marker=dict(size=4), connectgaps=False,
    ))
    trend_fig.add_trace(go.Scatter(
        x=all_years, y=hhi_vals, mode="lines",
        name="HHI", line=dict(color="#8b5cf6", width=1.5, dash="dot"),
        visible="legendonly", connectgaps=False,
    ))
    trend_fig.add_trace(go.Scatter(
        x=all_years, y=geo_vals, mode="lines",
        name="Geo Risk", line=dict(color="#dc2626", width=1.5, dash="dot"),
        visible="legendonly", connectgaps=False,
    ))
    trend_fig.add_trace(go.Scatter(
        x=all_years, y=subst_vals, mode="lines",
        name="Substitutability",
        hovertemplate="Substitutability: %{y:.3f}<br>√(global export HHI)<extra></extra>",
        line=dict(color="#059669", width=1.5, dash="dot"),
        visible="legendonly", connectgaps=False,
    ))
    trend_fig.add_vline(
        x=year, line_dash="dash", line_color="gray",
        annotation_text="Selected", annotation_position="top right",
    )
    trend_fig.update_layout(
        template="plotly_white", font_family="Inter",
        title=f"Global Dependency Trend \u2014 {description}",
        xaxis_title="Year", yaxis_title="Score",
        yaxis_range=[0, 1], height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=20, t=60, b=40),
    )

    return html.Div([
        html.H5("Dependency Trend", className="fw-semibold mt-4 mb-2"),
        dcc.Graph(id="product-trend-chart", figure=trend_fig, config={"displayModeBar": False}),
    ])



@callback(
    Output("product-sankey-container", "children"),
    [Input("product-hs6-selector", "value"),
     Input("year-store", "data")],
)
def update_sankey(hs6, year):
    """Render Sankey diagram of trade flows for the selected product and year."""
    if not hs6:
        return html.Div()

    flows = data.get_trade_flows(hs6, year)
    if not flows:
        return html.P("No trade flow data available for this product/year.", className="text-muted")

    # Look up product description
    description = hs6
    for p in data.get_product_list():
        if p["hs6"] == hs6:
            description = p["description"]
            break

    # Aggregate by exporter
    from collections import defaultdict
    exporter_totals = defaultdict(float)
    for f in flows:
        exporter_totals[f["exporter_iso3"]] += f.get("value_usd", 0) or 0

    top_exporters = sorted(exporter_totals, key=exporter_totals.get, reverse=True)[:10]
    top_exporter_set = set(top_exporters)

    # Aggregate by importer
    importer_totals = defaultdict(float)
    for f in flows:
        importer_totals[f["importer_iso3"]] += f.get("value_usd", 0) or 0

    top_importers = sorted(importer_totals, key=importer_totals.get, reverse=True)[:10]
    top_importer_set = set(top_importers)

    # Build name lookups
    exp_names = {}
    imp_names = {}
    exp_risk = {}
    for f in flows:
        exp_names[f["exporter_iso3"]] = f["exporter_name"]
        imp_names[f["importer_iso3"]] = f["importer_name"]
        exp_risk[f["exporter_iso3"]] = f.get("exporter_geo_risk", 0) or 0

    # Build node labels: exporters on left, importers on right
    exporter_labels = [exp_names.get(e, e) for e in top_exporters]
    has_other_exp = len(exporter_totals) > 10
    if has_other_exp:
        exporter_labels.append("Other (exporters)")

    importer_labels = [imp_names.get(i, i) for i in top_importers]
    has_other_imp = len(importer_totals) > 10
    if has_other_imp:
        importer_labels.append("Other (importers)")

    labels = exporter_labels + importer_labels
    exp_offset = 0
    imp_offset = len(exporter_labels)

    # Build exporter index
    exp_idx = {e: i + exp_offset for i, e in enumerate(top_exporters)}
    if has_other_exp:
        other_exp_idx = len(top_exporters)
    imp_idx = {i: idx + imp_offset for idx, i in enumerate(top_importers)}
    if has_other_imp:
        other_imp_idx = len(top_importers) + imp_offset

    # Build links
    from collections import Counter
    link_agg = Counter()
    link_risk = {}
    for f in flows:
        e = f["exporter_iso3"]
        m = f["importer_iso3"]
        val = f.get("value_usd", 0) or 0
        risk = f.get("exporter_geo_risk", 0) or 0

        src_idx = exp_idx.get(e, other_exp_idx if has_other_exp else None)
        tgt_idx = imp_idx.get(m, other_imp_idx if has_other_imp else None)
        if src_idx is not None and tgt_idx is not None:
            key = (src_idx, tgt_idx)
            link_agg[key] += val
            link_risk[key] = max(link_risk.get(key, 0), risk)

    sources = []
    targets = []
    values = []
    link_colors = []
    for (s, t), v in link_agg.items():
        if v > 0:
            sources.append(s)
            targets.append(t)
            values.append(v)
            risk = link_risk.get((s, t), 0)
            if risk > 0.7:
                link_colors.append("rgba(220, 38, 38, 0.4)")
            elif risk > 0.4:
                link_colors.append("rgba(217, 119, 6, 0.3)")
            else:
                link_colors.append("rgba(22, 163, 74, 0.2)")

    if not values:
        return html.P("No trade flow data to display.", className="text-muted")

    fig = go.Figure(go.Sankey(
        node=dict(
            label=labels,
            pad=15,
            thickness=20,
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
        ),
    ))
    fig.update_layout(
        template="plotly_white",
        font_family="Inter",
        title=f"Trade Flows \u2014 {description} ({year})",
        height=450,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return html.Div([
        html.H5("Trade Flow Analysis", className="fw-semibold mt-4 mb-3"),
        dcc.Graph(id="product-sankey", figure=fig, config={"displayModeBar": False}),
    ])

