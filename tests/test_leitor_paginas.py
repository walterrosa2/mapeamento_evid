from src import leitor_txt
from src.leitor_txt import detectar_paginas, dividir_por_paginas


DELIM = "---Página---"

DOC = (
    f"{DELIM} 1\nConteúdo da página um. Notas e contratos.\n"
    f"{DELIM} 2\nConteúdo da página dois. Pagamentos.\n"
    f"{DELIM} 3\nConteúdo da página três. Recibos.\n"
)


def test_detecta_paginas_pelo_delimitador():
    paginas = detectar_paginas(DOC, DELIM)
    assert len(paginas) == 3
    assert [n for n, _ in paginas] == [1, 2, 3]


def test_sem_delimitador_retorna_vazio():
    # Documento sem o marcador → lista vazia (aciona fallback no chamador)
    assert detectar_paginas("texto sem marcador algum", DELIM) == []
    # Delimitador vazio também
    assert detectar_paginas(DOC, "") == []


def test_dividir_por_paginas_agrupa():
    blocos = dividir_por_paginas(DOC, DELIM, paginas_por_bloco=2)
    # 3 páginas, 2 por bloco → 2 blocos
    assert len(blocos) == 2


def test_teto_de_tamanho_subdivide(monkeypatch):
    # Força um teto pequeno para validar a subdivisão de blocos grandes
    monkeypatch.setattr(leitor_txt, "MAX_CHARS_BLOCO", 50)
    pagina_grande = "palavra " * 200  # ~1600 chars
    doc = f"{DELIM} 1\n{pagina_grande}"
    blocos = dividir_por_paginas(doc, DELIM, paginas_por_bloco=10)
    assert len(blocos) > 1
    assert all(len(b) <= 60 for b in blocos)  # margem sobre o corte em ponto final
