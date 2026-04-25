from dash import Dash, html, dcc, callback, Output, Input, no_update
import plotly.express as px
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import plotly.graph_objects as go
import requests
import certifi
import io


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
url = "https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv"

response = requests.get(url, timeout=60, verify=certifi.where())
response.raise_for_status()

df = pd.read_csv(io.StringIO(response.text))

#df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

# ==============================
# SQ1: Health cost per person
# ==============================


_df_costs_raw = pd.read_csv(ROOT / "data/processed/gesundheitskosten.csv")
_df_pop_raw = pd.read_csv(ROOT / "data/processed/bevoelkerung.csv")

_df_costs_canton = (
    _df_costs_raw[
        (_df_costs_raw['age'] == 'Total') & (_df_costs_raw['cantons'] != 'Total')
    ][['year', 'cantons', 'costs_chf']]
    .rename(columns={'cantons': 'canton'})
)

_df_pop_canton = (
    _df_pop_raw[
        (_df_pop_raw['age_label'] == 'Alter - Total') & (_df_pop_raw['canton'] != 'Schweiz')
    ][['year', 'canton', 'population']]
)

df_per_person = (
    _df_costs_canton.merge(_df_pop_canton, on=['year', 'canton'])
    .assign(cost_per_capita=lambda d: d['costs_chf'] / d['population'])
)

YEARS = sorted(df_per_person['year'].unique())


# ==============================
# SQ3: Aging & costs
# ==============================

_df_66_raw = pd.read_csv(ROOT / "data/processed/bevoelkerung_66_share.csv")
_df_kantone = pd.read_csv(ROOT / "data/processed/kantone.csv")

df_aging = (
    df_per_person[['year', 'canton', 'cost_per_capita']]
    .merge(
        _df_66_raw[_df_66_raw['canton'] != 'Schweiz'][['year', 'canton', 'population_share_66_plus']],
        on=['year', 'canton'],
    )
    .merge(_df_kantone, on='canton')
    .assign(share_pct=lambda d: d['population_share_66_plus'] * 100)
)

SQ3_YEARS = sorted(df_aging['year'].unique())

_QUADRANT_COLORS = {
    'Doppelbelastung': '#c0392b',
    'Kostenausreisser': '#e67e22',
    'Effizient trotz Alter': '#27ae60',
    'Tiefe Belastung': '#2980b9',
}


def _sq3_quadrant(dff: pd.DataFrame) -> pd.Series:
    avg_x = dff['share_pct'].mean()
    avg_y = dff['cost_per_capita'].mean()
    hi_x = dff['share_pct'] >= avg_x
    hi_y = dff['cost_per_capita'] >= avg_y
    labels = list(_QUADRANT_COLORS)
    return pd.Series(
        np.select(
            [hi_x & hi_y, ~hi_x & hi_y, hi_x & ~hi_y],
            labels[:3],
            default=labels[3],
        ),
        index=dff.index,
    )


def _build_sq3_scatter(year: int) -> go.Figure:
    dff = df_aging[df_aging['year'] == year].copy()
    dff['quadrant'] = _sq3_quadrant(dff)

    x, y = dff['share_pct'].values, dff['cost_per_capita'].values
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    r2 = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - y.mean()) ** 2)
    x_line = np.array([x.min(), x.max()])

    avg_x, avg_y = x.mean(), y.mean()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_line, y=slope * x_line + intercept, mode='lines',
        line=dict(color='#999', width=1.5, dash='dash'),
        name=f'Regression (R² = {r2:.2f})',
        hoverinfo='skip',
    ))

    fig.add_vline(x=avg_x, line_dash='dot', line_color='#ccc', line_width=1)
    fig.add_hline(y=avg_y, line_dash='dot', line_color='#ccc', line_width=1)

    for quad, color in _QUADRANT_COLORS.items():
        sub = dff[dff['quadrant'] == quad]
        fig.add_trace(go.Scatter(
            x=sub['share_pct'], y=sub['cost_per_capita'],
            mode='markers+text',
            text=sub['icc'],
            textposition='top center',
            textfont=dict(size=10, color=color),
            marker=dict(size=10, color=color, opacity=0.85),
            name=quad,
            customdata=sub[['canton', 'share_pct', 'cost_per_capita']].values,
            hovertemplate='<b>%{customdata[0]}</b><br>66+: %{customdata[1]:.1f}%<br>Kosten: CHF %{customdata[2]:,.0f}<extra></extra>',
        ))

    fig.update_layout(
        height=480,
        margin=dict(l=60, t=30, b=60, r=20),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(size=12, color='#888'),
        xaxis=dict(title='Anteil Bevölkerung 66+ (%)', gridcolor='#f0f0f0', zeroline=False),
        yaxis=dict(title='Gesundheitskosten pro Kopf (CHF)', gridcolor='#f0f0f0', zeroline=False),
        legend=dict(orientation='h', x=0, y=-0.18, xanchor='left', bgcolor='rgba(0,0,0,0)'),
        annotations=[dict(
            x=0.99, y=0.99, xref='paper', yref='paper',
            text=f'R² = {r2:.2f}',
            showarrow=False, xanchor='right', yanchor='top',
            bgcolor='rgba(255,255,255,0.85)', bordercolor='#ddd', borderwidth=1,
            font=dict(size=13, color='#333'),
        )],
    )
    return fig


