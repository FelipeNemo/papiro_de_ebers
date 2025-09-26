"""
Arquivo especial do pytest (conftest.py):
- Define "fixtures" reutilizáveis para todos os testes.
- Ajuda a preparar/limpar o ambiente entre testes automaticamente.

Conceitos rápidos:
- fixture: função que prepara algo para o teste (ex.: conexão, dados).
- scope="session": roda uma vez por sessão de testes.
- autouse=True: é aplicada automaticamente em todos os testes, sem precisar importar.
"""

import os
import uuid
import pytest
import psycopg
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    # Carrega variáveis do arquivo .env do módulo (se existir)
    mod_root = Path(__file__).resolve().parents[1]
    load_dotenv(mod_root / ".env", override=False)
    load_dotenv(override=False)  # também tenta o .env do diretório atual


def _db_url() -> str | None:
    """Monta a URL do Postgres a partir do .env (apenas DB_*)."""
    req = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"]
    if not all(os.getenv(k) for k in req):
        return None
    sslmode = os.getenv("DB_SSLMODE", "require")
    return (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT','5432')}/{os.getenv('DB_NAME')}?sslmode={sslmode}"
    )




@pytest.fixture(scope="session")
def db_ready():
    """Prepara o banco para os testes.

    - Carrega .env
    - Aplica migrações (schema + seed) uma vez por sessão, usando nosso runner Python
    - Se não houver DB configurado/acessível, os testes são pulados (skip)
    """
    _load_env()
    url = _db_url()
    if not url:
        pytest.skip("DB não configurado (.env faltando)")
    try:
        import scripts.migrate as mig
        sql_dir = (Path(__file__).resolve().parents[1] / "sql").resolve()
        # Aplica apenas os arquivos conhecidos (idempotente)
        mig.apply_sql_files(url, [sql_dir / "01_crm_schema.sql", sql_dir / "02_seed_status_lead.sql"], continue_on_error=False)
    except Exception as e:
        pytest.skip(f"Não foi possível aplicar migrações/se conectar ao DB: {e}")
    return url


@pytest.fixture(autouse=True)
def clean_db(db_ready):
    """Limpa as tabelas do CRM a cada teste para isolar cenários.

    Observação: isto remove dados entre testes (TRUNCATE). Use em ambiente de desenvolvimento.
    """
    with psycopg.connect(db_ready) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("truncate table public.itens_proposta cascade;")
            cur.execute("truncate table public.propostas cascade;")
            cur.execute("truncate table public.tarefas_lead cascade;")
            cur.execute("truncate table public.notas_lead cascade;")
            cur.execute("truncate table public.leads cascade;")
    yield


@pytest.fixture
def unique_email() -> str:
    """Gera um e-mail exclusivo por teste para evitar colisão de unicidade."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"
