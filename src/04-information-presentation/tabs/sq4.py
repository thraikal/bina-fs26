import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from dash import dcc, html

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


def _build_cluster_scatter():
    dff = _cluster_df.copy()
    dff['share_pct'] = dff['population_share_66_plus'] * 100

    fig = px.scatter(
        dff,
        x='share_pct',
        y='cost_per_capita',
        color='cluster_name',
        size='premium_median_monthly',
        hover_name='canton_label',
        text='canton_code',
        color_discrete_map=_CLUSTER_COLORS,
        category_orders={'cluster_name': list(_RANK_TO_NAME.values())},
        labels={
            'share_pct': 'Bevölkerungsanteil 66+ (%)',
            'cost_per_capita': 'Gesundheitskosten pro Kopf (CHF)',
            'premium_median_monthly': 'Median-Prämie (CHF/Mt.)',
            'cluster_name': 'Segment',
        },
        custom_data=['canton_label', 'cluster_name', 'belastungsindex', 'premium_median_monthly'],
    )
    fig.update_traces(
        textposition='top center',
        textfont_size=10,
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            'Segment: %{customdata[1]}<br>'
            'Belastungsindex: %{customdata[2]:.2f}<br>'
            'Kosten pro Kopf: CHF %{y:,.0f}<br>'
            'Anteil 66+: %{x:.1f}%<br>'
            'Median-Prämie: CHF %{customdata[3]:,.0f}/Mt.<extra></extra>'
        ),
    )
    fig.update_layout(
        height=520,
        margin=dict(l=60, t=8, b=40, r=8),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(size=12, color='#888'),
        legend=dict(
            orientation='v', x=1.01, y=1, xanchor='left', yanchor='top',
            font_size=11, title_text='Segment',
        ),
    )
    return fig


def _build_projection_chart():
    dff = df_manager_priorities.sort_values('belastungsindex_2030').copy()
    canton_order = dff['canton_label'].tolist()

    fig = go.Figure()

    # bars for 2030 belastungsindex
    colors = ['#d8232a' if f == 'Prioritär beobachten' else '#acb4bd' for f in dff['priority_flag']]
    fig.add_trace(go.Bar(
        x=dff['belastungsindex_2030'],
        y=dff['canton_label'],
        orientation='h',
        marker_color=colors,
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
            'Aktuell (%{customdata[0]:.2f}) → Δ %{customdata[1]:+.2f}<br>'
            'Kosten 2030: CHF %{customdata[3]:,.0f} pro Kopf<br>'
            'Anteil 66+ 2030: %{customdata[4]:.1f}%<br>'
            'Status: %{customdata[2]}<extra></extra>'
        ),
    ))

    # dots for current belastungsindex
    fig.add_trace(go.Scatter(
        x=dff['belastungsindex_latest'],
        y=dff['canton_label'],
        mode='markers',
        marker=dict(color='#2f4356', size=6, symbol='circle'),
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
            html.Div([
                html.Div("Belastungssegmente & Prognose 2030", style={
                    "fontSize": "18px", "fontWeight": "700", "color": "#2f4356",
                }),
                html.Div(
                    f"Kantonale Segmentierung ({_latest_year}) und lineare Trendfortschreibung bis 2030",
                    style={"fontSize": "12px", "color": "#888", "marginTop": "4px"},
                ),
            ], style={"marginBottom": "20px"}),

            html.Div([
                # Cluster scatter
                html.Div([
                    html.Div("Belastungssegmente nach Alterung & Kosten", style={
                        "fontSize": "13px", "fontWeight": "600", "color": "#555", "marginBottom": "4px",
                    }),
                    html.Div(
                        f"K-Means k=6 · Grösse = Median-Prämie · Jahr {_latest_year}",
                        style={"fontSize": "11px", "color": "#aaa", "marginBottom": "8px"},
                    ),
                    dcc.Graph(figure=_fig_clusters, config={"displayModeBar": False}),
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
                    dcc.Graph(figure=_fig_projection, config={"displayModeBar": False}),
                ], style={
                    "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                    "padding": "16px", "flex": "1",
                }),
            ], style={"display": "flex", "gap": "16px"}),

        ], style={"maxWidth": "1100px", "margin": "auto", "padding": "48px 32px 24px 32px"}),
    ],
)
