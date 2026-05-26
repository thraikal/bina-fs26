import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, callback, Output, Input, State, no_update

from data import cantons, df_aging, df_aging_ch, SQ3_YEARS

_SQ3_CANTON_OPTIONS = sorted(df_aging['canton'].unique())
from styles import BORDER, CARD_BG, TAB_STYLE, TAB_SELECTED, year_slider

_QUADRANT_COLORS = {
    'Doppelbelastung': '#c0392b',
    'Kostenausreisser': '#e67e22',
    'Effizient trotz Alter': '#27ae60',
    'Tiefe Belastung': '#2980b9',
}

_BTN_ON = {}
_BTN_OFF = {"border": "1.5px solid #ccc", "color": "#ccc", "cursor": "default", "pointerEvents": "none"}


def _sq3_quadrant(dff):
    avg_x, avg_y = dff['share_pct'].mean(), dff['cost_per_capita'].mean()
    hi_x, hi_y = dff['share_pct'] >= avg_x, dff['cost_per_capita'] >= avg_y
    labels = list(_QUADRANT_COLORS)
    return np.select([hi_x & hi_y, ~hi_x & hi_y, hi_x & ~hi_y], labels[:3], default=labels[3])


def _build_sq3_scatter(year: int, selected_canton: str | None = None) -> go.Figure:
    dff = df_aging[df_aging['year'] == year].copy()
    dff['quadrant'] = _sq3_quadrant(dff)

    x, y = dff['share_pct'].values, dff['cost_per_capita'].values
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    r2 = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - y.mean()) ** 2)
    avg_x, avg_y = x.mean(), y.mean()

    fig = go.Figure()

    if selected_canton:
        traj = df_aging[df_aging['canton'] == selected_canton].sort_values('year')
        if not traj.empty:
            icc = traj['icc'].iloc[0]
            fig.add_trace(go.Scatter(
                x=traj['share_pct'], y=traj['cost_per_capita'],
                mode='lines+markers',
                line=dict(color='#555', width=1.5, dash='dot'),
                marker=dict(size=5, color='#555', opacity=0.5),
                customdata=traj['year'].values,
                name=f'{icc}: Verlauf {SQ3_YEARS[0]}-{SQ3_YEARS[-1]}',
                hovertemplate='%{customdata}: %{x:.1f}% · CHF %{y:,.0f}<extra></extra>',
            ))

    fig.add_trace(go.Scatter(
        x=[x.min(), x.max()], y=[slope * x.min() + intercept, slope * x.max() + intercept],
        mode='lines', line=dict(color='#999', width=1.5, dash='dash'),
        name=f'Regression (R² = {r2:.2f})', hoverinfo='skip',
    ))
    fig.add_vline(x=avg_x, line_dash='dot', line_color='#ccc', line_width=1)
    fig.add_hline(y=avg_y, line_dash='dot', line_color='#ccc', line_width=1)

    for quad, color in _QUADRANT_COLORS.items():
        sub = dff[dff['quadrant'] == quad]
        fig.add_trace(go.Scatter(
            x=sub['share_pct'], y=sub['cost_per_capita'],
            mode='markers+text', text=sub['icc'],
            textposition='top center', textfont=dict(size=10, color=color),
            marker=dict(size=10, color=color, opacity=0.85),
            name=quad,
            customdata=sub[['canton', 'share_pct', 'cost_per_capita']].values,
            hovertemplate='<b>%{customdata[0]}</b><br>66+: %{customdata[1]:.1f}%<br>Kosten: CHF %{customdata[2]:,.0f}<extra></extra>',
        ))

    fig.update_layout(
        height=480, margin=dict(l=60, t=30, b=60, r=20),
        paper_bgcolor='white', plot_bgcolor='white', font=dict(size=12, color='#888'),
        xaxis=dict(title='Anteil Bevölkerung 66+ (%)', gridcolor='#f0f0f0', zeroline=False),
        yaxis=dict(title='Gesundheitskosten pro Kopf (CHF)', gridcolor='#f0f0f0', zeroline=False),
        legend=dict(orientation='h', x=0, y=-0.18, xanchor='left', bgcolor='rgba(0,0,0,0)'),
        annotations=[dict(
            x=0.99, y=0.99, xref='paper', yref='paper', text=f'R² = {r2:.2f}',
            showarrow=False, xanchor='right', yanchor='top',
            bgcolor='rgba(255,255,255,0.85)', bordercolor='#ddd', borderwidth=1,
            font=dict(size=13, color='#333'),
        )],
    )
    return fig


