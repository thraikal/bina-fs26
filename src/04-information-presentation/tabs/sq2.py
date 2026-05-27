import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, callback, Output, Input, State, no_update

from data import df_analysis_panel
from styles import BORDER, CARD_BG, TAB_STYLE, TAB_SELECTED, year_slider

_BTN_ON = {}
_BTN_OFF = {"border": "1.5px solid #ccc", "color": "#ccc", "cursor": "default", "pointerEvents": "none"}

SQ2_YEARS = sorted(df_analysis_panel['year'].unique().tolist())
_CANTON_OPTIONS = sorted(df_analysis_panel['canton_label'].unique().tolist())


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


def _build_kpis(year: int, canton: str | None = None) -> list:
    dff = _enrich(year)

    def _kpi(title, value, note='', note_color='#666'):
        return html.Div([
            html.Div(title, style={"fontSize": "11px", "color": "#888", "textTransform": "uppercase",
                                   "letterSpacing": "0.05em", "marginBottom": "4px"}),
            html.Div(value, style={"fontSize": "22px", "fontWeight": "700", "color": "#2f4356"}),
            html.Div(note, style={"fontSize": "11px", "color": note_color, "marginTop": "2px"}),
        ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                  "padding": "14px 18px", "flex": "1", "minWidth": "140px"})

    if canton:
        row = dff[dff['canton_label'] == canton].iloc[0]
        avg_cost = dff['cost_per_capita'].mean()
        avg_premium = dff['premium_median_monthly'].mean()
        cost_delta = (row['cost_per_capita'] - avg_cost) / avg_cost * 100
        premium_delta = (row['premium_median_monthly'] - avg_premium) / avg_premium * 100
        monthly_cost = row['cost_per_capita'] / 12
        coverage = row['premium_median_monthly'] / monthly_cost * 100
        avg_coverage = avg_premium / (avg_cost / 12) * 100
        coverage_delta = coverage - avg_coverage
        return [
            _kpi("Prämie deckt Kosten zu", f"{coverage:.0f}%",
                 f"{'+'if coverage_delta>=0 else ''}{coverage_delta:.1f}% gegenüber dem Schweizer Schnitt ({avg_coverage:.0f}%)"),
            _kpi("Kosten pro Kopf", f"CHF {row['cost_per_capita']/12:,.0f}".replace(',', "'") + " / Monat",
                 f"{'+'if cost_delta>=0 else ''}{cost_delta:.1f}% gegenüber dem Schweizer Durchschnitt",
                 note_color='#c0392b' if cost_delta > 0 else '#27ae60'),
            _kpi("Median-Basisprämie", f"CHF {row['premium_median_monthly']:,.0f}".replace(',', "'") + " / Monat",
                 f"{'+'if premium_delta>=0 else ''}{premium_delta:.1f}% gegenüber dem Schweizer Durchschnitt",
                 note_color='#c0392b' if premium_delta > 0 else '#27ae60'),
        ]

    r = dff['cost_per_capita'].corr(dff['premium_median_monthly'])
    if r >= 0.75:
        r_label = "Starke Übereinstimmung"
    elif r >= 0.5:
        r_label = "Moderate Übereinstimmung"
    else:
        r_label = "Schwache Übereinstimmung"
    outliers = int((dff['gap'].abs() > 1).sum())
    max_row = dff.loc[dff['gap'].abs().idxmax()]
    direction = 'über' if max_row['gap'] > 0 else 'unter'
    return [
        _kpi("Prämien spiegeln Kosten wider", r_label,
             f"Korrelation: r = {r:.2f} · alle Kantone {year}"),
        _kpi("Kantone mit Ungleichgewicht", f"{outliers} von {len(dff)}",
             "Prämien deutlich über oder unter Kostenprofil"),
        _kpi("Grösste Auffälligkeit", max_row['canton_label'],
             f"Prämien {direction} Kostenprofil"),
    ]


