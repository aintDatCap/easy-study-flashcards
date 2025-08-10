import locale
from enum import Enum
from typing import Dict, Optional


class Language(Enum):
    """Supported languages for the application."""

    EN = "en"
    IT = "it"


class LocalizedStrings:
    """Contains all localized strings used in the application."""

    strings: Dict[Language, Dict[str, str]] = {
        Language.EN: {
            # PDF Processing Messages
            "pdf_processing_start": "Starting PDF processing with Gemini SDK in '{folder}'",
            "pdf_files_found": "Found {count} PDF files in folder '{folder}'",
            "no_pdf_files": "No PDF files found in folder: {folder}",
            "folder_not_exist": "The specified folder does not exist: {folder}",
            "processing_complete": "PDF processing with Gemini SDK completed.",
            # LaTeX Messages
            "latex_compilation_attempt": "Attempting LaTeX compilation and PDF conversion for '{filename}'...",
            "latex_compilation_success": "LaTeX compilation of '{filename}' and PDF creation successful.",
            "latex_compilation_error": "LaTeX compilation ERROR for '{filename}'.",
            "latex_not_found": "Error: xelatex not found. Please ensure a LaTeX environment (e.g., TeX Live, MiKTeX) is installed and in PATH.",
            # Chapter Analysis Messages
            "chapter_analysis_start": "Starting chapter and physical page analysis for '{filename}'",
            "chapter_info_success": "Chapter information successfully extracted from '{model}'.",
            "chapter_info_error": "Error getting chapters from '{model}': {error}",
            # MiKTeX Installation Messages
            "miktex_download": "Downloading MiKTeX setup...",
            "miktex_extract": "Extracting MiKTeX setup...",
            "miktex_install": "Installing MiKTeX...",
            "miktex_success": "MiKTeX installation completed successfully",
            # API Messages
            "rate_limit": "Request limit reached. Waiting for {seconds:.2f} seconds...",
            "api_key_missing": "Error: The 'GEMINI_API_KEY' environment variable is not set. Please set it before running the script.",
            # Input Messages
            "subject_prompt": "What subject do you want to generate study cards for? (e.g., 'Linear Algebra', 'Roman History', 'Quantum Physics'): ",
            "no_subject": "No subject specified. Using 'generic subject'.",
            "generic_subject": "Generic subject",
            # Error Messages
            "pdf_invalid_page_indices": "Error: Invalid page indices for extraction. Start: {start}, End: {end}, Total pages: {total}",
            "pdf_unexpected_error": "Unexpected error during compilation of '{filename}': {error}",
            "latex_compilation_error_details": "Error details:\n{message}",
            # Additional Messages
            "splitting_pdf": "Splitting '{filename}' into chapters...",
            "chapter_page_out_of_bounds": "Warning: Start page for '{title}' (corresponds to physical page {page}) out of bounds. Skipping.",
            "chapter_saved": "Saved: '{filepath}' (Physical Pages: {start}-{end})",
            "no_pages_in_chapter": "No pages found for chapter '{title}'.",
            "no_chapters": "No chapters found to process.",
            "chapter_start_index": "The first chapter starts at the index {index} of the PDF file",
            "miktex_install_failed": "Couldn't install MikTex, aborting...",
            "miktex_download_error": "Failed to download MiKTeX setup: {error}",
            "miktex_install_error": "Unexpected error during MiKTeX installation: {error}",
        },
        Language.IT: {
            # PDF Processing Messages
            "pdf_processing_start": "Avvio elaborazione PDF con Gemini SDK in '{folder}'",
            "pdf_files_found": "Trovati {count} file PDF nella cartella '{folder}'",
            "no_pdf_files": "Nessun file PDF trovato nella cartella: {folder}",
            "folder_not_exist": "La cartella specificata non esiste: {folder}",
            "processing_complete": "Elaborazione PDF con Gemini SDK completata.",

            "pdf_no_page_extracted_warning": "Nessuna pagina estratta tra gli indici {start_page_index} e {end_page_index}.",
            "pdf_pages_extraction_error": "Errore durante l'estrazione delle pagine PDF:{error}",
            # LaTeX Messages
            "latex_compilation_attempt": "Tentativo di compilazione LaTeX e conversione PDF per '{filename}'...",
            "latex_compilation_success": "Compilazione LaTeX di '{filename}' e creazione PDF riuscita.",
            "latex_compilation_error": "ERRORE di compilazione LaTeX per '{filename}'.",
            "latex_not_found": "Errore: xelatex non trovato. Assicurati che un ambiente LaTeX (es. TeX Live, MiKTeX) sia installato e nel PATH.",
            # Chapter Analysis Messages
            "chapter_analysis_start": "Avvio analisi capitoli e pagina fisica per '{filename}'",
            "chapter_info_success": "Informazioni sui capitoli estratte con successo da '{model}'.",
            "chapter_info_error": "Errore nell'ottenere i capitoli da '{model}': {error}",
            # MiKTeX Installation Messages
            "miktex_download": "Download del setup MiKTeX in corso...",
            "miktex_extract": "Estrazione del setup MiKTeX...",
            "miktex_install": "Installazione MiKTeX in corso...",
            "miktex_success": "Installazione MiKTeX completata con successo",
            # API Messages
            "rate_limit": "Limite di richieste raggiunto. Attesa di {seconds:.2f} secondi...",
            "api_key_missing": "Errore: La variabile d'ambiente 'GEMINI_API_KEY' non è impostata. Si prega di impostarla prima di eseguire lo script.",
            # Input Messages
            "subject_prompt": "Per quale materia vuoi generare le schede di studio? (es. 'Algebra Lineare', 'Storia Romana', 'Fisica Quantistica'): ",
            "no_subject": "Nessuna materia specificata. Utilizzo 'materia generica'.",
            "generic_subject": "Materia generica",
            # Error Messages
            "pdf_invalid_page_indices": "Errore: Indici di pagina non validi per l'estrazione. Inizio: {start}, Fine: {end}, Totale pagine: {total}",
            "pdf_unexpected_error": "Si è verificato un errore inatteso durante la compilazione di '{filename}': {error}",
            "latex_compilation_error_details": "Dettagli errore:\n{message}",
            # Additional Messages
            "splitting_pdf": "Divisione di '{filename}' in capitoli...",
            "chapter_page_out_of_bounds": "Attenzione: Pagina iniziale per '{title}' (corrisponde alla pagina fisica {page}) fuori dai limiti. Saltando.",
            "chapter_saved": "Salvato: '{filepath}' (Pagine Fisiche: {start}-{end})",
            "no_pages_in_chapter": "Nessuna pagina trovata per il capitolo '{title}'.",
            "no_chapters": "Nessun capitolo trovato da elaborare.",
            "chapter_start_index": "Il primo capitolo inizia all'indice {index} del file PDF",
            "miktex_install_failed": "Impossibile installare MikTex, annullamento in corso...",
            "miktex_download_error": "Errore durante il download del setup MiKTeX: {error}",
            "miktex_install_error": "Errore inatteso durante l'installazione di MiKTeX: {error}",
        },
    }


class Localizer:
    """Handles localization of strings based on system locale."""

    _instance: Optional["Localizer"] = None
    _current_language: Language

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Localizer, cls).__new__(cls)
            # Get system locale and set default language
            system_locale, _ = locale.getdefaultlocale()
            if system_locale is None:
                system_locale = "en_EN"

            lang = system_locale.split("_")[0]
            cls._current_language = Language(lang)

        return cls._instance

    @classmethod
    def get_string(cls, key: str, **kwargs) -> str:
        """
        Gets a localized string by key and formats it with the provided arguments.
        """
        try:
            localized = LocalizedStrings.strings[cls._current_language][key]
            return localized.format(**kwargs) if kwargs else localized
        except KeyError:
            # Fallback to English if key not found in current language
            try:
                localized = LocalizedStrings.strings[Language.EN][key]
                return localized.format(**kwargs) if kwargs else localized
            except KeyError:
                return f"Missing localization for key: {key}"

    @classmethod
    def set_language(cls, language: Language) -> None:
        """
        Manually sets the current language.
        """
        cls._current_language = language

    @classmethod
    def get_current_language(cls) -> Language:
        """
        Returns the currently set language.
        """
        return cls._current_language


# Create a global instance
localizer = Localizer()
