import io
import os
import pathlib
import subprocess
from typing import List, Optional, Tuple

from pypdf import PdfReader, PdfWriter
from loguru import logger

from easy_study_flashcards.utils.latex import get_xelatex_path
from easy_study_flashcards.utils.colors import Colors
from easy_study_flashcards.utils.localization import localizer as _


class PDFProcessor:
    @staticmethod
    def extract_pdf_pages_to_bytes(
        pdf_path: pathlib.Path, start_page_index: int, end_page_index: int
    ) -> Optional[io.BytesIO]:
        """
        Extracts a range of pages from a PDF and returns them as BytesIO.
        Pages are 0-indexed for input (start_page_index, end_page_index).
        """
        try:
            reader: PdfReader = PdfReader(pdf_path)
            total_pdf_pages: int = len(reader.pages)

            if (
                start_page_index < 0
                or end_page_index < start_page_index
                or start_page_index >= total_pdf_pages
            ):
                logger.error(
                    _.get_string(
                        "pdf_invalid_page_indices",
                        start=start_page_index,
                        end=end_page_index,
                        total=total_pdf_pages
                    )
                )
                return None

            writer: PdfWriter = PdfWriter()
            for i in range(start_page_index, min(end_page_index, total_pdf_pages)):
                writer.add_page(reader.pages[i])

            if len(writer.pages) == 0:
                logger.error(
                    _.get_string(
                        "pdf_no_page_extracted_warning",
                        start_page_index=start_page_index,
                        end_page_index=end_page_index
                    )
                )
                return None

            buffer: io.BytesIO = io.BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            return buffer
        except Exception as e:
            logger.error(
                _.get_string("pdf_pages_extraction_error", error=str(e))
            )
            return None

    @staticmethod
    def validate_and_compile_latex_to_pdf(
        latex_content: str, output_directory: str, output_file_name_base: str
    ) -> Tuple[bool, str]:
        """
        Saves the LaTeX content to a temporary file and attempts to compile it with xelatex.
        If successful, it converts to PDF and returns (True, "").
        If compilation fails, it returns (False, error_message).
        """
        temp_file_name: str = output_file_name_base + ".tex"
        temp_file_path: str = os.path.join(output_directory, temp_file_name)
        temp_log_file: str = os.path.join(
            output_directory, output_file_name_base + ".log"
        )

        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        logger.info(
            _.get_string('latex_compilation_attempt', filename=temp_file_name)
        )

        xelatex_exe = get_xelatex_path()

        # Command for xelatex to compile and generate PDF
        compile_command: List[str] = [
            xelatex_exe,
            "-interaction=nonstopmode",
            "-c-style-errors",
            "-output-directory",
            output_directory,
            temp_file_path,
        ]

        error_message: str = ""
        try:
            result: subprocess.CompletedProcess = subprocess.run(
                compile_command,
                check=False,
                capture_output=True,
                text=True,
                errors="ignore",
            )

            if result.returncode != 0:
                logger.error(
                    _.get_string('latex_compilation_error', filename=temp_file_name)
                )
                if os.path.exists(temp_log_file):
                    with open(
                        temp_log_file, "r", encoding="utf-8", errors="ignore"
                    ) as log_f:
                        log_content: str = log_f.read()
                        error_lines: List[str] = [
                            line
                            for line in log_content.splitlines()
                            if line.startswith("!")
                            or "fatal error" in line.lower()
                            or "undefined control sequence" in line.lower()
                            or "missing" in line.lower()
                            or "runaway argument" in line.lower()
                        ]
                        if error_lines:
                            error_message = "\n".join(error_lines[:10])
                        else:
                            error_message = result.stderr + "\n" + result.stdout
                if not error_message:
                    error_message = result.stderr + "\n" + result.stdout

                logger.error(
                    _.get_string('latex_compilation_error_details', message=error_message)
                )
                return False, error_message
            else:
                logger.success(
                    _.get_string('latex_compilation_success', filename=temp_file_name)
                )
                return True, ""
        except FileNotFoundError:
            logger.error(_.get_string('latex_not_found'))
            return False, "xelatex_not_found"
        except Exception as e:
            logger.error(
                _.get_string('pdf_unexpected_error', filename=temp_file_name, error=str(e))
            )
            return False, f"Unexpected error: {e}"
        finally:
            # Clean up temporary files except the final PDF and tex file
            for ext in [".aux", ".log", ".out", ".fls", ".fdb_latexmk"]:
                temp_path_to_clean: str = os.path.join(
                    output_directory, output_file_name_base + ext
                )
                if os.path.exists(temp_path_to_clean):
                    os.remove(temp_path_to_clean)
