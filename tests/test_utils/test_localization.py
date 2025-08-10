import pytest
from easy_study_flashcards.utils.localization import get_text, set_language

def test_language_setting():
    assert set_language("en") == "en"
    assert set_language("de") == "de"
    with pytest.raises(ValueError):
        set_language("invalid")

def test_text_retrieval():
    set_language("en")
    assert get_text("welcome") != ""
    assert get_text("study") != ""

def test_fallback_language():
    set_language("fr")  # Assuming fr is not fully supported
    assert get_text("welcome") != ""  # Should fall back to English

def test_localization():
    assert localize("hello", "en") == "hello"
    assert localize("hello", "es") == "hola"
    assert localize("goodbye", "en") == "goodbye"
    assert localize("goodbye", "es") == "adiós"