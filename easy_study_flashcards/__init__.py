import os
import pathlib
from typing import List, Optional

from loguru import logger
from easy_study_flashcards.pdf_processing.core import PDFProcessor
from easy_study_flashcards.gemini.client import GeminiClientManager, get_chapters_from_gemini, process_pdfs_with_gemini_sdk
from easy_study_flashcards.gemini.models import ChapterInfo
from easy_study_flashcards.pdf_processing.splitter import split_pdf_by_chapters
from easy_study_flashcards.utils.latex import get_xelatex_path
from easy_study_flashcards.utils.colors import Colors
from easy_study_flashcards.utils.localization import localizer as _

if __name__ == "__main__":
    get_xelatex_path() # checks if xelatex is available

    pdf_folder: str = "."

    gemini_model_1_5: str = "gemini-1.5-flash"
    gemini_model_2_5: str = "gemini-2.5-flash"

    api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error(_.get_string('api_key_missing'))
        exit()

    gemini_client: GeminiClientManager = GeminiClientManager(api_key=api_key)

    PAGES_TO_ANALYZE_FOR_CHAPTERS: int = 10
    PAGES_TO_ANALYZE_FOR_FIRST_CHAPTER_PHYSICAL_PAGE: int = 25

    pdf_files_to_process: List[str] = [
        f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")
    ]

    if not pdf_files_to_process:
        logger.warning(_.get_string('no_pdf_files', folder=pdf_folder))
    else:
        subject_matter_input: str = input(_.get_string('subject_prompt'))
        if not subject_matter_input.strip():
            logger.warning(_.get_string('no_subject'))
            subject_matter_input = _.get_string("generic_subject")

        for pdf_file in pdf_files_to_process:
            full_pdf_path: pathlib.Path = pathlib.Path(
                os.path.join(pdf_folder, pdf_file)
            )

            book_structure = get_chapters_from_gemini(
                full_pdf_path,
                gemini_model_1_5,
                gemini_model_2_5,
                gemini_client,
                lang=_.get_current_language().value,
                pages_to_process_chapters=PAGES_TO_ANALYZE_FOR_CHAPTERS,
                pages_to_process_physical_page=PAGES_TO_ANALYZE_FOR_FIRST_CHAPTER_PHYSICAL_PAGE,
            )

            if book_structure:
                chapters_info: Optional[List[ChapterInfo]] = book_structure.chapters
                first_numbered_page: Optional[int] = (
                    book_structure.first_chapter_physical_page
                )

                logger.info(
                    _.get_string(
                        'chapter_start_index',
                        index=first_numbered_page
                    )
                )

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
                    lang=_.get_current_language().value,
                    subject_matter=subject_matter_input,
                )
            else:
                logger.error(
                    _.get_string(
                        'chapter_info_error',
                        model=gemini_model_1_5,
                        error='No structure returned'
                    )
                )
    print(f"{Colors.WARNING}Total cost for the whole conversion: ${gemini_client.total_cost.amount_as_string()} {Colors.ENDC}")
    logger.info(_.get_string('processing_complete'))