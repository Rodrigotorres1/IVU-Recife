import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from graficos import fig_bairro_detalhe, fig_dimensoes, fig_ivu_completo, fig_ranking
from mapa import mapa_cloropletico

ROOT         = Path(__file__).resolve().parent.parent
DATA_CSV     = ROOT / 'data' / 'final' / 'ivu_final.csv'
DATA_GEOJSON = ROOT / 'data' / 'final' / 'recife_ivu.geojson'

st.set_page_config(
    page_title='IVU Recife',
    page_icon='🏙️',
    layout='wide',
    initial_sidebar_state='expanded',
)


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    return pd.read_csv(DATA_CSV, encoding='utf-8')


df = carregar_dados()

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title('IVU — Recife')
st.sidebar.markdown('**Índice de Vulnerabilidade Urbana**')
st.sidebar.markdown('---')
st.sidebar.markdown(
    'Combina renda, segurança e mobilidade em um score de **0 a 10** por bairro.'
)
st.sidebar.markdown(
    '<p style="font-family:monospace; font-size:0.85em; '
    'background:#1e1e1e; padding:8px 10px; border-radius:4px; '
    'color:#e0e0e0; margin-top:4px;">'
    'IVU = renda×0,4 + seg×0,3 + mob×0,3</p>',
    unsafe_allow_html=True,
)
st.sidebar.markdown('---')
st.sidebar.caption('94 bairros de Recife · Dados de 2025')
st.sidebar.markdown(
    '**Equipe:**  \nRodrigo Torres · Renda  \n'
    'Victor Vilela · Segurança  \nArthur Von Sohsten · Mobilidade'
)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.title('🏙️ IVU Recife — Índice de Vulnerabilidade Urbana')

c1, c2, c3, c4 = st.columns(4)
c1.metric('Bairros avaliados', '94')
c2.metric('IVU médio', f"{df['IVU'].mean():.2f}")
c3.metric(
    'Mais vulnerável',
    df.loc[df['IVU'].idxmin(), 'bairro'],
    f"IVU {df['IVU'].min():.2f}",
    delta_color='off',
)
c4.metric(
    'Menos vulnerável',
    df.loc[df['IVU'].idxmax(), 'bairro'],
    f"IVU {df['IVU'].max():.2f}",
    delta_color='off',
)

st.markdown('---')

# ── Abas ──────────────────────────────────────────────────────────────────────
aba_mapa, aba_ranking, aba_comparativo, aba_busca = st.tabs([
    '🗺️ Mapa', '🏆 Ranking', '📊 Comparativo', '🔍 Busca por bairro',
])

with aba_mapa:
    st.plotly_chart(mapa_cloropletico(DATA_GEOJSON), use_container_width=True)

with aba_ranking:
    fig_top, fig_bottom = fig_ranking(df, n=10)
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(fig_top, use_container_width=True)
    with col_b:
        st.plotly_chart(fig_bottom, use_container_width=True)

    st.markdown('---')
    st.subheader('Ranking completo — 94 bairros')
    st.plotly_chart(fig_ivu_completo(df), use_container_width=True)

with aba_comparativo:
    st.plotly_chart(fig_dimensoes(df), use_container_width=True)

with aba_busca:
    bairro_sel = st.selectbox('Selecione um bairro', sorted(df['bairro'].tolist()))
    row = df[df['bairro'] == bairro_sel].iloc[0]

    st.subheader(bairro_sel)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric('IVU', f"{row['IVU']:.2f}")
    m2.metric('Renda (40%)',      f"{row['nota_renda']:.2f}",      row['dado_renda'])
    m3.metric('Segurança (30%)',  f"{row['nota_seguranca']:.2f}",  row['dado_seguranca'])
    m4.metric('Mobilidade (30%)', f"{row['nota_mobilidade']:.2f}", row['dado_mobilidade'])

    ranking_pos = int(df['IVU'].rank(ascending=False).loc[df['bairro'] == bairro_sel].iloc[0])
    st.info(f'**Posição no ranking:** {ranking_pos}º de 94 bairros')

    st.plotly_chart(fig_bairro_detalhe(row), use_container_width=True)
