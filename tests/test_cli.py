from pathlib import Path
from unittest.mock import patch

import pytest

from pymologie.cli import main


@pytest.fixture
def isolated_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("PYMOLOGIE_CACHE_DIR", str(tmp_path))
    return tmp_path


def test_download_flag_caches_pack_and_exits_zero(isolated_cache: Path, capsys: pytest.CaptureFixture) -> None:
    fake_csv = b"Term,Stamm,Sprache,Zeitraum\nHaus,hus,Mittelhochdeutsch,1050-1500\n"
    with patch("pymologie.packs.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = fake_csv
        exit_code = main(["--download", "de"])

    assert exit_code == 0
    assert (isolated_cache / "de.csv").exists()
    assert "downloaded 'de'" in capsys.readouterr().out


def test_lookup_against_undownloaded_language_prints_friendly_error(
    isolated_cache: Path, capsys: pytest.CaptureFixture
) -> None:
    exit_code = main(["Haus", "--language", "de"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "pymologie download de" in err


def test_word_required_unless_downloading() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_default_language_lookup_works_without_download() -> None:
    exit_code = main(["house"])
    assert exit_code == 0
