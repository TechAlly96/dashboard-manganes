import os
import pandas as pd
import plotly.graph_objs as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

# Caminho absoluto para o arquivo ASSAY.xlsx
file_path = os.path.join(os.path.dirname(__file__), "data", "ASSAY.xlsx")
df = pd.read_excel(file_path)

# Padronização dos nomes das colunas
df.columns = df.columns.str.strip().str.replace(" ", "_").str.upper()

# Conversão de tipos
df["DEPTH_FROM"] = pd.to_numeric(df["DEPTH_FROM"], errors="coerce")
df["DEPTH_TO"] = pd.to_numeric(df["DEPTH_TO"], errors="coerce")
df["Mn"] = pd.to_numeric(df["MN"], errors="coerce")

# Cálculo do centro de profundidade (z)
df["z"] = (df["DEPTH_FROM"] + df["DEPTH_TO"]) / 2

# Lista completa dos furos conhecidos
furos_projeto = df["FURO"].dropna().unique().tolist()
furos_todos = sorted(set(furos_projeto))

# Dicionário de localidades (substitua conforme suas preferências)
localidades_dict = df.set_index("FURO")["LOCAL"].to_dict()

# Mapeamento de cores por teor de manganês
def cor_mapa_calor(mn):
    if pd.isna(mn):
        return "gray"
    elif mn < 5:
        return "#00008B"
    elif mn < 10:
        return "#00CED1"
    elif mn < 15:
        return "green"
    elif mn < 20:
        return "yellow"
    elif mn < 30:
        return "orange"
    elif mn < 40:
        return "red"
    else:
        return "#8B0000"

# Inicialização do app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Análise de Teor de Manganês"

# Layout responsivo com seletor de idioma e abas
app.layout = dbc.Container([
    html.H2("Dashboard Interativo - Análise de Manganês", className="text-center my-3"),

    dcc.Dropdown(
        id="furo-dropdown",
        options=[{"label": furo, "value": furo} for furo in furos_todos],
        placeholder="Selecione o furo para análise",
        className="mb-3"
    ),

    dcc.Tabs(id="tabs", value="barras", children=[
        dcc.Tab(label="Gráfico de Barras (Metro a Metro)", value="barras"),
        dcc.Tab(label="Gráfico de Pizza (Resumo por Localidade)", value="pizza"),
    ]),

    html.Div(id="conteudo-aba", className="my-4"),

    html.Div(id="descricao-furo", className="text-info fs-5", style={"whiteSpace": "pre-line"}),

    html.Hr(),
    html.H5("Legenda do Mapa de Calor", className="mt-4"),
    dbc.Row([
        dbc.Col(html.Div("0–5%"), width=2, style={"background": "#00008B", "color": "white", "textAlign": "center"}),
        dbc.Col(html.Div("5–10%"), width=2, style={"background": "#00CED1", "color": "black", "textAlign": "center"}),
        dbc.Col(html.Div("10–15%"), width=2, style={"background": "green", "color": "white", "textAlign": "center"}),
        dbc.Col(html.Div("15–20%"), width=2, style={"background": "yellow", "color": "black", "textAlign": "center"}),
        dbc.Col(html.Div("20–30%"), width=2, style={"background": "orange", "color": "black", "textAlign": "center"}),
        dbc.Col(html.Div(">40%"), width=2, style={"background": "#8B0000", "color": "white", "textAlign": "center"}),
    ])
], fluid=True)

# Callback de conteúdo da aba
@app.callback(
    Output("conteudo-aba", "children"),
    Input("tabs", "value"),
    Input("furo-dropdown", "value")
)
def atualizar_conteudo(tab, furo):
    if tab == "barras":
        return dcc.Graph(figure=grafico_barras(furo))
    elif tab == "pizza":
        return dcc.Graph(figure=grafico_pizza())
    return ""

# Callback para frase inteligente
@app.callback(
    Output("descricao-furo", "children"),
    Input("furo-dropdown", "value")
)
def atualizar_descricao(furo):
    if furo is None:
        return "Selecione um furo para visualizar a análise detalhada."

    dff = df[df["FURO"] == furo]
    local = localidades_dict.get(furo, "Desconhecida")

    if dff.empty:
        return f"O furo {furo}, localizado em {local}, ainda não possui dados de amostragem registrados no sistema."

    n_amostras = len(dff)
    maior_mn = dff["Mn"].max()
    menor_mn = dff["Mn"].min()
    media_mn = dff["Mn"].mean()

    return (
        f"Furo {furo} — Localidade: {local}\n"
        f"Número de amostras: {n_amostras}\n"
        f"Leituras feitas por amostra: 2 disparos\n"
        f"Maior teor de manganês: {maior_mn:.2f}%\n"
        f"Menor teor de manganês: {menor_mn:.2f}%\n"
        f"Média geral de manganês: {media_mn:.2f}%"
    )

# Função do gráfico de barras por metro
def grafico_barras(furo):
    if furo is None:
        return go.Figure()

    dff = df[df["FURO"] == furo]
    if dff.empty:
        return go.Figure()

    profundidade_texto = dff.apply(lambda x: f"{int(x['DEPTH_FROM'])}-{int(x['DEPTH_TO'])} m", axis=1)
    cores = dff["Mn"].apply(cor_mapa_calor)

    fig = go.Figure(data=[
        go.Bar(
            x=dff["Mn"],
            y=profundidade_texto,
            orientation="h",
            marker_color=cores,
            text=[f"{v:.2f}%" for v in dff["Mn"]],
            hoverinfo="text"
        )
    ])
    fig.update_layout(
        yaxis=dict(autorange="reversed", title="Profundidade"),
        xaxis_title="Teor de Manganês (%)",
        height=500
    )
    return fig

# Função do gráfico de pizza
def grafico_pizza():
    dff = df.copy()
    localidades = dff.groupby("LOCAL").agg(
        max_mn=("Mn", "max"),
        avg_mn=("Mn", "mean"),
        count=("Mn", "count")
    ).reset_index()

    labels = localidades["LOCAL"]
    values = localidades["max_mn"]
    textos = [
        f"{row.LOCAL}\nMáx Mn: {row.max_mn:.2f}%\nMédia: {row.avg_mn:.2f}%\nAmostras: {row['count']}"
        for row in localidades.itertuples()
    ]

    fig = go.Figure(data=[
        go.Pie(labels=labels, values=values, text=textos, hoverinfo="text+percent")
    ])
    fig.update_layout(
        title="Distribuição do Maior Teor de Mn por Localidade",
        height=500
    )
    return fig

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
