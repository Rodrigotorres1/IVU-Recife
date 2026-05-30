"""Limpeza e análise de cobertura de transporte público por bairro em Recife.

Realiza join espacial entre paradas de ônibus e bairros, calcula densidade
de paradas e cobertura por buffer de 500m, normaliza em nota 0-10 e salva
os arquivos de saída para o pipeline IVU.
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


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


def carregar_bairros(bairros_path: Path) -> tuple[gpd.GeoDataFrame, str]:
    """Carrega setores censitários e dissolve em polígonos de bairro.

    Args:
        bairros_path: Caminho para data/processed/recife_renda.geojson.

    Returns:
        Tupla (GeoDataFrame de bairros, nome da coluna de bairro).
    """
    if not bairros_path.exists():
        raise FileNotFoundError(
            f'GeoJSON não encontrado: {bairros_path}\n'
            'Execute src/limpeza/limpeza_renda.py primeiro.'
        )
    gdf = gpd.read_file(bairros_path)
    col = _detectar_col_bairro(gdf)
    gdf = gdf[[col, 'geometry']].dropna(subset=[col])
    gdf = gdf.dissolve(by=col).reset_index()
    print(f'Bairros após dissolve: {len(gdf)} | coluna: "{col}"')
    return gdf, col


def carregar_paradas(paradas_path: Path, crs_destino) -> gpd.GeoDataFrame:
    """Carrega paradas de ônibus e reprojecta se necessário.

    Args:
        paradas_path: Caminho para data/processed/recife_paradas.geojson.
        crs_destino: CRS de referência para reprojeção.

    Returns:
        GeoDataFrame de paradas no mesmo CRS dos bairros.
    """
    if not paradas_path.exists():
        raise FileNotFoundError(
            f'GeoJSON não encontrado: {paradas_path}\n'
            'Execute src/coleta/coleta_gtfs.py primeiro.'
        )
    paradas = gpd.read_file(paradas_path)
    if paradas.crs != crs_destino:
        paradas = paradas.to_crs(crs_destino)
    print(f'Paradas carregadas: {len(paradas)}')
    return paradas


def contar_paradas_por_bairro(
    paradas: gpd.GeoDataFrame,
    bairros: gpd.GeoDataFrame,
    col_bairro: str,
) -> gpd.GeoDataFrame:
    """Spatial join entre paradas e bairros, com contagem por bairro.

    Args:
        paradas: GeoDataFrame de pontos de parada.
        bairros: GeoDataFrame de polígonos de bairro.
        col_bairro: Nome da coluna de bairro.

    Returns:
        GeoDataFrame de bairros com coluna num_paradas.
    """
    paradas_no_bairro = gpd.sjoin(
        paradas, bairros[[col_bairro, 'geometry']], how='inner', predicate='within'
    )
    contagem = paradas_no_bairro.groupby(col_bairro).size().reset_index(name='num_paradas')
    result = bairros.merge(contagem, on=col_bairro, how='left')
    result['num_paradas'] = result['num_paradas'].fillna(0).astype(int)
    print(f'Bairros sem paradas: {(result["num_paradas"] == 0).sum()}')
    return result


def calcular_area_e_densidade(bairros_mob: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Calcula área em km² e densidade de paradas por km².

    Args:
        bairros_mob: GeoDataFrame de bairros com num_paradas.

    Returns:
        GeoDataFrame com colunas area_km2 e densidade_paradas.
    """
    bairros_utm = bairros_mob.to_crs('EPSG:31985')
    bairros_mob['area_km2'] = bairros_utm.geometry.area / 1_000_000
    bairros_mob['densidade_paradas'] = (
        bairros_mob['num_paradas'] / bairros_mob['area_km2'].replace(0, np.nan)
    ).fillna(0)
    return bairros_mob


