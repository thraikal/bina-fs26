import plotly.express as px
from dash import dcc, html, callback, Output, Input, State, no_update

from data import cantons, df_per_person, YEARS
from styles import BORDER, CARD_BG, TAB_STYLE, TAB_SELECTED, year_slider

_CANTON_OPTIONS = sorted(df_per_person['canton'].unique())

_BTN_ON = {}
_BTN_OFF = {"border": "1.5px solid #ccc", "color": "#ccc", "cursor": "default", "pointerEvents": "none"}


def _build_sq1_kpis(year: int, canton: str | None = None) -> list:
    dff = df_per_person[df_per_person['year'] == year]

    def _kpi(title, value, note='', note_color='#666'):
        return html.Div([
            html.Div(title, style={"fontSize": "11px", "color": "#888", "textTransform": "uppercase",
                                   "letterSpacing": "0.05em", "marginBottom": "4px"}),
            html.Div(value, style={"fontSize": "22px", "fontWeight": "700", "color": "#2f4356"}),
            html.Div(note, style={"fontSize": "11px", "color": note_color, "marginTop": "2px"}),
        ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                  "padding": "14px 18px", "flex": "1", "minWidth": "140px"})

    if canton:
        row = dff[dff['canton'] == canton].iloc[0]
        avg_cost = dff['cost_per_capita'].mean()
        cost_delta = (row['cost_per_capita'] - avg_cost) / avg_cost * 100
        rank = int((dff['cost_per_capita'] > row['cost_per_capita']).sum()) + 1
        first_year_cost = df_per_person.loc[
            (df_per_person['canton'] == canton) & (df_per_person['year'] == YEARS[0]), 'cost_per_capita'
        ].iloc[0]
        growth = (row['cost_per_capita'] - first_year_cost) / first_year_cost * 100
        return [
            _kpi("Kosten pro Kopf", f"CHF {row['cost_per_capita']:,.0f}".replace(',', "'"),
                 f"{'+'if cost_delta>=0 else ''}{cost_delta:.1f}% gegenüber dem Schweizer Durchschnitt",
                 note_color='#c0392b' if cost_delta > 0 else '#27ae60'),
            _kpi("Rang nach Kosten", f"{rank} von {len(dff)}", "von teuer nach günstig"),
            _kpi(f"Wachstum seit {YEARS[0]}",
                 f"{'+'if growth>=0 else ''}{growth:.1f}%",
                 f"CHF {first_year_cost:,.0f} → CHF {row['cost_per_capita']:,.0f}".replace(',', "'"),
                 note_color='#c0392b' if growth > 0 else '#27ae60'),
        ]

    avg_cost = dff['cost_per_capita'].mean()
    max_row = dff.loc[dff['cost_per_capita'].idxmax()]
    min_row = dff.loc[dff['cost_per_capita'].idxmin()]
    return [
        _kpi("Ø Kosten pro Kopf", f"CHF {avg_cost:,.0f}".replace(',', "'"), f"Schweizer Durchschnitt {year}"),
        _kpi("Höchste Kosten", max_row['canton'],
             f"CHF {max_row['cost_per_capita']:,.0f}".replace(',', "'")),
        _kpi("Tiefste Kosten", min_row['canton'],
             f"CHF {min_row['cost_per_capita']:,.0f}".replace(',', "'")),
    ]


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
    fig.update_geos(fitbounds='locations', visible=False, projection_type='mercator')
    fig.update_coloraxes(colorbar=dict(
        orientation='h', x=0.5, y=1.01, xanchor='center', yanchor='bottom',
        thickness=10, len=0.7, title_text='CHF pro Kopf', title_side='top',
    ))
    fig.update_layout(margin=dict(l=0, r=0, t=45, b=0), height=480, font=dict(size=12, color='#888'))
    return fig


_sq1_initial_figure = _build_sq1_map(YEARS[-1])
_initial_kpis = _build_sq1_kpis(YEARS[-1])

