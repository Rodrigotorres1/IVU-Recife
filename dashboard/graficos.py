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

    fig = go.Figure()
    dimensoes = [
        ('nota_renda',      'Renda',      '#2ecc71'),
        ('nota_seguranca',  'Segurança',  '#e74c3c'),
        ('nota_mobilidade', 'Mobilidade', '#3498db'),
    ]
    for col, nome, cor in dimensoes:
        fig.add_trace(go.Bar(
            y=df_plot['bairro'], x=df_plot[col],
            name=nome, orientation='h',
            marker_color=cor, opacity=0.85,
            width=0.25,  # altura fixa em unidades de dados — evita sumiço ao dar zoom
        ))
    fig.add_trace(go.Scatter(
        y=df_plot['bairro'], x=df_plot['IVU'],
        name='IVU', mode='markers',
        marker=dict(symbol='diamond', size=8, color='#2c3e50'),
    ))
    fig.update_layout(
        barmode='group',
        title='Comparativo das 3 Dimensões por Bairro',
        height=2200,
        xaxis=dict(range=[0, 11], title='Nota (0–10)'),
        yaxis_title='',
        legend=dict(orientation='v', yanchor='middle', y=0.5, xanchor='left', x=1.02),
        margin=dict(l=0, r=120, t=50, b=0),
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
