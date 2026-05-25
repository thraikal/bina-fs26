import plotly.express as px
from dash import dcc, html, callback, Output, Input, no_update

from data import cantons, df_per_person, YEARS
from styles import BORDER, CARD_BG, TAB_STYLE, TAB_SELECTED, year_slider

_BTN_ON = {}
_BTN_OFF = {"border": "1.5px solid #ccc", "color": "#ccc", "cursor": "default", "pointerEvents": "none"}

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
        orientation='h', x=0.5, y=1.01, xanchor='center', yanchor='bottom',
        thickness=10, len=0.7, title_text='CHF pro Kopf', title_side='top',
    ))
    fig.update_layout(margin=dict(l=0, r=0, t=45, b=0), height=480, font=dict(size=12, color='#888'))
    return fig


_sq1_initial_figure = _build_sq1_map(YEARS[-1])

tab = dcc.Tab(
    label="1. Kosten pro Kopf", value="sq1", className="tab",
    style=TAB_STYLE, selected_style=TAB_SELECTED,
    children=[
        html.Div([
            html.Div([
                html.Div("Gesundheitskosten pro Kopf nach Kanton", style={
                    "fontSize": "18px", "fontWeight": "700", "color": "#2f4356", "lineHeight": "1.3",
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
                dcc.Loading(type='circle', color='#d8232a', children=html.Div(id='sq1-loading-anchor')),
                style={"height": "8px", "marginBottom": "8px", "display": "flex", "justifyContent": "center"},
            ),
            html.Div([
                dcc.Store(id='sq1-active-canton'),
                html.Div([
                    dcc.Graph(id='sq1-map', figure=_sq1_initial_figure,
                              config={"displayModeBar": False, "scrollZoom": True}, clear_on_unhover=True),
                ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px", "padding": "12px", "flex": "1"}),
                html.Div([
                    dcc.Graph(id='sq1-trend', config={"displayModeBar": False}, clear_on_unhover=True),
                ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px", "padding": "12px", "flex": "1"}),
            ], style={"display": "flex", "gap": "16px"}),
        ], style={"maxWidth": "1000px", "margin": "auto", "padding": "24px 32px"}),
    ],
)


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
    if map_click and map_click['points']:
        return map_click['points'][0]['location']
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
        x='year', y='cost_per_capita', color='canton',
        markers=True, custom_data=['canton'],
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
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(size=12, color='#888'),
        xaxis=dict(range=[YEARS[0] - 0.3, YEARS[-1] + 0.3]),
        legend=dict(orientation='h', x=0.01, y=0.99, xanchor='left', yanchor='top',
                    bgcolor='rgba(255,255,255,0.7)'),
    )
    return fig
