# Pipeline e Dashboard — Integração do IVU

**Responsável:** Rodrigo Torres  
**Fase:** Pipeline de integração + Dashboard Streamlit

---

## Objetivo

Integrar as três dimensões de análise (renda, segurança e mobilidade) em um único score por bairro — o **Índice de Vulnerabilidade Urbana (IVU)** — e entregar um dashboard interativo com mapas, rankings e comparativos.

---

## Status atual

| Dimensão | Responsável | CSV de entrada | Status |
|---|---|---|---|
| Renda | Rodrigo | `notas_renda.csv` | CONCLUÍDO |
| Mobilidade | Arthur | `mobilidade_por_bairro.csv` | CONCLUÍDO |
| Segurança | Victor | `notas_seguranca.csv` | CONCLUÍDO |

---

## Fórmula do IVU

```
IVU = (nota_renda × 0.4) + (nota_seguranca × 0.3) + (nota_mobilidade × 0.3)
```

| Dimensão | Peso | Justificativa |
|---|---|---|
| Renda | 40% | Determinante estrutural principal da vulnerabilidade |
| Segurança | 30% | Impacto direto na qualidade de vida e no território |
| Mobilidade | 30% | Acesso a oportunidades (trabalho, saúde, educação) |

Resultado: score de **0 a 10** por bairro, onde 0 = máxima vulnerabilidade e 10 = mínima vulnerabilidade.

---

## Entradas do pipeline

| Arquivo | Colunas | Bairros |
|---|---|---|
| `data/processed/notas_renda.csv` | bairro, nota_dimensao, dado_principal | 94 |
| `data/processed/mobilidade_por_bairro.csv` | bairro, nota_dimensao, dado_principal | 94 |
| `data/processed/notas_seguranca.csv` | bairro, nota_dimensao, dado_principal | 94 |
| `data/processed/recife_mobilidade.geojson` | NM_BAIRRO + geometria dos bairros | 94 |

Padrão obrigatório dos CSVs de entrada:
- Coluna `bairro` em Title Case com acentos (ex: `Boa Viagem`, `Santo Antônio`)
- Coluna `nota_dimensao` float entre 0 e 10, sem nulos
- Exatamente 94 bairros, sem duplicados

---

## Notebook do pipeline

`notebooks/pipeline/04_pipeline_ivu.ipynb`:
- Carrega os 3 CSVs de notas
- Valida: 94 bairros, sem nulos, notas entre 0 e 10, nomes alinhados
- Calcula o IVU com os pesos acima
- Faz join com o GeoJSON de bairros para o mapa
- Salva `data/final/ivu_final.csv` e `data/final/recife_ivu.geojson`

---

## Saídas do pipeline

| Arquivo | Descrição |
|---|---|
| `data/final/ivu_final.csv` | Score IVU por bairro com as 3 notas componentes |
| `data/final/recife_ivu.geojson` | GeoJSON dos 94 bairros com o IVU e as dimensões para o mapa |

Estrutura do `ivu_final.csv`:

```
bairro,IVU,nota_renda,nota_seguranca,nota_mobilidade
Jaqueira,7.2,10.0,6.5,3.6
Boa Viagem,5.4,7.8,4.2,2.1
...
```

---

## Dashboard Streamlit

`dashboard/app.py`:

### Seções planejadas

| Seção | Conteúdo |
|---|---|
| Visão geral | Mapa coroplético do IVU por bairro (Folium/Plotly) |
| Ranking | Top 10 mais vulneráveis e top 10 menos vulneráveis |
| Comparativo | Gráfico de barras com as 3 dimensões por bairro |
| Busca | Selecionar um bairro e ver seu IVU detalhado |

### Arquivos do dashboard

| Arquivo | Responsabilidade |
|---|---|
| `dashboard/app.py` | Aplicação principal Streamlit — layout e navegação |
| `dashboard/mapa.py` | Funções de geração do mapa coroplético interativo |
| `dashboard/graficos.py` | Funções de geração dos gráficos Plotly |

### Como rodar

```bash
cd dashboard
streamlit run app.py
```

---

## Próximos passos

1. Testar o dashboard localmente com `streamlit run app.py`
2. Publicar resultado final
