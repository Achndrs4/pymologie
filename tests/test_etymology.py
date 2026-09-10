from pathlib import Path

import pytest

import pymologie
from pymologie import LANGUAGES, Etymology, LanguagePackNotFoundError, Node, Origin
from pymologie.packs import BUNDLED_LANGUAGES
from pymologie.transliteration import annotate_transliteration

FIXTURE = Path(__file__).parent / "fixtures" / "mini_etymologie.csv"
TRANSLIT_FIXTURE = Path(__file__).parent / "fixtures" / "mini_transliterated.csv"


@pytest.fixture
def etymology() -> Etymology:
    return Etymology(data_path=FIXTURE)


@pytest.fixture
def translit_etymology() -> Etymology:
    return Etymology(language="sa", data_path=TRANSLIT_FIXTURE)


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


def test_unknown_language_raises() -> None:
    with pytest.raises(ValueError):
        Etymology(language="xx")


@pytest.mark.parametrize("language", sorted(BUNDLED_LANGUAGES))
def test_bundled_dataset_loads_and_is_non_empty(language: str) -> None:
    etymology = Etymology(language=language)
    assert len(etymology._data) > 0


def test_default_language_is_english() -> None:
    assert Etymology().language == "en"


def test_non_bundled_language_without_download_raises_language_pack_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PYMOLOGIE_CACHE_DIR", str(tmp_path))
    with pytest.raises(LanguagePackNotFoundError, match="pymologie download de"):
        Etymology(language="de")


def test_native_script_lookup_is_unchanged(translit_etymology: Etymology) -> None:
    node = translit_etymology.tree("गुरु")
    assert isinstance(node, Node)
    assert node.word == "गुरु"

    origins_list = translit_etymology.origins("गुरु")
    assert isinstance(origins_list, list)
    assert all(isinstance(o, Origin) for o in origins_list)


def test_latin_search_single_match_is_list_wrapped(translit_etymology: Etymology) -> None:
    result = translit_etymology.tree("guru")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].word == "गुरु"

    origins_result = translit_etymology.origins("guru")
    assert origins_result == [translit_etymology.origins("गुरु")]


def test_latin_search_is_case_insensitive(translit_etymology: Etymology) -> None:
    result = translit_etymology.tree("GURU")
    assert isinstance(result, list)
    assert result[0].word == "गुरु"


def test_latin_search_ambiguous_match_returns_all(translit_etymology: Etymology) -> None:
    result = translit_etymology.tree("eka")
    assert isinstance(result, list)
    assert {node.word for node in result} == {"एक", "ऎक"}


def test_latin_search_no_match_falls_back_to_usual(translit_etymology: Etymology) -> None:
    node = translit_etymology.tree("nonexistentword")
    assert isinstance(node, Node)
    assert node.children == []

    assert translit_etymology.origins("nonexistentword") == []


def test_transliterate_output_flag() -> None:
    etymology = Etymology(language="sa", data_path=TRANSLIT_FIXTURE, transliterate=True)
    node = etymology.tree("गुरु")
    assert node.word == annotate_transliteration("गुरु") == "गुरु (guru)"
    assert node.children[0].word == annotate_transliteration("गुर्वी")


def test_settings_object_reused_by_top_level_api() -> None:
    etymology = Etymology(language="sa", data_path=TRANSLIT_FIXTURE, transliterate=True)
    node = pymologie.tree("गुरु", settings=etymology)
    assert node.word == annotate_transliteration("गुरु")
