import json
import os
import pathlib
import time
from typing import List, Optional

from loguru import logger
from openai import APIError, OpenAI
from pypdf import PdfReader
from stockholm import Money

from easy_study_flashcards.deepseek.models import (
    BookStructure,
    ChapterInfo,
    ChaptersOnly,
)
from easy_study_flashcards.deepseek.prompts import PromptsForDeepSeek
from easy_study_flashcards.pdf_processing.core import PDFProcessor
from easy_study_flashcards.utils.colors import Colors
from easy_study_flashcards.utils.latex import fix_common_generated_latex_erros
from easy_study_flashcards.utils.localization import localizer as _


class DeepSeekClientManager:
    """
    A class that manages the DeepSeek API client and enforces rate limits.
    Uses the OpenAI-compatible API at api.deepseek.com.
    """

    request_timestamps: list[float]
    total_cost: Money = Money(0)
    __MAX_REQUESTS_PER_MINUTE: int = 10
    __TIME_WINDOW_SECONDS: int = 60

    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        self.request_timestamps = []

    def _wait_for_rate_limit(self):
        current_time: float = time.time()
        self.request_timestamps = [
            ts
            for ts in self.request_timestamps
            if current_time - ts < self.__TIME_WINDOW_SECONDS
        ]

        if len(self.request_timestamps) >= self.__MAX_REQUESTS_PER_MINUTE:
            time_to_wait: float = (
                self.request_timestamps[0] + self.__TIME_WINDOW_SECONDS - current_time
            )
            if time_to_wait > 0:
                logger.warning(_.get_string("rate_limit", seconds=time_to_wait))
                time.sleep(time_to_wait)
                current_time = time.time()
                self.request_timestamps = [
                    ts
                    for ts in self.request_timestamps
                    if current_time - ts < self.__TIME_WINDOW_SECONDS
                ]

    def _count_tokens_estimate(self, text: str) -> int:
        """Rough estimate of token count (4 chars per token on average)."""
        return len(text) // 4

    def chat_completion_with_rate_limit(
        self, model: str, messages: list[dict], **kwargs
    ) -> str:
        self._wait_for_rate_limit()

        input_text = " ".join(m.get("content", "") or "" for m in messages)
        input_tokens = self._count_tokens_estimate(input_text)

        while True:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **kwargs,
                )
                break
            except APIError as e:
                if e.status_code == 503:
                    logger.warning(
                        "DeepSeek server is temporarily unavailable, waiting 10 seconds"
                    )
                    time.sleep(10)
                else:
                    raise

        result_text: str = response.choices[0].message.content or ""
        output_tokens = self._count_tokens_estimate(result_text)
        self.print_generated_content_cost(input_tokens, output_tokens, model)
        self.request_timestamps.append(time.time())
        return result_text

    def print_generated_content_cost(self, input_tokens, output_tokens, model_name):
        pricing = {
            "deepseek-v4-flash": {
                "input": 0.15,
                "output": 0.60,
            },
            "deepseek-v4-pro": {
                "input": 0.30,
                "output": 1.10,
            },
        }

        if model_name not in pricing:
            logger.warning(f"Pricing data not available for model '{model_name}'.")
            return

        input_price = pricing[model_name]["input"]
        output_price = pricing[model_name]["output"]

        content_cost = (Money(input_tokens) / 1_000_000) * input_price + (
            Money(output_tokens) / 1_000_000
        ) * output_price

        self.total_cost += content_cost

        print(
            f"{Colors.BOLD}Estimated cost: ${content_cost.amount_as_string()}. "
            f"Input tokens (est.): {input_tokens}, "
            f"Output tokens (est.): {output_tokens} {Colors.ENDC}"
        )


def _extract_pages_as_text(pdf_path: pathlib.Path, num_pages: int) -> Optional[str]:
    """Extracts text from the first `num_pages` pages of a PDF."""
    try:
        reader: PdfReader = PdfReader(pdf_path)
        total_pages: int = len(reader.pages)
        pages_to_extract: int = min(num_pages, total_pages)

        text_parts: list[str] = []
        for i in range(pages_to_extract):
            page = reader.pages[i]
            page_text: str = page.extract_text() or ""
            text_parts.append(f"--- Page {i + 1} ---\n{page_text}")

        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting text from PDF '{pdf_path.name}': {e}")
        return None


