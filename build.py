import os
import shutil
import subprocess

def main():

    pyinstaller_executable = shutil.which("pyinstaller", path=".venv/Scripts/")
    if not pyinstaller_executable:
        raise RuntimeError("PyInstaller not found in virtual environment")

    subprocess.run(
        [   
            pyinstaller_executable,
            "--onefile",
            "study_flashcards_from_pdf/__init__.py",
            "--name",
            "Study_flashcards_from_pdf",
        ],
        cwd=os.getcwd(),
        check=True
    )

if __name__ == "__main__":
    main()
