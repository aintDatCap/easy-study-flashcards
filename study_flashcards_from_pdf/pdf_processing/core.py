import io
import os
import pathlib
import subprocess
from typing import List, Optional, Tuple

from pypdf import PdfReader, PdfWriter

from study_flashcards_from_pdf.utils.colors import Colors


class PDFProcessor:
    @staticmethod
    def extract_pdf_pages_to_bytes(
        pdf_path: pathlib.Path, start_page_index: int, end_page_index: int
    ) -> Optional[io.BytesIO]:
        """
        Estrae un intervallo di pagine da un PDF e le restituisce come BytesIO.
        Le pagine sono 0-indexed per l'input (start_page_index, end_page_index).
        """
        try:
            reader: PdfReader = PdfReader(pdf_path)
            total_pdf_pages: int = len(reader.pages)

            if (
                start_page_index < 0
                or end_page_index < start_page_index
                or start_page_index >= total_pdf_pages
            ):
                print(
                    f"{Colors.FAIL}Errore: Indici di pagina non validi per l'estrazione. Inizio: {start_page_index}, Fine: {end_page_index}, Totale pagine: {total_pdf_pages}{Colors.ENDC}"
                )
                return None

            writer: PdfWriter = PdfWriter()
            for i in range(start_page_index, min(end_page_index, total_pdf_pages)):
                writer.add_page(reader.pages[i])

            if len(writer.pages) == 0:
                print(
                    f"{Colors.WARNING}Nessuna pagina estratta tra gli indici {start_page_index} e {end_page_index}.{Colors.ENDC}"
                )
                return None

            buffer: io.BytesIO = io.BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            return buffer
        except Exception as e:
            print(
                f"{Colors.FAIL}Errore durante l'estrazione delle pagine PDF: {e}{Colors.ENDC}"
            )
            return None

    @staticmethod
    def validate_and_compile_latex_to_pdf(
        latex_content: str, output_directory: str, output_file_name_base: str
    ) -> Tuple[bool, str]:
        """
        Saves the LaTeX content to a temporary file and attempts to compile it with xelatex.
        If successful, it converts to PDF and returns (True, None).
        If compilation fails, it returns (False, error_message).
        """
        temp_file_name: str = output_file_name_base + ".tex"
        temp_file_path: str = os.path.join(output_directory, temp_file_name)
        temp_log_file: str = os.path.join(
            output_directory, output_file_name_base + ".log"
        )

        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        print(
            f"\n{Colors.OKCYAN}Tentativo di compilazione LaTeX e conversione PDF per '{temp_file_name}'...{Colors.ENDC}"
        )

        # Command for xelatex to compile and generate PDF
        compile_command: List[str] = [
            "xelatex",
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
                print(
                    f"{Colors.FAIL}ERRORE di compilazione LaTeX per '{temp_file_name}'.{Colors.ENDC}"
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
                            error_message = result.stderr + "\n" + result.stdout[-500:]
                if not error_message:
                    error_message = result.stderr + "\n" + result.stdout[-500:]
                print(f"{Colors.FAIL}Dettagli errore:\n{error_message}{Colors.ENDC}")
                return False, error_message
            else:
                print(
                    f"{Colors.OKGREEN}Compilazione LaTeX di '{temp_file_name}' e creazione PDF riuscita.{Colors.ENDC}"
                )
                return True, ""
        except FileNotFoundError:
            print(
                f"{Colors.FAIL}Errore: xelatex non trovato. Assicurati che un ambiente LaTeX (es. TeX Live, MiKTeX) sia installato e nel PATH.{Colors.ENDC}"
            )
            return (
                False,
                "xelatex_not_found",
            )
        except Exception as e:
            print(
                f"{Colors.FAIL}Si è verificato un errore inatteso durante la compilazione di '{temp_file_name}': {e}{Colors.ENDC}"
            )
            return False, f"Errore inatteso: {e}"
        finally:
            # Clean up temporary files except the final PDF and tex file
            for ext in [".aux", ".log", ".out", ".fls", ".fdb_latexmk"]:
                temp_path_to_clean: str = os.path.join(
                    output_directory, output_file_name_base + ext
                )
                if os.path.exists(temp_path_to_clean):
                    os.remove(temp_path_to_clean)
