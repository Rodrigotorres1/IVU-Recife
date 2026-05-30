"""Cálculo do Índice de Vulnerabilidade Urbana (IVU) por bairro de Recife.

Une as três dimensões (renda, segurança, mobilidade), calcula o IVU com
os pesos definidos, faz join com o GeoJSON de bairros e salva os arquivos
finais para o dashboard.

Fórmula:
    IVU = (nota_renda × 0.4) + (nota_seguranca × 0.3) + (nota_mobilidade × 0.3)
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

PESOS = {'renda': 0.4, 'seguranca': 0.3, 'mobilidade': 0.3}


def find_root() -> Path:
    """Localiza a raiz do projeto pelo marcador .git."""
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / '.git').exists():
            return p
    return Path.cwd()


def carregar_notas(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carrega os três arquivos de notas das dimensões.

    Args:
        root: Raiz do projeto.

    Returns:
        Tupla (notas_renda, notas_seguranca, notas_mobilidade).
    """
    processed = root / 'data' / 'processed'
    renda      = pd.read_csv(processed / 'notas_renda.csv')
    seguranca  = pd.read_csv(processed / 'notas_seguranca.csv')
    mobilidade = pd.read_csv(processed / 'mobilidade_por_bairro.csv')
    print(f'Arquivos carregados: renda={len(renda)}, seg={len(seguranca)}, mob={len(mobilidade)} bairros')
    return renda, seguranca, mobilidade


def validar_notas(df: pd.DataFrame, nome: str) -> None:
    """Valida estrutura e integridade de um arquivo de notas.

    Args:
        df: DataFrame a ser validado.
        nome: Identificador do arquivo para mensagens de erro.

    Raises:
        AssertionError: Se alguma validação falhar.
    """
    assert list(df.columns) == ['bairro', 'nota_dimensao', 'dado_principal'], \
        f'Colunas inesperadas em {nome}: {df.columns.tolist()}'
    assert len(df) == 94, f'{nome} tem {len(df)} linhas (esperado 94)'
    assert df.isnull().sum().sum() == 0, f'{nome} tem valores nulos'
    assert df['bairro'].nunique() == 94, f'{nome} tem bairros duplicados'


def calcular_ivu(
    renda: pd.DataFrame,
    seguranca: pd.DataFrame,
    mobilidade: pd.DataFrame,
    pesos: dict = PESOS,
) -> pd.DataFrame:
    """Realiza o merge das três dimensões e calcula o IVU ponderado.

    Args:
        renda: DataFrame com notas de renda.
        seguranca: DataFrame com notas de segurança.
        mobilidade: DataFrame com notas de mobilidade.
        pesos: Dicionário com pesos por dimensão (devem somar 1.0).

    Returns:
        DataFrame com 94 bairros, notas por dimensão e IVU calculado.
    """
    df = renda.rename(columns={'nota_dimensao': 'nota_renda', 'dado_principal': 'dado_renda'})
    df = df.merge(
        seguranca.rename(columns={'nota_dimensao': 'nota_seguranca', 'dado_principal': 'dado_seguranca'}),
        on='bairro',
    )
    df = df.merge(
        mobilidade.rename(columns={'nota_dimensao': 'nota_mobilidade', 'dado_principal': 'dado_mobilidade'}),
        on='bairro',
    )
    df['IVU'] = (
        df['nota_renda']      * pesos['renda']     +
        df['nota_seguranca']  * pesos['seguranca'] +
        df['nota_mobilidade'] * pesos['mobilidade']
    ).round(2)
    df = df.sort_values('IVU', ascending=False).reset_index(drop=True)
    print(f'IVU calculado: {len(df)} bairros | min={df["IVU"].min():.2f} | max={df["IVU"].max():.2f} | média={df["IVU"].mean():.2f}')
    return df


def validar_ivu(df: pd.DataFrame, pesos: dict = PESOS) -> None:
    """Valida o DataFrame com IVU calculado.

    Args:
        df: DataFrame resultante de calcular_ivu.
        pesos: Pesos usados no cálculo.

    Raises:
        AssertionError: Se alguma validação falhar.
    """
    assert len(df) == 94, f'Merge perdeu bairros: {len(df)} (esperado 94)'
    assert df['IVU'].between(0, 10).all(), 'IVU fora do intervalo [0, 10]'
    assert df.isnull().sum().sum() == 0, 'Valores nulos no DataFrame final'
    assert df['bairro'].nunique() == 94, 'Bairros duplicados no resultado'
    assert abs(sum(pesos.values()) - 1.0) < 1e-9, f'Pesos não somam 1: {sum(pesos.values())}'
    print('Todas as validações passaram.')


def join_geojson(df: pd.DataFrame, geojson_path: Path) -> gpd.GeoDataFrame:
    """Faz join do IVU calculado com os polígonos de bairro do GeoJSON.

    Args:
        df: DataFrame com IVU por bairro (coluna 'bairro').
        geojson_path: Caminho para recife_mobilidade.geojson.

    Returns:
        GeoDataFrame com polígonos e IVU por bairro.
    """
    gdf = gpd.read_file(geojson_path)
    gdf_ivu = gdf[['NM_BAIRRO', 'geometry']].merge(
        df.rename(columns={'bairro': 'NM_BAIRRO'}),
        on='NM_BAIRRO',
        how='left',
    )
    sem_ivu = gdf_ivu['IVU'].isna().sum()
    if sem_ivu:
        print(f'ATENÇÃO: {sem_ivu} bairros sem IVU no GeoJSON.')
    else:
        print(f'Join perfeito: {len(gdf_ivu)} bairros com IVU.')
    return gdf_ivu


def salvar_resultados(
    df: pd.DataFrame,
    gdf_ivu: gpd.GeoDataFrame,
    root: Path,
) -> None:
    """Salva os arquivos finais do pipeline IVU.

    Gera:
        - data/final/ivu_final.csv
        - data/final/recife_ivu.geojson

    Args:
        df: DataFrame com IVU e notas por bairro.
        gdf_ivu: GeoDataFrame com polígonos e IVU.
        root: Raiz do projeto.
    """
    output_dir = root / 'data' / 'final'
    output_dir.mkdir(parents=True, exist_ok=True)

    cols_csv = ['bairro', 'IVU', 'nota_renda', 'nota_seguranca', 'nota_mobilidade',
                'dado_renda', 'dado_seguranca', 'dado_mobilidade']
    df[cols_csv].to_csv(output_dir / 'ivu_final.csv', index=False, encoding='utf-8')
    print(f'Salvo: {output_dir / "ivu_final.csv"}')

    gdf_ivu.to_file(output_dir / 'recife_ivu.geojson', driver='GeoJSON')
    print(f'Salvo: {output_dir / "recife_ivu.geojson"}')


def main() -> None:
    """Pipeline completo de cálculo do IVU."""
    root = find_root()

    renda, seguranca, mobilidade = carregar_notas(root)
    for df, nome in [(renda, 'renda'), (seguranca, 'seguranca'), (mobilidade, 'mobilidade')]:
        validar_notas(df, nome)

    df = calcular_ivu(renda, seguranca, mobilidade)
    validar_ivu(df)

    geojson_path = root / 'data' / 'processed' / 'recife_mobilidade.geojson'
    gdf_ivu = join_geojson(df, geojson_path)

    salvar_resultados(df, gdf_ivu, root)
    print('Cálculo do IVU concluído.')


if __name__ == '__main__':
    main()
