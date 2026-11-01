"""TEST-011: critérios de aceitação do PRD (CA-001 a CA-010) com a base completa."""
from datetime import date

import pytest

from garden_dashboard import metrics as m
from garden_dashboard.loader import load_data

INICIO, FIM = date(2024, 1, 15), date(2024, 6, 14)


@pytest.fixture(scope="module")
def dados():
    from pathlib import Path
    return load_data(Path(__file__).resolve().parents[1] / "data" / "raw")


def _kpis(dados, inicio=INICIO, fim=FIM, cats=None, forns=None, desc=False):
    v = m.build_product_view(dados, inicio, fim)
    f = m.apply_filters(v, cats if cats is not None else v.category_name.unique().tolist(),
                        forns if forns is not None else dados["suppliers"].supplier_name.tolist(), desc)
    return f, m.compute_kpis(f, m.open_orders_count(dados["orders"], dados["order_items"], inicio, fim, f.product_id))


def test_periodo_padrao_e_o_da_base(dados):
    assert m.default_period(dados["orders"]) == (INICIO, FIM)


def test_ca01_indicadores_padrao(dados):
    _, k = _kpis(dados)
    assert k == {"products_to_reorder": 5, "zero_stock": 1, "stock_value": pytest.approx(4731.0),
                 "units_sold": 86, "open_orders": 6}


def test_ca02_lista_de_prioridades(dados):
    f, _ = _kpis(dados)
    t = m.priority_table(f)
    assert list(zip(t.product_name, t.priority)) == [
        ("Hanging Basket", "P1 Urgente"), ("Tomato Seeds 'Roma'", "P1 Urgente"), ("Hand Cultivator", "P1 Urgente"),
        ("Pothos 'Golden'", "P2 Alta"), ("Orchid Food", "P3 Média"), ("Solar Lantern", "Monitorar")]


def test_ca03_cancelado(dados):
    f, _ = _kpis(dados)
    assert f.set_index("product_name").loc["Pruning Shears", "units_sold"] == 1


def test_ca04_incluir_descontinuados(dados):
    f, k = _kpis(dados, desc=True)
    bird = f.set_index("product_name").loc["Bird Feeder"]
    assert (bird.status, bird.priority) == ("Descontinuado", "Não repor")
    assert k["products_to_reorder"] == 5 and k["stock_value"] == pytest.approx(4763.0)


def test_ca05_categoria_tools(dados):
    _, k = _kpis(dados, cats=["Tools"])
    assert (k["products_to_reorder"], k["stock_value"], k["units_sold"]) == (1, pytest.approx(448.5), 5)


def test_ca06_fornecedor_sem_produtos(dados):
    f, k = _kpis(dados, forns=["RootWorks Supply"])
    assert f.empty and k["products_to_reorder"] == 0 and k["stock_value"] == 0


def test_ca07_periodo_sem_vendas(dados):
    _, k = _kpis(dados, date(2024, 7, 1), date(2024, 7, 31))
    assert (k["units_sold"], k["open_orders"], k["products_to_reorder"]) == (0, 0, 5)
    assert k["stock_value"] == pytest.approx(4731.0)


def test_ca08_produto_sem_vendas(dados):
    f, _ = _kpis(dados)
    assert f.set_index("product_name").loc["Hanging Basket", "units_sold"] == 0


def test_ca09_sem_duplicacao(dados):
    f, _ = _kpis(dados)
    assert f.set_index("product_name").loc["Fiddle-Leaf Fig", "stock_value"] == 252


def test_ca10_email_ausente(dados):
    f, _ = _kpis(dados)
    s = m.supplier_summary(f).set_index("supplier_name")
    assert s.loc["Ironwood Tools", "contact_email"] == "não cadastrado"
