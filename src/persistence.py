import sqlite3
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from loguru import logger
from config import CAMINHO_DB, CAMINHO_SAIDA
import os

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
RUN_RUNNING    = "RUNNING"
RUN_COMPLETED  = "COMPLETED"
RUN_FAILED     = "FAILED"
RUN_INCOMPLETA = "INCOMPLETA"

ITEM_OK         = "OK"
ITEM_ERRO_LLM   = "ERRO_LLM"
ITEM_ERRO_PARSE = "ERRO_PARSE"

_DDL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS runs (
    run_id              TEXT PRIMARY KEY,
    nome                TEXT NOT NULL,
    arquivo_origem      TEXT,
    started_at          TEXT NOT NULL,
    finished_at         TEXT,
    status              TEXT NOT NULL DEFAULT 'RUNNING',
    total_blocos        INTEGER,
    blocos_processados  INTEGER DEFAULT 0,
    total_evidencias    INTEGER DEFAULT 0,
    email_destino       TEXT,
    erro_msg            TEXT
);

CREATE TABLE IF NOT EXISTS run_items (
    run_id           TEXT NOT NULL,
    bloco_id         INTEGER NOT NULL,
    status           TEXT NOT NULL,
    evidencias_count INTEGER DEFAULT 0,
    erro_msg         TEXT,
    processed_at     TEXT NOT NULL,
    PRIMARY KEY (run_id, bloco_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_items_run   ON run_items(run_id);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


@contextmanager
def _conn():
    os.makedirs(CAMINHO_SAIDA, exist_ok=True)
    con = sqlite3.connect(CAMINHO_DB, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    """Cria banco e tabelas se não existirem (idempotente)."""
    try:
        with _conn() as con:
            con.executescript(_DDL)
        logger.debug(f"Banco inicializado: {CAMINHO_DB}")
    except Exception as exc:
        logger.error(f"Falha ao inicializar banco: {exc}")
        raise


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------

def criar_run(nome: str, arquivo_origem: str = None, email_destino: str = None) -> str:
    """Insere nova run com status RUNNING. Retorna run_id (UUID)."""
    run_id = str(uuid.uuid4())
    with _conn() as con:
        con.execute(
            """INSERT INTO runs (run_id, nome, arquivo_origem, started_at, status, email_destino)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, nome, arquivo_origem, _now_iso(), RUN_RUNNING, email_destino),
        )
    logger.info(f"Run criada: {run_id} | {nome}")
    return run_id


def atualizar_progresso_run(run_id: str, total_blocos: int,
                             blocos_processados: int, total_evidencias: int) -> None:
    with _conn() as con:
        con.execute(
            """UPDATE runs
               SET total_blocos=?, blocos_processados=?, total_evidencias=?
               WHERE run_id=?""",
            (total_blocos, blocos_processados, total_evidencias, run_id),
        )


def finalizar_run(run_id: str, status: str, erro_msg: str = None) -> None:
    """Marca run como COMPLETED, FAILED ou INCOMPLETA."""
    with _conn() as con:
        con.execute(
            """UPDATE runs
               SET status=?, finished_at=?, erro_msg=?
               WHERE run_id=?""",
            (status, _now_iso(), erro_msg, run_id),
        )
    logger.info(f"Run finalizada: {run_id} → {status}")


def get_run(run_id: str) -> dict | None:
    with _conn() as con:
        row = con.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
    return dict(row) if row else None


def listar_runs() -> list[dict]:
    """Todas as runs, mais recentes primeiro. Orphan RUNNING → INCOMPLETA."""
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM runs ORDER BY started_at DESC"
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        if d["status"] == RUN_RUNNING and d["finished_at"] is None:
            d["status"] = RUN_INCOMPLETA
        result.append(d)
    return result


def listar_runs_incompletas() -> list[dict]:
    """Runs que podem ser retomadas."""
    return [r for r in listar_runs()
            if r["status"] in (RUN_INCOMPLETA, RUN_FAILED, RUN_RUNNING)]


# ---------------------------------------------------------------------------
# Run items
# ---------------------------------------------------------------------------

def salvar_run_item(run_id: str, bloco_id: int, status: str,
                    evidencias_count: int = 0, erro_msg: str = None) -> None:
    with _conn() as con:
        con.execute(
            """INSERT OR REPLACE INTO run_items
               (run_id, bloco_id, status, evidencias_count, erro_msg, processed_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, bloco_id, status, evidencias_count, erro_msg, _now_iso()),
        )


def get_processed_block_ids(run_id: str) -> set:
    """Retorna set de bloco_ids já processados com status OK."""
    with _conn() as con:
        rows = con.execute(
            "SELECT bloco_id FROM run_items WHERE run_id=? AND status=?",
            (run_id, ITEM_OK),
        ).fetchall()
    return {r["bloco_id"] for r in rows}
