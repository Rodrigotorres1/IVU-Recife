# IVU-Recife — Índice de Vulnerabilidade Urbana

Passo 1 — Cada um clona o repositório

Passo 2 - Depois muda para sua branch:

# Rodrigo 
git checkout rodrigo/renda-social

# Victor
git checkout victor/seguranca

# Arthur
git checkout arthur/mobilidade

Passo 3 — Instalar as bibliotecas: pip install -r requirements.txt

Passo 4 — Cada um baixa seus dados

Integrante   Primeiro dado a baixar              Link
Rodrigo     Shapefile dos bairros de Recife    dados.recife.pe.gov.br
Victor      Crimes registrados SSP-PE          seguranca.pe.gov.br
Arthur         GTFS Grande Recife              granderecife.pe.gov.br

Passo 5 — Criar o primeiro notebook
Cada um cria seu primeiro arquivo na pasta certa:
notebooks/rodrigo/01_coleta_ibge.ipynb
notebooks/victor/01_coleta_ssp.ipynb
notebooks/arthur/01_coleta_gtfs.ipynb
Esse notebook só precisa fazer uma coisa: carregar o dado bruto e mostrar as primeiras linhas com df.head().
