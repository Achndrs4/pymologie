# Pymologie : Etymology Finder 
![alt text](https://github.com/Achndrs4/pymologie/blob/main/src/pymologie/resources/pymologie.gif?raw=true)

## Usage

`pymologie` derives a word's full etymology as a tree, since a word's stem
can itself be a word with its own further-back origins. **English (`en`)**
ships bundled and works immediately after `pip install`. **German (`de`),
Tamil (`ta`), Sanskrit (`sa`), Telugu (`te`), Malayalam (`ml`), and
Kannada (`kn`)** are also supported but download on demand — see
[Downloading language packs](#downloading-language-packs) below.

```python
import pymologie

# A Node tree: the root is the word you looked up, each child is a
# direct origin, and each of those can have its own children going
# further back. `language` defaults to "en".
node = pymologie.tree("house")
print(node)
# house
# ├── hous (Middle English, 1150 CE - 1500 CE)
# ├── hūs (Old English, 450 CE - 1150 CE)
# ├── *hūsą (Proto-Germanic, 500 BCE - 500 CE)
# └── *(s)kews- (Proto-Indo-European, 4500 BCE - 2500 BCE)

pymologie.download_language("ta")           # one-time, per language
print(pymologie.tree("குரு", language="ta"))
# குரு
# └── गुरु (Sanskrit, 1500 BCE - present (liturgical/classical))
#         ├── *gr̥Húṣ (Proto-Indo-Aryan, 2000 BCE - 1500 BCE)
#         ├── *gr̥Húš (Proto-Indo-Iranian, 2200 BCE - 1800 BCE)
#         └── *gʷréh₂us (Proto-Indo-European, 4500 BCE - 2500 BCE)

node.to_dict()                              # recursive dict, e.g. for json.dumps(...)
pymologie.origins("house")                  # flat list of direct Origin(word, language, period)
pymologie.analyze(["house", "cat"])         # Counter of language frequency
pymologie.LANGUAGES                         # {"en": "en.csv", "de": "de.csv", "ta": "ta.csv", ...}
```

### Downloading language packs

Every language except English needs its data pack downloaded once before
use — this is a deliberate, explicit step (never a silent network call from
`tree()`/`origins()`/`analyze()`), so it's clear when a lookup needs one:

```python
pymologie.download_language("de")           # fetches and caches de.csv
pymologie.tree("Haus", language="de")       # now works

pymologie.tree("Haus", language="de")       # BEFORE downloading: raises
# pymologie.LanguagePackNotFoundError: language pack 'de' isn't downloaded.
# Run: pymologie download de  (or pymologie.download_language('de'))
```

Packs are fetched from this project's own GitHub repo (pinned to the tag
matching your installed `pymologie` version, so the data you get always
matches the code you're running) and cached in `~/.cache/pymologie` —
override the location with the `PYMOLOGIE_CACHE_DIR` environment variable.
Pass `force=True` to `download_language` to re-fetch a pack that's already
cached.

From the CLI:

```
pymologie --download de
pymologie Haus --language de
```

#### Migrating from 2.x

Two changes in 3.0 affect existing code:
- **The default language changed from `de` to `en`.** Any call that relied
  on the implicit default (`pymologie.tree(word)` with no `language=`) now
  looks up English, not German — pass `language="de"` explicitly to keep
  the old behavior.
- **Non-English languages now require `download_language(...)` first.**
  This includes `de` — it's no longer bundled in the wheel.

### Reusable settings

Repeating `language=`/`transliterate=` on every call gets old fast — build
an `Etymology` once and reuse it, either directly or by passing it to the
top-level functions as `settings=`:

```python
from pymologie import Etymology

tamil = Etymology(language="ta", transliterate=True)
tamil.tree("குரு")          # no need to repeat language/transliterate

# or keep using the flat pymologie.* functions, reusing the same settings:
pymologie.tree("குரு", settings=tamil)
pymologie.origins("குரு", settings=tamil)
```

For a custom dataset, or more control, use the `Etymology` class directly:

```python
etym = Etymology(language="sa")
etym.tree("गुरु", max_depth=5)

# or point at your own CSV entirely (same Term,Stamm,Sprache,Zeitraum shape)
etym = Etymology(data_path="path/to/your.csv")
```

### Latin transliteration and search

Pass `transliterate=True` to show the Latin romanization of every non-Latin
word **alongside** its original script, rather than replacing it — words
already in Latin script (German, proto-forms, etc.) are left as-is. Tamil,
Telugu, Kannada, Malayalam, and Sanskrit use ISO 15919 diacritics (the same
style already used for reconstructed proto-forms like `*gr̥Húṣ`); words that
trace back to Ancient Greek or Persian/Arabic origins — which show up deep
in these etymology trees even though they aren't bundled top-level
languages — use ALA-LC romanization instead:

```python
print(pymologie.tree("குரு", language="ta", transliterate=True))
# குரு (kuru)
# └── गुरு (guru) (Sanskrit, 1500 BCE - present (liturgical/classical))
#         ├── gr̥Húṣ (Proto-Indo-Aryan, 2000 BCE - 1500 BCE)
#         ├── gr̥Húš (Proto-Indo-Iranian, 2200 BCE - 1800 BCE)
#         └── gʷréh₂us (Proto-Indo-European, 4500 BCE - 2500 BCE)

print(pymologie.tree("قهوه", language="sa", transliterate=True))
# قهوه (qhwh)
# └── قَهْوَة (qahwah) (Arabic, 600 CE - present)
```

(Tamil script doesn't mark voiced/voiceless consonants, so a literal
transliteration of `குரு` is `kuru`, not the phonetic `guru` — that's a
property of the script itself, not a quirk of this library. Likewise,
Greek accents and the iota subscript are dropped rather than represented,
and Persian/Arabic's `و`/`ي` always romanize as consonants (`w`/`y`),
never as long vowels — telling those apart needs dictionary knowledge this
library doesn't have. Persian and Arabic also share a few letters that
ALA-LC romanizes differently between the two languages; this library uses
one Arabic-flavored table for both.

Persian/Arabic is a right-to-left script, so its output above may look odd
in a plain-text file — in a terminal or editor that understands Unicode
bidi, the romanization reliably renders to the right of the original word
regardless.)

Independent of that flag, you can also look words up **by their Latin
spelling** instead of native script — useful when your terminal can't
render Tamil/Telugu/Kannada/Malayalam/Devanagari:

```python
pymologie.tree("guru", language="ta")   # same as looking up குரு
```

A Latin-spelled lookup always returns a **list** — one tree/origin-list per
matching native-script word — even when there's only one match, since the
same Latin spelling can correspond to more than one native word. Looking
up a word directly in its native script, or an unknown word, keeps
returning a single `Node`/flat list exactly as before:

```python
pymologie.tree("குரு", language="ta")   # -> a single Node, as always
pymologie.tree("guru", language="ta")   # -> [Node, ...], even if len == 1
```

`pymologie.transliterate(text)` is also available standalone, for
romanizing arbitrary text outside of a lookup.

### CLI

```
pymologie house
pymologie house --json
pymologie house --max-depth 3

pymologie --download ta                         # once, before first use
pymologie --language ta குரு
pymologie --language sa गुरु
pymologie --language te తెలుగు
pymologie --language ml മലയാളം
pymologie --language kn ಗುರು
pymologie --language ta guru --transliterate    # Latin input, romanized output
```

### Where the data comes from

The per-language CSVs are filtered from
[droher/etymology-db](https://github.com/droher/etymology-db), a
Wiktionary-derived graph of etymological relationships covering ~2900
languages. `scripts/build_dataset.py` walks that dump outward from each
language's terms and writes just the reachable rows into
`src/pymologie/resources/`. Only `en.csv` actually ships inside the pip
package — the rest stay committed in this repo and are fetched by
`download_language()` on demand (see
[Downloading language packs](#downloading-language-packs)).

To regenerate the data yourself (e.g. after a newer etymology-db release,
or to add a language), download that project's CSV dump and run:

```
python scripts/build_dataset.py path/to/etymology-db.csv --languages English --code en
```

## Liscence 
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.