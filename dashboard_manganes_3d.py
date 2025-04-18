import os
import pandas as pd
import plotly.graph_objs as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback

# === CONFIGURACOES INICIAIS ===
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Dashboard Manganês 3D"

# === DADOS ===
caminho_excel = os.path.join("data", "ASSAY.xlsx")
df = pd.read_excel(caminho_excel)

# Padroniza nomes de colunas
df.columns = df.columns.str.strip().str.replace(" ", "_").str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("utf-8")

COL_FURO = "Furo"
COL_FROM = "DEPTH_FROM"
COL_TO = "DEPTH_TO"
COL_MN = "Mn"
COL_LOCAL = "LOCAL"

# Furos conhecidos (mesmo sem dados ainda)
furos_conhecidos = [
    "FCC-1-1", "FCC-2-2", "FCC-3-3", "FCC-4-4", "FCC-5-5", "FCC-6-6", "FCC-7-7", "FCC-8-8", "FCC-9-9", "FCC-10-10",
    "FCN-1-25", "FCN-2-26", "FCN-3-27", "FCN-4-28", "FCN-5-29", "FCN-6-30",
    "FBC-1-31", "FBC-2-32", "FBC-3-33", "FBC-4-34", "FBC-5-35", "FBC-6-36",
    "FCZ-1-11", "FCZ-2-2", "FCZ-3-13", "FCZ-4-14", "FCZ-5-15", "FCZ-6-16",
    "FMB-1-37", "FMB-2-38", "FMB-3-39", "FMB-4-40", "FMB-5-41", "FMB-6-42", "FMB-7-43", "FMB-8-44", "FMB-9-45", "FMB-10-46", "FMB-11-47", "FMB-12-48", "FMB-13-49", "FMB-14-50", "FMB-15-51",
    "FBU-1-17", "FBU-2-18", "FBU-3-19", "FBU-4-20", "FBU-5-21", "FBU-6-22", "FBU-7-23", "FBU-8-24",
    "CN1-1-56", "CN1-2-57", "CN1-3-58", "CN1-4-59", "CN1-5-60", "CN1-6-61", "CN1-7-62", "CN1-8-63",
    "FNA-1-54", "FNA-2-55"
]

# === FUNCOES ===
def mapa_calor(mn):
    if pd.isna(mn):
        return "lightgrey"
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

# === LAYOUT ===
app.layout = html.Div([
    html.H2("Dashboard Interativo - Análise de Manganês", className="text-center my-4"),

    dcc.Slider(id="mn-slider", min=0, max=50, step=1, value=0,
               marks={i: f"{i}%" for i in range(0, 51, 10)},
               tooltip={"always_visible": False, "placement": "bottom"}),

    dcc.Dropdown(
        id="furo-dropdown",
        options=[{"label": furo, "value": furo} for furo in sorted(furos_conhecidos)],
        placeholder="Selecione um furo para análise",
        className="my-3"
    ),

    html.Div(id="descricao-furo", className="mb-4"),

    html.Div([
        dcc.Graph(id="grafico-3d"),
        dcc.Graph(id="grafico-barras"),
        dcc.Graph(id="grafico-pizza")
    ])
], className="container")

# === CALLBACKS ===
@callback(
    Output("grafico-3d", "figure"),
    Output("descricao-furo", "children"),
    Input("mn-slider", "value"),
    Input("furo-dropdown", "value")
)
def atualizar_grafico_3d(mn_min, furo):
    dff = df[df[COL_MN] >= mn_min] if mn_min else df.copy()
    fig = go.Figure()
    descricao = ""

    if furo:
        amostras = df[df[COL_FURO] == furo]
        if amostras.empty:
            descricao = f"O furo **{furo}** ainda não possui dados de amostragem registrados no sistema."
        else:
            for _, linha in amostras.iterrows():
                fig.add_trace(go.Scatter3d(
                    x=[furo, furo],
                    y=[linha[COL_FROM], linha[COL_TO]],
                    z=[0, 0],
                    mode='lines',
                    line=dict(color=mapa_calor(linha[COL_MN]), width=6),
                    hovertext=f"Mn: {linha[COL_MN]}%"
                ))
            descricao = (
                f"Análise do furo **{furo}** localizado em **{amostras[COL_LOCAL].iloc[0]}**, onde coletamos **{len(amostras)}** amostras.\n"
                f"Maior teor de Mn = {amostras[COL_MN].max():.2f}%, Menor = {amostras[COL_MN].min():.2f}%\n"
                f"Média = {amostras[COL_MN].mean():.2f}%"
            )
    else:
        descricao = "Selecione um furo para ver os detalhes em 3D."

    fig.update_layout(height=500, margin=dict(l=0, r=0, b=0, t=0),
                      scene=dict(xaxis_title="Furo", yaxis_title="Profundidade (m)", zaxis_title=""))
    return fig, dcc.Markdown(descricao)

@callback(
    Output("grafico-barras", "figure"),
    Input("mn-slider", "value")
)
def atualizar_barras(mn_min):
    dff = df[df[COL_MN] >= mn_min] if mn_min else df.copy()
    barras = dff.groupby(COL_FURO)[COL_MN].mean()
    barras = barras.reindex(furos_conhecidos).fillna(0)

    return go.Figure(data=[go.Bar(
        x=barras.values,
        y=barras.index,
        orientation='h',
        marker_color='steelblue'
    )], layout_title_text="Teor Médio de Mn por Furo")

@callback(
    Output("grafico-pizza", "figure"),
    Input("mn-slider", "value")
)
def atualizar_pizza(mn_min):
    dff = df[df[COL_MN] >= mn_min] if mn_min else df.copy()
    dados = dff.groupby(COL_LOCAL).agg(
        Maior_Mn=(COL_MN, "max"),
        Media_Mn=(COL_MN, "mean"),
        Amostras=(COL_MN, "count")
    )
    dados["Texto"] = dados.apply(lambda x: f"Mn Max: {x.Maior_Mn:.2f}%, Mn Média: {x.Media_Mn:.2f}%, Amostras: {x.Amostras}", axis=1)

    fig = go.Figure(data=[go.Pie(
        labels=dados.index,
        values=dados["Maior_Mn"],
        text=dados["Texto"],
        hoverinfo="label+text+percent"
    )])
    fig.update_layout(title="Resumo por Localidade (Maior teor de Mn)")
    return fig

# === RODAR APLICACAO ===
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
