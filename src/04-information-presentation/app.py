from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import json
from pathlib import Path
import plotly.graph_objects as go

DATA_DIR = Path(__file__).parents[2] / "data"

with open(DATA_DIR / "cantons.geojson") as f:
    cantons = json.load(f)

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

app = Dash()

app.layout = [
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