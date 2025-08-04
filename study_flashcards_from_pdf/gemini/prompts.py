class PromptsForGemini:

    @staticmethod
    def get_prompt_chapters_pages(lang: str, pages_to_scan: int) -> str:
        assert lang in PromptsForGemini.prompts

        return PromptsForGemini.prompts[lang]["prompt_chapters_pages"].format(
            pages_to_scan=pages_to_scan
        )

    @staticmethod
    def get_prompt_first_chapter_physical_page(lang: str, pages_to_scan: int) -> str:
        assert lang in PromptsForGemini.prompts

        return PromptsForGemini.prompts[lang][
            "prompt_first_chapter_physical_page"
        ].format(pages_to_scan=pages_to_scan)

    @staticmethod
    def get_prompt_to_elaborate_single_pdf(lang: str, subject_matter: str) -> str: # Added subject_matter parameter
        assert lang in PromptsForGemini.prompts

        return PromptsForGemini.prompts[lang]["prompt_elaborate_single_pdf"].format(
            subject_matter=subject_matter
        )

    @staticmethod
    def get_prompt_for_error_correction(lang: str, error_message: str) -> str:
        assert lang in PromptsForGemini.prompts

        return PromptsForGemini.prompts[lang]["prompt_error_correction"].format(
            error_message=error_message
        )

    prompts: dict[str, dict[str, str]] = {
        "en": {"prompt_chapters_pages": ""},
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
                **Ruolo:** Sei un assistente AI esperto nella creazione di schede di studio interattive da documenti accademici sulla materia di {subject_matter}.

                Il tuo compito è analizzare il documento PDF fornito e generare un documento LaTeX strutturato per creare schede di studio, focalizzandoti sulla richiesta attiva di conoscenza al lettore. Le schede devono essere ottimizzate per imparare, richiedendo al lettore di fornire le risposte.

                1.  Analizza attentamente il testo del documento PDF.
                2.  **Identifica e estrai l'intestazione del documento, se presente, come il titolo principale, l'autore e la data.**
                3.  **Identifica e estrai tutti i teoremi o principi fondamentali presentati.** Per ogni teorema, includi il suo enunciato completo e, se presente, il suo numero (es. Teorema 1.1). Subito dopo l'enunciato, inserisci una richiesta al lettore di dimostrarlo. **NON devi fornire la dimostrazione del teorema.**
                4.  **Identifica e estrai le definizioni dei concetti chiave.** Per ogni concetto, indica chiaramente il termine da definire e poi chiedi al lettore di fornirne la definizione, aggiungendo il numero della definizione se presente.
                5.  **Identifica e estrai le domande a risposta aperta implicite o esplicite nel testo.** Queste possono derivare da paragrafi che introducono un problema o una discussione. Trasforma queste informazioni in domande dirette rivolte al lettore.
                6.  **Identifica e estrai gli esercizi presentati.** Per ogni esercizio, includi il testo completo. **Se il testo dell'esercizio originale non è esplicitamente presente ma è solo un riferimento (es. "Esercizio 1"), l'AI dovrà generare un testo dell'esercizio rappresentativo basandosi sul contesto circostante o sul tipo di problema tipico di quell'argomento.** **NON devi fornire la soluzione dell'esercizio.**
                7.  **Genera 1 esercizio aggiuntivo per ciascun esercizio estratto.** Questi esercizi generati dall'AI devono richiedere gli stessi strumenti concettuali per la risoluzione degli esercizi originali, ma devono presentare dati, contesti o scenari diversi in modo da essere concettualmente distinti. Assicurati che siano coerenti con il livello di difficoltà e gli argomenti trattati nel documento originale.

                **[REGOLA FONDAMENTALE]**: In nessun caso devono essere fornite spiegazioni dettagliate, soluzioni di esercizi, dimostrazioni di teoremi, o risposte a domande. L'obiettivo è stimolare la memoria attiva del lettore.

                8.  Ignora completamente:
                    * Dimostrazioni complete di teoremi.
                    * Commenti o spiegazioni aggiuntive che non rientrano nelle categorie sopra menzionate (teoremi, definizioni, domande, esercizi).
                    * Griglie di valutazione o punteggi.
                    * Contenuto completo del libro o sezioni esplicative approfondite che non siano teoremi, definizioni, domande o esercizi.
                    * ISBN o qualsiasi altro dato editoriale.

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
                * **Dopo `\begin{document}`, inserisci l'intestazione estratta, se presente, formattandola come segue:**
                    * Il titolo principale usando `\title{}` e `\maketitle`.
                    * L'autore usando `\author{}`.
                * **Utilizza le seguenti sezioni per organizzare il contenuto:**
                    * **Definizioni e Teoremi:** Utilizza una sezione intitolata `\section*{Definizioni e Teoremi}`. All'interno di questa sezione, elenca teoremi e definizioni nell'ordine esatto in cui sono stati trovati nel documento originale.
                        * Ogni teorema deve essere presentato come un elemento di un elenco numerato (`enumerate`). L'enunciato deve seguire il formato: `\textbf{Teorema [Numero del Teorema/Nome]:} [Enunciato del teorema]. \\textit{Dimostra il seguente teorema.}`
                        * Ogni concetto da definire deve essere presentato come un elemento di un elenco numerato (`enumerate`). La definizione deve seguire il formato: `\textbf{Definizione [Numero della Definizione]:} Definire [Concetto da Definire].`
                    * **Domande a Risposta Aperta:** Utilizza una sezione intitolata `\section*{Domande a Risposta Aperta}`. Ogni domanda deve essere presentata come un elemento di un elenco numerato (`enumerate`). Il testo della domanda deve seguire il formato: `\textbf{Domanda [Numero]:} [Testo della domanda].`
                    * **Esercizi Originali:** Utilizza una sezione intitolata `\section*{Esercizi Originali}`. Ogni esercizio deve essere presentato come un elemento di un elenco numerato (`enumerate`). Il testo dell'esercizio deve seguire il formato: `\textbf{Esercizio [Numero dell'Esercizio]:} [Testo completo dell'esercizio generato dall'AI se mancante o estratto].`
                    * **Esercizi Generati dall'AI:** Utilizza una sezione intitolata `\section*{Esercizi Generati dall'AI}`. Ogni esercizio generato deve essere un elemento di un elenco numerato (`enumerate`). Il formato deve essere:
                        ```latex
                        \begin{enumerate}
                            \item [Testo del primo esercizio generato.]
                            \item [Testo del secondo esercizio generato.]
                            \item [Testo del terzo esercizio generato.]
                            ...
                            \item [Testo dell'n-esimo esercizio generato.]
                        \end{enumerate}
                        ```
                * Mantieni la formattazione originale del testo estratto:
                    * Il **grassetto** deve essere `\\textbf{testo}`.
                    * Il `monospace` per il codice inline deve essere `\\texttt{codice}`.
                * Per le notazioni matematiche e scientifiche, utilizza la formattazione LaTeX standard:
                    * Includi le espressioni matematiche inline all'interno di `$ $`.
                    * Includi i blocchi di equazioni all'interno di `$$ $$` o ambienti come `equation*` o `align*`.
                * Alla fine del documento, chiudi l'ambiente `document` con `\\end{document}`.
                * **[REGOLA CRITICA]** La tua risposta deve contenere *esclusivamente* il contenuto LaTeX. Non includere alcuna frase introduttiva, di saluto o di spiegazione (es. "Ecco l'output...", "Certo, ecco le domande...", ecc.). La tua risposta deve iniziare direttamente con `\documentclass{article}`.
            """,
            "prompt_error_correction": """
                Il codice LaTeX che hai generato in precedenza per il documento è risultato non valido durante la compilazione.
                Si sono verificati i seguenti errori:
                ```
                {error_message}

                ```
                Ti prego di analizzare attentamente questi errori. Il tuo compito è **correggere il codice LaTeX in modo da risolvere questi problemi di compilazione**, mantenendo **fedelmente il contenuto e la struttura originale** che avevi estratto dal PDF. Non alterare il significato o la formattazione dei teoremi, definizioni ed esercizi.

                **Regole LaTeX Cruciali per la Correzione:**
                * **Ambienti Accoppiati:** Ogni `\\begin{{ambiente}}` deve avere un corrispondente `\\end{{ambiente}}` (es. `\\begin{{itemize}}` e `\\end{{itemize}}`, `\\begin{{equation}}` e `\\end{{equation}}`).
                * **Delimitatori Matematici:**
                    * Equazioni inline: Usare sempre singoli dollari `$` per iniziare e terminare (es. `Un vettore $v$`).
                    * Blocchi di equazioni (display mode): Usare doppi dollari `$$` o ambienti specifici come `\\begin{{equation}}` / `\\begin{{equation}}` o `\\begin{align*}` / `\\begin{align*}`. Evitare `\\[ \\]` se non strettamente necessario, preferendo `$$ $$` per semplicità o gli ambienti AMS.
                * **Comandi Non Definiti:** Assicurati che tutti i comandi (`\\cmd`) e gli ambienti siano definiti dai pacchetti inclusi (`amsmath`, `amsfonts`, `amssymb`, `enumitem`, `fancyhdr`, `hyperref`, `xcolor`, `courier`, `listings`). Non introdurre nuovi comandi o ambienti senza i pacchetti necessari.
                * **Caratteri Speciali:** I caratteri speciali LaTeX (es. `#`, `$`, `%`, `&`, `_`, `{`, `}`, `~`, `^`, `\\`, `<`, `>`) devono essere preceduti da un backslash (`\\`) se devono apparire come testo normale, a meno che non siano usati per il loro scopo LaTeX.
                * **Bilanciamento delle Parentesi:** Tutte le parentesi tonde, quadre e graffe (specialmente quelle usate in comandi o ambienti LaTeX) devono essere correttamente bilanciate.
                * **Evitare `[ ]` per Testo in Linea:** Non utilizzare `[` e `]` per racchiudere testo normale, a meno che non si tratti di un argomento opzionale di un comando LaTeX.
                * **Testo non Matematico in Ambienti Matematici:** Il testo normale all'interno di ambienti matematici (`$` o `$$`) deve essere racchiuso in `\\text{}` o `\\mbox{}` per garantire la corretta formattazione del font (es. `$ \\text{dove } x > 0 $`).
                * **Errore Comune: Parentesi Graffe Mancanti/Sbagliate:** L'errore più comune, soprattutto negli esercizi generati, è l'uso errato o la mancanza di parentesi graffe `}`. Spesso, viene usato un carattere come `>` al posto di `}` per chiudere un comando o un ambiente LaTeX. Controlla attentamente che tutte le parentesi graffe siano presenti e posizionate correttamente.

                Forniscimi una versione valida e compilabile del codice LaTeX.
                Mantieni esattamente il formato LaTeX richiesto nel prompt originale (senza introduzioni, saluti o spiegazioni, iniziando direttamente con `\\documentclass{article}`).
            """,
        },
    }