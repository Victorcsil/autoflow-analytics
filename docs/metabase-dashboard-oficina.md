# Documentação: Painel Executivo de Análise Operacional e Financeira - Oficina Automotiva

## 1. Introdução

Este documento apresenta a especificação técnica e funcional do **Painel Executivo de Análise Operacional e Financeira** desenvolvido para a gestão de ordens de serviço no domínio de oficina automotiva. O painel foi implementado utilizando a plataforma de business intelligence **Metabase**, integrada ao banco de dados **Amazon Athena** contendo histórico transacional de ordens.

**Escopo**: Análise de ordens concluídas, com foco em receita, performance operacional e inteligência comercial.

**Identificador no Metabase**: Dashboard ID 2  
**Data de Atualização**: 29 de março de 2026  
**Status de Operação**: Ativo

---

## 2. Objetivos

O painel foi concebido com os seguintes objetivos:

1. **Centralizar métricas operacionais**: Oferecer visualização única de KPIs chave do negócio
2. **Facilitar análise temporal**: Permitir compreensão de tendências de receita e volume
3. **Benchmarking de recursos**: Comparar performance entre mecânicos e tipos de serviço
4. **Inteligência comercial**: Identificar clientes recorrentes, serviços prioritários e peças críticas
5. **Tomada de decisão ágil**: Prover filtros dinâmicos para exploração exploratória de dados

---

## 3. Arquitetura de Dados e Integração

### 3.1 Fonte de Dados Primária
- **Tabela**: `automative_db.ordens` no Amazon Athena
- **Escopo**: Registros de ordens de serviço com status de conclusão
- **Frequência de Atualização**: Conforme pipeline de ETL (definido em `docs/tecnico.md`)

### 3.2 Filtros Globais Disponíveis
O dashboard disponibiliza três parâmetros de filtro que afetam globalmente todos os indicadores:

| Parâmetro | Tipo | Descrição | Comportamento |
|-----------|------|-----------|---------------|
| **Período** | Date Range | Intervalo de datas para análise | Filtra ordens por data_entrada |
| **Mecânico** | String (seleção única) | Identificador de mecânico | Filtra por mecanico responsável |
| **Status** | String (seleção única) | Situação da ordem | Filtra por status da ordem |

**Implementação**: Os filtros utilizam o mecanismo de parameter mapping do Metabase, permitindo aplicação dinâmica aos cards nativos.



---

## 4. Design e Estrutura de Visualización

### 4.1 Arquitetura de Layout
O painel adota uma abordagem de grid responsivo com 24 colunas de largura, dividida em cinco seções temáticas organizadas verticalmente. Esta estrutura segue princípios de design de interfaces de BI para progressão lógica de informações (executivo → operacional → detalhe).

#### 4.1.1 Seção 1: Indicadores-Chave de Desempenho (KPIs)
**Localização**: Linha 0, Colunas 0-23  
**Propósito**: Apresentar métricas executivas de ordens concluídas  
**Componentes**: 4 cards escalares com valores agregados

#### 4.1.2 Seção 2: Análise Temporal de Receita
**Localização**: Linha 4, Colunas 0-23  
**Propósito**: Visualizar comportamento temporal de receita e volume  
**Componentes**: 2 series temporais (line charts)

#### 4.1.3 Seção 3: Análise Operacional por Dimensão
**Localização**: Linha 10, Colunas 0-23  
**Propósito**: Segmentar receita por fatores operacionais  
**Componentes**: 3 tabelas detalhadas + 1 gráfico de barras

#### 4.1.4 Seção 4: Inteligência Comercial
**Localização**: Linha 16, Colunas 0-23  
**Propósito**: Análise de clientes recorrentes e insumos críticos  
**Componentes**: 2 tabelas de detalhe

---

## 5. Especificação dos Indicadores

### 5.1 KPI - Ordens Concluídas

**Card ID Metabase**: 98  
**Tipo de Visualização**: Scalar (valor numérico)  
**Posicionamento**: Coluna 0-5, Linha 0  
**Dimensão do Card**: 6x4 unidades de grid

**Definição**: Contagem total de ordens com status indicando conclusão (padrão: iniciado com "concl").

