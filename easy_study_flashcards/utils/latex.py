from enum import Enum
import shutil
import sys
import requests
import subprocess
import tempfile
import zipfile
from pathlib import Path
from easy_study_flashcards.utils.localization import localizer as _
from loguru import logger
import os

class MikTexInstallationResult(Enum):
    OK = 1
    ERROR_DOWNLOAD = 2
    ERROR_EXTRACTION = 3
    ERROR_INSTALLATION = 4


def download_and_install_miktex() -> MikTexInstallationResult:
    """Downloads and installs miktex."""
    MIKTEX_SETUP_URL = "https://miktex.org/download/win/miktexsetup-x64.zip"

    try:
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "miktexsetup.zip"

            logger.info(_.get_string('miktex_download'))
            response = requests.get(MIKTEX_SETUP_URL, stream=True)
            response.raise_for_status()

            with open(zip_path, "wb") as f:
                f.write(response.content)

            logger.info(_.get_string('miktex_extract'))
            try:
                with zipfile.ZipFile(zip_path) as zip_ref:
                    zip_ref.extractall(temp_path)
            except zipfile.BadZipFile:
                logger.error("Failed to extract MiKTeX setup")
                return MikTexInstallationResult.ERROR_EXTRACTION

            setup_exe = temp_path / "miktexsetup_standalone.exe"

            logger.info(_.get_string('miktex_install'))
            download_result = subprocess.run(
                [
                    str(setup_exe),
                    "--package-set=basic",
                    "--local-package-repository=current",
                    "download",
                ],
                capture_output=True,
                text=True,
            )
            if download_result.returncode != 0:
                logger.error(f"Failed to download packages: {download_result.stderr}")
                return MikTexInstallationResult.ERROR_DOWNLOAD


            logger.info("Installing MiKTeX...")
            install_result = subprocess.run(
                [
                    str(setup_exe),
                    "--package-set=basic",
                    "--local-package-repository=current",
                    "install",
                ],
                capture_output=True,
                text=True,
            )
            if install_result.returncode != 0:
                logger.error(f"Failed to install MiKTeX: {install_result.stderr}")
                return MikTexInstallationResult.ERROR_INSTALLATION

            logger.success(_.get_string('miktex_success'))
            return MikTexInstallationResult.OK

    except requests.RequestException as e:
        logger.error(_.get_string('miktex_download_error', error=str(e)))
        return MikTexInstallationResult.ERROR_DOWNLOAD
    except Exception as e:
        logger.error(_.get_string('miktex_install_error', error=str(e)))
        return MikTexInstallationResult.ERROR_INSTALLATION


def fix_common_generated_latex_erros(latex_text: str) -> str:
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


def get_xelatex_path() -> str:
    executable_path: str | None = shutil.which("xelatex")

    if executable_path is None:
        logger.warning(_.get_string('latex_not_found'))

        # if OS is windows
        if os.name == "nt":
            result = download_and_install_miktex()

            if result != MikTexInstallationResult.OK:
                logger.error(_.get_string('miktex_install_failed'))
                sys.exit(1)
                
            executable_path = shutil.which("xelatex")
        
        assert executable_path is not None

    return executable_path