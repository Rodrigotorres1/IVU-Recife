# Victor - Dimensao de Analise: Seguranca Publica

**Integrante:** Victor Vilela  
**Dimensao:** Seguranca publica por bairro - violencia armada em Recife

---

## Fontes de dados

| Fonte | Arquivo bruto | Descricao |
|---|---|---|
| SDS-PE | `data/raw/seguranca/microdados_cvli.xlsx` | Microdados oficiais de CVLI por municipio, disponiveis ate abril de 2026 |
| SDS-PE | `data/raw/seguranca/microdados_cvp.xlsx` | Microdados oficiais de CVP por municipio, disponiveis ate abril de 2026 |
| Fogo Cruzado API | `data/raw/seguranca/fogo_cruzado_recife_2025.csv` | Ocorrencias de tiroteios/disparos em Recife com bairro, coordenadas, vitimas e motivo |

Observacao metodologica: a analise foi feita a partir dos sites de seguranca publica solicitados para o tema, combinando os microdados oficiais da SDS-PE com a API aberta do Fogo Cruzado. Os microdados publicos da SDS-PE baixados para o projeto estao agregados no nivel de municipio; por isso, para gerar uma nota por bairro e o mapa de hotspots, foi usada a base do Fogo Cruzado, que possui granularidade de bairro e geolocalizacao.

---

## Notebooks

### `01_coleta_ssp.ipynb`
- Baixa os microdados oficiais de CVLI e CVP da SDS-PE.
- Consulta a API do Fogo Cruzado para Recife no ano-base 2025.
- Salva `data/raw/seguranca/fogo_cruzado_recife_2025.csv`.

### `02_limpeza_crimes.ipynb`
- Padroniza datas, horarios, bairros, coordenadas e contagens de vitimas.
- Normaliza os nomes dos bairros para a lista de bairros de Recife usada no projeto.
- Salva `data/processed/ocorrencias_seguranca_recife.csv`.

### `03_mapa_hotspots.ipynb`
- Agrega ocorrencias por bairro.
- Calcula a nota de seguranca de 0 a 10.
- Gera o mapa de calor em `docs/mapa_hotspots_seguranca.html`.
- Salva `data/processed/notas_segurança.csv` e `data/processed/notas_seguranca.csv`.

Todos os CSVs gerados pela parte de seguranca usam codificacao `utf-8-sig` e separador `;`, para abrir corretamente no Excel em portugues.

---

## Arquivos gerados

| Arquivo | Descricao |
|---|---|
| `data/processed/ocorrencias_seguranca_recife.csv` | Ocorrencias limpas, uma linha por registro |
| `data/processed/recife_seguranca_bairros.csv` | Agregacao por bairro da analise de seguranca, com cada indicador em uma coluna |
| `data/processed/seguranca_por_bairro.csv` | Agregacao por bairro com ocorrencias, mortos, feridos, baleados e indice de risco |
| `data/processed/notas_segurança.csv` | Arquivo final da dimensao seguranca com bairro, nota e indicador principal |
| `data/processed/notas_seguranca.csv` | Versao sem acento no nome para facilitar abertura em alguns sistemas |
| `data/processed/seguranca_contexto_sds_recife_2025.csv` | Totais municipais de CVLI e CVP da SDS-PE para contextualizacao |
| `docs/mapa_hotspots_seguranca.html` | Heatmap interativo das ocorrencias georreferenciadas |

---

## Metodologia

### Ano-base
Foi usado **2025**, por ser o ultimo ano completo disponivel nas bases consultadas em maio de 2026. Os dados de 2026 existem apenas ate abril, entao nao foram usados na nota final para evitar comparacao de ano parcial.

### Indice de risco
Para cada bairro:

```text
indice_risco = ocorrencias + 2 * mortos + feridos + 0.5 * acoes_policiais + 3 * chacinas
```

A morte recebe peso maior que ferimento, e chacina aumenta o peso por indicar evento extremo. Acoes policiais entram com peso menor porque indicam contexto de confronto/operacao.

### Nota de 0 a 10
A nota usa normalizacao min-max invertida sobre o indice de risco, porque menor violencia significa melhor seguranca:

```text
nota = 10 - ((indice_risco - risco_min) / (risco_max - risco_min) * 10)
```

- Bairro com menor risco: nota proxima de **10**.
- Bairro com maior risco: nota **0**.

---

## Estrutura do notas_segurança.csv

```csv
bairro;nota_dimensao;dado_principal
Aflitos;10.0;"0 ocorrencias e 0 baleados"
Nova Descoberta;0.0;"22 ocorrencias e 33 baleados"
```

| Coluna | Tipo | Descricao |
|---|---|---|
| `bairro` | string | Nome do bairro padronizado para os 94 bairros de Recife |
| `nota_dimensao` | float (0-10) | Nota calculada por normalizacao min-max invertida sobre o indice de risco |
| `dado_principal` | string | Resumo formatado com ocorrencias e pessoas baleadas |
