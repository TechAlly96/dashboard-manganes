# Dashboard 3D - Análise de Manganês

Este projeto apresenta um dashboard interativo para análise de resultados de sondagem com foco na concentração de manganês (Mn), utilizando dados obtidos por fluorescência de raios X com o aparelho X-MET8000.

## Funcionalidades

- Visualização em 3D das amostras com aplicação de mapa de calor por profundidade e teor de Mn.
- Gráfico de barras detalhado com profundidade, teor de manganês e descrição do furo.
- Frases interpretativas automáticas por localidade e por furo.
- Análise estatística (média, máximo, quantidade de amostras por área).
- Interface responsiva para dispositivos móveis e desktop.

## Requisitos

- Python 3.10+
- Bibliotecas: `dash`, `plotly`, `pandas`, `dash-bootstrap-components`, `openpyxl`

Instale com:

```bash
pip install -r requirements.txt
```

## Execução local

```bash
python dashboard_manganes_3d.py
```

Acesse em `http://127.0.0.1:10000`

## Sobre

Projeto desenvolvido para análise de amostras da Brasil Minerais Impex em regiões como Bufalo, Centralzinho, entre outras.