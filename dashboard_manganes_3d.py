# dashboard_manganes_3d.py
# Dashboard Interativo com Abas Separadas
# Por: Marlon Myaggy ✨

import pandas as pd
import plotly.graph_objs as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
from pathlib import Path

# Caminho para o arquivo Excel
file_path = Path("data/ASSAY.xlsx")
if not file_path.exists():
    raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

# Leitura e tratamento dos dados
all_furos = [
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

localidades = {
    "FCC": "Central Central",
    "FCZ": "Centralzinho",
    "FBU": "Bufalo",
    "FCN": "Central Norte",
    "FBC": "Brechinha",
    "FMB": "Morro das Brechas",
    "FNA": "Ninho da Arara",
    "CN1": "CN1"
}

df = pd.read_excel(file_path)
df.columns = df.columns.str.strip().str.replace(' ', '_').str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

# Adiciona coluna de localidade e furo formatado
df['Furo'] = df['Furo'].astype(str).str.strip()
df['Localidade'] = df['Furo'].apply(lambda x: next((nome for sigla, nome in localidades.items() if x.startswith(sigla)), "Desconhecida"))

# Identificadores
COLUNA_FURO = "Furo"
COLUNA_MN = "Mn"
COLUNA_DEPTH_FROM = "DEPTH_FROM"
COLUNA_DEPTH_TO = "DEPTH_TO"
COLUNA_LOCALIDADE = "Localidade"

# Aplicativo
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Dashboard Interativo - Manganês"

def frase_inteligente(furo):
    if furo not in df[COLUNA_FURO].values:
        return f"O furo {furo} ainda não possui dados de amostragem registrados no sistema."
    amostras = df[df[COLUNA_FURO] == furo]
    loc = amostras[COLUNA_LOCALIDADE].iloc[0]
    max_mn = amostras[COLUNA_MN].max()
    min_mn = amostras[COLUNA_MN].min()
    media = amostras[COLUNA_MN].mean()
    qtd = len(amostras)
    return (
        f"Análise do furo {furo}: localizado em {loc}, onde coletamos {qtd} amostras por sondagem, "
        f"armazenadas na caixa de amostra ID:{furo}. A leitura XRF foi feita com 2 disparos por amostra. "
        f"Maior teor de Mn: {max_mn:.2f}%. Menor: {min_mn:.2f}%. Média: {media:.2f}%."
    )

app.layout = html.Div([
    html.H1("Dashboard Interativo - Teores de Manganês por Furo", style={"textAlign": "center"}),

    html.Label("Filtrar por Teor Mínimo de Mn (%)"),
    dcc.Slider(id='mn-slider', min=0, max=50, step=1, value=0,
               marks={i: f"{i}%" for i in range(0, 51, 10)}),

    html.Br(),
    dcc.Dropdown(options=[{"label": furo, "value": furo} for furo in all_furos],
                 id="furo-dropdown", placeholder="Selecione um furo para análise detalhada"),
    html.Br(),
    html.Div(id="descricao-furo"),
    html.Br(),

    dcc.Tabs(id="tabs", value="tab-barras", children=[
        dcc.Tab(label="Gráfico de Barras", value="tab-barras"),
        dcc.Tab(label="Gráfico de Pizza", value="tab-pizza"),
        dcc.Tab(label="Gráfico 3D (em breve)", value="tab-3d"),
    ]),
    html.Div(id="conteudo-tab")
])

@app.callback(
    Output("descricao-furo", "children"),
    Input("furo-dropdown", "value")
)
def atualizar_descricao(furo):
    if not furo:
        return "Selecione um furo para análise detalhada."
    return dcc.Markdown(frase_inteligente(furo))

@app.callback(
    Output("conteudo-tab", "children"),
    Input("tabs", "value"),
    Input("mn-slider", "value")
)
def render_tab(tab, mn_min):
    dff = df[df[COLUNA_MN] >= mn_min]
    if tab == "tab-barras":
        medias = dff.groupby(COLUNA_FURO)[COLUNA_MN].mean().reindex(all_furos)
        fig = go.Figure(data=[go.Bar(x=medias.values, y=medias.index, orientation="h")])
        fig.update_layout(title="Teor Médio de Mn por Furo", xaxis_title="Mn (%)", yaxis_title="Furo")
        return dcc.Graph(figure=fig)

    elif tab == "tab-pizza":
        resumo = dff.groupby(COLUNA_LOCALIDADE)[COLUNA_MN].agg(['max', 'mean', 'count']).sort_values('max', ascending=False)
        labels = resumo.index
        values = resumo['max']
        hover = [f"Mn Máx: {m:.2f}%, Mn Média: {a:.2f}%, Amostras: {c}" for m, a, c in resumo.values]
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, text=hover, hoverinfo="text+percent")])
        fig.update_layout(title="Resumo por Localidade (Maior teor de Mn)")
        return dcc.Graph(figure=fig)

    elif tab == "tab-3d":
        return html.Div("Visualização 3D de hastes será implementada em breve.", style={"textAlign": "center", "color": "gray"})

    return html.Div("Selecione uma aba.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)