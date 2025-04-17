import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc

# Caminho da planilha
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, 'data', 'ASSAY.xlsx')

# Inicializa o app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Dashboard Interativo - Análise de Manganês'

# Leitura dos dados
df = pd.read_excel(FILE_PATH)

# Ajuste de tipos
df['Mn'] = df['Mn'].astype(float)

# Layout do dashboard
app.layout = dbc.Container([
    html.H1("Dashboard Interativo - Análise de Manganês", style={'textAlign': 'center'}),
    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.Label("Selecionar localidade:"),
            dcc.Dropdown(
                id='dropdown-local',
                options=[{'label': loc, 'value': loc} for loc in sorted(df['LOCAL'].unique())],
                value=sorted(df['LOCAL'].unique())[0],
                placeholder="Selecione a localidade"
            ),
            html.Br(),

            html.Label("Selecionar furo:"),
            dcc.Dropdown(id='dropdown-furo', placeholder="Selecione o furo"),

            html.Br(),
            dcc.Slider(
                id='slider-teor',
                min=0,
                max=50,
                step=1,
                value=0,
                marks={i: f"{i}%" for i in range(0, 51, 10)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
        ], width=4),

        dbc.Col([
            dcc.Tabs(id='tabs', value='tab-3d', children=[
                dcc.Tab(label='Visualização 3D', value='tab-3d'),
                dcc.Tab(label='Gráfico de Barras por Furo', value='tab-barras')
            ]),
            html.Div(id='graficos'),
            html.Div(id='frase-inteligente', style={'marginTop': '20px', 'fontWeight': 'bold'})
        ], width=8)
    ])
], fluid=True)

# Callback para atualizar dropdown de furos
@app.callback(
    Output('dropdown-furo', 'options'),
    Input('dropdown-local', 'value')
)
def atualizar_furos(local):
    opcoes = df[df['LOCAL'] == local]['Furo'].unique()
    return [{'label': f, 'value': f} for f in sorted(opcoes)]

# Callback principal para atualizar gráficos e frases
@app.callback(
    [Output('graficos', 'children'),
     Output('frase-inteligente', 'children')],
    [Input('tabs', 'value'),
     Input('slider-teor', 'value'),
     Input('dropdown-local', 'value'),
     Input('dropdown-furo', 'value')]
)
def atualizar_dashboard(tab, teor_minimo, local, furo):
    df_filtrado = df[(df['Mn'] >= teor_minimo) & (df['LOCAL'] == local)]

    if furo:
        df_filtrado = df_filtrado[df_filtrado['Furo'] == furo]

    if df_filtrado.empty:
        return [], "Nenhum dado disponível para os filtros selecionados."

    # Definir escala de cor manual
    def cor_personalizada(valor):
        if valor < 5: return "darkblue"
        elif valor < 10: return "deepskyblue"
        elif valor < 15: return "green"
        elif valor < 20: return "yellow"
        elif valor < 30: return "orange"
        elif valor < 40: return "red"
        else: return "darkred"

    df_filtrado['cor'] = df_filtrado['Mn'].apply(cor_personalizada)

    if tab == 'tab-3d':
        fig = px.scatter_3d(
            df_filtrado,
            x='Furo', y='Mn', z='DEPTH_FROM',
            color='Mn',
            color_continuous_scale=["darkblue", "deepskyblue", "green", "yellow", "orange", "red", "darkred"],
            title=f"Visualização 3D - Teor de Mn em {local}"
        )
        fig.update_layout(scene=dict(yaxis=dict(autorange="reversed")))
    else:
        media_por_furo = df_filtrado.groupby('Furo')['Mn'].mean().reset_index()
        fig = px.bar(
            media_por_furo, x='Furo', y='Mn', color='Mn',
            color_continuous_scale=["darkblue", "deepskyblue", "green", "yellow", "orange", "red", "darkred"],
            title=f"Teor Médio por Furo - {local}"
        )

    # Frase descritiva
    frases = []
    if furo:
        profundidades = df_filtrado[['DEPTH_FROM', 'DEPTH_TO']].astype(str).agg(' a '.join, axis=1).tolist()
        teor_max = df_filtrado['Mn'].max()
        frases.append(f"Furo {furo} apresenta teor máximo de {teor_max:.2f}% de manganês.")
        frases.append(f"Intervalos amostrados: {', '.join(profundidades[:3])}...")
    else:
        teor_global = df_filtrado.groupby('Furo')['Mn'].mean().idxmax()
        frases.append(f"Furo com maior teor médio: {teor_global}.")

    return [dcc.Graph(figure=fig)], ' '.join(frases)

# Execução
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
