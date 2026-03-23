"""Product Risk stub page for DependencyAtlas (Phase 5 will add full content)."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard import data

dash.register_page(
    __name__,
    path="/product",
    name="Product Risk",
    title="DependencyAtlas — Product Risk",
)


def layout():
    """Callable layout — evaluated per request so get_default_product() is called at render time."""
    default_product = data.get_default_product()
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(html.H3("Product Risk"), width=12),
                className="mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    dcc.Loading(
                        id="loading-product-content",
                        type="circle",
                        children=html.Div(
                            id="product-content-placeholder",
                            children=dbc.Alert(
                                f"Product view coming in Phase 5. Default selection: {default_product}",
                                color="info",
                                className="mt-3",
                            ),
                            style={"minHeight": "400px"},
                        ),
                    ),
                    width=12,
                )
            ),
        ],
        fluid=True,
        className="py-4",
    )
