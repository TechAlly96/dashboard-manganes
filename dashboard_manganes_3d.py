import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import os

# Caminho absoluto para o arquivo ASSAY.xlsx dentro da pasta 'data'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, 'data', 'ASSAY.xlsx')

# Inicialização do app
app = dash.Dash(__name__)
app.title = 'Dashboard Interativo - Análise de Manganês'

# Tentativa de leitura dos dados
try:
    df = pd.read_excel(FILE_PATH)

    # Validação das colunas esperadas
    colunas_necessarias = ['Mn', 'DEPTH_TO', 'HOLE_ID']
    for col in colunas_necessarias:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente: {col}")

    # Dados estatísticos
    total_amostras = len(df)
    teor_medio = df['Mn'].mean()
    maior_teor = df['Mn'].max()
    menor_teor = df['Mn'].min()
    unique_furos = df['HOLE_ID'].unique()

except Exception as e:
    df = pd.DataFrame()
    erro_carregamento = str(e)
else:
    erro_carregamento = None

# Layout do dashboard
app.layout = html.Div([
    html.H1("Dashboard Interativo - Análise de Manganês", style={'textAlign': 'center'}),

    html.Div([
        dcc.Tabs(id='tabs', value='tab-3d', children=[
            dcc.Tab(label='Visualização 3D', value='tab-3d'),
            dcc.Tab(label='Gráfico de Barras por Furo', value='tab-barras')
        ])
    ]),

    html.Div([
        dcc.Slider(
            id='slider-teor',
            min=0,
            max=50,
            step=1,
            value=0,
            marks={i: f"{i}%" for i in range(0, 51, 10)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={'margin': '20px'}),

    html.Div(id='graficos'),

    html.Div(id='mensagem-erro', style={'color': 'red', 'textAlign': 'center', 'marginTop': '20px'})
])

# Callback principal
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
        return [], "Dados não disponíveis."

    if tab == 'tab-3d':
        fig = px.scatter_3d(
            df_filtrado,
            x='HOLE_ID',
            y='DEPTH_TO',
            z='Mn',
            color='Mn',
            color_continuous_scale='YlOrRd',
            title='Visualização 3D - Teor de Manganês'
        )
    else:
        media_por_furo = df_filtrado.groupby('HOLE_ID')['Mn'].mean().reset_index()
        fig = px.bar(
            media_por_furo,
            x='HOLE_ID',
            y='Mn',
            title='Teor Médio por Furo',
            color='Mn',
            color_continuous_scale='YlGnBu'
        )

    return [dcc.Graph(figure=fig)], ""

# Execução do servidor local
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

