import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, callback, Output, Input

from data import df_gapminder, cantons
from styles import BORDER, CARD_BG, TAB_STYLE, TAB_SELECTED

tab = dcc.Tab(
    label="Übersicht", value="overview", className="tab",
    style=TAB_STYLE, selected_style=TAB_SELECTED,
    children=[
        html.Div([
            html.Div([
                html.Div("From Data to Decisions", style={
                    "fontSize": "18px", "fontWeight": "700", "color": "#2f4356", "lineHeight": "1.3",
                }),
                html.Div("Gesundheitskosten, Alterung & Prämienbelastung in der Schweiz", style={
                    "fontSize": "12px", "color": "#888", "marginTop": "4px",
                }),
            ], style={"marginBottom": "20px"}),
            html.Div([
                html.Div([
                    html.Label("Land:", style={"fontWeight": "600", "marginBottom": "8px", "display": "block", "fontSize": "13px", "color": "#555"}),
                    dcc.Dropdown(df_gapminder.country.unique(), 'Switzerland', id='country-dropdown'),
                ], style={"marginBottom": "16px"}),
                dcc.Graph(id='graph-content', config={"displayModeBar": False}),
            ], style={
                "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                "padding": "20px", "marginBottom": "16px",
            }),
            html.Div([
                html.H3("Kantone - Bevölkerung", style={"margin": "0 0 12px", "fontSize": "13px", "color": "#555"}),
                dcc.Graph(id='cantons-map', config={"displayModeBar": False}),
            ], style={
                "background": CARD_BG, "border": BORDER, "borderRadius": "8px", "padding": "20px",
            }),
        ], style={"maxWidth": "1000px", "margin": "auto", "padding": "24px 32px"}),
    ],
)


@callback(Output('graph-content', 'figure'), Input('country-dropdown', 'value'))
def update_graph(selected_country):
    dff = df_gapminder[df_gapminder.country == selected_country]
    return px.line(dff, x='year', y='pop')


@callback(Output('cantons-map', 'figure'), Input('cantons-map', 'id'))
def render_map(_):
    fig = go.Figure(go.Choropleth(
        geojson=cantons,
        locations=[f['properties']['name'] for f in cantons['features']],
        featureidkey='properties.name',
        z=[f['properties']['einwohnerzahl'] for f in cantons['features']],
    ))
    fig.update_geos(fitbounds='locations', visible=False)
    return fig
