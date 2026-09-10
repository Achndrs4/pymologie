"""Bundled-vs-downloadable language data and the download mechanism.

English ships inside the wheel (``BUNDLED_LANGUAGES``) so a fresh install
works immediately for the default language. Every other bundled language
code is fetched on demand from this project's own GitHub repo, pinned to
the tag matching the installed package version, and cached locally —
nothing here ever downloads silently; callers must ask for it via
:func:`download_language`.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from typing import IO, Iterator

#: Language codes whose CSV ships inside the pip package itself.
BUNDLED_LANGUAGES = {"en"}

_RAW_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/Achndrs4/pymologie/"
    "v{version}/src/pymologie/resources/{filename}"
)


class LanguagePackNotFoundError(RuntimeError):
    """Raised when a non-bundled language's data hasn't been downloaded yet."""


def cache_dir() -> Path:
    """Where downloaded language packs are cached.

    Honors ``$PYMOLOGIE_CACHE_DIR`` (used by tests and anyone who wants a
    non-default location); otherwise ``~/.cache/pymologie``.
    """
    override = os.environ.get("PYMOLOGIE_CACHE_DIR")
    if override:
        return Path(override)
    return Path.home() / ".cache" / "pymologie"


def download_language(language: str, filename: str, *, force: bool = False) -> Path:
    """Download ``filename`` for ``language`` into the cache, returning its path.

    Skips the network call if already cached unless ``force=True``.
    """
    from . import __version__

    target = cache_dir() / filename
    if target.exists() and not force:
        return target

    url = _RAW_URL_TEMPLATE.format(version=__version__, filename=filename)
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        raise LanguagePackNotFoundError(
            f"could not download language pack {language!r} from {url} ({exc}); "
            f"it may not exist for pymologie version {__version__}"
        ) from exc

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, target)
    return target


@contextmanager
def resolve_resource(language: str, filename: str) -> Iterator[IO[str]]:
    """Open ``filename`` for ``language``, bundled or previously downloaded.

    Raises :class:`LanguagePackNotFoundError` naming the exact command to
    run when a non-bundled language hasn't been downloaded yet.
    """
    if language in BUNDLED_LANGUAGES:
        with resources.files("pymologie.resources").joinpath(filename).open(
            "r", encoding="utf-8", newline=""
        ) as file:
            yield file
        return

    cached = cache_dir() / filename
    if not cached.exists():
        raise LanguagePackNotFoundError(
            f"language pack {language!r} isn't downloaded. Run: "
            f"pymologie download {language}  "
            f"(or pymologie.download_language({language!r}))"
        )
    with cached.open("r", encoding="utf-8", newline="") as file:
        yield file
