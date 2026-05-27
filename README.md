# 🗺️ Recife em Dados — Índice de Vulnerabilidade Urbana

> Análise urbana integrada de Recife cruzando dados de renda, segurança, mobilidade e infraestrutura para calcular o Índice de Vulnerabilidade Urbana (IVU) dos 94 bairros da cidade.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![GeoPandas](https://img.shields.io/badge/GeoPandas-0.14-green?style=flat-square)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red?style=flat-square&logo=streamlit)
![Status](https://img.shields.io/badge/Status-Em%20desenvolvimento-yellow?style=flat-square)
![Licença](https://img.shields.io/badge/Licença-MIT-lightgrey?style=flat-square)

---

## 📌 Sobre o Projeto

O **Recife em Dados** é um projeto de análise urbana que cruza dados públicos de **renda, segurança, mobilidade e infraestrutura** para calcular o **Índice de Vulnerabilidade Urbana (IVU)** dos 94 bairros da cidade do Recife, Pernambuco.

O objetivo é identificar padrões de desigualdade, regiões críticas e oportunidades de melhoria urbana, entregando um produto de dados com visual profissional e potencial real de uso por gestores públicos, pesquisadores e consultorias.

> "O que os dados revelam sobre a cidade que a olho nu não se vê."

---

## 🎯 Problema Central

**Quais bairros de Recife concentram simultaneamente baixa renda, alta criminalidade e pouco acesso a transporte?**

Essa pergunta guia todas as análises e leva à construção do IVU — um score de 0 a 10 que resume a vulnerabilidade urbana de cada bairro em uma única métrica comparável.

---

## 📊 Dimensões Analisadas

| Dimensão | Descrição | Responsável |
|---|---|---|
| 🏘️ Renda e Desigualdade | Renda per capita, pobreza, IDH por bairro | Rodrigo Torres |
| 🚨 Segurança Pública | Crimes por tipo, localização e horário | Victor Vilela |
| 🚌 Mobilidade Urbana | Cobertura de ônibus e metrô por bairro | Arthur Von Sohsten |
| ⚙️ Pipeline e Dashboard | Integração dos dados e produto final | Rodrigo Torres |

---

## 👥 Equipe

| Nome | Função | Branch |
|---|---|---|
| Rodrigo Torres | Renda/Social + Pipeline/Dashboard | `rodrigo` |
| Victor Vilela | Segurança Pública | `victor` |
| Arthur Von Sohsten | Mobilidade Urbana | `arthur` |

---

## 🗂️ Estrutura do Projeto

```
IVU-Recife/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── raw/              ← dados originais (nunca editar)
│   ├── processed/        ← dados limpos e padronizados
│   └── final/            ← dados prontos para análise e dashboard
│
├── notebooks/
│   ├── rodrigo/          ← renda, análise social e pipeline
│   ├── victor/           ← segurança pública
│   └── arthur/           ← mobilidade urbana
│
├── src/
│   ├── coleta/           ← scripts de download e APIs
│   ├── limpeza/          ← tratamento e padronização de dados
│   └── analise/          ← cálculo do IVU e análises finais
│
├── dashboard/            ← aplicação Streamlit
│   ├── app.py
│   ├── mapa.py
│   └── graficos.py
│
└── docs/
    ├── escopo_rodrigo.md
    ├── escopo_victor.md
    └── escopo_arthur.md
```

---

## 🔀 Branches

| Branch | Responsável | Conteúdo |
|---|---|---|
| `main` | Todos | Apenas versão final aprovada |
| `rodrigo` | Rodrigo Torres | Renda/Social + Pipeline/Dashboard |
| `victor` | Victor Vilela | Segurança Pública |
| `arthur` | Arthur Von Sohsten | Mobilidade Urbana |

> Regra: ninguém commita direto na `main`. Sempre abrir um Pull Request.

---

## ⚙️ Como Rodar o Projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/Rodrigotorres1/IVU-Recife.git
cd IVU-Recife
```

### 2. Mudar para sua branch

```bash
# Rodrigo
git checkout rodrigo

# Victor
git checkout victor

# Arthur
git checkout arthur
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Baixar os dados de cada dimensão

| Integrante | Dado | Fonte |
|---|---|---|
| Rodrigo | Censo IBGE 2022 + Shapefile bairros | censo2022.ibge.gov.br · dados.recife.pe.gov.br |
| Victor | Crimes registrados SSP-PE | seguranca.pe.gov.br · dados.recife.pe.gov.br |
| Arthur | GTFS Grande Recife + OSM | granderecife.pe.gov.br |

> O shapefile dos bairros de Recife é necessário para todos. Baixe primeiro.

### 5. Rodar os notebooks

Cada integrante abre o Jupyter e executa os notebooks na sua pasta em ordem:

```bash
jupyter notebook
```

```
notebooks/rodrigo/01_coleta_ibge.ipynb
notebooks/rodrigo/02_limpeza_renda.ipynb
notebooks/rodrigo/03_analise_social.ipynb

notebooks/victor/01_coleta_ssp.ipynb
notebooks/victor/02_limpeza_crimes.ipynb
notebooks/victor/03_mapa_hotspots.ipynb

notebooks/arthur/01_coleta_gtfs.ipynb
notebooks/arthur/02_cobertura_transporte.ipynb
notebooks/arthur/03_mapa_mobilidade.ipynb
```

### 6. Rodar o dashboard

```bash
cd dashboard
streamlit run app.py
```

---

## 📦 Padrão de Entrega

Cada integrante entrega uma tabela no formato abaixo para o Rodrigo integrar no IVU:

```
bairro          | nota_dimensao | dado_principal
----------------|---------------|------------------
Boa Viagem      | 7.2           | R$ 4.200/mês
Casa Amarela    | 3.1           | R$ 890/mês
Afogados        | 4.5           | R$ 1.100/mês
```

---

## 📅 Cronograma

| Semana | O que fazer |
|---|---|
| 1 | Clonar repositório, instalar bibliotecas, baixar dados |
| 2 e 3 | Cada um limpa e analisa seus dados |
| 4 | Cada um gera sua nota por bairro |
| 5 | Rodrigo integra tudo e monta o dashboard |
| 6 | Revisão, README final e publicação |

---

## 🛠️ Tecnologias

- **Python 3.11**
- **Pandas / GeoPandas** — manipulação de dados tabulares e geoespaciais
- **Folium / Plotly** — mapas interativos e visualizações
- **Streamlit** — dashboard interativo
- **OSMnx** — dados de transporte via OpenStreetMap
- **Jupyter Notebook** — análise exploratória

---

## 📁 Fontes de Dados

| Fonte | Dados | Link |
|---|---|---|
| IBGE Censo 2022 | Renda, população, pobreza | censo2022.ibge.gov.br |
| Dados Abertos Recife | Shapefile bairros, infraestrutura | dados.recife.pe.gov.br |
| SSP-PE | Crimes por tipo e localização | seguranca.pe.gov.br |
| Grande Recife Consórcio | GTFS, rotas de ônibus | granderecife.pe.gov.br |
| OpenStreetMap | Malha viária, pontos de ônibus | openstreetmap.org |
| Base dos Dados | Dados socioeconômicos consolidados | basedosdados.org |

---

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.
