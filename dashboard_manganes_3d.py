import pandas as pd
import plotly.graph_objs as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

# Caminho para o arquivo Excel
df = pd.read_excel("data/ASSAY.xlsx")

# Nomes das colunas
COLUNA_FURO = "Furo"
COLUNA_DEPTH_FROM = "Profundidade_Inicial"
COLUNA_DEPTH_TO = "Profundidade_Final"
COLUNA_MN = "Mn"
COLUNA_LOCALIDADE = "Localidade"

# Verifica colunas obrigatórias
for col in [COLUNA_FURO, COLUNA_DEPTH_FROM, COLUNA_DEPTH_TO, COLUNA_MN, COLUNA_LOCALIDADE]:
    if col not in df.columns:
        raise ValueError(f"Coluna obrigatória ausente: {col}")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Interativo - Análise de Manganês"

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

app.layout = html.Div([
    html.H1("Dashboard Interativo - Análise de Manganês", style={"textAlign": "center"}),
    dcc.Tabs([
        dcc.Tab(label="Visualização 3D", children=[
            html.Label("Filtrar por Teor de Mn mínimo (%)"),
            dcc.Slider(0, 50, step=1, value=0, marks={i: f"{i}%" for i in range(0, 51, 10)}, id="mn-slider"),
            dcc.Dropdown(
                options=[{"label": furo, "value": furo} for furo in sorted(df[COLUNA_FURO].unique())],
                id="furo-dropdown",
                placeholder="Selecionar furo para análise detalhada",
                multi=False
            ),
            html.Div(id="descricao-furo"),
            dcc.Graph(id="grafico-3d")
        ]),
        dcc.Tab(label="Gráfico de Barras por Furo", children=[
            dcc.Graph(id="grafico-barras", figure={})
        ]),
        dcc.Tab(label="Gráfico de Pizza por Localidade", children=[
            dcc.Graph(id="grafico-pizza", figure={})
        ])
    ])
])

@app.callback(
    Output("grafico-3d", "figure"),
    Output("descricao-furo", "children"),
    Input("mn-slider", "value"),
    Input("furo-dropdown", "value")
)
def atualizar_grafico(mn_min, furo_selecionado):
    try:
        dff = df[df[COLUNA_MN] >= mn_min]
        if furo_selecionado:
            dff = dff[dff[COLUNA_FURO] == furo_selecionado]

        if dff.empty:
            return go.Figure(), html.P("Nenhum dado para exibir com esse filtro.", style={"color": "red"})

        cores = dff[COLUNA_MN].apply(color_scale)

        fig = go.Figure(data=[go.Scatter3d(
            x=dff[COLUNA_FURO],
            y=dff[COLUNA_DEPTH_FROM],
            z=dff[COLUNA_DEPTH_TO],
            mode="markers",
            marker=dict(size=5, color=cores),
            text=[f"Mn: {v:.2f}%" for v in dff[COLUNA_MN]],
            hoverinfo="text"
        )])
        fig.update_layout(scene=dict(
            xaxis_title="Furo",
            yaxis_title="Profundidade Inicial",
            zaxis_title="Profundidade Final"
        ))

        if furo_selecionado:
            amostras = df[df[COLUNA_FURO] == furo_selecionado]
            n_amostras = len(amostras)
            max_mn = amostras[COLUNA_MN].max()
            loc = amostras[COLUNA_LOCALIDADE].iloc[0]
            frase = f"Análise do furo **{furo_selecionado}** localizado em **{loc}**, contendo **{n_amostras} amostras** e total de **{n_amostras * 2} disparos**. Maior teor de Mn registrado: **{max_mn:.2f}%**."
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
    barras = dff.groupby(COLUNA_FURO)[COLUNA_MN].mean().sort_values(ascending=False)
    return go.Figure(data=[go.Bar(x=barras.index, y=barras.values, marker_color="teal")])

@app.callback(
    Output("grafico-pizza", "figure"),
    Input("mn-slider", "value")
)
def grafico_pizza(mn_min):
    dff = df[df[COLUNA_MN] >= mn_min]
    localidade_max = dff.groupby(COLUNA_LOCALIDADE)[COLUNA_MN].max()
    localidade_contagem = df[COLUNA_LOCALIDADE].value_counts()

    labels = []
    values = []
    texto = []
    for loc in localidade_max.index:
        labels.append(loc)
        values.append(localidade_max[loc])
        amostras = localidade_contagem[loc]
        texto.append(f"Maior Mn: {localidade_max[loc]:.2f}%\\nDisparos: {amostras * 2}")

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, text=texto, hoverinfo="label+text+percent")])
    fig.update_layout(title="Distribuição do Maior Teor de Manganês por Localidade")
    return fig

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
