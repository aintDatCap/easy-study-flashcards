import os
import shutil
import subprocess

def main():

    subprocess.run(
        [   
            "pyinstaller",
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
