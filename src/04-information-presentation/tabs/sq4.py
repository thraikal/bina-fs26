import numpy as np
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from dash import dcc, html, callback, Output, Input, State, no_update

from data import df_analysis_panel, df_manager_priorities
from styles import BORDER, CARD_BG, TAB_STYLE, TAB_SELECTED

_CLUSTER_FEATURES = ['cost_per_capita', 'population_share_66_plus', 'premium_median_monthly']
_CHOSEN_K = 6
_RANK_TO_NAME = {
    1: 'Niedriger Druck',
    2: 'Mittlerer Druck',
    3: 'Erhöhter Druck',
    4: 'Hoher Druck',
    5: 'Sehr hoher Druck',
    6: 'Extremer Druck',
}
_CLUSTER_COLORS = {
    'Niedriger Druck':    '#4a90d9',
    'Mittlerer Druck':    '#7cb8e8',
    'Erhöhter Druck':     '#f5a623',
    'Hoher Druck':        '#e07b39',
    'Sehr hoher Druck':   '#c0392b',
    'Extremer Druck':     '#7b0d0d',
}
_HIGH_RISK = {'Sehr hoher Druck', 'Extremer Druck'}


def _build_clusters():
    latest_year = int(df_analysis_panel['year'].max())
    dff = df_analysis_panel[df_analysis_panel['year'] == latest_year][
        ['canton_code', 'canton_label', 'belastungsindex', *_CLUSTER_FEATURES]
    ].dropna().copy()

    X = dff[_CLUSTER_FEATURES].to_numpy(dtype=float)
    X_scaled = StandardScaler().fit_transform(X)

    model = KMeans(n_clusters=_CHOSEN_K, random_state=42, n_init=20)
    dff['cluster_id'] = model.fit_predict(X_scaled)

    profile = dff.groupby('cluster_id')['belastungsindex'].mean()
    rank_map = profile.rank(ascending=True, method='dense').astype(int).to_dict()
    dff['cluster_name'] = dff['cluster_id'].map(lambda cid: _RANK_TO_NAME[rank_map[cid]])
    return dff, latest_year


_cluster_df, _latest_year = _build_clusters()

# --- KPI computations (module-level, static) ---
_n_priority = int((df_manager_priorities['priority_flag'] == 'Prioritär beobachten').sum())
_n_total = len(df_manager_priorities)
_n_high_risk = int(_cluster_df['cluster_name'].isin(_HIGH_RISK).sum())

_pos_delta = df_manager_priorities[df_manager_priorities['delta_belastungsindex_to_2030'] > 0]
if not _pos_delta.empty:
    _max_delta_idx = _pos_delta['delta_belastungsindex_to_2030'].idxmax()
    _max_delta_canton = df_manager_priorities.loc[_max_delta_idx, 'canton_label']
    _max_delta_val = df_manager_priorities.loc[_max_delta_idx, 'delta_belastungsindex_to_2030']
else:
    _max_delta_canton = '–'
    _max_delta_val = 0.0

_CANTON_OPTIONS = sorted(_cluster_df['canton_label'].unique().tolist())


def _kpi(title, value, note='', note_color='#666'):
    return html.Div([
        html.Div(title, style={"fontSize": "11px", "color": "#888", "textTransform": "uppercase",
                               "letterSpacing": "0.05em", "marginBottom": "4px"}),
        html.Div(value, style={"fontSize": "22px", "fontWeight": "700", "color": "#2f4356"}),
        html.Div(note, style={"fontSize": "11px", "color": note_color, "marginTop": "2px"}),
    ], style={"background": CARD_BG, "border": BORDER, "borderRadius": "8px",
              "padding": "14px 18px", "flex": "1", "minWidth": "140px"})


_INITIAL_KPIS = [
    _kpi(
        "Prioritär beobachten",
        f"{_n_priority} von {_n_total}",
        "Kantone mit erwartetem Handlungsbedarf bis 2030",
        note_color='#c0392b',
    ),
    _kpi(
        "In Risikosegment",
        f"{_n_high_risk} Kantone",
        "Segment «Sehr hoher Druck» oder «Extremer Druck»",
        note_color='#c0392b',
    ),
    _kpi(
        "Grösster Anstieg bis 2030",
        _max_delta_canton,
        f"+{_max_delta_val:.2f} Punkte Belastungsindex bis 2030",
        note_color='#c0392b',
    ),
]


