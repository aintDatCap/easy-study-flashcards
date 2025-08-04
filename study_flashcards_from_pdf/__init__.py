import os
import pathlib
from typing import List, Optional

from loguru import logger
from study_flashcards_from_pdf.pdf_processing.core import PDFProcessor
from study_flashcards_from_pdf.gemini.client import GeminiClientManager, get_chapters_from_gemini, process_pdfs_with_gemini_sdk
from study_flashcards_from_pdf.gemini.models import ChapterInfo
from study_flashcards_from_pdf.pdf_processing.splitter import split_pdf_by_chapters
from study_flashcards_from_pdf.utils import get_xelatex_path
from study_flashcards_from_pdf.utils.colors import Colors # Assuming pdf_processing/core.py

if __name__ == "__main__":
    
    get_xelatex_path() # checks if xelatex is available

    pdf_folder: str = "."

    gemini_model_1_5: str = "gemini-1.5-flash"
    gemini_model_2_5: str = "gemini-2.5-flash"

    api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            f"{Colors.FAIL}Errore: La variabile d'ambiente 'GEMINI_API_KEY' non è impostata. Si prega di impostarla prima di eseguire lo script.{Colors.ENDC}"
        )
        exit()

    gemini_client: GeminiClientManager = GeminiClientManager(api_key=api_key)

    PAGES_TO_ANALYZE_FOR_CHAPTERS: int = 10
    PAGES_TO_ANALYZE_FOR_FIRST_CHAPTER_PHYSICAL_PAGE: int = 25

    pdf_files_to_process: List[str] = [
        f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")
    ]

    if not pdf_files_to_process:
        print(
            f"{Colors.WARNING}Nessun file PDF trovato nella cartella specificata per la divisione in capitoli.{Colors.ENDC}"
        )
    else:
        # Ask the user for the subject matter
        subject_matter_input: str = input(
            f"{Colors.OKCYAN}Per quale materia vuoi generare le schede di studio? (es. 'Algebra Lineare', 'Storia Romana', 'Fisica Quantistica'): {Colors.ENDC}"
        )
        if not subject_matter_input.strip():
            print(f"{Colors.WARNING}Nessuna materia specificata. Utilizzo 'materia generica'.{Colors.ENDC}")
            subject_matter_input = "materia generica"


        for pdf_file in pdf_files_to_process:
            full_pdf_path: pathlib.Path = pathlib.Path(
                os.path.join(pdf_folder, pdf_file)
            )

            book_structure = get_chapters_from_gemini(
                full_pdf_path,
                gemini_model_1_5,
                gemini_model_2_5,
                gemini_client,
                lang="it", # Assuming Italian is the desired language for prompts
                pages_to_process_chapters=PAGES_TO_ANALYZE_FOR_CHAPTERS,
                pages_to_process_physical_page=PAGES_TO_ANALYZE_FOR_FIRST_CHAPTER_PHYSICAL_PAGE,
            )

            if book_structure:
                chapters_info: Optional[List[ChapterInfo]] = book_structure.chapters
                first_numbered_page: Optional[int] = (
                    book_structure.first_chapter_physical_page
                )

                logger.info(f"The first chapter starts at the index {first_numbered_page} of the PDF file")

                output_chapter_folder: str = os.path.join(
                    pdf_folder, f"{os.path.splitext(pdf_file)[0]}_chapters"
                )
                split_pdf_by_chapters(
                    full_pdf_path,
                    chapters_info,
                    first_numbered_page,
                    output_chapter_folder,
                )

                process_pdfs_with_gemini_sdk(
                    output_chapter_folder,
                    gemini_model_2_5,
                    gemini_client,
                    lang="it", 
                    subject_matter=subject_matter_input,
                )
            else:
                print(
                    f"{Colors.WARNING}Impossibile ottenere informazioni sui capitoli per '{pdf_file}'. Salto la divisione e l'elaborazione.{Colors.ENDC}"
                )

    print(f"\n{Colors.HEADER}Script completato.{Colors.ENDC}\n")