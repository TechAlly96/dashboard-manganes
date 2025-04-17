import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

# Caminho para o arquivo Excel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, 'data', 'ASSAY.xlsx')

# Inicializa o app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Dashboard Interativo - Análise de Manganês'

# Leitura dos dados
try:
    df = pd.read_excel(FILE_PATH)

    # Corrige separador decimal e converte para float
    df['DEPTH_FROM'] = df['DEPTH_FROM'].astype(str).str.replace(',', '.').astype(float)
    df['DEPTH_TO'] = df['DEPTH_TO'].astype(str).str.replace(',', '.').astype(float)
    df['Mn'] = pd.to_numeric(df['Mn'], errors='coerce')
    df = df.dropna(subset=['Mn', 'DEPTH_FROM', 'DEPTH_TO'])

    erro_carregamento = None
except Exception as e:
    df = pd.DataFrame()
    erro_carregamento = str(e)

# Função para definir cores personalizadas conforme faixa de Mn
def faixa_cor_mn(valor):
    if valor <= 5:
        return 'darkblue'
    elif valor <= 10:
        return 'deepskyblue'
    elif valor <= 15:
        return 'green'
    elif valor <= 20:
        return 'yellow'
    elif valor <= 30:
        return 'orange'
    elif valor <= 40:
        return 'red'
    else:
        return 'darkred'

df['cor'] = df['Mn'].apply(faixa_cor_mn)

# Layout
app.layout = dbc.Container([
    html.H2("Dashboard Interativo - Análise de Manganês", style={'textAlign': 'center'}),
    dcc.Slider(
        id='slider-teor',
        min=0,
        max=50,
        step=1,
        value=0,
        marks={i: f"{i}%" for i in range(0, 51, 5)},
        tooltip={"placement": "bottom", "always_visible": True}
    ),
    html.Br(),
    dcc.Tabs(id='tabs', value='tab-3d', children=[
        dcc.Tab(label='Visualização 3D', value='tab-3d'),
        dcc.Tab(label='Teor Médio por Furo', value='tab-barras')
    ]),
    html.Div(id='graficos'),
    html.Div(id='mensagem-erro', style={'color': 'red', 'textAlign': 'center', 'marginTop': '20px'})
], fluid=True)

# Callback dos gráficos
@app.callback(
    Output('graficos', 'children'),
    Output('mensagem-erro', 'children'),
    Input('tabs', 'value'),
    Input('slider-teor', 'value')
)
def atualizar_grafico(tab, teor_minimo):
    if df.empty:
        return [], f"Erro ao carregar os dados: {erro_carregamento}"

    df_filtrado = df[df['Mn'] >= teor_minimo]
    if df_filtrado.empty:
        return [], "Dados não disponíveis para o filtro selecionado."

    if tab == 'tab-3d':
        fig = go.Figure(data=[
            go.Scatter3d(
                x=df_filtrado['Furo'],
                y=df_filtrado['DEPTH_FROM'],
                z=df_filtrado['Mn'],
                mode='markers',
                marker=dict(
                    size=6,
                    color=df_filtrado['Mn'],
                    colorscale=[
                        [0.0, 'darkblue'],
                        [0.1, 'deepskyblue'],
                        [0.3, 'green'],
                        [0.4, 'yellow'],
                        [0.6, 'orange'],
                        [0.8, 'red'],
                        [1.0, 'darkred']
                    ],
                    colorbar=dict(title='Mn (%)')
                ),
                text=df_filtrado['LOCAL']
            )
        ])
        fig.update_layout(
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(
                xaxis_title="Furo",
                yaxis_title="Profundidade (m)",
                zaxis_title="Mn (%)",
                yaxis=dict(autorange="reversed")
            )
        )
    else:
        media = df_filtrado.groupby('Furo')['Mn'].mean().reset_index()
        fig = px.bar(media, x='Furo', y='Mn', color='Mn',
                     color_continuous_scale=[
                        'darkblue', 'deepskyblue', 'green', 'yellow', 'orange', 'red', 'darkred'
                     ],
                     title='Teor Médio de Mn por Furo')

    return [dcc.Graph(figure=fig)], ""

# Executar localmente ou no Render
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