def _build_cluster_scatter(canton: str | None = None):
    dff = _cluster_df.copy()
    dff['share_pct'] = dff['population_share_66_plus'] * 100

    fig = go.Figure()

    # Draw one trace per cluster; if a canton is selected, exclude it from the
    # cluster trace and re-add it separately on top for the highlight effect.
    for cname in list(_RANK_TO_NAME.values()):
        sub = dff[dff['cluster_name'] == cname]
        if sub.empty:
            continue
        sub_plot = sub[sub['canton_label'] != canton] if canton else sub
        if not sub_plot.empty:
            fig.add_trace(go.Scatter(
                x=sub_plot['share_pct'],
                y=sub_plot['cost_per_capita'],
                mode='markers+text',
                text=sub_plot['canton_code'],
                textposition='top center',
                textfont=dict(size=10, color=_CLUSTER_COLORS[cname]),
                marker=dict(
                    size=list(sub_plot['premium_median_monthly'] / 40),
                    color=_CLUSTER_COLORS[cname],
                    opacity=0.18 if canton else 0.85,
                ),
                name=cname,
                legendgroup=cname,
                showlegend=True,
                customdata=sub_plot[
                    ['canton_label', 'cluster_name', 'belastungsindex', 'premium_median_monthly']
                ].values,
                hovertemplate=(
                    '<b>%{customdata[0]}</b><br>'
                    'Segment: %{customdata[1]}<br>'
                    'Belastungsindex: %{customdata[2]:.2f}<br>'
                    'Kosten pro Kopf: CHF %{y:,.0f}<br>'
                    'Anteil 66+: %{x:.1f}%<br>'
                    'Median-Prämie: CHF %{customdata[3]:,.0f}/Mt.<extra></extra>'
                ),
            ))

    # Highlighted canton on top
    if canton:
        sel = dff[dff['canton_label'] == canton]
        if not sel.empty:
            row = sel.iloc[0]
            cname = row['cluster_name']
            fig.add_trace(go.Scatter(
                x=[row['share_pct']],
                y=[row['cost_per_capita']],
                mode='markers+text',
                text=[row['canton_code']],
                textposition='top center',
                textfont=dict(size=12, color=_CLUSTER_COLORS[cname]),
                marker=dict(
                    size=[row['premium_median_monthly'] / 34],
                    color=_CLUSTER_COLORS[cname],
                    opacity=1.0,
                ),
                name=canton,
                legendgroup=cname,
                showlegend=False,
                customdata=[[
                    row['canton_label'], row['cluster_name'],
                    row['belastungsindex'], row['premium_median_monthly'],
                ]],
                hovertemplate=(
                    '<b>%{customdata[0]}</b><br>'
                    'Segment: %{customdata[1]}<br>'
                    'Belastungsindex: %{customdata[2]:.2f}<br>'
                    'Kosten pro Kopf: CHF %{y:,.0f}<br>'
                    'Anteil 66+: %{x:.1f}%<br>'
                    'Median-Prämie: CHF %{customdata[3]:,.0f}/Mt.<extra></extra>'
                ),
            ))

    fig.update_layout(
        height=520,
        margin=dict(l=60, t=8, b=40, r=8),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(size=12, color='#888'),
        xaxis=dict(title='Bevölkerungsanteil 66+ (%)', gridcolor='#f0f0f0', zeroline=False),
        yaxis=dict(title='Gesundheitskosten pro Kopf (CHF)', gridcolor='#f0f0f0', zeroline=False),
        legend=dict(
            orientation='v', x=1.01, y=1, xanchor='left', yanchor='top',
            font_size=11, title_text='Segment',
        ),
    )
    return fig


