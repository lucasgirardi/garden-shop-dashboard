"""T-04 a T-10: regras de negócio (SPEC §4, §5 e exemplos da §7.1)."""
from datetime import date

import pandas as pd
import pytest

from garden_dashboard import metrics as m
from garden_dashboard.loader import load_data

INICIO, FIM = date(2024, 1, 1), date(2024, 12, 31)


@pytest.fixture
def dados(recorte_dir):
    return load_data(recorte_dir)


@pytest.fixture
def view(dados):
    return m.build_product_view(dados, INICIO, FIM)


def _linha(v, nome):
    return v.loc[v.product_name == nome].iloc[0]


def _todos(v):
    return m.apply_filters(v, v.category_name.unique().tolist(), v.supplier_name.unique().tolist(), False)


# T-04 vendas efetivas ------------------------------------------------------
def test_unidades_vendidas_por_produto_recorte(view):
    vendas = dict(zip(view.product_name, view.units_sold))
    assert vendas == {"Fiddle-Leaf Fig": 4, "Pruning Shears": 1, "Hand Cultivator": 2,
                      "Hanging Basket": 0, "Bird Feeder": 0}


def test_pedido_cancelado_nao_conta(dados):
    vendas = m.sales_by_product(dados["orders"], dados["order_items"], INICIO, FIM)
    assert vendas.set_index("product_id").loc[9, "units_sold"] == 1  # pedido 17 cancelado excluído


def test_pending_e_processing_contam_como_venda(dados):
    vendas = m.sales_by_product(dados["orders"], dados["order_items"], INICIO, FIM)
    assert vendas.set_index("product_id").loc[11, "units_sold"] == 2  # pedido 7 pending


def test_indicador_unidades_vendidas_recorte(view):
    assert m.compute_kpis(_todos(view), 0)["units_sold"] == 7


def test_periodo_filtra_vendas_com_datas_inclusivas(dados):
    v = m.build_product_view(dados, date(2024, 3, 2), date(2024, 5, 1))  # bordas = pedidos 1 e 7
    assert dict(zip(v.product_name, v.units_sold))["Fiddle-Leaf Fig"] == 1
    assert m.compute_kpis(_todos(v), 0)["units_sold"] == 4


# T-05 valor do estoque ----------------------------------------------------
def test_valor_do_estoque_recorte(view):
    assert m.compute_kpis(_todos(view), 0)["stock_value"] == pytest.approx(460.50)


def test_valor_do_estoque_com_descontinuados(view):
    f = m.apply_filters(view, view.category_name.unique().tolist(), view.supplier_name.unique().tolist(), True)
    assert m.compute_kpis(f, 0)["stock_value"] == pytest.approx(492.50)


# T-06 status e prioridade -------------------------------------------------
def _dados_sinteticos(produtos):
    """produtos: lista de (id, qoh, nivel, descontinuado, unidades_vendidas)."""
    products = pd.DataFrame(
        [{"product_id": i, "product_name": f"P{i}", "category_id": 1, "supplier_id": 1, "cost": 1.0,
          "quantity_on_hand": q, "reorder_level": r, "discontinued": d} for i, q, r, d, _ in produtos])
    orders = pd.DataFrame([{"order_id": 1, "order_date": pd.Timestamp("2024-01-10"), "status": "shipped"}])
    items = pd.DataFrame([{"order_item_id": i, "order_id": 1, "product_id": i, "quantity": u}
                          for i, _, _, _, u in produtos if u > 0])
    if items.empty:
        items = pd.DataFrame(columns=["order_item_id", "order_id", "product_id", "quantity"])
    return {"products": products, "orders": orders, "order_items": items,
            "categories": pd.DataFrame([{"category_id": 1, "category_name": "Cat"}]),
            "suppliers": pd.DataFrame([{"supplier_id": 1, "supplier_name": "Forn", "contact_email": None}])}


@pytest.mark.parametrize("qoh,nivel,status,repor", [
    (0, 10, "Zerado", True),
    (5, 10, "Crítico", True),            # exatamente 50%
    (6, 10, "Abaixo do nível", True),
    (10, 10, "Abaixo do nível", True),   # igual ao nível → repõe (≤)
    (10, 8, "Atenção", False),           # exatamente 125%
    (11, 8, "OK", False),
    (0, 0, "Sem nível definido", False), # sem divisão por zero
    (5, 0, "Sem nível definido", False),
])
def test_faixas_de_status(qoh, nivel, status, repor):
    v = m.build_product_view(_dados_sinteticos([(1, qoh, nivel, False, 0)]), INICIO, FIM)
    assert v.iloc[0]["status"] == status
    assert bool(v.iloc[0]["needs_reorder"]) is repor


def test_prioridade_usa_mediana_das_vendas():
    # vendas dos ativos: 5, 2, 3, 0 → mediana 2,5
    v = m.build_product_view(_dados_sinteticos([
        (1, 8, 12, False, 5),   # Abaixo, 5 ≥ 2,5 → P2
        (2, 6, 10, False, 2),   # Abaixo, 2 < 2,5 → P3
        (3, 3, 10, False, 3),   # Crítico → P1
        (4, 9, 8, False, 0),    # Atenção → Monitorar
    ]), INICIO, FIM)
    assert dict(zip(v.product_name, v.priority)) == {"P1": "P2 Alta", "P2": "P3 Média", "P3": "P1 Urgente", "P4": "Monitorar"}


def test_prioridade_nao_muda_com_filtro_de_categoria(raw_dir):
    v = m.build_product_view(load_data(raw_dir), date(2024, 1, 15), date(2024, 6, 14))
    so_houseplants = m.apply_filters(v, ["Houseplants"], v.supplier_name.unique().tolist(), False)
    assert _linha(so_houseplants, "Pothos 'Golden'")["priority"] == "P2 Alta"


