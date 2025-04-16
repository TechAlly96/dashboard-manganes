import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

# Inicializar o app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Carregar a planilha ASSAY.xlsx
try:
    df = pd.read_excel("data/ASSAY.xlsx")
    df = df.rename(columns=lambda x: x.strip().upper())
    df = df.rename(columns={
        'MN': 'MN_%',  # Teor de manganês já em porcentagem
        'AMOSTRA': 'AMOSTRA',
        'X': 'X',
        'Y': 'Y',
        'Z': 'Z',
        'LOCAL': 'LOCAL',
        'FURO': 'FURO'
    })
    df.dropna(subset=['MN_%'], inplace=True)
except Exception as e:
    print("Erro ao carregar os dados:", e)
    df = pd.DataFrame()

# Layout
app.layout = dbc.Container([
    html.H2("Dashboard 3D - Análise de Manganês", className="text-center my-4"),
    dbc.Row([
        dbc.Col([
            html.Label("Tipo de visualização:"),
            dcc.RadioItems(
                id='tipo-grafico',
                options=[
                    {'label': 'Gráfico 3D', 'value': '3d'},
                    {'label': 'Gráfico de Barras', 'value': 'barras'}
                ],
                value='3d',
                inline=True
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='grafico-manganes', style={"height": "700px"})
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(id='resumo-local', className='mt-4')
        ])
    ])
], fluid=True)

# Callback
@app.callback(
    [Output('grafico-manganes', 'figure'),
     Output('resumo-local', 'children')],
    [Input('tipo-grafico', 'value')]
)
def atualizar_visualizacao(tipo):
    if df.empty:
        return go.Figure(), "Erro ao carregar dados."

    if tipo == '3d':
        fig = px.scatter_3d(
            df, x='X', y='Y', z='Z',
            color='MN_%',
            size='MN_%',
            hover_data=['AMOSTRA', 'FURO', 'LOCAL', 'MN_%'],
            color_continuous_scale='Hot',
            title="Distribuição 3D das Amostras de Manganês"
        )
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=40))
    else:
        fig = px.bar(
            df,
            x='FURO',
            y='MN_%',
            color='LOCAL',
            hover_data=['AMOSTRA', 'MN_%'],
            title="Comparativo por Furo - Teor de Manganês (%)"
        )
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=40))

    frases = []
    for localidade in df['LOCAL'].unique():
        sub_df = df[df['LOCAL'] == localidade]
        for furo in sub_df['FURO'].unique():
            sub_furo = sub_df[sub_df['FURO'] == furo]
            maior = sub_furo['MN_%'].max()
            media = sub_furo['MN_%'].mean()
            frases.append(
                html.P(f"Na localidade {localidade}, no furo {furo}, encontramos manganês com teor máximo de {maior:.2f}%. "
                       f"A média das {len(sub_furo)} amostras é de {media:.2f}% de manganês.")
            )

    return fig, frases

# Run
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
