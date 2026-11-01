"""T-01 a T-03: carga e validação dos CSVs (SPEC §3)."""
import hashlib
import shutil

import pandas as pd
import pytest

from garden_dashboard.loader import DataError, load_data

ARQUIVOS = ["products.csv", "categories.csv", "suppliers.csv", "orders.csv", "order_items.csv"]


def _copia(src, tmp_path):
    for nome in ARQUIVOS:
        shutil.copy(src / nome, tmp_path / nome)
    return tmp_path


def _edita(path, linha_antiga, linha_nova):
    texto = path.read_text()
    assert linha_antiga in texto
    path.write_text(texto.replace(linha_antiga, linha_nova))


# T-01 ---------------------------------------------------------------------
def test_carrega_recorte_com_tipos_corretos(recorte_dir):
    d = load_data(recorte_dir)
    assert set(d) == {"products", "categories", "suppliers", "orders", "order_items"}
    p = d["products"]
    assert len(p) == 5
    assert p["discontinued"].dtype == bool
    assert bool(p.loc[p.product_id == 24, "discontinued"].item()) is True
    assert pd.api.types.is_datetime64_any_dtype(d["orders"]["order_date"])
    assert set(d["orders"]["status"]) == {"shipped", "pending", "cancelled"}


def test_nao_carrega_customers(raw_dir):
    assert "customers" not in load_data(raw_dir)


def test_email_ausente_permanece_nulo(recorte_dir):
    s = load_data(recorte_dir)["suppliers"]
    assert s.loc[s.supplier_id == 5, "contact_email"].isna().item()


def test_status_e_discontinued_normalizados(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    _edita(d / "orders.csv", "7,2,2024-05-01,,pending,", "7,2,2024-05-01,,  PENDING ,")
    _edita(d / "products.csv", "Bird Feeder,8,5,17.00,8.00,4,6,true", "Bird Feeder,8,5,17.00,8.00,4,6,TRUE")
    dados = load_data(d)
    assert "pending" in set(dados["orders"]["status"])
    assert dados["products"]["discontinued"].sum() == 1


# T-02 ---------------------------------------------------------------------
def test_arquivo_ausente(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    (d / "products.csv").unlink()
    with pytest.raises(DataError, match="products.csv: arquivo não encontrado"):
        load_data(d)


def test_coluna_ausente(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    df = pd.read_csv(d / "products.csv").drop(columns=["reorder_level"])
    df.to_csv(d / "products.csv", index=False)
    with pytest.raises(DataError, match="products.csv: colunas ausentes: reorder_level"):
        load_data(d)


def test_chave_duplicada(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    _edita(d / "orders.csv", "10,15,", "7,15,")
    with pytest.raises(DataError, match="orders.csv: order_id duplicado: 7"):
        load_data(d)


def test_status_desconhecido(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    _edita(d / "orders.csv", "17,9,2024-04-03,,cancelled,", "17,9,2024-04-03,,returned,")
    with pytest.raises(DataError, match="orders.csv: status desconhecido: 'returned'"):
        load_data(d)


def test_data_fora_do_formato(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    _edita(d / "orders.csv", "1,1,2024-03-02,", "1,1,02/03/2024,")
    with pytest.raises(DataError, match="orders.csv: order_date inválida: '02/03/2024'"):
        load_data(d)


def test_discontinued_invalido(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    _edita(d / "products.csv", "8,5,17.00,8.00,4,6,true", "8,5,17.00,8.00,4,6,sim")
    with pytest.raises(DataError, match="products.csv: discontinued inválido: 'sim'"):
        load_data(d)


def test_fk_invalida(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    _edita(d / "order_items.csv", "34,18,1,2,32.00", "34,18,99,2,32.00")
    with pytest.raises(DataError, match="order_items.csv: product_id sem produto correspondente: 99"):
        load_data(d)


def test_numero_negativo(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    _edita(d / "products.csv", "Hand Cultivator,3,5,8.00,3.50,3,10", "Hand Cultivator,3,5,8.00,3.50,-3,10")
    with pytest.raises(DataError, match="products.csv: valor inválido em quantity_on_hand"):
        load_data(d)


def test_numero_nao_numerico(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    _edita(d / "products.csv", "Fiddle-Leaf Fig,1,1,32.00,18.00", "Fiddle-Leaf Fig,1,1,32.00,abc")
    with pytest.raises(DataError, match="products.csv: valor inválido em cost"):
        load_data(d)


def test_quantidade_zero(recorte_dir, tmp_path):
    d = _copia(recorte_dir, tmp_path)
    _edita(d / "order_items.csv", "34,18,1,2,32.00", "34,18,1,0,32.00")
    with pytest.raises(DataError, match="order_items.csv: quantity deve ser > 0"):
        load_data(d)


# T-03 ---------------------------------------------------------------------
def test_arquivos_originais_nao_sao_alterados(raw_dir):
    def hashes():
        return {f.name: hashlib.md5(f.read_bytes()).hexdigest() for f in sorted(raw_dir.iterdir())}

    antes = hashes()
    load_data(raw_dir)
    assert hashes() == antes
