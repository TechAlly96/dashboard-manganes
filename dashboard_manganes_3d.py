import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# Carregar os dados
try:
    df = pd.read_excel("ASSAY.xlsx")
    df["Mn"] = df["Mn"].astype(float)
except Exception as e:
    df = pd.DataFrame()
    erro_carregamento = str(e)
else:
    erro_carregamento = None

# Inicializar o app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = html.Div([
    html.H1("Dashboard Interativo - Análise de Manganês"),

    dcc.Tabs(id="tabs", value="tab-3d", children=[
        dcc.Tab(label="Visualização 3D", value="tab-3d"),
        dcc.Tab(label="Gráfico de Barras por Furo", value="tab-bar")
    ]),

    html.Div(id="tabs-content")
])

# Callbacks
@app.callback(
    Output("tabs-content", "children"),
    Input("tabs", "value")
)
def render_content(tab):
    if df.empty:
        return html.P("Dados não disponíveis." + (f" Erro: {erro_carregamento}" if erro_carregamento else ""))

    if tab == "tab-3d":
        fig = px.scatter_3d(df, x="X", y="Y", z="Z", color="Mn",
                            title="Distribuição 3D dos Teores de Manganês",
                            labels={"Mn": "Teor de Mn (%)"})
        return dcc.Graph(figure=fig)
    elif tab == "tab-bar":
        barras = df.groupby("Furo")["Mn"].mean().reset_index()
        fig = px.bar(barras, x="Furo", y="Mn",
                     title="Teor Médio de Manganês por Furo",
                     labels={"Mn": "Teor de Mn (%)"})
        return dcc.Graph(figure=fig)

# Rodar app
if __name__ == "__main__":
    app.run_server(debug=False, port=10000)
