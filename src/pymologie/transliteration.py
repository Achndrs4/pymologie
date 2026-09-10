"""Romanize Tamil, Telugu, Kannada, Malayalam, Sanskrit (Devanagari), Ancient
Greek, and Persian/Arabic text into Latin script.

The five Brahmic scripts (ta/te/kn/ml/sa) use ISO 15919 / IAST-style
diacritics: a consonant carries an inherent "a" unless it's followed by a
vowel sign (matra), which replaces that vowel, or a virama, which
suppresses it entirely. Their Unicode blocks don't overlap, so this is
implemented as one linear scan driven by merged per-script lookup tables,
rather than five separate algorithms.

Greek and Persian/Arabic use the ALA-LC (Library of Congress) romanization
standard instead, since they aren't Brahmic abugidas: Greek is a true
alphabet and Persian/Arabic is an abjad (consonants carry no inherent
vowel at all). Both get their own contiguous-run branch in the same linear
scan, detected by Unicode block rather than an explicit language tag.

Known simplifications, documented rather than silently wrong:
- Tamil script doesn't distinguish voiced/voiceless/aspirated consonants
  (e.g. க covers both "k" and "g" sounds depending on context), so a
  strict letter-for-letter transliteration of Tamil renders words like
  "குரு" as "kuru", not the phonetic "guru" — that's a property of the
  Tamil script, not a bug in this table.
- Greek accents (acute/grave/circumflex) and the iota subscript are
  dropped rather than represented, matching ALA-LC's ancient/medieval
  convention.
- Persian and Arabic share Unicode code points for several letters that
  ALA-LC romanizes differently between the two languages (e.g. ث, ذ, ض,
  و); this module uses one merged, Arabic-flavored table for both rather
  than requiring a language hint. و and ي always romanize as consonants
  ("w"/"y"), never as long vowels ("ū"/"ī"), since telling those apart
  needs dictionary knowledge this module doesn't have.
"""

from __future__ import annotations

import unicodedata

# --- Devanagari (Sanskrit) ------------------------------------------------

_DEVANAGARI_VOWELS = {
    "अ": "a", "आ": "ā", "इ": "i", "ई": "ī", "उ": "u", "ऊ": "ū",
    "ऋ": "r̥", "ॠ": "r̥̄", "ऌ": "l̥", "ॡ": "l̥̄",
    "ऎ": "e", "ए": "e", "ऐ": "ai", "ऒ": "o", "ओ": "o", "औ": "au",
    "ऍ": "ê", "ऑ": "ô",
}
_DEVANAGARI_MATRAS = {
    "ा": "ā", "ि": "i", "ी": "ī", "ु": "u", "ू": "ū",
    "ृ": "r̥", "ॄ": "r̥̄", "ॢ": "l̥", "ॣ": "l̥̄",
    "ॆ": "e", "े": "e", "ै": "ai", "ॊ": "o", "ो": "o", "ौ": "au",
    "ॅ": "ê", "ॉ": "ô",
}
_DEVANAGARI_CONSONANTS = {
    "क": "ka", "ख": "kha", "ग": "ga", "घ": "gha", "ङ": "ṅa",
    "च": "ca", "छ": "cha", "ज": "ja", "झ": "jha", "ञ": "ña",
    "ट": "ṭa", "ठ": "ṭha", "ड": "ḍa", "ढ": "ḍha", "ण": "ṇa",
    "त": "ta", "थ": "tha", "द": "da", "ध": "dha", "न": "na",
    "प": "pa", "फ": "pha", "ब": "ba", "भ": "bha", "म": "ma",
    "य": "ya", "र": "ra", "ल": "la", "व": "va", "ळ": "ḷa",
    "श": "śa", "ष": "ṣa", "स": "sa", "ह": "ha",
    "क़": "qa", "ख़": "k͟ha", "ग़": "ġa", "ज़": "za",
    "ड़": "ṛa", "ढ़": "ṛha", "फ़": "fa", "य़": "ẏa",
}
_DEVANAGARI_MARKS = {"ं": "ṃ", "ः": "ḥ", "ँ": "m̐", "ऽ": "'", "ॐ": "oṃ"}
_DEVANAGARI_VIRAMA = "्"
_DEVANAGARI_DIGITS = {c: str(i) for i, c in enumerate("०१२३४५६७८९")}

