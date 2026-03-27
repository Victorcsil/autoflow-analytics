# Documentação Técnica — Automotive BigData Pipeline

## Visão Geral

Pipeline de dados construída na AWS para processamento e análise de dados operacionais de uma oficina mecânica. A arquitetura segue o padrão **Data Lake em camadas** (raw → processed → results), com processamento distribuído via Apache Spark (AWS Glue) e visualização via Metabase.

---

## Stack Tecnológica

### Por que AWS?

A AWS foi escolhida por oferecer o ecossistema mais completo de serviços gerenciados para Big Data com free tier funcional. Alternativas como GCP (QuickSight bloqueado em contas novas) e Azure (custo mais elevado para o mesmo setup) foram descartadas. Todos os serviços utilizados operam dentro do free tier para o volume de dados do projeto.

---

## Armazenamento — Amazon S3

O S3 (Simple Storage Service) é o backbone da arquitetura. Funciona como sistema de arquivos distribuído e serve como base do Data Lake.

### Buckets criados

| Bucket | Camada | Formato | Função |
|---|---|---|---|
| `automative-dev-piiva` | raw | CSV | Dados brutos gerados pelo Python |
| `automative-prod-piiva` | processed | Parquet | Dados limpos e transformados |
| `automative-results-piiva` | results | CSV | Output das análises de negócio |

### Por que três buckets separados?

A separação por bucket (em vez de pastas no mesmo bucket) garante:

- **Isolamento de permissões**: o job de limpeza tem acesso de leitura no `dev` e escrita no `prod`, mas não nos `results`. Segue o princípio de menor privilégio.
- **Lifecycle policies independentes**: é possível configurar retenção diferente por camada — dados raw podem expirar em 30 dias, processed ficam indefinidamente.
- **Clareza de responsabilidade**: cada camada tem um dono claro na pipeline.

### Por que Parquet na camada processed?

CSV é linha a linha — para consultar apenas a coluna `valor_total` de 100k registros, o Athena precisa ler o arquivo inteiro. Parquet é **colunar**: o Athena lê apenas as colunas necessárias. Na prática isso significa:

- Queries até 10x mais rápidas para análises agregadas
- Compressão automática (~70% menor que CSV equivalente)
- Schema embutido no arquivo (sem necessidade de inferência)

### Estrutura de pastas no S3

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
│   ├── part-00000-xxx.parquet
│   └── part-00001-xxx.parquet
├── pecas/
│   └── part-00000-xxx.parquet
└── estoque/
    ├── part-00000-xxx.parquet
    └── part-00001-xxx.parquet

automative-results-piiva/
├── receita_por_servico/
├── receita_mensal/
├── top_mecanicos/
├── clientes_recorrentes/
├── pecas_mais_utilizadas/
├── formas_pagamento/
└── athena-output/
```

Os múltiplos arquivos `part-xxxxx` na camada processed são evidência direta do processamento distribuído — cada worker Spark processou uma partição e gravou seu próprio arquivo em paralelo.

---

## Catálogo de Dados — AWS Glue Data Catalog

O Glue Data Catalog é o metastore centralizado que mapeia os arquivos físicos no S3 para tabelas consultáveis via SQL.

### Databases criados

| Database | Aponta para | Tabelas |
|---|---|---|
| `automotive_db` | `automative-dev-piiva/` | clientes, ordens, pecas, estoque |
| `automative_db_prd` | `automative-prod-piiva/` | prd-clientes, prd-ordens, prd-pecas, prd-estoque |
| `automotive_db_results` | `automative-results-piiva/` | receita_por_servico, receita_mensal, top_mecanicos, ... |

### Crawlers

Os Crawlers são processos que inspecionam o S3, inferem o schema dos arquivos e registram as tabelas no catálogo automaticamente. Sem o crawler, o Athena não consegue enxergar os dados.

**Por que um crawler por camada em vez de um único?**

Um único crawler apontando para a raiz do bucket mistura tabelas de diferentes estágios no mesmo database, dificultando o controle de acesso e a navegação. Crawlers separados permitem databases separados com permissões distintas.

---

## Processamento Distribuído — AWS Glue + Apache Spark

O AWS Glue é um serviço de ETL serverless que roda Apache Spark por baixo dos panos. A escolha do Glue em vez de configurar um cluster EMR diretamente foi intencional: o Glue abstrai o provisionamento de infraestrutura, cobranças por segundo de uso e auto-scaling.

### Job 1 — `automotive-clean-job`

**Entrada**: CSV bruto em `automative-dev-piiva/`  
**Saída**: Parquet limpo em `automative-prod-piiva/`  

Lê os dados diretamente do S3 via `spark.read.csv()` (não pelo catálogo, para evitar dependência de schema inferido que pode divergir dos arquivos reais).

**Transformações por tabela:**

```
clientes:
  - dropDuplicates(["cliente_id"])
  - filter: cliente_id e nome não nulos
  - withColumn: nome → UPPER, cidade → initcap, estado → UPPER
  - cast: ano_veiculo → IntegerType, filter entre 1990 e 2025
  - cast: data_cadastro → DateType

