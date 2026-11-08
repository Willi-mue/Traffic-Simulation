import pytest

from traffic_sim import i18n
from traffic_sim.__main__ import parse_args
from traffic_sim.world import MapError, World


def test_default_is_german():
    assert i18n.get_language() == "de"
    assert i18n.tr("window_title") == "Verkehrssimulation"


def test_all_languages_have_the_same_keys():
    keys = {lang: set(texts) for lang, texts in i18n.TEXTS.items()}
    assert keys["de"] == keys["en"]


def test_help_has_same_number_of_lines():
    de = i18n.TEXTS["de"]["help"].splitlines()
    en = i18n.TEXTS["en"]["help"].splitlines()
    assert len(de) == len(en)


def test_toggle_language():
    i18n.set_language(i18n.next_language())
    assert i18n.get_language() == "en"
    i18n.set_language(i18n.next_language())
    assert i18n.get_language() == "de"


def test_errors_follow_language():
    i18n.set_language("en")
    with pytest.raises(MapError, match="line 1, column 2"):
        World(["<+"])
    i18n.set_language("de")
    with pytest.raises(MapError, match="Zeile 1, Spalte 2"):
        World(["<+"])


def test_cli_lang_option():
    parse_args(["--lang", "en"])
    assert i18n.get_language() == "en"
    parse_args([])
    assert i18n.get_language() == "de"


def test_unknown_language_raises():
    with pytest.raises(ValueError):
        i18n.set_language("fr")
