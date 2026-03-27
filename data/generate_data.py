import os
import random
import boto3
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

fake = Faker("pt_BR")
random.seed(42)

AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
BUCKET_RAW = os.getenv("BUCKET_RAW", "automative-dev-piiva")

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# ── Configurações ──────────────────────────────────────────────────────────────

N_CLIENTES      = 3_000
N_ORDENS        = 100_000
N_PECAS         = 500
N_ESTOQUE       = 80_000

SERVICOS = [
    ("Troca de óleo",            150, 350),
    ("Revisão completa",         800, 2500),
    ("Alinhamento e balanceamento", 120, 250),
    ("Troca de freios",          300, 900),
    ("Suspensão",                500, 1800),
    ("Elétrica",                 200, 1200),
    ("Ar-condicionado",          350, 1100),
    ("Câmbio",                   900, 3500),
    ("Motor",                    1500, 8000),
    ("Funilaria e pintura",      600, 4000),
]

MARCAS_MODELOS = {
    "Fiat":       ["Uno", "Palio", "Strada", "Toro", "Cronos"],
    "Chevrolet":  ["Onix", "Prisma", "S10", "Tracker", "Spin"],
    "Volkswagen": ["Gol", "Polo", "T-Cross", "Virtus", "Saveiro"],
    "Toyota":     ["Corolla", "Hilux", "Yaris", "SW4", "RAV4"],
    "Honda":      ["Civic", "HR-V", "Fit", "City", "CR-V"],
    "Hyundai":    ["HB20", "Creta", "Tucson", "ix35", "Elantra"],
    "Ford":       ["Ka", "EcoSport", "Ranger", "Fusion", "Fiesta"],
}

MECANICOS = [fake.name() for _ in range(20)]

FORNECEDORES = [fake.company() for _ in range(30)]

CATEGORIAS_PECA = [
    "Motor", "Freios", "Suspensão", "Elétrica",
    "Transmissão", "Arrefecimento", "Combustível", "Carroceria",
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def rand_date(start_year=2022, end_year=2025):
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def upload(df: pd.DataFrame, key: str):
    csv = df.to_csv(index=False)
    s3.put_object(Bucket=BUCKET_RAW, Key=key, Body=csv.encode("utf-8"))
    print(f"  ✓ s3://{BUCKET_RAW}/{key}  ({len(df):,} registros)")

# ── Geração ────────────────────────────────────────────────────────────────────

def gerar_clientes():
    print("Gerando clientes...")
    rows = []
    for i in range(N_CLIENTES):
        marca  = random.choice(list(MARCAS_MODELOS))
        modelo = random.choice(MARCAS_MODELOS[marca])
        rows.append({
            "cliente_id":   f"CLI{i+1:05d}",
            "nome":         fake.name(),
            "cpf":          fake.cpf(),
            "telefone":     fake.phone_number(),
            "email":        fake.email(),
            "cidade":       fake.city(),
            "estado":       fake.state_abbr(),
            "marca_veiculo": marca,
            "modelo_veiculo": modelo,
            "ano_veiculo":  random.randint(2005, 2024),
            "placa":        fake.license_plate(),
            "data_cadastro": rand_date(2020, 2022).date(),
        })
    df = pd.DataFrame(rows)
    upload(df, "clientes/clientes.csv")
    return df

def gerar_pecas():
    print("Gerando peças...")
    rows = []
    for i in range(N_PECAS):
        cat = random.choice(CATEGORIAS_PECA)
        rows.append({
            "peca_id":      f"PEC{i+1:04d}",
            "nome":         f"{cat} - {fake.word().capitalize()} {random.randint(100,9999)}",
            "categoria":    cat,
            "fornecedor":   random.choice(FORNECEDORES),
            "preco_custo":  round(random.uniform(20, 1500), 2),
            "preco_venda":  round(random.uniform(40, 2500), 2),
            "estoque_atual": random.randint(0, 200),
        })
    df = pd.DataFrame(rows)
    upload(df, "pecas/pecas.csv")
    return df

def gerar_ordens(clientes_df, pecas_df):
    print("Gerando ordens de serviço...")
    cliente_ids = clientes_df["cliente_id"].tolist()
    peca_ids    = pecas_df["peca_id"].tolist()
    rows = []
    for i in range(N_ORDENS):
        servico, vmin, vmax = random.choice(SERVICOS)
        data_entrada = rand_date(2022, 2025)
        dias         = random.randint(1, 10)
        data_saida   = data_entrada + timedelta(days=dias)
        rows.append({
            "ordem_id":       f"OS{i+1:07d}",
            "cliente_id":     random.choice(cliente_ids),
            "mecanico":       random.choice(MECANICOS),
            "servico":        servico,
            "valor_servico":  round(random.uniform(vmin, vmax), 2),
            "peca_utilizada": random.choice(peca_ids) if random.random() > 0.3 else None,
            "valor_peca":     round(random.uniform(40, 2500), 2) if random.random() > 0.3 else 0,
            "data_entrada":   data_entrada.date(),
            "data_saida":     data_saida.date(),
            "status":         random.choices(
                                ["Concluído", "Em andamento", "Aguardando peça", "Cancelado"],
                                weights=[75, 10, 10, 5]
                              )[0],
            "pagamento":      random.choice(["Dinheiro", "Cartão débito", "Cartão crédito", "Pix"]),
        })
    df = pd.DataFrame(rows)
    upload(df, "ordens/ordens.csv")
    return df

def gerar_movimentacao_estoque(pecas_df):
    print("Gerando movimentação de estoque...")
    peca_ids = pecas_df["peca_id"].tolist()
    rows = []
    for i in range(N_ESTOQUE):
        tipo = random.choices(["Entrada", "Saída"], weights=[40, 60])[0]
        rows.append({
            "mov_id":      f"MOV{i+1:07d}",
            "peca_id":     random.choice(peca_ids),
            "tipo":        tipo,
            "quantidade":  random.randint(1, 50),
            "fornecedor":  random.choice(FORNECEDORES) if tipo == "Entrada" else None,
            "data":        rand_date(2022, 2025).date(),
            "responsavel": random.choice(MECANICOS),
        })
    df = pd.DataFrame(rows)
    upload(df, "estoque/movimentacao_estoque.csv")
    return df

# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nGerando dados simulados → s3://{BUCKET_RAW}\n")
    clientes = gerar_clientes()
    pecas    = gerar_pecas()
    _ordens  = gerar_ordens(clientes, pecas)
    _estoque = gerar_movimentacao_estoque(pecas)
    print("\n✅ Todos os arquivos enviados pro S3 com sucesso!")
    print(f"\nEstrutura criada:")
    print(f"  s3://{BUCKET_RAW}/clientes/clientes.csv")
    print(f"  s3://{BUCKET_RAW}/pecas/pecas.csv")
    print(f"  s3://{BUCKET_RAW}/ordens/ordens.csv")
    print(f"  s3://{BUCKET_RAW}/estoque/movimentacao_estoque.csv")