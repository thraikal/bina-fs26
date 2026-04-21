from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path
import plotly.graph_objects as go


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))
from utils.fetch_cantons import load_cantons_geojson


# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------

TAB_STYLE = {
    "borderTop": "none",
    "userSelect": "none",
}

TAB_SELECTED = {
    **TAB_STYLE,
    "borderBottom": "3px solid #d8232a",
    "color": "#d8232a",
}


# ---------------------------------------------------------
# Data loading
# ---------------------------------------------------------

cantons = load_cantons_geojson(ROOT / "data/dashboard")

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

# ==============================
# SQ1: Health cost per person
# ==============================

_POP_TO_COSTS = {
    'Schweiz': 'Total',
    'Zürich': 'Zurich',
    'Bern / Berne': 'Bern',
    'Luzern': 'Lucerne',
    'Fribourg / Freiburg': 'Fribourg',
    'Genève': 'Geneva',
    'Graubünden / Grigioni / Grischun': 'Graubünden',
    'Valais / Wallis': 'Valais',
}

_COSTS_TO_GEO = {
    'Zurich': 'Zürich',
    'Lucerne': 'Luzern',
    'Geneva': 'Genève',
}

_df_costs_raw = pd.read_csv(ROOT / "data/processed/gesundheitskosten.csv")
_df_pop_raw = pd.read_csv(ROOT / "data/interim/bevoelkerung_2011_2026.csv", encoding='utf-8-sig')

_df_costs_canton = (
    _df_costs_raw[
        (_df_costs_raw['AGE'] == '_T') & (_df_costs_raw['CANTON'] != '_T')
    ][['TIME_PERIOD', 'Swiss cantons', 'costs_chf']]
    .rename(columns={'TIME_PERIOD': 'year', 'Swiss cantons': 'canton'})
)

_df_pop_canton = (
    _df_pop_raw[_df_pop_raw['Alter'] == 'Alter - Total']
    [['Jahr', 'Kanton', 'Bestand am 31. Dezember']]
    .rename(columns={'Jahr': 'year', 'Kanton': 'canton', 'Bestand am 31. Dezember': 'population'})
    .copy()
)
_df_pop_canton['canton'] = _df_pop_canton['canton'].replace(_POP_TO_COSTS)
_df_pop_canton = _df_pop_canton[_df_pop_canton['canton'] != 'Schweiz']

df_per_person = (
    _df_costs_canton.merge(_df_pop_canton, on=['year', 'canton'])
    .assign(
        cost_per_capita=lambda d: d['costs_chf'] / d['population'],
        geo_name=lambda d: d['canton'].replace(_COSTS_TO_GEO),
    )
)

YEARS = sorted(df_per_person['year'].unique())


# ---------------------------------------------------------
# UI components
# ---------------------------------------------------------
def year_slider(slider_id: str, years: list[int]) -> dcc.Slider:
    years = [int(y) for y in years]
    marks = {y: str(y) for y in years if y % 5 == 0 or y == years[0] or y == years[-1]}
    return dcc.Slider(
        id=slider_id,
        min=years[0], max=years[-1], step=1,
        value=years[-1],
        marks=marks,
        tooltip={"placement": "bottom", "always_visible": False},
    )


# ---------------------------------------------------------
# App
# ---------------------------------------------------------

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
            style={"width": "1500px", "max-width": "1500px", "margin": "auto", "paddingLeft": "40px",}
        ),
        style={
            "display": "flex",
            "height": "46px",
            "color": "#ffffff",
            "backgroundColor": "#2f4356",
            "alignItems": "center",
        }
    ),
    html.Div([
        dcc.Tabs(id="tabs", value="overview", children=[
            dcc.Tab(label="Übersicht", value="overview", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[
                html.Div(children=[
                    html.H1('From Data to Decisions', style={'textAlign': 'center'}),
                    dcc.Dropdown(df.country.unique(), 'Switzerland', id='country-dropdown'),
                    dcc.Graph(id='graph-content'),
                    dcc.Graph(id='cantons-map')
                ], style={"max-width": "1000px", "margin": "auto"})
            ]),
            dcc.Tab(label="1. Kosten pro Kopf", value="sq1", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[
                html.Div([
                    html.H1("Gesundheitskosten pro Kopf nach Kanton", style={'textAlign': 'left'}),
                    html.Div([
                        html.Label("Jahr:", style={'marginRight': '12px', 'fontWeight': 'bold', 'whiteSpace': 'nowrap'}),
                        html.Div(year_slider("sq1-year-slider", YEARS), style={'flex': '1'}),
                        html.Button("‹", id='sq1-year-prev', n_clicks=0, className='year-step-btn'),
                        html.Button("›", id='sq1-year-next', n_clicks=0, className='year-step-btn'),
                    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px', 'gap': '8px'}),
                    dcc.Graph(id='sq1-map'),
                ], style={'maxWidth': '1200px', 'margin': 'auto', 'padding': '20px'}),
            ]),
            dcc.Tab(label="2. Prämien & Kosten", value="sq2", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[]),
            dcc.Tab(label="3. Alterung & Kosten", value="sq3", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[]),
            dcc.Tab(label="4. Segmente & Prognose", value="sq4", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[]),
        ]),
    ], style={"max-width": "1500px", "margin": "auto", "minHeight": "calc(100vh - 92px)"}),
    html.Div(
        html.Div(
            html.Div('Case Study · Business Intelligence & Analytics · MSc Wirtschaftsinformatik · 2026'),
            style={"width": "1500px", "max-width": "1500px", "margin": "auto", "paddingLeft": "40px",}
        ),
        style={
            "display": "flex",
            "height": "46px",
            "color": "#ffffff",
            "backgroundColor": "#2f4356",
            "alignItems": "center",
        }
    ),
]


# ---------------------------------------------------------
# Callbacks
# ---------------------------------------------------------

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

@callback(
    Output('sq1-year-slider', 'value'),
    Input('sq1-year-prev', 'n_clicks'),
    Input('sq1-year-next', 'n_clicks'),
    Input('sq1-year-slider', 'value'),
)
def sq1_step_year(_prev, _next, current_year):
    from dash import ctx
    if ctx.triggered_id == 'sq1-year-prev':
        return max(YEARS[0], current_year - 1)
    if ctx.triggered_id == 'sq1-year-next':
        return min(YEARS[-1], current_year + 1)
    return current_year


@callback(Output('sq1-map', 'figure'), Input('sq1-year-slider', 'value'))
def sq1_map(year):
    dff = df_per_person[df_per_person['year'] == year]
    fig = px.choropleth(
        dff,
        geojson=cantons,
        locations='geo_name',
        featureidkey='properties.name',
        color='cost_per_capita',
        hover_name='canton',
        hover_data={'cost_per_capita': ':,.0f', 'geo_name': False},
        color_continuous_scale='Reds',
        labels={'cost_per_capita': 'CHF pro Kopf'},
        title=f'Gesundheitskosten pro Kopf {year}',
    )
    fig.update_geos(fitbounds='locations', visible=False)
    fig.update_layout(margin={'r': 0, 't': 40, 'l': 0, 'b': 0}, height=480)
    return fig


if __name__ == '__main__':
    app.run(debug=True)