def _build_sq3_map(year: int) -> go.Figure:
    dff = df_aging[df_aging['year'] == year]
    fig = px.choropleth(
        dff, geojson=cantons,
        locations='canton', featureidkey='properties.name',
        color='share_pct',
        hover_name='canton',
        hover_data={'share_pct': ':.1f', 'cost_per_capita': ':,.0f', 'canton': False},
        color_continuous_scale='Oranges',
        labels={'share_pct': '% 66+', 'cost_per_capita': 'CHF/Kopf'},
    )
    fig.update_geos(fitbounds='locations', visible=False)
    fig.update_coloraxes(colorbar=dict(
        orientation='h', x=0.5, y=1.01, xanchor='center', yanchor='bottom',
        thickness=10, len=0.7, title_text='Anteil 66+ (%)', title_side='top',
    ))
    fig.update_layout(margin=dict(l=0, r=0, t=45, b=0), height=480, font=dict(size=12, color='#888'))
    return fig


def _build_sq3_kpis(year: int) -> list:
    dff = df_aging[df_aging['year'] == year]
    avg_share = dff['share_pct'].mean()
    top = dff.loc[dff['share_pct'].idxmax()]
    r = np.corrcoef(dff['share_pct'].values, dff['cost_per_capita'].values)[0, 1]

    def _kpi(title, value, note=''):
        return html.Div([
            html.Div(title, style={"fontSize": "11px", "color": "#888", "textTransform": "uppercase",
                                   "letterSpacing": "0.05em", "marginBottom": "4px"}),
            html.Div(value, style={"fontSize": "22px", "fontWeight": "700", "color": "#2f4356"}),
            html.Div(note, style={"fontSize": "11px", "color": "#aaa", "marginTop": "2px"}),
        ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                  "padding": "14px 18px", "flex": "1", "minWidth": "140px"})

    return [
        _kpi("Ø Anteil 66+", f"{avg_share:.1f}%", "alle Kantone"),
        _kpi("Höchster 66+-Anteil", top['icc'], f"{top['share_pct']:.1f}% · {top['canton']}"),
        _kpi("Korrelation r", f"{r:.2f}", "Alterung ↔ Kosten/Kopf"),
    ]


_sq3_initial_scatter = _build_sq3_scatter(SQ3_YEARS[-1])
_sq3_initial_map = _build_sq3_map(SQ3_YEARS[-1])
_sq3_initial_kpis = _build_sq3_kpis(SQ3_YEARS[-1])


def _build_sq1_map(year: int):
    dff = df_per_person[df_per_person['year'] == year]
    fig = px.choropleth(
        dff,
        geojson=cantons,
        locations='canton',
        featureidkey='properties.name',
        color='cost_per_capita',
        hover_name='canton',
        hover_data={'cost_per_capita': ':,.0f'},
        color_continuous_scale='Reds',
        labels={'cost_per_capita': 'CHF pro Kopf'},
    )
    fig.update_geos(fitbounds='locations', visible=False)
    fig.update_coloraxes(colorbar=dict(
        orientation='h',
        x=0.5, y=1.01,
        xanchor='center', yanchor='bottom',
        thickness=10, len=0.7,
        title_text='CHF pro Kopf',
        title_side='top',
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=45, b=0),
        height=480,
        font=dict(size=12, color='#888'),
    )
    return fig


