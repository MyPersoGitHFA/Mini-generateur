from dash import Dash, html

app = Dash(__name__)
app.layout = html.Div("Hello Patoche from Dash!")
server = app.server
