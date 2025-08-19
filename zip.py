import os
import shutil
import zipapp
from pathlib import Path

def create_distribution():
    # Get project root directory
    root_dir = Path(__file__).parent
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    package_dir = root_dir / "easy_study_flashcards"
    
    # Clean and create build/dist directories
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    build_dir.mkdir()
    dist_dir.mkdir()
    
    # Copy package files to build directory
    shutil.copytree(
        package_dir,
        build_dir / "easy_study_flashcards",
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc')
    )
    
    # Create __main__.py in build directory
    main_file = build_dir / "__main__.py"
    main_file.write_text('''
from easy_study_flashcards.gemini.client import GeminiClient
from easy_study_flashcards.pdf_processing.core import PDFProcessor
from easy_study_flashcards.pdf_processing.splitter import split_pdf_by_chapters

if __name__ == "__main__":
    print("Easy Study Flashcards Starting...")
    '''.strip())

    # Get pipenv python interpreter path
    interpreter = os.environ.get('VIRTUAL_ENV')
    if not interpreter:
        raise EnvironmentError("Pipenv virtual environment not activated!")
    python_path = Path(interpreter) / 'Scripts' / 'python.exe'

    # Create the archive
    output_file = dist_dir / "easy_study_flashcards.pyz"
    zipapp.create_archive(
        build_dir,
        output_file,
        interpreter=str(python_path),
        filter=lambda path: not path.name.startswith('__pycache__')
    )

    print(f"Archive created successfully at {output_file}")

if __name__ == "__main__":
    create_distribution()