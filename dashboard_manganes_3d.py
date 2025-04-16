
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Inicializar app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Carregar e preparar os dados
try:
    df = pd.read_excel("data/ASSAY.xlsx")
    df = df.rename(columns=lambda x: x.strip().upper())
    df.rename(columns={
        "MN": "MN_%",
        "X": "X",
        "Y": "Y",
        "Z": "Z",
        "LOCAL": "LOCAL",
        "FURO": "FURO",
        "AMOSTRA": "AMOSTRA"
    }, inplace=True)
    df = df.dropna(subset=["MN_%"])
except Exception as e:
    print("Erro ao carregar os dados:", e)
    df = pd.DataFrame()

# Layout do app
app.layout = dbc.Container([
    html.H2("Dashboard de Teores de Manganês", className="text-center my-4"),
    dbc.Row([
        dbc.Col([
            html.Label("Tipo de gráfico:"),
            dcc.RadioItems(
                id="tipo-grafico",
                options=[
                    {"label": "Gráfico 3D", "value": "3d"},
                    {"label": "Gráfico de Barras", "value": "barras"}
                ],
                value="3d",
                inline=True
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="grafico")
        ])
    ]),
    html.Hr(),
    html.Div(id="resumo", className="mt-3")
], fluid=True)

# Callback de atualização
@app.callback(
    [Output("grafico", "figure"),
     Output("resumo", "children")],
    [Input("tipo-grafico", "value")]
)
def atualizar_grafico(tipo):
    if df.empty:
        return px.scatter_3d(), "Erro ao carregar dados da planilha ASSAY."

    if tipo == "3d":
        fig = px.scatter_3d(
            df,
            x="X", y="Y", z="Z",
            color="MN_%",
            size="MN_%",
            hover_data=["AMOSTRA", "FURO", "LOCAL", "MN_%"],
            color_continuous_scale="Hot",
            title="Teores de Manganês (%) - Visualização 3D"
        )
    else:
        fig = px.bar(
            df,
            x="FURO", y="MN_%",
            color="LOCAL",
            hover_data=["AMOSTRA", "MN_%"],
            title="Teor de Manganês por Furo"
        )

    # Frases descritivas automáticas
    frases = []
    for local in df["LOCAL"].unique():
        sub_df = df[df["LOCAL"] == local]
        for furo in sub_df["FURO"].unique():
            dados = sub_df[sub_df["FURO"] == furo]
            maior = dados["MN_%"].max()
            media = dados["MN_%"].mean()
            frases.append(html.P(
                f"Na localidade {local}, no furo {furo}, encontramos manganês com teor máximo de {maior:.2f}%. "
                f"A média das {len(dados)} amostras analisadas é de {media:.2f}%."
            ))

    return fig, frases

# Execução local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
