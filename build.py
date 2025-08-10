import os
import shutil
import subprocess

def main():

    subprocess.run(
        [   
            "pyinstaller",
            "--onefile",
            "easy_study_flashcards/__init__.py",
            "--name",
            "Study flashcards from pdf",
        ],
        cwd=os.getcwd(),
        check=True
    )

if __name__ == "__main__":
    main()
