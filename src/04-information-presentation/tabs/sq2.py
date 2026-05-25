import numpy as np
import plotly.express as px
from dash import dcc, html, callback, Output, Input, no_update

from data import df_analysis_panel
from styles import BORDER, CARD_BG, TAB_STYLE, TAB_SELECTED, year_slider

_BTN_ON = {}
_BTN_OFF = {"border": "1.5px solid #ccc", "color": "#ccc", "cursor": "default", "pointerEvents": "none"}

SQ2_YEARS = sorted(df_analysis_panel['year'].unique().tolist())


def _enrich(year: int):
    dff = df_analysis_panel[df_analysis_panel['year'] == year].copy()
    def _z(s):
        return (s - s.mean()) / s.std(ddof=0)
    dff['z_cost'] = _z(dff['cost_per_capita'])
    dff['z_premium'] = _z(dff['premium_median_monthly'])
    dff['gap'] = dff['z_premium'] - dff['z_cost']
    dff['alignment'] = np.where(dff['gap'] > 0, 'Prämien über Kostenprofil', 'Prämien unter Kostenprofil')
    dff['size_val'] = (dff['belastungsindex'] - dff['belastungsindex'].min() + 0.3).clip(lower=0.1)
    return dff


def _build_scatter(year: int):
    dff = _enrich(year)
    fig = px.scatter(
        dff,
        x='cost_per_capita',
        y='premium_median_monthly',
        color='gap',
        size='size_val',
        hover_name='canton_label',
        text='canton_code',
        color_continuous_scale='RdBu_r',
        color_continuous_midpoint=0,
        labels={
            'cost_per_capita': 'Gesundheitskosten pro Kopf (CHF)',
            'premium_median_monthly': 'Median-Basisprämie / Monat (CHF)',
            'gap': 'Prämien-Kosten-Gap',
            'size_val': '',
        },
        custom_data=['canton_label', 'gap', 'belastungsindex'],
    )
    fig.update_traces(
        textposition='top center',
        textfont_size=10,
        hovertemplate=(
            '<b>%{hovertext}</b><br>'
            'Kosten pro Kopf: CHF %{x:,.0f}<br>'
            'Median-Prämie: CHF %{y:,.0f}/Mt.<br>'
            'Gap (z): %{customdata[1]:.2f}<br>'
            'Belastungsindex: %{customdata[2]:.2f}<extra></extra>'
        ),
    )
    fig.update_coloraxes(colorbar=dict(
        orientation='h', x=0.5, y=1.02, xanchor='center', yanchor='bottom',
        thickness=10, len=0.6, title_text='Prämien-Kosten-Gap', title_side='top',
    ))
    fig.update_layout(
        height=520,
        margin=dict(l=60, t=50, b=40, r=8),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(size=12, color='#888'),
    )
    return fig


def _build_gap_bar(year: int):
    dff = _enrich(year).sort_values('gap')
    canton_order = dff['canton_label'].tolist()
    fig = px.bar(
        dff,
        x='gap',
        y='canton_label',
        orientation='h',
        color='alignment',
        color_discrete_map={
            'Prämien über Kostenprofil': '#d8232a',
            'Prämien unter Kostenprofil': '#2f4356',
        },
        category_orders={'canton_label': canton_order},
        labels={
            'gap': 'Prämienniveau − Kostenbelastung (z-Score)',
            'canton_label': 'Kanton',
            'alignment': '',
        },
        custom_data=['canton_label', 'cost_per_capita', 'premium_median_monthly'],
    )
    fig.update_traces(
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            'Gap: %{x:.2f}<br>'
            'Kosten pro Kopf: CHF %{customdata[1]:,.0f}<br>'
            'Median-Prämie: CHF %{customdata[2]:,.0f}/Mt.<extra></extra>'
        ),
    )
    fig.add_vline(x=0, line_color='#aaa', line_width=1)
    fig.update_layout(
        height=620,
        margin=dict(l=0, r=8, t=36, b=40),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(size=11, color='#888'),
        legend=dict(orientation='h', x=0, y=1.02, xanchor='left', yanchor='bottom', font_size=11),
        yaxis=dict(automargin=True),
    )
    return fig


_initial_scatter = _build_scatter(SQ2_YEARS[-1])
_initial_gap_bar = _build_gap_bar(SQ2_YEARS[-1])