# --- Tamil ------------------------------------------------------------

_TAMIL_VOWELS = {
    "அ": "a", "ஆ": "ā", "இ": "i", "ஈ": "ī", "உ": "u", "ஊ": "ū",
    "எ": "e", "ஏ": "ē", "ஐ": "ai", "ஒ": "o", "ஓ": "ō", "ஔ": "au",
}
_TAMIL_MATRAS = {
    "ா": "ā", "ி": "i", "ீ": "ī", "ு": "u", "ூ": "ū",
    "ெ": "e", "ே": "ē", "ை": "ai", "ொ": "o", "ோ": "ō", "ௌ": "au",
}
_TAMIL_CONSONANTS = {
    "க": "ka", "ங": "ṅa", "ச": "ca", "ஜ": "ja", "ஞ": "ña",
    "ட": "ṭa", "ண": "ṇa", "த": "ta", "ந": "na", "ன": "ṉa",
    "ப": "pa", "ம": "ma", "ய": "ya", "ர": "ra", "ற": "ṟa",
    "ல": "la", "ள": "ḷa", "ழ": "ḻa", "வ": "va",
    "ஶ": "śa", "ஷ": "ṣa", "ஸ": "sa", "ஹ": "ha",
}
_TAMIL_MARKS = {"ஃ": "ḥ"}
_TAMIL_VIRAMA = "்"
_TAMIL_DIGITS = {c: str(i) for i, c in enumerate("௦௧௨௩௪௫௬௭௮௯")}

# --- Telugu -------------------------------------------------------------

_TELUGU_VOWELS = {
    "అ": "a", "ఆ": "ā", "ఇ": "i", "ఈ": "ī", "ఉ": "u", "ఊ": "ū",
    "ఋ": "r̥", "ౠ": "r̥̄", "ఌ": "l̥", "ౡ": "l̥̄",
    "ఎ": "e", "ఏ": "ē", "ఐ": "ai", "ఒ": "o", "ఓ": "ō", "ఔ": "au",
}
_TELUGU_MATRAS = {
    "ా": "ā", "ి": "i", "ీ": "ī", "ు": "u", "ూ": "ū",
    "ృ": "r̥", "ౄ": "r̥̄",
    "ె": "e", "ే": "ē", "ై": "ai", "ొ": "o", "ో": "ō", "ౌ": "au",
}
_TELUGU_CONSONANTS = {
    "క": "ka", "ఖ": "kha", "గ": "ga", "ఘ": "gha", "ఙ": "ṅa",
    "చ": "ca", "ఛ": "cha", "జ": "ja", "ఝ": "jha", "ఞ": "ña",
    "ట": "ṭa", "ఠ": "ṭha", "డ": "ḍa", "ఢ": "ḍha", "ణ": "ṇa",
    "త": "ta", "థ": "tha", "ద": "da", "ధ": "dha", "న": "na",
    "ప": "pa", "ఫ": "pha", "బ": "ba", "భ": "bha", "మ": "ma",
    "య": "ya", "ర": "ra", "ఱ": "ṟa", "ల": "la", "ళ": "ḷa",
    "వ": "va", "శ": "śa", "ష": "ṣa", "స": "sa", "హ": "ha",
}
_TELUGU_MARKS = {"ం": "ṃ", "ః": "ḥ", "ఁ": "m̐"}
_TELUGU_VIRAMA = "్"
_TELUGU_DIGITS = {c: str(i) for i, c in enumerate("౦౧౨౩౪౫౬౭౮౯")}

# --- Kannada ------------------------------------------------------------

