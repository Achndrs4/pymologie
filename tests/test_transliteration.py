from pymologie import transliterate
from pymologie.transliteration import annotate_transliteration, transliterate_text


def test_devanagari_guru() -> None:
    assert transliterate_text("गुरु") == "guru"


def test_telugu_guru() -> None:
    assert transliterate_text("గురు") == "guru"


def test_kannada_guru() -> None:
    assert transliterate_text("ಗುರು") == "guru"


def test_malayalam_guru() -> None:
    assert transliterate_text("ഗുരു") == "guru"


def test_tamil_guru_has_no_voicing_distinction() -> None:
    # Tamil script doesn't mark voiced/voiceless consonants, so a literal
    # letter transliteration of "குரு" is "kuru", not the phonetic "guru".
    assert transliterate_text("குரு") == "kuru"


def test_virama_suppresses_inherent_vowel() -> None:
    assert transliterate_text("विश्व") == "viśva"


def test_conjunct_across_virama() -> None:
    assert transliterate_text("सिद्ध") == "siddha"


def test_anusvara_and_vocalic_r() -> None:
    assert transliterate_text("संस्कृत") == "saṃskr̥ta"


def test_passes_through_already_latin_text() -> None:
    assert transliterate_text("*hūs") == "*hūs"
    assert transliterate_text("taxi") == "taxi"


def test_passes_through_mixed_script_and_latin() -> None:
    assert transliterate_text("Proto-Dravidian *teṉ") == "Proto-Dravidian *teṉ"


def test_top_level_transliterate_is_reexported() -> None:
    assert transliterate("गुरु") == "guru"


def test_annotate_transliteration_shows_both_scripts_side_by_side() -> None:
    assert annotate_transliteration("गुरु") == "गुरु (guru)"


def test_annotate_transliteration_passes_through_latin_unchanged() -> None:
    assert annotate_transliteration("taxi") == "taxi"
    assert annotate_transliteration("*hūs") == "*hūs"


# --- Greek (ALA-LC) -------------------------------------------------------


def test_greek_single_letters_and_digraphs() -> None:
    assert transliterate_text("πλαστικός") == "plastikos"


def test_greek_diphthong_and_smooth_breathing_dropped() -> None:
    # Αἴγυπτος carries *smooth* breathing (on the iota of the αι diphthong),
    # not rough — so there's no leading "h", unlike English "Egypt".
    assert transliterate_text("Αἴγυπτος") == "Aigyptos"


def test_greek_rough_breathing_on_diphthong() -> None:
    assert transliterate_text("Εὐρώπη") == "Eurōpē"


def test_greek_rough_breathing_on_rho_is_rh_not_hr() -> None:
    assert transliterate_text("ῥήτωρ") == "rhētōr"


def test_greek_gamma_nasal_assimilation() -> None:
    assert transliterate_text("ἄγγελος") == "angelos"


def test_greek_iota_subscript_is_dropped_not_appended() -> None:
    assert transliterate_text("ᾳ") == "a"
    assert transliterate_text("ῃ") == "ē"
    assert transliterate_text("ῳ") == "ō"


def test_greek_diaeresis_breaks_diphthong() -> None:
    # Without a diaeresis, "αυ" is the diphthong "au"; with one on the
    # upsilon, it's two separate letters, and standalone upsilon is "y".
    assert transliterate_text("αυ") == "au"
    assert transliterate_text("αϋ") == "ay"


# --- Persian/Arabic (ALA-LC) ----------------------------------------------


def test_arabic_shadda_doubles_the_consonant() -> None:
    assert transliterate_text("مُحَمَّد") == "muḥammad"


def test_arabic_tanwin() -> None:
    assert transliterate_text("كِتابٌ") == "kitābun"


def test_persian_only_letters() -> None:
    assert transliterate_text("پارس") == "pārs"
    assert transliterate_text("گل") == "gl"


def test_annotate_transliteration_wraps_rtl_word_in_bidi_isolates() -> None:
    annotated = annotate_transliteration("قهوه")
    assert annotated == "⁧قهوه⁩ (qhwh)"
