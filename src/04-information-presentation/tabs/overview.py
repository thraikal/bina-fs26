import plotly.express as px
from dash import dcc, html

from data import cantons, df_analysis_panel, df_manager_priorities
from styles import BORDER, CARD_BG, TAB_STYLE, TAB_SELECTED

_latest_year = int(df_analysis_panel['year'].max())
_baseline_year = int(df_analysis_panel['year'].min())
_panel_latest = df_analysis_panel[df_analysis_panel['year'] == _latest_year].copy()
_panel_latest['share_pct_66'] = _panel_latest['population_share_66_plus'] * 100

_avg_cost = _panel_latest['cost_per_capita'].mean()
_avg_premium = _panel_latest['premium_median_monthly'].mean()
_avg_age_share = _panel_latest['population_share_66_plus'].mean()


def _kpi_card(card_id, value, label):
    return html.Div([
        html.Div(value, style={"fontSize": "22px", "fontWeight": "700", "color": "#2f4356"}),
        html.Div(label, style={"fontSize": "12px", "color": "#444", "marginTop": "4px", "fontWeight": "600"}),
        html.Div("Detail ansehen →", className="kpi-hint", style={"fontSize": "10px", "color": "#d8232a", "marginTop": "8px", "fontWeight": "600"}),
    ], id=card_id, n_clicks=0, className="kpi-card-link", style={
        "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
        "padding": "16px 20px", "flex": "1", "cursor": "pointer",
    })


def _build_belastung_map():
    fig = px.choropleth(
        _panel_latest,
        geojson=cantons,
        locations='canton_label',
        featureidkey='properties.name',
        color='belastungsindex',
        hover_name='canton_label',
        hover_data={
            'cost_per_capita': ':,.0f',
            'share_pct_66': ':.1f',
            'premium_median_monthly': ':,.0f',
            'belastungsindex': ':.2f',
            'canton_label': False,
        },
        color_continuous_scale='Reds',
        labels={
            'belastungsindex': 'Belastungsindex',
            'cost_per_capita': 'Kosten pro Kopf (CHF)',
            'share_pct_66': 'Anteil 66+ (%)',
            'premium_median_monthly': 'Median-Prämie (CHF/Mt.)',
        },
    )
    fig.update_geos(
        visible=False, projection_type='mercator',
        lonaxis_range=[4.8, 11.8], lataxis_range=[45.5, 48.1],
    )
    fig.update_coloraxes(colorbar=dict(
        orientation='h', x=0.5, y=1.01, xanchor='center', yanchor='bottom',
        thickness=10, len=0.7, title_text='Belastungsindex', title_side='top',
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=48, b=0), autosize=True,
        font=dict(size=12, color='#888'),
    )
    return fig


def _priority_rows():
    top5 = df_manager_priorities.sort_values('belastungsindex_2030', ascending=False).head(5)
    rows = []
    _TH = {"padding": "7px 8px", "fontSize": "13px"}
    for _, row in top5.iterrows():
        delta = row['delta_belastungsindex_to_2030']
        is_priority = row['priority_flag'] == 'Prioritär beobachten'
        rows.append(html.Tr([
            html.Td(row['canton_label'], style={**_TH}),
            html.Td(f"{row['belastungsindex_latest']:.2f}", style={**_TH, "textAlign": "right"}),
            html.Td(f"{row['belastungsindex_2030']:.2f}", style={**_TH, "textAlign": "right", "fontWeight": "600"}),
            html.Td(
                f"+{delta:.2f}" if delta > 0.01 else (f"-{abs(delta):.2f}" if delta < -0.01 else f"{delta:.2f}"),
                style={
                    **_TH, "textAlign": "right",
                    "color": "#d8232a" if delta > 0.01 else ("#2a8a4a" if delta < -0.01 else "#888"),
                },
            ),
            html.Td(
                html.Span("Prioritär", style={
                    "background": "#d8232a" if is_priority else "#ccc",
                    "color": "#fff", "borderRadius": "3px",
                    "padding": "2px 6px", "fontSize": "10px", "whiteSpace": "nowrap",
                }),
                style={"padding": "7px 8px", "textAlign": "center"},
            ),
        ], style={"borderBottom": "1px solid #f0f0f0"}))
    return rows


_TH_STYLE = {"padding": "5px 8px", "fontSize": "11px", "color": "#888", "fontWeight": "600",
             "borderBottom": "1px solid #ddd", "whiteSpace": "nowrap"}

