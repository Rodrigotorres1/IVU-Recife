"""Coleta e filtragem dos setores censitários de Recife (Censo IBGE 2022).

Extrai o shapefile de setores de Pernambuco, filtra apenas Recife
e salva em data/raw/setores_ibge/recife_setores.geojson.
"""

import os
import zipfile
from pathlib import Path

import geopandas as gpd


def find_root() -> Path:
    """Localiza a raiz do projeto pelo marcador .git."""
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / '.git').exists():
            return p
    return Path.cwd()


def extrair_shapefile(zip_path: Path, extract_dir: Path) -> Path:
    """Extrai o ZIP dos setores censitários e retorna o caminho do .shp encontrado.

    Args:
        zip_path: Caminho para o arquivo ZIP do IBGE.
        extract_dir: Diretório de destino da extração.

    Returns:
        Caminho para o primeiro arquivo .shp encontrado.

    Raises:
        FileNotFoundError: Se o ZIP não existir ou não contiver .shp.
    """
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)
    print(f'Arquivos extraídos em: {extract_dir}')

    shp_files = [
        Path(root) / fname
        for root, _, files in os.walk(extract_dir)
        for fname in files if fname.endswith('.shp')
    ]
    if not shp_files:
        raise FileNotFoundError('Nenhum arquivo .shp encontrado após extração.')
    return shp_files[0]


def carregar_setores(shp_path: Path) -> gpd.GeoDataFrame:
    """Carrega o shapefile de setores censitários de Pernambuco.

    Args:
        shp_path: Caminho para o arquivo .shp.

    Returns:
        GeoDataFrame com todos os setores do estado.
    """
    gdf = gpd.read_file(shp_path)
    print(f'Total de setores em PE: {len(gdf)} | CRS: {gdf.crs}')
    return gdf


def filtrar_recife(gdf: gpd.GeoDataFrame, cod_recife: str = '2611606') -> gpd.GeoDataFrame:
    """Filtra apenas os setores do município de Recife.

    Args:
        gdf: GeoDataFrame com setores de Pernambuco.
        cod_recife: Código IBGE do município de Recife.

    Returns:
        GeoDataFrame com apenas os setores de Recife.
    """
    recife = gdf[gdf['CD_MUN'] == cod_recife].copy()
    print(f'Setores de Recife encontrados: {len(recife)}')
    return recife


def salvar_geojson(gdf: gpd.GeoDataFrame, output_path: Path) -> None:
    """Salva GeoDataFrame como GeoJSON.

    Args:
        gdf: GeoDataFrame a ser salvo.
        output_path: Caminho de destino do arquivo GeoJSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver='GeoJSON')
    print(f'GeoJSON salvo em: {output_path}')


def main() -> None:
    """Pipeline completo de coleta dos setores censitários de Recife."""
    root = find_root()
    zip_path    = root / 'data' / 'raw' / 'setores_ibge' / 'PE_setores_CD2022.zip'
    extract_dir = root / 'data' / 'raw' / 'setores_ibge' / 'PE_setores_CD2022'
    output_path = root / 'data' / 'raw' / 'setores_ibge' / 'recife_setores.geojson'

    shp_path = extrair_shapefile(zip_path, extract_dir)
    gdf = carregar_setores(shp_path)
    recife = filtrar_recife(gdf)
    salvar_geojson(recife, output_path)
    print('Coleta de setores censitários concluída.')


if __name__ == '__main__':
    main()
