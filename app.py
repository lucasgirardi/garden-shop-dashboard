"""Dashboard de Estoque e Reposição da Garden Shop (interface Streamlit).

Autor: Lucas Girardi. Sem fórmulas aqui: todas as regras estão em garden_dashboard/metrics.py.
Executar: streamlit run app.py
"""
import os
from datetime import date
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from garden_dashboard import metrics as m
from garden_dashboard.formatting import brl_int, brl_usd
from garden_dashboard.loader import DataError, load_data

# GARDEN_DATA_DIR permite apontar outra pasta (usado nos testes de erro, RF-020)
DATA_DIR = Path(os.environ.get("GARDEN_DATA_DIR", Path(__file__).parent / "data" / "raw"))

# RN-011: paleta sem vermelho (SPEC REQ-009)
STATUS_COLORS = {
    m.ZERADO: "#3B3B3B", m.CRITICO: "#D9822B", m.ABAIXO: "#E8B931", m.ATENCAO: "#7A9CC6",
    m.OK: "#4F9A6B", m.DESCONTINUADO: "#A8A8A8", m.SEM_NIVEL: "#B9A6D6",
}
COLOR_SCALE = alt.Scale(domain=list(STATUS_COLORS), range=list(STATUS_COLORS.values()))

MSG_SEM_PRODUTOS = "Nenhum produto encontrado para os filtros selecionados."
MSG_SEM_VENDAS = "Sem vendas efetivas no período selecionado."
MSG_SEM_REPOSICAO = "Nenhum produto precisa de reposição nos filtros selecionados."

st.set_page_config(page_title="Garden Shop · Estoque e Reposição", page_icon="🌿", layout="wide")


@st.cache_data
def carregar(path: str):
    return load_data(Path(path))


# ---------------------------------------------------------------- dados (RF-020)
try:
    dados = carregar(str(DATA_DIR))
except DataError as e:
    st.warning(f"Não foi possível carregar os dados: {e}")
    st.stop()

inicio_padrao, fim_padrao = m.default_period(dados["orders"])

# ---------------------------------------------------------------- filtros (RF-007 a RF-010)
st.sidebar.header("Filtros")
periodo = st.sidebar.date_input(
    "Período de vendas", value=(inicio_padrao, fim_padrao),
    min_value=date(inicio_padrao.year, 1, 1), max_value=date(fim_padrao.year, 12, 31), format="DD/MM/YYYY",
    help="Afeta apenas as vendas e os pedidos em aberto. O estoque é sempre a posição atual.")
if isinstance(periodo, (tuple, list)) and len(periodo) == 2:
    inicio, fim = sorted(periodo)
else:  # usuário escolheu só uma data
    inicio = fim = periodo[0] if isinstance(periodo, (tuple, list)) else periodo

todas_categorias = sorted(dados["categories"]["category_name"])
todos_fornecedores = sorted(dados["suppliers"]["supplier_name"])
categorias = st.sidebar.multiselect("Categoria", todas_categorias, default=todas_categorias)
fornecedores = st.sidebar.multiselect("Fornecedor", todos_fornecedores, default=todos_fornecedores)
incluir_desc = st.sidebar.toggle("Incluir descontinuados", value=False,
                                 help="Descontinuados nunca são recomendados para reposição (RN-004).")

# ---------------------------------------------------------------- cálculo
visao = m.build_product_view(dados, inicio, fim)
filtrada = m.apply_filters(visao, categorias, fornecedores, incluir_desc)
abertos = m.open_orders_count(dados["orders"], dados["order_items"], inicio, fim, filtrada["product_id"])
k = m.compute_kpis(filtrada, abertos)

# ---------------------------------------------------------------- cabeçalho (RF-016)
st.title("🌿 Garden Shop · Estoque e Reposição")
st.caption(
    f"Autor: Lucas Girardi · Estoque: **posição atual** (`quantity_on_hand`) · "
    f"Vendas: **{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}**, pedidos cancelados excluídos · "
    f"Descontinuados: **{'visíveis (não repor)' if incluir_desc else 'ocultos'}**")

# ---------------------------------------------------------------- indicadores (RF-001 a RF-006)
c = st.columns(5)
c[0].metric("Produtos a repor", brl_int(k["products_to_reorder"]),
            help="Produtos ativos com estoque ≤ nível de reposição (RN-003).")
c[0].caption("Posição atual")
c[1].metric("Produtos zerados", brl_int(k["zero_stock"]), help="Produtos ativos com estoque = 0.")
c[1].caption("Posição atual")
c[2].metric("Valor do estoque (custo)", brl_usd(k["stock_value"]), help="Σ estoque × custo.")
c[2].caption("Posição atual")
c[3].metric("Unidades vendidas", brl_int(k["units_sold"]), help="Pedidos shipped, pending e processing (RN-001).")
c[3].caption("Período selecionado")
c[4].metric("Pedidos em aberto", brl_int(k["open_orders"]), help="Pedidos pending + processing (RN-002).")
c[4].caption("Período selecionado")

if filtrada.empty:  # RF-017
    st.info(MSG_SEM_PRODUTOS)
    st.stop()


def _colorir_status(col: pd.Series):
    return [f"background-color: {STATUS_COLORS.get(v, '')}; color: {'white' if v in (m.ZERADO, m.OK) else 'black'}"
            for v in col]


