# dashboard_manganes_3d.py

import pandas as pd
import plotly.graph_objs as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import os

# Caminho absoluto para o arquivo Excel
file_path = os.path.abspath("data/ASSAY.xlsx")
df = pd.read_excel(file_path)

# Normalizar nomes das colunas
df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace(".", "_", regex=False)

# Garantir colunas necessárias
if "Furo" not in df.columns or "z" not in df.columns or "Mn" not in df.columns:
    raise ValueError("Planilha deve conter as colunas 'Furo', 'z' (profundidade) e 'Mn'.")

# Calcular Mn_% se necessário
if "Mn_%" not in df.columns:
    df["Mn_%"] = (df["Mn"] / 10000).round(2)  # de ppm para %

# Lista de todos os furos conhecidos do projeto
furos_conhecidos = [
    "FCC-1-1", "FCC-2-2", "FCC-3-3", "FCC-4-4", "FCC-5-5", "FCC-6-6", "FCC-7-7", "FCC-8-8", "FCC-9-9", "FCC-10-10",
    "FCN-1-25", "FCN-2-26", "FCN-3-27", "FCN-4-28", "FCN-5-29", "FCN-6-30",
    "FBC-1-31", "FBC-2-32", "FBC-3-33", "FBC-4-34", "FBC-5-35", "FBC-6-36",
    "FCZ-1-11", "FCZ-2-2", "FCZ-3-13", "FCZ-4-14", "FCZ-5-15", "FCZ-6-16",
    "FMB-1-37", "FMB-2-38", "FMB-3-39", "FMB-4-40", "FMB-5-41", "FMB-6-42", "FMB-7-43", "FMB-8-44", "FMB-9-45",
    "FMB-10-46", "FMB-11-47", "FMB-12-48", "FMB-13-49", "FMB-14-50", "FMB-15-51",
    "FBU-1-17", "FBU-2-18", "FBU-3-19", "FBU-4-20", "FBU-5-21", "FBU-6-22", "FBU-7-23", "FBU-8-24",
    "CN1-1-56", "CN1-2-57", "CN1-3-58", "CN1-4-59", "CN1-5-60", "CN1-6-61", "CN1-7-62", "CN1-8-63",
    "FNA-1-54", "FNA-2-55"
]

# Função para colorir as barras com base no teor
def cor_mapa_calor(valor):
    if valor < 5:
        return "darkblue"
    elif valor < 10:
        return "deepskyblue"
    elif valor < 15:
        return "green"
    elif valor < 20:
        return "yellow"
    elif valor < 30:
        return "orange"
    elif valor < 40:
        return "red"
    else:
        return "darkred"

# Inicialização do app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Interativo - Teores de Manganês"

app.layout = html.Div([
    html.H1("Dashboard Interativo - Teores de Manganês por Furo", style={"textAlign": "center"}),

    html.Label("Filtrar por Teor Mínimo de Mn (%)"),
    dcc.Slider(0, 50, step=1, value=0, marks={i: f"{i}%" for i in range(0, 51, 10)}, id="mn-slider"),

    dcc.Dropdown(options=[{"label": furo, "value": furo} for furo in furos_conhecidos],
                 id="furo-dropdown",
                 placeholder="Selecione um furo para análise detalhada"),

    html.Div(id="descricao-furo"),

    dcc.Tabs(id="tabs", value="barras", children=[
        dcc.Tab(label="Gráfico de Barras", value="barras"),
        dcc.Tab(label="Gráfico de Pizza", value="pizza"),
        dcc.Tab(label="Gráfico 3D (em breve)", value="3d", disabled=True)
    ]),

    dcc.Graph(id="grafico-analise")
])

@app.callback(
    Output("grafico-analise", "figure"),
    Output("descricao-furo", "children"),
    Input("mn-slider", "value"),
    Input("furo-dropdown", "value"),
    Input("tabs", "value")
)
def atualizar_visual(mn_min, furo, aba):
    if furo is None:
        return go.Figure(), html.P("Selecione um furo para análise.")

    dados_furo = df[df["Furo"] == furo]

    if dados_furo.empty:
        return go.Figure(), html.P(f"O furo {furo} ainda não possui dados de amostragem registrados no sistema.")

    dados_filtrados = dados_furo[dados_furo["Mn_%"] >= mn_min]

    if aba == "barras":
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dados_filtrados["Mn_%"],
            y=dados_filtrados["z"],
            orientation="h",
            marker_color=dados_filtrados["Mn_%"].apply(cor_mapa_calor),
            text=[f"{z}m: {mn}%" for z, mn in zip(dados_filtrados["z"], dados_filtrados["Mn_%"])],
            hoverinfo="text"
        ))
        fig.update_layout(
            title="Teor de Mn por Metro (Profundidade)",
            xaxis_title="Mn (%)",
            yaxis_title="Profundidade (m)",
            yaxis=dict(autorange="reversed"),
            height=500
        )
        
    elif aba == "pizza":
        locais = df.groupby("LOCAL")
        labels, values, textos = [], [], []
        for nome, grupo in locais:
            labels.append(nome)
            valores = grupo["Mn_%"]
            values.append(valores.max())
            textos.append(f"Mn Max: {valores.max():.2f}%, Média: {valores.mean():.2f}%, Amostras: {len(valores)}")

        fig = go.Figure(data=[go.Pie(labels=labels, values=values, text=textos, hoverinfo="label+text+percent")])
        fig.update_layout(title="Distribuição de Mn por Localidade (Maior teor)")

    else:
        fig = go.Figure()

    maior = dados_furo["Mn_%"].max()
    menor = dados_furo["Mn_%"].min()
    media = dados_furo["Mn_%"].mean()
    amostras = len(dados_furo)
    loc = dados_furo["LOCAL"].iloc[0] if "LOCAL" in dados_furo.columns else "desconhecida"
    frase = (
        f"Análise do furo {furo}: localizado em {loc}, onde coletamos {amostras} amostras por sondagem, "
        f"armazenadas na caixa de amostra ID:{furo}. A leitura XRF foi feita com 2 disparos por amostra. "
        f"Maior teor de Mn: {maior:.2f}%. Menor: {menor:.2f}%. Média: {media:.2f}%."
    )

    return fig, dcc.Markdown(frase)

if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=10000)