def get_book_structure_from_deepseek(
    pdf_path: pathlib.Path,
    model_name_chapters: str,
    model_name_physical_page: str,
    client: DeepSeekClientManager,
    lang: str,
    pages_to_process_chapters: int = 30,
    pages_to_process_physical_page: int = 40,
) -> Optional[BookStructure]:
    assert pages_to_process_chapters > 0
    assert pages_to_process_physical_page > 0

    print(
        f"\n--- {Colors.OKBLUE}{_.get_string('chapter_analysis_start', filename=pdf_path.name)}{Colors.ENDC} ---"
    )

    reader: PdfReader = PdfReader(pdf_path)
    total_pdf_pages: int = len(reader.pages)

    if total_pdf_pages == 0:
        logger.warning(f"PDF file '{pdf_path.name}' contains no pages.")
        return None

    chapters_info: Optional[List[ChapterInfo]] = None
    first_chapter_physical_page: Optional[int] = None

    num_pages_to_extract_chapters: int = min(pages_to_process_chapters, total_pdf_pages)
    text_chapters: Optional[str] = _extract_pages_as_text(
        pdf_path, num_pages_to_extract_chapters
    )
    if not text_chapters:
        return None

    num_pages_to_extract_physical_page: int = min(
        pages_to_process_physical_page, total_pdf_pages
    )
    text_physical_page: Optional[str] = _extract_pages_as_text(
        pdf_path, num_pages_to_extract_physical_page
    )
    if not text_physical_page:
        return None

    # --- PHASE 1: Extract chapters ---
    prompt_chapters: str = PromptsForDeepSeek.get_prompt_chapters_pages(
        lang=lang, pages_to_scan=num_pages_to_extract_chapters
    )
    print(
        f"{Colors.OKCYAN}Sending first {num_pages_to_extract_chapters} pages (as text) to "
        f"'{model_name_chapters}' for chapter extraction...{Colors.ENDC}"
    )
    try:
        chapters_json: str = client.chat_completion_with_rate_limit(
            model=model_name_chapters,
            messages=[
                {
                    "role": "user",
                    "content": f"Here is the extracted text from the first {num_pages_to_extract_chapters} pages of a textbook PDF:\n\n{text_chapters}\n\n{prompt_chapters}",
                },
            ],
            response_format={"type": "json_object"},
        )
        parsed: dict = json.loads(chapters_json)
        chapters_only: ChaptersOnly = ChaptersOnly(**parsed)
        chapters_info = chapters_only.chapters
        print(
            f"{Colors.OKGREEN}Chapter information successfully extracted from '{model_name_chapters}'.{Colors.ENDC}"
        )
    except Exception as e:
        logger.error(f"Error getting chapters from '{model_name_chapters}': {e}")
        return None

    # --- PHASE 2: Extract physical page of the first chapter ---
    prompt_physical_page: str = (
        PromptsForDeepSeek.get_prompt_first_chapter_physical_page(
            lang=lang, pages_to_scan=num_pages_to_extract_physical_page
        )
    )
    print(
        f"{Colors.OKCYAN}Sending first {num_pages_to_extract_physical_page} pages (as text) to "
        f"'{model_name_physical_page}' for first chapter physical page extraction...{Colors.ENDC}"
    )
    try:
        physical_page_text: str = client.chat_completion_with_rate_limit(
            model=model_name_physical_page,
            messages=[
                {
                    "role": "user",
                    "content": f"Here is the extracted text from the first {num_pages_to_extract_physical_page} pages of a textbook PDF:\n\n{text_physical_page}\n\n{prompt_physical_page}",
                },
            ],
        )
        first_chapter_physical_page = int(physical_page_text.strip())
        print(
            f"{Colors.OKGREEN}First chapter physical page successfully extracted from '{model_name_physical_page}'.{Colors.ENDC}"
        )
    except ValueError:
        print(
            f"{Colors.FAIL}Error: DeepSeek response for physical page is not a valid integer: '{physical_page_text.strip() if 'physical_page_text' in dir() else ''}'{Colors.ENDC}"
        )
        return None
    except Exception as e:
        print(
            f"{Colors.FAIL}Error getting the first chapter's physical page from '{model_name_physical_page}': {e}{Colors.ENDC}"
        )
        return None

    if chapters_info is not None and first_chapter_physical_page is not None:
        return BookStructure(
            chapters=chapters_info,
            first_chapter_physical_page=first_chapter_physical_page,
        )
    return None


