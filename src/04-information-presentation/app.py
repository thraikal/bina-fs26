import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from dash import Dash, html, dcc, Input, Output, ctx

import tabs.overview as overview
import tabs.sq1 as sq1
import tabs.sq2 as sq2
import tabs.sq3 as sq3
import tabs.sq4 as sq4

app = Dash()
app.title = "Gesundheitskosten, Alterung & Prämienbelastung"

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        {%favicon%}
        {%css%}
        <style>
            body {
                margin: 0;
                font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
            }
            .tab:hover * {
                color: #d8232a;
            }
            .year-step-btn {
                background: transparent;
                border: 1.5px solid #d8232a;
                color: #d8232a;
                font-size: 16px;
                font-weight: 600;
                padding: 4px 14px;
                cursor: pointer;
                border-radius: 4px;
                line-height: 1.4;
                letter-spacing: 0.02em;
                transition: background 0.15s, color 0.15s;
            }
            .year-step-btn:hover {
                background: #d8232a;
                color: #ffffff;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

app.layout = [
    html.Div(
        html.Div(
            html.Div('Gesundheitskosten, Alterung & Prämienbelastung in der Schweiz'),
            style={"width": "1500px", "max-width": "1500px", "margin": "auto", "paddingLeft": "40px"},
        ),
        style={
            "display": "flex", "height": "46px",
            "color": "#ffffff", "backgroundColor": "#2f4356", "alignItems": "center",
        },
    ),
    html.Div([
        dcc.Tabs(id="tabs", value="overview", children=[
            overview.tab,
            sq1.tab,
            sq2.tab,
            sq3.tab,
            sq4.tab,
        ]),
    ], style={"max-width": "1500px", "margin": "auto", "minHeight": "calc(100vh - 92px)", "background": "#ffffff"}),
    html.Div(
        html.Div(
            html.Div('Case Study · Business Intelligence & Analytics · MSc Wirtschaftsinformatik · 2026'),
            style={"width": "1500px", "max-width": "1500px", "margin": "auto", "paddingLeft": "40px"},
        ),
        style={
            "display": "flex", "height": "46px",
            "color": "#ffffff", "backgroundColor": "#2f4356", "alignItems": "center",
        },
    ),
]

@app.callback(
    Output("tabs", "value"),
    Input("kpi-cost", "n_clicks"),
    Input("kpi-premium", "n_clicks"),
    Input("kpi-age", "n_clicks"),
    Input("overview-priority-table", "n_clicks"),
    prevent_initial_call=True,
)
def _navigate_from_kpi(_c, _pr, _a, _t):
    return {"kpi-cost": "sq1", "kpi-premium": "sq2", "kpi-age": "sq3", "overview-priority-table": "sq4"}.get(ctx.triggered_id, "overview")


if __name__ == '__main__':
    app.run(debug=True)
