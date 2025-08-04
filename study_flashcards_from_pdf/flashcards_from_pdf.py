import os
import pathlib
import time
from google import genai
from google.genai import types
from pypdf import PdfReader, PdfWriter
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from .colors import Colors
from .pdf_processor import PDFProcessor
from .prompts import PromptsForGemini


# Definisci lo schema Pydantic per l'informazione del capitolo
class ChapterInfo(BaseModel):
    """Informazioni su un singolo capitolo di un libro, inclusi il titolo e la pagina di inizio."""

    title: str = Field(description="Il titolo del capitolo.")
    # start_page ora è la pagina logica (come numerata nel libro)
    start_page: int = Field(description="Il numero di pagina (basato su 1, come numerata nel libro) dove inizia il capitolo.")


# Lo schema per il primo modello (Gemini 1.5) che estrarrà solo i capitoli
class ChaptersOnly(BaseModel):
    """Schema per estrarre solo la lista dei capitoli."""
    chapters: List[ChapterInfo] = Field(description="Una lista di informazioni sui capitoli principali.")


# Lo schema BookStructure ora contiene la lista dei capitoli e l'offset del primo capitolo.
class BookStructure(BaseModel):
    """Informazioni sulla struttura del libro, inclusi i capitoli e la pagina fisica del primo capitolo."""

    chapters: List[ChapterInfo] = Field(description="Una lista di informazioni sui capitoli principali.")
    first_chapter_physical_page: int = Field(description="La posizione fisica nel PDF (pagina basata su 1) del primo capitolo numerato del libro.")


def fix_common_generated_latex_erros(latex_text:str) -> str:
    """
    Dato del testo latex generato da AI, questa funzione risolve alcuni errori comuni presenti nel testo.
    """
    latex_text = latex_text.replace(r"\begin{enumerate>", r"\begin{enumerate}")
    latex_text = latex_text.replace(r"\end{enumerate>", r"\end{enumerate}")

    if latex_text.startswith("```latex\n"):
        latex_text = latex_text.replace("```latex\n", "", 1)
    if latex_text.endswith("```"):
        latex_text = latex_text.replace("```", "")

    return latex_text


