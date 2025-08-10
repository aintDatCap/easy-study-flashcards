import pytest
import os
from easy_study_flashcards.pdf_processing.core import PDFProcessor

@pytest.fixture
def pdf_paths():
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
    return {
        'calculus': os.path.join(assets_dir, 'Calculus 3 - Jerrold Marseden and Alan Weinstein.pdf'),
        'algebra': os.path.join(assets_dir, 'Elements of Abstract and Linear Algebra - E. H. Connell.pdf'),
        'physics': os.path.join(assets_dir, 'Modern Physics - Benjamin Crowell.pdf')
    }

def test_pdf_loader_exists(pdf_paths):
    """Test if PDF files exist in assets folder"""
    for name, path in pdf_paths.items():
        assert os.path.exists(path), f"PDF {name} not found at {path}"

def test_pdf_processor_initialization(pdf_paths):
    """Test PDF processor initialization"""
    processor = PDFProcessor(pdf_paths['calculus'])
    assert processor is not None
    assert hasattr(processor, 'extract_text')

def test_pdf_text_extraction(pdf_paths):
    """Test PDF text extraction"""
    processor = PDFProcessor(pdf_paths['algebra'])
    text = processor.extract_text()
    assert isinstance(text, str)
    assert len(text) > 0
    assert "algebra" in text.lower()