def _build_projection_chart(canton: str | None = None):
    dff = df_manager_priorities.sort_values('belastungsindex_2030').copy()
    canton_order = dff['canton_label'].tolist()

    fig = go.Figure()

    def _bar_color(flag):
        return '#d8232a' if flag == 'Prioritär beobachten' else '#acb4bd'

    if canton:
        other = dff[dff['canton_label'] != canton]
        sel = dff[dff['canton_label'] == canton]

        if not other.empty:
            fig.add_trace(go.Bar(
                x=other['belastungsindex_2030'],
                y=other['canton_label'],
                orientation='h',
                marker_color=[_bar_color(f) for f in other['priority_flag']],
                marker_opacity=0.18,
                name='Belastungsindex 2030',
                showlegend=False,
                customdata=np.stack([
                    other['belastungsindex_latest'],
                    other['delta_belastungsindex_to_2030'],
                    other['priority_flag'],
                    other['cost_per_capita_2030'],
                    other['population_share_66_plus_2030'] * 100,
                ], axis=-1),
                hovertemplate=(
                    '<b>%{y}</b><br>'
                    'Belastungsindex 2030: %{x:.2f}<br>'
                    'Aktuell: %{customdata[0]:.2f} · Δ %{customdata[1]:+.2f}<br>'
                    'Kosten 2030: CHF %{customdata[3]:,.0f}/Kopf<br>'
                    'Anteil 66+ 2030: %{customdata[4]:.1f}%<br>'
                    'Status: %{customdata[2]}<extra></extra>'
                ),
            ))

        if not sel.empty:
            row = sel.iloc[0]
            fig.add_trace(go.Bar(
                x=sel['belastungsindex_2030'],
                y=sel['canton_label'],
                orientation='h',
                marker_color=_bar_color(row['priority_flag']),
                name='Belastungsindex 2030',
                showlegend=True,
                customdata=np.stack([
                    sel['belastungsindex_latest'],
                    sel['delta_belastungsindex_to_2030'],
                    sel['priority_flag'],
                    sel['cost_per_capita_2030'],
                    sel['population_share_66_plus_2030'] * 100,
                ], axis=-1),
                hovertemplate=(
                    '<b>%{y}</b><br>'
                    'Belastungsindex 2030: %{x:.2f}<br>'
                    'Aktuell: %{customdata[0]:.2f} · Δ %{customdata[1]:+.2f}<br>'
                    'Kosten 2030: CHF %{customdata[3]:,.0f}/Kopf<br>'
                    'Anteil 66+ 2030: %{customdata[4]:.1f}%<br>'
                    'Status: %{customdata[2]}<extra></extra>'
                ),
            ))
    else:
        fig.add_trace(go.Bar(
            x=dff['belastungsindex_2030'],
            y=dff['canton_label'],
            orientation='h',
            marker_color=[_bar_color(f) for f in dff['priority_flag']],
            name='Belastungsindex 2030',
            customdata=np.stack([
                dff['belastungsindex_latest'],
                dff['delta_belastungsindex_to_2030'],
                dff['priority_flag'],
                dff['cost_per_capita_2030'],
                dff['population_share_66_plus_2030'] * 100,
            ], axis=-1),
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Belastungsindex 2030: %{x:.2f}<br>'
                'Aktuell: %{customdata[0]:.2f} · Δ %{customdata[1]:+.2f}<br>'
                'Kosten 2030: CHF %{customdata[3]:,.0f}/Kopf<br>'
                'Anteil 66+ 2030: %{customdata[4]:.1f}%<br>'
                'Status: %{customdata[2]}<extra></extra>'
            ),
        ))

    # Dots for current belastungsindex (per-point opacity)
    dot_opacity = [
        1.0 if (canton is None or row['canton_label'] == canton) else 0.18
        for _, row in dff.iterrows()
    ]
    fig.add_trace(go.Scatter(
        x=dff['belastungsindex_latest'],
        y=dff['canton_label'],
        mode='markers',
        marker=dict(color='#2f4356', size=6, symbol='circle', opacity=dot_opacity),
        name=f'Aktuell ({_latest_year})',
        hoverinfo='skip',
    ))

    fig.update_layout(
        height=620,
        margin=dict(l=0, r=8, t=8, b=40),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(size=11, color='#888'),
        yaxis=dict(categoryorder='array', categoryarray=canton_order, automargin=True),
        xaxis_title='Belastungsindex',
        legend=dict(orientation='h', x=0, y=1.02, xanchor='left', yanchor='bottom', font_size=11),
        barmode='overlay',
    )
    return fig


_fig_clusters = _build_cluster_scatter()
_fig_projection = _build_projection_chart()

