from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def load_fixture():
    def _load(relative_path: str) -> str:
        return (FIXTURES_DIR / relative_path).read_text(encoding="utf-8")

    return _load