**Especificação SQL**:
```sql
SELECT COUNT(*) AS total_concluidas 
FROM automative_db.ordens 
WHERE regexp_like(lower(coalesce(status,'')), '^concl')
```

**Interpretação**: Representa o volume absoluto de transações finalizadas dentro do período filtrado.

**Tempo Médio de Execução**: ~5 segundos  
**Atualizações**: Contínua conforme disponibilidade de dados

---

### 5.2 KPI - Taxa de Conclusão

**Card ID Metabase**: 99  
**Tipo de Visualização**: Scalar (percentual)  
**Posicionamento**: Coluna 6-11, Linha 0  
**Dimensão do Card**: 6x4 unidades de grid

**Definição**: Proporção de ordens concluídas em relação ao universo total de ordens.

**Especificação SQL**:
```sql
SELECT 100.0 * AVG(
    CASE WHEN regexp_like(lower(coalesce(status,'')), '^concl') 
    THEN 1 ELSE 0 END
) AS taxa_conclusao_pct
FROM automative_db.ordens
```

**Formatação**: Percentual com 2 casas decimais  
**Tempo Médio de Execução**: ~4 segundos  
**Interpretação**: Métrica de eficiência operacional; valores acima de 75% indicam performance saudável.

---

### 5.3 KPI - Receita Concluída

**Card ID Metabase**: 100  
**Tipo de Visualização**: Scalar (moeda)  
**Posicionamento**: Coluna 12-17, Linha 0  
**Dimensão do Card**: 6x4 unidades de grid

**Definição**: Somatório de receita (serviços + peças) de todas as ordens concluídas.

**Especificação SQL**:
```sql
SELECT SUM(COALESCE(valor_servico,0) + COALESCE(valor_peca,0)) 
  AS receita_concluida
FROM automative_db.ordens 
WHERE regexp_like(lower(coalesce(status,'')), '^concl')
```

**Formatação**: Moeda (BRL - Real Brasileiro)  
**Tempo Médio de Execução**: ~4 segundos  
**Interpretação**: Métrica financeira principal; base para decisões de alocação de recursos.

---

### 5.4 KPI - Ticket Médio Concluído

**Card ID Metabase**: 101  
**Tipo de Visualização**: Scalar (moeda)  
**Posicionamento**: Coluna 18-23, Linha 0  
**Dimensão do Card**: 6x4 unidades de grid

**Definição**: Valor médio por ordem de serviço concluída.

**Especificação SQL**:
```sql
SELECT AVG(COALESCE(valor_servico,0) + COALESCE(valor_peca,0)) 
  AS ticket_medio
FROM automative_db.ordens 
WHERE regexp_like(lower(coalesce(status,'')), '^concl')
```

**Formatação**: Moeda (BRL)  
**Tempo Médio de Execução**: ~4 segundos  
**Interpretação**: Indica valor médio de transação; utilizado para previsão de receita e segmentação de clientes.

---

### 5.5 Receita Mensal (Ordens Concluídas)

**Card ID Metabase**: 104  
**Tipo de Visualização**: Line Chart (série temporal)  
**Posicionamento**: Coluna 0-15, Linha 4  
**Dimensão do Card**: 16x6 unidades de grid

**Definição**: Evolução mensal de receita total, volume de ordens e ticket médio de ordens concluídas.

**Especificação SQL**:
```sql
SELECT 
  date_trunc('month', try(date_parse(data_entrada, '%Y-%m-%d'))) AS mes,
  COUNT(*) AS total_ordens,
  SUM(COALESCE(valor_servico,0) + COALESCE(valor_peca,0)) AS receita_total,
  AVG(COALESCE(valor_servico,0) + COALESCE(valor_peca,0)) AS ticket_medio
FROM automative_db.ordens 
WHERE regexp_like(lower(coalesce(status,'')), '^concl')
GROUP BY 1 
ORDER BY 1
```

**Série de Dados**: 3 eixos (receita, volume, ticket médio)  
**Período Típico**: Últimos 48 meses  
**Tempo Médio de Execução**: ~4.8 segundos  
**Interpretação**: Detecta sazonalidade, tendências de negócio e anomalias operacionais.

