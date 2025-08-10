class PromptsForGemini:

    @staticmethod
    def get_prompt_chapters_pages(lang: str, pages_to_scan: int) -> str:
        assert (
            lang in PromptsForGemini.prompts
        ), "Invalid language provided to PromptsForGemini.get_prompt_chapters_pages"
        assert pages_to_scan > 0, "pages_to_scan should be an integer bigger than 0"

        return PromptsForGemini.prompts[lang]["prompt_chapters_pages"].format(
            pages_to_scan=pages_to_scan
        )

    @staticmethod
    def get_prompt_first_chapter_physical_page(lang: str, pages_to_scan: int) -> str:
        assert (
            lang in PromptsForGemini.prompts
        ), "Invalid language provided to PromptsForGemini.get_prompt_first_chapter_physical_page"
        assert pages_to_scan > 0, "pages_to_scan should be an integer bigger than 0"

        return PromptsForGemini.prompts[lang][
            "prompt_first_chapter_physical_page"
        ].format(pages_to_scan=pages_to_scan)

    @staticmethod
    def get_prompt_to_elaborate_single_pdf(lang: str, subject_matter:str) -> str:
        """
        Gets the prompt template for elaborating a single PDF and formats it with the subject matter.
        """
        assert lang in PromptsForGemini.prompts, "Invalid language provided"
        return PromptsForGemini.prompts[lang]["prompt_elaborate_single_pdf"].replace("**[subject]**", subject_matter)

    @staticmethod
    def get_prompt_for_error_correction(lang: str, error_message: str) -> str:
        assert (
            lang in PromptsForGemini.prompts
        ), "Invalid language provided to PromptsForGemini.get_prompt_for_error_correction"

        return PromptsForGemini.prompts[lang]["prompt_error_correction"].replace("**[error_message]**", error_message)

    # Translated through AI, I'm way too lazy to do that by myself
    prompts: dict[str, dict[str, str]] = {
        "en": {
            "prompt_chapters_pages": """
                Analyze the attached PDF, which is a textbook. I have extracted only the first {pages_to_scan} pages of the original document.

                Your task is to identify and list *exclusively* the main chapters that begin with clear numbering,
                such as "Chapter 1", "Chapter 2", "Unit 3", "Section 4", or similar numbered formats.
                Do not include introductions, prefaces, indexes, bibliographies, appendices, solutions, or any other section
                that is not an explicitly numbered chapter. For each identified chapter, return its exact title as it appears in the text and the page number where it begins,
                as **numbered within the book** (for example, if the chapter starts on physical page 15 of the PDF but is labeled as page '1' *in the book text*, you return 1 for `start_page`).
                Only provide chapters that begin within the first {pages_to_scan} physical pages of the PDF.

                If a table of contents is present in the extracted pages, prioritize extracting information from it.
                Make sure the output strictly adheres to the specified JSON format.
            """,
            "prompt_first_chapter_physical_page": """
                Analyze the attached PDF, which is a textbook. I have extracted only the first {pages_to_scan} pages of the original document.

                Your task is to identify the physical page number (1-based) of the PDF that corresponds to the beginning of the *first numbered chapter*.
                **[CRITICAL RULE]**: Do not consider prefaces, indexes, or other introductory sections as the first chapter.
                For example, if the first chapter is found on physical page 8 of the PDF, you should return 8.
                Your answer must be *exclusively* the integer of the physical page. Do not add any additional text, explanation, or formatting.
            """,
            "prompt_elaborate_single_pdf": r""" 
                **Role:** You are an AI assistant specialized in processing academic documents. Your expertise is in analyzing and restructuring technical content for any subject matter.

                I am analyzing a PDF document containing educational material (lectures, notes, handouts) related to "**[subject]**". I need to create a structured LaTeX document that summarizes key concepts, extracts presented exercises, and generates new exercises.

                1. Carefully analyze the text of the provided PDF document.
                2. **Identify and extract the document header, if present, such as the main title, author, and date.**
                3. **Identify and extract all theorems or principles/laws presented.** For each theorem, you must include its complete statement and, if present, its number (e.g., Theorem 1.1, Ohm's Law). **Do not provide the theorem's proof, but ask the reader to prove it.**
                4. **Identify and extract definitions of key concepts.** For each concept, you must indicate the term to be defined, then ask the reader to provide the definition and add the definition number. **It is crucial that the order of theorems and definitions in the LaTeX document mirrors their order in the original PDF.**
                5. **Identify and extract the presented exercises.** For each exercise, you must include the complete exercise text. **If the original exercise text is not explicitly present but is only a reference (e.g., "Exercise 1"), the AI should generate a representative exercise text based on the surrounding context or the typical problem type for that topic.** **Do not provide the exercise solution.**
                6. **Generate 1 additional exercise for each extracted exercise.** These AI-generated exercises must require the same conceptual tools for solving as the original exercises but must present different data, contexts, or scenarios to be conceptually distinct. Ensure they are consistent with the difficulty level and topics covered in the original document.
                7. Completely ignore:
                    * Complete theorem proofs.
                    * Additional comments or explanations that don't fall into the above categories (theorems, definitions, exercises).
                    * Grading rubrics or scores.
                    * **Complete book content or in-depth explanatory sections that are not theorems, definitions, or exercises.**
                    * **ISBN or any other editorial data.**

                * The final file must be in LaTeX format (`.tex`).
                * **Start the file with the following LaTeX structure:**
                    \documentclass{article}
                    \usepackage[utf8]{inputenc}
                    \usepackage{amsmath} % For advanced math equations
                    \usepackage{amsfonts} % For additional math symbols
                    \usepackage{amssymb} % For additional math symbols
                    \usepackage{enumitem} % For customizing lists
                    \usepackage{fancyhdr} % For headers/footers (optional, if needed)
                    \usepackage{hyperref} % For links (optional)
                    \usepackage{xcolor} % For colors (optional, if needed)
                    \usepackage{courier} % For monospaced text (or other desired monospaced font)
                    \usepackage{listings} % For code blocks and pseudocode
                    \lstset{
                        basicstyle=\ttfamily, % Monospaced font for code
                        columns=fullflexible, % Adapt columns to text
                        breaklines=true, % Break long lines
                        frame=single, % Frame around code blocks
                        showstringspaces=false % Don't show spaces in strings
                        % You can add other code formatting options
                    }

                    \pagestyle{plain} % Or fancy if using fancyhdr

                    \begin{document}
                * **After `\begin{document}`, insert the extracted header, if present, formatted as follows:**
                    * The main title using `\title{}` and `\maketitle`.
                    * The author using `\author{}`.
                * **Use the following sections to organize the content:**
                    * **Extracted Content:** Use a section titled `\section*{Extracted Content}`. Within this section, list theorems and definitions in the exact order they were found in the original document.
                        * Each theorem must be presented as an item in a numbered list (`enumerate`). The statement must follow the format: `\textbf{Theorem/Principle/Law [Number/Name]:} [Complete statement]. \par \textbf{Proof:} [Leave space for reader's proof]`
                        * Each concept to be defined must be presented as an item in a numbered list (`enumerate`). The definition must follow the format: `\textbf{Definition [Definition Number]:} Define [Concept to be Defined].`
                    * **Original Exercises:** Use a section titled `\section*{Original Exercises}`. Each exercise must be presented as an item in a numbered list (`enumerate`). The exercise text must follow the format: `\textbf{Exercise [Exercise Number]:} [Complete exercise text generated by AI if missing or extracted].`
                    * **AI-Generated Exercises:** Use a section titled `\section*{AI-Generated Exercises}`. Each generated exercise must be an item in a numbered list (`enumerate`). The format must be:
                        ```latex
                        \begin{enumerate}
                            \item [Text of first generated exercise.]
                            \item [Text of second generated exercise.]
                            \item [Text of third generated exercise.]
                            ...
                            \item [Text of nth generated exercise.]
                        \end{enumerate}
                        ```
                * Maintain the original text formatting:
                    * **Bold** must be `\textbf{text}`.
                    * `monospace` for inline code must be `\texttt{code}`.
                * For mathematical and scientific notations, use standard LaTeX formatting:
                    * Include inline mathematical expressions within `$ $`.
                    * Include equation blocks within `$$ $$` or environments like `equation*` or `align*`.
                * At the end of the document, close the `document` environment with `\end{document}`.
                * **[CRITICAL RULE]** Your response must contain *exclusively* the LaTeX content. Do not include any introductory, greeting, or explanatory phrases (e.g., "Here's the output...", "Sure, here are the questions...", etc.). Your response must start directly with `\documentclass{article}`.
            """,
            "prompt_error_correction": r"""
                The LaTeX code you previously generated for the document was invalid during compilation.
                The following errors occurred:
                ```
                **[error_message]**

                ```
                Please analyze these errors carefully. Your task is to **correct the LaTeX code to resolve these compilation issues**, while **faithfully maintaining the original content and structure** that you extracted from the PDF. Do not alter the meaning or formatting of theorems, definitions, and exercises.

                **Critical LaTeX Rules for Correction:**
                * **Paired Environments:** Every `\begin{environment}` must have a corresponding `\end{environment}` (e.g., `\begin{itemize}` and `\end{itemize}`, `\begin{equation}` and `\end{equation}`).
                * **Math Delimiters:**
                    * Inline equations: Always use single dollars `$` to start and end (e.g., `A vector $v$`).
                    * Equation blocks (display mode): Use double dollars `$$` or specific environments like `\begin{equation}` / `\end{equation}` or `\begin{align*}` / `\end{align*}`.
                * **Undefined Commands:** Ensure all commands (`\cmd`) and environments are defined by included packages (`amsmath`, `amsfonts`, `amssymb`, `enumitem`, `fancyhdr`, `hyperref`, `xcolor`, `courier`, `listings`). Don't introduce new commands or environments without necessary packages.
                * **Special Characters:** LaTeX special characters (e.g., `#`, `$`, `%`, `&`, `_`, `{{`, `}}`, `~`, `^`, `\\`, `<`, `>`) must be escaped with a backslash (`\\`) if they should appear as normal text, unless used for their LaTeX purpose.
                * **Bracket Balance:** All parentheses, square brackets, and curly braces (especially those used in LaTeX commands or environments) must be properly balanced.
                * **Avoid `[ ]` for Inline Text:** Don't use `[` and `]` to enclose normal text unless it's an optional argument of a LaTeX command.
                * **Non-Math Text in Math Environments:** Normal text inside math environments (`$` or `$$`) must be enclosed in `\\text{}` or `\\mbox{}` to ensure proper font formatting (e.g., `$ \\text{where} x > 0 $`).
                * **Common Error: Missing/Wrong Curly Braces:** The most common error, especially in generated exercises, is incorrect use or missing curly braces `}`. Often, a character like `>` is used instead of `}` to close a LaTeX command or environment. Carefully check that all curly braces are present and correctly positioned.

                Provide me with a valid and compilable version of the LaTeX code.
                Maintain exactly the LaTeX format required in the original prompt (without introductions, greetings, or explanations, starting directly with `\documentclass{article}`).
            """,
        },
        "it": {
            "prompt_chapters_pages": """
                Analizza il PDF allegato, che è un libro di testo. Ho estratto solo le prime {pages_to_scan} pagine del documento originale.

                Il tuo compito è identificare e elencare *esclusivamente* i capitoli principali che iniziano con una numerazione chiara,
                come "Capitolo 1", "Capitolo 2", "Chapter 3", "Unit 4", o simili formati numerati.
                Non includere introduzioni, prefazioni, indici, bibliografie, appendici, soluzioni, o qualsiasi altra sezione
                che non sia un capitolo numerato esplicitamente. Per ogni capitolo identificato, restituisci il suo titolo esatto come appare nel testo e il numero della pagina su cui inizia,
                così come **numerato all'interno del libro** (ad esempio, se il capitolo inizia sulla pagina fisica 15 del PDF ma è etichettata come pagina '1' *nel testo del libro*, tu restituisci 1 per `start_page`).
                Fornisci solo i capitoli che iniziano entro le prime {pages_to_scan} pagine fisiche del PDF.

                Se un indice è presente nelle pagine estratte, prioritizza l'estrazione delle informazioni da esso.
                Assicurati che l'output aderisca rigorosamente al formato JSON specificato.
                """,
            "prompt_first_chapter_physical_page": """
                Analizza il PDF allegato, che è un un libro di testo. Ho estratto solo le prime {pages_to_scan} pagine del documento originale.

                Il tuo compito è identificare la pagina fisica (basata su 1) del PDF che corrisponde all'inizio del *primo capitolo numerato*.
                **[REGOLA CRITICA]**: Non considerare prefazioni, indici o altre sezioni introduttive come il primo capitolo.
                Ad esempio, se il primo capitolo si trova nella pagina fisica 8 del PDF, devi restituire 8.
                La tua risposta deve essere *esclusivamente* il numero intero della pagina fisica. Non aggiungere alcun testo aggiuntivo, spiegazione o formattazione.
            """,
            "prompt_elaborate_single_pdf": r""" 
                 **Ruolo:** Sei un assistente AI esperto nell'elaborazione di documenti accademici. La tua specializzazione è l'analisi e la ristrutturazione di contenuti tecnici, per qualsiasi materia. 

                 Sto analizzando un documento PDF contenente materiale didattico (lezioni, appunti, dispense) relativo a "**[subject]**". Ho bisogno di creare un documento strutturato in LaTeX che riassuma i concetti chiave, estragga gli esercizi presentati e generi nuovi esercizi. 

                 1.  Analizza attentamente il testo del documento PDF che ti verrà fornito. 
                 2.  **Identifica e estrai l'intestazione del documento, se presente, come il titolo principale, l'autore e la data.**                 
                 3.  **Identifica e estrai tutti i teoremi o principi/leggi presentati.** Per ogni teorema, dovrai includere il suo enunciato completo e, se presente, il suo numero (es. Teorema 1.1, Legge di Ohm). **Non devi fornire la dimostrazione del teorema, ma richiedi al lettore di farlo.**
                 4.  **Identifica e estrai le definizioni dei concetti chiave.** Per ogni concetto, dovrai indicare il termine da definire richiedendo poi al lettore di dare la definizione e aggiungendo il numero della definizione. **È fondamentale che l'ordine di presentazione dei teoremi e delle definizioni nel documento LaTeX rispecchi l'ordine in cui appaiono nel PDF originale.**
                 5.  **Identifica e estrai gli esercizi presentati.** Per ogni esercizio, dovrai includere il testo completo dell'esercizio. **Se il testo dell'esercizio originale non è esplicitamente presente ma è solo un riferimento (es. "Esercizio 1"), l'AI dovrà generare un testo dell'esercizio rappresentativo basandosi sul contesto circostante o sul tipo di problema tipico di quell'argomento.** **Non devi fornire la soluzione dell'esercizio.**
                 6.  **Genera 1 esercizio aggiuntivo per ciascun esercizio estratto.** Questi esercizi generati dall'AI devono richiedere gli stessi strumenti concettuali per la risoluzione degli esercizi originali, ma devono presentare dati, contesti o scenari diversi in modo da essere concettualmente distinti. Assicurati che siano coerenti con il livello di difficoltà e gli argomenti trattati nel documento originale.
                 7.  Ignora completamente: 
                     * Dimostrazioni complete di teoremi. 
                     * Commenti o spiegazioni aggiuntive che non rientrano nelle categorie sopra menzionate (teoremi, definizioni, esercizi). 
                     * Griglie di valutazione o punteggi. 
                     * **Contenuto completo del libro o sezioni esplicative approfondite che non siano teoremi, definizioni o esercizi.**                     
                     * **ISBN o qualsiasi altro dato editoriale.**                 
                * Il file finale deve essere in formato LaTeX (`.tex`). 
                * **Inizia il file con la seguente struttura LaTeX:**                     
                    \documentclass{article} 
                     \usepackage[utf8]{inputenc} 
                     \usepackage{amsmath} % Per equazioni matematiche avanzate 
                     \usepackage{amsfonts} % Per simboli matematici aggiuntivi 
                     \usepackage{amssymb} % Per simboli matematici aggiuntivi 
                     \usepackage{enumitem} % Per personalizzare gli elenchi 
                     \usepackage{fancyhdr} % Per intestazioni/piè di pagina (opzionale, se serve) 
                     \usepackage{hyperref} % Per link (opzionale) 
                     \usepackage{xcolor} % Per colori (opzionale, se serve) 
                     \usepackage{courier} % Per testo monospaced (o altro font monospaced desiderato) 
                     \usepackage{listings} % Per blocchi di codice e pseudocodice 
                     \lstset{ 
                         basicstyle=\ttfamily, % Font monospaced per il codice 
                         columns=fullflexible, % Adatta le colonne al testo 
                         breaklines=true, % Spezza le righe lunghe 
                         frame=single, % Cornice intorno ai blocchi di codice 
                         showstringspaces=false % Non mostrare spazi nelle stringhe 
                         % Puoi aggiungere altre opzioni per la formattazione del codice 
                     } 

                     \pagestyle{plain} % O fancy se usi fancyhdr 

                     \begin{document} 
                 * **Dopo `\begin{document}`, inserisci l'intestazione estratta, se presente, formattandola come segue:**                     * Il titolo principale usando `\title{}` e `\maketitle`. 
                     * L'autore usando `\author{}`. 
                 * **Utilizza le seguenti sezioni per organizzare il contenuto:**                     * **Contenuti Estratti:** Utilizza una sezione intitolata `\section*{Contenuti Estratti}`. All'interno di questa sezione, elenca teoremi e definizioni nell'ordine esatto in cui sono stati trovati nel documento originale. 
                         * Ogni teorema deve essere presentato come un elemento di un elenco numerato (`enumerate`). L'enunciato deve seguire il formato: `\textbf{Teorema/Principio/Legge [Numero/Nome]:} [Enunciato completo]. \par \textbf{Dimostrazione:} [Lasciare spazio per la dimostrazione del lettore]` 
                         * Ogni concetto da definire deve essere presentato come un elemento di un elenco numerato (`enumerate`). La definizione deve seguire il formato: `\textbf{Definizione [Numero della Definizione]:} Definire [Concetto da Definire].` 
                     * **Esercizi Originali:** Utilizza una sezione intitolata `\section*{Esercizi Originali}`. Ogni esercizio deve essere presentato come un elemento di un elenco numerato (`enumerate`). Il testo dell'esercizio deve seguire il formato: `\textbf{Esercizio [Numero dell'Esercizio]:} [Testo completo dell'esercizio generato dall'AI se mancante o estratto].` 
                     * **Esercizi Generati dall'AI:** Utilizza una sezione intitolata `\section*{Esercizi Generati dall'AI}`. Ogni esercizio generato deve essere un elemento di un elenco numerato (`enumerate`). Il formato deve essere: 
                         ```latex 
                         \begin{enumerate} 
                             \item [Testo del primo esercizio generato.] 
                             \item [Testo del secondo esercizio generato.] 
                             \item [Testo del terzo esercizio generato.] 
                             ... 
                             \item [Testo dell'n-esimo esecizio generato.] 
                         \end{enumerate} 
                         ``` 
                 * Mantieni la formattazione originale del testo estratto: 
                     * Il **grassetto** deve essere `\textbf{testo}`. 
                     * Il `monospace` per il codice inline deve essere `\texttt{codice}`. 
                 * Per le notazioni matematiche e scientifiche, utilizza la formattazione LaTeX standard: 
                     * Includi le espressioni matematiche inline all'interno di `$ $`. 
                     * Includi i blocchi di equazioni all'interno di `$$ $$` o ambienti come `equation*` o `align*`. 
                 * Alla fine del documento, chiudi l'ambiente `document` con `\end{document}`. 
                 * **[REGOLA CRITICA]** La tua risposta deve contenere *esclusivamente* il contenuto LaTeX. Non includere alcuna frase introduttiva, di saluto o di spiegazione (es. "Ecco l'output...", "Certo, ecco le domande...", ecc.). La tua risposta deve iniziare direttamente con `\documentclass{article}`. 
             """,
            "prompt_error_correction": r"""
                Il codice LaTeX che hai generato in precedenza per il documento è risultato non valido durante la compilazione.
                Si sono verificati i seguenti errori:
                ```
                **[error_message]**

                ```
                Ti prego di analizzare attentamente questi errori. Il tuo compito è **correggere il codice LaTeX in modo da risolvere questi problemi di compilazione**, mantenendo **fedelmente il contenuto e la struttura originale** che avevi estratto dal PDF. Non alterare il significato o la formattazione dei teoremi, definizioni ed esercizi.

                **Regole LaTeX Cruciali per la Correzione:**
                * **Ambienti Accoppiati:** Ogni `\begin{ambiente}` deve avere un corrispondente `\end{ambiente}` (es. `\begin{itemize}` e `\end{itemize}`, `\begin{equation}` e `\end{equation}`).
                * **Delimitatori Matematici:**
                    * Equazioni inline: Usare sempre singoli dollari `$` per iniziare e terminare (es. `Un vettore $v$`).
                    * Blocchi di equazioni (display mode): Usare doppi dollari `$$` o ambienti specifici come `\begin{equation}` / `\end{equation}` o `\begin{align*}` / `\end{align*}`.
                * **Comandi Non Definiti:** Assicurati che tutti i comandi (`\cmd`) e gli ambienti siano definiti dai pacchetti inclusi (`amsmath`, `amsfonts`, `amssymb`, `enumitem`, `fancyhdr`, `hyperref`, `xcolor`, `courier`, `listings`). Non introdurre nuovi comandi o ambienti senza i pacchetti necessari.
                * **Caratteri Speciali:** I caratteri speciali LaTeX (es. `#`, `$`, `%`, `&`, `_`, `{{`, `}}`, `~`, `^`, `\\`, `<`, `>`) devono essere preceduti da un backslash (`\\`) se devono apparire come testo normale, a meno che non siano usati per il loro scopo LaTeX.
                * **Bilanciamento delle Parentesi:** Tutte le parentesi tonde, quadre e graffe (specialmente quelle usate in comandi o ambienti LaTeX) devono essere correttamente bilanciate.
                * **Evitare `[ ]` per Testo in Linea:** Non utilizzare `[` e `]` per racchiudere testo normale, a meno che non si tratti di un argomento opzionale di un comando LaTeX.
                * **Testo non Matematico in Ambienti Matematici:** Il testo normale all'interno di ambienti matematici (`$` o `$$`) deve essere racchiuso in `\\text{}` o `\\mbox{}` per garantire la corretta formattazione del font (es. `$ \\text{{dove}} x > 0 $`).
                * **Errore Comune: Parentesi Graffe Mancanti/Sbagliate:** L'errore più comune, soprattutto negli esercizi generati, è l'uso errato o la mancanza di parentesi graffe `}`. Spesso, viene usato un carattere come `>` al posto di `}` per chiudere un comando o un ambiente LaTeX. Controlla attentamente che tutte le parentesi graffe siano presenti e posizionate correttamente.

                Forniscimi una versione valida e compilabile del codice LaTeX.
                Mantieni esattamente il formato LaTeX richiesto nel prompt originale (senza introduzioni, saluti o spiegazioni, iniziando direttamente con `\documentclass{article}`).
            """,
        },
    }
