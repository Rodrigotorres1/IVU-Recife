"""Geração de visualizações da dimensão de mobilidade urbana de Recife.

Produz mapa estático (PNG), mapa interativo Folium (HTML) e gráfico
Plotly (HTML) a partir dos dados processados de mobilidade.
"""

import os
from pathlib import Path

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px


def find_root() -> Path:
    """Localiza a raiz do projeto pelo marcador .git."""
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / '.git').exists():
            return p
    return Path.cwd()


def _detectar_col_bairro(gdf: gpd.GeoDataFrame) -> str:
    """Detecta a coluna com o nome do bairro no GeoDataFrame."""
    for col in gdf.columns:
        if col.upper().startswith('NM_') and 'BAIRRO' in col.upper():
            return col
    for col in gdf.columns:
        if 'bairro' in col.lower():
            return col
    raise KeyError('Coluna de nome de bairro não encontrada.')


def carregar_mobilidade(geo_path: Path) -> tuple[gpd.GeoDataFrame, str]:
    """Carrega o GeoJSON de mobilidade processado.

    Args:
        geo_path: Caminho para data/processed/recife_mobilidade.geojson.

    Returns:
        Tupla (GeoDataFrame, nome_coluna_bairro).
    """
    if not geo_path.exists():
        raise FileNotFoundError(
            f'GeoJSON não encontrado: {geo_path}\n'
            'Execute src/limpeza/limpeza_mobilidade.py primeiro.'
        )
    gdf = gpd.read_file(geo_path)
    col = _detectar_col_bairro(gdf)
    gdf = gdf.dropna(subset=[col]).copy()
    gdf[col] = gdf[col].astype(str)
    print(f'Bairros carregados: {len(gdf)} | coluna: "{col}"')
    return gdf, col


def gerar_mapa_estatico(
    gdf: gpd.GeoDataFrame,
    col_bairro: str,
    output_path: Path,
) -> None:
    """Gera e salva mapa coroplético estático (matplotlib) em PNG.

    Args:
        gdf: GeoDataFrame com nota_mobilidade por bairro.
        col_bairro: Nome da coluna de bairro.
        output_path: Caminho de destino do arquivo PNG.
    """
    fig, ax = plt.subplots(figsize=(12, 12))
    gdf.plot(
        column='nota_mobilidade',
        ax=ax,
        cmap='YlGnBu',
        legend=True,
        legend_kwds={'label': 'Nota de Mobilidade (0-10)', 'shrink': 0.6},
        edgecolor='white',
        linewidth=0.4,
        missing_kwds={'color': 'lightgrey', 'label': 'Sem dados'},
    )
    ax.set_title('Mobilidade Urbana por Bairro — Recife\n(densidade de paradas de ônibus)', fontsize=14)
    ax.set_axis_off()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Mapa estático salvo: {output_path}')


def gerar_mapa_interativo(
    gdf: gpd.GeoDataFrame,
    col_bairro: str,
    output_path: Path,
) -> None:
    """Gera e salva mapa coroplético interativo Folium em HTML.

    Args:
        gdf: GeoDataFrame com nota_mobilidade por bairro.
        col_bairro: Nome da coluna de bairro.
        output_path: Caminho de destino do arquivo HTML.
    """
    gdf_wgs84 = gdf.to_crs('EPSG:4326')
    geo_json_str = gdf_wgs84.to_json()

    mapa = folium.Map(location=[-8.05, -34.93], zoom_start=12, tiles='CartoDB positron')
    folium.Choropleth(
        geo_data=geo_json_str,
        data=gdf_wgs84[[col_bairro, 'nota_mobilidade']],
        columns=[col_bairro, 'nota_mobilidade'],
        key_on=f'feature.properties.{col_bairro}',
        fill_color='YlGnBu',
        fill_opacity=0.75,
        line_opacity=0.4,
        legend_name='Nota de Mobilidade (0-10)',
        nan_fill_color='lightgrey',
        highlight=True,
    ).add_to(mapa)

    tooltip_fields = [f for f in [col_bairro, 'nota_mobilidade', 'num_paradas'] if f in gdf_wgs84.columns]
    folium.GeoJson(
        geo_json_str,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=['Bairro', 'Nota Mobilidade', 'Nº de Paradas'][:len(tooltip_fields)],
            localize=True,
        ),
        style_function=lambda x: {'fillOpacity': 0, 'weight': 0},
    ).add_to(mapa)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapa.save(str(output_path))
    print(f'Mapa interativo salvo: {output_path}')


def gerar_grafico_barras(csv_path: Path, output_path: Path) -> None:
    """Gera e salva gráfico Plotly de barras com as notas de mobilidade.

    Args:
        csv_path: Caminho para mobilidade_por_bairro.csv.
        output_path: Caminho de destino do arquivo HTML.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f'CSV não encontrado: {csv_path}\n'
            'Execute src/limpeza/limpeza_mobilidade.py primeiro.'
        )
    df = pd.read_csv(csv_path)
    df_sorted = df.sort_values('nota_dimensao', ascending=True)

    fig = px.bar(
        df_sorted,
        x='nota_dimensao',
        y='bairro',
        orientation='h',
        color='nota_dimensao',
        color_continuous_scale='YlGnBu',
        labels={'nota_dimensao': 'Nota de Mobilidade (0-10)', 'bairro': 'Bairro'},
        title='Nota de Mobilidade Urbana por Bairro — Recife',
    )
    fig.update_layout(
        height=max(600, len(df) * 18),
        coloraxis_showscale=False,
        yaxis=dict(tickfont=dict(size=9)),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path))
    print(f'Gráfico salvo: {output_path}')


def imprimir_resumo(df: pd.DataFrame) -> None:
    """Imprime resumo estatístico da dimensão de mobilidade.

    Args:
        df: DataFrame com bairro e nota_dimensao.
    """
    print('=' * 50)
    print('RESUMO — DIMENSÃO MOBILIDADE URBANA')
    print('=' * 50)
    print(f'Total de bairros analisados : {len(df)}')
    print(f'Nota média                  : {df["nota_dimensao"].mean():.2f}')
    print(f'Nota máxima                 : {df["nota_dimensao"].max():.2f} ({df.loc[df["nota_dimensao"].idxmax(), "bairro"]})')
    print(f'Nota mínima                 : {df["nota_dimensao"].min():.2f} ({df.loc[df["nota_dimensao"].idxmin(), "bairro"]})')
    print(f'Bairros nota < 3 (ruim)     : {(df["nota_dimensao"] < 3).sum()}')
    print(f'Bairros nota > 7 (bom)      : {(df["nota_dimensao"] > 7).sum()}')
    print('=' * 50)


def main() -> None:
    """Pipeline completo de geração de visualizações de mobilidade."""
    root = find_root()
    geo_path = root / 'data' / 'processed' / 'recife_mobilidade.geojson'
    csv_path = root / 'data' / 'processed' / 'mobilidade_por_bairro.csv'
    out_dir  = root / 'notebooks' / 'arthur'

    gdf, col_bairro = carregar_mobilidade(geo_path)
    gerar_mapa_estatico(gdf, col_bairro, out_dir / 'mapa_mobilidade.png')
    gerar_mapa_interativo(gdf, col_bairro, out_dir / 'mapa_mobilidade_interativo.html')
    gerar_grafico_barras(csv_path, out_dir / 'grafico_mobilidade.html')

    df = pd.read_csv(csv_path)
    imprimir_resumo(df)
    print('Análise de mobilidade concluída.')


if __name__ == '__main__':
    main()
