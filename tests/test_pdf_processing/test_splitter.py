import pytest
import os
from easy_study_flashcards.pdf_processing.splitter import split_pdf_by_chapters
from easy_study_flashcards.pdf_processing.core import PDFProcessor

def test_chapter_detection(pdf_paths):
    """Test chapter detection in PDF"""
    splitter = PDFSplitter(pdf_paths['calculus'])
    chapters = splitter.detect_chapters()
    assert isinstance(chapters, list)
    assert len(chapters) > 0
    
def test_content_splitting():
    """Test content splitting logic"""
    sample_text = """
    Chapter 1: Introduction
    Some content here
    Chapter 2: Basic Concepts
    More content here
    """
    splitter = PDFSplitter()
    sections = splitter.split_content(sample_text)
    assert len(sections) == 2
    assert "Introduction" in sections[0]
    assert "Basic Concepts" in sections[1]

def test_invalid_pdf_handling():
    """Test handling of invalid PDF files"""
    with pytest.raises(FileNotFoundError):
        split_pdf_by_chapters("nonexistent.pdf")

def test_empty_pdf_handling(tmp_path):
    """Test handling of empty PDF files"""
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")
    with pytest.raises(ValueError):
        split_pdf_by_chapters(empty_pdf)