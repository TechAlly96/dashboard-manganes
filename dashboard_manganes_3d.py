
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Inicializa o app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Carregamento e pré-processamento da planilha
try:
    df = pd.read_excel("data/ASSAY.xlsx")
    df.columns = df.columns.str.upper().str.strip()
    df = df.rename(columns={
        "Mn": "Mn",
        "X": "X", "Y": "Y", "Z": "Z", "AMOSTRA": "AMOSTRA",
        "FURO": "FURO", "LOCALIDADE": "LOCALIDADE"
    })
    df = df[df["Mn"].notna()]
    df["MN_%"] = (df["Mn"] / 10000).round(2)
except Exception as e:
    print("Erro ao carregar os dados:", e)
    df = pd.DataFrame(columns=["LOCALIDADE", "FURO", "X", "Y", "Z", "Mn", "MN_%"])

# Layout
app.layout = dbc.Container([
    html.H2("Dashboard Interativo - Análise de Manganês", className="text-center my-3"),
    dcc.Tabs([
        dcc.Tab(label='Visualização 3D', children=[
            dcc.RangeSlider(id='range-slider', min=0, max=50, step=0.5, value=[0, 50],
                marks={i: f"{i}%" for i in range(0, 51, 10)}),
            dcc.Graph(id='graph-3d'),
            html.Div(id='resumo-analitico', className="mt-4")
        ]),
        dcc.Tab(label='Gráfico de Barras por Furo', children=[
            dcc.Graph(id='graph-bar')
        ])
    ])
], fluid=True)

# Callback para o gráfico 3D e resumo
@app.callback(
    Output("graph-3d", "figure"),
    Output("resumo-analitico", "children"),
    Input("range-slider", "value")
)
def update_graph(range_mn):
    if df.empty:
        return go.Figure(), "Dados não disponíveis."

    filtered = df[(df["MN_%"] >= range_mn[0]) & (df["MN_%"] <= range_mn[1])]
    fig = px.scatter_3d(filtered, x="X", y="Y", z="Z",
                        color="MN_%", size="MN_%",
                        hover_name="AMOSTRA",
                        color_continuous_scale="Hot",
                        title="Distribuição 3D das Amostras")
    fig.update_traces(marker=dict(line=dict(width=0)))
    fig.update_layout(height=700, margin=dict(l=0, r=0, b=0, t=40))

    mensagens = []
    for loc in filtered["LOCALIDADE"].unique():
        sub = filtered[filtered["LOCALIDADE"] == loc]
        media = sub["MN_%"].mean()
        maior = sub.loc[sub["MN_%"].idxmax()]
        mensagens.append(html.P(f"Na localidade {loc}, no furo {maior['FURO']} encontramos manganês com teor de {maior['MN_%']}% aferido pelo aparelho X-MET8000 por fluorescência."))
        mensagens.append(html.P(f"A média de {len(sub)} amostras em {loc} é de {media:.2f}%."))

    return fig, mensagens

# Callback para gráfico de barras
@app.callback(
    Output("graph-bar", "figure"),
    Input("range-slider", "value")
)
def bar_chart(range_mn):
    if df.empty:
        return go.Figure()

    filtro = df[(df["MN_%"] >= range_mn[0]) & (df["MN_%"] <= range_mn[1])]
    agrupado = filtro.groupby(["LOCALIDADE", "FURO"]).agg(
        MEDIA_MN=("MN_%", "mean"),
        MAX_MN=("MN_%", "max"),
        AMOSTRAS=("MN_%", "count")
    ).reset_index()

    fig = px.bar(agrupado, x="FURO", y="MEDIA_MN", color="LOCALIDADE",
                 hover_data=["MAX_MN", "AMOSTRAS"],
                 title="Média de Manganês por Furo e Localidade")
    fig.update_layout(barmode="group", height=600)
    return fig

# Execução
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
