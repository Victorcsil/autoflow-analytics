# PI-IV-A: Pipeline de Big Data Automotiva

## Resumo

Este projeto implementa uma pipeline de dados na AWS para processamento e análise de dados operacionais de uma oficina mecânica. A arquitetura segue o padrão de Data Lake em camadas (raw → processed → results), utilizando processamento distribuído via Apache Spark (AWS Glue) e visualização de dados com Metabase. O objetivo é transformar dados brutos de operações em insights de negócio acionáveis.

## Visão Geral do Projeto

A pipeline de dados automotiva foi construída para gerenciar e analisar grandes volumes de dados de uma oficina mecânica. Ela abrange desde a geração de dados sintéticos até o processamento, limpeza, transformação e análise, culminando em visualizações de negócio. A arquitetura é baseada em serviços gerenciados da AWS, seguindo um modelo de Data Lake para garantir escalabilidade, flexibilidade e governança de dados.

## Tecnologias

A escolha da AWS se deu pela robustez de seu ecossistema de serviços gerenciados para Big Data, com a possibilidade de operar dentro do *free tier* para o volume de dados do projeto.

| Tecnologia | Descrição |
| :--------- | :-------- |
| **AWS S3** | Backbone da arquitetura, atuando como sistema de arquivos distribuído e base do Data Lake em camadas. |
| **AWS Glue** | Serviço ETL (Extract, Transform, Load) serverless que executa jobs Apache Spark para processamento e limpeza de dados. |
| **Apache Spark** | Motor de processamento distribuído utilizado nos jobs do AWS Glue para manipulação e análise de grandes volumes de dados. |
| **Python** | Linguagem de programação utilizada para a geração de dados sintéticos e para o desenvolvimento dos scripts dos jobs AWS Glue. |
| **Docker** | Usado para empacotar e executar o Metabase de forma isolada, facilitando a implantação local da ferramenta de visualização. |
| **Metabase** | Ferramenta de *Business Intelligence* (BI) para visualização e exploração dos dados analisados. |

## Arquitetura do Data Lake

A arquitetura do projeto segue o padrão de Data Lake em camadas, utilizando o Amazon S3 como armazenamento central. Essa abordagem garante isolamento, políticas de ciclo de vida independentes e clareza de responsabilidade para cada etapa da pipeline.

### Camadas de Armazenamento no S3

Três buckets S3 são utilizados para organizar os dados em suas diferentes fases de processamento:

| Bucket | Camada | Formato | Função |
| :---------------------- | :-------- | :------ | :------------------------------------------------ |
| `automative-dev-piiva` | `raw` | CSV | Armazena os dados brutos gerados pela aplicação Python. |
| `automative-prod-piiva` | `processed` | Parquet | Contém os dados limpos, padronizados e transformados, otimizados para consulta. |
| `automative-results-piiva` | `results` | CSV | Armazena os resultados finais das análises de negócio, prontos para consumo por ferramentas de BI. |

A separação em três buckets garante isolamento de permissões, permite configurar políticas de *lifecycle* independentes para cada camada e oferece clareza na responsabilidade de cada etapa da pipeline.

### Otimização com Formato Parquet

O formato Parquet é adotado na camada `processed` por suas vantagens sobre o CSV, especialmente para análises em larga escala:

-   **Consultas mais rápidas**: Formato colunar permite que motores de consulta (como Athena) leiam apenas as colunas necessárias, acelerando queries em até 10x.
-   **Compressão eficiente**: Oferece compressão automática, resultando em arquivos aproximadamente 70% menores que equivalentes em CSV.
-   **Schema embutido**: O schema dos dados é armazenado no próprio arquivo, eliminando a necessidade de inferência de schema.

### Estrutura de Pastas no S3

Os dados são organizados dentro dos buckets S3 em pastas por entidade:

```
automative-dev-piiva/
├── clientes/
│   └── clientes.csv
├── ordens/
│   └── ordens.csv
├── pecas/
│   └── pecas.csv
└── estoque/
    └── movimentacao_estoque.csv

automative-prod-piiva/
├── clientes/
│   ├── part-00000-xxx.parquet
│   └── part-00001-xxx.parquet
├── ordens/
│   ├── part-00000-yyy.parquet
│   └── part-00001-yyy.parquet
...
```

## Configuração e Instalação

### Requisitos

-   Docker e Docker Compose (para Metabase)
-   Python 3.x
-   Credenciais AWS configuradas (para acesso ao S3)

### Configuração do Metabase Local

O Metabase pode ser executado localmente usando Docker e Docker Compose:

1.  **Navegue** até a pasta `infra/`.
2.  **Construa e inicie** o contêiner do Metabase:
    ```bash
    docker-compose up --build -d
    ```
    Este comando irá construir a imagem Docker baseada no `Dockerfile` fornecido e iniciar o serviço Metabase em segundo plano.