_KANNADA_VOWELS = {
    "ಅ": "a", "ಆ": "ā", "ಇ": "i", "ಈ": "ī", "ಉ": "u", "ಊ": "ū",
    "ಋ": "r̥", "ೠ": "r̥̄", "ಌ": "l̥", "ೡ": "l̥̄",
    "ಎ": "e", "ಏ": "ē", "ಐ": "ai", "ಒ": "o", "ಓ": "ō", "ಔ": "au",
}
_KANNADA_MATRAS = {
    "ಾ": "ā", "ಿ": "i", "ೀ": "ī", "ು": "u", "ೂ": "ū",
    "ೃ": "r̥", "ೄ": "r̥̄",
    "ೆ": "e", "ೇ": "ē", "ೈ": "ai", "ೊ": "o", "ೋ": "ō", "ೌ": "au",
}
_KANNADA_CONSONANTS = {
    "ಕ": "ka", "ಖ": "kha", "ಗ": "ga", "ಘ": "gha", "ಙ": "ṅa",
    "ಚ": "ca", "ಛ": "cha", "ಜ": "ja", "ಝ": "jha", "ಞ": "ña",
    "ಟ": "ṭa", "ಠ": "ṭha", "ಡ": "ḍa", "ಢ": "ḍha", "ಣ": "ṇa",
    "ತ": "ta", "ಥ": "tha", "ದ": "da", "ಧ": "dha", "ನ": "na",
    "ಪ": "pa", "ಫ": "pha", "ಬ": "ba", "ಭ": "bha", "ಮ": "ma",
    "ಯ": "ya", "ರ": "ra", "ಱ": "ṟa", "ಲ": "la", "ಳ": "ḷa",
    "ವ": "va", "ಶ": "śa", "ಷ": "ṣa", "ಸ": "sa", "ಹ": "ha",
}
_KANNADA_MARKS = {"ಂ": "ṃ", "ಃ": "ḥ"}
_KANNADA_VIRAMA = "್"
_KANNADA_DIGITS = {c: str(i) for i, c in enumerate("೦೧೨೩೪೫೬೭೮೯")}

# --- Malayalam ----------------------------------------------------------

_MALAYALAM_VOWELS = {
    "അ": "a", "ആ": "ā", "ഇ": "i", "ഈ": "ī", "ഉ": "u", "ഊ": "ū",
    "ഋ": "r̥", "ൠ": "r̥̄", "ഌ": "l̥", "ൡ": "l̥̄",
    "എ": "e", "ഏ": "ē", "ഐ": "ai", "ഒ": "o", "ഓ": "ō", "ഔ": "au",
}
_MALAYALAM_MATRAS = {
    "ാ": "ā", "ി": "i", "ീ": "ī", "ു": "u", "ൂ": "ū",
    "ൃ": "r̥", "ൄ": "r̥̄",
    "െ": "e", "േ": "ē", "ൈ": "ai", "ൊ": "o", "ോ": "ō", "ൌ": "au", "ൗ": "au",
}
_MALAYALAM_CONSONANTS = {
    "ക": "ka", "ഖ": "kha", "ഗ": "ga", "ഘ": "gha", "ങ": "ṅa",
    "ച": "ca", "ഛ": "cha", "ജ": "ja", "ഝ": "jha", "ഞ": "ña",
    "ട": "ṭa", "ഠ": "ṭha", "ഡ": "ḍa", "ഢ": "ḍha", "ണ": "ṇa",
    "ത": "ta", "ഥ": "tha", "ദ": "da", "ധ": "dha", "ന": "na",
    "പ": "pa", "ഫ": "pha", "ബ": "ba", "ഭ": "bha", "മ": "ma",
    "യ": "ya", "ര": "ra", "റ": "ṟa", "ല": "la", "ള": "ḷa", "ഴ": "ḻa",
    "വ": "va", "ശ": "śa", "ഷ": "ṣa", "സ": "sa", "ഹ": "ha", "ഩ": "ṉa",
}
_MALAYALAM_CHILLU = {
    "ൻ": "n", "ൺ": "ṇ", "ർ": "r", "ൽ": "l", "ൾ": "ḷ", "ൿ": "k",
}
_MALAYALAM_MARKS = {"ം": "ṃ", "ഃ": "ḥ"}
_MALAYALAM_VIRAMA = "്"
_MALAYALAM_DIGITS = {c: str(i) for i, c in enumerate("൦൧൨൩൪൫൬൭൮൯")}

# --- Ancient/Koine Greek (ALA-LC) ---------------------------------------
#
# Greek is a true alphabet, not an abugida, so it needs a different
# algorithm than the Brahmic scripts above: single-letter mapping plus
# gamma-nasal assimilation, breathing marks, and diphthong lookahead. It's
# handled as its own contiguous-run branch in transliterate_text().

