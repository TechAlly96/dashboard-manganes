import os
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

# Caminho absoluto para o arquivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "data", "ASSAY.xlsx")

# Leitura e padronização
df = pd.read_excel(FILE_PATH)
df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")

# Renomear colunas
df = df.rename(columns={
    "DEPTH_FROM": "DEPTH_FROM",
    "DEPTH_TO": "DEPTH_TO",
    "MN": "Mn",
    "FURO": "Furo",
    "LOCAL": "Localidade"
})

# Converte DEPTH_FROM e DEPTH_TO para numérico (caso estejam como texto)
df["DEPTH_FROM"] = pd.to_numeric(df["DEPTH_FROM"], errors="coerce")
df["DEPTH_TO"] = pd.to_numeric(df["DEPTH_TO"], errors="coerce")

# Remove linhas com valores ausentes nas colunas DEPTH
df = df.dropna(subset=["DEPTH_FROM", "DEPTH_TO"])

# Cria coluna de profundidade média (z)
df["z"] = (df["DEPTH_FROM"] + df["DEPTH_TO"]) / 2

# Verifica colunas obrigatórias
for col in ["Furo", "z", "Mn"]:
    if col not in df.columns:
        raise ValueError("Planilha deve conter as colunas 'Furo', 'z' (profundidade) e 'Mn'.")

# Mapa de calor
def color_mn(mn):
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

# App Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Manganês"

app.layout = html.Div([
    html.H1("Dashboard de Manganês", className="text-center my-4"),
    
    html.Div([
        html.Label("Selecione um furo:", className="fw-bold"),
        dcc.Dropdown(
            options=[{"label": f, "value": f} for f in sorted(df["Furo"].unique())],
            id="furo-dropdown",
            placeholder="Ex: FCC-1-1"
        )
    ], className="mb-4"),

    html.Div([
        dcc.Tabs(id="tabs", value='grafico_barras', children=[
            dcc.Tab(label="Gráfico de Barras", value='grafico_barras'),
            dcc.Tab(label="Gráfico 3D", value='grafico_3d'),
            dcc.Tab(label="Gráfico de Pizza", value='grafico_pizza'),
        ]),
        html.Div(id="conteudo-grafico", className="my-4"),
        html.Div(id="frase-inteligente", className="mt-4")
    ])
], className="container")

@app.callback(
    Output("conteudo-grafico", "children"),
    Output("frase-inteligente", "children"),
    Input("furo-dropdown", "value"),
    Input("tabs", "value")
)
def atualizar_grafico(furo, aba_selecionada):
    if furo is None:
        return html.P("Selecione um furo para visualizar os dados."), ""

    dff = df[df["Furo"] == furo]

    if dff.empty:
        return html.P("O furo selecionado ainda não possui dados de amostragem registrados no sistema."), ""

    if aba_selecionada == "grafico_barras":
        profundidades = [f"{int(a)}–{int(b)} m" for a, b in zip(dff["DEPTH_FROM"], dff["DEPTH_TO"])]
        teores = dff["Mn"]
        cores = teores.apply(color_mn)

        fig = go.Figure(go.Bar(
            y=profundidades,
            x=teores,
            orientation='h',
            marker_color=cores,
            text=[f"{v:.2f}%" for v in teores],
            textposition="outside"
        ))

        fig.update_layout(
            title=f"Teor de Mn por metro no furo {furo}",
            xaxis_title="Teor de Mn (%)",
            yaxis_title="Profundidade (do topo ao fundo)",
            yaxis=dict(autorange="reversed")
        )
        grafico = dcc.Graph(figure=fig)

    elif aba_selecionada == "grafico_3d":
        fig = go.Figure(data=[go.Scatter3d(
            x=dff["Furo"],
            y=dff["z"],
            z=dff["Mn"],
            mode='markers',
            marker=dict(size=5, color=dff["Mn"], colorscale="Jet", colorbar_title="Mn (%)"),
            text=[f"{v:.2f}%" for v in dff["Mn"]]
        )])
        fig.update_layout(scene=dict(
            xaxis_title="Furo",
            yaxis_title="Profundidade Média (z)",
            zaxis_title="Mn (%)"
        ))
        grafico = dcc.Graph(figure=fig)

    else:  # Pizza
        agrupado = df.groupby("Localidade").agg({
            "Mn": ["mean", "max", "count"]
        })
        agrupado.columns = ["Mn_medio", "Mn_maximo", "Amostras"]
        agrupado = agrupado.reset_index()

        fig = go.Figure(data=[go.Pie(
            labels=agrupado["Localidade"],
            values=agrupado["Mn_maximo"],
            hoverinfo='label+value+text',
            text=[f"Média: {m:.2f}%\nAmostras: {n}" for m, n in zip(agrupado["Mn_medio"], agrupado["Amostras"])]
        )])
        fig.update_layout(title="Distribuição do Maior Teor de Mn por Localidade")
        grafico = dcc.Graph(figure=fig)

    mn_max = dff["Mn"].max()
    mn_min = dff["Mn"].min()
    mn_media = dff["Mn"].mean()
    local = dff["Localidade"].iloc[0] if "Localidade" in dff.columns else "N/A"

    frase = (f"Análise do furo **{furo}**, localizado em **{local}**, onde coletamos "
             f"**{len(dff)} amostras** organizadas metro a metro. "
             f"A leitura foi feita com aparelho XRF em múltiplos disparos por amostra. "
             f"Maior teor de Mn registrado: **{mn_max:.2f}%**, menor teor: **{mn_min:.2f}%** "
             f"e a média do teor é de **{mn_media:.2f}%**.")

    return grafico, dcc.Markdown(frase)

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=10000, debug=False)
