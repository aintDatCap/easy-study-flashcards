import os
import pathlib
from google import genai
from typing import List, Optional
from .colors import Colors
from gemini.client import get_chapters_from_gemini, process_pdfs_with_gemini_sdk
from gemini.models import *
from pdf_processing.core import PDFProcessor

if __name__ == "__main__":
    pdf_folder: str = "."

    gemini_model_1_5: str = "gemini-1.5-flash"
    gemini_model_2_5: str = "gemini-2.5-flash"

    api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            f"{Colors.FAIL}Errore: La variabile d'ambiente 'GEMINI_API_KEY' non è impostata. Si prega di impostarla prima di eseguire lo script.{Colors.ENDC}"
        )
        exit()

    gemini_client: genai.Client = genai.Client(api_key=api_key)

    PAGES_TO_ANALYZE_FOR_CHAPTERS: int = 10  # RIDOTTO A 10
    PAGES_TO_ANALYZE_FOR_FIRST_CHAPTER_PHYSICAL_PAGE: int = 25  # INVARIATO

    pdf_files_to_process: List[str] = [
        f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")
    ]

    if not pdf_files_to_process:
        print(
            f"{Colors.WARNING}Nessun file PDF trovato nella cartella specificata per la divisione in capitoli.{Colors.ENDC}"
        )
    else:
        for pdf_file in pdf_files_to_process:
            full_pdf_path: pathlib.Path = pathlib.Path(
                os.path.join(pdf_folder, pdf_file)
            )

            book_structure = get_chapters_from_gemini(
                full_pdf_path,
                gemini_model_1_5,  # Modello per i capitoli
                gemini_model_2_5,  # Modello per trovare l'indice del primo capitolo nel pdf
                gemini_client,
                PAGES_TO_ANALYZE_FOR_CHAPTERS,
                PAGES_TO_ANALYZE_FOR_FIRST_CHAPTER_PHYSICAL_PAGE,
            )

            if book_structure:
                chapters_info: Optional[List[ChapterInfo]] = book_structure.chapters
                first_numbered_page: Optional[int] = (
                    book_structure.first_chapter_physical_page
                )

                print(
                    f"{Colors.OKGREEN}La pagina del primo capitolo del libro si trova alla pagina fisica {first_numbered_page} del PDF '{pdf_file}'.{Colors.ENDC}"
                )

                output_chapter_folder: str = os.path.join(
                    pdf_folder, f"{os.path.splitext(pdf_file)[0]}_chapters"
                )
                PDFProcessor.split_pdf_by_chapters(
                    full_pdf_path,
                    chapters_info,
                    first_numbered_page,
                    output_chapter_folder,
                )

                process_pdfs_with_gemini_sdk(
                    output_chapter_folder, gemini_model_2_5, gemini_client, lang="it"
                )  # TODO: Make other languages available
            else:
                print(
                    f"{Colors.WARNING}Impossibile ottenere informazioni sui capitoli per '{pdf_file}'. Salto la divisione e l'elaborazione.{Colors.ENDC}"
                )

    print(f"\n{Colors.HEADER}Script completato.{Colors.ENDC}\n")
