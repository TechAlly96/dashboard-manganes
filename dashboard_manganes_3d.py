# Dashboard Manganês - Código Corrigido e Melhorado
# Por: Marlon Myaggy
# Descrição: Dashboard interativo com gráficos 3D de hastes, barras horizontais e pizza com informações completas

import os
import pandas as pd
import plotly.graph_objs as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

# Caminho para o arquivo Excel
excel_path = os.path.join("data", "ASSAY.xlsx")
df = pd.read_excel(excel_path)

# Padronização das colunas
df.columns = df.columns.str.strip().str.replace(' ', '_').str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

# Mapeamento das colunas obrigatórias
COLUNA_FURO = "Furo"
COLUNA_DEPTH_FROM = "DEPTH_FROM"
COLUNA_DEPTH_TO = "DEPTH_TO"
COLUNA_MN = "Mn"
COLUNA_LOCALIDADE = "LOCAL"

for col in [COLUNA_FURO, COLUNA_DEPTH_FROM, COLUNA_DEPTH_TO, COLUNA_MN, COLUNA_LOCALIDADE]:
    if col not in df.columns:
        raise ValueError(f"Coluna obrigatória ausente: {col}")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Interativo - Análise de Manganês"

# Escala de cores
def color_scale(mn):
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
    html.H2("Dashboard Interativo - Análise de Manganês", className="text-center mt-4"),
    dcc.Tabs([
        dcc.Tab(label="Gráfico 3D de Hastes", children=[
            html.Br(),
            html.Label("Filtrar por Teor de Mn mínimo (%)"),
            dcc.Slider(0, 50, step=1, value=0, marks={i: f"{i}%" for i in range(0, 51, 10)}, id="mn-slider"),
            dcc.Dropdown(
                options=[{"label": furo, "value": furo} for furo in sorted(df[COLUNA_FURO].unique())],
                id="furo-dropdown",
                placeholder="Selecionar furo para análise detalhada",
            ),
            html.Div(id="descricao-furo", className="mt-3"),
            dcc.Graph(id="grafico-3d")
        ]),
        dcc.Tab(label="Gráfico de Barras por Furo", children=[
            dcc.Graph(id="grafico-barras")
        ]),
        dcc.Tab(label="Gráfico de Pizza por Localidade", children=[
            dcc.Graph(id="grafico-pizza")
        ])
    ])
], fluid=True)

@app.callback(
    Output("grafico-3d", "figure"),
    Output("descricao-furo", "children"),
    Input("mn-slider", "value"),
    Input("furo-dropdown", "value")
)
def atualizar_grafico_3d(mn_min, furo_selecionado):
    try:
        dff = df[df[COLUNA_MN] >= mn_min]
        if furo_selecionado:
            dff = dff[dff[COLUNA_FURO] == furo_selecionado]

        if dff.empty:
            return go.Figure(), html.P("Nenhum dado para exibir com esse filtro.", style={"color": "red"})

        fig = go.Figure()
        for furo in dff[COLUNA_FURO].unique():
            dados_furo = dff[dff[COLUNA_FURO] == furo]
            for _, row in dados_furo.iterrows():
                fig.add_trace(go.Scatter3d(
                    x=[furo, furo],
                    y=[-row[COLUNA_DEPTH_FROM], -row[COLUNA_DEPTH_TO]],
                    z=[0, 0],
                    mode="lines",
                    line=dict(color=color_scale(row[COLUNA_MN]), width=10),
                    name=f"{furo} | Mn: {row[COLUNA_MN]:.2f}%"
                ))

        fig.update_layout(scene=dict(
            xaxis_title="Furo",
            yaxis_title="Profundidade (m)",
            zaxis_title="",
        ), showlegend=False)

        if furo_selecionado:
            amostras = df[df[COLUNA_FURO] == furo_selecionado]
            n_amostras = len(amostras)
            max_mn = amostras[COLUNA_MN].max()
            min_mn = amostras[COLUNA_MN].min()
            media_mn = amostras[COLUNA_MN].mean()
            loc = amostras[COLUNA_LOCALIDADE].iloc[0]
            frase = f"""
**Análise do furo {furo_selecionado}**: localizado em **{loc}**, onde coletamos **{n_amostras} amostras por sondagem**,
sendo uma amostra por metro perfurado armazenadas na caixa de amostra **ID:{furo_selecionado}**.
A leitura foi realizada em **{n_amostras * 2} disparos XRF**.  
**Maior teor de Mn (Manganês): {max_mn:.2f}%**  
**Menor teor de Mn: {min_mn:.2f}%**  
**Média de Mn: {media_mn:.2f}%**
"""
            return fig, dcc.Markdown(frase)

        return fig, ""

    except Exception as e:
        return go.Figure(), html.P(f"Erro ao carregar os dados: {e}", style={"color": "red"})

@app.callback(
    Output("grafico-barras", "figure"),
    Input("mn-slider", "value")
)
def grafico_barras(mn_min):
    dff = df[df[COLUNA_MN] >= mn_min]
    barras = dff.groupby(COLUNA_FURO)[COLUNA_MN].mean().sort_values()
    return go.Figure(data=[
        go.Bar(y=barras.index, x=barras.values, orientation='h', marker_color="mediumturquoise")
    ]).update_layout(title="Média de Mn por Furo", xaxis_title="Mn (%)", yaxis_title="Furo")

@app.callback(
    Output("grafico-pizza", "figure"),
    Input("mn-slider", "value")
)
def grafico_pizza(mn_min):
    dff = df[df[COLUNA_MN] >= mn_min]
    localidades = dff.groupby(COLUNA_LOCALIDADE)

    labels, valores, textos = [], [], []
    for local, grupo in localidades:
        max_mn = grupo[COLUNA_MN].max()
        mean_mn = grupo[COLUNA_MN].mean()
        amostras = grupo.shape[0]
        disparos = amostras * 2
        labels.append(local)
        valores.append(max_mn)
        textos.append(f"Máx: {max_mn:.2f}%\nMédia: {mean_mn:.2f}%\nAmostras: {amostras}\nDisparos: {disparos}")

    fig = go.Figure(data=[
        go.Pie(labels=labels, values=valores, text=textos, hoverinfo="label+text+percent")
    ])
    fig.update_layout(title="Distribuição Máxima de Mn por Localidade (sem duplicidade)")
    return fig

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