def _build_scatter(year: int, canton: str | None = None):
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
    if canton:
        traj = df_analysis_panel[df_analysis_panel['canton_label'] == canton].sort_values('year')
        if not traj.empty:
            icc = traj['canton_code'].iloc[0]
            fig.add_trace(go.Scatter(
                x=traj['cost_per_capita'],
                y=traj['premium_median_monthly'],
                mode='lines+markers',
                line=dict(color='#555', width=1.5, dash='dot'),
                marker=dict(size=5, color='#555', opacity=0.5),
                customdata=traj[['year']].values,
                name=f'{icc}: Verlauf {SQ2_YEARS[0]}–{SQ2_YEARS[-1]}',
                hovertemplate='%{customdata[0]}: CHF %{x:,.0f} / CHF %{y:,.0f}/Mt.<extra></extra>',
                showlegend=True,
            ))
    # diagonal reference line: expected premium ∝ cost (fitted OLS)
    x_vals = dff['cost_per_capita']
    y_vals = dff['premium_median_monthly']
    m, b = np.polyfit(x_vals, y_vals, 1)
    x_range = [x_vals.min(), x_vals.max()]
    y_range = [m * x + b for x in x_range]
    fig.add_trace(go.Scatter(
        x=x_range, y=y_range,
        mode='lines',
        line=dict(color='#aaa', width=1.5, dash='dot'),
        name='Erwartetes Prämienniveau',
        hoverinfo='skip',
        showlegend=True,
    ))
    fig.update_coloraxes(colorbar=dict(
        orientation='h', x=0.5, y=1.02, xanchor='center', yanchor='bottom',
        thickness=10, len=0.6,
        title_text='Prämien relativ zu Kosten (rot = zu hoch, blau = zu tief)',
        title_side='top',
    ))
    fig.update_layout(
        height=520,
        margin=dict(l=60, t=50, b=40, r=8),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(size=12, color='#888'),
        legend=dict(orientation='h', x=0.01, y=0.99, xanchor='left', yanchor='top',
                    bgcolor='rgba(255,255,255,0.7)', font_size=11),
    )
    return fig


def _build_gap_bar(year: int, canton: str | None = None):
    dff = _enrich(year).sort_values('gap')
    canton_order = dff['canton_label'].tolist()
    fig = go.Figure()

    def _color(alignment):
        return '#d8232a' if alignment == 'Prämien über Kostenprofil' else '#2f4356'

    if canton:
        other = dff[dff['canton_label'] != canton]
        sel = dff[dff['canton_label'] == canton]
        fig.add_trace(go.Bar(
            x=other['gap'], y=other['canton_label'],
            orientation='h',
            marker_color=[_color(a) for a in other['alignment']],
            marker_opacity=0.2,
            customdata=other[['canton_label', 'cost_per_capita', 'premium_median_monthly']].values,
            hovertemplate='<b>%{customdata[0]}</b><br>Gap: %{x:.2f}<extra></extra>',
            showlegend=False,
        ))
        if not sel.empty:
            row = sel.iloc[0]
            fig.add_trace(go.Bar(
                x=sel['gap'], y=sel['canton_label'],
                orientation='h',
                marker_color=_color(row['alignment']),
                customdata=sel[['canton_label', 'cost_per_capita', 'premium_median_monthly']].values,
                hovertemplate='<b>%{customdata[0]}</b><br>Gap: %{x:.2f}<br>Kosten: CHF %{customdata[1]:,.0f}<br>Prämie: CHF %{customdata[2]:,.0f}/Mt.<extra></extra>',
                showlegend=False,
            ))
    else:
        fig.add_trace(go.Bar(
            x=dff['gap'], y=dff['canton_label'],
            orientation='h',
            marker_color=[_color(a) for a in dff['alignment']],
            customdata=dff[['canton_label', 'cost_per_capita', 'premium_median_monthly']].values,
            hovertemplate='<b>%{customdata[0]}</b><br>Gap: %{x:.2f}<br>Kosten: CHF %{customdata[1]:,.0f}<br>Prämie: CHF %{customdata[2]:,.0f}/Mt.<extra></extra>',
            showlegend=False,
        ))

    fig.add_vline(x=0, line_color='#aaa', line_width=1)
    fig.update_layout(
        height=620,
        margin=dict(l=0, r=8, t=36, b=40),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(size=11, color='#888'),
        yaxis=dict(categoryorder='array', categoryarray=canton_order, automargin=True),
        xaxis_title='← Prämien zu tief   |   Prämien zu hoch →',
        barmode='overlay',
    )
    return fig