_GREEK_BASE = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z",
    "η": "ē", "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m",
    "ν": "n", "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s",
    "ς": "s", "τ": "t", "υ": "y", "φ": "ph", "χ": "ch", "ψ": "ps",
    "ω": "ō",
}
_GREEK_NASAL_TRIGGERS = {"γ", "κ", "ξ", "χ"}
_GREEK_DIPHTHONGS = {
    ("α", "ι"): "ai", ("α", "υ"): "au", ("ε", "ι"): "ei", ("ε", "υ"): "eu",
    ("ο", "ι"): "oi", ("ο", "υ"): "ou", ("υ", "ι"): "ui", ("η", "υ"): "ēu",
}
_GREEK_ROUGH_BREATHING = "̔"  # dasia
_GREEK_DIAERESIS = "̈"  # dialytika — breaks a diphthong pairing
# Smooth breathing (psili, ̓), accents (acute/grave/circumflex), and
# the iota subscript (ͅ) are recognized implicitly: they're never
# consulted below, so they're dropped from the output automatically, same
# as any other unrecognized combining mark left over after NFD (e.g. the
# vowel-length breve seen in the bundled data's "σκορπῐ́ος").


def _in_greek_block(ch: str) -> bool:
    cp = ord(ch)
    return 0x370 <= cp <= 0x3FF or 0x1F00 <= cp <= 0x1FFF


def _transliterate_greek(run: str) -> str:
    """Romanize one contiguous run of Greek-script text (ALA-LC)."""
    # Precomposed letters with breathing/accent/subscript marks (e.g. ἴ, ῥ,
    # ᾳ) must be split into base + combining marks to be table-driven. This
    # is safe here because it's applied only to an already-extracted Greek
    # run, never to the whole input string (see the module-level NFD note).
    normalized = unicodedata.normalize("NFD", run)

    clusters: list = []
    for ch in normalized:
        if ch.lower() in _GREEK_BASE:
            clusters.append({"base": ch, "marks": set()})
        elif unicodedata.combining(ch):
            if clusters:
                clusters[-1]["marks"].add(ch)
            # a stray combining mark with no preceding base letter is dropped
        else:
            clusters.append({"literal": ch})

    out: list = []
    j, n = 0, len(clusters)
    while j < n:
        cluster = clusters[j]
        if "literal" in cluster:
            out.append(cluster["literal"])
            j += 1
            continue

        base = cluster["base"]
        base_lower = base.lower()
        marks = cluster["marks"]
        is_upper = base.isupper()
        nxt = clusters[j + 1] if j + 1 < n else None
        nxt_base_lower = nxt.get("base", "").lower() if nxt else None

        if base_lower == "γ" and nxt_base_lower in _GREEK_NASAL_TRIGGERS:
            out.append("N" if is_upper else "n")
            j += 1
            continue

        pair = (base_lower, nxt_base_lower)
        if nxt is not None and "base" in nxt and pair in _GREEK_DIPHTHONGS:
            if _GREEK_DIAERESIS not in nxt["marks"]:
                latin = _GREEK_DIPHTHONGS[pair]
                rough = _GREEK_ROUGH_BREATHING in marks or _GREEK_ROUGH_BREATHING in nxt["marks"]
                if rough:
                    latin = "h" + latin
                if is_upper:
                    latin = latin[0].upper() + latin[1:]
                out.append(latin)
                j += 2
                continue

        if base_lower == "ρ" and _GREEK_ROUGH_BREATHING in marks:
            latin = "Rh" if is_upper else "rh"
        else:
            latin = _GREEK_BASE[base_lower]
            if _GREEK_ROUGH_BREATHING in marks:
                latin = "h" + latin
            if is_upper:
                latin = latin[0].upper() + latin[1:]
        out.append(latin)
        j += 1

    return "".join(out)


# --- Persian/Arabic (ALA-LC) ---------------------------------------------
#
# A Perso-Arabic abjad: consonants carry no inherent vowel (unlike the
# Brahmic abugidas above) — a vowel only appears via a following harakat
# diacritic. One merged, Arabic-flavored table serves both languages (see
# the module docstring for why). Handled as its own contiguous-run branch,
# triggered by the Arabic Unicode block, which also covers the four
# Persian-only letters and both Arabic-Indic digit ranges.

