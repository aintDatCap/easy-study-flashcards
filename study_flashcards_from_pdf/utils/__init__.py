import shutil
import sys
import os
from loguru import logger

def get_xelatex_path() -> str:
    is_frozen: bool = getattr(sys, 'frozen', False)
    
    base_executable: str = os.path.join(sys._MEIPASS, "xelatex") if is_frozen else "xelatex"  # type: ignore
    executable_path: str | None = shutil.which(base_executable)
    
    if executable_path is None:
        logger.error("XeLaTeX executable not found in system PATH")
        sys.exit(1)  

    return executable_path
    
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