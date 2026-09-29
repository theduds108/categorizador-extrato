import io

import pytest

from categorizador import carregar_extrato, categorizar, formatar_moeda


@pytest.mark.parametrize(
    "descricao, esperado",
    [
        ("IFOOD *RESTAURANTE SABOR", "Alimentação"),
        ("UBER *TRIP", "Transporte"),
        ("Farmácia São João", "Saúde"),          # acentos e maiúsculas
        ("MERCADO LIVRE ELETRONICOS", "Compras"), # termo específico vence o genérico
        ("SUPERMERCADO BOM PRECO", "Alimentação"),
        ("PIX RECEBIDO JOAO", "Receitas"),
        ("TARIFA BANCARIA", "Outros"),
    ],
)
def test_categorizar(descricao, esperado):
    assert categorizar(descricao) == esperado


def test_carregar_extrato_valida_colunas():
    csv = io.StringIO("data,historico,valor\n01/09/2026,UBER,-10\n")
    with pytest.raises(ValueError, match="descricao"):
        carregar_extrato(csv)


def test_carregar_extrato_descarta_linhas_invalidas():
    csv = io.StringIO(
        "data,descricao,valor\n"
        "01/09/2026,UBER,-10\n"
        "data-invalida,NETFLIX,-39.90\n"
        "03/09/2026,SPOTIFY,abc\n"
    )
    df = carregar_extrato(csv)
    assert len(df) == 1
    assert df.iloc[0]["categoria"] == "Transporte"


def test_formatar_moeda():
    assert formatar_moeda(1234.5) == "R$ 1.234,50"
    assert formatar_moeda(-89.9) == "-R$ 89,90"