_ARABIC_CONSONANTS = {
    "ء": "ʼ", "ا": "ā", "أ": "ʼ", "إ": "ʼ", "آ": "ā", "ى": "ā",
    "ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "ḥ", "خ": "kh",
    "د": "d", "ذ": "dh", "ر": "r", "ز": "z", "س": "s", "ش": "sh",
    "ص": "ṣ", "ض": "ḍ", "ط": "ṭ", "ظ": "ẓ", "ع": "ʻ", "غ": "gh",
    "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "و": "w", "ي": "y", "ة": "h", "ؤ": "ʼ", "ئ": "ʼ",
    # Persian-only letters
    "پ": "p", "چ": "ch", "ژ": "zh", "گ": "g",
    # Persian/Urdu glyph variants of the Arabic letters above, common in
    # the bundled data's Persian/Middle-Persian/Urdu-adjacent entries —
    # same sound, different code point than their Arabic counterpart.
    "ک": "k",   # KEHEH, Persian/Urdu variant of ك
    "ی": "y",   # FARSI YEH, Persian/Urdu variant of ي
    "ہ": "h",   # HEH GOAL, Urdu variant of ه
    "ھ": "h",   # HEH DOACHASHMEE, Urdu (aspiration digraphs like بھ)
    "ڈ": "ḍ",   # DDAL, Urdu retroflex d
    "ڭ": "ng",  # NG, rare Central Asian Arabic-script letter
    "ٱ": "ā",   # ALEF WASLA
    "ڙ": "r",   # REH WITH FOUR DOTS ABOVE, Sindhi
}
_ARABIC_HARAKAT = {"َ": "a", "ِ": "i", "ُ": "u", "ْ": "", "ٰ": "ā"}  # incl. dagger alif
_ARABIC_TANWIN = {"ً": "an", "ٍ": "in", "ٌ": "un"}
_ARABIC_SHADDA = "ّ"
_ARABIC_DIGITS = {c: str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}
_ARABIC_DIGITS.update({c: str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")})


def _in_arabic_block(ch: str) -> bool:
    return 0x600 <= ord(ch) <= 0x6FF


def _transliterate_arabic(run: str) -> str:
    """Romanize one contiguous run of Perso-Arabic-script text (ALA-LC)."""
    out: list = []
    i, n = 0, len(run)
    while i < n:
        ch = run[i]
        if ch in _ARABIC_CONSONANTS:
            base = _ARABIC_CONSONANTS[ch]
            j = i + 1
            doubled = False
            vowel = ""
            # Shadda and the vowel diacritic can appear in either order:
            # NFC-normalized text (combining class order) puts the vowel
            # first, but "shadda then vowel" is also common in hand-typed
            # text, so check both diacritic slots order-agnostically.
            for _ in range(2):
                if j < n and run[j] == _ARABIC_SHADDA and not doubled:
                    doubled = True
                    j += 1
                elif j < n and run[j] in _ARABIC_HARAKAT and not vowel:
                    vowel = _ARABIC_HARAKAT[run[j]]
                    j += 1
                elif j < n and run[j] in _ARABIC_TANWIN and not vowel:
                    vowel = _ARABIC_TANWIN[run[j]]
                    j += 1
                else:
                    break
            out.append(base + base + vowel if doubled else base + vowel)
            i = j
        elif ch in _ARABIC_DIGITS:
            out.append(_ARABIC_DIGITS[ch])
            i += 1
        elif ch in _ARABIC_HARAKAT or ch in _ARABIC_TANWIN or ch == _ARABIC_SHADDA:
            # a stray diacritic with no preceding consonant is dropped
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


# --- merged flat tables (the five Unicode blocks don't overlap) --------

_VOWELS = {
    **_DEVANAGARI_VOWELS, **_TAMIL_VOWELS, **_TELUGU_VOWELS,
    **_KANNADA_VOWELS, **_MALAYALAM_VOWELS,
}
_MATRAS = {
    **_DEVANAGARI_MATRAS, **_TAMIL_MATRAS, **_TELUGU_MATRAS,
    **_KANNADA_MATRAS, **_MALAYALAM_MATRAS,
}
_CONSONANTS = {
    **_DEVANAGARI_CONSONANTS, **_TAMIL_CONSONANTS, **_TELUGU_CONSONANTS,
    **_KANNADA_CONSONANTS, **_MALAYALAM_CONSONANTS,
}
_MARKS = {
    **_DEVANAGARI_MARKS, **_TAMIL_MARKS, **_TELUGU_MARKS,
    **_KANNADA_MARKS, **_MALAYALAM_MARKS,
}
_DIGITS = {
    **_DEVANAGARI_DIGITS, **_TAMIL_DIGITS, **_TELUGU_DIGITS,
    **_KANNADA_DIGITS, **_MALAYALAM_DIGITS,
}
_CHILLU = dict(_MALAYALAM_CHILLU)
_VIRAMAS = {
    _DEVANAGARI_VIRAMA, _TAMIL_VIRAMA, _TELUGU_VIRAMA,
    _KANNADA_VIRAMA, _MALAYALAM_VIRAMA,
}


def transliterate_text(text: str) -> str:
    """Romanize Devanagari/Tamil/Telugu/Kannada/Malayalam/Greek/Perso-Arabic
    text to Latin.

    Any character outside these scripts (Latin letters, digits,
    punctuation, combining marks already used in reconstructed proto-forms
    like ``*hūs``) is passed through unchanged, so this is safe to call on
    already-Latin text, or text mixing scripts with Latin annotations.
    """
    out: list = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if _in_greek_block(ch):
            start = i
            i += 1
            while i < n and (_in_greek_block(text[i]) or unicodedata.combining(text[i])):
                i += 1
            out.append(_transliterate_greek(text[start:i]))
        elif _in_arabic_block(ch):
            start = i
            i += 1
            while i < n and _in_arabic_block(text[i]):
                i += 1
            out.append(_transliterate_arabic(text[start:i]))
        elif ch in _CONSONANTS:
            base = _CONSONANTS[ch]
            if nxt in _VIRAMAS:
                out.append(base[:-1])
                i += 2
            elif nxt in _MATRAS:
                out.append(base[:-1] + _MATRAS[nxt])
                i += 2
            else:
                out.append(base)
                i += 1
        elif ch in _VOWELS:
            out.append(_VOWELS[ch])
            i += 1
        elif ch in _CHILLU:
            out.append(_CHILLU[ch])
            i += 1
        elif ch in _MARKS:
            out.append(_MARKS[ch])
            i += 1
        elif ch in _DIGITS:
            out.append(_DIGITS[ch])
            i += 1
        elif ch in _VIRAMAS:
            # stray virama with no preceding consonant handled above; drop it
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


_RLI = "⁧"  # RIGHT-TO-LEFT ISOLATE
_PDI = "⁩"  # POP DIRECTIONAL ISOLATE


def _contains_rtl(text: str) -> bool:
    """Whether ``text`` contains any Perso-Arabic (right-to-left) script."""
    return any(_in_arabic_block(ch) for ch in text)


def annotate_transliteration(text: str) -> str:
    """Show ``text`` alongside its Latin romanization, original script first.

    ``text`` that's already Latin script (German, reconstructed
    Proto-Indo-European forms like ``*hūs``, English loanwords, etc.) is
    returned unchanged, since ``transliterate_text`` would just echo it back
    and a parenthetical repeating the same text is noise, not information.

    Persian/Arabic text is right-to-left, so the original word is wrapped in
    Unicode bidi isolate marks (RLI/PDI) before the parenthetical is
    appended — this tells any bidi-aware renderer (terminal, editor,
    browser) to treat the Arabic run as an opaque block, so the
    romanization reliably lands to its right instead of being reordered by
    the bidi algorithm. These are "default ignorable" format characters, so
    non-bidi-aware terminals render them invisibly with no visual change.
    """
    translit = transliterate_text(text)
    if translit == text:
        return text
    display = f"{_RLI}{text}{_PDI}" if _contains_rtl(text) else text
    return f"{display} ({translit})"
