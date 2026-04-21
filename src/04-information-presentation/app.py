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

BORDER = "1px solid #acb4bd"
CARD_BG = "#ffffff"
LIGHT_BG = "#ffffff"

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
                html.Div([
                    html.Div([
                        html.Div("From Data to Decisions", style={
                            "fontSize": "18px", "fontWeight": "700", "color": "#2f4356",
                            "lineHeight": "1.3",
                        }),
                        html.Div("Gesundheitskosten, Alterung & Prämienbelastung in der Schweiz", style={
                            "fontSize": "12px", "color": "#888", "marginTop": "4px",
                        }),
                    ], style={"marginBottom": "20px"}),
                    html.Div([
                        html.Div([
                            html.Label("Land:", style={"fontWeight": "600", "marginBottom": "8px", "display": "block", "fontSize": "13px", "color": "#555"}),
                            dcc.Dropdown(df.country.unique(), 'Switzerland', id='country-dropdown'),
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
                        "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                        "padding": "20px",
                    }),
                ], style={"maxWidth": "1000px", "margin": "auto", "padding": "24px 32px"})
            ]),
            dcc.Tab(label="1. Kosten pro Kopf", value="sq1", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[
                html.Div([
                    html.Div([
                        html.Div("Gesundheitskosten pro Kopf nach Kanton", style={
                            "fontSize": "18px", "fontWeight": "700", "color": "#2f4356",
                            "lineHeight": "1.3",
                        }),
                        html.Div("Kantonaler Vergleich auf Basis OKP-Daten", style={
                            "fontSize": "12px", "color": "#888", "marginTop": "4px",
                        }),
                    ], style={"marginBottom": "20px"}),
                    html.Div([
                        html.Div([
                            html.Label("Jahr:", style={"fontWeight": "600", "whiteSpace": "nowrap", "fontSize": "13px", "color": "#555"}),
                            html.Div(year_slider("sq1-year-slider", YEARS), style={"flex": "1"}),
                            html.Button("‹", id='sq1-year-prev', n_clicks=0, className='year-step-btn'),
                            html.Button("›", id='sq1-year-next', n_clicks=0, className='year-step-btn'),
                        ], style={"display": "flex", "alignItems": "center", "gap": "12px"}),
                    ], style={
                        "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                        "padding": "16px 20px", "marginBottom": "16px",
                    }),
                    html.Div([
                        html.Div([
                            dcc.Graph(id='sq1-map', config={"displayModeBar": False}),
                        ], style={
                            "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                            "padding": "12px", "flex": "1",
                        }),
                        html.Div([
                            dcc.Graph(id='sq1-trend', config={"modeBarButtons": [["toImage"]], "displaylogo": False}),
                        ], style={
                            "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                            "padding": "12px", "flex": "1",
                        }),
                    ], style={"display": "flex", "gap": "16px"}),
                ], style={"maxWidth": "1000px", "margin": "auto", "padding": "24px 32px"}),
            ]),
            dcc.Tab(label="2. Prämien & Kosten", value="sq2", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[]),
            dcc.Tab(label="3. Alterung & Kosten", value="sq3", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[]),
            dcc.Tab(label="4. Segmente & Prognose", value="sq4", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[]),
        ]),
    ], style={"max-width": "1500px", "margin": "auto", "minHeight": "calc(100vh - 92px)", "background": LIGHT_BG}),
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
    fig.update_coloraxes(colorbar=dict(thickness=10, len=0.5, title_side='right'))
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=480)
    return fig


@callback(
    Output('sq1-trend', 'figure'),
    Input('sq1-year-slider', 'value'),
    Input('sq1-map', 'hoverData'),
    Input('sq1-map', 'clickData'),
)
def sq1_trend(selected_year, hover_data, click_data):
    # click locks a selection; hover overrides only when nothing is clicked
    active_data = click_data or hover_data
    selected_geo = None
    if active_data and active_data['points']:
        selected_geo = active_data['points'][0]['location']

    # map geo_name → canton label used by the line traces
    geo_to_canton = df_per_person.drop_duplicates('geo_name').set_index('geo_name')['canton']

    fig = px.line(
        df_per_person.sort_values('year'),
        x='year',
        y='cost_per_capita',
        color='canton',
        markers=True,
        labels={'year': 'Jahr', 'cost_per_capita': 'CHF pro Kopf', 'canton': 'Kanton'},
    )

    highlighted = None
    if selected_geo and selected_geo in geo_to_canton.index:
        highlighted = geo_to_canton[selected_geo]

    for trace in fig.data:
        if highlighted:
            if trace.name == highlighted:
                trace.line.width = 3
                trace.opacity = 1.0
                trace.showlegend = True
            else:
                trace.line.width = 1
                trace.opacity = 0.15
                trace.showlegend = False
        else:
            trace.showlegend = False

    fig.add_vline(x=selected_year, line_dash='dot', line_color='gray', opacity=0.6)
    fig.update_layout(
        height=480,
        margin=dict(t=8, b=0, r=8),
        xaxis=dict(range=[YEARS[0] - 0.3, YEARS[-1] + 0.3]),
        legend=dict(orientation='h', x=0.01, y=0.99, xanchor='left', yanchor='top',
                    bgcolor='rgba(255,255,255,0.7)'),
    )
    return fig


if __name__ == '__main__':
    app.run(debug=True)