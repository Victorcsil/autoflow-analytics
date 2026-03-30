# Documentação: Painel Executivo de Análise Operacional e Financeira - Oficina Automotiva

## 1. Introdução

Este documento apresenta o **Painel Executivo de Análise Operacional e Financeira** desenvolvido para visualização de métricas de ordens de serviço em oficina automotiva.

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

## 3. Filtros Disponíveis

O dashboard oferece três filtros que afetam todos os indicadores:

| Filtro | Tipo | Função |
|--------|------|--------|
| **Período** | Intervalo de datas | Selecionar range temporal para análise |
| **Mecânico** | Seleção única | Filtrar apenas ordens de um mecânico específico |
| **Status** | Seleção única | Filtrar ordens por situação |

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

**Interpretação**: Representa o volume absoluto de transações finalizadas dentro do período filtrado.

**Atualizações**: Contínua conforme disponibilidade de dados

---

### 5.2 KPI - Taxa de Conclusão

**Card ID Metabase**: 99  
**Tipo de Visualização**: Scalar (percentual)  
**Posicionamento**: Coluna 6-11, Linha 0  
**Dimensão do Card**: 6x4 unidades de grid

**Definição**: Proporção de ordens concluídas em relação ao universo total de ordens.

**Formatação**: Percentual com 2 casas decimais  
**Interpretação**: Métrica de eficiência operacional; valores acima de 75% indicam performance saudável.

---

### 5.3 KPI - Receita Concluída

**Card ID Metabase**: 100  
**Tipo de Visualização**: Scalar (moeda)  
**Posicionamento**: Coluna 12-17, Linha 0  
**Dimensão do Card**: 6x4 unidades de grid

**Definição**: Somatório de receita (serviços + peças) de todas as ordens concluídas.

**Formatação**: Moeda (BRL - Real Brasileiro)  
**Interpretação**: Métrica financeira principal; base para decisões de alocação de recursos.

---

### 5.4 KPI - Ticket Médio Concluído

**Card ID Metabase**: 101  
**Tipo de Visualização**: Scalar (moeda)  
**Posicionamento**: Coluna 18-23, Linha 0  
**Dimensão do Card**: 6x4 unidades de grid

**Definição**: Valor médio por ordem de serviço concluída.

**Formatação**: Moeda (BRL)  
**Interpretação**: Indica valor médio de transação; utilizado para previsão de receita e segmentação de clientes.

---

### 5.5 Receita Mensal (Ordens Concluídas)

**Card ID Metabase**: 104  
**Tipo de Visualização**: Line Chart (série temporal)  
**Posicionamento**: Coluna 0-15, Linha 4  
**Dimensão do Card**: 16x6 unidades de grid

**Definição**: Evolução mensal de receita total, volume de ordens e ticket médio de ordens concluídas.

**Série de Dados**: 3 eixos (receita, volume, ticket médio)  
**Período Típico**: Últimos 48 meses  
**Interpretação**: Detecta sazonalidade, tendências de negócio e anomalias operacionais.

---

### 5.6 Composição Mensal da Receita

**Card ID Metabase**: 97  
**Tipo de Visualização**: Line Chart (série temporal)  
**Posicionamento**: Coluna 16-23, Linha 4  
**Dimensão do Card**: 8x6 unidades de grid

**Definição**: Decomposição mensal de receita discriminando componentes (serviços e peças).

**Interpretação**: Fornece inteligência sobre mix de receita; suporta decisões sobre portfolio de serviços.

---

### 5.7 Receita por Serviço

**Card ID Metabase**: 102  
**Tipo de Visualização**: Table (tabela detalhada)  
**Posicionamento**: Coluna 0-7, Linha 10  
**Dimensão do Card**: 8x6 unidades de grid

**Definição**: Agregação de receita, volume e ticket médio por tipo de serviço (Top 20).

**Colunas**: servico, total_ordens, receita_total, ticket_medio  
**Interpretação**: Identifica serviços prioritários e oportunidades de cross-selling.

---

### 5.8 Top Mecânicos

**Card ID Metabase**: 103  
**Tipo de Visualização**: Table (tabela detalhada)  
**Posicionamento**: Coluna 8-15, Linha 10  
**Dimensão do Card**: 8x6 unidades de grid

**Definição**: Ranking de mecânicos por receita gerada (Top 10).

**Colunas**: mecanico, total_ordens, receita_total, ticket_medio  
**Interpretação**: Suporta avaliação de performance individual e identificação de best practices.

---

### 5.9 Formas de Pagamento

**Card ID Metabase**: 105  
**Tipo de Visualização**: Bar Chart (gráfico de barras)  
**Posicionamento**: Coluna 16-23, Linha 10  
**Dimensão do Card**: 8x6 unidades de grid

**Definição**: Distribuição de volume e receita por forma de pagamento.

**Visualização**: Valores exibidos nos elementos do gráfico  
**Interpretação**: Monitora fluxo de caixa e preferências de clientes.

---

### 5.10 Clientes Recorrentes

**Card ID Metabase**: 106  
**Tipo de Visualização**: Table (tabela detalhada)  
**Posicionamento**: Coluna 0-11, Linha 16  
**Dimensão do Card**: 12x6 unidades de grid

**Definição**: Clientes com maior frequência de visitas e gasto acumulado (Top 20).

**Colunas**: cliente_id, total_visitas, gasto_total, primeira_visita, ultima_visita  
**Interpretação**: Base para estratégias de fidelização e retenção de clientes de alto valor.

---

### 5.11 Peças Mais Utilizadas

**Card ID Metabase**: 107  
**Tipo de Visualização**: Table (tabela detalhada)  
**Posicionamento**: Coluna 12-23, Linha 16  
**Dimensão do Card**: 12x6 unidades de grid

**Definição**: Peças com maior frequência de utilização em ordens concluídas, com receita associada (Top 20).

**Colunas**: peca, total_uso, receita_pecas  
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

## 7. Recomendações de Uso

### 7.1 Público-Alvo

- **Gestão Executiva**: Utilizar KPIs da Seção 1 para visão executiva diária
- **Gestão Operacional**: Explorar Seção 3 (análise por dimensão) e Seção 4 (inteligência comercial)
- **Análise Comercial**: Detalhar clientes recorrentes e peças críticas
- **Gestão de RH**: Utilizar ranking de mecânicos para avaliação de performance

### 7.2 Frequência de Consulta Recomendada

- **KPIs Executivos**: Diária (ao início do expediente)
- **Tendências Temporais**: Semanal
- **Análise Detalhada**: Conforme demanda de decisão
- **Relatórios**: Mensal (consolidação)

---

## 8. Conclusão

Este painel foi desenvolvido com objetivo de centralizar e democratizar acesso a métricas operacionais e financeiras de ordens de serviço automotivo. Através de integração com Metabase e Athena, oferece:

✓ **Visibilidade Executiva**: 4 KPIs chave em tempo real  
✓ **Análise Temporal**: Compreensão de tendências e sazonalidade  
✓ **Inteligência Operacional**: Segmentação por serviço, mecânico e forma de pagamento  
✓ **Inteligência Comercial**: Identificação de clientes recorrentes e peças críticas  
✓ **Interatividade**: Filtros dinâmicos para exploração exploratória de dados  

**Status Atual**: Operacional e estável  
**Data da Documentação**: 29 de março de 2026  
**Versão**: Rev B