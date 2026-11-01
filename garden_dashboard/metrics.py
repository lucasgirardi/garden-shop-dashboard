"""Regras de negócio do dashboard (SPEC §4 e §5).

Funções puras: recebem DataFrames/parâmetros e devolvem DataFrames/números.
Nada aqui lê arquivos nem usa Streamlit.
"""
from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd

EFFECTIVE_STATUS = ("shipped", "pending", "processing")  # RN-01, RN-02
OPEN_STATUS = ("pending", "processing")                  # RN-02

ZERADO, CRITICO, ABAIXO, ATENCAO, OK = "Zerado", "Crítico", "Abaixo do nível", "Atenção", "OK"
DESCONTINUADO, SEM_NIVEL = "Descontinuado", "Sem nível definido"
P1, P2, P3, MONITORAR, NAO_REPOR, SEM_PRIORIDADE = (
    "P1 Urgente", "P2 Alta", "P3 Média", "Monitorar", "Não repor", "—")
PRIORITY_ORDER = {P1: 1, P2: 2, P3: 3, MONITORAR: 4, NAO_REPOR: 5, SEM_PRIORIDADE: 6}
MISSING_EMAIL = "não cadastrado"


def default_period(orders: pd.DataFrame) -> tuple[date, date]:
    """Período padrão = primeira e última data de pedido da base (RF-07)."""
    return orders["order_date"].min().date(), orders["order_date"].max().date()


def _in_period(orders: pd.DataFrame, start: date, end: date) -> pd.Series:
    d = orders["order_date"].dt.normalize()
    return (d >= pd.Timestamp(start)) & (d <= pd.Timestamp(end))  # datas inclusivas