def calcular_cobertura(
    bairros_mob: gpd.GeoDataFrame,
    paradas: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Calcula a cobertura percentual de bairros dentro de 500m de uma parada.

    Metodologia: buffer euclidiano de 500m — padrão IBGE/WRI para análise
    de acessibilidade urbana. Diferença vs isócronas de rede em área densa
    é ~10-15%, aceitável para granularidade de bairro.

    Args:
        bairros_mob: GeoDataFrame de bairros (CRS geográfico).
        paradas: GeoDataFrame de paradas (mesmo CRS dos bairros).

    Returns:
        GeoDataFrame com colunas area_coberta_km2 e pct_cobertura_500m.
    """
    paradas_utm  = paradas.to_crs('EPSG:31985')
    bairros_utm  = bairros_mob.to_crs('EPSG:31985')
    buffer_500m  = paradas_utm.geometry.buffer(500).union_all()

    bairros_mob['area_coberta_km2'] = (
        bairros_utm.geometry.intersection(buffer_500m).area / 1_000_000
    )
    bairros_mob['pct_cobertura_500m'] = (
        bairros_mob['area_coberta_km2'] / bairros_mob['area_km2'] * 100
    ).round(1).clip(upper=100)

    print(f'Bairros com cobertura >= 80%: {(bairros_mob["pct_cobertura_500m"] >= 80).sum()}')
    print(f'Bairros com cobertura <  50%: {(bairros_mob["pct_cobertura_500m"] < 50).sum()}')
    return bairros_mob


def calcular_notas(bairros_mob: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Normaliza densidade de paradas em nota 0-10 via min-max.

    Args:
        bairros_mob: GeoDataFrame com coluna densidade_paradas.

    Returns:
        GeoDataFrame com coluna nota_mobilidade adicionada.
    """
    d_min = bairros_mob['densidade_paradas'].min()
    d_max = bairros_mob['densidade_paradas'].max()
    bairros_mob['nota_mobilidade'] = (
        (bairros_mob['densidade_paradas'] - d_min) / (d_max - d_min) * 10
    ).round(2)
    print(f'Notas: min={bairros_mob["nota_mobilidade"].min():.2f} | max={bairros_mob["nota_mobilidade"].max():.2f}')
    return bairros_mob


def salvar_resultados(
    bairros_mob: gpd.GeoDataFrame,
    col_bairro: str,
    root: Path,
) -> None:
    """Salva os arquivos de saída da dimensão de mobilidade.

    Gera:
        - data/processed/mobilidade_por_bairro.csv  (entrega para o pipeline)
        - data/processed/ranking_mobilidade.csv     (ranking completo)
        - data/processed/bairros_sem_acesso_500m.csv
        - data/processed/recife_mobilidade.geojson  (mapa)

    Args:
        bairros_mob: GeoDataFrame de bairros com notas calculadas.
        col_bairro: Nome da coluna de bairro.
        root: Raiz do projeto.
    """
    out_dir = root / 'data' / 'processed'
    out_dir.mkdir(parents=True, exist_ok=True)

    tabela = bairros_mob[[col_bairro, 'nota_mobilidade', 'num_paradas']].copy()
    tabela.columns = ['bairro', 'nota_dimensao', 'dado_principal']
    tabela['dado_principal'] = tabela['dado_principal'].astype(str) + ' paradas'
    tabela = tabela.sort_values('nota_dimensao', ascending=False).reset_index(drop=True)

    tabela[['bairro', 'nota_dimensao', 'dado_principal']].to_csv(
        out_dir / 'mobilidade_por_bairro.csv', index=False
    )
    print(f'Salvo: {out_dir / "mobilidade_por_bairro.csv"}')

    tabela.insert(0, 'ranking', range(1, len(tabela) + 1))
    tabela.to_csv(out_dir / 'ranking_mobilidade.csv', index=False)

    sem_acesso = (
        bairros_mob[[col_bairro, 'num_paradas', 'area_km2', 'pct_cobertura_500m']]
        .loc[bairros_mob['pct_cobertura_500m'] < 50]
        .sort_values('pct_cobertura_500m')
        .reset_index(drop=True)
    )
    sem_acesso.to_csv(out_dir / 'bairros_sem_acesso_500m.csv', index=False)

    bairros_mob.to_file(out_dir / 'recife_mobilidade.geojson', driver='GeoJSON')
    print(f'Salvo: {out_dir / "recife_mobilidade.geojson"}')


def main() -> None:
    """Pipeline completo de limpeza e análise de mobilidade."""
    root = find_root()
    bairros_path = root / 'data' / 'processed' / 'recife_renda.geojson'
    paradas_path = root / 'data' / 'processed' / 'recife_paradas.geojson'

    bairros, col_bairro = carregar_bairros(bairros_path)
    paradas = carregar_paradas(paradas_path, bairros.crs)
    bairros = contar_paradas_por_bairro(paradas, bairros, col_bairro)
    bairros = calcular_area_e_densidade(bairros)
    bairros = calcular_cobertura(bairros, paradas)
    bairros = calcular_notas(bairros)
    salvar_resultados(bairros, col_bairro, root)
    print('Limpeza de mobilidade concluída.')


if __name__ == '__main__':
    main()
