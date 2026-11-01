"""Formatação de números no padrão brasileiro (valores em US$, conforme o dicionário)."""


def brl_usd(value: float) -> str:
    """4731 -> 'US$ 4.731,00'."""
    texto = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"US$ {texto}"


def brl_int(value: float) -> str:
    """1234 -> '1.234'."""
    return f"{int(value):,}".replace(",", ".")
