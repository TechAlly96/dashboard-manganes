
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import os

# Leitura da planilha ASSAY
df = pd.read_excel("ASSAY.xlsx")

# Normaliza colunas
df.columns = [col.strip().lower() for col in df.columns]
col_furo = next((col for col in df.columns if "furo" in col), None)
col_z = next((col for col in df.columns if col in ["z", "profundidade", "depth", "prof"]), None)
col_mn = next((col for col in df.columns if "mn" in col and "%" in col), None)
col_localidade = next((col for col in df.columns if "localidade" in col), None)

# Remove NaNs nas colunas essenciais
df = df[[col_furo, col_z, col_mn, col_localidade]].dropna()

# Define função de cor personalizada
def mapa_cor(teor):
    if teor <= 5:
        return "#00008B"  # Azul escuro
    elif teor <= 10:
        return "#5F9EA0"  # Azul claro / Verde-azulado
    elif teor <= 15:
        return "#228B22"  # Verde
    elif teor <= 20:
        return "#FFD700"  # Amarelo
    elif teor <= 30:
        return "#FFA500"  # Laranja
    elif teor <= 40:
        return "#FF0000"  # Vermelho
    else:
        return "#8B0000"  # Vermelho escuro / Bordô

df["cor"] = df[col_mn].apply(mapa_cor)

# Dashboard
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.title = "Dashboard Manganês 3D"

app.layout = dbc.Container([
    html.H1("Dashboard 3D - Teor de Manganês", className="my-4 text-center"),

    dcc.Tabs([
        dcc.Tab(label="Visualização 3D", children=[
            dcc.Dropdown(
                id="furo-dropdown",
                options=[{"label": f, "value": f} for f in sorted(df[col_furo].unique())],
                placeholder="Selecione um furo para análise detalhada",
                multi=False
            ),
            dcc.Graph(id="grafico-3d")
        ]),
        dcc.Tab(label="Gráfico de Pizza por Localidade", children=[
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure=px.pie(
                            df.groupby(col_localidade).agg(maior_teor=(col_mn, "max")).reset_index(),
                            names=col_localidade,
                            values="maior_teor",
                            title="Maior Teor de Manganês por Localidade",
                            color_discrete_sequence=px.colors.sequential.RdBu
                        )
                    )
                ], width=6),
                dbc.Col([
                    dcc.Graph(
                        figure=px.bar(
                            df.groupby(col_localidade).agg(amostras=(col_mn, "count")).assign(disparos=lambda x: x["amostras"] * 2).reset_index(),
                            x=col_localidade,
                            y="disparos",
                            title="Total de Disparos Realizados por Localidade",
                            labels={"disparos": "Disparos"},
                            color=col_localidade
                        )
                    )
                ], width=6)
            ])
        ])
    ]),

    html.Div(id="descricao-furo", className="my-3")
])

@app.callback(
    Output("grafico-3d", "figure"),
    Output("descricao-furo", "children"),
    Input("furo-dropdown", "value")
)
def atualizar_grafico(furo):
    if not furo:
        return dash.no_update, ""

    df_filtro = df[df[col_furo] == furo]

    fig = px.scatter_3d(
        df_filtro,
        x=col_furo,
        y=col_z,
        z=col_mn,
        color=col_mn,
        color_continuous_scale=[
            "#00008B", "#5F9EA0", "#228B22", "#FFD700", "#FFA500", "#FF0000", "#8B0000"
        ],
        title=f"Furo: {furo} - Distribuição 3D do Teor de Manganês",
        labels={col_mn: "Mn (%)", col_z: "Profundidade"}
    )

    media = df_filtro[col_mn].mean()
    maximo = df_filtro[col_mn].max()
    minimo = df_filtro[col_mn].min()
    amostras = len(df_filtro)

    frase = (
        f"Análise do furo **{furo}** com **{amostras} amostras** (total de {amostras*2} disparos):
"
        f"- Teor médio de manganês: **{media:.2f}%**
"
        f"- Teor máximo: **{maximo:.2f}%**, mínimo: **{minimo:.2f}%**"
    )

    return fig, dcc.Markdown(frase)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
