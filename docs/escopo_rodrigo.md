# Rodrigo — Dimensão de Análise: Renda

**Integrante:** Rodrigo  
**Dimensão:** Renda por bairro — Censo IBGE 2022

---

## Fontes de dados

| Fonte | Arquivo bruto | Descrição |
|---|---|---|
| IBGE — Malhas territoriais 2022 | `data/raw/setores_ibge/PE_setores_CD2022.zip` | Shapefile com geometria de todos os setores censitários de Pernambuco |
| IBGE — Agregados por setores (renda) | `data/raw/renda_ibge/Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip` | CSV nacional com variáveis de renda do responsável por domicílio — Censo 2022 |

### Variáveis utilizadas do CSV de renda

| Variável | Descrição |
|---|---|
| `CD_SETOR` | Código do setor censitário (15 dígitos) |
| `V06001` | Total de responsáveis por domicílio no setor |
| `V06003` | Média de moradores por domicílio |
| `V06004` | Rendimento nominal médio mensal do responsável (R$) |
| `V06006` | Rendimento nominal mediano mensal do responsável (R$) |

---

## Notebooks

### `01_coleta_shapefile.ipynb`
- Extrai o ZIP do IBGE com setores censitários de Pernambuco
- Filtra os setores de Recife pelo código do município (`CD_MUN = 2611606`)
- Resultado: **2.835 setores** censitários urbanos
- Plota mapa dos setores para validação visual
- Salva `data/raw/setores_ibge/recife_setores.geojson`

### `02_limpeza_renda.ipynb`
- Extrai o CSV de renda nacional (458.772 linhas)
- Filtra os **2.814 setores de Recife** (primeiros 7 dígitos do `CD_SETOR = 2611606`)
- Realiza join pelo `CD_SETOR` com o GeoJSON de geometrias — **zero setores sem correspondência**
- Salva `data/processed/recife_renda.geojson` com 36 colunas (geometria + renda)

### `03_analise_social.ipynb`
- Agrega os setores por bairro (`NM_BAIRRO`) — **94 bairros** após remoção de 1 linha com `NM_BAIRRO = NaN`
- Calcula renda média ponderada, mediana e % abaixo da linha de pobreza
- Gera mapa coroplético interativo (Plotly) e rankings top 10
- Calcula nota de 0 a 10 por normalização min-max
- Salva `data/processed/recife_renda_bairros.csv` e `data/processed/notas_renda.csv`

---

## Arquivos gerados

| Arquivo | Linhas | Descrição |
|---|---|---|
| `data/raw/setores_ibge/recife_setores.geojson` | 2.835 | Geometria dos setores censitários de Recife |
| `data/processed/recife_renda.geojson` | 2.835 | Setores com geometria + variáveis de renda do IBGE |
| `data/processed/recife_renda_bairros.csv` | 94 | Agregação por bairro: renda média, mediana, % pobreza |
| `data/processed/notas_renda.csv` | 94 | Nota 0–10 por bairro com renda formatada |

---

## Metodologia

### Renda média por bairro
Média ponderada de `V06004` (renda média do responsável por setor), usando `V06001` (total de responsáveis) como peso:

```
renda_media_bairro = Σ(V06004 × V06001) / Σ(V06001)
```

### % abaixo da linha de pobreza
Estimativa de renda per capita por setor:

```
renda_percapita = V06004 / V06003
```

Setores com `renda_percapita < R$ 436/mês` são classificados como em situação de pobreza (critério Bolsa Família 2022). O percentual por bairro é calculado como a fração de responsáveis nesses setores sobre o total do bairro.

### Nota de 0 a 10 (normalização min-max)
Transforma a `renda_media` de cada bairro em uma nota comparativa dentro do município:

```
nota = (renda_media - renda_min) / (renda_max - renda_min) × 10
```

- Bairro com **menor renda** (Recife — R$ 1.116,60): nota **0,00**
- Bairro com **maior renda** (Jaqueira — R$ 16.337,43): nota **10,00**
- Média do município: R$ 4.068,80 → nota **1,94**

---

## Estrutura do notas_renda.csv

```
bairro,nota_dimensao,dado_principal
Jaqueira,10.0,"R$ 16.337,43"
Casa Forte,8.67,"R$ 14.308,91"
Parnamirim,8.07,"R$ 13.405,17"
...
Ilha Joana Bezerra,0.01,"R$ 1.134,42"
Recife,0.0,"R$ 1.116,60"
```

| Coluna | Tipo | Descrição |
|---|---|---|
| `bairro` | string | Nome do bairro (`NM_BAIRRO` do IBGE) |
| `nota_dimensao` | float (0–10) | Nota calculada por normalização min-max sobre `renda_media` |
| `dado_principal` | string | Renda média do responsável formatada em reais (padrão brasileiro) |

O arquivo contém **94 bairros**, ordenados da maior para a menor nota.
