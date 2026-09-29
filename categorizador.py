"""
Regras de categorização e leitura de extratos.
Módulo independente da interface, para poder ser testado e reutilizado.
"""

from __future__ import annotations

import unicodedata

import pandas as pd

REGRAS: dict[str, list[str]] = {
    "Alimentação": ["ifood", "restaurante", "lanchonete", "padaria", "mercado", "supermercado", "acougue"],
    "Transporte": ["uber", "99app", "posto", "combustivel", "estacionamento", "pedagio", "metro", "onibus"],
    "Moradia": ["aluguel", "condominio", "energia", "luz", "agua", "internet", "gas"],
    "Saúde": ["farmacia", "drogaria", "hospital", "clinica", "plano de saude"],
    "Educação": ["faculdade", "curso", "escola", "udemy", "alura"],
    "Lazer": ["cinema", "netflix", "spotify", "steam", "show", "ingresso"],
    "Compras": ["magazine", "shopee", "amazon", "mercado livre", "loja"],
    "Receitas": ["salario", "pix recebido", "deposito", "transferencia recebida", "reembolso"],
}

CATEGORIA_PADRAO = "Outros"
COLUNAS_OBRIGATORIAS = {"data", "descricao", "valor"}

# Palavras-chave mais longas são testadas primeiro, para que expressões específicas
# ("mercado livre") tenham prioridade sobre termos genéricos ("mercado").
_PALAVRAS_ORDENADAS = sorted(
    ((palavra, categoria) for categoria, palavras in REGRAS.items() for palavra in palavras),
    key=lambda item: len(item[0]),
    reverse=True,
)


def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, para comparação tolerante."""
    texto = str(texto).lower().strip()
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def categorizar(descricao: str) -> str:
    descricao_normalizada = normalizar(descricao)
    for palavra, categoria in _PALAVRAS_ORDENADAS:
        if palavra in descricao_normalizada:
            return categoria
    return CATEGORIA_PADRAO


def carregar_extrato(origem) -> pd.DataFrame:
    """Lê o CSV, valida colunas, converte tipos e adiciona categoria e mês."""
    df = pd.read_csv(origem)
    df.columns = [c.lower().strip() for c in df.columns]

    faltando = COLUNAS_OBRIGATORIAS - set(df.columns)
    if faltando:
        raise ValueError(f"Colunas obrigatórias ausentes no CSV: {', '.join(sorted(faltando))}")

    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["data", "valor"]).copy()

    df["categoria"] = df["descricao"].apply(categorizar)
    df["mes"] = df["data"].dt.to_period("M").dt.to_timestamp()
    return df.sort_values("data").reset_index(drop=True)


def formatar_moeda(valor: float) -> str:
    """Formata no padrão brasileiro: R$ 1.234,56"""
    texto = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"-R$ {texto}" if valor < 0 else f"R$ {texto}"