tab = dcc.Tab(
    label="2. Prämien & Kosten", value="sq2", className="tab",
    style=TAB_STYLE, selected_style=TAB_SELECTED,
    children=[
        html.Div([
            html.Div([
                html.Div("Prämienniveau und Gesundheitskostenbelastung", style={
                    "fontSize": "18px", "fontWeight": "700", "color": "#2f4356",
                }),
                html.Div(
                    "Wo passen Prämien und Kosten zusammen – und wo gibt es Auffälligkeiten?",
                    style={"fontSize": "12px", "color": "#888", "marginTop": "4px"},
                ),
            ], style={"marginBottom": "20px"}),

            html.Div([
                html.Div([
                    html.Label("Jahr:", style={"fontWeight": "600", "whiteSpace": "nowrap", "fontSize": "13px", "color": "#555"}),
                    html.Div(year_slider("sq2-year-slider", SQ2_YEARS), style={"flex": "1"}),
                    html.Button("‹", id='sq2-year-prev', n_clicks=0, className='year-step-btn'),
                    html.Button("›", id='sq2-year-next', n_clicks=0, className='year-step-btn'),
                ], style={"display": "flex", "alignItems": "center", "gap": "12px"}),
            ], style={
                "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                "padding": "16px 20px", "marginBottom": "8px",
            }),

            html.Div(
                dcc.Loading(type='circle', color='#d8232a', children=html.Div(id='sq2-loading-anchor')),
                style={"height": "8px", "marginBottom": "8px", "display": "flex", "justifyContent": "center"},
            ),

            html.Div([
                html.Div([
                    html.Div("Prämien vs. Kosten pro Kopf", style={
                        "fontSize": "13px", "fontWeight": "600", "color": "#555", "marginBottom": "4px",
                    }),
                    html.Div(
                        "Grösse = Belastungsindex · Farbe = Prämien-Kosten-Gap",
                        style={"fontSize": "11px", "color": "#aaa", "marginBottom": "8px"},
                    ),
                    dcc.Graph(id='sq2-scatter', figure=_initial_scatter, config={"displayModeBar": False}),
                ], style={
                    "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                    "padding": "16px", "flex": "1",
                }),

                html.Div([
                    html.Div("Auffälligkeiten nach Kanton", style={
                        "fontSize": "13px", "fontWeight": "600", "color": "#555", "marginBottom": "4px",
                    }),
                    html.Div(
                        "Positiver Gap = Prämie über Kostenprofil · Negativer Gap = Prämie darunter",
                        style={"fontSize": "11px", "color": "#aaa", "marginBottom": "8px"},
                    ),
                    dcc.Graph(id='sq2-gap-bar', figure=_initial_gap_bar, config={"displayModeBar": False}),
                ], style={
                    "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                    "padding": "16px", "flex": "1",
                }),
            ], style={"display": "flex", "gap": "16px"}),

        ], style={"maxWidth": "1100px", "margin": "auto", "padding": "24px 32px"}),
    ],
)


@callback(
    Output('sq2-year-slider', 'value'),
    Output('sq2-year-prev', 'style'),
    Output('sq2-year-next', 'style'),
    Input('sq2-year-prev', 'n_clicks'),
    Input('sq2-year-next', 'n_clicks'),
    Input('sq2-year-slider', 'value'),
)
def sq2_step_year(_prev, _next, current_year):
    from dash import ctx
    new_year = current_year
    if ctx.triggered_id == 'sq2-year-prev':
        new_year = max(SQ2_YEARS[0], current_year - 1)
    elif ctx.triggered_id == 'sq2-year-next':
        new_year = min(SQ2_YEARS[-1], current_year + 1)
    slider_out = new_year if new_year != current_year else no_update
    return slider_out, _BTN_OFF if new_year == SQ2_YEARS[0] else _BTN_ON, _BTN_OFF if new_year == SQ2_YEARS[-1] else _BTN_ON


@callback(
    Output('sq2-scatter', 'figure'),
    Output('sq2-gap-bar', 'figure'),
    Output('sq2-loading-anchor', 'children'),
    Input('sq2-year-slider', 'value'),
)
def sq2_update(year):
    return _build_scatter(year), _build_gap_bar(year), None
