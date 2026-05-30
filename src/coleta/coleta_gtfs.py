"""Coleta dos dados de transporte público (GTFS) e malha viária de Recife.

Baixa o feed GTFS do Grande Recife Consórcio, extrai as paradas,
filtra para a área de Recife e baixa a malha viária via OSMnx.
Salva data/processed/recife_paradas.geojson e
data/processed/recife_malha_viaria.geojson.
"""

import os
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

GTFS_URL = 'https://www.granderecife.pe.gov.br/gtfs/gtfs.zip'

# Bounding box aproximada de Recife (WGS84)
BBOX_RECIFE = {'lat_min': -8.18, 'lat_max': -7.93, 'lon_min': -35.05, 'lon_max': -34.87}


def find_root() -> Path:
    """Localiza a raiz do projeto pelo marcador .git."""
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / '.git').exists():
            return p
    return Path.cwd()


def baixar_gtfs(url: str, zip_path: Path) -> None:
    """Baixa o arquivo ZIP do GTFS se ainda não existir.

    Args:
        url: URL pública do feed GTFS.
        zip_path: Caminho de destino do ZIP.
    """
    if zip_path.exists():
        print(f'GTFS já disponível: {zip_path}')
        return
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    print(f'Baixando GTFS de: {url}')
    urllib.request.urlretrieve(url, zip_path)
    print(f'ZIP salvo em: {zip_path}')


def extrair_gtfs(zip_path: Path, extract_dir: Path) -> Path:
    """Extrai o ZIP do GTFS e retorna o diretório de extração.

    Args:
        zip_path: Caminho para o ZIP do GTFS.
        extract_dir: Diretório de destino.

    Returns:
        Caminho do diretório com os arquivos extraídos.
    """
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)
    print(f'GTFS extraído em: {extract_dir}')
    return extract_dir


def carregar_paradas(extract_dir: Path) -> gpd.GeoDataFrame:
    """Carrega stops.txt e cria GeoDataFrame de pontos de parada.

    Args:
        extract_dir: Diretório com os arquivos GTFS extraídos.

    Returns:
        GeoDataFrame com geometria de pontos (EPSG:4326).
    """
    stops = pd.read_csv(extract_dir / 'stops.txt')
    gdf = gpd.GeoDataFrame(
        stops,
        geometry=gpd.points_from_xy(stops['stop_lon'], stops['stop_lat']),
        crs='EPSG:4326',
    )
    print(f'Total de paradas no GTFS: {len(gdf)}')
    return gdf


def filtrar_recife(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filtra paradas dentro da bounding box de Recife.

    Args:
        gdf: GeoDataFrame com todas as paradas do GTFS.

    Returns:
        GeoDataFrame com paradas dentro dos limites de Recife.
    """
    mask = (
        (gdf['stop_lat'] >= BBOX_RECIFE['lat_min']) &
        (gdf['stop_lat'] <= BBOX_RECIFE['lat_max']) &
        (gdf['stop_lon'] >= BBOX_RECIFE['lon_min']) &
        (gdf['stop_lon'] <= BBOX_RECIFE['lon_max'])
    )
    recife = gdf[mask].copy()
    print(f'Paradas em Recife: {len(recife)}')
    return recife


def baixar_malha_viaria(output_path: Path) -> gpd.GeoDataFrame:
    """Baixa a malha viária de Recife via OSMnx ou carrega se já existir.

    Args:
        output_path: Caminho de destino do GeoJSON da malha viária.

    Returns:
        GeoDataFrame com os segmentos de rua (geometria LineString).
    """
    if output_path.exists():
        print(f'Malha viária já disponível: {output_path}')
        return gpd.read_file(output_path)

    import osmnx as ox  # import tardio — evita dependência obrigatória

    print('Baixando malha viária via OSMnx (~1-2 min)...')
    G = ox.graph_from_place('Recife, Pernambuco, Brasil', network_type='walk')
    _, edges = ox.graph_to_gdfs(G)
    edges_simples = edges[['geometry']].reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    edges_simples.to_file(output_path, driver='GeoJSON')
    print(f'Malha viária salva: {output_path} ({len(edges_simples)} segmentos)')
    return edges_simples


def main() -> None:
    """Pipeline completo de coleta de GTFS e malha viária."""
    root = find_root()
    zip_path    = root / 'data' / 'raw' / 'gtfs' / 'gtfs_grande_recife.zip'
    extract_dir = root / 'data' / 'raw' / 'gtfs' / 'gtfs_extraido'
    out_paradas = root / 'data' / 'processed' / 'recife_paradas.geojson'
    out_malha   = root / 'data' / 'processed' / 'recife_malha_viaria.geojson'

    baixar_gtfs(GTFS_URL, zip_path)
    extract_dir = extrair_gtfs(zip_path, extract_dir)

    gdf_stops = carregar_paradas(extract_dir)
    gdf_recife = filtrar_recife(gdf_stops)
    out_paradas.parent.mkdir(parents=True, exist_ok=True)
    gdf_recife.to_file(out_paradas, driver='GeoJSON')
    print(f'Paradas salvas: {out_paradas}')

    baixar_malha_viaria(out_malha)
    print('Coleta de GTFS e malha viária concluída.')


if __name__ == '__main__':
    main()
