"""Dash application entry point for DependencyAtlas."""

import dash
import dash_bootstrap_components as dbc

from dashboard.layout import create_layout

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.LUX,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
    ],
    suppress_callback_exceptions=True,
)

app.layout = create_layout()

# WSGI entry point for gunicorn: gunicorn dashboard.app:server
server = app.server

if __name__ == "__main__":
    app.run(debug=True, port=8050)
