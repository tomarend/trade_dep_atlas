"""Country Exposure stub page for DependencyAtlas (Phase 4 will add full content)."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard import data

dash.register_page(
    __name__,
    path="/country",
    name="Country Exposure",
    title="DependencyAtlas — Country Exposure",
)


def layout():
    """Callable layout — evaluated per request so get_default_country() is called at render time."""
    default_country = data.get_default_country()
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(html.H3("Country Exposure"), width=12),
                className="mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    dcc.Loading(
                        id="loading-country-content",
                        type="circle",
                        children=html.Div(
                            id="country-content-placeholder",
                            children=dbc.Alert(
                                f"Country view coming in Phase 4. Default selection: {default_country}",
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
