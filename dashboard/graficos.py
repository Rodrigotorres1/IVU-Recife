from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def fig_ranking(df: pd.DataFrame, n: int = 10) -> tuple:
    top    = df.nlargest(n, 'IVU').sort_values('IVU')
    bottom = df.nsmallest(n, 'IVU').sort_values('IVU', ascending=False)

    def _bar(data, title):
        fig = px.bar(
            data, x='IVU', y='bairro', orientation='h',
            color='IVU', color_continuous_scale='RdYlGn', range_color=[0, 10],
            text='IVU', title=title,
            labels={'IVU': 'IVU (0–10)', 'bairro': ''},
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(
            coloraxis_showscale=False,
            xaxis_range=[0, 11],
            height=400,
            margin=dict(l=0, r=60, t=40, b=0),
        )
        return fig

    return _bar(top, f'Top {n} — menos vulneráveis'), _bar(bottom, f'Top {n} — mais vulneráveis')


def fig_dimensoes(df: pd.DataFrame) -> go.Figure:
    df_plot = df.sort_values('IVU', ascending=False)

    z = df_plot[['nota_renda', 'nota_seguranca', 'nota_mobilidade', 'IVU']].values.T
    labels_y = ['Renda', 'Segurança', 'Mobilidade', 'IVU']

    fig = go.Figure(go.Heatmap(
        z=z,
        x=df_plot['bairro'].tolist(),
        y=labels_y,
        colorscale='RdYlGn',
        zmin=0,
        zmax=10,
        text=[[f'{v:.1f}' for v in row] for row in z],
        texttemplate='%{text}',
        textfont=dict(size=9),
        hovertemplate='<b>%{x}</b><br>%{y}: %{z:.2f}<extra></extra>',
        colorbar=dict(title='Nota<br>(0–10)', tickformat='.0f'),
    ))
    fig.update_layout(
        title='Comparativo das 3 Dimensões por Bairro',
        height=300,
        xaxis=dict(
            tickangle=-60,
            tickfont=dict(size=9),
            title='',
        ),
        yaxis=dict(title='', autorange='reversed'),
        margin=dict(l=90, r=80, t=50, b=140),
    )
    return fig


def fig_ivu_completo(df: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df.sort_values('IVU'),
        x='IVU', y='bairro', orientation='h',
        color='IVU', color_continuous_scale='RdYlGn', range_color=[0, 10],
        text='IVU',
        hover_data={'nota_renda': ':.2f', 'nota_seguranca': ':.2f', 'nota_mobilidade': ':.2f'},
        labels={'IVU': 'IVU (0–10)', 'bairro': ''},
        title='IVU por Bairro — Recife (2025)',
        height=2200,
    )
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(
        coloraxis_showscale=False,
        xaxis_range=[0, 11],
        margin=dict(l=0, r=60, t=50, b=0),
    )
    return fig


def fig_bairro_detalhe(row: pd.Series) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=['Renda', 'Segurança', 'Mobilidade', 'IVU'],
        y=[row['nota_renda'], row['nota_seguranca'], row['nota_mobilidade'], row['IVU']],
        marker_color=['#2ecc71', '#e74c3c', '#3498db', '#2c3e50'],
        text=[f"{row['nota_renda']:.2f}", f"{row['nota_seguranca']:.2f}",
              f"{row['nota_mobilidade']:.2f}", f"{row['IVU']:.2f}"],
        textposition='outside',
    ))
    fig.update_layout(
        yaxis=dict(range=[0, 11], title='Nota (0–10)'),
        title=f'Notas por dimensão — {row["bairro"]}',
        height=350,
        margin=dict(l=0, r=0, t=50, b=0),
    )
    return fig
