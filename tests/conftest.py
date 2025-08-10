import pytest
import os

@pytest.fixture(scope="session")
def test_assets_dir():
    """Return the path to the test assets directory"""
    return os.path.join(os.path.dirname(__file__), 'assets')

@pytest.fixture(scope="session")
def test_pdfs():
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    return [f for f in os.listdir(assets_dir) if f.endswith(".pdf")]

@pytest.fixture(scope="session")
def sample_pdf_content():
    """Return sample PDF content for testing"""
    return """
    Chapter 1: Introduction to Mathematics
    1.1 Basic Concepts
    1.2 Number Systems
    
    Chapter 2: Linear Algebra
    2.1 Vectors
    2.2 Matrices
    """

@pytest.fixture
def sample_math_text():
    return """
    Chapter 1: Introduction to Calculus
    The fundamental theorem of calculus states that differentiation
    and integration are inverse operations.
    """

@pytest.fixture
def mock_gemini_response():
    return {
        "cards": [
            {"question": "Test Q", "answer": "Test A"}
        ]
    }