pecas:
  - dropDuplicates(["peca_id"])
  - cast: preco_custo, preco_venda → DoubleType
  - filter: preco_venda >= preco_custo (garante margem positiva)
  - withColumn: margem_pct = (venda - custo) / custo * 100

ordens:
  - dropDuplicates(["ordem_id"])
  - cast: valor_servico, valor_peca → DoubleType, datas → DateType
  - filter: data_saida >= data_entrada (consistência temporal)
  - withColumn: valor_total = valor_servico + coalesce(valor_peca, 0)
  - withColumn: dias_servico = datediff(data_saida, data_entrada)
  - withColumn: ano, mes extraídos de data_entrada

estoque:
  - dropDuplicates(["mov_id"])
  - cast: quantidade → IntegerType, data → DateType
  - withColumn: quantidade_signed = quantidade * -1 quando tipo == "Saída"
  - withColumn: ano, mes extraídos de data
```

### Job 2 — `automotive-analysis-job`

**Entrada**: Parquet em `automative-prod-piiva/`  
**Saída**: CSV de análises em `automative-results-piiva/`  

Utiliza `coalesce(1)` na escrita para gerar um único arquivo CSV por análise, facilitando o consumo pelo Athena e Metabase. Em produção com volumes maiores isso seria removido para manter o paralelismo na escrita.

**Análises geradas:**

```
receita_por_servico:
  GROUP BY servico WHERE status = 'Concluído'
  → count(ordem_id), sum(valor_total), avg(valor_total), avg(dias_servico)

receita_mensal:
  GROUP BY ano, mes WHERE status = 'Concluído'
  → count, sum, avg — ordenado cronologicamente

top_mecanicos:
  GROUP BY mecanico WHERE status = 'Concluído'
  → receita total e ticket médio — top 10

clientes_recorrentes:
  GROUP BY cliente_id + JOIN com clientes
  → total_visitas, gasto_total, primeira e última visita — top 20

pecas_mais_utilizadas:
  GROUP BY peca_utilizada + JOIN com pecas
  → total_uso, receita_pecas, margem — top 20

formas_pagamento:
  GROUP BY pagamento WHERE status = 'Concluído'
  → distribuição de volume e receita por forma de pagamento
```

### Por que Spark e não SQL puro no Athena?

Para as transformações de limpeza (cast, filtros, campos derivados aplicados linha a linha em 183k registros), Spark é mais adequado: opera em memória distribuída e não cobra por volume de dados lido como o Athena. O Athena cobra $5 por TB escaneado — para iterações de desenvolvimento, rodar o job de limpeza 10 vezes no Glue sai mais barato do que fazer o mesmo via Athena.

---

## Consultas SQL — Amazon Athena

O Athena é um query engine serverless que executa SQL diretamente sobre arquivos no S3, usando o Glue Data Catalog como metastore. Não há banco de dados ou servidor para gerenciar.

### Por que Athena e não RDS ou Redshift?

| Critério | Athena | RDS | Redshift |
|---|---|---|---|
| Infraestrutura | Zero (serverless) | Instância gerenciada | Cluster gerenciado |
| Custo fixo | Nenhum | ~$15/mês mínimo | ~$180/mês mínimo |
| Caso de uso ideal | Queries ad hoc sobre Data Lake | OLTP transacional | OLAP em grande escala |
| Free tier | Sim (5GB/mês) | Sim (750h t2.micro) | Não |

Para análises exploratórias sobre um Data Lake existente no S3, Athena é a escolha natural. RDS seria inadequado porque exigiria carregar os dados para um banco relacional — adicionando uma etapa desnecessária. Redshift seria overkill para o volume do projeto.

### Configuração necessária

O único requisito de configuração é definir um bucket S3 para output das queries:

```
s3://automative-results-piiva/athena-output/
```

O Athena grava os resultados de cada query nesse path automaticamente.

---

## Visualização — Metabase

O Metabase é uma ferramenta open-source de Business Intelligence que conecta diretamente ao Athena via driver JDBC. Foi escolhido em vez do QuickSight (bloqueado na conta AWS free tier) e do Looker Studio (sem driver nativo para Athena sem configuração extra).

### Execução via Docker

```yaml
# docker-compose.yml
services:
  metabase:
    image: metabase/metabase:latest
    ports:
      - "3000:3000"
    volumes:
      - metabase-data:/metabase-data
