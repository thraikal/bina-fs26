from dash import dcc

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
