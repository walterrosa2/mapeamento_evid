from src.controlador import extrair_campos


def test_json_puro():
    resp = '[{"Tipo de Evidência": "Contrato", "Trecho": "t", "Conteúdo": "c", "Resumo": "r", "Referência": "Pág. 1"}]'
    out = extrair_campos(resp)
    assert len(out) == 1
    assert out[0]["Tipo de Evidência"] == "Contrato"
    assert out[0]["Referência"] == "Pág. 1"


def test_json_com_cercas_e_texto_extra():
    resp = (
        "Aqui está a resposta:\n```json\n"
        '[{"Tipo de Evidência": "Nota Fiscal", "Trecho": "NF 123", "Conteúdo": "c", "Resumo": "r", "Referência": "Pág. 2"}]'
        "\n```\nFim."
    )
    out = extrair_campos(resp)
    assert len(out) == 1
    assert out[0]["Tipo de Evidência"] == "Nota Fiscal"


def test_json_truncado_recupera_objetos_completos():
    # Array cortado no meio do 3º objeto (limite de tokens)
    resp = (
        '[{"Tipo de Evidência": "A", "Trecho": "t1", "Conteúdo": "c1", "Resumo": "r1", "Referência": "Pág. 1"},'
        '{"Tipo de Evidência": "B", "Trecho": "t2", "Conteúdo": "c2", "Resumo": "r2", "Referência": "Pág. 2"},'
        '{"Tipo de Evidência": "C", "Trecho": "t3", "Conte'
    )
    out = extrair_campos(resp)
    # Recupera os 2 objetos completos, descarta o truncado
    assert len(out) == 2
    assert {o["Tipo de Evidência"] for o in out} == {"A", "B"}


def test_chaves_normalizadas():
    # Chaves em minúsculas / variações são normalizadas
    resp = '[{"tipo": "Pagamento", "trecho": "TED", "conteudo": "c", "resumo": "r", "pagina": "Pág. 5"}]'
    out = extrair_campos(resp)
    assert out[0]["Tipo de Evidência"] == "Pagamento"
    assert out[0]["Referência"] == "Pág. 5"


def test_fallback_markdown_simples():
    resp = (
        "| Tipo de Evidência | Trecho | Conteúdo | Resumo | Referência |\n"
        "|---|---|---|---|---|\n"
        "| Contrato | t | c | r | Pág. 9 |\n"
    )
    out = extrair_campos(resp)
    assert len(out) == 1
    assert out[0]["Tipo de Evidência"] == "Contrato"


def test_vazio_retorna_lista_vazia():
    assert extrair_campos("[]") == []
    assert extrair_campos("sem nada útil aqui") == []