3.  **Acesse o Metabase**: Abra seu navegador e navegue para `http://localhost:3000`.

**Detalhes da Configuração Docker:**

-   A imagem base é `metabase/metabase:latest`.
-   A porta `3000` é exposta e mapeada para a porta `3000` do host.
-   Variáveis de ambiente `MB_DB_TYPE=h2` e `JAVA_TIMEZONE=America/Sao_Paulo` são definidas no `Dockerfile` e `docker-compose.yaml`.
-   Um volume `metabase-data` é criado para persistir os dados do Metabase.

### Variáveis de Ambiente

Para a geração de dados e interação com a AWS, são esperadas as seguintes variáveis de ambiente, tipicamente configuradas em um arquivo `.env` ou diretamente no ambiente:

-   `AWS_REGION`: Região da AWS (ex: `us-east-2`)
-   `BUCKET_RAW`: Nome do bucket S3 para dados brutos (ex: `automative-dev-piiva`)
-   `AWS_ACCESS_KEY_ID`: Sua chave de acesso AWS
-   `AWS_SECRET_ACCESS_KEY`: Sua chave secreta AWS

## Geração de Dados Sintéticos

O script `data/generate_data.py` é responsável por criar dados sintéticos de clientes, ordens de serviço, peças e estoque, utilizando a biblioteca `Faker`. Estes dados são então carregados para o bucket S3 `automative-dev-piiva`.

Para executar o gerador de dados:

1.  Certifique-se de que as variáveis de ambiente AWS estão configuradas.
2.  Instale as dependências Python (pandas, boto3, faker, python-dotenv).
3.  Execute o script:
    ```bash
    python data/generate_data.py
    ```

O script gera os seguintes conjuntos de dados e os carrega para S3:
-   `clientes.csv`
-   `ordens.csv`
-   `pecas.csv`
-   `movimentacao_estoque.csv`

## Processamento de Dados (AWS Glue Job: `automotive-clean-job`)

O job `pipeline/automotive-clean-job.py` é um script Python/Spark executado no AWS Glue. Ele é responsável por ler os dados brutos (CSV) da camada `raw`, aplicar transformações de limpeza e padronização, e salvar os dados processados (Parquet) na camada `processed`.

Exemplos de transformações realizadas:
-   Remoção de duplicatas (`dropDuplicates`).
-   Filtros para remover registros inválidos (`filter`).
-   Normalização de strings (ex: `trim`, `upper`, `initcap`).
-   Conversão de tipos de dados (`cast` para `IntegerType`, `DoubleType`, `DateType`).
-   Cálculo de novas colunas (ex: `margem_pct` para peças).

## Análise de Dados (AWS Glue Job: `automotive-analysis-job`)

O job `pipeline/automotive-analysis-job.py` é outro script Python/Spark executado no AWS Glue. Ele lê os dados limpos e transformados (Parquet) da camada `processed`, realiza análises de negócio e salva os resultados (CSV) na camada `results`.

Exemplos de análises geradas:
-   **Receita por tipo de serviço**: Agrega o total de ordens, receita total, ticket médio e média de dias por serviço.
-   **Receita mensal**: Calcula o total de ordens, receita total e ticket médio por ano e mês.
-   **Top 10 mecânicos por receita**: Identifica os mecânicos que geraram mais receita.

## Visualização de Dados

O Metabase, configurado via Docker, é a ferramenta utilizada para visualizar e explorar os resultados das análises. Ele pode se conectar aos dados na camada `results` (ou `processed`) do S3, permitindo a criação de dashboards e relatórios interativos para monitorar o desempenho da oficina.

## Estrutura do Projeto

A organização do repositório é a seguinte:

```
.
├── .gitignore
├── README.md
├── data/
│   └── generate_data.py
├── docs/
│   ├── tecnico.md
│   └── (outros arquivos de documentação)
├── infra/
│   ├── Dockerfile
│   └── docker-compose.yaml
└── pipeline/
    ├── automative-analysis-job.py
    └── automative-clean-job.py
```

| Caminho | Conteúdo Principal |
| :------ | :----------------- |
| `.` (raiz) | Arquivos de configuração de controle de versão e documentação geral. |
| `data/` | Scripts Python para geração de dados sintéticos para popular o Data Lake. |
| `docs/` | Documentação técnica detalhada sobre a arquitetura e componentes do projeto. |
| `infra/` | Arquivos de configuração para infraestrutura, como `Dockerfile` e `docker-compose.yaml` para o Metabase. |
| `pipeline/` | Scripts Python/Spark dos jobs AWS Glue para limpeza e análise de dados. |