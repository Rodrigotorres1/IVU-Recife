import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def mapa_cloropletico(geojson_path: Path) -> go.Figure:
    with open(geojson_path, encoding='utf-8') as f:
        geojson = json.load(f)

    for feat in geojson['features']:
        feat['id'] = feat['properties']['NM_BAIRRO']

    df = pd.DataFrame([feat['properties'] for feat in geojson['features']])

    fig = px.choropleth_mapbox(
        df,
        geojson=geojson,
        locations='NM_BAIRRO',
        featureidkey='properties.NM_BAIRRO',
        color='IVU',
        color_continuous_scale='RdYlGn',
        range_color=[0, 10],
        mapbox_style='carto-positron',
        zoom=11,
        center={'lat': -8.05, 'lon': -34.92},
        opacity=0.75,
        hover_name='NM_BAIRRO',
        hover_data={
            'NM_BAIRRO':        False,
            'IVU':              ':.2f',
            'nota_renda':       ':.2f',
            'nota_seguranca':   ':.2f',
            'nota_mobilidade':  ':.2f',
        },
        labels={
            'IVU':             'IVU',
            'nota_renda':      'Renda',
            'nota_seguranca':  'Segurança',
            'nota_mobilidade': 'Mobilidade',
        },
        title='Mapa de Vulnerabilidade Urbana — Recife (2025)',
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=580,
        coloraxis_colorbar=dict(title='IVU', tickformat='.1f'),
    )
    return fig
