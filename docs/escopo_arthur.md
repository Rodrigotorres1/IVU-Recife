# Arthur — Dimensão de Análise: Mobilidade Urbana

**Integrante:** Arthur Von Sohsten  
**Dimensão:** Mobilidade Urbana — cobertura de transporte público por bairro

---

## Fontes de dados

| Fonte | Arquivo bruto | Descrição |
|---|---|---|
| Grande Recife Consórcio — GTFS | `data/raw/gtfs/gtfs_grande_recife.zip` | Feed GTFS com paradas, linhas, viagens e horários do transporte público metropolitano |
| OpenStreetMap via OSMnx | `data/processed/recife_malha_viaria.geojson` | Malha viária pedonal de Recife (100.588 segmentos de rua) |
| IBGE — Malhas territoriais 2022 | shapefile de bairros de Recife | Polígonos dos 94 bairros para cruzamento espacial |

### Arquivos dentro do GTFS

| Arquivo | Descrição |
|---|---|
| `stops.txt` | Paradas de ônibus (id, nome, latitude, longitude) — 7.148 paradas totais |
| `routes.txt` | Linhas de ônibus — 393 linhas |
| `trips.txt` | Viagens por linha |
| `stop_times.txt` | Horários por parada |

---

## Notebooks

### `01_coleta_gtfs.ipynb`
- Baixa o ZIP do GTFS do Grande Recife Consórcio
- Extrai e lê `stops.txt` (7.148 paradas) e `routes.txt` (393 linhas)
- Filtra as paradas dentro da bounding box de Recife — **4.748 paradas**
- Baixa a malha viária pedonal via OSMnx (100.588 segmentos)
- Salva `data/processed/recife_paradas.geojson` e `data/processed/recife_malha_viaria.geojson`

### `02_cobertura_transporte.ipynb`
- Projeta paradas e bairros para EPSG:31985 (SIRGAS/UTM zona 25S) para cálculos métricos
- Aplica buffer euclidiano de 500m em cada parada
- Faz interseção dos buffers com os polígonos dos bairros
- Calcula: número de paradas, área coberta (km²), percentual de cobertura e densidade de paradas/km²
- Identifica bairros sem nenhuma parada dentro de 500m
- Salva `data/processed/recife_mobilidade.geojson`

### `03_mapa_mobilidade.ipynb`
- Gera mapa coroplético estático (matplotlib) dos bairros coloridos pela nota de mobilidade
- Gera mapa coroplético interativo (Folium) com tooltip por bairro
- Gera gráfico de barras interativo (Plotly) com ranking dos 94 bairros
- Calcula a nota de 0 a 10 por normalização min-max sobre a densidade de paradas
- Salva `data/processed/mobilidade_por_bairro.csv`

---

## Arquivos gerados

| Arquivo | Features | Descrição |
|---|---|---|
| `data/processed/recife_paradas.geojson` | 4.748 | Paradas de ônibus filtradas dentro de Recife (CRS: EPSG:4326) |
| `data/processed/recife_malha_viaria.geojson` | 100.588 | Segmentos de rua pedestres via OSMnx (CRS: EPSG:4326) |
| `data/processed/recife_mobilidade.geojson` | 94 | Bairros com métricas de cobertura e nota de mobilidade (CRS: EPSG:4674) |
| `data/processed/mobilidade_por_bairro.csv` | 94 | Nota 0–10 por bairro com número de paradas como dado principal |

---

## Metodologia

### Buffer euclidiano de 500m
Para cada parada de ônibus, cria-se um círculo de 500m de raio no plano projetado (EPSG:31985). A área de sobreposição de todos os buffers com cada bairro determina a **área coberta** e o **percentual de cobertura**.

A distância de 500m segue o padrão **IBGE/WRI** para acessibilidade a transporte público a pé. A diferença em relação a isócronas de rede viária é de aproximadamente 10–15% — aceitável para análise comparativa entre bairros.

### Densidade de paradas por km²
Métrica principal de normalização:

```
densidade_paradas = num_paradas / area_km2
```

Usada como base para a nota porque bairros muito grandes com muitas paradas dispersas têm acesso real menor do que bairros pequenos e densos.

### Nota de 0 a 10 (normalização min-max)

```
nota = (densidade - densidade_min) / (densidade_max - densidade_min) × 10
```

- Bairro com **menor densidade** (Pau Ferro — 0 paradas): nota **0,00**
- Bairro com **maior densidade** (Santo Antônio — 55 paradas, área pequena): nota **10,00**
- Média do município: nota **2,06** (distribuição assimétrica — 77 de 94 bairros têm nota < 3)

> **Nota metodológica:** Santo Antônio é um bairro de área reduzida no centro histórico com alta concentração de paradas, o que gera nota máxima por normalização min-max. O 2º colocado (Alto Santa Terezinha) tem nota 4,79. Isso reflete a realidade da concentração do transporte no centro da cidade.

---

## Estrutura do mobilidade_por_bairro.csv

```
bairro,nota_dimensao,dado_principal
Santo Antônio,10.0,55 paradas
Alto Santa Terezinha,4.79,16 paradas
Mangueira,3.58,12 paradas
...
Guabiraba,0.05,24 paradas
Pau Ferro,0.0,0 paradas
```

| Coluna | Tipo | Descrição |
|---|---|---|
| `bairro` | string | Nome do bairro (`NM_BAIRRO` do IBGE) |
| `nota_dimensao` | float (0–10) | Nota calculada por normalização min-max sobre `densidade_paradas` |
| `dado_principal` | string | Número de paradas de ônibus dentro do bairro |

O arquivo contém **94 bairros**, alinhados exatamente com `notas_renda.csv` (100% de correspondência por nome).