tab = dcc.Tab(
    label="4. Segmente & Prognose", value="sq4", className="tab",
    style=TAB_STYLE, selected_style=TAB_SELECTED,
    children=[
        html.Div([
            # Header
            html.Div([
                html.Div("Belastungssegmente & Prognose 2030", style={
                    "fontSize": "18px", "fontWeight": "700", "color": "#2f4356",
                }),
                html.Div(
                    "Welche Kantone sind in kritischen Segmenten und wo steigt der Druck bis 2030?",
                    style={"fontSize": "12px", "color": "#888", "marginTop": "4px"},
                ),
            ], style={"marginBottom": "20px"}),

            # KPI row
            html.Div(
                _INITIAL_KPIS,
                style={"display": "flex", "gap": "12px", "marginBottom": "16px"},
            ),

            # Canton filter
            html.Div([
                html.Label("Kanton:", style={
                    "fontWeight": "600", "whiteSpace": "nowrap",
                    "fontSize": "13px", "color": "#555",
                }),
                dcc.Dropdown(
                    id='sq4-canton-dropdown',
                    options=[{"label": c, "value": c} for c in _CANTON_OPTIONS],
                    value=None,
                    clearable=True,
                    placeholder="Alle Kantone",
                    style={"flex": "1", "fontSize": "13px"},
                ),
            ], style={
                "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                "padding": "16px 20px", "marginBottom": "16px",
                "display": "flex", "alignItems": "center", "gap": "12px",
            }),

            # Charts
            html.Div([
                # Cluster scatter
                html.Div([
                    html.Div(f"Belastungssegmente nach Kanton ({_latest_year})", style={
                        "fontSize": "13px", "fontWeight": "600", "color": "#555", "marginBottom": "4px",
                    }),
                    html.Div(
                        f"Kantone mit ähnlichem Kosten- und Altersprofil bilden ein Segment"
                        f" · Kreisgrösse = Median-Prämie",
                        style={"fontSize": "11px", "color": "#aaa", "marginBottom": "8px"},
                    ),
                    dcc.Graph(id='sq4-scatter', figure=_fig_clusters, config={"displayModeBar": False}),
                ], style={
                    "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                    "padding": "16px", "flex": "1",
                }),

                # Projection bar
                html.Div([
                    html.Div("Erwarteter Belastungsindex 2030", style={
                        "fontSize": "13px", "fontWeight": "600", "color": "#555", "marginBottom": "4px",
                    }),
                    html.Div(
                        "Balken = Prognose 2030 · Punkt = aktueller Wert · Rot = prioritär beobachten",
                        style={"fontSize": "11px", "color": "#aaa", "marginBottom": "8px"},
                    ),
                    dcc.Graph(id='sq4-projection', figure=_fig_projection, config={"displayModeBar": False}),
                ], style={
                    "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                    "padding": "16px", "flex": "1",
                }),
            ], style={"display": "flex", "gap": "16px"}),

        ], style={"maxWidth": "1100px", "margin": "auto", "padding": "48px 32px 24px 32px"}),
    ],
)


@callback(
    Output('sq4-scatter', 'figure'),
    Output('sq4-projection', 'figure'),
    Input('sq4-canton-dropdown', 'value'),
)
def sq4_update(canton):
    return _build_cluster_scatter(canton), _build_projection_chart(canton)


@callback(
    Output('sq4-scatter', 'clickData'),
    Output('sq4-projection', 'clickData'),
    Input('sq4-canton-dropdown', 'value'),
    prevent_initial_call=True,
)
def sq4_reset_click_data(dropdown_value):
    if dropdown_value is None:
        return None, None
    return no_update, no_update


@callback(
    Output('sq4-canton-dropdown', 'value'),
    Input('sq4-scatter', 'clickData'),
    Input('sq4-projection', 'clickData'),
    State('sq4-canton-dropdown', 'value'),
    prevent_initial_call=True,
)
def sq4_click_to_dropdown(scatter_click, proj_click, current_value):
    from dash import ctx
    clicked = None
    if ctx.triggered_id == 'sq4-scatter' and scatter_click:
        pts = scatter_click.get('points', [])
        if pts:
            cd = pts[0].get('customdata')
            if cd:
                clicked = cd[0]
    elif ctx.triggered_id == 'sq4-projection' and proj_click:
        pts = proj_click.get('points', [])
        if pts:
            clicked = pts[0].get('y')
    if clicked is None:
        return no_update
    return None if clicked == current_value else clicked