def _build_sq3_map(year: int) -> go.Figure:
    dff = df_aging[df_aging['year'] == year]
    fig = px.choropleth(
        dff, geojson=cantons, locations='canton', featureidkey='properties.name',
        color='share_pct', hover_name='canton',
        hover_data={'share_pct': ':.1f', 'cost_per_capita': ':,.0f', 'canton': False},
        color_continuous_scale='Oranges',
        labels={'share_pct': '% 66+', 'cost_per_capita': 'CHF/Kopf'},
    )
    fig.update_geos(fitbounds='locations', visible=False, projection_type='mercator')
    fig.update_coloraxes(colorbar=dict(
        orientation='h', x=0.5, y=1.01, xanchor='center', yanchor='bottom',
        thickness=10, len=0.7, title_text='Anteil 66+ (%)', title_side='top',
    ))
    fig.update_layout(margin=dict(l=0, r=0, t=45, b=0), height=480, font=dict(size=12, color='#888'))
    return fig


def _build_sq3_kpis(year: int, canton: str | None = None) -> list:
    dff = df_aging[df_aging['year'] == year]

    def _kpi(title, value, note='', note_color='#aaa'):
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
        avg_share = dff['share_pct'].mean()
        cost_delta = (row['cost_per_capita'] - avg_cost) / avg_cost * 100
        share_delta = row['share_pct'] - avg_share
        rank = int((dff['cost_per_capita'] > row['cost_per_capita']).sum()) + 1
        return [
            _kpi("Anteil 66+", f"{row['share_pct']:.1f}%",
                 f"{'+'if share_delta>=0 else ''}{share_delta:.1f}% vs. CH-Schnitt",
                 note_color='#e67e22' if share_delta > 0 else '#2980b9'),
            _kpi("Kosten pro Kopf", f"CHF {row['cost_per_capita']:,.0f}",
                 f"{'+'if cost_delta>=0 else ''}{cost_delta:.1f}% vs. CH-Schnitt",
                 note_color='#c0392b' if cost_delta > 0 else '#27ae60'),
            _kpi("Rang nach Kosten", f"{rank} von {len(dff)}", "von teuer nach günstig"),
        ]

    avg_share = dff['share_pct'].mean()
    top_cost = dff.loc[dff['cost_per_capita'].idxmax()]
    top_age = dff.loc[dff['share_pct'].idxmax()]
    return [
        _kpi("Ø Anteil 66+", f"{avg_share:.1f}%", "alle Kantone"),
        _kpi("Höchste Kosten", top_cost['icc'],
             f"CHF {top_cost['cost_per_capita']:,.0f} · {top_cost['canton']}"),
        _kpi("Höchster 66+-Anteil", top_age['icc'],
             f"{top_age['share_pct']:.1f}% · {top_age['canton']}"),
    ]