tab = dcc.Tab(
    label="Übersicht", value="overview", className="tab",
    style=TAB_STYLE, selected_style=TAB_SELECTED,
    children=[
        html.Div([
            # Header
            html.Div([
                html.Div("Kantonale Gesundheitsbelastung im Überblick", style={
                    "fontSize": "18px", "fontWeight": "700", "color": "#2f4356",
                }),
                html.Div(
                    f"Gesundheitskosten, Alterung & Prämienbelastung in der Schweiz, Analysefenster {_baseline_year}–{_latest_year}",
                    style={"fontSize": "12px", "color": "#888", "marginTop": "4px"},
                ),
            ], style={"marginBottom": "20px"}),

            html.Div([
                _kpi_card("factor-cost",    f"CHF {_avg_cost / 12:,.0f}".replace(',', "'") + " / Monat", "Ø Gesundheitskosten pro Kopf"),
                _kpi_card("factor-premium", f"CHF {_avg_premium:,.0f} / Monat", "Ø Median-Basisprämie aller Kantone"),
                _kpi_card("factor-age",     f"{_avg_age_share:.1%}", "Ø Bevölkerungsanteil 66+ (Schweiz)"),
            ], style={"display": "flex", "gap": "16px", "marginBottom": "16px"}),

            # Belastungsindex entry card
            html.Div([
                html.Div("Was ist der Belastungsindex?", style={
                    "fontSize": "14px", "fontWeight": "700", "color": "#2f4356", "marginBottom": "6px",
                }),
                html.Div(
                    "Der Belastungsindex misst, wie stark ein Kanton vom Schweizer Durchschnitt abweicht — "
                    "positiv bedeutet stärker belastet, negativ bedeutet geringer belastet. "
                    "Er setzt sich aus drei gleich gewichteten Faktoren zusammen:",
                    style={"fontSize": "12px", "color": "#555", "lineHeight": "1.6", "marginBottom": "10px"},
                ),
                html.Ul([
                    html.Li("45% — Gesundheitskosten pro Kopf nach Kanton (grösster Treiber)", style={"marginBottom": "4px"}),
                    html.Li("30% — Bevölkerungsanteil 66+ als Proxy für langfristigen Kostendruck", style={"marginBottom": "4px"}),
                    html.Li("25% — Median-Basisprämie relativ zum kantonalen Kostenprofil"),
                ], style={"fontSize": "12px", "color": "#555", "lineHeight": "1.6", "margin": "0", "paddingLeft": "20px"}),
            ], style={
                "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                "padding": "20px 24px", "marginBottom": "12px",
            }),

            # Map + priority table
            html.Div([
                # Choropleth
                html.Div([
                    html.Div(
                        f"Kantonaler Belastungsindex {_latest_year}",
                        style={"fontSize": "13px", "fontWeight": "600", "color": "#555", "marginBottom": "4px"},
                    ),
                    html.Div(
                        dcc.Graph(figure=_build_belastung_map(), config={"displayModeBar": False},
                                  responsive=True, style={"height": "100%"}),
                        style={"width": "100%", "aspectRatio": "1.6 / 1"},
                    ),
                ], style={
                    "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                    "padding": "16px", "flex": "3",
                }),

                # Priority table
                html.Div([
                    html.Div([
                        html.Div("Höchste Belastung 2030", style={
                            "fontSize": "13px", "fontWeight": "700", "color": "#2f4356",
                        }),
                        html.Div("Sortiert nach erwartetem Belastungsindex 2030", style={
                            "fontSize": "11px", "color": "#aaa", "marginTop": "2px", "marginBottom": "10px",
                        }),
                    ]),
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Kanton", style={**_TH_STYLE, "textAlign": "left"}),
                            html.Th(f"{_latest_year}", style={**_TH_STYLE, "textAlign": "right"}),
                            html.Th("2030", style={**_TH_STYLE, "textAlign": "right"}),
                            html.Th("Trend", style={**_TH_STYLE, "textAlign": "right"}),
                            html.Th("", style=_TH_STYLE),
                        ])),
                        html.Tbody(_priority_rows()),
                    ], style={"width": "100%", "borderCollapse": "collapse"}),
                    html.Div("Vollanalyse in SQ4 ansehen →", className="kpi-hint", style={
                        "fontSize": "10px", "color": "#d8232a", "marginTop": "10px", "fontWeight": "600",
                    }),
                ], id="overview-priority-table", n_clicks=0, className="kpi-card-link", style={
                    "background": CARD_BG, "border": BORDER, "borderRadius": "8px",
                    "padding": "16px", "flex": "2", "cursor": "pointer",
                }),
            ], style={"display": "flex", "gap": "16px"}),

        ], style={"maxWidth": "1100px", "margin": "auto", "padding": "48px 32px 24px 32px"}),
    ],
)
