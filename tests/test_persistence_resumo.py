from src import persistence


def test_init_cria_e_migra_coluna_resumo(tmp_path, monkeypatch):
    db = tmp_path / "runs.db"
    monkeypatch.setattr(persistence, "CAMINHO_DB", str(db))
    monkeypatch.setattr(persistence, "CAMINHO_SAIDA", str(tmp_path))

    persistence.init_db()

    with persistence._conn() as con:
        colunas = {row["name"] for row in con.execute("PRAGMA table_info(runs)").fetchall()}
    assert "resumo_processo" in colunas


def test_salvar_e_ler_resumo(tmp_path, monkeypatch):
    db = tmp_path / "runs.db"
    monkeypatch.setattr(persistence, "CAMINHO_DB", str(db))
    monkeypatch.setattr(persistence, "CAMINHO_SAIDA", str(tmp_path))

    persistence.init_db()
    run_id = persistence.criar_run(nome="Teste", arquivo_origem="x.txt")

    persistence.salvar_resumo_run(run_id, "TIPO DE AÇÃO: Reclamação Trabalhista")

    run = persistence.get_run(run_id)
    assert run is not None
    assert run["resumo_processo"] == "TIPO DE AÇÃO: Reclamação Trabalhista"


def test_migracao_idempotente_em_banco_legado(tmp_path, monkeypatch):
    """Banco antigo sem a coluna recebe a coluna sem perder dados."""
    db = tmp_path / "runs.db"
    monkeypatch.setattr(persistence, "CAMINHO_DB", str(db))
    monkeypatch.setattr(persistence, "CAMINHO_SAIDA", str(tmp_path))

    # Cria um banco "legado" sem a coluna resumo_processo
    import sqlite3
    con = sqlite3.connect(str(db))
    con.execute(
        "CREATE TABLE runs (run_id TEXT PRIMARY KEY, nome TEXT NOT NULL, started_at TEXT NOT NULL, status TEXT NOT NULL)"
    )
    con.execute(
        "INSERT INTO runs (run_id, nome, started_at, status) VALUES ('r1', 'Legado', '2026-01-01 00:00:00', 'COMPLETED')"
    )
    con.commit()
    con.close()

    # init_db deve migrar sem erro e preservar a run existente
    persistence.init_db()
    run = persistence.get_run("r1")
    assert run is not None
    assert run["nome"] == "Legado"
    assert run["resumo_processo"] is None
