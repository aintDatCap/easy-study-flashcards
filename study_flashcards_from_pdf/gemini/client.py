import os
import pathlib
import time
from io import BytesIO
from typing import List, Optional
from google import genai
from google.genai.types import GenerateContentResponse, Part
from pypdf import PdfReader

from study_flashcards_from_pdf.gemini.models import (
    BookStructure,
    ChapterInfo,
    ChaptersOnly,
)
from study_flashcards_from_pdf.gemini.prompts import PromptsForGemini
from study_flashcards_from_pdf.utils.latex import fix_common_generated_latex_erros
from study_flashcards_from_pdf.utils.colors import Colors
from study_flashcards_from_pdf.utils.localization import localizer as _
from loguru import logger

from study_flashcards_from_pdf.pdf_processing.core import PDFProcessor


class GeminiClientManager(genai.Client):
    """
    A class that extends the Gemini client to manage API calls
    and enforce rate limits.
    """
    request_timestamps: list[float]
    __MAX_REQUESTS_PER_MINUTE: int = 10
    __TIME_WINDOW_SECONDS: int = 60

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_timestamps = []

    def _wait_for_rate_limit(self):
        """
        Internal method to enforce the API request rate limit.
        """
        current_time: float = time.time()
        # Filter out timestamps older than the time window
        self.request_timestamps = [
            ts for ts in self.request_timestamps if current_time - ts < self.__TIME_WINDOW_SECONDS
        ]

        if len(self.request_timestamps) >= self.__MAX_REQUESTS_PER_MINUTE:
            time_to_wait: float = (
                self.request_timestamps[0] + self.__TIME_WINDOW_SECONDS - current_time
            )
            if time_to_wait > 0:
                logger.warning(
                    _.get_string('rate_limit', seconds=time_to_wait)
                )
                time.sleep(time_to_wait)
                # After waiting, update the current time and filter timestamps again
                current_time = time.time()
                self.request_timestamps = [
                    ts for ts in self.request_timestamps if current_time - ts < self.__TIME_WINDOW_SECONDS
                ]
    
    def generate_content_with_rate_limit(self, **kwargs) -> GenerateContentResponse:
        """
        Wrapper around the generate_content method that respects the rate limit.
        """
        self._wait_for_rate_limit()
        
        # Make the API call
        response = self.models.generate_content(**kwargs)
        
        # Record the timestamp of the new request
        self.request_timestamps.append(time.time())
        return response