# ---------------------------------------------------------------- lista de prioridades (RF-011)
st.subheader("Lista de prioridades de reposição")
prioridades = m.priority_table(filtrada)
if not filtrada["needs_reorder"].any():
    st.info(MSG_SEM_REPOSICAO)  # RF-019
if not prioridades.empty:
    tabela = prioridades.rename(columns={
        "priority": "Prioridade", "product_name": "Produto", "category_name": "Categoria",
        "supplier_name": "Fornecedor", "quantity_on_hand": "Estoque", "reorder_level": "Nível de reposição",
        "deficit": "Déficit (un.)", "units_sold": "Vendidas no período", "status": "Status"})
    st.dataframe(tabela.style.apply(_colorir_status, subset=["Status"]), hide_index=True, use_container_width=True)
    st.caption("P1 Urgente = zerado ou crítico (≤ 50% do nível) · P2/P3 = abaixo do nível, com vendas acima/abaixo "
               "da mediana · Monitorar = até 125% do nível · Déficit = mínimo para voltar ao nível de reposição.")

# ---------------------------------------------------------------- visualizações (RF-012 a RF-014)
esq, dir_ = st.columns([1.1, 1])
with esq:
    st.subheader("Unidades vendidas por produto")
    vendas = m.sales_chart_data(filtrada)
    if vendas["units_sold"].sum() == 0:  # RF-018
        st.info(MSG_SEM_VENDAS)
    else:
        grafico = alt.Chart(vendas).mark_bar().encode(
            x=alt.X("units_sold:Q", title="Unidades vendidas no período"),
            y=alt.Y("product_name:N", sort=None, title=None, axis=alt.Axis(labelOverlap=False, labelLimit=180)),
            color=alt.Color("status:N", scale=COLOR_SCALE, title="Status do estoque",
                            legend=alt.Legend(orient="bottom", columns=4)),
            tooltip=[alt.Tooltip("product_name", title="Produto"), alt.Tooltip("units_sold", title="Unidades"),
                     alt.Tooltip("status", title="Status")],
        ).properties(height=alt.Step(20))
        st.altair_chart(grafico, use_container_width=True)
        st.caption("Cor = status do estoque atual. Produtos sem vendas aparecem com zero.")

with dir_:
    st.subheader("Produtos a repor por categoria")
    cat = m.reorder_by_category(filtrada)
    if cat["to_reorder"].sum() == 0:
        st.info(MSG_SEM_REPOSICAO)
    else:
        cat_long = cat.assign(outros=cat["products"] - cat["to_reorder"]).melt(
            id_vars="category_name", value_vars=["to_reorder", "outros"], var_name="grupo", value_name="n")
        cat_long["grupo"] = cat_long["grupo"].map({"to_reorder": "A repor", "outros": "Demais produtos"})
        graf_cat = alt.Chart(cat_long).mark_bar().encode(
            x=alt.X("sum(n):Q", stack="zero", title="Produtos", axis=alt.Axis(tickMinStep=1, format="d")),
            y=alt.Y("category_name:N", sort=list(cat["category_name"]), title=None,
                    axis=alt.Axis(labelOverlap=False, labelLimit=180)),
            color=alt.Color("grupo:N", scale=alt.Scale(domain=["A repor", "Demais produtos"],
                                                       range=["#D9822B", "#D6DDE6"]),
                            title=None, legend=alt.Legend(orient="bottom")),
            order=alt.Order("grupo:N", sort="ascending"),
            tooltip=[alt.Tooltip("category_name", title="Categoria"), alt.Tooltip("grupo", title="Grupo"),
                     alt.Tooltip("sum(n)", title="Produtos")],
        ).properties(height=alt.Step(26))
        st.altair_chart(graf_cat, use_container_width=True)

    st.subheader("Fornecedores dos produtos a repor")
    forn = m.supplier_summary(filtrada)
    if forn.empty:
        st.info(MSG_SEM_REPOSICAO)
    else:
        st.dataframe(forn.rename(columns={"supplier_name": "Fornecedor", "products": "Produtos a repor",
                                          "deficit_total": "Déficit (un.)", "contact_email": "E-mail"}),
                     hide_index=True, use_container_width=True,
                     column_config={"Produtos a repor": st.column_config.NumberColumn(width="small"),
                                    "Déficit (un.)": st.column_config.NumberColumn(width="small")})

# ---------------------------------------------------------------- detalhe (RF-015)
with st.expander(f"Todos os produtos filtrados ({len(filtrada)})"):
    detalhe = filtrada[["product_name", "category_name", "supplier_name", "quantity_on_hand", "reorder_level",
                        "cost", "stock_value", "units_sold", "status", "priority"]].sort_values("product_name")
    st.dataframe(detalhe.rename(columns={
        "product_name": "Produto", "category_name": "Categoria", "supplier_name": "Fornecedor",
        "quantity_on_hand": "Estoque", "reorder_level": "Nível", "cost": "Custo (US$)",
        "stock_value": "Valor (US$)", "units_sold": "Vendidas", "status": "Status", "priority": "Prioridade"}),
        hide_index=True, use_container_width=True,
        column_config={"Custo (US$)": st.column_config.NumberColumn(format="%.2f"),
                       "Valor (US$)": st.column_config.NumberColumn(format="%.2f")})