def _build_sq3_detail(canton: str | None = None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_aging_ch['year'], y=df_aging_ch['cost_per_capita'],
        mode='lines+markers', name='CH: Kosten pro Kopf',
        line=dict(color='#2f4356', width=1.5, dash='dash'), marker=dict(size=5),
        yaxis='y1', hovertemplate='%{x}: CHF %{y:,.0f}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=df_aging_ch['year'], y=df_aging_ch['share_pct'],
        mode='lines+markers', name='CH: Anteil 66+',
        line=dict(color='#e67e22', width=1.5, dash='dash'), marker=dict(size=5),
        yaxis='y2', hovertemplate='%{x}: %{y:.1f}%<extra></extra>',
    ))
    if canton:
        dff = df_aging[df_aging['canton'] == canton].sort_values('year')
        icc = dff['icc'].iloc[0]
        fig.add_trace(go.Scatter(
            x=dff['year'], y=dff['cost_per_capita'],
            mode='lines+markers', name=f'{icc}: Kosten pro Kopf',
            line=dict(color='#2f4356', width=2.5), marker=dict(size=7),
            yaxis='y1', hovertemplate='%{x}: CHF %{y:,.0f}<extra></extra>',
        ))
        fig.add_trace(go.Scatter(
            x=dff['year'], y=dff['share_pct'],
            mode='lines+markers', name=f'{icc}: Anteil 66+',
            line=dict(color='#e67e22', width=2.5), marker=dict(size=7),
            yaxis='y2', hovertemplate='%{x}: %{y:.1f}%<extra></extra>',
        ))
    fig.update_layout(
        height=260, margin=dict(l=60, t=12, b=40, r=60),
        paper_bgcolor='white', plot_bgcolor='white', font=dict(size=12, color='#888'),
        xaxis=dict(gridcolor='#f0f0f0', zeroline=False, dtick=1),
        yaxis=dict(title=dict(text='CHF pro Kopf', font=dict(color='#2f4356')),
                   tickfont=dict(color='#2f4356'), gridcolor='#f0f0f0', zeroline=False),
        yaxis2=dict(title=dict(text='Anteil 66+ (%)', font=dict(color='#e67e22')),
                    tickfont=dict(color='#e67e22'), overlaying='y', side='right',
                    zeroline=False, showgrid=False),
        legend=dict(orientation='h', x=0, y=-0.2, xanchor='left', bgcolor='rgba(0,0,0,0)'),
    )
    return fig


_initial_scatter = _build_sq3_scatter(SQ3_YEARS[-1])
_initial_map = _build_sq3_map(SQ3_YEARS[-1])
_initial_kpis = _build_sq3_kpis(SQ3_YEARS[-1])

