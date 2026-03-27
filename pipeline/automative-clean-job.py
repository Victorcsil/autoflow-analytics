import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, DateType

# ── Inicialização ──────────────────────────────────────────────────────────────

args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc   = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job   = Job(glueContext)
job.init(args["JOB_NAME"], args)

BUCKET_RAW       = "automative-dev-piiva"
BUCKET_PROCESSED = "automative-prod-piiva"

# ── Helpers ────────────────────────────────────────────────────────────────────

def read_csv(path):
    return spark.read.option("header", "true").option("inferSchema", "true").csv(path)

def write_parquet(df, path):
    df.write.mode("overwrite").parquet(f"s3://{BUCKET_PROCESSED}/{path}/")
    print(f"  ✓ s3://{BUCKET_PROCESSED}/{path}/  ({df.count():,} registros)")

# ── Clientes ───────────────────────────────────────────────────────────────────

print("\n[1/4] Limpando clientes...")
clientes = read_csv(f"s3://{BUCKET_RAW}/clientes/")

clientes = (
    clientes
    .dropDuplicates(["cliente_id"])
    .filter(F.col("cliente_id").isNotNull())
    .filter(F.col("nome").isNotNull())
    .withColumn("nome",   F.trim(F.upper(F.col("nome"))))
    .withColumn("estado", F.trim(F.upper(F.col("estado"))))
    .withColumn("cidade", F.trim(F.initcap(F.col("cidade"))))
    .withColumn("ano_veiculo", F.col("ano_veiculo").cast(IntegerType()))
    .filter(F.col("ano_veiculo").between(1990, 2025))
    .withColumn("data_cadastro", F.col("data_cadastro").cast(DateType()))
)

write_parquet(clientes, "clientes")

# ── Peças ──────────────────────────────────────────────────────────────────────

print("\n[2/4] Limpando peças...")
pecas = read_csv(f"s3://{BUCKET_RAW}/pecas/")

pecas = (
    pecas
    .dropDuplicates(["peca_id"])
    .filter(F.col("peca_id").isNotNull())
    .withColumn("preco_custo", F.col("preco_custo").cast(DoubleType()))
    .withColumn("preco_venda", F.col("preco_venda").cast(DoubleType()))
    .withColumn("estoque_atual", F.col("estoque_atual").cast(IntegerType()))
    .filter(F.col("preco_custo") > 0)
    .filter(F.col("preco_venda") > 0)
    .filter(F.col("preco_venda") >= F.col("preco_custo"))
    .withColumn("margem_pct",
        F.round(
            (F.col("preco_venda") - F.col("preco_custo")) / F.col("preco_custo") * 100,
            2
        )
    )
    .withColumn("nome",      F.trim(F.col("nome")))
    .withColumn("categoria", F.trim(F.col("categoria")))
)

write_parquet(pecas, "pecas")

# ── Ordens de Serviço ──────────────────────────────────────────────────────────

print("\n[3/4] Limpando ordens...")
ordens = read_csv(f"s3://{BUCKET_RAW}/ordens/")

ordens = (
    ordens
    .dropDuplicates(["ordem_id"])
    .filter(F.col("ordem_id").isNotNull())
    .filter(F.col("cliente_id").isNotNull())
    .withColumn("valor_servico", F.col("valor_servico").cast(DoubleType()))
    .withColumn("valor_peca",    F.col("valor_peca").cast(DoubleType()))
    .withColumn("data_entrada",  F.col("data_entrada").cast(DateType()))
    .withColumn("data_saida",    F.col("data_saida").cast(DateType()))
    .filter(F.col("valor_servico") > 0)
    .filter(F.col("data_saida") >= F.col("data_entrada"))
    .withColumn("valor_total",
        F.round(F.col("valor_servico") + F.coalesce(F.col("valor_peca"), F.lit(0.0)), 2)
    )
    .withColumn("dias_servico",
        F.datediff(F.col("data_saida"), F.col("data_entrada"))
    )
    .withColumn("ano",  F.year(F.col("data_entrada")))
    .withColumn("mes",  F.month(F.col("data_entrada")))
    .withColumn("servico",   F.trim(F.col("servico")))
    .withColumn("status",    F.trim(F.col("status")))
    .withColumn("pagamento", F.trim(F.col("pagamento")))
)

write_parquet(ordens, "ordens")

# ── Movimentação de Estoque ────────────────────────────────────────────────────

print("\n[4/4] Limpando estoque...")
estoque = read_csv(f"s3://{BUCKET_RAW}/estoque/")

estoque = (
    estoque
    .dropDuplicates(["mov_id"])
    .filter(F.col("mov_id").isNotNull())
    .filter(F.col("peca_id").isNotNull())
    .withColumn("quantidade", F.col("quantidade").cast(IntegerType()))
    .withColumn("data",       F.col("data").cast(DateType()))
    .filter(F.col("quantidade") > 0)
    .withColumn("tipo", F.trim(F.col("tipo")))
    .withColumn("quantidade_signed",
        F.when(F.col("tipo") == "Saída", F.col("quantidade") * -1)
         .otherwise(F.col("quantidade"))
    )
    .withColumn("ano", F.year(F.col("data")))
    .withColumn("mes", F.month(F.col("data")))
)

write_parquet(estoque, "estoque")

# ── Finalização ────────────────────────────────────────────────────────────────

print("\n✅ Limpeza concluída! Dados salvos em:")
print(f"  s3://{BUCKET_PROCESSED}/clientes/")
print(f"  s3://{BUCKET_PROCESSED}/pecas/")
print(f"  s3://{BUCKET_PROCESSED}/ordens/")
print(f"  s3://{BUCKET_PROCESSED}/estoque/")

job.commit()