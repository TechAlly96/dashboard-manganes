# dashboard_manganes_3d.py

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objects as go
import os

# Função para corrigir nomes de colunas
def corrigir_colunas(df):
    colunas_corrigidas = {col: col.strip().replace(" ", "_").upper() for col in df.columns}
    df.rename(columns=colunas_corrigidas, inplace=True)
    return df

# Carregamento de dados
path_data = "data"
df = pd.read_excel(os.path.join(path_data, "ASSAY.xlsx"))
df = corrigir_colunas(df)

for col in ['DEPTH_FROM', 'DEPTH_TO', 'MN', 'FE']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df.dropna(subset=['MN', 'DEPTH_FROM', 'DEPTH_TO', 'FURO', 'LOCAL'], inplace=True)
df['z'] = (df['DEPTH_FROM'] + df['DEPTH_TO']) / 2

# App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Interativo - Análise de Manganês"

# Cores do mapa de calor
cores_calor = ['#00008B', '#00CED1', 'green', 'yellow', 'orange', '#8B0000']
def cor_teor_mn(teor):
    if teor < 5: return cores_calor[0]
    elif teor < 10: return cores_calor[1]
    elif teor < 15: return cores_calor[2]
    elif teor < 20: return cores_calor[3]
    elif teor < 30: return cores_calor[4]
    else: return cores_calor[5]

# Layout
app.layout = dbc.Container([
    html.H2("Dashboard Interativo - Análise de Manganês", className="text-center my-3"),

    dcc.Dropdown(
        id='furo-dropdown',
        options=[{'label': f, 'value': f} for f in sorted(df['FURO'].unique())],
        value=sorted(df['FURO'].unique())[0],
        clearable=False
    ),

    dcc.Tabs(id='tabs', value='apresentacao', children=[
        dcc.Tab(label='Apresentação', value='apresentacao'),
        dcc.Tab(label='Gráfico de Barras (Metro a Metro)', value='barra'),
        dcc.Tab(label='Gráfico de Pizza (Resumo por Localidade)', value='pizza'),
        dcc.Tab(label='Histograma Geral (Distribuição de Teores)', value='histograma'),
        dcc.Tab(label='CUTOFF (Resumo por Localidade)', value='cutoff'),
        dcc.Tab(label='Coleta de Amostras', value='coleta')
    ]),

    html.Div(id='conteudo'),

    html.Div([
        html.H6("Legenda do Mapa de Calor", className="mt-4"),
        html.Div([
            html.Span("0–5%", style={'backgroundColor': cores_calor[0], 'color': 'white', 'padding': '4px'}),
            html.Span("5–10%", style={'backgroundColor': cores_calor[1], 'padding': '4px'}),
            html.Span("10–15%", style={'backgroundColor': cores_calor[2], 'color': 'white', 'padding': '4px'}),
            html.Span("15–20%", style={'backgroundColor': cores_calor[3], 'padding': '4px'}),
            html.Span("20–30%", style={'backgroundColor': cores_calor[4], 'padding': '4px'}),
            html.Span(">30%", style={'backgroundColor': cores_calor[5], 'color': 'white', 'padding': '4px'})
        ], style={"display": "flex", "gap": "10px", "flexWrap": "wrap"})
    ])
], fluid=True)

# Renderização dinâmica
@app.callback(
    Output('conteudo', 'children'),
    Input('tabs', 'value'),
    Input('furo-dropdown', 'value')
)
def renderizar_conteudo(aba, furo):
    if aba == 'apresentacao':
        return html.Iframe(src="assets/apresentacao.html", style={"width": "100%", "height": "600px"})

    elif aba == 'barra':
        dff = df[df['FURO'] == furo].copy().sort_values('DEPTH_FROM')
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
        fig.update_layout(xaxis_title="Mn (%)", yaxis=dict(autorange='reversed'), height=450)
        local = dff['LOCAL'].iloc[0]
        return [
            dcc.Graph(figure=fig),
            html.Div([
                html.P(f"Furo {furo} — Localidade: {local}"),
                html.P(f"Número de amostras: {len(dff)}"),
                html.P(f"Máximo teor: {dff['MN'].max():.2f}%"),
                html.P(f"Mínimo teor: {dff['MN'].min():.2f}%")
            ], className="text-info fw-bold p-2")
        ]

    elif aba == 'pizza':
        dff = df.groupby("LOCAL").agg({"MN": "mean", "FURO": pd.Series.nunique}).reset_index()
        fig = go.Figure(go.Pie(
            labels=dff['LOCAL'], values=dff['MN'],
            hovertext=[f"{qtd} furos" for qtd in dff['FURO']],
            textinfo='label+percent'
        ))
        return [
            dcc.Graph(figure=fig),
            html.Ul([
                html.Li(f"{row.LOCAL}: {row.FURO} furos, média {row.MN:.2f}% Mn")
                for _, row in dff.iterrows()
            ], className="text-info fw-bold p-2")
        ]

    elif aba == 'histograma':
        df['cor'] = df['MN'].apply(cor_teor_mn)
        fig = go.Figure(go.Histogram(
            x=df['MN'],
            xbins=dict(start=0, end=52, size=2),
            marker_color='#008B8B'
        ))
        fig.update_layout(xaxis_title="Mn (%)", yaxis_title="Frequência", height=500)
        return dcc.Graph(figure=fig)

    elif aba == 'cutoff':
        return html.Div([
            html.Label("Defina o valor de cutoff (%):"),
            dcc.Input(id="cutoff-input", type="number", value=10, step=0.1),
            html.Div(id="cutoff-output", className="text-info mt-3")
        ], className="p-3")

    elif aba == 'coleta':
        return html.Iframe(src="assets/mapa_amostras_solo.html", style={"width": "100%", "height": "600px"})

    return html.Div("Aba não implementada.")

# Callback para CUTOFF
@app.callback(
    Output("cutoff-output", "children"),
    Input("cutoff-input", "value")
)
def atualizar_cutoff(corte):
    if corte is None or not isinstance(corte, (int, float)):
        return "Informe um valor válido."
    saidas = []
    for local, grupo in df.groupby('LOCAL'):
        total = len(grupo)
        filtrado = grupo[grupo['MN'] > corte]
        if filtrado.empty:
            continue
        media_mn = filtrado['MN'].mean()
        max_mn = filtrado['MN'].max()
        min_mn = filtrado['MN'].min()
        media_fe = filtrado['FE'].mean()
        mn_fe = media_mn / media_fe if media_fe else 0
        saidas.append(html.P([
            html.Strong(f"{local.upper()}: ", style={"color": "#0d6efd"}),
            f"{total} amostras, após corte de {corte:.1f}% restaram {len(filtrado)}. ",
            f"Média Mn: {media_mn:.2f}%, Máx: {max_mn:.2f}%, Mín: {min_mn:.2f}%, Fe: {media_fe:.2f}%, Mn/Fe: {mn_fe:.2f}"
        ]))
    if not saidas:
        return f"Nenhuma localidade possui Mn > {corte:.2f}%."
    return saidas



server = app.server  # para Railway identificar o servidor

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)


application = app  # para gunicorn encontrar o app

