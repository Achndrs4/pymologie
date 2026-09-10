# Pymologie: Wortherkünfte in der deutschen Sprache
![alt text](https://github.com/Achndrs4/pymologie/blob/main/src/pymologie/resources/pymologie.gif?raw=true)
## Hinweise 
Implementierung ist nur mit dieser [Quelle](https://github.com/droher/etymology-db) und ihrer Lizenz möglich. In diesem Geist ist diese Repo auch mit dem MIT Lizenz veröffentlicht. Hierunter finden Sie eine (inoffiziel) Übersetzung dieses Lizenzes.
 
## Einstellungen 
1. Bitte nur mit Python >= 3.9 benutzen
2. Mit [pip](https://docs.python.org/3/installing/index.html) installieren im Projectort mit folgendem Befehl:
   1. pip3 install pymologie

## Usage

`pymologie` derives a word's full etymology as a tree, since a word's stem
can itself be a word with its own further-back origins. **German (`de`),
Tamil (`ta`), Sanskrit (`sa`), Telugu (`te`), Malayalam (`ml`), and
Kannada (`kn`)** are bundled.

```python
import pymologie

# A Node tree: the root is the word you looked up, each child is a
# direct origin, and each of those can have its own children going
# further back. `language` defaults to "de".
node = pymologie.tree("Haus")
print(node)
# Haus
# ├── hūs (Middle High German, 1050 CE - 1500 CE)
# ├── hūs (Old High German, 750 CE - 1050 CE)
# ├── *hūs (Proto-West Germanic, before 500 CE (unconfirmed))
# └── *hūsą (Proto-Germanic, 500 BCE - 500 CE)

print(pymologie.tree("குரு", language="ta"))
# குரு
# └── गुरु (Sanskrit, 1500 BCE - present (liturgical/classical))
#         ├── *gr̥Húṣ (Proto-Indo-Aryan, 2000 BCE - 1500 BCE)
#         ├── *gr̥Húš (Proto-Indo-Iranian, 2200 BCE - 1800 BCE)
#         └── *gʷréh₂us (Proto-Indo-European, 4500 BCE - 2500 BCE)

node.to_dict()                              # recursive dict, e.g. for json.dumps(...)
pymologie.origins("Haus")                   # flat list of direct Origin(word, language, period)
pymologie.analyze(["Haus", "Katze"])        # Counter of language frequency
pymologie.LANGUAGES                         # {"de": "de.csv", "ta": "ta.csv", "sa": "sa.csv", ...}
```

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
pymologie Haus
pymologie Haus --json
pymologie Haus --max-depth 3
pymologie --language ta குரு
pymologie --language sa गुरु
pymologie --language te తెలుగు
pymologie --language ml മലയാളം
pymologie --language kn ಗುರು
pymologie --language ta guru --transliterate    # Latin input, romanized output
```

### Where the data comes from

The bundled per-language CSVs are filtered from
[droher/etymology-db](https://github.com/droher/etymology-db), a
Wiktionary-derived graph of etymological relationships covering ~2900
languages. `scripts/build_dataset.py` walks that dump outward from each
bundled language's terms and writes just the reachable rows into
`src/pymologie/resources/`, which is what the pip package actually ships.

To regenerate the bundled data yourself (e.g. after a newer etymology-db
release), download that project's CSV dump and run:

```
python scripts/build_dataset.py path/to/etymology-db.csv
```

## MIT Lizenz
Jedem, der eine Kopie dieser Software und der zugehörigen Dokumentationsdateien (die „Software“) erhält, wird hiermit kostenlos die Erlaubnis erteilt, ohne Einschränkung mit der Software zu handeln, einschließlich und ohne Einschränkung der Rechte zur Nutzung, zum Kopieren, Ändern, Zusammenführen, Veröffentlichen, Verteilen, Unterlizenzieren und/oder Verkaufen von Kopien der Software, und Personen, denen die Software zur Verfügung gestellt wird, dies unter den folgenden Bedingungen zu gestatten:

Der obige Urheberrechtshinweis und dieser Genehmigungshinweis müssen in allen Kopien oder wesentlichen Teilen der Software enthalten sein.

Die Software wird ohne Mängelgewähr und ohne jegliche Ausdrückliche oder Stillschweigende gewährleistung, einschließlich, aber nicht beschränkt auf die Gewährleistung der Marktgängigkeit, der Eignung für einen bestimmten Zweck und der Nichtverletzung von rechten Dritter, zur verfügung gestellt. Die Autoren oder Urheberrechtsinhaber sind in keinem Fall haftbar für Ansprüche, Schäden oder andere Verpflichtungen, ob in einer Vertrags- oder Haftungsklage, einer unerlaubten Handlung oder anderweitig, die sich aus oder in Verbindung mit der Software oder der Nutzung oder anderen geschäften mit der Software ergeben. 
