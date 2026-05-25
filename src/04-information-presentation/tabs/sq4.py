from dash import dcc, html

from styles import TAB_STYLE, TAB_SELECTED

tab = dcc.Tab(
    label="4. Segmente & Prognose", value="sq4", className="tab",
    style=TAB_STYLE, selected_style=TAB_SELECTED,
    children=[],
)