_sq1_initial_figure = _build_sq1_map(YEARS[-1])


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
                        "padding": "16px 20px", "marginBottom": "8px",
                    }),
                    html.Div(
                        dcc.Loading(type='circle', color='#d8232a',
                            children=html.Div(id='sq1-loading-anchor'),
                        ),
                        style={"height": "8px", "marginBottom": "8px", "display": "flex", "justifyContent": "center"},
                    ),
                    html.Div([
                        dcc.Store(id='sq1-active-canton'),
                        html.Div([
                            dcc.Graph(id='sq1-map', figure=_sq1_initial_figure, config={"displayModeBar": False, "scrollZoom": True}, clear_on_unhover=True),
                        ], style={
                            "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                            "padding": "12px", "flex": "1",
                        }),
                        html.Div([
                            dcc.Graph(id='sq1-trend', config={"displayModeBar": False}, clear_on_unhover=True),
                        ], style={
                            "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                            "padding": "12px", "flex": "1",
                        }),
                    ], style={"display": "flex", "gap": "16px"}),
                ], style={"maxWidth": "1000px", "margin": "auto", "padding": "24px 32px"}),
            ]),
            dcc.Tab(label="2. Prämien & Kosten", value="sq2", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[]),
            dcc.Tab(label="3. Alterung & Kosten", value="sq3", className="tab", style=TAB_STYLE, selected_style=TAB_SELECTED, children=[
                html.Div([
                    html.Div([
                        html.Div("Alterung & Gesundheitskosten", style={
                            "fontSize": "18px", "fontWeight": "700", "color": "#2f4356", "lineHeight": "1.3",
                        }),
                        html.Div("Korrelation zwischen Anteil 66+ und Kosten pro Kopf nach Kanton", style={
                            "fontSize": "12px", "color": "#888", "marginTop": "4px",
                        }),
                    ], style={"marginBottom": "20px"}),
                    html.Div(id='sq3-kpis', children=_sq3_initial_kpis,
                             style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),
                    html.Div([
                        html.Div([
                            html.Label("Jahr:", style={"fontWeight": "600", "whiteSpace": "nowrap", "fontSize": "13px", "color": "#555"}),
                            html.Div(year_slider("sq3-year-slider", SQ3_YEARS), style={"flex": "1"}),
                            html.Button("‹", id='sq3-year-prev', n_clicks=0, className='year-step-btn'),
                            html.Button("›", id='sq3-year-next', n_clicks=0, className='year-step-btn'),
                        ], style={"display": "flex", "alignItems": "center", "gap": "12px"}),
                    ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                              "padding": "16px 20px", "marginBottom": "16px"}),
                    html.Div([
                        html.Div([
                            html.H3("Korrelation: Bevölkerungsalterung & Kosten pro Kopf", style={"margin": "0 0 2px", "fontSize": "13px", "color": "#555"}),
                            html.P("Gestrichelte Linie = Regressionsgerade · Kreuzlinien = Schweizer Durchschnitt", style={"fontSize": "11px", "color": "#bbb", "margin": "0 0 8px"}),
                            dcc.Graph(id='sq3-scatter', figure=_sq3_initial_scatter, config={"displayModeBar": False}),
                        ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                                  "padding": "12px", "flex": "2"}),
                        html.Div([
                            html.H3("Anteil 66+ nach Kanton", style={"margin": "0 0 8px", "fontSize": "13px", "color": "#555"}),
                            dcc.Graph(id='sq3-map', figure=_sq3_initial_map, config={"displayModeBar": False}),
                        ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                                  "padding": "12px", "flex": "1"}),
                    ], style={"display": "flex", "gap": "16px"}),
                ], style={"maxWidth": "1000px", "margin": "auto", "padding": "24px 32px"}),
            ]),
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

_BTN_ON  = {}
_BTN_OFF = {"border": "1.5px solid #ccc", "color": "#ccc", "cursor": "default", "pointerEvents": "none"}


