import os
import shutil
import subprocess
import sys

xelatex_executable_path = shutil.which("xelatex")

assert xelatex_executable_path is not None

EXTERNAL_DIR_PATH = os.path.join(os.getcwd(), "./build/external/")
EXTERNAL_DIR_PATH = os.path.normpath(EXTERNAL_DIR_PATH)

xelatex_basename = os.path.basename(xelatex_executable_path)
copied_xelatex_path = os.path.join(EXTERNAL_DIR_PATH, xelatex_basename)

if not os.path.exists(EXTERNAL_DIR_PATH):
    os.makedirs(EXTERNAL_DIR_PATH)
    shutil.copyfile(xelatex_executable_path, os.path.join(EXTERNAL_DIR_PATH, xelatex_basename))

pyinstaller_executable = shutil.which("pyinstaller", path=".venv/Scripts/")

assert pyinstaller_executable is not None

subprocess.run(
    [   
        pyinstaller_executable,
        "--onefile",
        "study_flashcards_from_pdf/__init__.py",
        "--name",
        "Study_flashcards_from_pdf",
        "--add-binary",
        f"{copied_xelatex_path};." if sys.platform.startswith("win32") or sys.platform.startswith("cygwin")  else 
        f"{copied_xelatex_path}:."
    ],
    cwd=os.getcwd()
)
