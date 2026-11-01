"""TEST-012: formatação de moeda."""
from garden_dashboard.formatting import brl_usd, brl_int


def test_moeda():
    assert brl_usd(4731) == "US$ 4.731,00"
    assert brl_usd(0) == "US$ 0,00"
    assert brl_usd(448.5) == "US$ 448,50"
    assert brl_usd(1234567.891) == "US$ 1.234.567,89"


def test_inteiro():
    assert brl_int(1234) == "1.234"
    assert brl_int(0) == "0"
