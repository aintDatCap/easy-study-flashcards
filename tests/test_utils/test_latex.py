import pytest
from easy_study_flashcards.utils.latex import format_latex, clean_latex

def test_latex_functionality():
    assert latex_to_pdf("sample.tex") == "sample.pdf"
    assert latex_to_pdf("invalid.tex") is None
    assert latex_to_pdf("") is None

def test_latex_formatting():
    raw_text = "The equation is: E = mc^2"
    formatted = format_latex(raw_text)
    assert "\\(" in formatted
    assert "\\)" in formatted

def test_latex_cleaning():
    dirty_latex = "\\[ \\text{messy} \\latex \\]"
    cleaned = clean_latex(dirty_latex)
    assert cleaned == "\\text{messy} \\latex"

def test_invalid_latex():
    with pytest.raises(ValueError):
        format_latex("\\invalid{")