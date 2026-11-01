"""Carga e validação dos CSVs da Garden Shop (SPEC §3).

Os arquivos são apenas lidos (RN-10). Qualquer problema gera DataError com
mensagem no formato "<arquivo>: <problema>" (RF-20).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

VALID_STATUS = {"shipped", "pending", "processing", "cancelled"}

# Tabelas e campos necessários (SPEC §2.1). customers.csv não é carregado.
SCHEMA: dict[str, dict] = {
    "products": {
        "file": "products.csv",
        "pk": "product_id",
        "columns": ["product_id", "product_name", "category_id", "supplier_id",
                    "cost", "quantity_on_hand", "reorder_level", "discontinued"],
        "non_negative": ["cost", "quantity_on_hand", "reorder_level"],
    },
    "categories": {
        "file": "categories.csv",
        "pk": "category_id",
        "columns": ["category_id", "category_name"],
        "non_negative": [],
    },
    "suppliers": {
        "file": "suppliers.csv",
        "pk": "supplier_id",
        "columns": ["supplier_id", "supplier_name", "contact_email"],
        "non_negative": [],
    },
    "orders": {
        "file": "orders.csv",
        "pk": "order_id",
        "columns": ["order_id", "order_date", "status"],
        "non_negative": [],
    },
    "order_items": {
        "file": "order_items.csv",
        "pk": "order_item_id",
        "columns": ["order_item_id", "order_id", "product_id", "quantity"],
        "non_negative": ["quantity"],
    },
}

# (tabela filha, coluna FK, tabela pai)
FOREIGN_KEYS = [
    ("products", "category_id", "categories"),
    ("products", "supplier_id", "suppliers"),
    ("order_items", "order_id", "orders"),
    ("order_items", "product_id", "products"),
]

PARENT_LABEL = {"products": "produto", "categories": "categoria", "suppliers": "fornecedor", "orders": "pedido"}

OPTIONAL = {("suppliers", "contact_email")}


class DataError(Exception):
    """Erro de dados com mensagem pronta para o usuário."""


def _read(data_dir: Path, name: str) -> pd.DataFrame:
    spec = SCHEMA[name]
    path = Path(data_dir) / spec["file"]
    if not path.exists():
        raise DataError(f"{spec['file']}: arquivo não encontrado em {data_dir}")  # V1
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [c for c in spec["columns"] if c not in df.columns]
    if missing:
        raise DataError(f"{spec['file']}: colunas ausentes: {', '.join(missing)}")  # V2
    df = df[spec["columns"]].copy()
    for col in df.columns:
        df[col] = df[col].str.strip().replace("", pd.NA)
        if (name, col) not in OPTIONAL and df[col].isna().any():
            raise DataError(f"{spec['file']}: valor ausente em {col}")
    return df


def _to_number(df: pd.DataFrame, name: str, cols: list[str], integer: bool) -> None:
    spec = SCHEMA[name]
    for col in cols:
        conv = pd.to_numeric(df[col], errors="coerce")
        bad = conv.isna() | (conv < 0) | (integer and (conv % 1 != 0))
        if bad.any():
            first = df.loc[bad, spec["pk"]].iloc[0]
            raise DataError(f"{spec['file']}: valor inválido em {col} (linha do {spec['pk']} {first})")  # V4
        df[col] = conv.astype("int64") if integer else conv.astype(float)


def load_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    """Lê e valida products, categories, suppliers, orders e order_items."""
    data_dir = Path(data_dir)
    data = {name: _read(data_dir, name) for name in SCHEMA}

    # Chaves (inteiras) e campos numéricos
    id_cols = {
        "products": ["product_id", "category_id", "supplier_id"],
        "categories": ["category_id"],
        "suppliers": ["supplier_id"],
        "orders": ["order_id"],
        "order_items": ["order_item_id", "order_id", "product_id"],
    }
    for name, cols in id_cols.items():
        _to_number(data[name], name, cols, integer=True)
    _to_number(data["products"], "products", ["quantity_on_hand", "reorder_level"], integer=True)
    _to_number(data["products"], "products", ["cost"], integer=False)
    _to_number(data["order_items"], "order_items", ["quantity"], integer=True)
    if (data["order_items"]["quantity"] <= 0).any():
        raise DataError("order_items.csv: quantity deve ser > 0")  # V5

    # V3: chave primária única
    for name, spec in SCHEMA.items():
        dup = data[name][spec["pk"]].duplicated()
        if dup.any():
            raise DataError(f"{spec['file']}: {spec['pk']} duplicado: {data[name].loc[dup, spec['pk']].iloc[0]}")

    # V6: discontinued booleano
    disc = data["products"]["discontinued"].str.lower()
    bad = ~disc.isin(["true", "false"])
    if bad.any():
        raise DataError(f"products.csv: discontinued inválido: '{data['products'].loc[bad, 'discontinued'].iloc[0]}'")
    data["products"]["discontinued"] = disc.eq("true")

    # V7: status conhecido
    status = data["orders"]["status"].str.lower()
    bad = ~status.isin(VALID_STATUS)
    if bad.any():
        raise DataError(f"orders.csv: status desconhecido: '{status[bad].iloc[0]}'")
    data["orders"]["status"] = status

    # V8: data ISO (AAAA-MM-DD), mesmo que o dicionário diga DD/MM/AAAA
    dates = pd.to_datetime(data["orders"]["order_date"], format="%Y-%m-%d", errors="coerce")
    if dates.isna().any():
        raise DataError(f"orders.csv: order_date inválida: '{data['orders'].loc[dates.isna(), 'order_date'].iloc[0]}'")
    data["orders"]["order_date"] = dates

    # V9: integridade referencial
    for child, col, parent in FOREIGN_KEYS:
        orphan = ~data[child][col].isin(data[parent][SCHEMA[parent]["pk"]])
        if orphan.any():
            label = PARENT_LABEL[parent]
            raise DataError(
                f"{SCHEMA[child]['file']}: {col} sem {label} correspondente: {data[child].loc[orphan, col].iloc[0]}"
            )

    return data