_initial_scatter = _build_scatter(SQ2_YEARS[-1])
_initial_gap_bar = _build_gap_bar(SQ2_YEARS[-1])
_initial_kpis = _build_kpis(SQ2_YEARS[-1])
tab = dcc.Tab(
    label="2. Prämienbelastung", value="sq2", className="tab",
    style=TAB_STYLE, selected_style=TAB_SELECTED,
    children=[
        html.Div([
            html.Div([
                html.Div("Prämienniveau und Gesundheitskostenbelastung", style={
                    "fontSize": "18px", "fontWeight": "700", "color": "#2f4356",
                }),
                html.Div(
                    "Wo passen Prämien und Kosten zusammen und wo gibt es Auffälligkeiten?",
                    style={"fontSize": "12px", "color": "#888", "marginTop": "4px"},
                ),
            ], style={"marginBottom": "20px"}),

            html.Div(id='sq2-kpis', children=_initial_kpis,
                     style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),

            html.Div([
                html.Div([
                    html.Label("Jahr:", style={"fontWeight": "600", "whiteSpace": "nowrap", "fontSize": "13px", "color": "#555"}),
                    html.Div(year_slider("sq2-year-slider", SQ2_YEARS), style={"flex": "1"}),
                    html.Button("‹", id='sq2-year-prev', n_clicks=0, className='year-step-btn'),
                    html.Button("›", id='sq2-year-next', n_clicks=0, className='year-step-btn'),
                ], style={"display": "flex", "alignItems": "center", "gap": "12px", "position": "relative", "zIndex": 2}),
                html.Div([
                    html.Label("Kanton:", style={"fontWeight": "600", "whiteSpace": "nowrap", "fontSize": "13px", "color": "#555"}),
                    dcc.Dropdown(
                        id='sq2-canton-dropdown',
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
                dcc.Loading(type='circle', color='#d8232a', children=html.Div(id='sq2-loading-anchor')),
                style={"height": "8px", "marginBottom": "8px", "display": "flex", "justifyContent": "center"},
            ),

            html.Div([
                html.Div([
                    html.Div("Prämien vs. Kosten pro Kopf", style={
                        "fontSize": "13px", "fontWeight": "600", "color": "#555", "marginBottom": "4px",
                    }),
                    html.Div(
                        "Kantone weit von der gestrichelten Linie haben ein Ungleichgewicht · Rot = Prämien zu hoch · Blau = Prämien zu tief",
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

        ], style={"maxWidth": "1100px", "margin": "auto", "padding": "48px 32px"}),
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
    Output('sq2-scatter', 'clickData'),
    Output('sq2-gap-bar', 'clickData'),
    Input('sq2-canton-dropdown', 'value'),
    prevent_initial_call=True,
)
def sq2_reset_click_data(dropdown_value):
    if dropdown_value is None:
        return None, None
    return no_update, no_update


@callback(
    Output('sq2-canton-dropdown', 'value'),
    Input('sq2-scatter', 'clickData'),
    Input('sq2-gap-bar', 'clickData'),
    State('sq2-canton-dropdown', 'value'),
    prevent_initial_call=True,
)
def sq2_click_to_dropdown(scatter_click, bar_click, current_value):
    from dash import ctx
    clicked = None
    if ctx.triggered_id == 'sq2-scatter' and scatter_click:
        clicked = scatter_click['points'][0]['customdata'][0]
    elif ctx.triggered_id == 'sq2-gap-bar' and bar_click:
        clicked = bar_click['points'][0]['y']
    if clicked is None:
        return no_update
    return None if clicked == current_value else clicked


@callback(
    Output('sq2-scatter', 'figure'),
    Output('sq2-gap-bar', 'figure'),
    Output('sq2-kpis', 'children'),
    Output('sq2-loading-anchor', 'children'),
    Input('sq2-year-slider', 'value'),
    Input('sq2-canton-dropdown', 'value'),
)
def sq2_update(year, canton):
    return _build_scatter(year, canton), _build_gap_bar(year, canton), _build_kpis(year, canton), None
