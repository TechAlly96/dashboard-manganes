# dashboard_manganes_3d.py

import pandas as pd
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
from pathlib import Path

# Caminho absoluto para planilha
file_path = Path(__file__).parent / "data" / "ASSAY.xlsx"
df = pd.read_excel(file_path)

# Corrigir nomes das colunas
df.columns = df.columns.str.strip().str.upper()
df.rename(columns={"DEPTH_FROM": "DEPTH_FROM", "DEPTH_TO": "DEPTH_TO", "FURO": "FURO", "MN": "MN"}, inplace=True)
df["DEPTH_FROM"] = pd.to_numeric(df["DEPTH_FROM"], errors="coerce")
df["DEPTH_TO"] = pd.to_numeric(df["DEPTH_TO"], errors="coerce")
df["z"] = (df["DEPTH_FROM"] + df["DEPTH_TO"]) / 2
df.dropna(subset=["z", "MN", "FURO"], inplace=True)

idiomas = {
    "pt": {
        "titulo": "Dashboard Interativo - Análise de Manganês",
        "grafico_3d": "Gráfico 3D (em breve)",
        "grafico_barras": "Gráfico de Barras - Teor por metro",
        "grafico_pizza": "Gráfico de Pizza - Maiores Teores por Localidade",
        "selecione_furo": "Selecione o furo para análise"
    },
    "en": {
        "titulo": "Interactive Dashboard - Manganese Analysis",
        "grafico_3d": "3D Chart (coming soon)",
        "grafico_barras": "Bar Chart - Mn by Depth",
        "grafico_pizza": "Pie Chart - Highest Mn by Location",
        "selecione_furo": "Select borehole"
    }
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Manganês"

app.layout = dbc.Container([
    html.Br(),
    dcc.Dropdown(
        id="idioma-seletor",
        options=[
            {"label": "Português", "value": "pt"},
            {"label": "English", "value": "en"},
        ],
        value="pt",
        style={"width": "200px"}
    ),
    html.H1(id="titulo-principal", className="text-center mt-3"),
    dcc.Tabs(id="abas-graficos", value="barras", children=[
        dcc.Tab(label="Gráfico de Barras", value="barras"),
        dcc.Tab(label="Gráfico de Pizza", value="pizza"),
        dcc.Tab(label="Gráfico 3D", value="3d"),
    ]),
    html.Div([
        dcc.Dropdown(
            id="furo-dropdown",
            options=[{"label": f, "value": f} for f in sorted(df["FURO"].unique())],
            placeholder="Selecionar furo",
            style={"width": "300px", "margin": "10px auto"}
        ),
        html.Div(id="descricao-furo", className="text-center mb-3"),
        dcc.Graph(id="grafico-principal")
    ])
], fluid=True)

@app.callback(
    Output("titulo-principal", "children"),
    Input("idioma-seletor", "value")
)
def atualizar_titulo(lang):
    return idiomas[lang]["titulo"]

@app.callback(
    Output("grafico-principal", "figure"),
    Output("descricao-furo", "children"),
    Input("furo-dropdown", "value"),
    Input("abas-graficos", "value"),
    Input("idioma-seletor", "value")
)
def atualizar_grafico(furo, aba, lang):
    if not furo:
        return go.Figure(), ""

    dff = df[df["FURO"] == furo]

    if dff.empty:
        return go.Figure(), f"Furo {furo} sem dados registrados."

    if aba == "barras":
        profundidades = [f"{int(row['DEPTH_FROM'])}–{int(row['DEPTH_TO'])} m" for _, row in dff.iterrows()]
        cores = dff["MN"].apply(lambda x: (
            "darkblue" if x < 5 else
            "deepskyblue" if x < 10 else
            "green" if x < 15 else
            "yellow" if x < 20 else
            "orange" if x < 30 else
            "red" if x < 40 else
            "darkred"
        ))

        fig = go.Figure(go.Bar(
            x=dff["MN"],
            y=profundidades,
            orientation="h",
            marker=dict(color=cores)
        ))
        fig.update_layout(
            title=idiomas[lang]["grafico_barras"],
            xaxis_title="Mn (%)",
            yaxis_title="Profundidade (m)",
            yaxis_autorange="reversed"
        )

    elif aba == "pizza":
        resumo = df.groupby("LOCAL")["MN"].agg(["mean", "max", "count"]).reset_index()
        fig = go.Figure(go.Pie(
            labels=resumo["LOCAL"],
            values=resumo["max"],
            hovertext=[
                f"Média: {row['mean']:.2f}%<br>Máx: {row['max']:.2f}%<br>N: {row['count']}"
                for _, row in resumo.iterrows()
            ],
            hoverinfo="label+percent+text"
        ))
        fig.update_layout(title=idiomas[lang]["grafico_pizza"])
    else:
        fig = go.Figure()
        fig.add_annotation(text=idiomas[lang]["grafico_3d"], showarrow=False, font_size=20)
        fig.update_layout(height=350)

    frase = (
        f"{idiomas[lang]['selecione_furo']}: {furo} | "
        f"Amostras: {len(dff)} | "
        f"Mn Máx: {dff['MN'].max():.2f}% | "
        f"Mn Méd: {dff['MN'].mean():.2f}% | "
        f"Mn Mín: {dff['MN'].min():.2f}%"
    )

    return fig, frase

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
