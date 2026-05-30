"""Limpeza e enriquecimento geográfico dos dados de renda do IBGE.

Extrai o ZIP de renda por setor censitário, filtra Recife, faz join
com a geometria e salva data/processed/recife_renda.geojson.
"""

import glob
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd


def find_root() -> Path:
    """Localiza a raiz do projeto pelo marcador .git."""
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / '.git').exists():
            return p
    return Path.cwd()


def extrair_csv_renda(zip_path: Path, extract_dir: Path) -> Path:
    """Extrai o ZIP de renda e retorna o caminho do CSV encontrado.

    Args:
        zip_path: Caminho para o ZIP com dados de renda do IBGE.
        extract_dir: Diretório de destino da extração.

    Returns:
        Caminho para o primeiro CSV encontrado após extração.
    """
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)

    csv_files = glob.glob(str(extract_dir / '**' / '*.csv'), recursive=True)
    if not csv_files:
        raise FileNotFoundError('Nenhum CSV encontrado após extração.')
    print(f'CSV encontrado: {csv_files[0]}')
    return Path(csv_files[0])


def carregar_csv_renda(csv_path: Path) -> tuple[pd.DataFrame, str]:
    """Carrega o CSV de renda e detecta a coluna de código do setor.

    Args:
        csv_path: Caminho para o CSV de renda.

    Returns:
        Tupla (DataFrame, nome_coluna_setor).
    """
    df = pd.read_csv(csv_path, sep=';', dtype=str, encoding='latin-1')
    candidatas = [c for c in df.columns if any(k in c.lower() for k in ('setor', 'geocod', 'cod'))]
    col_setor = candidatas[0] if candidatas else df.columns[0]
    print(f'CSV carregado: {len(df)} linhas | coluna setor: "{col_setor}"')
    return df, col_setor


def filtrar_recife(df: pd.DataFrame, col_setor: str, cod_recife: str = '2611606') -> pd.DataFrame:
    """Filtra linhas cujos 7 primeiros dígitos do código correspondem a Recife.

    Args:
        df: DataFrame com dados de renda por setor.
        col_setor: Nome da coluna com o código do setor.
        cod_recife: Código IBGE do município de Recife (7 dígitos).

    Returns:
        DataFrame filtrado para Recife.
    """
    df[col_setor] = df[col_setor].astype(str).str.strip()
    df_recife = df[df[col_setor].str[:7] == cod_recife].copy()
    print(f'Setores de Recife encontrados: {len(df_recife)}')
    return df_recife


def carregar_geojson_setores(geo_path: Path) -> tuple[gpd.GeoDataFrame, str]:
    """Carrega o GeoJSON de setores e detecta a coluna de código.

    Args:
        geo_path: Caminho para o GeoJSON de setores de Recife.

    Returns:
        Tupla (GeoDataFrame, nome_coluna_setor).
    """
    if not geo_path.exists():
        raise FileNotFoundError(
            f'GeoJSON não encontrado: {geo_path}\n'
            'Execute src/coleta/coleta_renda.py primeiro.'
        )
    gdf = gpd.read_file(geo_path)
    candidatas = [c for c in gdf.columns if any(k in c.lower() for k in ('setor', 'geocod'))]
    col_geo = candidatas[0] if candidatas else 'CD_SETOR'
    gdf[col_geo] = gdf[col_geo].astype(str).str.strip()
    print(f'GeoJSON carregado: {len(gdf)} setores | coluna: "{col_geo}"')
    return gdf, col_geo


def join_renda_geo(
    gdf: gpd.GeoDataFrame,
    df_renda: pd.DataFrame,
    col_geo: str,
    col_renda: str,
) -> gpd.GeoDataFrame:
    """Join entre geometria dos setores e dados de renda pelo código do setor.

    Args:
        gdf: GeoDataFrame com geometria dos setores.
        df_renda: DataFrame com dados de renda.
        col_geo: Coluna de código no GeoDataFrame.
        col_renda: Coluna de código no DataFrame de renda.

    Returns:
        GeoDataFrame enriquecido com dados de renda.
    """
    df_renda[col_renda] = df_renda[col_renda].astype(str).str.strip()
    result = gdf.merge(df_renda, left_on=col_geo, right_on=col_renda, how='left')
    com_renda = result[col_renda].notna().sum()
    print(f'Join concluído: {len(result)} setores | com renda: {com_renda}')
    return result


def salvar_geojson(gdf: gpd.GeoDataFrame, output_path: Path) -> None:
    """Salva GeoDataFrame como GeoJSON.

    Args:
        gdf: GeoDataFrame a ser salvo.
        output_path: Caminho de destino.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver='GeoJSON')
    print(f'GeoJSON salvo em: {output_path}')


def main() -> None:
    """Pipeline completo de limpeza e join dos dados de renda."""
    root = find_root()
    zip_path    = root / 'data' / 'raw' / 'renda_ibge' / 'Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip'
    extract_dir = root / 'data' / 'raw' / 'renda_ibge' / 'extraido'
    geo_path    = root / 'data' / 'raw' / 'setores_ibge' / 'recife_setores.geojson'
    output_path = root / 'data' / 'processed' / 'recife_renda.geojson'

    csv_path = extrair_csv_renda(zip_path, extract_dir)
    df, col_setor = carregar_csv_renda(csv_path)
    df_recife = filtrar_recife(df, col_setor)
    gdf, col_geo = carregar_geojson_setores(geo_path)
    gdf_renda = join_renda_geo(gdf, df_recife, col_geo, col_setor)
    salvar_geojson(gdf_renda, output_path)
    print('Limpeza de renda concluída.')


if __name__ == '__main__':
    main()
