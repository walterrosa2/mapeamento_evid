from src import mailer


class FakeSMTP:
    """Servidor SMTP fake usável como context manager."""
    instancias = []

    def __init__(self, *args, **kwargs):
        self.enviados = []
        self.logou = False
        self.starttls_chamado = False
        FakeSMTP.instancias.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.starttls_chamado = True

    def login(self, user, password):
        self.logou = True

    def sendmail(self, remetente, destinos, msg):
        self.enviados.append((remetente, destinos, msg))


def _configurar_smtp(monkeypatch):
    monkeypatch.setattr(mailer, "SMTP_HOST", "smtp.exemplo.com")
    monkeypatch.setattr(mailer, "SMTP_USER", "user@exemplo.com")
    monkeypatch.setattr(mailer, "SMTP_PASS", "senha-de-app")
    monkeypatch.setattr(mailer, "SMTP_PORT", 587)
    monkeypatch.setattr(mailer, "SMTP_TLS", True)


def test_envio_sucesso_com_factory_mock(monkeypatch):
    _configurar_smtp(monkeypatch)
    FakeSMTP.instancias.clear()

    ok = mailer.enviar_resultado(
        destino="dest@exemplo.com",
        run_nome="Run Teste",
        xlsx_path=None,
        resumo="resumo qualquer",
        smtp_factory=FakeSMTP,
    )

    assert ok is True
    assert len(FakeSMTP.instancias) == 1
    srv = FakeSMTP.instancias[0]
    assert srv.starttls_chamado is True
    assert srv.logou is True
    assert len(srv.enviados) == 1


def test_sem_destino_retorna_false(monkeypatch):
    _configurar_smtp(monkeypatch)
    ok = mailer.enviar_resultado(destino="", run_nome="R", xlsx_path=None, resumo="x")
    assert ok is False


def test_sem_config_smtp_retorna_false(monkeypatch):
    monkeypatch.setattr(mailer, "SMTP_HOST", "")
    monkeypatch.setattr(mailer, "SMTP_USER", "")
    monkeypatch.setattr(mailer, "SMTP_PASS", "")
    ok = mailer.enviar_resultado(destino="dest@exemplo.com", run_nome="R", xlsx_path=None, resumo="x")
    assert ok is False


def test_excecao_no_envio_retorna_false(monkeypatch):
    _configurar_smtp(monkeypatch)

    def factory_que_falha(*args, **kwargs):
        raise OSError("conexão recusada")

    ok = mailer.enviar_resultado(
        destino="dest@exemplo.com",
        run_nome="R",
        xlsx_path=None,
        resumo="x",
        smtp_factory=factory_que_falha,
    )
    assert ok is False
