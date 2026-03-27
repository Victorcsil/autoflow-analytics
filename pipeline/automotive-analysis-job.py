import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F

# ── Inicialização ──────────────────────────────────────────────────────────────

args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc   = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job   = Job(glueContext)
job.init(args["JOB_NAME"], args)

BUCKET_PROCESSED = "automative-prod-piiva"
BUCKET_RESULTS   = "automative-results-piiva"

# ── Helpers ────────────────────────────────────────────────────────────────────

def read_parquet(path):
    return spark.read.parquet(f"s3://{BUCKET_PROCESSED}/{path}/")

def write_csv(df, path):
    df.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"s3://{BUCKET_RESULTS}/{path}/")
    print(f"  ✓ s3://{BUCKET_RESULTS}/{path}/  ({df.count():,} registros)")

# ── Leitura ────────────────────────────────────────────────────────────────────

print("\nLendo dados processados...")
ordens   = read_parquet("ordens")
clientes = read_parquet("clientes")
pecas    = read_parquet("pecas")
estoque  = read_parquet("estoque")

# ── Análise 1: Receita por tipo de serviço ─────────────────────────────────────

print("\n[1/6] Receita por tipo de serviço...")
receita_servico = (
    ordens
    .filter(F.col("status") == "Concluído")
    .groupBy("servico")
    .agg(
        F.count("ordem_id").alias("total_ordens"),
        F.round(F.sum("valor_total"), 2).alias("receita_total"),
        F.round(F.avg("valor_total"), 2).alias("ticket_medio"),
        F.round(F.avg("dias_servico"), 1).alias("media_dias"),
    )
    .orderBy(F.desc("receita_total"))
)
write_csv(receita_servico, "receita_por_servico")

# ── Análise 2: Receita mensal ──────────────────────────────────────────────────

print("\n[2/6] Receita mensal...")
receita_mensal = (
    ordens
    .filter(F.col("status") == "Concluído")
    .groupBy("ano", "mes")
    .agg(
        F.count("ordem_id").alias("total_ordens"),
        F.round(F.sum("valor_total"), 2).alias("receita_total"),
        F.round(F.avg("valor_total"), 2).alias("ticket_medio"),
    )
    .orderBy("ano", "mes")
)
write_csv(receita_mensal, "receita_mensal")

# ── Análise 3: Top 10 mecânicos por receita ────────────────────────────────────

print("\n[3/6] Top mecânicos...")
top_mecanicos = (
    ordens
    .filter(F.col("status") == "Concluído")
    .groupBy("mecanico")
    .agg(
        F.count("ordem_id").alias("total_ordens"),
        F.round(F.sum("valor_total"), 2).alias("receita_total"),
        F.round(F.avg("valor_total"), 2).alias("ticket_medio"),
        F.round(F.avg("dias_servico"), 1).alias("media_dias"),
    )
    .orderBy(F.desc("receita_total"))
    .limit(10)
)
write_csv(top_mecanicos, "top_mecanicos")

# ── Análise 4: Clientes mais recorrentes ──────────────────────────────────────

print("\n[4/6] Clientes recorrentes...")
clientes_recorrentes = (
    ordens
    .filter(F.col("status") == "Concluído")
    .groupBy("cliente_id")
    .agg(
        F.count("ordem_id").alias("total_visitas"),
        F.round(F.sum("valor_total"), 2).alias("gasto_total"),
        F.round(F.avg("valor_total"), 2).alias("ticket_medio"),
        F.min("data_entrada").alias("primeira_visita"),
        F.max("data_entrada").alias("ultima_visita"),
    )
    .join(clientes.select("cliente_id", "nome", "cidade", "estado", "marca_veiculo", "modelo_veiculo"), "cliente_id")
    .orderBy(F.desc("total_visitas"))
    .limit(20)
)
write_csv(clientes_recorrentes, "clientes_recorrentes")

# ── Análise 5: Peças mais utilizadas ──────────────────────────────────────────

print("\n[5/6] Peças mais utilizadas...")
pecas_utilizadas = (
    ordens
    .filter(F.col("peca_utilizada").isNotNull())
    .groupBy("peca_utilizada")
    .agg(
        F.count("ordem_id").alias("total_uso"),
        F.round(F.sum("valor_peca"), 2).alias("receita_pecas"),
    )
    .join(pecas.select("peca_id", "nome", "categoria", "preco_custo", "preco_venda", "margem_pct"),
          F.col("peca_utilizada") == F.col("peca_id"))
    .orderBy(F.desc("total_uso"))
    .limit(20)
)
write_csv(pecas_utilizadas, "pecas_mais_utilizadas")

# ── Análise 6: Formas de pagamento ────────────────────────────────────────────

print("\n[6/6] Formas de pagamento...")
pagamentos = (
    ordens
    .filter(F.col("status") == "Concluído")
    .groupBy("pagamento")
    .agg(
        F.count("ordem_id").alias("total_ordens"),
        F.round(F.sum("valor_total"), 2).alias("receita_total"),
        F.round(F.avg("valor_total"), 2).alias("ticket_medio"),
    )
    .orderBy(F.desc("total_ordens"))
)
write_csv(pagamentos, "formas_pagamento")

# ── Finalização ────────────────────────────────────────────────────────────────

print("\n✅ Análises concluídas! Resultados em:")
print(f"  s3://{BUCKET_RESULTS}/receita_por_servico/")
print(f"  s3://{BUCKET_RESULTS}/receita_mensal/")
print(f"  s3://{BUCKET_RESULTS}/top_mecanicos/")
print(f"  s3://{BUCKET_RESULTS}/clientes_recorrentes/")
print(f"  s3://{BUCKET_RESULTS}/pecas_mais_utilizadas/")
print(f"  s3://{BUCKET_RESULTS}/formas_pagamento/")

job.commit()