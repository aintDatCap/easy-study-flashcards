import pytest
import os


@pytest.fixture(scope="session")
def test_assets_dir():
    """Return the path to the test assets directory, downloading files if needed"""
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)

    # Check if assets need to be downloaded
    existing_pdfs = [f for f in os.listdir(assets_dir) if f.endswith(".pdf")]
    if len(existing_pdfs) < 3:
        try:
            import gdown
        except ImportError:
            raise ImportError(
                "gdown is required to download test assets. Please install it with 'pipenv install --dev'."
            )

        file_ids = [
            "1dYgNJhAPwST242vCtwdEP69xmgybLYXT",
            "1dV8mrGnO6-PzSN5KSyM9A6IYLkNCe8P_",
            "1jIvXi5cqLyD_iw0i2G64YmA7RkTXNkKf",
        ]

        cwd = os.getcwd()
        try:
            os.chdir(assets_dir)
            for file_id in file_ids:
                # use_cookies=False is often needed for public drive files to avoid issues
                gdown.download(id=file_id, quiet=False)
        finally:
            os.chdir(cwd)

    return assets_dir


@pytest.fixture(scope="session")
def test_pdfs(test_assets_dir):
    return [f for f in os.listdir(test_assets_dir) if f.endswith(".pdf")]


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
    return {"cards": [{"question": "Test Q", "answer": "Test A"}]}
