import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objects as go
import os

# Corrigir nome de colunas antes de carregar o dataframe
def corrigir_colunas(df):
    colunas_corrigidas = {col.strip().replace(" ", "_").upper(): col for col in df.columns}
    df.rename(columns=colunas_corrigidas, inplace=True)
    return df

# Carregar dados
caminho_arquivo = os.path.join("data", "ASSAY.xlsx")
df = pd.read_excel(caminho_arquivo)
df = corrigir_colunas(df)

# Corrigir tipos de dados
df['DEPTH_FROM'] = pd.to_numeric(df['DEPTH_FROM'], errors='coerce')
df['DEPTH_TO'] = pd.to_numeric(df['DEPTH_TO'], errors='coerce')
df['MN'] = pd.to_numeric(df['MN'], errors='coerce')
df.dropna(subset=['MN', 'DEPTH_FROM', 'DEPTH_TO', 'FURO', 'LOCAL'], inplace=True)
df['z'] = (df['DEPTH_FROM'] + df['DEPTH_TO']) / 2

# Inicializar app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Interativo - Análise de Manganês"

# Função de cor para mapa de calor
def cor_teor_mn(teor):
    if teor < 5:
        return '#00008B'  # Azul escuro
    elif teor < 10:
        return '#00CED1'  # Azul claro
    elif teor < 15:
        return 'green'
    elif teor < 20:
        return 'yellow'
    elif teor < 30:
        return 'orange'
    else:
        return '#8B0000'

# Layout
app.layout = dbc.Container([
    html.H2("Dashboard Interativo - Análise de Manganês", className="text-center my-3"),

    dcc.Dropdown(
        id='furo-dropdown',
        options=[{'label': furo, 'value': furo} for furo in sorted(df['FURO'].unique())],
        value=sorted(df['FURO'].unique())[0],
        clearable=False
    ),

    dcc.Tabs(id="tabs", value='barra', children=[
        dcc.Tab(label='Gráfico de Barras (Metro a Metro)', value='barra'),
        dcc.Tab(label='Gráfico de Pizza (Resumo por Localidade)', value='pizza'),
        dcc.Tab(label='Histograma Geral (Distribuição de Teores)', value='histograma'),
    ]),

    dcc.Graph(id='grafico-mn'),
    html.Div(id='descricao', className="text-info fw-bold p-2"),

    html.Div([
        html.H6("Legenda do Mapa de Calor", className="mt-4"),
        html.Div([
            html.Span("0–5%", style={'backgroundColor': '#00008B', 'color': 'white', 'padding': '4px'}),
            html.Span("5–10%", style={'backgroundColor': '#00CED1', 'color': 'black', 'padding': '4px'}),
            html.Span("10–15%", style={'backgroundColor': 'green', 'color': 'white', 'padding': '4px'}),
            html.Span("15–20%", style={'backgroundColor': 'yellow', 'padding': '4px'}),
            html.Span("20–30%", style={'backgroundColor': 'orange', 'padding': '4px'}),
            html.Span(">30%", style={'backgroundColor': '#8B0000', 'color': 'white', 'padding': '4px'}),
        ], style={"display": "flex", "gap": "10px", "flexWrap": "wrap"})
    ])
], fluid=True)

# Callbacks
@app.callback(
    Output('grafico-mn', 'figure'),
    Output('descricao', 'children'),
    Input('furo-dropdown', 'value'),
    Input('tabs', 'value')
)
def atualizar_grafico(furo_selecionado, aba):
    if aba == 'barra':
        dff = df[df['FURO'] == furo_selecionado].copy()
        dff = dff.sort_values('DEPTH_FROM')
        dff['cor'] = dff['MN'].apply(cor_teor_mn)

        profundidades = [f"{row['DEPTH_FROM']:.0f}–{row['DEPTH_TO']:.0f} m" for _, row in dff.iterrows()]
        fig = go.Figure(go.Bar(
            x=dff['MN'],
            y=profundidades,
            orientation='h',
            marker=dict(color=dff['cor']),
            text=[f"{v:.2f}%" for v in dff['MN']],
            textposition='auto'
        ))

        fig.update_layout(
            xaxis_title="Teor de Manganês (%)",
            yaxis_title="Profundidade",
            yaxis=dict(autorange="reversed"),
            height=450,
            margin=dict(l=40, r=10, t=40, b=30)
        )

        local = dff['LOCAL'].iloc[0]
        maior = dff['MN'].max()
        menor = dff['MN'].min()
        total = len(dff)

        descricao = html.Div([
            html.P(f"Furo {furo_selecionado} — Localidade: {local}"),
            html.P(f"Número de amostras: {total}"),
            html.P("Leituras feitas por amostra: 2 disparos"),
            html.P(f"Máximo teor registrado: {maior:.2f}% de manganês"),
            html.P(f"Mínimo teor registrado: {menor:.2f}% de manganês"),
        ])

    elif aba == 'pizza':
        dff = df.groupby("LOCAL").agg({"MN": "mean", "FURO": pd.Series.nunique}).reset_index()
        fig = go.Figure(go.Pie(
            labels=dff['LOCAL'],
            values=dff['MN'],
            hovertext=[f"{qtd} furos" for qtd in dff['FURO']],
            textinfo='label+percent'
        ))

        fig.update_layout(
            height=500,
            margin=dict(t=30, b=30, l=30, r=30)
        )

        descricao = html.Ul([
            html.Li(f"Localidade {row.LOCAL}: {row.FURO} furos com média de {row.MN:.2f}% de manganês")
            for _, row in dff.iterrows()
        ])

    elif aba == 'histograma':
        hist_data = df['MN']
        bins = list(range(0, 52, 2))  # Bins de 2 em 2%

        cores = [cor_teor_mn(x) for x in hist_data]

        fig = go.Figure(go.Histogram(
            x=hist_data,
            nbinsx=len(bins),
            marker=dict(color="#008B8B"),
            autobinx=False,
            xbins=dict(start=0, end=52, size=2),
        ))

        fig.update_traces(marker_color='#008B8B')

        fig.update_layout(
            xaxis_title="Teor de Manganês (%)",
            yaxis_title="Frequência de Ocorrências",
            height=500,
            margin=dict(t=30, b=30, l=30, r=30)
        )

        maximo = hist_data.max()
        minimo = hist_data.min()
        total_amostras = len(hist_data)

        descricao = html.Div([
            html.P(f"Número total de amostras analisadas: {total_amostras}"),
            html.P(f"Máximo teor registrado: {maximo:.2f}% de manganês"),
            html.P(f"Mínimo teor registrado: {minimo:.2f}% de manganês"),
            html.P("Este histograma ajuda a entender a distribuição de teores no projeto.", style={"marginTop": "10px"})
        ], style={"color": "deepskyblue", "padding": "10px"})

    return fig, descricao

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