tab = dcc.Tab(
    label="3. Alterung & Kosten", value="sq3", className="tab",
    style=TAB_STYLE, selected_style=TAB_SELECTED,
    children=[
        html.Div([
            html.Div([
                html.Div("Alterung & Gesundheitskosten", style={
                    "fontSize": "18px", "fontWeight": "700", "color": "#2f4356", "lineHeight": "1.3",
                }),
                html.Div("Korrelation zwischen Anteil 66+ und Kosten pro Kopf nach Kanton", style={
                    "fontSize": "12px", "color": "#888", "marginTop": "4px",
                }),
            ], style={"marginBottom": "20px"}),
            html.Div(id='sq3-kpis', children=_initial_kpis,
                     style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),
            html.Div([
                html.Div([
                    html.Label("Jahr:", style={"fontWeight": "600", "whiteSpace": "nowrap", "fontSize": "13px", "color": "#555"}),
                    html.Div(year_slider("sq3-year-slider", SQ3_YEARS), style={"flex": "1"}),
                    html.Button("‹", id='sq3-year-prev', n_clicks=0, className='year-step-btn'),
                    html.Button("›", id='sq3-year-next', n_clicks=0, className='year-step-btn'),
                ], style={"display": "flex", "alignItems": "center", "gap": "12px", "position": "relative", "zIndex": 2}),
                html.Div([
                    html.Label("Kanton:", style={"fontWeight": "600", "whiteSpace": "nowrap", "fontSize": "13px", "color": "#555"}),
                    dcc.Dropdown(
                        id='sq3-canton-dropdown',
                        options=[{"label": c, "value": c} for c in _SQ3_CANTON_OPTIONS],
                        value=None,
                        clearable=True,
                        placeholder="Alle Kantone",
                        style={"flex": "1", "fontSize": "13px"},
                    ),
                ], style={"display": "flex", "alignItems": "center", "gap": "12px", "marginTop": "10px"}),
            ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                      "padding": "16px 20px", "marginBottom": "8px"}),
            html.Div(
                dcc.Loading(type='circle', color='#d8232a', children=html.Div(id='sq3-loading-anchor')),
                style={"height": "8px", "marginBottom": "8px", "display": "flex", "justifyContent": "center"},
            ),
            html.Div([
                html.Div([
                    html.H3("Korrelation: Bevölkerungsalterung & Kosten pro Kopf",
                            style={"margin": "0 0 2px", "fontSize": "13px", "color": "#555"}),
                    html.P("Gestrichelte Linie = Regressionsgerade · Kreuzlinien = Schweizer Durchschnitt",
                           style={"fontSize": "11px", "color": "#bbb", "margin": "0 0 8px"}),
                    dcc.Graph(id='sq3-scatter', figure=_initial_scatter, config={"displayModeBar": False}),
                ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px", "padding": "12px", "flex": "2"}),
                html.Div([
                    html.H3("Anteil 66+ nach Kanton", style={"margin": "0 0 8px", "fontSize": "13px", "color": "#555"}),
                    dcc.Graph(id='sq3-map', figure=_initial_map, config={"displayModeBar": False}),
                ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px", "padding": "12px", "flex": "1"}),
            ], style={"display": "flex", "gap": "16px"}),
            html.Div(id='sq3-detail', style={"marginTop": "16px"}),
        ], style={"maxWidth": "1100px", "margin": "auto", "padding": "24px 32px"}),
    ],
)


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
    Output('sq3-loading-anchor', 'children'),
    Input('sq3-year-slider', 'value'),
    Input('sq3-canton-dropdown', 'value'),
)
def sq3_charts(year, selected_canton):
    return _build_sq3_scatter(year, selected_canton), _build_sq3_map(year), _build_sq3_kpis(year, selected_canton), None



@callback(
    Output('sq3-map', 'clickData'),
    Output('sq3-scatter', 'clickData'),
    Input('sq3-canton-dropdown', 'value'),
    prevent_initial_call=True,
)
def sq3_reset_click_data(dropdown_value):
    if dropdown_value is None:
        return None, None
    return no_update, no_update


@callback(
    Output('sq3-canton-dropdown', 'value'),
    Input('sq3-scatter', 'clickData'),
    Input('sq3-map', 'clickData'),
    State('sq3-canton-dropdown', 'value'),
    prevent_initial_call=True,
)
def sq3_click_to_dropdown(scatter_click, map_click, current_value):
    from dash import ctx
    clicked = None
    if ctx.triggered_id == 'sq3-scatter' and scatter_click:
        clicked = scatter_click['points'][0]['customdata'][0]
    elif ctx.triggered_id == 'sq3-map' and map_click:
        clicked = map_click['points'][0]['location']
    if clicked is None:
        return no_update
    return None if clicked == current_value else clicked


@callback(Output('sq3-detail', 'children'), Input('sq3-canton-dropdown', 'value'))
def sq3_detail_chart(canton):
    if canton:
        icc = df_aging.loc[df_aging['canton'] == canton, 'icc'].iloc[0]
        title = f"Entwicklung {canton} ({icc}) vs. Schweiz"
    else:
        title = "Entwicklung Schweiz (Gesamtschweiz)"
    return [
        html.Div([
            html.H3(title, style={"margin": "0 0 8px", "fontSize": "13px", "color": "#555"}),
            dcc.Graph(figure=_build_sq3_detail(canton), config={"displayModeBar": False}),
        ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px", "padding": "12px"}),
    ]