```

O volume `metabase-data` persiste a configuração e dashboards entre reinicializações do container.

### Conexão com Athena

A conexão é feita via driver nativo do Metabase para Athena, usando as credenciais do IAM user `svc-pipeline` e apontando para o database `automotive_db_results` no Glue Catalog.

---

## Geração de Dados — Python + Faker

Como a Digoi Auto Center não possui sistema de captura de dados, os dados foram simulados com a biblioteca Faker (locale `pt_BR`) para representar fielmente o contexto brasileiro.

### Volume gerado

| Tabela | Registros | Justificativa |
|---|---|---|
| clientes | 3.000 | Base realista para uma oficina de médio porte |
| ordens | 100.000 | ~2.5 anos de operação com ~40 OS/dia |
| pecas | 500 | Catálogo típico de uma oficina generalista |
| estoque | 80.000 | ~2 movimentações por ordem em média |
| **Total** | **183.000** | Caracteriza Big Data no contexto do projeto |

### Seed fixo

```python
random.seed(42)
```

O seed fixo garante reprodutibilidade — rodar o script duas vezes gera exatamente os mesmos dados, facilitando a depuração e a validação dos resultados.

---

## IAM — Controle de Acesso

Três usuários IAM foram criados seguindo o princípio de menor privilégio:

| Usuário | Tipo | Permissões | Access Key? |
|---|---|---|---|
| `thalles` | Humano | Full access via grupo dev-bigdata | Não |
| `colega` | Humano | Full access via grupo dev-bigdata | Não |
| `svc-pipeline` | Serviço | Full access via grupo dev-bigdata | Sim |

Apenas o `svc-pipeline` possui Access Key — usada nos scripts Python e na conexão do Metabase com o Athena. Usuários humanos acessam o console AWS com senha, sem expor credenciais programáticas.

---

## Repositório

```
automotive-bigdata-pucgo/
├── data/
│   └── generate_data.py        # geração dos dados simulados com Faker
├── pipeline/
│   ├── glue_job_clean.py       # Spark job de limpeza (raw → processed)
│   └── glue_job_analysis.py    # Spark job de análise (processed → results)
├── infra/
│   └── architecture.svg        # diagrama de arquitetura
├── docs/
│   └── relatorio_final.docx    # relatório acadêmico
├── Dockerfile                  # imagem do Metabase
├── docker-compose.yml          # orquestração local do Metabase
├── .env                        # credenciais (não versionado)
├── .gitignore                  # exclui .env e __pycache__
└── README.md
```

---

## Fluxo Completo da Pipeline

```
Python + Faker
     │
     │ upload CSV
     ▼
S3 automative-dev-piiva/        ← Data Lake raw
     │
     ├──► Glue Crawler ──► Glue Catalog (automotive_db)
     │
     │ spark.read.csv()
     ▼
Glue Job — clean (Apache Spark)
     │ limpeza, tipos, campos derivados
     │ spark.write.parquet()
     ▼
S3 automative-prod-piiva/       ← Data Lake processed
     │
     ├──► Glue Crawler ──► Glue Catalog (automative_db_prd)
     │
     │ spark.read.parquet()
     ▼
Glue Job — analysis (Apache Spark)
     │ 6 análises de negócio
     │ df.coalesce(1).write.csv()
     ▼
S3 automative-results-piiva/    ← Data Lake results
     │
     ├──► Glue Crawler ──► Glue Catalog (automotive_db_results)
     │
     │ JDBC / SQL
     ▼
Amazon Athena
     │
     │ JDBC driver
     ▼
Metabase (Docker)
     │
     ▼
Dashboard
```