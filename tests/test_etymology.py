from pathlib import Path

import pytest

from pymologie import Etymology, Origin

FIXTURE = Path(__file__).parent / "fixtures" / "mini_etymologie.csv"


@pytest.fixture
def etymology() -> Etymology:
    return Etymology(data_path=FIXTURE)


def test_origins_known_word(etymology: Etymology) -> None:
    assert etymology.origins("Haus") == [
        Origin("hus", "Mittelhochdeutsch", "1050-1500"),
        Origin("hus_alt", "Althochdeutsch", "750-1050"),
    ]


def test_origins_unknown_word(etymology: Etymology) -> None:
    assert etymology.origins("Nichtvorhanden") == []


def test_analyze_counts_languages(etymology: Etymology) -> None:
    counts = etymology.analyze(["Haus", "Katze", "Nichtvorhanden"])
    assert counts == {
        "Mittelhochdeutsch": 2,
        "Althochdeutsch": 1,
    }
