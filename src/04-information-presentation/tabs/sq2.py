from dash import dcc, html

from styles import TAB_STYLE, TAB_SELECTED

tab = dcc.Tab(
    label="2. Prämien & Kosten", value="sq2", className="tab",
    style=TAB_STYLE, selected_style=TAB_SELECTED,
    children=[],
)