---

### 5.6 Composição Mensal da Receita

**Card ID Metabase**: 97  
**Tipo de Visualização**: Line Chart (série temporal)  
**Posicionamento**: Coluna 16-23, Linha 4  
**Dimensão do Card**: 8x6 unidades de grid

**Definição**: Decomposição mensal de receita discriminando componentes (serviços e peças).

**Tempo Médio de Execução**: Variável conforme período selecionado (~2-5 segundos)  
**Interpretação**: Fornece inteligência sobre mix de receita; suporta decisões sobre portfolio de serviços.

---

### 5.7 Receita por Serviço

**Card ID Metabase**: 102  
**Tipo de Visualização**: Table (tabela detalhada)  
**Posicionamento**: Coluna 0-7, Linha 10  
**Dimensão do Card**: 8x6 unidades de grid

**Definição**: Agregação de receita, volume e ticket médio por tipo de serviço (Top 20).

**Especificação SQL**:
```sql
SELECT 
  servico,
  COUNT(*) AS total_ordens,
  SUM(COALESCE(valor_servico,0) + COALESCE(valor_peca,0)) AS receita_total,
  AVG(COALESCE(valor_servico,0) + COALESCE(valor_peca,0)) AS ticket_medio
FROM automative_db.ordens 
WHERE regexp_like(lower(coalesce(status,'')), '^concl') 
  AND servico IS NOT NULL
GROUP BY 1 
ORDER BY receita_total DESC 
LIMIT 20
```

**Colunas**: servico, total_ordens, receita_total, ticket_medio  
**Tempo Médio de Execução**: ~1.7 segundos  
**Interpretação**: Identifica serviços prioritários e oportunidades de cross-selling.

---

### 5.8 Top Mecânicos

**Card ID Metabase**: 103  
**Tipo de Visualização**: Table (tabela detalhada)  
**Posicionamento**: Coluna 8-15, Linha 10  
**Dimensão do Card**: 8x6 unidades de grid

**Definição**: Ranking de mecânicos por receita gerada (Top 10).

**Especificação SQL**:
```sql
SELECT 
  mecanico,
  COUNT(*) AS total_ordens,
  SUM(COALESCE(valor_servico,0) + COALESCE(valor_peca,0)) AS receita_total,
  AVG(COALESCE(valor_servico,0) + COALESCE(valor_peca,0)) AS ticket_medio
FROM automative_db.ordens 
WHERE regexp_like(lower(coalesce(status,'')), '^concl') 
  AND mecanico IS NOT NULL
GROUP BY 1 
ORDER BY receita_total DESC 
LIMIT 10
```

**Colunas**: mecanico, total_ordens, receita_total, ticket_medio  
**Tempo Médio de Execução**: ~1.7 segundos  
**Interpretação**: Suporta avaliação de performance individual e identificação de best practices.

---

### 5.9 Formas de Pagamento

**Card ID Metabase**: 105  
**Tipo de Visualização**: Bar Chart (gráfico de barras)  
**Posicionamento**: Coluna 16-23, Linha 10  
**Dimensão do Card**: 8x6 unidades de grid

**Definição**: Distribuição de volume e receita por forma de pagamento.

**Especificação SQL**:
```sql
SELECT 
  pagamento AS forma_pagamento,
  COUNT(*) AS total_ordens,
  SUM(COALESCE(valor_servico,0) + COALESCE(valor_peca,0)) AS receita_total
FROM automative_db.ordens 
WHERE regexp_like(lower(coalesce(status,'')), '^concl') 
  AND pagamento IS NOT NULL
GROUP BY 1 
ORDER BY receita_total DESC
```

**Tempo Médio de Execução**: ~1.4 segundos  
**Visualização**: Valores exibidos nos elementos do gráfico  
**Interpretação**: Monitora fluxo de caixa e preferências de clientes.

---

### 5.10 Clientes Recorrentes

**Card ID Metabase**: 106  
**Tipo de Visualização**: Table (tabela detalhada)  
**Posicionamento**: Coluna 0-11, Linha 16  
**Dimensão do Card**: 12x6 unidades de grid

