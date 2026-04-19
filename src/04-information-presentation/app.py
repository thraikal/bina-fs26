from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path
import plotly.graph_objects as go

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))
from utils.fetch_cantons import load_cantons_geojson

cantons = load_cantons_geojson(ROOT / "data/dashboard")

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

app = Dash()

app.title = "Gesundheitskosten, Alterung & Prämienbelastung"

# override the default index.html template to set body margin to 0
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
        'Gesundheitskosten, Alterung & Prämienbelastung in der Schweiz',
        style={
            "display": "flex",
            "height": "46px",
            "color": "#ffffff",
            "backgroundColor": "#2f4356",
            "paddingLeft": "40px",
            "alignItems": "center",
        }
    ),
    html.H1('From Data to Decisions', style={'textAlign': 'center'}),
    dcc.Dropdown(df.country.unique(), 'Switzerland', id='country-dropdown'),
    dcc.Graph(id='graph-content'),
    dcc.Graph(id='cantons-map')
]

@callback(
    Output('graph-content', 'figure'),
    Input('country-dropdown', 'value')
)
def update_graph(selected_country):
    dff = df[df.country == selected_country]
    return px.line(dff, x='year', y='pop')

@callback(
    Output('cantons-map', 'figure'),
    Input('cantons-map', 'id')
)
def render_map(_):
    fig = go.Figure(go.Choropleth(
        geojson=cantons,
        locations=[f['properties']['name'] for f in cantons['features']],
        featureidkey='properties.name',
        z=[f['properties']['einwohnerzahl'] for f in cantons['features']]
    ))
    fig.update_geos(fitbounds='locations', visible=False)
    return fig

if __name__ == '__main__':
    app.run(debug=True)