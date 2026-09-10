from pathlib import Path
from unittest.mock import patch

import pytest

from pymologie import packs


@pytest.fixture
def isolated_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("PYMOLOGIE_CACHE_DIR", str(tmp_path))
    return tmp_path


def test_cache_dir_honors_env_override(isolated_cache: Path) -> None:
    assert packs.cache_dir() == isolated_cache


def test_cache_dir_defaults_to_user_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYMOLOGIE_CACHE_DIR", raising=False)
    assert packs.cache_dir() == Path.home() / ".cache" / "pymologie"


def test_download_language_writes_file_and_uses_current_version(isolated_cache: Path) -> None:
    fake_csv = b"Term,Stamm,Sprache,Zeitraum\nHaus,hus,Mittelhochdeutsch,1050-1500\n"
    with patch("pymologie.packs.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = fake_csv
        result = packs.download_language("de", "de.csv")

    requested_url = mock_urlopen.call_args[0][0]
    assert "de.csv" in requested_url
    import pymologie

    assert f"v{pymologie.__version__}" in requested_url
    assert result == isolated_cache / "de.csv"
    assert result.read_bytes() == fake_csv


def test_download_language_skips_network_call_when_already_cached(isolated_cache: Path) -> None:
    cached = isolated_cache / "de.csv"
    cached.write_bytes(b"already here")

    with patch("pymologie.packs.urllib.request.urlopen") as mock_urlopen:
        result = packs.download_language("de", "de.csv")

    mock_urlopen.assert_not_called()
    assert result.read_bytes() == b"already here"


def test_download_language_force_redownloads(isolated_cache: Path) -> None:
    cached = isolated_cache / "de.csv"
    cached.write_bytes(b"stale")
    fresh_csv = b"fresh"

    with patch("pymologie.packs.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = fresh_csv
        result = packs.download_language("de", "de.csv", force=True)

    mock_urlopen.assert_called_once()
    assert result.read_bytes() == fresh_csv


def test_resolve_resource_raises_for_undownloaded_language(isolated_cache: Path) -> None:
    with pytest.raises(packs.LanguagePackNotFoundError, match="pymologie download de"):
        with packs.resolve_resource("de", "de.csv"):
            pass


def test_resolve_resource_reads_cached_file(isolated_cache: Path) -> None:
    (isolated_cache / "de.csv").write_text("Term,Stamm,Sprache,Zeitraum\n", encoding="utf-8")
    with packs.resolve_resource("de", "de.csv") as file:
        assert file.read() == "Term,Stamm,Sprache,Zeitraum\n"


def test_resolve_resource_reads_bundled_language() -> None:
    with packs.resolve_resource("en", "en.csv") as file:
        header = file.readline()
    assert header.strip() == "Term,Stamm,Sprache,Zeitraum"