**Definição**: Clientes com maior frequência de visitas e gasto acumulado (Top 20).

**Especificação SQL**:
```sql
SELECT 
  cliente_id,
  COUNT(*) AS total_visitas,
  SUM(COALESCE(valor_servico,0) + COALESCE(valor_peca,0)) AS gasto_total,
  MIN(try(date_parse(data_entrada, '%Y-%m-%d'))) AS primeira_visita,
  MAX(try(date_parse(data_entrada, '%Y-%m-%d'))) AS ultima_visita
FROM automative_db.ordens 
WHERE regexp_like(lower(coalesce(status,'')), '^concl')
GROUP BY 1 
ORDER BY total_visitas DESC, gasto_total DESC 
LIMIT 20
```

**Colunas**: cliente_id, total_visitas, gasto_total, primeira_visita, ultima_visita  
**Tempo Médio de Execução**: ~1.7 segundos  
**Interpretação**: Base para estratégias de fidelização e retenção de clientes de alto valor.

---

### 5.11 Peças Mais Utilizadas

**Card ID Metabase**: 107  
**Tipo de Visualização**: Table (tabela detalhada)  
**Posicionamento**: Coluna 12-23, Linha 16  
**Dimensão do Card**: 12x6 unidades de grid

**Definição**: Peças com maior frequência de utilização em ordens concluídas, com receita associada (Top 20).

**Especificação SQL**:
```sql
SELECT 
  peca_utilizada AS peca,
  COUNT(*) AS total_uso,
  SUM(COALESCE(valor_peca,0)) AS receita_pecas
FROM automative_db.ordens 
WHERE regexp_like(lower(coalesce(status,'')), '^concl') 
  AND peca_utilizada IS NOT NULL 
  AND trim(peca_utilizada) <> ''
GROUP BY 1 
ORDER BY total_uso DESC 
LIMIT 20
```

**Colunas**: peca, total_uso, receita_pecas  
**Tempo Médio de Execução**: ~1.75 segundos  
---

## 6. Guia de Operação

### 6.1 Aplicação de Filtros Interativos

O painel oferece capacidade de filtração dinâmica através dos parâmetros globais. Procedimento de aplicação:

1. Localizar controle de **Filtros** no cabeçalho do dashboard
2. Selecionar critérios desejados (Período, Mecânico, Status)
3. Confirmar aplicação — todos os cards se atualizam automaticamente
4. Para limpar filtros, utilizar botão "Limpar Filtros" ou desmarcar seleções

### 6.2 Exploração de Dados Detalhados

Para análise mais profunda:

1. **Abrir Card Individual**: Clique no título ou corpo de um card para expandi-lo em visualização full-screen
2. **Busca em Tabelas**: Utilize Ctrl+F para localizar valores específicos em cards tabulares
3. **Interatividade em Gráficos**: Posicione mouse sobre elementos gráficos para visualizar valores exatos
4. **Download de Dados**: Acesse menu "⋮" (Mais Ações) > Exportar > Escolha formato (CSV, XLSX)

### 6.3 Exportação de Dados

Procedimento para extração de dados:

1. Abrir card específico (clique para expandir)
2. Localizar menu lateral "Mais" (⋮)
3. Selecionar "Download" ou "Exportar"
4. Escolher formato desejado (CSV para planilhas abertas, XLSX para compatibilidade com Excel)
5. Arquivo é gerado e baixado localmente

---

## 7. Considerações Técnicas e de Implementação

### 7.1 Camada de Dados

**Fonte Primária**: Tabela `automative_db.ordens` em Amazon Athena  
**Escopo**: Registros históricos de ordens de serviço automotivo  
**Atualização**: Frequência conforme pipeline ETL definido em `docs/tecnico.md`

### 7.2 Tratamento de Dados Ausentes

Implementações detectadas:

- **Valores NULL de Receita**: Substituição por zero utilizando `COALESCE(valor_servico,0) + COALESCE(valor_peca,0)`
- **Parsing de Datas**: Utilização de `try(date_parse(...))` para tolerância a formatos variáveis
- **Trimagem de Strings**: Remoção de espaços em branco em categorias via `trim()`