def get_chapters_from_gemini(
    pdf_path: pathlib.Path,
    model_name_chapters: str,  # Model for chapters (e.g., Gemini 1.5 Pro)
    model_name_physical_page: str,  # Model for physical page (e.g., Gemini 1.5 Flash)
    client: GeminiClientManager,
    lang: str,
    pages_to_process_chapters: int = 10,
    pages_to_process_physical_page: int = 25,
) -> Optional[BookStructure]:
    """
    Asks Gemini models to identify chapters and the physical page of the first chapter,
    processing only a subset of initial PDF pages.
    Returns a BookStructure object.
    """

    assert pages_to_process_chapters > 0, "pages_to_process_chapters should be bigger than 0"
    assert pages_to_process_physical_page > 0, "pages_to_process_physical_page should be bigger than 0"

    print(
        f"\n--- {Colors.OKBLUE}{_.get_string('chapter_analysis_start', filename=pdf_path.name)}{Colors.ENDC} ---"
    )

    reader: PdfReader = PdfReader(pdf_path)
    total_pdf_pages: int = len(reader.pages)

    if total_pdf_pages == 0:
        logger.warning(
            f"PDF file '{pdf_path.name}' contains no pages."
        )
        return None

    chapters_info: Optional[List[ChapterInfo]] = None
    first_chapter_physical_page: Optional[int] = None

    # --- Prepare PDF parts for the two models using PDFProcessor ---

    # For the chapters model (fewer pages)
    num_pages_to_extract_chapters: int = min(pages_to_process_chapters, total_pdf_pages)
    sub_pdf_bytes_chapters: Optional[BytesIO] = PDFProcessor.extract_pdf_pages_to_bytes(
        pdf_path, 0, num_pages_to_extract_chapters
    )
    if not sub_pdf_bytes_chapters:
        return None

    # For the physical page model (more pages)
    num_pages_to_extract_physical_page: int = min(
        pages_to_process_physical_page, total_pdf_pages
    )
    sub_pdf_bytes_physical_page: Optional[BytesIO] = (
        PDFProcessor.extract_pdf_pages_to_bytes(
            pdf_path, 0, num_pages_to_extract_physical_page
        )
    )
    if not sub_pdf_bytes_physical_page:
        return None

    # --- PHASE 1: Extract chapters with Gemini 1.5 (using pages_to_process_chapters) ---
    prompt_chapters: str = PromptsForGemini.get_prompt_chapters_pages(
        lang=lang, pages_to_scan=num_pages_to_extract_chapters
    )
    print(
        f"{Colors.OKCYAN}Sending first {num_pages_to_extract_chapters} pages to '{model_name_chapters}' for chapter extraction...{Colors.ENDC}"
    )
    try:
        gemini_response_chapters: GenerateContentResponse = (
            client.generate_content_with_rate_limit(
                model=model_name_chapters,
                contents=[
                    Part.from_bytes(
                        data=sub_pdf_bytes_chapters.getvalue(),
                        mime_type="application/pdf",
                    ),
                    prompt_chapters,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ChaptersOnly,
                },
            )
        )
        chapters_only: ChaptersOnly = gemini_response_chapters.parsed  # type: ignore
        chapters_info = chapters_only.chapters
        print(
            f"{Colors.OKGREEN}Chapter information successfully extracted from '{model_name_chapters}'.{Colors.ENDC}"
        )
    except Exception as e:
        print(
            f"{Colors.FAIL}Error getting chapters from '{model_name_chapters}': {e}{Colors.ENDC}"
        )
        if 'gemini_response_chapters' in locals() and hasattr(gemini_response_chapters, "text"):  # type: ignore
            print(f"{Colors.FAIL}Raw response from Gemini (on error): {gemini_response_chapters.text}{Colors.ENDC}")  # type: ignore
        return None

    # --- PHASE 2: Extract physical page of the first chapter with Gemini 2.5 (using pages_to_process_physical_page) ---
    prompt_physical_page: str = PromptsForGemini.get_prompt_first_chapter_physical_page(
        lang=lang, pages_to_scan=num_pages_to_extract_physical_page
    )
    print(
        f"{Colors.OKCYAN}Sending first {num_pages_to_extract_physical_page} pages to '{model_name_physical_page}' for first chapter physical page extraction...{Colors.ENDC}"
    )
    try:
        gemini_response_physical_page: GenerateContentResponse = (
            client.generate_content_with_rate_limit(
                model=model_name_physical_page,
                contents=[
                    Part.from_bytes(
                        data=sub_pdf_bytes_physical_page.getvalue(),
                        mime_type="application/pdf",
                    ),
                    prompt_physical_page,
                ],
                config={
                    "response_mime_type": "text/plain",  # We expect only an integer as text
                },
            )
        )
        if gemini_response_physical_page.text is None:
            print(f"{Colors.FAIL}Error: Gemini model '{model_name_physical_page}' returned no text response.{Colors.ENDC}")
            return None

        # Try to convert the response to an integer
        try:
            first_chapter_physical_page = int(
                gemini_response_physical_page.text.strip()
            )
        except ValueError:
            print(
                f"{Colors.FAIL}Error: Gemini response for physical page is not a valid integer: '{gemini_response_physical_page.text.strip()}'{Colors.ENDC}"
            )
            return None
        
        print(
            f"{Colors.OKGREEN}First chapter physical page successfully extracted from '{model_name_physical_page}'.{Colors.ENDC}"
        )
    except Exception as e:
        print(
            f"{Colors.FAIL}Error getting the first chapter's physical page from '{model_name_physical_page}': {e}{Colors.ENDC}"
        )
        if 'gemini_response_physical_page' in locals() and hasattr(gemini_response_physical_page, "text"):  # type: ignore
            print(f"{Colors.FAIL}Raw response from Gemini (on error): {gemini_response_physical_page.text}{Colors.ENDC}")  # type: ignore
        return None

    if chapters_info is not None and first_chapter_physical_page is not None:
        return BookStructure(
            chapters=chapters_info,
            first_chapter_physical_page=first_chapter_physical_page,
        )
    return None