def sales_by_product(orders: pd.DataFrame, order_items: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """RN-01/RN-02/RN-07: unidades em vendas efetivas no período, uma linha por produto."""
    valid = orders.loc[orders["status"].isin(EFFECTIVE_STATUS) & _in_period(orders, start, end), "order_id"]
    items = order_items[order_items["order_id"].isin(valid)]
    return (items.groupby("product_id", as_index=False)["quantity"].sum()
            .rename(columns={"quantity": "units_sold"}))


def open_orders_count(orders: pd.DataFrame, order_items: pd.DataFrame, start: date, end: date,
                      product_ids: Iterable[int]) -> int:
    """RF-05: pedidos pending/processing distintos no período com ao menos um produto visível."""
    open_ids = orders.loc[orders["status"].isin(OPEN_STATUS) & _in_period(orders, start, end), "order_id"]
    items = order_items[order_items["order_id"].isin(open_ids) & order_items["product_id"].isin(list(product_ids))]
    return int(items["order_id"].nunique())


def _status(row) -> str:
    """RN-05 (SPEC §4.4): vale a primeira condição verdadeira."""
    if row.discontinued:
        return DESCONTINUADO
    if row.reorder_level == 0:
        return SEM_NIVEL
    if row.quantity_on_hand == 0:
        return ZERADO
    if row.pct_level <= 0.50:
        return CRITICO
    if row.pct_level <= 1.00:
        return ABAIXO
    if row.pct_level <= 1.25:
        return ATENCAO
    return OK


def _priority(status: str, units_sold: float, median: float) -> str:
    """RN-06 (SPEC §4.5)."""
    if status in (ZERADO, CRITICO):
        return P1
    if status == ABAIXO:
        return P2 if units_sold >= median else P3
    if status == ATENCAO:
        return MONITORAR
    if status == DESCONTINUADO:
        return NAO_REPOR
    return SEM_PRIORIDADE


def build_product_view(data: dict[str, pd.DataFrame], start: date, end: date) -> pd.DataFrame:
    """RN-03 a RN-09: uma linha por produto, com estoque atual e vendas do período."""
    products = data["products"]
    sales = sales_by_product(data["orders"], data["order_items"], start, end)  # agregado ANTES do join (RN-08)

    view = (products
            .merge(data["categories"], on="category_id", how="left", validate="many_to_one")
            .merge(data["suppliers"][["supplier_id", "supplier_name", "contact_email"]],
                   on="supplier_id", how="left", validate="many_to_one")
            .merge(sales, on="product_id", how="left", validate="one_to_one"))
    if len(view) != len(products) or not view["product_id"].is_unique:  # SPEC §5, item 3
        raise RuntimeError("Duplicação detectada na visão por produto")

    view["units_sold"] = view["units_sold"].fillna(0).astype(int)
    view["stock_value"] = view["quantity_on_hand"] * view["cost"]
    view["pct_level"] = (view["quantity_on_hand"] / view["reorder_level"].where(view["reorder_level"] > 0)).astype(float)
    view["needs_reorder"] = (~view["discontinued"]) & (view["reorder_level"] > 0) & (
        view["quantity_on_hand"] <= view["reorder_level"])
    view["deficit"] = (view["reorder_level"] - view["quantity_on_hand"]).clip(lower=0).where(~view["discontinued"], 0)
    view["deficit"] = view["deficit"].astype(int)
    view["status"] = view.apply(_status, axis=1)

    median = view.loc[~view["discontinued"], "units_sold"].median() if (~view["discontinued"]).any() else 0
    view["priority"] = [_priority(s, u, median) for s, u in zip(view["status"], view["units_sold"])]
    return view


def apply_filters(view: pd.DataFrame, categories: list[str], suppliers: list[str],
                  include_discontinued: bool) -> pd.DataFrame:
    """RF-08 a RF-10. O período não é aplicado aqui (RN-07)."""
    mask = view["category_name"].isin(categories) & view["supplier_name"].isin(suppliers)
    if not include_discontinued:
        mask &= ~view["discontinued"]
    return view[mask].copy()


def compute_kpis(filtered: pd.DataFrame, open_orders: int) -> dict:
    """RF-01 a RF-05 sobre a visão filtrada. Vazio -> zeros (RF-17)."""
    return {
        "products_to_reorder": int(filtered["needs_reorder"].sum()) if not filtered.empty else 0,
        "zero_stock": int((filtered["status"] == ZERADO).sum()) if not filtered.empty else 0,
        "stock_value": float(filtered["stock_value"].sum()) if not filtered.empty else 0.0,
        "units_sold": int(filtered["units_sold"].sum()) if not filtered.empty else 0,
        "open_orders": int(open_orders),
    }


PRIORITY_COLUMNS = ["priority", "product_name", "category_name", "supplier_name", "quantity_on_hand",
                    "reorder_level", "deficit", "units_sold", "status"]


def priority_table(view: pd.DataFrame) -> pd.DataFrame:
    """RF-11: itens com alguma prioridade, do mais ao menos urgente."""
    t = view[view["priority"] != SEM_PRIORIDADE].copy()
    t["_ord"] = t["priority"].map(PRIORITY_ORDER)
    t = t.sort_values(["_ord", "pct_level", "product_name"], na_position="last")
    return t[PRIORITY_COLUMNS].reset_index(drop=True)


def sales_chart_data(view: pd.DataFrame) -> pd.DataFrame:
    """RF-12: todos os produtos filtrados (inclusive sem vendas), por vendas decrescentes."""
    return (view.sort_values(["units_sold", "product_name"], ascending=[False, True])
            [["product_name", "units_sold", "status"]].reset_index(drop=True))


def reorder_by_category(view: pd.DataFrame) -> pd.DataFrame:
    """RF-13: produtos e produtos a repor por categoria."""
    if view.empty:
        return pd.DataFrame(columns=["category_name", "products", "to_reorder"])
    return (view.groupby("category_name", as_index=False)
            .agg(products=("product_id", "count"), to_reorder=("needs_reorder", "sum"))
            .astype({"to_reorder": int})
            .sort_values(["to_reorder", "category_name"], ascending=[False, True])
            .reset_index(drop=True))


def supplier_summary(view: pd.DataFrame) -> pd.DataFrame:
    """RF-14: fornecedores dos produtos a repor, com contato."""
    r = view[view["needs_reorder"]] if not view.empty else view
    if r.empty:
        return pd.DataFrame(columns=["supplier_name", "products", "deficit_total", "contact_email"])
    s = (r.groupby("supplier_name", as_index=False)
         .agg(products=("product_id", "count"), deficit_total=("deficit", "sum"), contact_email=("contact_email", "first")))
    s["contact_email"] = s["contact_email"].fillna(MISSING_EMAIL)
    return s.sort_values(["products", "deficit_total"], ascending=False).reset_index(drop=True)
