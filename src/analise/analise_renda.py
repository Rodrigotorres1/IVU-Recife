"""Análise social da dimensão de renda por bairro em Recife.

Agrega setores censitários por bairro, calcula renda média ponderada,
percentual abaixo da linha de pobreza, normaliza em nota 0-10 e salva
data/processed/notas_renda.csv e data/processed/recife_renda_bairros.csv.
"""

import os
from pathlib import Path

import geopandas as gpd
import pandas as pd

LINHA_POBREZA = 436.0  # R$/mês per capita — critério Bolsa Família 2022
COLS_NUM = ['V06001', 'V06002', 'V06003', 'V06004', 'V06005', 'V06006']


def find_root() -> Path:
    """Localiza a raiz do projeto pelo marcador .git."""
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / '.git').exists():
            return p
    return Path.cwd()


def carregar_renda_geojson(input_path: Path) -> gpd.GeoDataFrame:
    """Carrega o GeoJSON de setores com dados de renda.

    Args:
        input_path: Caminho para data/processed/recife_renda.geojson.

    Returns:
        GeoDataFrame com colunas numéricas convertidas.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f'GeoJSON não encontrado: {input_path}\n'
            'Execute src/limpeza/limpeza_renda.py primeiro.'
        )
    gdf = gpd.read_file(input_path)
    for col in COLS_NUM:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors='coerce')
    print(f'Setores carregados: {len(gdf)} | Bairros únicos: {gdf["NM_BAIRRO"].nunique()}')
    return gdf


def agregar_por_bairro(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """Agrega setores censitários por bairro com renda média ponderada.

    Usa V06004 (renda média do responsável) ponderada por V06001
    (total de responsáveis do setor).

    Args:
        gdf: GeoDataFrame com setores de Recife e colunas de renda.

    Returns:
        DataFrame agregado por bairro.
    """
    gdf['renda_pond'] = gdf['V06004'] * gdf['V06001']

    agg = (
        gdf
        .groupby(['CD_BAIRRO', 'NM_BAIRRO'], dropna=False)
        .agg(
            n_setores          = ('CD_SETOR',   'count'),
            total_responsaveis = ('V06001',     'sum'),
            soma_pond          = ('renda_pond', 'sum'),
            mediana_renda      = ('V06006',     'median'),
        )
        .reset_index()
    )
    agg['renda_media'] = (agg['soma_pond'] / agg['total_responsaveis']).round(2)
    agg = agg.drop(columns=['soma_pond'])
    print(f'Bairros agregados: {len(agg)}')
    return agg


def calcular_pobreza(gdf: gpd.GeoDataFrame, agg: pd.DataFrame) -> pd.DataFrame:
    """Calcula o percentual de responsáveis abaixo da linha de pobreza por bairro.

    Args:
        gdf: GeoDataFrame com setores e colunas de renda.
        agg: DataFrame já agregado por bairro.

    Returns:
        DataFrame com colunas resp_pobreza e pct_pobreza adicionadas.
    """
    gdf['renda_percapita'] = gdf['V06004'] / gdf['V06003']
    gdf['em_pobreza']      = gdf['renda_percapita'] < LINHA_POBREZA
    gdf['resp_em_pobreza'] = gdf['em_pobreza'].astype(float) * gdf['V06001']

    agg_pob = (
        gdf
        .groupby(['CD_BAIRRO', 'NM_BAIRRO'], dropna=False)
        .agg(
            resp_pobreza = ('resp_em_pobreza', 'sum'),
            total_resp   = ('V06001',          'sum'),
        )
        .reset_index()
    )
    agg_pob['pct_pobreza'] = (agg_pob['resp_pobreza'] / agg_pob['total_resp'] * 100).round(1)

    result = agg.merge(agg_pob[['NM_BAIRRO', 'resp_pobreza', 'pct_pobreza']], on='NM_BAIRRO', how='left')
    print(f'Bairros com > 0% em pobreza: {(result["pct_pobreza"] > 0).sum()}')
    return result


def calcular_notas(agg: pd.DataFrame) -> pd.DataFrame:
    """Normaliza a renda média em nota de 0 a 10 via min-max.

    Args:
        agg: DataFrame com coluna renda_media.

    Returns:
        DataFrame com coluna nota_dimensao adicionada.
    """
    agg = agg.dropna(subset=['NM_BAIRRO']).reset_index(drop=True)
    renda_min = agg['renda_media'].min()
    renda_max = agg['renda_media'].max()
    agg['nota_dimensao'] = ((agg['renda_media'] - renda_min) / (renda_max - renda_min) * 10).round(2)
    print(f'Notas calculadas: min={agg["nota_dimensao"].min():.2f} | max={agg["nota_dimensao"].max():.2f}')
    return agg


def formatar_brl(valor: float) -> str:
    """Formata valor em reais no padrão brasileiro (R$ 1.234,56).

    Args:
        valor: Valor numérico em reais.

    Returns:
        String formatada no padrão pt-BR.
    """
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def salvar_resultados(agg: pd.DataFrame, root: Path) -> None:
    """Salva os arquivos de saída da dimensão de renda.

    Gera:
        - data/processed/recife_renda_bairros.csv  (agregação completa)
        - data/processed/notas_renda.csv           (entrega para o pipeline)

    Args:
        agg: DataFrame agregado por bairro com notas calculadas.
        root: Raiz do projeto.
    """
    output_dir = root / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV completo de renda por bairro
    agg_out = agg[[
        'CD_BAIRRO', 'NM_BAIRRO', 'n_setores', 'total_responsaveis',
        'renda_media', 'mediana_renda', 'resp_pobreza', 'pct_pobreza',
    ]].copy()
    agg_out.columns = [
        'cd_bairro', 'nm_bairro', 'n_setores', 'total_responsaveis',
        'renda_media_responsavel', 'mediana_renda_responsavel',
        'responsaveis_em_pobreza', 'pct_abaixo_pobreza',
    ]
    agg_out = agg_out.sort_values('renda_media_responsavel', ascending=False).reset_index(drop=True)
    csv_bairros = output_dir / 'recife_renda_bairros.csv'
    agg_out.to_csv(csv_bairros, index=False, encoding='utf-8')
    print(f'Salvo: {csv_bairros}')

    # Arquivo de notas para o pipeline IVU
    notas = pd.DataFrame({
        'bairro':         agg['NM_BAIRRO'],
        'nota_dimensao':  agg['nota_dimensao'],
        'dado_principal': agg['renda_media'].apply(formatar_brl),
    }).sort_values('nota_dimensao', ascending=False).reset_index(drop=True)

    csv_notas = output_dir / 'notas_renda.csv'
    notas.to_csv(csv_notas, index=False, encoding='utf-8')
    print(f'Salvo: {csv_notas} ({len(notas)} bairros)')


def main() -> None:
    """Pipeline completo de análise social da dimensão de renda."""
    root = find_root()
    input_path = root / 'data' / 'processed' / 'recife_renda.geojson'

    gdf = carregar_renda_geojson(input_path)
    agg = agregar_por_bairro(gdf)
    agg = calcular_pobreza(gdf, agg)
    agg = calcular_notas(agg)
    salvar_resultados(agg, root)
    print('Análise de renda concluída.')


if __name__ == '__main__':
    main()