def process_pdfs_with_gemini_sdk(
    folder_path: str,
    model_name: str,
    client: GeminiClientManager,
    lang: str,
    subject_matter: str,  # Added subject_matter
) -> None:
    """
    Processes PDF files with the Gemini SDK, including LaTeX validation and auto-correction,
    and then converts the validated LaTeX to PDF.
    """

    if not os.path.isdir(folder_path):
        logger.error(_.get_string('folder_not_exist', folder=folder_path))
        return

    result_folder_path: str = os.path.join(folder_path, "results/")
    if not os.path.exists(result_folder_path):
        os.mkdir(result_folder_path)

    pdf_files: List[str] = [
        f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        logger.warning(_.get_string('no_pdf_files', folder=folder_path))
        return

    logger.info(_.get_string('pdf_processing_start', folder=folder_path))
    logger.info(
        _.get_string('pdf_files_found', count=len(pdf_files), folder=folder_path)
    )

    MAX_RETRIES: int = 3

    for pdf_file in pdf_files:
        pdf_path: pathlib.Path = pathlib.Path(os.path.join(folder_path, pdf_file))
        output_file_name_base: str = os.path.splitext(pdf_file)[0] + "-domande"
        output_tex_file_path: str = os.path.join(
            result_folder_path, output_file_name_base + ".tex"
        )

        # Make sure to read bytes only once for the original PDF part
        try:
            original_pdf_part: Part = Part.from_bytes(
                data=pdf_path.read_bytes(), mime_type="application/pdf"
            )
        except Exception as e:
            logger.warning(
                f"Error reading PDF file '{pdf_file}': {e}. Skipping this file."
            )
            continue

        num_retries: int = 0
        latex_is_valid: bool = False
        generated_text: str = ""
        last_error_message: str = ""

        while num_retries <= MAX_RETRIES and not latex_is_valid:
            try:
                prompt_to_send: str
                contents_to_send: List[Part | str]

                if num_retries == 0:
                    logger.info(
                        f"Initial invocation of Gemini model '{model_name}' for '{pdf_file}'..."
                    )
                    prompt_to_send = PromptsForGemini.get_prompt_to_elaborate_single_pdf(
                        lang=lang,
                        subject_matter=subject_matter  # Add this parameter
                    )
                    contents_to_send = [original_pdf_part, prompt_to_send]
                else:
                    logger.info(
                        f"Attempt {num_retries}/{MAX_RETRIES}: Requesting LaTeX correction for '{pdf_file}'..."
                    )
                    correction_prompt: str = (
                        PromptsForGemini.get_prompt_for_error_correction(
                            lang=lang, error_message=last_error_message
                        )
                    )

                    contents_to_send = [
                        original_pdf_part,
                        generated_text,  # Send previous generated text for context
                        correction_prompt,
                    ]

                gemini_response = client.generate_content_with_rate_limit(
                    model=model_name,
                    contents=contents_to_send,
                )

                if gemini_response.text is None:
                    logger.error("Gemini didn't respond with any text")
                    continue

                generated_text = gemini_response.text
                generated_text = fix_common_generated_latex_erros(generated_text)

                if not generated_text.strip().startswith("\\documentclass"):
                    print(
                        f"{Colors.WARNING}Warning: AI output did not start with \\documentclass. This will likely cause an error.{Colors.ENDC}"
                    )
                    last_error_message = "Output does not start with \\documentclass. The LaTeX format was not respected."
                    num_retries += 1
                    time.sleep(1)
                    continue

                is_valid: bool
                error_msg: str
                is_valid, error_msg = PDFProcessor.validate_and_compile_latex_to_pdf(
                    generated_text, result_folder_path, output_file_name_base
                )

                if is_valid:
                    latex_is_valid = True
                    print(
                        f"{Colors.OKGREEN}Generated LaTeX code for '{pdf_file}' is valid and PDF was created.{Colors.ENDC}"
                    )
                else:
                    if error_msg == "xelatex_not_found":
                        logger.warning(
                            "Cannot validate LaTeX: xelatex not found. Saving generated file but no PDF conversion."
                        )
                        exit()
                    else:
                        last_error_message = error_msg
                        num_retries += 1
                        print(
                            f"{Colors.FAIL}Generated LaTeX code for '{pdf_file}' is NOT valid. Attempting correction ({num_retries}/{MAX_RETRIES})...{Colors.ENDC}"
                        )
                        time.sleep(2)
            except Exception as e:
                logger.error(
                    f"Error processing '{pdf_file}' with Gemini: {e}"
                )
                last_error_message = f"Generic error during generation/compilation: {e}"
                num_retries += 1
                time.sleep(2)

        with open(output_tex_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(generated_text)
        print(
            f"{Colors.HEADER}Final output (after {num_retries} attempts) saved to: {output_tex_file_path}{Colors.ENDC}"
        )

    print(
        f"\n--- {Colors.OKBLUE}PDF processing with Gemini SDK completed.{Colors.ENDC} ---"
    )