### 7.3 Critério Unificado de Conclusão

Todos os cards aplicam filtro consistente: `regexp_like(lower(coalesce(status,'')), '^concl')`

**Justificativa**: Padronização de semântica de "conclusão" independente de variações de caso ou formatação no banco de dados.

### 7.4 Performance

Tempos de execução observados:

| Componente | Tempo (seg) | Classificação |
|-----------|------------|---------------|
| Receita Mensal | 4.8 | Mais Lento |
| KPIs (cada um) | 4.0-5.0 | Lento |
| Tabelas Detalhadas | 1.4-1.7 | Rápido |
| Formas de Pagamento | 1.4 | Mais Rápido |

**Tempo Total de Refresh**: 15-20 segundos (refresh completo do dashboard)

---

## 8. Recomendações de Uso

### 8.1 Público-Alvo

- **Gestão Executiva**: Utilizar KPIs da Seção 1 para visão executiva diária
- **Gestão Operacional**: Explorar Seção 3 (análise por dimensão) e Seção 4 (inteligência comercial)
- **Análise Comercial**: Detalhar clientes recorrentes e peças críticas
- **Gestão de RH**: Utilizar ranking de mecânicos para avaliação de performance

### 8.2 Frequência de Consulta Recomendada

- **KPIs Executivos**: Diária (ao início do expediente)
- **Tendências Temporais**: Semanal
- **Análise Detalhada**: Conforme demanda de decisão
- **Relatórios**: Mensal (consolidação)

---

## 9. Roadmap de Evoluções

### 9.1 Oportunidades Futuras

#### 9.1.1 Hospedagem em Amazon ECS
Uma evolução arquitetural estratégica seria migrar a instância Metabase de um ambiente Docker Compose local para um serviço containerizado gerenciado em **Amazon ECS (Elastic Container Service)**.

**Benefícios Esperados**:
- **Escalabilidade Automática**: Aumentar/reduzir recursos conforme demanda sem interrupção de serviço
- **Alta Disponibilidade**: Configuração multi-AZ com balanceamento de carga automático
- **Persistência de Dados**: Integração nativa com Amazon RDS PostgreSQL para banco de dados do Metabase
- **Segurança em Nível Enterprise**: Suporte a IAM, VPC, Security Groups, AWS Secrets Manager
- **Monitoramento e Observabilidade**: CloudWatch integrado com alertas automáticos

**Roadmap Técnico Sugerido**:
1. Criar definição de tarefa ECS otimizada com Dockerfile multi-stage
2. Configurar RDS PostgreSQL como backend do Metabase (substitui SQLite local)
3. Documentar Terraform para infraestrutura como código (IaC)
4. Implementar pipeline CI/CD via GitHub Actions → AWS CodePipeline
5. Validar em ambiente de staging antes de produção

---

## 10. Conclusão e Resumo Executivo

Este painel foi desenvolvido com objetivo de centralizar e democratizar acesso a métricas operacionais e financeiras de ordens de serviço automotivo. Através de integração com Metabase e Athena, oferece:

✓ **Visibilidade Executiva**: 4 KPIs chave em tempo real  
✓ **Análise Temporal**: Compreensão de tendências e sazonalidade  
✓ **Inteligência Operacional**: Segmentação por serviço, mecânico e forma de pagamento  
✓ **Inteligência Comercial**: Identificação de clientes recorrentes e peças críticas  
✓ **Interatividade**: Filtros dinâmicos para exploração exploratória de dados  

**Status Atual**: Operacional e estável  
**Data da Documentação**: 29 de março de 2026  
**Versão**: Rev B

---

## 11. Referências e Documentação Complementar

Para informações adicionais sobre arquitetura de dados, pipeline ETL e especificações técnicas do projeto, consultar:
- [Documentação Técnica - `docs/tecnico.md`](./tecnico.md)
- [Workflow de Snapshots - `infra/SNAPSHOT_WORKFLOW.md`](../infra/SNAPSHOT_WORKFLOW.md)

**Contato**: Para dúvidas técnicas sobre este painel, consulte a equipe de dados ou gestores de projeto listados em `docs/tecnico.md`.
