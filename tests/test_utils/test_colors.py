import pytest
from easy_study_flashcards.utils.colors import color_util_function, get_theme_colors

def test_color_util_function():
    assert color_util_function("red") == "#FF0000"
    assert color_util_function("green") == "#00FF00"
    assert color_util_function("blue") == "#0000FF"

def test_invalid_color():
    with pytest.raises(ValueError):
        color_util_function("invalid_color")

def test_theme_colors():
    theme = get_theme_colors("dark")
    assert isinstance(theme, dict)
    assert "background" in theme
    assert "text" in theme