def get_chapters_from_ai(
    pdf_path: pathlib.Path,
    model_name_chapters: str,  # Modello per i capitoli (es. Gemini 1.5)
    model_name_physical_page: str,  # Modello per la pagina fisica (es. Gemini 2.5)
    client: genai.Client,
    lang:str,
    pages_to_process_chapters: int = 10, # Ridotto a 10
    pages_to_process_physical_page: int = 25, # Invariato
) -> Optional[BookStructure]:
    """
    Chiede ai modelli Gemini di identificare i capitoli e la pagina fisica del primo capitolo,
    elaborando solo un sottoinsieme di pagine iniziali del PDF.
    Restituisce un oggetto BookStructure.
    """

    # Prompt per identificare i capitoli (per Gemini 1.5)
    prompt_chapters: str = PromptsForGemini.get_prompt_chapters_pages(lang=lang, pages_to_scan=pages_to_process_chapters)

    # Prompt per identificare la pagina fisica del primo capitolo (per Gemini 2.5)
    prompt_physical_page: str = PromptsForGemini.get_prompt_first_chapter_physical_page(lang=lang, pages_to_scan=pages_to_process_physical_page)


    print(f"\n--- {Colors.OKBLUE}Inizio analisi capitoli e pagina fisica per '{pdf_path.name}'{Colors.ENDC} ---")
    
    reader: PdfReader = PdfReader(pdf_path)
    total_pdf_pages: int = len(reader.pages)

    if total_pdf_pages == 0:
        print(f"{Colors.WARNING}Avviso: Il PDF '{pdf_path.name}' non contiene pagine.{Colors.ENDC}")
        return None

    requests_timestamps: List[float] = []
    MAX_REQUESTS_PER_MINUTE: int = 10
    TIME_WINDOW_SECONDS: int = 60

    chapters_info: Optional[List[ChapterInfo]] = None
    first_chapter_physical_page: Optional[int] = None

    # --- Prepara le parti del PDF per i due modelli usando la nuova funzione ---
    
    # Per il modello dei capitoli (meno pagine)
    num_pages_to_extract_chapters: int = min(pages_to_process_chapters, total_pdf_pages)
    sub_pdf_bytes_chapters = PDFProcessor.extract_pdf_pages_to_bytes(pdf_path, 0, num_pages_to_extract_chapters)
    if not sub_pdf_bytes_chapters:
        return None
    
    # Per il modello della pagina fisica (più pagine)
    num_pages_to_extract_physical_page: int = min(pages_to_process_physical_page, total_pdf_pages)
    sub_pdf_bytes_physical_page = PDFProcessor.extract_pdf_pages_to_bytes(pdf_path, 0, num_pages_to_extract_physical_page)
    if not sub_pdf_bytes_physical_page:
        return None


    # --- FASE 1: Estrazione dei capitoli con Gemini 1.5 (pages_to_process_chapters) ---
    print(f"{Colors.OKCYAN}Invio le prime {num_pages_to_extract_chapters} pagine a '{model_name_chapters}' per l'estrazione dei capitoli...{Colors.ENDC}")
    try:
        current_time: float = time.time()
        requests_timestamps = [ts for ts in requests_timestamps if current_time - ts < TIME_WINDOW_SECONDS]
        if len(requests_timestamps) >= MAX_REQUESTS_PER_MINUTE:
            time_to_wait: float = requests_timestamps[0] + TIME_WINDOW_SECONDS - current_time
            if time_to_wait > 0:
                print(f"{Colors.WARNING}Limite di richieste raggiunto. Attesa di {time_to_wait:.2f} secondi...{Colors.ENDC}")
                time.sleep(time_to_wait)
        
        gemini_response_chapters:types.GenerateContentResponse = client.models.generate_content(
            model=model_name_chapters,
            contents=[
                types.Part.from_bytes(
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
        chapters_only: ChaptersOnly = gemini_response_chapters.parsed  # type: ignore
        chapters_info = chapters_only.chapters
        requests_timestamps.append(time.time())
        print(f"{Colors.OKGREEN}Informazioni sui capitoli estratte con successo da '{model_name_chapters}'.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}Errore durante l'ottenimento dei capitoli da '{model_name_chapters}': {e}{Colors.ENDC}")
        if hasattr(gemini_response_chapters, "text"): # type: ignore
            print(f"{Colors.FAIL}Risposta raw da Gemini (in caso di errore): {gemini_response_chapters.text}{Colors.ENDC}") # type: ignore
        return None

    # --- FASE 2: Estrazione della pagina fisica del primo capitolo con Gemini 2.5 (pages_to_process_physical_page) ---
    print(f"{Colors.OKCYAN}Invio le prime {num_pages_to_extract_physical_page} pagine a '{model_name_physical_page}' per l'estrazione della pagina fisica del primo capitolo...{Colors.ENDC}")
    try:
        current_time: float = time.time()
        requests_timestamps = [ts for ts in requests_timestamps if current_time - ts < TIME_WINDOW_SECONDS]
        if len(requests_timestamps) >= MAX_REQUESTS_PER_MINUTE:
            time_to_wait: float = requests_timestamps[0] + TIME_WINDOW_SECONDS - current_time
            if time_to_wait > 0:
                print(f"{Colors.WARNING}Limite di richieste raggiunto. Attesa di {time_to_wait:.2f} secondi...{Colors.ENDC}")
                time.sleep(time_to_wait)

        gemini_response_physical_page: types.GenerateContentResponse = client.models.generate_content(
            model=model_name_physical_page,
            contents=[
                types.Part.from_bytes(
                    data=sub_pdf_bytes_physical_page.getvalue(),
                    mime_type="application/pdf",
                ),
                prompt_physical_page,
            ],
            config={
                "response_mime_type": "text/plain", # Ci aspettiamo solo un numero intero come testo
            },
        )
        if gemini_response_physical_page.text is None:
            return None
        
        # Prova a convertire la risposta in un intero
        try:
            first_chapter_physical_page = int(gemini_response_physical_page.text.strip())
        except ValueError:
            print(f"{Colors.FAIL}Errore: La risposta di Gemini 2.5 per la pagina fisica non è un numero intero valido: '{gemini_response_physical_page.text.strip()}'{Colors.ENDC}")
            return None
        
        requests_timestamps.append(time.time())
        print(f"{Colors.OKGREEN}Pagina fisica del primo capitolo estratta con successo da '{model_name_physical_page}'.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}Errore durante l'ottenimento della pagina fisica del primo capitolo da '{model_name_physical_page}': {e}{Colors.ENDC}")
        if hasattr(gemini_response_physical_page, "text"): # type: ignore
            print(f"{Colors.FAIL}Risposta raw da Gemini (in caso di errore): {gemini_response_physical_page.text}{Colors.ENDC}") # type: ignore
        return None

    if chapters_info is not None and first_chapter_physical_page is not None:
        return BookStructure(chapters=chapters_info, first_chapter_physical_page=first_chapter_physical_page)



def split_pdf_by_chapters(
    pdf_path: pathlib.Path,
    chapters: List[ChapterInfo],
    first_numbered_page_in_doc: int,
    output_folder: str,
) -> None:
    """
    Divide un file PDF in più file, uno per ogni capitolo, basandosi
    sui numeri di pagina logici e l'offset della prima pagina numerata fornito dall'utente.
    """
    if not chapters:
        print(f"{Colors.WARNING}Nessuna informazione sui capitoli disponibile per la divisione del PDF.{Colors.ENDC}")
        return

    reader: PdfReader = PdfReader(pdf_path)
    total_pages: int = len(reader.pages)

    # Calcola l'offset: la pagina fisica (0-indexed) che corrisponde alla pagina logica '1' del libro.
    # Questo valore è fornito dall'utente.
    offset_physical_page_index: int = first_numbered_page_in_doc - 1

    # Ordina i capitoli per numero di pagina logico per assicurarsi che siano in ordine
    sorted_chapters: List[ChapterInfo] = sorted(chapters, key=lambda chap: chap.start_page)

    # Crea la cartella di output se non esiste
    os.makedirs(output_folder, exist_ok=True)

    print(f"\n--- {Colors.OKBLUE}Dividendo '{pdf_path.name}' in capitoli...{Colors.ENDC} ---")

    for i, chapter_info in enumerate(sorted_chapters):
        writer: PdfWriter = PdfWriter()

        # Calcola la pagina di inizio fisica per il capitolo
        # Esempio: Se Chapter 1 è a pagina logica 5, e la pagina logica 1 è la fisica 10,
        # allora Chapter 1 è alla pagina fisica 10 + (5 - 1) = 14.
        start_physical_page_index: int = offset_physical_page_index + (chapter_info.start_page - 1)

        # Determina la pagina di fine fisica per il capitolo corrente
        if i + 1 < len(sorted_chapters):
            next_chapter_logical_page: int = sorted_chapters[i + 1].start_page
            end_physical_page_index: int = offset_physical_page_index + (next_chapter_logical_page - 1)
        else:
            end_physical_page_index = total_pages  # Ultima pagina del documento per l'ultimo capitolo

        if start_physical_page_index >= total_pages or start_physical_page_index < 0:
            print(f"{Colors.WARNING}Avviso: Pagina di inizio '{chapter_info.start_page}' per '{chapter_info.title}' (corrispondente alla pagina fisica {start_physical_page_index + 1}) fuori dai limiti. Ignorato.{Colors.ENDC}")
            continue

        if end_physical_page_index > total_pages:
            end_physical_page_index = total_pages  # Assicura che l'indice finale non superi il numero totale di pagine

        for page_num in range(start_physical_page_index, end_physical_page_index):
            if page_num < total_pages:  # Assicura che la pagina esista
                writer.add_page(reader.pages[page_num])
            else:
                break  # Non ci sono più pagine da aggiungere

        if len(writer.pages) > 0:
            # Pulisci il nome del capitolo per il nome del file
            safe_chapter_name: str = "".join([c if c.isalnum() or c in (" ", "-") else "_" for c in chapter_info.title]).strip()
            safe_chapter_name = safe_chapter_name.replace(" ", "_")
            output_filename: str = f"Capitolo_{i+1}-{safe_chapter_name}.pdf"
            output_filepath: str = os.path.join(output_folder, output_filename)

            with open(output_filepath, "wb") as output_pdf:
                writer.write(output_pdf)
            print(f"{Colors.OKGREEN}Salvataggio: '{output_filepath}' (Pagine fisiche: {start_physical_page_index + 1}-{end_physical_page_index}){Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}Nessuna pagina trovata per il capitolo '{chapter_info.title}'.{Colors.ENDC}")


def process_pdfs_with_gemini_sdk(folder_path: str, model_name: str, client: genai.Client, lang:str) -> None:
    """
    Processes PDF files with the Gemini SDK, including LaTeX validation and auto-correction,
    and then converts the validated LaTeX to PDF.
    """

    if not os.path.isdir(folder_path):
        print(f"{Colors.FAIL}La cartella specificata non esiste: {folder_path}{Colors.ENDC}")
        return

    result_folder_path: str = os.path.join(folder_path, "results/")
    if not os.path.exists(result_folder_path):
        os.mkdir(result_folder_path)

    pdf_files: List[str] = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"{Colors.WARNING}Nessun file PDF trovato nella cartella: {folder_path}{Colors.ENDC}")
        return

    print(f"\n--- {Colors.OKBLUE}Inizio elaborazione PDF con Gemini SDK in '{folder_path}'{Colors.ENDC} ---")
    print(f"{Colors.OKCYAN}Trovati {len(pdf_files)} file PDF nella cartella '{folder_path}'.{Colors.ENDC}")

    requests_timestamps: List[float] = []
    MAX_REQUESTS_PER_MINUTE: int = 10
    TIME_WINDOW_SECONDS: int = 60
    MAX_RETRIES: int = 3

    for pdf_file in pdf_files:
        pdf_path: pathlib.Path = pathlib.Path(os.path.join(folder_path, pdf_file))
        output_file_name_base: str = os.path.splitext(pdf_file)[0] + "-domande"
        output_tex_file_path: str = os.path.join(result_folder_path, output_file_name_base + ".tex")

        original_pdf_part: types.Part = types.Part.from_bytes(data=pdf_path.read_bytes(), mime_type="application/pdf")

        num_retries: int = 0
        latex_is_valid: bool = False
        generated_text: str = ""
        last_error_message: str = ""

        while num_retries <= MAX_RETRIES and not latex_is_valid:
            current_time: float = time.time()
            requests_timestamps = [ts for ts in requests_timestamps if current_time - ts < TIME_WINDOW_SECONDS]

            if len(requests_timestamps) >= MAX_REQUESTS_PER_MINUTE:
                time_to_wait: float = requests_timestamps[0] + TIME_WINDOW_SECONDS - current_time
                if time_to_wait > 0:
                    print(f"{Colors.WARNING}Limite di richieste raggiunto. Attesa di {time_to_wait:.2f} secondi...{Colors.ENDC}")
                    time.sleep(time_to_wait)
                current_time = time.time()
                requests_timestamps = [ts for ts in requests_timestamps if current_time - ts < TIME_WINDOW_SECONDS]

            try:
                prompt_to_send: str
                contents_to_send: List[types.Part | str]

                if num_retries == 0:
                    print(f"\n{Colors.OKCYAN}Invocazione iniziale del modello '{model_name}' di Gemini per '{pdf_file}'...{Colors.ENDC}")
                    prompt_to_send = PromptsForGemini.get_prompt_to_elaborate_single_pdf(lang=lang)
                    contents_to_send = [original_pdf_part, prompt_to_send]
                else:
                    print(f"\n{Colors.WARNING}Tentativo {num_retries}/{MAX_RETRIES}: Richiesta di correzione LaTeX per '{pdf_file}'...")
                    correction_prompt: str = PromptsForGemini.get_prompt_for_error_correction(lang=lang, error_message=last_error_message)
                    
                    prompt_to_send = correction_prompt
                    contents_to_send = [
                        original_pdf_part,
                        generated_text, 
                        prompt_to_send,
                    ]

                gemini_response = client.models.generate_content(
                    model=model_name,
                    contents=contents_to_send,
                )
                generated_text = gemini_response.text

                generated_text = fix_common_generated_latex_erros(generated_text)

                if not generated_text.strip().startswith("\\documentclass"):
                    print(f"{Colors.WARNING}Avviso: L'AI non ha iniziato l'output con \\documentclass. Questo causerà probabilmente un errore.{Colors.ENDC}")
                    last_error_message = "Output non inizia con \\documentclass. Il formato LaTeX non è stato rispettato."
                    num_retries += 1
                    time.sleep(1)
                    continue

                is_valid: bool
                error_msg: Optional[str]
                is_valid, error_msg = PDFProcessor.validate_and_compile_latex_to_pdf(generated_text, result_folder_path, output_file_name_base)

                if is_valid:
                    latex_is_valid = True
                    print(f"{Colors.OKGREEN}Il codice LaTeX generato per '{pdf_file}' è valido e il PDF è stato creato.{Colors.ENDC}")
                else:
                    if error_msg == "xelatex_not_found":
                        print(f"{Colors.WARNING}Impossibile convalidare il LaTeX: xelatex non trovato. Salvataggio del file generato ma nessuna conversione PDF.{Colors.ENDC}")
                        latex_is_valid = True  # Considera "valido" nel senso che non proveremo a correggerlo se xelatex manca
                    else:
                        last_error_message = error_msg
                        num_retries += 1
                        print(f"{Colors.FAIL}Il codice LaTeX generato per '{pdf_file}' NON è valido. Tentativo di correzione ({num_retries}/{MAX_RETRIES})...{Colors.ENDC}")
                        time.sleep(2)

            except Exception as e:
                print(f"{Colors.FAIL}Errore durante l'elaborazione di '{pdf_file}' con Gemini: {e}{Colors.ENDC}")
                last_error_message = f"Errore generico durante la generazione/compilazione: {e}"
                num_retries += 1
                time.sleep(2)

        with open(output_tex_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(generated_text)
        print(f"{Colors.HEADER}Output finale (dopo {num_retries} tentativi) salvato in: {output_tex_file_path}{Colors.ENDC}")

        requests_timestamps.append(time.time())

    print(f"\n--- {Colors.OKBLUE}Elaborazione PDF con Gemini SDK completata.{Colors.ENDC} ---")