tab = dcc.Tab(
    label="1. Kostenverteilung", value="sq1", className="tab",
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
            html.Div(id='sq1-kpis', children=_initial_kpis,
                     style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),
            html.Div([
                html.Div([
                    html.Label("Jahr:", style={"fontWeight": "600", "whiteSpace": "nowrap", "fontSize": "13px", "color": "#555"}),
                    html.Div(year_slider("sq1-year-slider", YEARS), style={"flex": "1"}),
                    html.Button("‹", id='sq1-year-prev', n_clicks=0, className='year-step-btn'),
                    html.Button("›", id='sq1-year-next', n_clicks=0, className='year-step-btn'),
                ], style={"display": "flex", "alignItems": "center", "gap": "12px", "position": "relative", "zIndex": 2}),
                html.Div([
                    html.Label("Kanton:", style={"fontWeight": "600", "whiteSpace": "nowrap", "fontSize": "13px", "color": "#555"}),
                    dcc.Dropdown(
                        id='sq1-canton-dropdown',
                        options=[{"label": c, "value": c} for c in _CANTON_OPTIONS],
                        value=None,
                        clearable=True,
                        placeholder="Alle Kantone",
                        style={"flex": "1", "fontSize": "13px"},
                    ),
                ], style={"display": "flex", "alignItems": "center", "gap": "12px", "marginTop": "10px"}),
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
                    html.Div("Kosten pro Kopf nach Kanton", style={
                        "fontSize": "13px", "fontWeight": "600", "color": "#555", "marginBottom": "4px",
                    }),
                    html.Div("Kanton anklicken für Details",
                             style={"fontSize": "11px", "color": "#aaa", "marginBottom": "8px"}),
                    dcc.Graph(id='sq1-map', figure=_sq1_initial_figure,
                              config={"displayModeBar": False, "scrollZoom": True}, clear_on_unhover=True),
                ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px", "padding": "16px", "flex": "1"}),
                html.Div([
                    html.Div("Kostenverlauf nach Kanton", style={
                        "fontSize": "13px", "fontWeight": "600", "color": "#555", "marginBottom": "4px",
                    }),
                    html.Div("Kanton anklicken um Verlauf hervorzuheben · Punkt anklicken um Jahr zu wechseln",
                             style={"fontSize": "11px", "color": "#aaa", "marginBottom": "8px"}),
                    dcc.Graph(id='sq1-trend', config={"displayModeBar": False}, clear_on_unhover=True),
                ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px", "padding": "16px", "flex": "1"}),
            ], style={"display": "flex", "gap": "16px"}),
        ], style={"maxWidth": "1100px", "margin": "auto", "padding": "48px 32px"}),
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


@callback(
    Output('sq1-map', 'figure'),
    Output('sq1-kpis', 'children'),
    Output('sq1-loading-anchor', 'children'),
    Input('sq1-year-slider', 'value'),
    Input('sq1-canton-dropdown', 'value'),
)
def sq1_update(year, canton):
    return _build_sq1_map(year), _build_sq1_kpis(year, canton), None


@callback(
    Output('sq1-map', 'clickData'),
    Output('sq1-trend', 'clickData'),
    Input('sq1-canton-dropdown', 'value'),
    prevent_initial_call=True,
)
def sq1_reset_click_data(dropdown_value):
    if dropdown_value is None:
        return None, None
    return no_update, no_update


@callback(
    Output('sq1-canton-dropdown', 'value'),
    Input('sq1-map', 'clickData'),
    Input('sq1-trend', 'clickData'),
    State('sq1-canton-dropdown', 'value'),
    prevent_initial_call=True,
)
def sq1_click_to_dropdown(map_click, trend_click, current_value):
    from dash import ctx
    if ctx.triggered_id == 'sq1-map' and map_click and map_click['points']:
        clicked = map_click['points'][0]['location']
    elif ctx.triggered_id == 'sq1-trend' and trend_click and trend_click['points']:
        clicked = trend_click['points'][0]['customdata'][0]
    else:
        return no_update
    return None if clicked == current_value else clicked


@callback(
    Output('sq1-active-canton', 'data'),
    Input('sq1-map', 'hoverData'),
    Input('sq1-canton-dropdown', 'value'),
    Input('sq1-trend', 'hoverData'),
)
def sq1_active_canton(map_hover, dropdown_value, trend_hover):
    hovered = None
    if trend_hover and trend_hover['points']:
        hovered = trend_hover['points'][0]['customdata'][0]
    elif map_hover and map_hover['points']:
        hovered = map_hover['points'][0]['location']
    return {"selected": dropdown_value, "hovered": hovered}


@callback(
    Output('sq1-trend', 'figure'),
    Input('sq1-year-slider', 'value'),
    Input('sq1-active-canton', 'data'),
)
def sq1_trend(selected_year, active):
    selected = active.get('selected') if active else None
    hovered = active.get('hovered') if active else None
    # don't show hovered as a second highlight if it's the same as selected
    if hovered == selected:
        hovered = None

    fig = px.line(
        df_per_person.sort_values('year'),
        x='year', y='cost_per_capita', color='canton',
        markers=True, custom_data=['canton'],
        labels={'year': 'Jahr', 'cost_per_capita': 'CHF pro Kopf', 'canton': 'Kanton'},
    )
    any_highlighted = selected or hovered
    for trace in fig.data:
        if any_highlighted:
            if trace.name == selected:
                trace.line.width = 3
                trace.opacity = 1.0
                trace.showlegend = True
            elif trace.name == hovered:
                trace.line.width = 2
                trace.opacity = 0.75
                trace.showlegend = bool(selected)  # show label only when comparing
            else:
                trace.line.width = 1
                trace.opacity = 0.08
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
