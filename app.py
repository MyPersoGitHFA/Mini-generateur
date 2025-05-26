import dash
from dash import dcc, html, Input, Output
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import io
import base64

app = dash.Dash(__name__)
server = app.server

def champ_magnetique(distance_mm):
    distance_cm = distance_mm / 10
    return max(0.01, 0.5 * np.exp(-distance_cm / 0.5))

def make_3d_scene(diametre_mm, distance_mm, nb_bobines):
    r_arbre = diametre_mm / 2000
    r_ext = r_arbre + distance_mm / 1000
    h = 0.05

    theta = np.linspace(0, 2*np.pi, 50)
    z = np.linspace(0, h, 10)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x_grid = r_arbre * np.cos(theta_grid)
    y_grid = r_arbre * np.sin(theta_grid)

    arbre = go.Surface(x=x_grid, y=y_grid, z=z_grid,
                       colorscale='Greys', showscale=False, opacity=0.6)

    aimants = []
    angle_step = 2 * np.pi / nb_bobines if nb_bobines > 0 else 0

    for i in range(nb_bobines):
        angle = i * angle_step
        x_a = r_ext * np.cos(angle)
        y_a = r_ext * np.sin(angle)
        x_b = r_ext * np.cos(angle + np.pi / nb_bobines)
        y_b = r_ext * np.sin(angle + np.pi / nb_bobines)

        aimants.append(go.Scatter3d(x=[x_a], y=[y_a], z=[h/2],
                                    mode='markers', marker=dict(size=6, color='red'), name='Aimant'))
        aimants.append(go.Scatter3d(x=[x_b], y=[y_b], z=[h/2],
                                    mode='markers', marker=dict(size=6, color='blue'), name='Bobine'))

    layout = go.Layout(
        scene=dict(
            xaxis=dict(title='x'),
            yaxis=dict(title='y'),
            zaxis=dict(title='z'),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        showlegend=False
    )

    return {'data': [arbre] + aimants, 'layout': layout}

app.layout = html.Div([
    html.H2("Mini Générateur à Aimants Permanents"),

    html.Div([
        html.Div([
            html.Label("Distance aimant-bobine (mm)"),
            dcc.Input(id='distance', type='number', value=3, min=0.5, step=0.1),
        ]),
        html.Div([
            html.Label("Surface bobine (cm²)"),
            dcc.Input(id='surface', type='number', value=2.0, min=0.1, step=0.1),
        ]),
        html.Div([
            html.Label("Nombre de spires par bobine"),
            dcc.Input(id='spires', type='number', value=200, min=1),
        ]),
        html.Div([
            html.Label("Nombre de bobines en série"),
            dcc.Input(id='nb_bobines', type='number', value=4, min=1),
        ]),
        html.Div([
            html.Label("Diamètre de l'arbre (mm)"),
            dcc.Input(id='diametre', type='number', value=20, min=1),
        ]),
        html.Div([
            html.Label("Vitesse de rotation (tr/min)"),
            dcc.Input(id='rpm', type='number', value=1000, min=1),
        ]),
    ], style={'width': '300px', 'display': 'flex', 'flexDirection': 'column', 'gap': '10px'}),

    html.Br(),
    html.Div(id='resultats'),
    html.Br(),
    html.Button("Exporter en CSV", id="export-button"),
    dcc.Download(id="download-dataframe-csv"),
    html.Br(), html.Br(),
    dcc.Graph(id='scene-3d')
])

@app.callback(
    Output('resultats', 'children'),
    Output('scene-3d', 'figure'),
    Output('download-dataframe-csv', 'data'),
    Input('distance', 'value'),
    Input('surface', 'value'),
    Input('spires', 'value'),
    Input('nb_bobines', 'value'),
    Input('diametre', 'value'),
    Input('rpm', 'value'),
    Input('export-button', 'n_clicks'),
    prevent_initial_call='initial_duplicate'
)
def calculer(distance_mm, surface_cm2, N, nb_bobines, diametre_mm, rpm, export_clicks):
    B = champ_magnetique(distance_mm)
    surface_m2 = surface_cm2 / 1e4
    rayon_m = diametre_mm / 2000
    omega = 2 * np.pi * rpm / 60
    v = omega * rayon_m

    e_bobine = (N * B * surface_m2 * v) / np.sqrt(2)
    e_total = nb_bobines * e_bobine

    R_par_bobine = 0.5
    R_total = nb_bobines * R_par_bobine

    puissance = e_total**2 / R_total

    texte = [
        html.P(f"Champ magnétique estimé B = {B:.3f} T"),
        html.P(f"Tension efficace totale : {e_total:.3f} V"),
        html.P(f"Puissance électrique disponible : {puissance*1000:.3f} mW")
    ]

    figure = make_3d_scene(diametre_mm, distance_mm, nb_bobines)

    if export_clicks:
        df = pd.DataFrame([{
            "Distance mm": distance_mm,
            "Surface cm2": surface_cm2,
            "Spires par bobine": N,
            "Nb bobines": nb_bobines,
            "Diamètre arbre mm": diametre_mm,
            "RPM": rpm,
            "Champ B (T)": B,
            "Tension (V)": e_total,
            "Puissance (W)": puissance
        }])
        return texte, figure, dcc.send_data_frame(df.to_csv, "resultats_generateurs.csv", index=False)

    return texte, figure, None



if __name__ == '__main__':
    app.run_server(debug=True)
