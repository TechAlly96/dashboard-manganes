import os
import pandas as pd
import plotly.graph_objs as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

# Caminho para o arquivo Excel
file_path = os.path.join("data", "ASSAY.xlsx")
df = pd.read_excel(file_path)

# Padronização dos nomes de colunas
df.columns = df.columns.str.strip().str.replace(" ", "_").str.upper()

# Nomes padronizados
COLUNA_LOCALIDADE = "LOCAL"
COLUNA_FURO = "FURO"
COLUNA_DEPTH_FROM = "DEPTH_FROM"
COLUNA_DEPTH_TO = "DEPTH_TO"
COLUNA_MN = "MN"

# Validação de colunas obrigatórias
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
                options=[{"label": str(furo), "value": str(furo)} for furo in sorted(df[COLUNA_FURO].dropna().astype(str).unique())],
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
    dff = df[df[COLUNA_MN] >= mn_min]
    if furo_selecionado:
        dff = dff[dff[COLUNA_FURO].astype(str) == str(furo_selecionado)]

    if dff.empty:
        return go.Figure(), html.P("Nenhum dado para exibir com esse filtro.", style={"color": "red"})

    shapes = []
    for _, row in dff.iterrows():
        color = color_scale(row[COLUNA_MN])
        shapes.append(dict(
            type="line",
            x0=row[COLUNA_FURO], x1=row[COLUNA_FURO],
            y0=row[COLUNA_DEPTH_FROM], y1=row[COLUNA_DEPTH_TO],
            z0=0, z1=0,
            line=dict(color=color, width=10)
        ))

    fig = go.Figure()
    for shape in shapes:
        fig.add_trace(go.Scatter3d(
            x=[shape['x0'], shape['x1']],
            y=[shape['y0'], shape['y1']],
            z=[shape['z0'], shape['z1']],
            mode="lines",
            line=dict(color=shape['line']['color'], width=5)
        ))

    fig.update_layout(scene=dict(
        xaxis_title="Furo",
        yaxis_title="Profundidade Inicial",
        zaxis_title="",
        yaxis=dict(autorange="reversed")
    ))

    if furo_selecionado:
        amostras = df[df[COLUNA_FURO].astype(str) == str(furo_selecionado)]
        n_amostras = len(amostras)
        max_mn = amostras[COLUNA_MN].max()
        min_mn = amostras[COLUNA_MN].min()
        media_mn = amostras[COLUNA_MN].mean()
        loc = amostras[COLUNA_LOCALIDADE].iloc[0]
        frase = (
            f"Análise do furo {furo_selecionado}: localizado em {loc}, onde coletamos {n_amostras} amostras por sondagem, "
            f"sendo uma amostra por metro perfurado organizadas e armazenadas na caixa de amostra ID:{furo_selecionado}. "
            f"A leitura dos elementos presentes em cada amostra com o aparelho XRF foi realizada em {n_amostras * 2} disparos de 15 segundos com raio de fluorescência. "
            f"Maior teor de Mn=Manganês registrado: {max_mn:.2f}%. Menor teor de Manganês registrado foi: {min_mn:.2f}% e a média comparativa é de {media_mn:.2f}%"
        )
        return fig, dcc.Markdown(frase)

    return fig, ""

@app.callback(
    Output("grafico-barras", "figure"),
    Input("mn-slider", "value")
)
def grafico_barras(mn_min):
    dff = df[df[COLUNA_MN] >= mn_min]
    barras = dff.groupby(COLUNA_FURO)[COLUNA_MN].mean().sort_values(ascending=True)
    return go.Figure(data=[go.Bar(
        y=barras.index.astype(str),
        x=barras.values,
        orientation="h",
        marker_color="teal"
    )], layout=go.Layout(title="Média de Mn (%) por Furo", xaxis_title="Mn (%)", yaxis_title="Furo"))

@app.callback(
    Output("grafico-pizza", "figure"),
    Input("mn-slider", "value")
)
def grafico_pizza(mn_min):
    dff = df[df[COLUNA_MN] >= mn_min]
    resumo = dff.groupby(COLUNA_LOCALIDADE).agg({
        COLUNA_MN: ['mean', 'max', 'count']
    })
    resumo.columns = ['Mn_medio', 'Mn_max', 'N_amostras']
    resumo = resumo.reset_index()

    fig = go.Figure(data=[go.Pie(
        labels=resumo[COLUNA_LOCALIDADE],
        values=resumo['Mn_max'],
        hovertext=[
            f"Localidade: {row[COLUNA_LOCALIDADE]}\nMaior Mn: {row['Mn_max']:.2f}%\nMédia Mn: {row['Mn_medio']:.2f}%\nAmostras: {row['N_amostras']}"
            for _, row in resumo.iterrows()
        ],
        hoverinfo="label+text+percent"
    )])
    fig.update_layout(title="Distribuição do Maior Teor de Mn por Localidade")
    return fig

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