def process_pdfs_with_deepseek(
    folder_path: str,
    model_name: str,
    client: DeepSeekClientManager,
    lang: str,
    subject_matter: str,
) -> None:
    if not os.path.isdir(folder_path):
        logger.error(_.get_string("folder_not_exist", folder=folder_path))
        return

    result_folder_path: str = os.path.join(folder_path, "results/")
    if not os.path.exists(result_folder_path):
        os.mkdir(result_folder_path)

    pdf_files: List[str] = [
        f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        logger.warning(_.get_string("no_pdf_files", folder=folder_path))
        return

    logger.info(_.get_string("pdf_processing_start", folder=folder_path))
    logger.info(
        _.get_string("pdf_files_found", count=len(pdf_files), folder=folder_path)
    )

    MAX_RETRIES: int = 3

    for pdf_file in pdf_files:
        pdf_path: pathlib.Path = pathlib.Path(os.path.join(folder_path, pdf_file))
        output_file_name_base: str = os.path.splitext(pdf_file)[0] + "-domande"
        output_tex_file_path: str = os.path.join(
            result_folder_path, output_file_name_base + ".tex"
        )

        # Extract text from the PDF for sending to DeepSeek
        try:
            pdf_text: Optional[str] = _extract_pages_as_text(
                pdf_path, 9999
            )  # large number = all pages
            if not pdf_text:
                logger.warning(
                    f"Could not extract text from PDF '{pdf_file}'. Skipping."
                )
                continue
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
                if num_retries == 0:
                    logger.info(
                        f"Initial invocation of DeepSeek model '{model_name}' for '{pdf_file}'..."
                    )
                    prompt_to_send: str = (
                        PromptsForDeepSeek.get_prompt_to_elaborate_single_pdf(
                            lang=lang,
                            subject_matter=subject_matter,
                        )
                    )
                    messages: list[dict] = [
                        {
                            "role": "user",
                            "content": f"Here is the extracted text from a PDF document:\n\n{pdf_text}\n\n{prompt_to_send}",
                        },
                    ]
                else:
                    logger.info(
                        f"Attempt {num_retries}/{MAX_RETRIES}: Requesting LaTeX correction for '{pdf_file}'..."
                    )
                    correction_prompt: str = (
                        PromptsForDeepSeek.get_prompt_for_error_correction(
                            lang=lang, error_message=last_error_message
                        )
                    )
                    messages = [
                        {
                            "role": "user",
                            "content": f"Here is the extracted text from a PDF document:\n\n{pdf_text}",
                        },
                        {
                            "role": "assistant",
                            "content": generated_text,
                        },
                        {
                            "role": "user",
                            "content": correction_prompt,
                        },
                    ]

                response_text: str = client.chat_completion_with_rate_limit(
                    model=model_name,
                    messages=messages,
                )

                generated_text = response_text
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
                logger.error(f"Error processing '{pdf_file}' with DeepSeek: {e}")
                last_error_message = f"Generic error during generation/compilation: {e}"
                num_retries += 1
                time.sleep(2)

        with open(output_tex_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(generated_text)
        print(
            f"{Colors.HEADER}Final output (after {num_retries} attempts) saved to: {output_tex_file_path}{Colors.ENDC}"
        )

    print(
        f"\n--- {Colors.OKBLUE}PDF processing with DeepSeek SDK completed.{Colors.ENDC} ---"
    )
