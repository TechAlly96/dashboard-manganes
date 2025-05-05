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

# Carregar dados principais
df = pd.read_excel(os.path.join("data", "ASSAY.xlsx"))
df = corrigir_colunas(df)

# Converter colunas para numérico, tratando erros
numeric_cols_df = ['DEPTH_FROM', 'DEPTH_TO', 'MN', 'FE']
for col in numeric_cols_df:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

df.dropna(subset=['MN', 'FE', 'DEPTH_FROM', 'DEPTH_TO', 'FURO', 'LOCAL'], inplace=True)
df['z'] = (df['DEPTH_FROM'] + df['DEPTH_TO']) / 2

# Dados da aba Coleta de Amostras
df_solo = pd.read_excel("data/Amostras de Solo Coletadas.xlsx")
df_solo = corrigir_colunas(df_solo)

# Converter colunas para numérico, tratando erros
numeric_cols_solo = ['LATITUDE', 'LONGITUDE', 'MN', 'FE']
for col in numeric_cols_solo:
    if col in df_solo.columns:
        df_solo[col] = pd.to_numeric(df_solo[col], errors='coerce')

# Remover a geração dinâmica da descrição, já que não será usada
# def gerar_descricao(row):
#     # Seleciona apenas colunas numéricas válidas para análise
#     numeric_elements = row[valid_cols_for_descricao].dropna()
#     destaque = numeric_elements.sort_values(ascending=False)
#     if not destaque.empty:
#         top = destaque.index[0]
#         return (f"Teor de ferro em {row['FE']:.2f}% foi destaque na análise com XRF, "
#                 f"teor de manganês {row['MN']:.2f}%. Outro elemento com teor elevado foi {top} com {row[top]:.2f}%.")
#     return "Dados insuficientes para gerar descrição."
#
# df_solo['DESCRICAO'] = df_solo.apply(gerar_descricao, axis=1)

# App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Interativo - Análise de Manganês"

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
        dcc.Tab(label='CUTOFF (Resumo por Localidade)', value='cutoff'),
        dcc.Tab(label='Coleta de Amostras', value='coleta')
    ]),
    html.Div(id='conteudo'),
    html.Div([
        html.H6("Legenda do Mapa de Calor", className="mt-4"),
        html.Div([
            html.Span("0–5%", style={'backgroundColor': '#00008B', 'color': 'white', 'padding': '4px'}),
            html.Span("5–10%", style={'backgroundColor': '#00CED1', 'color': 'black', 'padding': '4px'}),
            html.Span("10–15%", style={'backgroundColor': 'green', 'color': 'white', 'padding': '4px'}),
            html.Span("15–20%", style={'backgroundColor': 'yellow', 'color': 'black', 'padding': '4px'}),
            html.Span("20–30%", style={'backgroundColor': 'orange', 'color': 'black', 'padding': '4px'}),
            html.Span(">30%", style={'backgroundColor': '#8B0000', 'color': 'white', 'padding': '4px'})
        ], style={"display": "flex", "gap": "10px", "flexWrap": "wrap"})
    ])
], fluid=True)

def cor_teor_mn(teor):
    if teor < 5:
        return '#00008B'
    elif teor < 10:
        return '#00CED1'
    elif teor < 15:
        return 'green'
    elif teor < 20:
        return 'yellow'
    elif teor < 30:
        return 'orange'
    else:
        return '#8B0000'

@app.callback(
    Output('conteudo', 'children'),
    Input('furo-dropdown', 'value'),
    Input('tabs', 'value')
)
def atualizar_conteudo(furo_selecionado, aba):
    if aba == 'barra':
        dff = df[df['FURO'] == furo_selecionado].copy().sort_values('DEPTH_FROM')
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
            height=450, margin=dict(l=40, r=10, t=40, b=30)
        )
        local = dff['LOCAL'].iloc[0]
        maior, menor = dff['MN'].max(), dff['MN'].min()
        total = len(dff)
        return [
            dcc.Graph(figure=fig),
            html.Div([
                html.P(f"Furo {furo_selecionado} — Localidade: {local}"),
                html.P(f"Número de amostras: {total}"),
                html.P("Leituras feitas por amostra: 2 disparos"),
                html.P(f"Máximo teor registrado: {maior:.2f}% de manganês"),
                html.P(f"Mínimo teor registrado: {menor:.2f}% de manganês")
            ], className="text-info fw-bold p-2")
        ]

    elif aba == 'pizza':
        dff = df.groupby("LOCAL").agg({"MN": "mean", "FURO": pd.Series.nunique}).reset_index()
        fig = go.Figure(go.Pie(
            labels=dff['LOCAL'],
            values=dff['MN'],
            hovertext=[f"{qtd} furos" for qtd in dff['FURO']],
            textinfo='label+percent'
        ))
        return [
            dcc.Graph(figure=fig),
            html.Ul([
                html.Li(f"Localidade {row.LOCAL}: {row.FURO} furos com média de {row.MN:.2f}% de manganês")
                for _, row in dff.iterrows()
            ], className="text-info fw-bold p-2")
        ]

    elif aba == 'histograma':
        hist_data = df['MN']
        bins = list(range(0, 55, 5))
        counts, edges = pd.cut(hist_data, bins=bins, retbins=True, labels=False, include_lowest=True)
        colors = [cor_teor_mn((edges[i] + edges[i+1]) / 2) for i in range(len(edges)-1)]
        fig = go.Figure(go.Bar(
            x=[f"{edges[i]}–{edges[i+1]}" for i in range(len(edges)-1)],
            y=pd.value_counts(counts, sort=False).fillna(0),
            marker_color=colors
        ))
        fig.update_layout(
            xaxis_title="Teor de Manganês (%)",
            yaxis_title="Frequência de Ocorrências",
            height=500, margin=dict(l=40, r=10, t=40, b=30)
        )
        return [
            dcc.Graph(figure=fig),
            html.Div([
                html.P(f"Número total de amostras analisadas: {len(df)}"),
                html.P(f"Máximo teor registrado: {df['MN'].max():.2f}% de manganês"),
                html.P(f"Mínimo teor registrado: {df['MN'].min():.2f}% de manganês"),
                html.P("Este histograma ajuda a entender a distribuição de teores no projeto.")
            ], className="text-info fw-bold p-2")
        ]

    elif aba == 'cutoff':
        return html.Div([
            html.Label("Defina o valor de cutoff (%):"),
            dcc.Input(id="cutoff-input", type="number", value=10, step=0.1),
            html.Div(id="cutoff-output", className="text-info mt-3")
        ], className="p-3")

    elif aba == 'coleta':
        return html.Iframe(src="assets/mapa_amostras_solo.html",
                           style={"width": "100%", "height": "600px"})

    return html.P("Selecione uma aba.")

@app.callback(
    Output("cutoff-output", "children"),
    Input("cutoff-input", "value")
)
def atualizar_cutoff(corte):
    if corte is None:
        return "Informe um valor de corte."
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
        saidas.append(html.Div([
            html.P([
                html.Strong(f"{local.upper()}: ", style={"color": "#0d6efd"}),
                f"{total} amostras, após corte de {corte:.1f}% restaram {len(filtrado)}. ",
                f"Média Mn: {media_mn:.2f}%, Máximo: {max_mn:.2f}%, Mínimo: {min_mn:.2f}%. ",
                f"Média Fe: {media_fe:.2f}%, Mn/Fe: {mn_fe:.2f}"
            ])
        ]))
    return saidas

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)