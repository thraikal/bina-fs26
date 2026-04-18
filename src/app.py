from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

app = Dash()

app.layout = [
    html.H1('From Data to Decisions', style={'textAlign': 'center'}),
    dcc.Dropdown(df.country.unique(), 'Switzerland', id='country-dropdown'),
    dcc.Graph(id='graph-content')
]

@callback(
    Output('graph-content', 'figure'),
    Input('country-dropdown', 'value')
)
def update_graph(selected_country):
    dff = df[df.country == selected_country]
    return px.line(dff, x='year', y='pop')

if __name__ == '__main__':
    app.run(debug=True)