@callback(
    Output('sq1-year-slider', 'value'),
    Output('sq1-year-prev', 'style'),
    Output('sq1-year-next', 'style'),
    Input('sq1-year-prev', 'n_clicks'),
    Input('sq1-year-next', 'n_clicks'),
    Input('sq1-year-slider', 'value'),
    Input('sq1-trend', 'clickData'),
)
def sq1_step_year(_prev, _next, current_year, trend_click):
    from dash import ctx
    new_year = current_year
    if ctx.triggered_id == 'sq1-year-prev':
        new_year = max(YEARS[0], current_year - 1)
    elif ctx.triggered_id == 'sq1-year-next':
        new_year = min(YEARS[-1], current_year + 1)
    elif ctx.triggered_id == 'sq1-trend' and trend_click and trend_click['points']:
        clicked_year = int(trend_click['points'][0]['x'])
        if clicked_year in YEARS:
            new_year = clicked_year
    slider_out = new_year if new_year != current_year else no_update
    return slider_out, _BTN_OFF if new_year == YEARS[0] else _BTN_ON, _BTN_OFF if new_year == YEARS[-1] else _BTN_ON


@callback(Output('sq1-map', 'figure'), Output('sq1-loading-anchor', 'children'), Input('sq1-year-slider', 'value'))
def sq1_map(year):
    return _build_sq1_map(year), None


@callback(
    Output('sq1-active-canton', 'data'),
    Input('sq1-map', 'hoverData'),
    Input('sq1-map', 'clickData'),
    Input('sq1-trend', 'hoverData'),
)
def sq1_active_canton(map_hover, map_click, trend_hover):
    # click locks the selection permanently
    if map_click and map_click['points']:
        return map_click['points'][0]['location']
    # hovering the trend line is more direct than hovering the map
    if trend_hover and trend_hover['points']:
        return trend_hover['points'][0]['customdata'][0]
    if map_hover and map_hover['points']:
        return map_hover['points'][0]['location']
    return None


@callback(
    Output('sq1-trend', 'figure'),
    Input('sq1-year-slider', 'value'),
    Input('sq1-active-canton', 'data'),
)
def sq1_trend(selected_year, highlighted):
    fig = px.line(
        df_per_person.sort_values('year'),
        x='year',
        y='cost_per_capita',
        color='canton',
        markers=True,
        custom_data=['canton'],
        labels={'year': 'Jahr', 'cost_per_capita': 'CHF pro Kopf', 'canton': 'Kanton'},
    )

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
        margin=dict(l=55, t=8, b=0, r=8),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(size=12, color='#888'),
        xaxis=dict(range=[YEARS[0] - 0.3, YEARS[-1] + 0.3]),
        legend=dict(orientation='h', x=0.01, y=0.99, xanchor='left', yanchor='top',
                    bgcolor='rgba(255,255,255,0.7)'),
    )
    return fig


@callback(
    Output('sq3-year-slider', 'value'),
    Output('sq3-year-prev', 'style'),
    Output('sq3-year-next', 'style'),
    Input('sq3-year-prev', 'n_clicks'),
    Input('sq3-year-next', 'n_clicks'),
    Input('sq3-year-slider', 'value'),
)
def sq3_step_year(_prev, _next, current_year):
    from dash import ctx
    new_year = current_year
    if ctx.triggered_id == 'sq3-year-prev':
        new_year = max(SQ3_YEARS[0], current_year - 1)
    elif ctx.triggered_id == 'sq3-year-next':
        new_year = min(SQ3_YEARS[-1], current_year + 1)
    slider_out = new_year if new_year != current_year else no_update
    return slider_out, _BTN_OFF if new_year == SQ3_YEARS[0] else _BTN_ON, _BTN_OFF if new_year == SQ3_YEARS[-1] else _BTN_ON


@callback(
    Output('sq3-scatter', 'figure'),
    Output('sq3-map', 'figure'),
    Output('sq3-kpis', 'children'),
    Input('sq3-year-slider', 'value'),
)
def sq3_charts(year):
    return _build_sq3_scatter(year), _build_sq3_map(year), _build_sq3_kpis(year)


if __name__ == '__main__':
    app.run(debug=True)