def test_status_e_prioridade_recorte(view):
    esperado = {"Fiddle-Leaf Fig": ("OK", "—"), "Pruning Shears": ("OK", "—"),
                "Hand Cultivator": ("Crítico", "P1 Urgente"), "Hanging Basket": ("Zerado", "P1 Urgente"),
                "Bird Feeder": ("Descontinuado", "Não repor")}
    assert {r.product_name: (r.status, r.priority) for r in view.itertuples()} == esperado


def test_deficit(view):
    assert dict(zip(view.product_name, view.deficit)) == {
        "Fiddle-Leaf Fig": 0, "Pruning Shears": 0, "Hand Cultivator": 7, "Hanging Basket": 10, "Bird Feeder": 0}


# T-07 descontinuados ------------------------------------------------------
def test_descontinuado_nunca_e_reposto(view):
    bird = _linha(view, "Bird Feeder")
    assert bird["quantity_on_hand"] <= bird["reorder_level"]  # estaria abaixo do nível…
    assert not bird["needs_reorder"]                            # …mas não é recomendado


def test_descontinuados_ocultos_por_padrao_e_fora_dos_kpis(view):
    cats, forns = view.category_name.unique().tolist(), view.supplier_name.unique().tolist()
    sem = m.apply_filters(view, cats, forns, False)
    com = m.apply_filters(view, cats, forns, True)
    assert "Bird Feeder" not in set(sem.product_name)
    assert "Bird Feeder" in set(com.product_name)
    for f in (sem, com):
        k = m.compute_kpis(f, 0)
        assert k["products_to_reorder"] == 2 and k["zero_stock"] == 1


def test_descontinuado_aparece_como_nao_repor_na_lista(view):
    com = m.apply_filters(view, view.category_name.unique().tolist(), view.supplier_name.unique().tolist(), True)
    t = m.priority_table(com)
    assert t.iloc[-1]["product_name"] == "Bird Feeder" and t.iloc[-1]["priority"] == "Não repor"


# T-08 duplicação ----------------------------------------------------------
def test_uma_linha_por_produto(dados, view):
    assert len(view) == len(dados["products"])
    assert view.product_id.is_unique


def test_valor_nao_duplica_com_varios_pedidos(dados, view):
    ingenuo = dados["products"].merge(dados["order_items"], on="product_id")
    ingenuo_fiddle = (ingenuo.loc[ingenuo.product_id == 1, "quantity_on_hand"] * 18).sum()
    assert ingenuo_fiddle == 756  # o join direto triplicaria o valor
    assert _linha(view, "Fiddle-Leaf Fig")["stock_value"] == 252


# T-09 dados vazios --------------------------------------------------------
def test_filtro_sem_resultado(view):
    vazio = m.apply_filters(view, ["Inexistente"], view.supplier_name.unique().tolist(), True)
    assert vazio.empty
    assert m.compute_kpis(vazio, 0) == {"products_to_reorder": 0, "zero_stock": 0, "stock_value": 0.0,
                                       "units_sold": 0, "open_orders": 0}
    assert m.priority_table(vazio).empty
    assert m.sales_chart_data(vazio).empty
    assert m.reorder_by_category(vazio).empty
    assert m.supplier_summary(vazio).empty


def test_lista_vazia_de_categorias_nao_retorna_nada(view):
    assert m.apply_filters(view, [], view.supplier_name.unique().tolist(), False).empty


def test_periodo_sem_vendas_mantem_estoque(dados):
    v = _todos(m.build_product_view(dados, date(2024, 7, 1), date(2024, 7, 31)))
    k = m.compute_kpis(v, m.open_orders_count(dados["orders"], dados["order_items"],
                                              date(2024, 7, 1), date(2024, 7, 31), v.product_id))
    assert k["units_sold"] == 0 and k["open_orders"] == 0
    assert k["stock_value"] == pytest.approx(460.50) and k["products_to_reorder"] == 2


def test_produto_sem_vendas_aparece_no_grafico(view):
    g = m.sales_chart_data(_todos(view))
    assert "Hanging Basket" in set(g.product_name)
    assert g.iloc[0]["product_name"] == "Fiddle-Leaf Fig"  # ordenado por vendas


# T-10 pedidos em aberto ---------------------------------------------------
def test_pedidos_em_aberto(dados):
    o, i = dados["orders"], dados["order_items"]
    assert m.open_orders_count(o, i, INICIO, FIM, [1, 9, 11, 14]) == 1        # pedido 7
    assert m.open_orders_count(o, i, INICIO, FIM, [1, 14]) == 0               # pedido 7 não tem esses produtos
    assert m.open_orders_count(o, i, date(2024, 5, 2), FIM, [1, 9, 11, 14]) == 0  # fora do período


# Tabelas auxiliares -------------------------------------------------------
def test_tabela_de_prioridades_ordenada(view):
    t = m.priority_table(_todos(view))
    assert list(t.product_name) == ["Hanging Basket", "Hand Cultivator"]  # P1, menor % primeiro


def test_resumo_de_fornecedores(view):
    s = m.supplier_summary(_todos(view)).set_index("supplier_name")
    assert s.loc["Ironwood Tools"].tolist() == [1, 7, "não cadastrado"]
    assert s.loc["Terra Pots Co"].tolist() == [1, 10, "hello@terrapots.example"]
    assert "GreenLeaf Wholesale" not in s.index


def test_reposicao_por_categoria(view):
    c = m.reorder_by_category(_todos(view)).set_index("category_name")
    assert c.loc["Tools"].tolist() == [2, 1]
    assert c.loc["Houseplants"].tolist() == [1, 0]
