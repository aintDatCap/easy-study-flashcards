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