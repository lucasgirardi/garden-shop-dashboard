"""T-13: interface Streamlit (CA-01, CA-04, CA-06, CA-07, RF-20) via AppTest."""
from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"
MSG_SEM_PRODUTOS = "Nenhum produto encontrado para os filtros selecionados."
MSG_SEM_VENDAS = "Sem vendas efetivas no período selecionado."


def _app():
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.run()
    assert not at.exception
    return at


def _metricas(at):
    return {mt.label: mt.value for mt in at.metric}


def test_ca01_tela_inicial():
    at = _app()
    assert _metricas(at) == {"Produtos a repor": "5", "Produtos zerados": "1",
                            "Valor do estoque (custo)": "US$ 4.731,00", "Unidades vendidas": "86",
                            "Pedidos em aberto": "6"}
    assert not at.error  # RN-11: nenhum st.error (vermelho)


def test_ca04_incluir_descontinuados():
    at = _app()
    at.toggle[0].set_value(True).run()
    m = _metricas(at)
    assert m["Valor do estoque (custo)"] == "US$ 4.763,00" and m["Produtos a repor"] == "5"
    assert "Bird Feeder" in at.dataframe[0].value["Produto"].tolist()


def test_ca06_fornecedor_sem_produtos():
    at = _app()
    forn = [w for w in at.multiselect if w.label == "Fornecedor"][0]
    forn.set_value(["RootWorks Supply"]).run()
    assert _metricas(at)["Produtos a repor"] == "0"
    assert _metricas(at)["Valor do estoque (custo)"] == "US$ 0,00"
    assert any(MSG_SEM_PRODUTOS in i.value for i in at.info)
    assert not at.exception


def test_ca07_periodo_sem_vendas():
    at = _app()
    at.date_input[0].set_value((date(2024, 7, 1), date(2024, 7, 31))).run()
    m = _metricas(at)
    assert (m["Unidades vendidas"], m["Pedidos em aberto"], m["Produtos a repor"]) == ("0", "0", "5")
    assert m["Valor do estoque (custo)"] == "US$ 4.731,00"
    assert any(MSG_SEM_VENDAS in i.value for i in at.info)


def test_ca05_categoria_tools():
    at = _app()
    cat = [w for w in at.multiselect if w.label == "Categoria"][0]
    cat.set_value(["Tools"]).run()
    m = _metricas(at)
    assert (m["Produtos a repor"], m["Valor do estoque (custo)"], m["Unidades vendidas"]) == ("1", "US$ 448,50", "5")


def test_rf20_dados_invalidos_mostram_aviso_sem_numeros(tmp_path, monkeypatch):
    monkeypatch.setenv("GARDEN_DATA_DIR", str(tmp_path))  # pasta vazia: products.csv ausente
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.run()
    assert not at.exception and not at.error
    assert any("products.csv: arquivo não encontrado" in w.value for w in at.warning)
    assert len(at.metric) == 0  # nenhum número parcial
