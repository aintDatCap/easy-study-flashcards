import os
import pathlib
from typing import List, Optional

from dotenv import load_dotenv
from loguru import logger

from easy_study_flashcards.deepseek.client import (
    DeepSeekClientManager,
    get_book_structure_from_deepseek,
    process_pdfs_with_deepseek,
)
from easy_study_flashcards.deepseek.models import ChapterInfo
from easy_study_flashcards.pdf_processing.core import PDFProcessor
from easy_study_flashcards.pdf_processing.splitter import split_pdf_by_chapters
from easy_study_flashcards.utils.latex import get_xelatex_path
from easy_study_flashcards.utils.localization import localizer as _

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    get_xelatex_path()  # checks if xelatex is available

    pdf_folder: str = "."

    deepseek_model_fast: str = "deepseek-v4-flash"
    deepseek_model_pro: str = "deepseek-v4-pro"

    api_key: Optional[str] = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error(_.get_string("api_key_missing"))
        exit()

    deepseek_client: DeepSeekClientManager = DeepSeekClientManager(api_key=api_key)

    PAGES_TO_ANALYZE_FOR_CHAPTERS: int = 30
    PAGES_TO_ANALYZE_FOR_FIRST_CHAPTER_PHYSICAL_PAGE: int = 40

    pdf_files_to_process: List[str] = [
        f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")
    ]

    if not pdf_files_to_process:
        logger.warning(_.get_string("no_pdf_files", folder=pdf_folder))
    else:
        subject_matter_input: str = input(_.get_string("subject_prompt"))
        if not subject_matter_input.strip():
            logger.warning(_.get_string("no_subject"))
            subject_matter_input = _.get_string("generic_subject")

        for pdf_file in pdf_files_to_process:
            full_pdf_path: pathlib.Path = pathlib.Path(
                os.path.join(pdf_folder, pdf_file)
            )

            book_structure = get_book_structure_from_deepseek(
                full_pdf_path,
                deepseek_model_fast,
                deepseek_model_pro,
                deepseek_client,
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
                    _.get_string("chapter_start_index", index=first_numbered_page)
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

                process_pdfs_with_deepseek(
                    output_chapter_folder,
                    deepseek_model_pro,
                    deepseek_client,
                    lang=_.get_current_language().value,
                    subject_matter=subject_matter_input,
                )
            else:
                logger.error(
                    _.get_string(
                        "chapter_info_error",
                        model=deepseek_model_fast,
                        error="No structure returned",
                    )
                )

    logger.info(_.get_string("processing_complete"))
