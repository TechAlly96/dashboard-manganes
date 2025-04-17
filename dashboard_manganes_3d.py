import pandas as pd
import plotly.graph_objs as go
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import os

# Carregar os dados
df = pd.read_excel("ASSAY.xlsx")

# Normalizar nomes de colunas esperadas
colunas_esperadas = [
    "Localidade", "Furo", "Z (m)", "Mn (%)"
]
df.columns = [col.strip() for col in df.columns]

# Verificar colunas obrigatórias
for coluna in colunas_esperadas:
    if coluna not in df.columns:
        raise ValueError(f"Coluna obrigatória '{coluna}' não encontrada na planilha ASSAY.xlsx")

# Função para obter a cor com base no teor de manganês
def obter_cor(teor):
    if teor <= 5:
        return 'darkblue'
    elif teor <= 10:
        return 'deepskyblue'
    elif teor <= 15:
        return 'green'
    elif teor <= 20:
        return 'yellow'
    elif teor <= 30:
        return 'orange'
    elif teor <= 40:
        return 'red'
    else:
        return 'darkred'

# Cores para cada ponto
cores = df["Mn (%)"].apply(obter_cor)

# Inicializa app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Layout
app.layout = dbc.Container([
    html.H1("Dashboard 3D - Teor de Manganês por Furo", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Selecione um furo:"),
            dcc.Dropdown(
                id='dropdown-furo',
                options=[{'label': f, 'value': f} for f in sorted(df['Furo'].unique())],
                value=df['Furo'].unique()[0]
            )
        ], width=6),
    ]),

    html.Div(id='descricao-furo', className="my-3"),

    dcc.Graph(id='grafico-3d'),

    html.Hr(),
    html.H3("Gráfico de Pizza por Localidade"),
    dcc.Graph(id='grafico-pizza')
])

# Callbacks
@app.callback(
    Output('grafico-3d', 'figure'),
    Output('descricao-furo', 'children'),
    Output('grafico-pizza', 'figure'),
    Input('dropdown-furo', 'value')
)
def atualizar_dashboard(furo):
    # Filtrar dados por furo selecionado
    df_furo = df[df['Furo'] == furo]
    maior_teor = df_furo['Mn (%)'].max()
    amostras = len(df_furo)

    descricao = (
        f"Análise do furo **{furo}** com **{amostras} amostras** (total de {amostras*2} disparos): "
        f"O maior teor de manganês foi de {maior_teor:.2f}%."
    )

    fig = go.Figure(data=[
        go.Scatter3d(
            x=df_furo['Furo'],
            y=df_furo['Z (m)'],
            z=df_furo['Mn (%)'],
            mode='markers',
            marker=dict(
                size=5,
                color=df_furo['Mn (%)'].apply(obter_cor),
                opacity=0.8
            ),
            text=[f"Mn: {mn:.2f}%" for mn in df_furo['Mn (%)']],
        )
    ])
    fig.update_layout(scene=dict(
        xaxis_title='Furo',
        yaxis_title='Profundidade (m)',
        zaxis_title='Mn (%)'
    ))

    # Pizza por localidade
    df_pizza = df.groupby('Localidade').agg({
        'Mn (%)': 'max',
        'Furo': 'count'
    }).rename(columns={
        'Mn (%)': 'Maior Teor (%)',
        'Furo': 'Disparos'
    })

    pizza_fig = go.Figure(
        data=[go.Pie(
            labels=[f"{loc} ({row['Disparos']*2} disparos)" for loc, row in df_pizza.iterrows()],
            values=df_pizza['Maior Teor (%)'],
            hole=0.4,
            textinfo='label+percent',
            hoverinfo='label+value'
        )]
    )
    pizza_fig.update_layout(title_text="Distribuição do Maior Teor por Localidade")

    return fig, dcc.Markdown(descricao), pizza_fig

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
