from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RECORTE = ROOT / "tests" / "fixtures" / "recorte"
RAW = ROOT / "data" / "raw"


@pytest.fixture
def recorte_dir() -> Path:
    return RECORTE


@pytest.fixture
def raw_dir() -> Path:
    return RAW
