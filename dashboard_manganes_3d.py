# dashboard_manganes_3d.py
import pandas as pd
import plotly.graph_objs as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import os

# Lista completa de furos do projeto
FUROS_CONHECIDOS = [
    "FCC-1-1", "FCC-2-2", "FCC-3-3", "FCC-4-4", "FCC-5-5", "FCC-6-6", "FCC-7-7", "FCC-8-8", "FCC-9-9", "FCC-10-10",
    "FCN-1-25", "FCN-2-26", "FCN-3-27", "FCN-4-28", "FCN-5-29", "FCN-6-30",
    "FBC-1-31", "FBC-2-32", "FBC-3-33", "FBC-4-34", "FBC-5-35", "FBC-6-36",
    "FCZ-1-11", "FCZ-2-2", "FCZ-3-13", "FCZ-4-14", "FCZ-5-15", "FCZ-6-16",
    "FMB-1-37", "FMB-2-38", "FMB-3-39", "FMB-4-40", "FMB-5-41", "FMB-6-42", "FMB-7-43", "FMB-8-44", "FMB-9-45", "FMB-10-46",
    "FMB-11-47", "FMB-12-48", "FMB-13-49", "FMB-14-50", "FMB-15-51",
    "FBU-1-17", "FBU-2-18", "FBU-3-19", "FBU-4-20", "FBU-5-21", "FBU-6-22", "FBU-7-23", "FBU-8-24",
    "CN1-1-56", "CN1-2-57", "CN1-3-58", "CN1-4-59", "CN1-5-60", "CN1-6-61", "CN1-7-62", "CN1-8-63",
    "FNA-1-54", "FNA-2-55"
]

# Caminho da planilha
file_path = os.path.join("data", "ASSAY.xlsx")
df = pd.read_excel(file_path)
df.columns = df.columns.str.strip().str.replace(' ', '_')

# Normaliza colunas
COL_FURO = "Furo"
COL_DEPTH_FROM = "DEPTH_FROM"
COL_DEPTH_TO = "DEPTH_TO"
COL_MN = "Mn"
COL_LOCAL = "LOCAL"

for col in [COL_FURO, COL_DEPTH_FROM, COL_DEPTH_TO, COL_MN, COL_LOCAL]:
    if col not in df.columns:
        raise ValueError(f"Coluna obrigatória ausente: {col}")

# Inicializa app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard de Manganês"

def escala_cores(mn):
    if mn < 5:
        return "darkblue"
    elif mn < 10:
        return "deepskyblue"
    elif mn < 15:
        return "green"
    elif mn < 20:
        return "yellow"
    elif mn < 30:
        return "orange"
    elif mn < 40:
        return "red"
    else:
        return "darkred"

app.layout = dbc.Container([
    html.H2("Dashboard Interativo - Teores de Manganês por Furo"),
    html.Hr(),
    dbc.Row([
        dbc.Col([
            html.Label("Filtrar por Teor Mínimo de Mn (%)"),
            dcc.Slider(0, 50, 1, value=0, id="mn-slider", marks={i: f"{i}%" for i in range(0, 51, 10)}),
            dcc.Dropdown(
                options=[{"label": furo, "value": furo} for furo in FUROS_CONHECIDOS],
                id="furo-dropdown",
                placeholder="Selecione o furo",
                multi=False
            ),
            html.Div(id="frase-inteligente")
        ], md=4),
        dbc.Col([
            dcc.Graph(id="grafico-3d")
        ], md=8)
    ]),
    html.Hr(),
    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico-barras"), md=6),
        dbc.Col(dcc.Graph(id="grafico-pizza"), md=6),
    ])
], fluid=True)

@app.callback(
    Output("grafico-3d", "figure"),
    Output("frase-inteligente", "children"),
    Input("mn-slider", "value"),
    Input("furo-dropdown", "value")
)
def atualizar_visualizacao(mn_min, furo):
    if not furo:
        return go.Figure(), "Selecione um furo para análise detalhada."

    dados_furo = df[df[COL_FURO] == furo]
    if dados_furo.empty:
        return go.Figure(), f"O furo {furo} ainda não possui dados de amostragem registrados no sistema."

    dados_filtrados = dados_furo[dados_furo[COL_MN] >= mn_min]
    cores = dados_filtrados[COL_MN].apply(escala_cores)

    fig = go.Figure(data=[go.Scatter3d(
        x=dados_filtrados[COL_FURO],
        y=-dados_filtrados[COL_DEPTH_FROM],
        z=[0]*len(dados_filtrados),
        mode="markers",
        marker=dict(size=6, color=cores),
        text=[f"Mn: {v:.2f}%" for v in dados_filtrados[COL_MN]],
        hoverinfo="text"
    )])

    fig.update_layout(scene=dict(
        xaxis_title="Furo",
        yaxis_title="Profundidade (m)",
        zaxis_title="",
        yaxis=dict(autorange="reversed")
    ))

    maior = dados_furo[COL_MN].max()
    menor = dados_furo[COL_MN].min()
    media = dados_furo[COL_MN].mean()
    local = dados_furo[COL_LOCAL].iloc[0]
    disparos = dados_furo.shape[0] * 2
    frase = (
        f"Análise do furo {furo}: localizado em {local}, onde coletamos {dados_furo.shape[0]} amostras por sondagem, "
        f"sendo uma amostra por metro perfurado organizadas e armazenadas na caixa de amostra ID:{furo}. A leitura foi realizada com 2 disparos por amostra.\n"
        f"Maior teor de Mn: {maior:.2f}%. Menor teor: {menor:.2f}%. Média: {media:.2f}% em {disparos} disparos."
    )
    return fig, frase

@app.callback(
    Output("grafico-barras", "figure"),
    Input("mn-slider", "value")
)
def grafico_barras(mn_min):
    barras = df[df[COL_MN] >= mn_min].groupby(COL_FURO)[COL_MN].mean()
    for furo in FUROS_CONHECIDOS:
        if furo not in barras:
            barras[furo] = 0
    barras = barras[FUROS_CONHECIDOS]  # ordena conforme lista original
    fig = go.Figure([go.Bar(y=barras.index, x=barras.values, orientation="h", marker_color="darkcyan")])
    fig.update_layout(title="Média de Mn por Furo", xaxis_title="Mn (%)")
    return fig

@app.callback(
    Output("grafico-pizza", "figure"),
    Input("mn-slider", "value")
)
def grafico_pizza(mn_min):
    dff = df[df[COL_MN] >= mn_min]
    agrupado = dff.groupby(COL_LOCAL)[COL_MN].agg(["mean", "max", "count"])
    agrupado = agrupado.reset_index()

    labels = agrupado[COL_LOCAL]
    values = agrupado["max"]
    textos = [
        f"Localidade: {row[COL_LOCAL]}<br>Mn Máx: {row['max']:.2f}%<br>Média: {row['mean']:.2f}%<br>Amostras: {row['count']}"
        for _, row in agrupado.iterrows()
    ]
    fig = go.Figure([go.Pie(labels=labels, values=values, text=textos, hoverinfo="text")])
    fig.update_layout(title="Distribuição de Mn por Localidade")
    return fig

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
