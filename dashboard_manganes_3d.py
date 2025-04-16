import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

# Caminho absoluto para o arquivo Excel dentro da pasta 'data'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, 'data', 'ASSAY.xlsx')

# Inicialização do app
app = dash.Dash(__name__)
app.title = 'Dashboard Interativo - Análise de Manganês'

# Tentativa de leitura dos dados
try:
    df = pd.read_excel(FILE_PATH)

    # Verificação de colunas necessárias
    colunas_necessarias = ['Mn', 'Furo', 'Z']
    for col in colunas_necessarias:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente: {col}")

    df['Mn'] = df['Mn'].astype(float)
    erro_carregamento = None

except Exception as e:
    df = pd.DataFrame()
    erro_carregamento = str(e)

# Layout
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
        ),
        html.Div(id='graficos'),
        html.Div(id='mensagem-erro', style={'color': 'red', 'textAlign': 'center', 'marginTop': '20px'})
    ], style={'margin': '20px'})
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
        return [], "Dados não disponíveis para o filtro selecionado."

    if tab == 'tab-3d':
        fig = px.scatter_3d(
            df_filtrado,
            x='Furo',
            y='Mn',
            z='Z',
            color='Mn',
            color_continuous_scale='YlOrRd',
            title='Visualização 3D - Teor de Manganês'
        )
    else:
        media_por_furo = df_filtrado.groupby('Furo')['Mn'].mean().reset_index()
        fig = px.bar(
            media_por_furo,
            x='Furo',
            y='Mn',
            title='Teor Médio por Furo',
            color='Mn',
            color_continuous_scale='YlGnBu'
        )

    return [dcc.Graph(figure=fig)], ""

# Execução
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


